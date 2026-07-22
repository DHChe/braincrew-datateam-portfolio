from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, cast

from .corpus_pack_v1_fixture import (
    canonical_json_bytes as canonical_json_bytes,
)
from .corpus_pack_v1_fixture import (
    corpus_manifest,
    source_descriptor,
    write_manifest,
    write_provenance_sidecar,
)
from .corpus_pack_v1_fixture import (
    run_cli as run_cli,
)
from .corpus_pack_v1_fixture import (
    sha256_digest as sha256_digest,
)

REPOSITORY_ROOT = Path(__file__).parents[1]
DATASET_V1_MANIFEST = REPOSITORY_ROOT / "datasets" / "dataset_manifest_v1.json"
DATASET_V2_MANIFEST = REPOSITORY_ROOT / "datasets" / "dataset_manifest_v2.json"
DATASET_ID = "braincrew-evaluation-dataset"
DATASET_VERSION = "2.0.0"
SEED_VERSION = "braincrew-evaluation-dataset-2.0.0"
ROLE_ORDER = ("Employee", "Executive", "HRPractitioner")


def _read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def stage_dataset_v2_bundle(directory: Path) -> Path:
    directory.mkdir(parents=True)
    manifest = _read_json(DATASET_V2_MANIFEST)
    for relative_path in (
        manifest["dataset_card"]["path"],
        manifest["components"]["parsing"]["path"],
        manifest["components"]["retrieval"]["path"],
        manifest["components"]["grounded"]["path"],
    ):
        source = DATASET_V1_MANIFEST.parent / relative_path
        destination = directory / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    manifest_path = directory / "dataset_manifest_v2.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _qualification_role(raw_role: str) -> str:
    if raw_role == "Executive":
        return "Executive"
    if raw_role.casefold() == "employee":
        return "Employee"
    return "HRPractitioner"


def _requirements() -> dict[str, dict[str, Any]]:
    parsing = _read_json(REPOSITORY_ROOT / "datasets/parsing/parsing_cases_v1.json")
    retrieval = _read_json(REPOSITORY_ROOT / "datasets/retrieval/retrieval_cases_v1.json")
    grounded = _read_json(REPOSITORY_ROOT / "datasets/grounded/grounded_cases_v1.json")
    grounded_observations = _read_json(
        REPOSITORY_ROOT / "tests/fixtures/grounded_observations_v1.json"
    )
    observed_source_texts = {
        (source["record_id"], source["source_text_digest"]): source["text"]
        for observation in grounded_observations["observations"]
        for source in observation["source_texts"]
    }
    requirements: dict[str, dict[str, Any]] = {}

    def add(
        source_id: str,
        *,
        source_bytes: bytes | None = None,
        required_role: str | None = None,
        forbidden_role: str | None = None,
        source_class: str = "company_rule",
    ) -> None:
        requirement = requirements.setdefault(
            source_id,
            {
                "source_bytes": None,
                "required_roles": set(),
                "forbidden_roles": set(),
                "source_class": source_class,
            },
        )
        if source_bytes is not None:
            prior = requirement["source_bytes"]
            assert prior is None or prior == source_bytes, source_id
            requirement["source_bytes"] = source_bytes
        if required_role is not None:
            requirement["required_roles"].add(required_role)
        if forbidden_role is not None:
            requirement["forbidden_roles"].add(forbidden_role)
        if source_class == "company_reference":
            requirement["source_class"] = source_class

    for case in parsing["cases"]:
        add(
            case["document"]["id"],
            source_bytes=case["document"]["canonical_text"].encode("utf-8"),
            required_role="HRPractitioner",
        )

    for case in retrieval["cases"]:
        role = _qualification_role(case["role"])
        for group in case["expected"]["evidence_groups"]:
            for alternative in group["alternatives"]:
                add(
                    alternative["record_id"],
                    required_role=role,
                    source_class=(
                        "company_reference"
                        if alternative["record_kind"] == "labor_law"
                        else "company_rule"
                    ),
                )
        for forbidden in case["expected"]["forbidden_sources"]:
            add(forbidden["record_id"], forbidden_role=role)

    for case in grounded["cases"]:
        role = _qualification_role(case["role"])
        role_forbidden = case["primary_focus"] == "visibility_abstention"
        for proposition in case["propositions"]:
            groups = (
                proposition["supporting_evidence_groups"]
                + proposition["contradicting_evidence_groups"]
            )
            for group in groups:
                for alternative in group["alternatives"]:
                    source_key = (
                        alternative["record_id"],
                        alternative["source_text_digest"],
                    )
                    source_text = observed_source_texts.get(source_key)
                    if source_text is None and alternative["record_id"] == "rule-30":
                        source_text = f"제30조: {alternative['source_matcher']['pattern']}."
                    if source_text is None and alternative["record_id"].startswith("rule-va-"):
                        source_text = (
                            f"접근 제한 합성 규정: {alternative['source_matcher']['pattern']}."
                        )
                    assert source_text is not None, alternative["record_id"]
                    source_bytes = source_text.encode("utf-8")
                    assert sha256_digest(source_bytes) == alternative["source_text_digest"]
                    add(
                        alternative["record_id"],
                        source_bytes=source_bytes,
                        required_role=None if role_forbidden else role,
                        forbidden_role=role if role_forbidden else None,
                        source_class=(
                            "company_reference"
                            if alternative["record_kind"] == "labor_law"
                            else "company_rule"
                        ),
                    )
    return requirements


