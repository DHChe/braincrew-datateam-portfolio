from __future__ import annotations

import importlib.util
import json
import shutil
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

from braincrew import dataset_registry
from braincrew.contracts import ParsingDatasetDocument
from braincrew.digest import canonical_digest

MANIFEST_PATH = Path(__file__).parents[2] / "datasets" / "dataset_manifest_v1.json"


def read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def copy_bundle(tmp_path: Path) -> Path:
    bundle_dir = tmp_path / "datasets"
    shutil.copytree(MANIFEST_PATH.parent, bundle_dir)
    return bundle_dir / MANIFEST_PATH.name


def rehash_snapshot(
    snapshot: dataset_registry.DatasetBundleSnapshot,
    *,
    manifest: dataset_registry.DatasetManifest | None = None,
    parsing: dataset_registry.ParsingDataset | None = None,
    retrieval: dataset_registry.RetrievalDataset | None = None,
    grounded: dataset_registry.GroundedDataset | None = None,
) -> dataset_registry.DatasetBundleSnapshot:
    parsing = parsing if parsing is not None else snapshot.parsing_dataset
    retrieval = retrieval if retrieval is not None else snapshot.retrieval_dataset
    grounded = grounded if grounded is not None else snapshot.grounded_dataset
    manifest = manifest if manifest is not None else snapshot.manifest
    component_digests = {
        "parsing": canonical_digest(parsing.model_dump(mode="json")),
        "retrieval": canonical_digest(retrieval.model_dump(mode="json")),
        "grounded": canonical_digest(grounded.model_dump(mode="json")),
    }
    components = manifest.components.model_copy(
        update={
            "parsing": manifest.components.parsing.model_copy(
                update={"content_digest": component_digests["parsing"]}
            ),
            "retrieval": manifest.components.retrieval.model_copy(
                update={"content_digest": component_digests["retrieval"]}
            ),
            "grounded": manifest.components.grounded.model_copy(
                update={"content_digest": component_digests["grounded"]}
            ),
        }
    )
    manifest = manifest.model_copy(update={"components": components})
    dataset_digest = canonical_digest(
        dataset_registry._dataset_digest_payload(manifest, parsing, retrieval, grounded)
    )
    manifest = manifest.model_copy(update={"content_digest": dataset_digest})
    return dataset_registry.DatasetBundleSnapshot(
        manifest=manifest,
        parsing_dataset=parsing,
        retrieval_dataset=retrieval,
        grounded_dataset=grounded,
        case_records=dataset_registry._build_case_records(parsing, retrieval, grounded),
        component_digests=component_digests,
        verification_denominators=dataset_registry._verification_denominators(
            parsing, retrieval, grounded
        ),
        dataset_digest=dataset_digest,
    )


def component_path(manifest_path: Path, name: str) -> Path:
    manifest = read_json(manifest_path)
    components = cast(dict[str, dict[str, object]], manifest["components"])
    return manifest_path.parent / str(components[name]["path"])


def mutate_component(
    manifest_path: Path,
    name: str,
    mutation: Callable[[dict[str, object]], None],
) -> None:
    path = component_path(manifest_path, name)
    payload = read_json(path)
    mutation(payload)
    write_json(path, payload)


def missing_component(manifest_path: Path) -> None:
    component_path(manifest_path, "parsing").unlink()


def escape_component_bundle(manifest_path: Path) -> None:
    manifest = read_json(manifest_path)
    components = cast(dict[str, dict[str, object]], manifest["components"])
    parsing_path = component_path(manifest_path, "parsing")
    escaped_path = manifest_path.parent.parent / "escaped-parsing.json"
    shutil.copyfile(parsing_path, escaped_path)
    components["parsing"]["path"] = "../escaped-parsing.json"
    write_json(manifest_path, manifest)


def misdeclare_component_schema(manifest_path: Path) -> None:
    manifest = read_json(manifest_path)
    components = cast(dict[str, dict[str, object]], manifest["components"])
    components["parsing"]["schema_version"] = "retrieval-dataset-v1"
    write_json(manifest_path, manifest)


