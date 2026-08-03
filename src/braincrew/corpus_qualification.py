from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from braincrew.corpus_sealing import (
    PROVENANCE_SIDECAR_NAME,
    CorpusPackError,
    ValidatedCorpus,
    VisibilityRole,
    canonical_json_bytes,
    replay_sealing_receipt,
    sha256_digest,
    validate_sealed_corpus,
)
from braincrew.dataset_registry import DatasetBundleSnapshot, validate_dataset_bundle

DATASET_ID = "braincrew-evaluation-dataset"
HISTORICAL_DATASET_VERSION = "2.0.0"
HISTORICAL_DATASET_DIGEST = (
    "sha256:ef6b0a1f50fcd2ecb8b5d7addc7bc5daaa54537899a1ac6faba7c784eee6e98a"
)
DATASET_VERSION = "3.0.0"
DATASET_V3_DIGEST = "sha256:c07c561963f7d7f82159a2554370a77a4f5f26b495f7378f10af4a80f420a19d"
DATASET_V3_COMPONENT_DIGESTS = {
    "grounded": "sha256:f76a9a1fa9a6a4b467f76ce7649dc7c15f5ad7c615d6cbb20ed3394e486d94b2",
    "parsing": "sha256:33e17fbb4d3f5485df1482de37e472e1b20fceef922c9b1dda90f8d9dfc25f73",
    "retrieval": "sha256:9687ead24590cab1b9d244ef876f226545a1fb1aa2013c50e4be7a63430c8408",
}
HISTORICAL_SEED_VERSION: Literal["braincrew-evaluation-dataset-2.0.0"] = (
    "braincrew-evaluation-dataset-2.0.0"
)
SEED_VERSION: Literal["braincrew-evaluation-dataset-3.0.0"] = "braincrew-evaluation-dataset-3.0.0"
QUALIFICATION_RECEIPT_NAME = "qualification-receipt.json"
IMPORT_MANIFEST_NAME = "import-manifest.json"
_SEALED_EXTRA_FILES = {
    "sealing-receipt.json",
    PROVENANCE_SIDECAR_NAME,
    QUALIFICATION_RECEIPT_NAME,
    IMPORT_MANIFEST_NAME,
}

Digest = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]
Identifier80 = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$",
    ),
]


class CorpusQualificationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class QualificationDatasetIdentityV1(_StrictModel):
    id: Literal["braincrew-evaluation-dataset"]
    version: Literal["2.0.0"]
    content_digest: Digest
    component_digests: dict[str, Digest]
    case_count: Literal[100]


class QualificationDatasetIdentityV2(_StrictModel):
    id: Literal["braincrew-evaluation-dataset"]
    version: Literal["3.0.0"]
    content_digest: Digest
    component_digests: dict[str, Digest]
    case_count: Literal[100]


class QualificationCorpusIdentityV1(_StrictModel):
    id: str = Field(min_length=1, max_length=160)
    version: str = Field(min_length=1, max_length=80)
    sealed_content_digest: Digest
    sealing_receipt_digest: Digest


class QualificationCorpusIdentityV2(QualificationCorpusIdentityV1):
    provenance_digest: Digest


class QualifiedSource(_StrictModel):
    source_id: str = Field(min_length=1, max_length=160)
    expected_content_sha256: Digest | None
    observed_content_sha256: Digest
    required_roles: list[VisibilityRole]
    forbidden_roles: list[VisibilityRole]


class CorpusQualificationReceiptV1(_StrictModel):
    schema_version: Literal["corpus-qualification-receipt-v1"]
    corpus: QualificationCorpusIdentityV1
    dataset: QualificationDatasetIdentityV1
    required_source_count: int = Field(ge=1)
    distractor_source_count: int = Field(ge=1)
    required_role_counts: dict[VisibilityRole, int]
    sources: list[QualifiedSource] = Field(min_length=1)
    receipt_digest: Digest