def stage_qualification_pack(
    staging_dir: Path,
    *,
    omit_source_id: str | None = None,
    mismatched_source_id: str | None = None,
    missing_required_role: tuple[str, str] | None = None,
    exposed_forbidden_role: tuple[str, str] | None = None,
    include_distractor: bool = True,
) -> dict[str, Any]:
    requirements = _requirements()
    if include_distractor:
        requirements["synthetic-distractor-001"] = {
            "source_bytes": b"Independent synthetic distractor.\n",
            "required_roles": {"Employee"},
            "forbidden_roles": set(),
            "source_class": "company_reference",
        }
    staging_dir.mkdir(parents=True)
    descriptors: list[dict[str, Any]] = []
    for source_id, requirement in sorted(requirements.items()):
        if source_id == omit_source_id:
            continue
        source_bytes = requirement["source_bytes"] or f"Synthetic source {source_id}.\n".encode()
        if source_id == mismatched_source_id:
            source_bytes += b"Changed after dataset freeze.\n"
        forbidden_roles = set(requirement["forbidden_roles"])
        roles = set(requirement["required_roles"])
        if missing_required_role is not None and source_id == missing_required_role[0]:
            roles.discard(missing_required_role[1])
        if exposed_forbidden_role is not None and source_id == exposed_forbidden_role[0]:
            roles.add(exposed_forbidden_role[1])
        if not roles:
            roles.add(next(role for role in ROLE_ORDER if role not in forbidden_roles))
        relative_path = f"sources/{source_id}.md"
        source_path = staging_dir / relative_path
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(source_bytes)
        descriptor = source_descriptor(
            source_id=source_id,
            path=relative_path,
            source_bytes=source_bytes,
        )
        descriptor["source_class"] = requirement["source_class"]
        descriptor["visibility_scope"] = {"roles": [role for role in ROLE_ORDER if role in roles]}
        descriptors.append(descriptor)
    payload = corpus_manifest(descriptors, corpus_version="2.0.0")
    write_manifest(staging_dir, payload)
    return payload


def seal_qualification_pack(staging_dir: Path, output_root: Path) -> Path:
    manifest = _read_json(staging_dir / "corpus-manifest.json")
    provenance_sidecar = write_provenance_sidecar(
        output_root.parent / f"{staging_dir.name}-provenance-review.json",
        manifest,
    )
    result = run_cli(
        "seal-corpus",
        "--staging-dir",
        str(staging_dir),
        "--output-root",
        str(output_root),
        "--provenance-sidecar",
        str(provenance_sidecar),
    )
    assert result.returncode == 0, result.stderr
    return Path(json.loads(result.stdout)["receipt_path"]).parent


def rewrite_manifest(sealed_dir: Path, mutate: Any) -> None:
    manifest_path = sealed_dir / "corpus-manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    mutate(payload)
    write_manifest(sealed_dir, payload)


def qualification_command(sealed_dir: Path, dataset_manifest: Path) -> tuple[str, ...]:
    return (
        "qualify-corpus",
        "--sealed-dir",
        str(sealed_dir),
        "--dataset-manifest",
        str(dataset_manifest),
        "--tenant-slug",
        "braincrew-demo-tenant",
        "--demo-company-id",
        "braincrew-demo-company",
    )


def import_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("import_digest")
    return sha256_digest(canonical_json_bytes(digest_payload))