def missing_dataset_card(manifest_path: Path) -> None:
    manifest = read_json(manifest_path)
    dataset_card = cast(dict[str, object], manifest["dataset_card"])
    (manifest_path.parent / cast(str, dataset_card["path"])).unlink()


def duplicate_case_identity(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        cases[1]["id"] = cases[0]["id"]

    mutate_component(manifest_path, "parsing", mutation)


def invalidate_case_identity(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        cases[0]["id"] = "unstable-case-id"

    mutate_component(manifest_path, "parsing", mutation)


def duplicate_case_content(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        second_id = cases[1]["id"]
        cases[1] = json.loads(json.dumps(cases[0]))
        cases[1]["id"] = second_id

    mutate_component(manifest_path, "parsing", mutation)


def drift_split(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        cases[0]["split"] = "verification"

    mutate_component(manifest_path, "parsing", mutation)


def break_component_schema(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        cases[0]["unexpected"] = True

    mutate_component(manifest_path, "retrieval", mutation)


def remove_case_provenance(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        del cases[0]["provenance"]

    mutate_component(manifest_path, "retrieval", mutation)


def invalidate_license(manifest_path: Path) -> None:
    manifest = read_json(manifest_path)
    provenance = cast(dict[str, object], manifest["provenance"])
    provenance["license"] = "UNLICENSED"
    write_json(manifest_path, manifest)


def invalidate_risk_policy(manifest_path: Path) -> None:
    manifest = read_json(manifest_path)
    policy = cast(dict[str, object], manifest["risk_policy"])
    policy["parsing_default"] = "high"
    write_json(manifest_path, manifest)


def reduce_verification_applicability(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        applicability = cast(dict[str, object], cases[0]["applicability"])
        applicability["claim_support_precision"] = False

    mutate_component(manifest_path, "grounded", mutation)


def leak_case_across_splits(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        verification_id = cases[14]["id"]
        cases[14] = json.loads(json.dumps(cases[0]))
        cases[14]["id"] = verification_id
        cases[14]["split"] = "verification"

    mutate_component(manifest_path, "parsing", mutation)


def leak_reference_answer(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        cases[0]["reference_answer"] = "금지된 자유서술 정답"

    mutate_component(manifest_path, "grounded", mutation)


def leak_answer_literal_into_query(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        propositions = cast(list[dict[str, object]], cases[0]["propositions"])
        surface_matchers = cast(list[dict[str, object]], propositions[0]["surface_matchers"])
        cases[0]["query"] = f"{cases[0]['query']} {surface_matchers[0]['pattern']}"

    mutate_component(manifest_path, "grounded", mutation)


def remove_all_case_applicability(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        applicability = cast(dict[str, object], cases[10]["applicability"])
        for metric in applicability:
            applicability[metric] = False

    mutate_component(manifest_path, "grounded", mutation)


def remove_focus_specific_applicability(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        visibility_case = next(
            case for case in cases if case["primary_focus"] == "visibility_abstention"
        )
        applicability = cast(dict[str, object], visibility_case["applicability"])
        applicability["abstention_accuracy"] = False

    mutate_component(manifest_path, "grounded", mutation)


def downgrade_grounded_provenance(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        provenance = cast(dict[str, object], payload["provenance"])
        provenance["review_status"] = "draft"

    mutate_component(manifest_path, "grounded", mutation)


def change_scoring_content(manifest_path: Path) -> None:
    def mutation(payload: dict[str, object]) -> None:
        cases = cast(list[dict[str, object]], payload["cases"])
        cases[0]["query"] = f"{cases[0]['query']} 변경"

    mutate_component(manifest_path, "retrieval", mutation)


def test_dataset_registry_contract_surface_exists() -> None:
    assert importlib.util.find_spec("braincrew.dataset_registry") is not None, (
        "Issue #12 must provide the integrated dataset registry contract"
    )


def test_integrated_manifest_freezes_exact_case_split_and_metric_contracts() -> None:
    validator = getattr(dataset_registry, "validate_dataset_bundle", None)
    assert callable(validator), "Issue #12 must expose dataset bundle validation"
    assert MANIFEST_PATH.is_file(), "Issue #12 must provide the frozen dataset manifest"

    report = validator(MANIFEST_PATH)

    assert report.state == "VALID"
    assert report.violations == ()
    assert report.snapshot is not None
    snapshot = report.snapshot
    assert snapshot.manifest.dataset_id == "braincrew-evaluation-dataset"
    assert snapshot.manifest.dataset_version == "1.0.0"
    assert snapshot.manifest.case_count == 100
    assert len(snapshot.case_records) == 100
    assert len({case.case_id for case in snapshot.case_records}) == 100
    assert Counter(case.primary_focus for case in snapshot.case_records) == {
        "parsing": 20,
        "retrieval": 30,
        "grounded_answer": 40,
        "visibility_abstention": 10,
    }
    assert Counter(case.split for case in snapshot.case_records) == {
        "Calibration": 70,
        "Verification": 30,
    }
    assert snapshot.verification_denominators.model_dump() == {
        "evidence_span_recovery": 6,
        "recall_at_5": 9,
        "claim_support_precision": 10,
        "citation_precision": 10,
        "answer_mode_accuracy": 15,
        "abstention_accuracy": 5,
    }
    assert snapshot.dataset_digest == snapshot.manifest.content_digest
    assert set(snapshot.component_digests) == {"parsing", "retrieval", "grounded"}
    assert all(value.startswith("sha256:") for value in snapshot.component_digests.values())
    assert snapshot.manifest.dataset_card.provenance_status == "complete"
    assert snapshot.manifest.dataset_card.license_status == "approved"


def test_dataset_card_publishes_digest_provenance_license_and_risk_status() -> None:
    report = dataset_registry.validate_dataset_bundle(MANIFEST_PATH)
    assert report.snapshot is not None
    manifest = report.snapshot.manifest
    card_path = MANIFEST_PATH.parent / manifest.dataset_card.path

    assert card_path.is_file(), "the frozen dataset must ship a reviewable dataset card"
    card = card_path.read_text(encoding="utf-8")
    assert manifest.dataset_id in card
    assert manifest.dataset_version in card
    assert manifest.content_digest in card
    assert "100 cases" in card
    assert "70 Calibration / 30 Verification" in card
    assert "CC0-1.0" in card
    assert "Provenance status: complete" in card
    assert "License status: approved" in card
    assert "Risk classification" in card
    assert "Grounded cases inherit dataset-level provenance" in card


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (missing_component, "COMPONENT_MISSING"),
        (escape_component_bundle, "COMPONENT_PATH_INVALID"),
        (misdeclare_component_schema, "SCHEMA_INVALID"),
        (missing_dataset_card, "DATASET_CARD_MISSING"),
        (duplicate_case_identity, "DUPLICATE_CASE_ID"),
        (invalidate_case_identity, "CASE_IDENTITY_INVALID"),
        (duplicate_case_content, "DUPLICATE_CASE_CONTENT"),
        (drift_split, "SPLIT_DRIFT"),
        (break_component_schema, "SCHEMA_INVALID"),
        (remove_case_provenance, "PROVENANCE_MISSING"),
        (invalidate_license, "LICENSE_INVALID"),
        (invalidate_risk_policy, "RISK_CLASSIFICATION_INVALID"),
        (reduce_verification_applicability, "METRIC_APPLICABILITY_INSUFFICIENT"),
        (leak_case_across_splits, "CALIBRATION_VERIFICATION_LEAKAGE"),
        (leak_reference_answer, "ANSWER_LEAKAGE"),
        (leak_answer_literal_into_query, "ANSWER_LEAKAGE"),
        (remove_all_case_applicability, "METRIC_APPLICABILITY_INSUFFICIENT"),
        (remove_focus_specific_applicability, "METRIC_APPLICABILITY_INSUFFICIENT"),
        (downgrade_grounded_provenance, "PROVENANCE_INCOMPLETE"),
    ],
    ids=lambda value: getattr(value, "__name__", str(value)),
)
def test_dataset_mutations_fail_closed_as_invalid(
    tmp_path: Path,
    mutation: Callable[[Path], None],
    expected_code: str,
) -> None:
    manifest_path = copy_bundle(tmp_path)
    mutation(manifest_path)

    try:
        report = dataset_registry.validate_dataset_bundle(manifest_path)
    except Exception as error:  # noqa: BLE001 - RED records the missing fail-closed contract.
        pytest.fail(f"validator must return INVALID instead of raising: {error}")

    assert report.state == "INVALID"
    assert report.snapshot is None
    assert expected_code in {violation.code for violation in report.violations}


def test_scoring_relevant_change_invalidates_component_and_dataset_digests(
    tmp_path: Path,
) -> None:
    manifest_path = copy_bundle(tmp_path)
    frozen_digest = read_json(manifest_path)["content_digest"]
    change_scoring_content(manifest_path)

    try:
        report = dataset_registry.validate_dataset_bundle(manifest_path)
    except Exception as error:  # noqa: BLE001 - RED records the missing invalidation report.
        pytest.fail(f"digest drift must return INVALID instead of raising: {error}")

    assert report.state == "INVALID"
    codes = {violation.code for violation in report.violations}
    assert "COMPONENT_DIGEST_MISMATCH" in codes
    assert "DATASET_DIGEST_MISMATCH" in codes
    assert report.computed_dataset_digest is not None
    assert report.computed_dataset_digest != frozen_digest


def test_focus_applicability_failure_explains_the_primary_focus_contract(
    tmp_path: Path,
) -> None:
    manifest_path = copy_bundle(tmp_path)
    remove_focus_specific_applicability(manifest_path)

    report = dataset_registry.validate_dataset_bundle(manifest_path)

    details = {
        violation.detail
        for violation in report.violations
        if violation.code == "METRIC_APPLICABILITY_INSUFFICIENT"
    }
    assert any("primary focus" in detail for detail in details)


def test_rehashed_snapshot_rejects_dataset_level_license_drift() -> None:
    valid = dataset_registry.validate_dataset_bundle(MANIFEST_PATH)
    assert valid.snapshot is not None
    snapshot = valid.snapshot
    parsing = snapshot.parsing_dataset.model_copy(
        update={
            "provenance": snapshot.parsing_dataset.provenance.model_copy(
                update={"license": "UNLICENSED"}
            )
        }
    )
    tampered = rehash_snapshot(snapshot, parsing=parsing)

    report = dataset_registry.validate_dataset_snapshot(tampered)

    assert report.state == "INVALID"
    assert "LICENSE_INVALID" in {violation.code for violation in report.violations}


def test_rehashed_snapshot_rejects_case_source_type_drift() -> None:
    valid = dataset_registry.validate_dataset_bundle(MANIFEST_PATH)
    assert valid.snapshot is not None
    snapshot = valid.snapshot
    assert isinstance(snapshot.parsing_dataset, ParsingDatasetDocument)
    parsing_cases = list(snapshot.parsing_dataset.cases)
    parsing_cases[0] = parsing_cases[0].model_copy(
        update={
            "provenance": parsing_cases[0].provenance.model_copy(update={"source_type": "public"})
        }
    )
    parsing = snapshot.parsing_dataset.model_copy(update={"cases": parsing_cases})
    tampered = rehash_snapshot(snapshot, parsing=parsing)

    report = dataset_registry.validate_dataset_snapshot(tampered)

    assert report.state == "INVALID"
    assert "PROVENANCE_INCONSISTENT" in {violation.code for violation in report.violations}


def test_rehashed_snapshot_rejects_component_path_escape() -> None:
    valid = dataset_registry.validate_dataset_bundle(MANIFEST_PATH)
    assert valid.snapshot is not None
    snapshot = valid.snapshot
    components = snapshot.manifest.components.model_copy(
        update={
            "parsing": snapshot.manifest.components.parsing.model_copy(
                update={"path": "../escaped-parsing.json"}
            )
        }
    )
    manifest = snapshot.manifest.model_copy(update={"components": components})
    tampered = rehash_snapshot(snapshot, manifest=manifest)

    report = dataset_registry.validate_dataset_snapshot(tampered)

    assert report.state == "INVALID"
    assert "COMPONENT_PATH_INVALID" in {violation.code for violation in report.violations}