class CorpusQualificationReceiptV2(_StrictModel):
    schema_version: Literal["corpus-qualification-receipt-v2"]
    corpus: QualificationCorpusIdentityV2
    dataset: QualificationDatasetIdentityV2
    required_source_count: int = Field(ge=1)
    distractor_source_count: int = Field(ge=1)
    required_role_counts: dict[VisibilityRole, int]
    sources: list[QualifiedSource] = Field(min_length=1)
    receipt_digest: Digest


class _AxImportManifestBase(_StrictModel):
    schema_version: Literal["ax-synthetic-seed-pack-v1"]
    corpus_id: str = Field(min_length=1, max_length=160)
    corpus_version: Identifier80
    tenant_slug: Identifier80
    demo_company_id: Identifier80
    corpus_manifest_path: Literal["corpus-manifest.json"]
    sealed_content_digest: Digest
    qualification_receipt_path: Literal["qualification-receipt.json"]
    qualification_receipt_digest: Digest
    normalization_contract_version: Literal["ax-seed-normalization-v1"]
    chunking_contract_version: Literal["ax-seed-chunking-v1"]
    import_digest: Digest


class AxImportManifestV1(_AxImportManifestBase):
    seed_version: Literal["braincrew-evaluation-dataset-2.0.0"]


class AxImportManifestV2(_AxImportManifestBase):
    seed_version: Literal["braincrew-evaluation-dataset-3.0.0"]


@dataclass(frozen=True)
class CorpusQualificationResult:
    receipt_path: Path
    import_manifest_path: Path
    receipt: CorpusQualificationReceiptV2
    import_manifest: AxImportManifestV2
    qualification_receipt_digest: str


@dataclass
class _SourceRequirement:
    source_id: str
    expected_content_sha256: str | None = None
    required_roles: set[VisibilityRole] = field(default_factory=set)
    forbidden_roles: set[VisibilityRole] = field(default_factory=set)


def qualify_corpus_pack(
    *,
    sealed_dir: Path,
    dataset_manifest_path: Path,
    tenant_slug: str,
    demo_company_id: str,
) -> CorpusQualificationResult:
    receipt_path = sealed_dir / QUALIFICATION_RECEIPT_NAME
    import_path = sealed_dir / IMPORT_MANIFEST_NAME
    if receipt_path.exists() or import_path.exists():
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "qualification outputs are create-only",
        )

    snapshot = _validate_dataset(dataset_manifest_path)
    validated, sealing_receipt_digest = _validate_pack(
        sealed_dir,
        allowed_extra_files=_SEALED_EXTRA_FILES,
    )
    _validate_source_corpus_binding(
        sealed_dir=sealed_dir,
        validated=validated,
        sealing_receipt_digest=sealing_receipt_digest,
        snapshot=snapshot,
    )
    receipt = _build_qualification_receipt_v2(
        validated=validated,
        sealing_receipt_digest=sealing_receipt_digest,
        snapshot=snapshot,
    )
    receipt_bytes = canonical_json_bytes(receipt.model_dump(mode="json")) + b"\n"
    qualification_receipt_digest = sha256_digest(receipt_bytes)
    import_manifest = _build_import_manifest_v2(
        receipt=receipt,
        qualification_receipt_digest=qualification_receipt_digest,
        tenant_slug=tenant_slug,
        demo_company_id=demo_company_id,
    )
    import_bytes = canonical_json_bytes(import_manifest.model_dump(mode="json"))

    receipt_created = False
    try:
        with TemporaryDirectory(
            prefix=".corpus-qualification-",
            dir=sealed_dir.resolve(strict=True).parent,
        ) as raw_temporary:
            temporary = Path(raw_temporary)
            temporary_receipt = temporary / QUALIFICATION_RECEIPT_NAME
            temporary_import = temporary / IMPORT_MANIFEST_NAME
            temporary_receipt.write_bytes(receipt_bytes)
            temporary_import.write_bytes(import_bytes)
            os.link(temporary_receipt, receipt_path)
            receipt_created = True
            os.link(temporary_import, import_path)
    except OSError as exc:
        if receipt_created:
            receipt_path.unlink(missing_ok=True)
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "qualification output pair could not be published create-only",
        ) from exc

    return CorpusQualificationResult(
        receipt_path=receipt_path,
        import_manifest_path=import_path,
        receipt=receipt,
        import_manifest=import_manifest,
        qualification_receipt_digest=qualification_receipt_digest,
    )


