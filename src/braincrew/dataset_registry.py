"""Integrated 100-case dataset registry contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from braincrew.contracts import ParsingDatasetDocument, RetrievalDatasetDocument
from braincrew.digest import canonical_digest
from braincrew.grounded_contracts import GroundedDatasetDocument

Digest = str
PrimaryFocus = Literal[
    "parsing",
    "retrieval",
    "grounded_answer",
    "visibility_abstention",
]


class StrictDatasetContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DatasetComponentReference(StrictDatasetContract):
    path: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    content_digest: Digest = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class DatasetComponents(StrictDatasetContract):
    parsing: DatasetComponentReference
    retrieval: DatasetComponentReference
    grounded: DatasetComponentReference


class DatasetAllocation(StrictDatasetContract):
    parsing: Literal[20]
    retrieval: Literal[30]
    grounded_answer: Literal[40]
    visibility_abstention: Literal[10]


class DatasetSplitCounts(StrictDatasetContract):
    Calibration: Literal[70]
    Verification: Literal[30]


class VerificationDenominators(StrictDatasetContract):
    evidence_span_recovery: int = Field(ge=0)
    recall_at_5: int = Field(ge=0)
    claim_support_precision: int = Field(ge=0)
    citation_precision: int = Field(ge=0)
    answer_mode_accuracy: int = Field(ge=0)
    abstention_accuracy: int = Field(ge=0)


class MinimumVerificationDenominators(StrictDatasetContract):
    evidence_span_recovery: Literal[6]
    recall_at_5: Literal[9]
    claim_support_precision: Literal[10]
    citation_precision: Literal[10]
    answer_mode_accuracy: Literal[15]
    abstention_accuracy: Literal[5]


class DatasetProvenance(StrictDatasetContract):
    source_type: Literal["synthetic", "public"]
    license: str = Field(min_length=1)
    review_status: Literal["reviewed"]


class DatasetCardStatus(StrictDatasetContract):
    path: str = Field(min_length=1)
    provenance_status: Literal["complete"]
    license_status: Literal["approved"]


class DatasetRiskPolicy(StrictDatasetContract):
    parsing_default: Literal["standard"]
    retrieval_standard: Literal["standard"]
    retrieval_adversarial: Literal["high"]
    grounded_field: Literal["risk_level"]


class DatasetLeakagePolicy(StrictDatasetContract):
    duplicate_content: Literal["reject_across_splits"]
    banned_answer_keys: tuple[
        Literal[
            "reference_answer",
            "gold_answer",
            "answer_key",
            "expected_answer_text",
        ],
        ...,
    ]


class DatasetSourceCorpus(StrictDatasetContract):
    id: Literal["braincrew-independent-hr-corpus"]
    version: Literal["1.0.0"]
    sealed_content_digest: Digest = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    provenance_digest: Digest = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    sealing_receipt_digest: Digest = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class DatasetManifest(StrictDatasetContract):
    schema_version: Literal["dataset-manifest-v1", "dataset-manifest-v2"]
    dataset_id: Literal["braincrew-evaluation-dataset"]
    dataset_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    case_count: Literal[100]
    allocation: DatasetAllocation
    split_counts: DatasetSplitCounts
    minimum_verification_denominators: MinimumVerificationDenominators
    components: DatasetComponents
    provenance: DatasetProvenance
    dataset_card: DatasetCardStatus
    risk_policy: DatasetRiskPolicy
    leakage_policy: DatasetLeakagePolicy
    source_corpus: DatasetSourceCorpus | None = None
    content_digest: Digest = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def require_versioned_source_corpus(self) -> DatasetManifest:
        if self.schema_version == "dataset-manifest-v2" and self.source_corpus is None:
            raise ValueError("dataset-manifest-v2 requires source_corpus")
        if self.schema_version == "dataset-manifest-v1" and self.source_corpus is not None:
            raise ValueError("dataset-manifest-v1 forbids source_corpus")
        return self


class DatasetCaseRecord(StrictDatasetContract):
    case_id: str = Field(min_length=1)
    primary_focus: PrimaryFocus
    split: Literal["Calibration", "Verification"]
    risk_classification: Literal["standard", "high"]
    provenance_status: Literal["complete", "incomplete"]
    license: str = Field(min_length=1)
    scoring_digest: Digest = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class DatasetBundleSnapshot(StrictDatasetContract):
    manifest: DatasetManifest
    parsing_dataset: ParsingDatasetDocument
    retrieval_dataset: RetrievalDatasetDocument
    grounded_dataset: GroundedDatasetDocument
    case_records: tuple[DatasetCaseRecord, ...]
    component_digests: dict[str, Digest]
    verification_denominators: VerificationDenominators
    dataset_digest: Digest = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class DatasetViolation(StrictDatasetContract):
    code: str
    detail: str


class DatasetValidationReport(StrictDatasetContract):
    state: Literal["VALID", "INVALID"]
    violations: tuple[DatasetViolation, ...]
    snapshot: DatasetBundleSnapshot | None
    computed_component_digests: dict[str, Digest]
    computed_dataset_digest: Digest | None


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _bundle_path(manifest_path: Path, relative_path: str) -> Path:
    bundle_root = manifest_path.parent.resolve()
    requested_path = Path(relative_path)
    if requested_path.is_absolute():
        raise ValueError("bundle paths must be relative")
    resolved_path = (bundle_root / requested_path).resolve()
    if not resolved_path.is_relative_to(bundle_root):
        raise ValueError("bundle path resolves outside the dataset directory")
    return resolved_path


def _component_path(manifest_path: Path, reference: DatasetComponentReference) -> Path:
    return _bundle_path(manifest_path, reference.path)


def _case_scoring_digest(case_payload: dict[str, object]) -> Digest:
    scoring_payload = {
        key: value
        for key, value in case_payload.items()
        if key not in {"id", "case_id", "split", "provenance", "review"}
    }
    return canonical_digest(scoring_payload)


def _build_case_records(
    parsing: ParsingDatasetDocument,
    retrieval: RetrievalDatasetDocument,
    grounded: GroundedDatasetDocument,
) -> tuple[DatasetCaseRecord, ...]:
    records: list[DatasetCaseRecord] = []
    for parsing_case in parsing.cases:
        records.append(
            DatasetCaseRecord(
                case_id=parsing_case.id,
                primary_focus="parsing",
                split=("Calibration" if parsing_case.split == "calibration" else "Verification"),
                risk_classification="standard",
                provenance_status="complete",
                license=parsing_case.provenance.license,
                scoring_digest=_case_scoring_digest(parsing_case.model_dump(mode="json")),
            )
        )
    for retrieval_case in retrieval.cases:
        records.append(
            DatasetCaseRecord(
                case_id=retrieval_case.id,
                primary_focus="retrieval",
                split=("Calibration" if retrieval_case.split == "calibration" else "Verification"),
                risk_classification=(
                    "high" if retrieval_case.difficulty == "adversarial" else "standard"
                ),
                provenance_status="complete",
                license=retrieval_case.provenance.license,
                scoring_digest=_case_scoring_digest(retrieval_case.model_dump(mode="json")),
            )
        )
    for grounded_case in grounded.cases:
        records.append(
            DatasetCaseRecord(
                case_id=grounded_case.case_id,
                primary_focus=grounded_case.primary_focus,
                split=grounded_case.split,
                risk_classification=grounded_case.risk_level,
                provenance_status=(
                    "complete"
                    if grounded.provenance.review_status in {"reviewed", "frozen"}
                    else "incomplete"
                ),
                license=grounded.provenance.license,
                scoring_digest=_case_scoring_digest(grounded_case.model_dump(mode="json")),
            )
        )
    return tuple(records)


def _verification_denominators(
    parsing: ParsingDatasetDocument,
    retrieval: RetrievalDatasetDocument,
    grounded: GroundedDatasetDocument,
) -> VerificationDenominators:
    parsing_cases = [case for case in parsing.cases if case.split == "verification"]
    retrieval_cases = [case for case in retrieval.cases if case.split == "verification"]
    grounded_cases = [case for case in grounded.cases if case.split == "Verification"]
    return VerificationDenominators(
        evidence_span_recovery=sum(bool(case.expected.evidence_spans) for case in parsing_cases),
        recall_at_5=sum(
            case.applicability.recall_at_5 and case.expected.source_identity_status == "resolved"
            for case in retrieval_cases
        ),
        claim_support_precision=sum(
            case.applicability.claim_support_precision for case in grounded_cases
        ),
        citation_precision=sum(case.applicability.citation_precision for case in grounded_cases),
        answer_mode_accuracy=sum(
            case.applicability.answer_mode_accuracy for case in grounded_cases
        ),
        abstention_accuracy=sum(case.applicability.abstention_accuracy for case in grounded_cases),
    )


def _dataset_digest_payload(
    manifest: DatasetManifest,
    parsing: ParsingDatasetDocument,
    retrieval: RetrievalDatasetDocument,
    grounded: GroundedDatasetDocument,
) -> dict[str, object]:
    manifest_payload = manifest.model_dump(mode="json")
    manifest_payload.pop("content_digest")
    if manifest.source_corpus is None:
        manifest_payload.pop("source_corpus")
    components = cast(dict[str, dict[str, object]], manifest_payload["components"])
    for component in components.values():
        component.pop("content_digest")
    return {
        "manifest": manifest_payload,
        "components": {
            "parsing": parsing.model_dump(mode="json"),
            "retrieval": retrieval.model_dump(mode="json"),
            "grounded": grounded.model_dump(mode="json"),
        },
    }


def _violation(code: str, detail: str) -> DatasetViolation:
    return DatasetViolation(code=code, detail=detail)


def _invalid_report(
    violations: list[DatasetViolation],
    *,
    component_digests: dict[str, Digest] | None = None,
    dataset_digest: Digest | None = None,
) -> DatasetValidationReport:
    unique = tuple(
        DatasetViolation(code=code, detail=detail)
        for code, detail in dict.fromkeys((item.code, item.detail) for item in violations)
    )
    return DatasetValidationReport(
        state="INVALID",
        violations=unique,
        snapshot=None,
        computed_component_digests=component_digests or {},
        computed_dataset_digest=dataset_digest,
    )


def _manifest_validation_code(error: ValidationError) -> str:
    locations = {str(part) for item in error.errors() for part in item["loc"]}
    if "risk_policy" in locations:
        return "RISK_CLASSIFICATION_INVALID"
    if "provenance" in locations:
        return "PROVENANCE_MISSING"
    return "SCHEMA_INVALID"


def _component_schema_code(error: ValidationError) -> str:
    message = str(error)
    if "case IDs must be unique" in message or "case identities must be unique" in message:
        return "DUPLICATE_CASE_ID"
    if "frozen split" in message or "calibration and" in message:
        return "SPLIT_DRIFT"
    if ".provenance" in message or "Field required" in message and "provenance" in message:
        return "PROVENANCE_MISSING"
    return "SCHEMA_INVALID"


def _contains_banned_answer_key(value: object, banned_keys: set[str]) -> bool:
    if isinstance(value, dict):
        return any(
            key in banned_keys or _contains_banned_answer_key(item, banned_keys)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_banned_answer_key(item, banned_keys) for item in value)
    return False


def _normalized_leakage_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _grounded_answer_is_leaked(grounded: GroundedDatasetDocument) -> bool:
    for case in grounded.cases:
        normalized_query = _normalized_leakage_text(case.query)
        for proposition in case.propositions:
            for matcher in proposition.surface_matchers:
                if matcher.kind != "literal":
                    continue
                pattern = _normalized_leakage_text(matcher.pattern)
                if pattern and pattern in normalized_query:
                    return True
    return False


def _all_cases_have_required_focus_applicability(
    retrieval: RetrievalDatasetDocument,
    grounded: GroundedDatasetDocument,
) -> bool:
    retrieval_cases_are_applicable = all(
        case.applicability.recall_at_5 and case.applicability.mrr_at_10 for case in retrieval.cases
    )
    grounded_cases_are_applicable = all(
        (
            case.applicability.claim_support_precision
            and case.applicability.citation_precision
            and case.applicability.citation_coverage
            and case.applicability.answer_mode_accuracy
        )
        if case.primary_focus == "grounded_answer"
        else (case.applicability.answer_mode_accuracy and case.applicability.abstention_accuracy)
        for case in grounded.cases
    )
    return retrieval_cases_are_applicable and grounded_cases_are_applicable


def _bundle_reference_is_safe(relative_path: str) -> bool:
    requested_path = Path(relative_path)
    return not requested_path.is_absolute() and ".." not in requested_path.parts


def _raw_component_violations(
    component_name: str,
    payload: object,
    banned_answer_keys: set[str],
) -> list[DatasetViolation]:
    if not isinstance(payload, dict):
        return [_violation("SCHEMA_INVALID", f"{component_name} component must be an object")]
    violations: list[DatasetViolation] = []
    if _contains_banned_answer_key(payload, banned_answer_keys):
        violations.append(
            _violation("ANSWER_LEAKAGE", f"{component_name} contains a banned free-text answer key")
        )
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        violations.append(
            _violation("PROVENANCE_MISSING", f"{component_name} provenance is missing")
        )
    elif provenance.get("license") != "CC0-1.0":
        violations.append(
            _violation("LICENSE_INVALID", f"{component_name} license is not approved")
        )
    cases = payload.get("cases")
    if not isinstance(cases, list):
        violations.append(_violation("SCHEMA_INVALID", f"{component_name} cases are missing"))
        return violations
    if component_name in {"parsing", "retrieval"}:
        for index, case in enumerate(cases):
            if not isinstance(case, dict) or not isinstance(case.get("provenance"), dict):
                violations.append(
                    _violation(
                        "PROVENANCE_MISSING",
                        f"{component_name} case {index} provenance is missing",
                    )
                )
                continue
            if cast(dict[str, object], case["provenance"]).get("license") != "CC0-1.0":
                violations.append(
                    _violation(
                        "LICENSE_INVALID",
                        f"{component_name} case {index} license is not approved",
                    )
                )
    return violations


def _has_cross_split_leakage(records: tuple[DatasetCaseRecord, ...]) -> bool:
    splits_by_digest: dict[Digest, set[str]] = {}
    for record in records:
        splits_by_digest.setdefault(record.scoring_digest, set()).add(record.split)
    return any(len(splits) > 1 for splits in splits_by_digest.values())


def _has_duplicate_content(records: tuple[DatasetCaseRecord, ...]) -> bool:
    digests = [record.scoring_digest for record in records]
    return len(digests) != len(set(digests))


def _case_identities_are_stable(records: tuple[DatasetCaseRecord, ...]) -> bool:
    patterns = {
        "parsing": re.compile(r"parsing-[0-9]{3}\Z"),
        "retrieval": re.compile(r"retrieval-[0-9]{3}\Z"),
        "grounded_answer": re.compile(r"GA-[0-9]{3}\Z"),
        "visibility_abstention": re.compile(r"VA-[0-9]{3}\Z"),
    }
    return all(patterns[record.primary_focus].fullmatch(record.case_id) for record in records)


def _denominators_satisfy_minimum(
    actual: VerificationDenominators,
    minimum: MinimumVerificationDenominators,
) -> bool:
    actual_values = actual.model_dump()
    minimum_values = minimum.model_dump()
    return all(actual_values[name] >= required for name, required in minimum_values.items())


def validate_dataset_snapshot(snapshot: DatasetBundleSnapshot) -> DatasetValidationReport:
    manifest = snapshot.manifest
    parsing = snapshot.parsing_dataset
    retrieval = snapshot.retrieval_dataset
    grounded = snapshot.grounded_dataset
    normalized_components = {
        "parsing": parsing.model_dump(mode="json"),
        "retrieval": retrieval.model_dump(mode="json"),
        "grounded": grounded.model_dump(mode="json"),
    }
    component_digests = {
        name: canonical_digest(payload) for name, payload in normalized_components.items()
    }
    dataset_digest = canonical_digest(
        _dataset_digest_payload(manifest, parsing, retrieval, grounded)
    )
    records = _build_case_records(parsing, retrieval, grounded)
    denominators = _verification_denominators(parsing, retrieval, grounded)
    expected_component_digests = {
        "parsing": manifest.components.parsing.content_digest,
        "retrieval": manifest.components.retrieval.content_digest,
        "grounded": manifest.components.grounded.content_digest,
    }
    violations: list[DatasetViolation] = []
    expected_schema_versions = {
        "parsing": "parsing-dataset-v1",
        "retrieval": "retrieval-dataset-v1",
        "grounded": "grounded-dataset-v1",
    }
    references = {
        "parsing": manifest.components.parsing,
        "retrieval": manifest.components.retrieval,
        "grounded": manifest.components.grounded,
    }
    for name, reference in references.items():
        if not _bundle_reference_is_safe(reference.path):
            violations.append(
                _violation(
                    "COMPONENT_PATH_INVALID",
                    f"{name}: component path is not confined to the dataset bundle",
                )
            )
        if reference.schema_version != expected_schema_versions[name]:
            violations.append(
                _violation(
                    "SCHEMA_INVALID",
                    f"{name}: manifest component schema version is incorrect",
                )
            )
    licenses = {
        manifest.provenance.license,
        parsing.provenance.license,
        retrieval.provenance.license,
        grounded.provenance.license,
        *(case.provenance.license for case in parsing.cases),
        *(case.provenance.license for case in retrieval.cases),
    }
    if licenses != {"CC0-1.0"}:
        violations.append(_violation("LICENSE_INVALID", "dataset license is not approved"))
    source_types = {
        parsing.provenance.source_type,
        retrieval.provenance.source_type,
        grounded.provenance.source_kind,
        *(case.provenance.source_type for case in parsing.cases),
        *(case.provenance.source_type for case in retrieval.cases),
    }
    if source_types != {manifest.provenance.source_type}:
        violations.append(
            _violation(
                "PROVENANCE_INCONSISTENT",
                "component and case source types must match the integrated provenance declaration",
            )
        )
    if component_digests != expected_component_digests or (
        snapshot.component_digests != component_digests
    ):
        violations.append(
            _violation(
                "COMPONENT_DIGEST_MISMATCH",
                "snapshot component digest does not reproduce the frozen manifest",
            )
        )
    if dataset_digest != manifest.content_digest or snapshot.dataset_digest != dataset_digest:
        violations.append(
            _violation(
                "DATASET_DIGEST_MISMATCH",
                "snapshot dataset digest does not reproduce the frozen manifest",
            )
        )
    if snapshot.case_records != records:
        violations.append(
            _violation("CASE_IDENTITY_MISMATCH", "snapshot case registry does not reproduce")
        )
    if any(record.provenance_status != "complete" for record in records):
        violations.append(
            _violation("PROVENANCE_INCOMPLETE", "dataset provenance review is incomplete")
        )
    case_ids = [record.case_id for record in records]
    if len(case_ids) != len(set(case_ids)):
        violations.append(
            _violation("DUPLICATE_CASE_ID", "case identities are not globally unique")
        )
    if not _case_identities_are_stable(records):
        violations.append(
            _violation("CASE_IDENTITY_INVALID", "snapshot contains an unstable case identity")
        )
    if _has_duplicate_content(records):
        violations.append(
            _violation("DUPLICATE_CASE_CONTENT", "snapshot contains duplicate scoring content")
        )
    actual_allocation = {
        focus: sum(record.primary_focus == focus for record in records)
        for focus in ("parsing", "retrieval", "grounded_answer", "visibility_abstention")
    }
    if actual_allocation != manifest.allocation.model_dump():
        violations.append(
            _violation("COUNT_ALLOCATION_INVALID", "primary-focus allocation drifted")
        )
    actual_splits = {
        split: sum(record.split == split for record in records)
        for split in ("Calibration", "Verification")
    }
    if actual_splits != manifest.split_counts.model_dump():
        violations.append(_violation("SPLIT_DRIFT", "Calibration/Verification allocation drifted"))
    if snapshot.verification_denominators != denominators or not _denominators_satisfy_minimum(
        denominators,
        manifest.minimum_verification_denominators,
    ):
        violations.append(
            _violation(
                "METRIC_APPLICABILITY_INSUFFICIENT",
                "snapshot Verification denominator does not reproduce the frozen minimum",
            )
        )
    if not _all_cases_have_required_focus_applicability(retrieval, grounded):
        violations.append(
            _violation(
                "METRIC_APPLICABILITY_INSUFFICIENT",
                "every dataset case must apply the complete metric family "
                "required by its primary focus",
            )
        )
    if _grounded_answer_is_leaked(grounded):
        violations.append(
            _violation("ANSWER_LEAKAGE", "grounded query contains an expected answer literal")
        )
    if _has_cross_split_leakage(records):
        violations.append(
            _violation(
                "CALIBRATION_VERIFICATION_LEAKAGE",
                "snapshot contains scoring-equivalent content in both splits",
            )
        )
    if violations:
        return _invalid_report(
            violations,
            component_digests=component_digests,
            dataset_digest=dataset_digest,
        )
    return DatasetValidationReport(
        state="VALID",
        violations=(),
        snapshot=DatasetBundleSnapshot(
            manifest=manifest,
            parsing_dataset=parsing,
            retrieval_dataset=retrieval,
            grounded_dataset=grounded,
            case_records=records,
            component_digests=component_digests,
            verification_denominators=denominators,
            dataset_digest=dataset_digest,
        ),
        computed_component_digests=component_digests,
        computed_dataset_digest=dataset_digest,
    )


def validate_dataset_bundle(manifest_path: Path) -> DatasetValidationReport:
    try:
        manifest_raw = _read_json(manifest_path)
        manifest = DatasetManifest.model_validate(manifest_raw)
    except (OSError, json.JSONDecodeError) as error:
        return _invalid_report([_violation("MANIFEST_MISSING", str(error))])
    except ValidationError as error:
        return _invalid_report([_violation(_manifest_validation_code(error), str(error))])

    violations: list[DatasetViolation] = []
    try:
        dataset_card_path = _bundle_path(manifest_path, manifest.dataset_card.path)
    except ValueError:
        dataset_card_path = None
    if dataset_card_path is None or not dataset_card_path.is_file():
        violations.append(
            _violation("DATASET_CARD_MISSING", "dataset card is missing from the bundle")
        )
    banned_answer_keys: set[str] = set(manifest.leakage_policy.banned_answer_keys)
    component_models: dict[str, object] = {}
    references = {
        "parsing": manifest.components.parsing,
        "retrieval": manifest.components.retrieval,
        "grounded": manifest.components.grounded,
    }
    model_types: dict[str, type[BaseModel]] = {
        "parsing": ParsingDatasetDocument,
        "retrieval": RetrievalDatasetDocument,
        "grounded": GroundedDatasetDocument,
    }
    for name, reference in references.items():
        try:
            path = _component_path(manifest_path, reference)
        except ValueError as error:
            violations.append(_violation("COMPONENT_PATH_INVALID", f"{name}: {error}"))
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError) as error:
            violations.append(_violation("COMPONENT_MISSING", f"{name}: {error}"))
            continue
        violations.extend(_raw_component_violations(name, payload, banned_answer_keys))
        try:
            component_models[name] = model_types[name].model_validate(payload)
        except ValidationError as error:
            violations.append(_violation(_component_schema_code(error), f"{name}: {error}"))

    if len(component_models) != 3:
        return _invalid_report(violations)

    parsing = cast(ParsingDatasetDocument, component_models["parsing"])
    retrieval = cast(RetrievalDatasetDocument, component_models["retrieval"])
    grounded = cast(GroundedDatasetDocument, component_models["grounded"])
    normalized_components = {
        "parsing": parsing.model_dump(mode="json"),
        "retrieval": retrieval.model_dump(mode="json"),
        "grounded": grounded.model_dump(mode="json"),
    }
    component_digests = {
        name: canonical_digest(payload) for name, payload in normalized_components.items()
    }
    dataset_digest = canonical_digest(
        _dataset_digest_payload(manifest, parsing, retrieval, grounded)
    )
    records = _build_case_records(parsing, retrieval, grounded)
    denominators = _verification_denominators(parsing, retrieval, grounded)
    candidate_snapshot = DatasetBundleSnapshot(
        manifest=manifest,
        parsing_dataset=parsing,
        retrieval_dataset=retrieval,
        grounded_dataset=grounded,
        case_records=records,
        component_digests=component_digests,
        verification_denominators=denominators,
        dataset_digest=dataset_digest,
    )
    snapshot_report = validate_dataset_snapshot(candidate_snapshot)
    violations.extend(snapshot_report.violations)
    if violations:
        return _invalid_report(
            violations,
            component_digests=component_digests,
            dataset_digest=dataset_digest,
        )
    return snapshot_report