def replay_qualification_receipt(receipt_path: Path) -> dict[str, str]:
    try:
        untrusted = json.loads(receipt_path.read_text("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "qualification receipt is not strict canonical JSON",
        ) from exc
    if not isinstance(untrusted, dict):
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "qualification receipt is not strict canonical JSON",
        )
    schema_version = untrusted.get("schema_version")
    if schema_version == "corpus-qualification-receipt-v1":
        receipt_model: type[CorpusQualificationReceiptV1 | CorpusQualificationReceiptV2] = (
            CorpusQualificationReceiptV1
        )
        import_model: type[AxImportManifestV1 | AxImportManifestV2] = AxImportManifestV1
    elif schema_version == "corpus-qualification-receipt-v2":
        receipt_model = CorpusQualificationReceiptV2
        import_model = AxImportManifestV2
    else:
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "qualification receipt schema version is unsupported",
        )
    receipt_bytes, receipt_payload = _read_canonical_model(
        receipt_path,
        receipt_model,
        byte_policy="trailing-lf-required",
        error_message="qualification receipt is not strict canonical JSON",
    )
    receipt = receipt_model.model_validate(receipt_payload)
    receipt_semantic_payload = receipt.model_dump(mode="json")
    declared_receipt_digest = receipt_semantic_payload.pop("receipt_digest")
    if sha256_digest(canonical_json_bytes(receipt_semantic_payload)) != declared_receipt_digest:
        raise CorpusQualificationError(
            "CORPUS_PACK_DIGEST_MISMATCH",
            "qualification receipt digest does not reproduce",
        )

    sealed_dir = receipt_path.resolve(strict=True).parent
    validated, sealing_receipt_digest = _validate_pack(
        sealed_dir,
        allowed_extra_files=_SEALED_EXTRA_FILES,
    )
    if isinstance(receipt, CorpusQualificationReceiptV1):
        snapshot = _validate_historical_dataset(_dataset_manifest_path("2.0.0"))
        expected_receipt: CorpusQualificationReceiptV1 | CorpusQualificationReceiptV2 = (
            _build_qualification_receipt_v1(
                validated=validated,
                sealing_receipt_digest=sealing_receipt_digest,
                snapshot=snapshot,
            )
        )
    else:
        snapshot = _validate_dataset(_dataset_manifest_path("3.0.0"))
        _validate_source_corpus_binding(
            sealed_dir=sealed_dir,
            validated=validated,
            sealing_receipt_digest=sealing_receipt_digest,
            snapshot=snapshot,
        )
        expected_receipt = _build_qualification_receipt_v2(
            validated=validated,
            sealing_receipt_digest=sealing_receipt_digest,
            snapshot=snapshot,
        )
    if expected_receipt != receipt:
        raise CorpusQualificationError(
            "CORPUS_PACK_DIGEST_MISMATCH",
            "qualification receipt does not bind the current pack and dataset bytes",
        )

    import_path = sealed_dir / IMPORT_MANIFEST_NAME
    _, import_payload = _read_canonical_model(
        import_path,
        import_model,
        byte_policy="ax-import",
        error_message="import manifest is not strict canonical JSON",
    )
    import_manifest = import_model.model_validate(import_payload)
    qualification_receipt_digest = sha256_digest(receipt_bytes)
    if isinstance(receipt, CorpusQualificationReceiptV1):
        expected_import: AxImportManifestV1 | AxImportManifestV2 = _build_import_manifest_v1(
            receipt=receipt,
            qualification_receipt_digest=qualification_receipt_digest,
            tenant_slug=import_manifest.tenant_slug,
            demo_company_id=import_manifest.demo_company_id,
        )
    else:
        expected_import = _build_import_manifest_v2(
            receipt=receipt,
            qualification_receipt_digest=qualification_receipt_digest,
            tenant_slug=import_manifest.tenant_slug,
            demo_company_id=import_manifest.demo_company_id,
        )
    if expected_import != import_manifest:
        raise CorpusQualificationError(
            "CORPUS_PACK_DIGEST_MISMATCH",
            "import manifest does not bind the qualification receipt",
        )
    return {
        "receipt_digest": receipt.receipt_digest,
        "qualification_receipt_digest": qualification_receipt_digest,
        "import_digest": import_manifest.import_digest,
        "sealed_content_digest": receipt.corpus.sealed_content_digest,
        "receipt_schema_version": receipt.schema_version,
    }


def _validate_pack(
    sealed_dir: Path,
    *,
    allowed_extra_files: set[str] | None = None,
) -> tuple[ValidatedCorpus, str]:
    try:
        raw_manifest = json.loads((sealed_dir / "corpus-manifest.json").read_text("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "sealed corpus manifest is unavailable or invalid",
        ) from exc
    if _provenance_requires_review(raw_manifest):
        raise CorpusQualificationError(
            "CORPUS_PROVENANCE_REVIEW_REQUIRED",
            "all corpus and source provenance must be synthetic CC0 and reviewed",
        )
    try:
        validated = validate_sealed_corpus(
            sealed_dir,
            allowed_extra_files=allowed_extra_files or {"sealing-receipt.json"},
        )
        sealing_summary = replay_sealing_receipt(sealed_dir / "sealing-receipt.json")
    except (CorpusPackError, OSError) as exc:
        code = getattr(exc, "code", "CORPUS_PACK_SCHEMA_INVALID")
        blocker = (
            "CORPUS_PACK_DIGEST_MISMATCH"
            if "DIGEST" in code or "RECEIPT" in code
            else "CORPUS_PACK_SCHEMA_INVALID"
        )
        raise CorpusQualificationError(blocker, "sealed corpus revalidation failed") from exc
    return validated, sealing_summary["receipt_digest"]


def _provenance_requires_review(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    if (
        payload.get("synthetic") is not True
        or payload.get("license") != "CC0-1.0"
        or payload.get("provenance_status") != "reviewed"
    ):
        return True
    sources = payload.get("sources")
    if not isinstance(sources, list):
        return False
    return any(
        not isinstance(source, dict)
        or source.get("synthetic") is not True
        or source.get("license") != "CC0-1.0"
        or source.get("provenance_status") != "reviewed"
        for source in sources
    )


def _validate_dataset(manifest_path: Path) -> DatasetBundleSnapshot:
    try:
        report = validate_dataset_bundle(manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            f"qualification requires {DATASET_ID}@{DATASET_VERSION}",
        ) from exc
    snapshot = report.snapshot
    if (
        report.state != "VALID"
        or snapshot is None
        or snapshot.manifest.dataset_id != DATASET_ID
        or snapshot.manifest.dataset_version != DATASET_VERSION
        or snapshot.manifest.case_count != 100
        or snapshot.manifest.schema_version != "dataset-manifest-v2"
        or snapshot.dataset_digest != DATASET_V3_DIGEST
        or snapshot.component_digests != DATASET_V3_COMPONENT_DIGESTS
    ):
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            f"qualification requires exact {DATASET_ID}@{DATASET_VERSION} bytes",
        )
    return snapshot


def _validate_historical_dataset(manifest_path: Path) -> DatasetBundleSnapshot:
    try:
        report = validate_dataset_bundle(manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            f"historical replay requires {DATASET_ID}@{HISTORICAL_DATASET_VERSION}",
        ) from exc
    snapshot = report.snapshot
    if (
        report.state != "VALID"
        or snapshot is None
        or snapshot.manifest.schema_version != "dataset-manifest-v1"
        or snapshot.manifest.dataset_id != DATASET_ID
        or snapshot.manifest.dataset_version != HISTORICAL_DATASET_VERSION
        or snapshot.dataset_digest != HISTORICAL_DATASET_DIGEST
    ):
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            f"historical replay requires exact {DATASET_ID}@{HISTORICAL_DATASET_VERSION} bytes",
        )
    return snapshot


def _dataset_manifest_path(version: Literal["2.0.0", "3.0.0"]) -> Path:
    filename = "dataset_manifest_v2.json" if version == "2.0.0" else "dataset_manifest_v3.json"
    repository_manifest = Path(__file__).resolve().parents[2] / "datasets" / filename
    if repository_manifest.is_file():
        return repository_manifest
    package_manifest = resources.files("braincrew").joinpath(
        "datasets",
        filename,
    )
    return Path(str(package_manifest))


def _validate_source_corpus_binding(
    *,
    sealed_dir: Path,
    validated: ValidatedCorpus,
    sealing_receipt_digest: str,
    snapshot: DatasetBundleSnapshot,
) -> None:
    binding = snapshot.manifest.source_corpus
    if binding is None:
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "successor dataset is missing its predecessor binding",
        )
    try:
        sealing_receipt = json.loads((sealed_dir / "sealing-receipt.json").read_text("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "sealed corpus receipt is unavailable",
        ) from exc
    observed = {
        "id": validated.manifest.corpus_id,
        "version": validated.manifest.corpus_version,
        "sealed_content_digest": validated.manifest.sealed_content_digest,
        "provenance_digest": sealing_receipt.get("provenance_digest"),
        "sealing_receipt_digest": sealing_receipt_digest,
    }
    if observed != binding.model_dump(mode="json"):
        raise CorpusQualificationError(
            "CORPUS_PACK_DIGEST_MISMATCH",
            "sealed corpus does not match the successor predecessor binding",
        )


def _qualification_receipt_payload(
    *,
    validated: ValidatedCorpus,
    sealing_receipt_digest: str,
    snapshot: DatasetBundleSnapshot,
    schema_version: Literal["corpus-qualification-receipt-v1", "corpus-qualification-receipt-v2"],
) -> dict[str, Any]:
    requirements = _dataset_requirements(snapshot)
    source_by_id = {source.source_id: source for source in validated.manifest.sources}
    blockers: list[tuple[str, str]] = []
    qualified_sources: list[dict[str, Any]] = []
    required_role_counts: dict[VisibilityRole, int] = {
        "Employee": 0,
        "Executive": 0,
        "HRPractitioner": 0,
        "HRAdmin": 0,
    }
    for source_id, requirement in sorted(requirements.items()):
        source = source_by_id.get(source_id)
        if source is None:
            blockers.append(("CORPUS_REQUIRED_SOURCE_MISSING", source_id))
            continue
        if (
            requirement.expected_content_sha256 is not None
            and source.content_sha256 != requirement.expected_content_sha256
        ):
            blockers.append(("CORPUS_SOURCE_TEXT_DIGEST_MISMATCH", source_id))
        visible_roles = set(source.visibility_scope.roles)
        missing_roles = requirement.required_roles - visible_roles
        exposed_roles = requirement.forbidden_roles & visible_roles
        if missing_roles:
            blockers.append(("CORPUS_REQUIRED_VISIBILITY_MISMATCH", source_id))
        if exposed_roles:
            blockers.append(("CORPUS_FORBIDDEN_VISIBILITY_MISMATCH", source_id))
        for role in requirement.required_roles:
            required_role_counts[role] += 1
        qualified_sources.append(
            {
                "source_id": source_id,
                "expected_content_sha256": requirement.expected_content_sha256,
                "observed_content_sha256": source.content_sha256,
                "required_roles": sorted(requirement.required_roles),
                "forbidden_roles": sorted(requirement.forbidden_roles),
            }
        )

    distractor_count = len(set(source_by_id) - set(requirements))
    if distractor_count == 0:
        blockers.append(("CORPUS_REQUIRED_SOURCE_MISSING", "distractor-source"))
    if blockers:
        code, identity = sorted(blockers)[0]
        raise CorpusQualificationError(code, f"qualification failed for {identity}")

    required_role_counts.pop("HRAdmin")
    payload: dict[str, Any] = {
        "schema_version": schema_version,
        "corpus": {
            "id": validated.manifest.corpus_id,
            "version": validated.manifest.corpus_version,
            "sealed_content_digest": validated.manifest.sealed_content_digest,
            "sealing_receipt_digest": sealing_receipt_digest,
        },
        "dataset": {
            "id": DATASET_ID,
            "version": snapshot.manifest.dataset_version,
            "content_digest": snapshot.dataset_digest,
            "component_digests": dict(sorted(snapshot.component_digests.items())),
            "case_count": len(snapshot.case_records),
        },
        "required_source_count": len(requirements),
        "distractor_source_count": distractor_count,
        "required_role_counts": required_role_counts,
        "sources": qualified_sources,
    }
    if schema_version == "corpus-qualification-receipt-v2":
        source_corpus = snapshot.manifest.source_corpus
        if source_corpus is None:
            raise CorpusQualificationError(
                "CORPUS_PACK_SCHEMA_INVALID",
                "successor dataset is missing its predecessor binding",
            )
        payload["corpus"]["provenance_digest"] = source_corpus.provenance_digest
    payload["receipt_digest"] = sha256_digest(canonical_json_bytes(payload))
    return payload


def _build_qualification_receipt_v1(
    *,
    validated: ValidatedCorpus,
    sealing_receipt_digest: str,
    snapshot: DatasetBundleSnapshot,
) -> CorpusQualificationReceiptV1:
    return CorpusQualificationReceiptV1.model_validate(
        _qualification_receipt_payload(
            validated=validated,
            sealing_receipt_digest=sealing_receipt_digest,
            snapshot=snapshot,
            schema_version="corpus-qualification-receipt-v1",
        )
    )


def _build_qualification_receipt_v2(
    *,
    validated: ValidatedCorpus,
    sealing_receipt_digest: str,
    snapshot: DatasetBundleSnapshot,
) -> CorpusQualificationReceiptV2:
    return CorpusQualificationReceiptV2.model_validate(
        _qualification_receipt_payload(
            validated=validated,
            sealing_receipt_digest=sealing_receipt_digest,
            snapshot=snapshot,
            schema_version="corpus-qualification-receipt-v2",
        )
    )


def _dataset_requirements(
    snapshot: DatasetBundleSnapshot,
) -> dict[str, _SourceRequirement]:
    requirements: dict[str, _SourceRequirement] = {}

    def add(
        source_id: str,
        *,
        expected_digest: str | None = None,
        required_role: VisibilityRole | None = None,
        forbidden_role: VisibilityRole | None = None,
    ) -> None:
        requirement = requirements.setdefault(
            source_id,
            _SourceRequirement(source_id=source_id),
        )
        if expected_digest is not None:
            if (
                requirement.expected_content_sha256 is not None
                and requirement.expected_content_sha256 != expected_digest
            ):
                raise CorpusQualificationError(
                    "CORPUS_PACK_SCHEMA_INVALID",
                    f"dataset freezes conflicting source digests for {source_id}",
                )
            requirement.expected_content_sha256 = expected_digest
        if required_role is not None:
            requirement.required_roles.add(required_role)
        if forbidden_role is not None:
            requirement.forbidden_roles.add(forbidden_role)

    parsing = snapshot.parsing_dataset.model_dump(mode="json")
    for case in parsing["cases"]:
        source_text = case["document"]["canonical_text"].encode("utf-8")
        add(
            case["document"]["id"],
            expected_digest=sha256_digest(source_text),
            required_role="HRPractitioner",
        )

    retrieval = snapshot.retrieval_dataset.model_dump(mode="json")
    for case in retrieval["cases"]:
        role = _qualification_role(case["role"])
        for group in case["expected"]["evidence_groups"]:
            for alternative in group["alternatives"]:
                add(
                    alternative["record_id"],
                    expected_digest=alternative.get("source_text_digest"),
                    required_role=role,
                )
        for forbidden in case["expected"]["forbidden_sources"]:
            add(forbidden["record_id"], forbidden_role=role)

    grounded = snapshot.grounded_dataset.model_dump(mode="json")
    for case in grounded["cases"]:
        role = _qualification_role(case["role"])
        forbidden = case["primary_focus"] == "visibility_abstention"
        for proposition in case["propositions"]:
            groups = (
                proposition["supporting_evidence_groups"]
                + proposition["contradicting_evidence_groups"]
            )
            for group in groups:
                for alternative in group["alternatives"]:
                    add(
                        alternative["record_id"],
                        expected_digest=alternative["source_text_digest"],
                        required_role=None if forbidden else role,
                        forbidden_role=role if forbidden else None,
                    )
    return requirements


def _qualification_role(raw_role: str) -> VisibilityRole:
    if raw_role == "Executive":
        return "Executive"
    if raw_role.casefold() == "employee":
        return "Employee"
    return "HRPractitioner"


def _build_import_manifest_payload(
    *,
    receipt: CorpusQualificationReceiptV1 | CorpusQualificationReceiptV2,
    qualification_receipt_digest: str,
    tenant_slug: str,
    demo_company_id: str,
    seed_version: Literal[
        "braincrew-evaluation-dataset-2.0.0", "braincrew-evaluation-dataset-3.0.0"
    ],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "ax-synthetic-seed-pack-v1",
        "corpus_id": receipt.corpus.id,
        "corpus_version": receipt.corpus.version,
        "seed_version": seed_version,
        "tenant_slug": tenant_slug,
        "demo_company_id": demo_company_id,
        "corpus_manifest_path": "corpus-manifest.json",
        "sealed_content_digest": receipt.corpus.sealed_content_digest,
        "qualification_receipt_path": QUALIFICATION_RECEIPT_NAME,
        "qualification_receipt_digest": qualification_receipt_digest,
        "normalization_contract_version": "ax-seed-normalization-v1",
        "chunking_contract_version": "ax-seed-chunking-v1",
    }
    payload["import_digest"] = sha256_digest(canonical_json_bytes(payload))
    return payload


def _build_import_manifest_v1(
    *,
    receipt: CorpusQualificationReceiptV1,
    qualification_receipt_digest: str,
    tenant_slug: str,
    demo_company_id: str,
) -> AxImportManifestV1:
    try:
        return AxImportManifestV1.model_validate(
            _build_import_manifest_payload(
                receipt=receipt,
                qualification_receipt_digest=qualification_receipt_digest,
                tenant_slug=tenant_slug,
                demo_company_id=demo_company_id,
                seed_version=HISTORICAL_SEED_VERSION,
            )
        )
    except ValidationError as exc:
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "AX import target identifiers are invalid",
        ) from exc


def _build_import_manifest_v2(
    *,
    receipt: CorpusQualificationReceiptV2,
    qualification_receipt_digest: str,
    tenant_slug: str,
    demo_company_id: str,
) -> AxImportManifestV2:
    try:
        return AxImportManifestV2.model_validate(
            _build_import_manifest_payload(
                receipt=receipt,
                qualification_receipt_digest=qualification_receipt_digest,
                tenant_slug=tenant_slug,
                demo_company_id=demo_company_id,
                seed_version=SEED_VERSION,
            )
        )
    except ValidationError as exc:
        raise CorpusQualificationError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "AX import target identifiers are invalid",
        ) from exc


def _read_canonical_model(
    path: Path,
    model: type[BaseModel],
    *,
    byte_policy: Literal["trailing-lf-required", "ax-import"],
    error_message: str,
) -> tuple[bytes, dict[str, Any]]:
    try:
        raw_bytes = path.read_bytes()
        payload = json.loads(raw_bytes.decode("utf-8"))
        validated = model.model_validate(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
        raise CorpusQualificationError("CORPUS_PACK_SCHEMA_INVALID", error_message) from exc
    canonical = canonical_json_bytes(validated.model_dump(mode="json"))
    accepted_bytes = (
        (canonical + b"\n",)
        if byte_policy == "trailing-lf-required"
        else (canonical, canonical + b"\n")
    )
    if raw_bytes not in accepted_bytes:
        raise CorpusQualificationError("CORPUS_PACK_DIGEST_MISMATCH", error_message)
    return raw_bytes, payload
