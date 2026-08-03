from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

import braincrew.corpus_qualification as qualification_module
from braincrew.corpus_qualification import CorpusQualificationError, qualify_corpus_pack
from braincrew.corpus_sealing import canonical_json_bytes, sha256_digest
from braincrew.dataset_registry import DatasetBundleSnapshot, validate_dataset_bundle

from ..corpus_qualification_v2_fixture import (
    DATASET_V2_MANIFEST,
    qualification_command,
    run_cli,
    seal_qualification_pack,
    stage_dataset_v2_bundle,
    stage_qualification_pack,
)

REPOSITORY_ROOT = Path(__file__).parents[2]
DATASET_V3_MANIFEST = REPOSITORY_ROOT / "datasets/dataset_manifest_v3.json"
ISSUE_36_CORPUS_MANIFEST = REPOSITORY_ROOT / "tests/fixtures/issue_36_corpus_manifest.json"
REVIEW_CHECKLIST = REPOSITORY_ROOT / "docs/reviews/2026-07-23-issue-53-successor-dataset-review.md"

EXPECTED_DATASET_V2_BYTES = {
    "datasets/dataset_manifest_v2.json": (
        "622313f93512dd0b1331676caa04b5494646f7adf9503950f49e68d1dfb9e293"
    ),
    "datasets/DATASET_CARD_V2.md": (
        "02b37effd7ddf4f5c9086503bfc538fa9cfcff0130e03c9ff15b79b80974bf47"
    ),
    "datasets/parsing/parsing_cases_v1.json": (
        "568a49480e7bb2e5de2f0deb54366099b643300b3890d8f24905d6f9f610ddb2"
    ),
    "datasets/retrieval/retrieval_cases_v1.json": (
        "8f93b1517e4c4a1b835298e115d8d6263364d39761e0d017859bd244d748da48"
    ),
    "datasets/grounded/grounded_cases_v1.json": (
        "3d1183395ec32473c5cc7d8f1102e54d2ac680f1a78e398ce17cee2d6f61fa37"
    ),
}
EXPECTED_DATASET_V2_DIGEST = (
    "sha256:ef6b0a1f50fcd2ecb8b5d7addc7bc5daaa54537899a1ac6faba7c784eee6e98a"
)
EXPECTED_SOURCE_CORPUS = {
    "id": "braincrew-independent-hr-corpus",
    "version": "1.0.0",
    "sealed_content_digest": (
        "sha256:5f0c254b3dc64b23470029b1004106dc078a9602062da8fa8041623bf91fb7e4"
    ),
    "provenance_digest": (
        "sha256:eb43fc824cd54bf10e8805b5fdeb1915bcaac368cb458ce8981a481cd7d4fce1"
    ),
    "sealing_receipt_digest": (
        "sha256:bc508b6001facbef67bacd7e0c1d4d5123f04bc1e33d2849b5e7d455183df62b"
    ),
}


def _read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text("utf-8")))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_successor() -> DatasetBundleSnapshot:
    assert DATASET_V3_MANIFEST.is_file(), "Issue #53 successor manifest is missing"
    report = validate_dataset_bundle(DATASET_V3_MANIFEST)
    assert report.state == "VALID", report.violations
    assert report.snapshot is not None
    return report.snapshot


def _copy_successor_bundle(directory: Path) -> Path:
    manifest = _read_json(DATASET_V3_MANIFEST)
    for relative_path in (
        manifest["dataset_card"]["path"],
        manifest["components"]["parsing"]["path"],
        manifest["components"]["retrieval"]["path"],
        manifest["components"]["grounded"]["path"],
    ):
        source = DATASET_V3_MANIFEST.parent / relative_path
        destination = directory / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    destination_manifest = directory / DATASET_V3_MANIFEST.name
    destination_manifest.write_bytes(DATASET_V3_MANIFEST.read_bytes())
    return destination_manifest


def _stage_exact_issue_36_pack(staging_dir: Path) -> None:
    assert ISSUE_36_CORPUS_MANIFEST.is_file(), "Issue #36 corpus fixture is missing"
    snapshot = _require_successor()
    source_text_by_id = {
        case.document.id: case.document.canonical_text.encode("utf-8")
        for case in snapshot.parsing_dataset.cases
    }
    source_text_by_id["demo-lifecycle-checklist-014"] = (
        b"# Synthetic Demo: Archived Exit Checklist\n\n"
        b"This newly authored CC0-1.0 checklist is fictional Northstar Demo Works material. "
        b"It is archived and lower authority than the current lifecycle policy.\n\n"
        b"The checklist lists equipment return, an account closure request, and a final meeting. "
        b"It does not cover the current requirements for written separation confirmation, final "
        b"payments, continuing obligations, access end time, or traceable record correction. The "
        b"current Onboarding, Organizational Change, Separation, and Records Policy controls.\n"
    )
    manifest = _read_json(ISSUE_36_CORPUS_MANIFEST)
    staging_dir.mkdir(parents=True)
    for source in manifest["sources"]:
        source_bytes = source_text_by_id[source["source_id"]]
        assert sha256_digest(source_bytes) == source["content_sha256"]
        source_path = staging_dir / source["path"]
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(source_bytes)
    (staging_dir / "corpus-manifest.json").write_bytes(canonical_json_bytes(manifest))


def _seal_exact_issue_36_pack(staging_dir: Path, output_root: Path) -> Path:
    _stage_exact_issue_36_pack(staging_dir)
    manifest = _read_json(staging_dir / "corpus-manifest.json")
    sidecar: dict[str, Any] = {
        "schema_version": "corpus-provenance-review-v1",
        "corpus_id": manifest["corpus_id"],
        "corpus_version": manifest["corpus_version"],
        "sealed_content_digest": manifest["sealed_content_digest"],
        "reviews": [
            {
                "source_id": source["source_id"],
                "content_sha256": source["content_sha256"],
                "synthetic_origin": "newly-authored-synthetic",
                "authoring_owner": "codex-issue-36-authoring-agent",
                "license_assignment": "CC0-1.0",
                "reviewer_identity": "DHChe-corpus-provenance-reviewer",
                "review_date": "2026-07-23",
                "review_timezone": "Asia/Seoul",
                "decision": "approved",
            }
            for source in manifest["sources"]
        ],
    }
    sidecar["provenance_digest"] = sha256_digest(canonical_json_bytes(sidecar))
    sidecar_path = output_root.parent / "provenance-review.json"
    sidecar_path.write_bytes(canonical_json_bytes(sidecar) + b"\n")
    sidecar_path.chmod(0o444)
    sealed = run_cli(
        "seal-corpus",
        "--staging-dir",
        str(staging_dir),
        "--output-root",
        str(output_root),
        "--provenance-sidecar",
        str(sidecar_path),
    )
    assert sealed.returncode == 0, sealed.stderr
    return Path(json.loads(sealed.stdout)["receipt_path"]).parent


def test_successor_manifest_freezes_exact_components_and_predecessor() -> None:
    snapshot = _require_successor()
    manifest = snapshot.manifest

    assert manifest.schema_version == "dataset-manifest-v2"
    assert manifest.dataset_version == "3.0.0"
    assert manifest.source_corpus is not None
    assert manifest.source_corpus.model_dump(mode="json") == EXPECTED_SOURCE_CORPUS
    assert manifest.allocation.model_dump() == {
        "parsing": 20,
        "retrieval": 30,
        "grounded_answer": 40,
        "visibility_abstention": 10,
    }
    assert manifest.split_counts.model_dump() == {"Calibration": 70, "Verification": 30}
    assert {
        "parsing": manifest.components.parsing.path,
        "retrieval": manifest.components.retrieval.path,
        "grounded": manifest.components.grounded.path,
    } == {
        "parsing": "parsing/parsing_cases_v2.json",
        "retrieval": "retrieval/retrieval_cases_v2.json",
        "grounded": "grounded/grounded_cases_v2.json",
    }
    assert snapshot.parsing_dataset.dataset.version == "2.0.0"
    assert snapshot.retrieval_dataset.dataset.version == "2.0.0"
    assert snapshot.grounded_dataset.dataset_version == "2.0.0"


def test_historical_dataset_v2_bytes_and_digests_are_immutable() -> None:
    for relative_path, expected in EXPECTED_DATASET_V2_BYTES.items():
        assert _sha256(REPOSITORY_ROOT / relative_path) == expected

    report = validate_dataset_bundle(DATASET_V2_MANIFEST)
    assert report.state == "VALID"
    assert report.snapshot is not None
    assert report.snapshot.dataset_digest == EXPECTED_DATASET_V2_DIGEST
    assert report.snapshot.manifest.schema_version == "dataset-manifest-v1"
    assert report.snapshot.manifest.dataset_version == "2.0.0"


def test_successor_preserves_evaluator_metric_risk_and_split_semantics() -> None:
    historical = validate_dataset_bundle(DATASET_V2_MANIFEST)
    successor = validate_dataset_bundle(DATASET_V3_MANIFEST)
    assert historical.snapshot is not None
    assert successor.snapshot is not None
    old = historical.snapshot
    new = successor.snapshot

    assert new.manifest.minimum_verification_denominators == (
        old.manifest.minimum_verification_denominators
    )
    assert new.manifest.risk_policy == old.manifest.risk_policy
    assert new.manifest.leakage_policy == old.manifest.leakage_policy
    assert [(case.split, case.primary_focus) for case in new.parsing_dataset.cases] == [
        (case.split, case.primary_focus) for case in old.parsing_dataset.cases
    ]
    assert [
        (case.split, case.primary_focus, case.difficulty, case.applicability)
        for case in new.retrieval_dataset.cases
    ] == [
        (case.split, case.primary_focus, case.difficulty, case.applicability)
        for case in old.retrieval_dataset.cases
    ]
    assert [
        (
            case.split,
            case.primary_focus,
            case.risk_level,
            case.expected_answer_mode,
            case.required_abstention_mode,
            case.required_output_paths,
            case.applicability,
        )
        for case in new.grounded_dataset.cases
    ] == [
        (
            case.split,
            case.primary_focus,
            case.risk_level,
            case.expected_answer_mode,
            case.required_abstention_mode,
            case.required_output_paths,
            case.applicability,
        )
        for case in old.grounded_dataset.cases
    ]


def test_successor_closes_every_source_digest_visibility_and_distractor_requirement() -> None:
    snapshot = _require_successor()
    assert ISSUE_36_CORPUS_MANIFEST.is_file()
    corpus = _read_json(ISSUE_36_CORPUS_MANIFEST)
    source_by_id = {source["source_id"]: source for source in corpus["sources"]}
    requirements = qualification_module._dataset_requirements(snapshot)

    assert len(snapshot.case_records) == 100
    assert set(requirements) <= set(source_by_id)
    for source_id, requirement in requirements.items():
        source = source_by_id[source_id]
        if requirement.expected_content_sha256 is not None:
            assert requirement.expected_content_sha256 == source["content_sha256"]
        visible_roles = set(source["visibility_scope"]["roles"])
        assert requirement.required_roles <= visible_roles
        assert requirement.forbidden_roles.isdisjoint(visible_roles)
    assert set(source_by_id) - set(requirements) == {"demo-lifecycle-checklist-014"}


Tamper = Callable[[dict[str, Any], dict[str, dict[str, Any]]], None]


def _tamper_case(manifest: dict[str, Any], components: dict[str, dict[str, Any]]) -> None:
    del manifest
    components["parsing"]["cases"][0]["id"] = "parsing-999"


def _tamper_source(manifest: dict[str, Any], components: dict[str, dict[str, Any]]) -> None:
    del manifest
    components["retrieval"]["cases"][0]["expected"]["evidence_groups"][0]["alternatives"][0][
        "record_id"
    ] = "substituted-source"


def _tamper_digest(manifest: dict[str, Any], components: dict[str, dict[str, Any]]) -> None:
    del manifest
    components["grounded"]["cases"][0]["propositions"][0]["supporting_evidence_groups"][0][
        "alternatives"
    ][0]["source_text_digest"] = "sha256:" + "0" * 64


def _tamper_visibility(manifest: dict[str, Any], components: dict[str, dict[str, Any]]) -> None:
    del manifest
    components["retrieval"]["cases"][0]["role"] = "HRManager"


def _tamper_split(manifest: dict[str, Any], components: dict[str, dict[str, Any]]) -> None:
    del manifest
    components["grounded"]["cases"][0]["split"] = "Calibration"


def _tamper_predecessor(manifest: dict[str, Any], components: dict[str, dict[str, Any]]) -> None:
    del components
    manifest["source_corpus"]["sealed_content_digest"] = "sha256:" + "0" * 64


@pytest.mark.parametrize(
    "tamper",
    [
        _tamper_case,
        _tamper_source,
        _tamper_digest,
        _tamper_visibility,
        _tamper_split,
        _tamper_predecessor,
    ],
)
def test_successor_replay_rejects_case_source_digest_visibility_split_and_predecessor_tampering(
    tmp_path: Path,
    tamper: Tamper,
) -> None:
    manifest_path = _copy_successor_bundle(tmp_path / "dataset")
    manifest = _read_json(manifest_path)
    components = {
        name: _read_json(manifest_path.parent / manifest["components"][name]["path"])
        for name in ("parsing", "retrieval", "grounded")
    }
    tamper(manifest, components)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8")
    for name, payload in components.items():
        path = manifest_path.parent / manifest["components"][name]["path"]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")

    assert validate_dataset_bundle(manifest_path).state == "INVALID"


def test_version_only_v3_substitution_is_rejected(tmp_path: Path) -> None:
    manifest_path = stage_dataset_v2_bundle(tmp_path / "substituted-dataset")
    manifest = _read_json(manifest_path)
    manifest["schema_version"] = "dataset-manifest-v2"
    manifest["dataset_version"] = "3.0.0"
    manifest["source_corpus"] = EXPECTED_SOURCE_CORPUS
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8")

    with pytest.raises(CorpusQualificationError, match="exact.*3.0.0"):
        qualify_corpus_pack(
            sealed_dir=tmp_path / "unused-sealed-dir",
            dataset_manifest_path=manifest_path,
            tenant_slug="braincrew-demo-tenant",
            demo_company_id="braincrew-demo-company",
        )


def test_successor_qualification_creates_receipt_v2_and_seed_v3_create_only(
    tmp_path: Path,
) -> None:
    sealed_dir = _seal_exact_issue_36_pack(tmp_path / "staging", tmp_path / "sealed")
    result = run_cli(*qualification_command(sealed_dir, DATASET_V3_MANIFEST))

    assert result.returncode == 0, result.stderr
    receipt = _read_json(sealed_dir / "qualification-receipt.json")
    import_manifest = _read_json(sealed_dir / "import-manifest.json")
    assert receipt["schema_version"] == "corpus-qualification-receipt-v2"
    assert receipt["dataset"]["version"] == "3.0.0"
    assert receipt["dataset"]["content_digest"] == _require_successor().dataset_digest
    assert import_manifest["seed_version"] == "braincrew-evaluation-dataset-3.0.0"
    original = (
        (sealed_dir / "qualification-receipt.json").read_bytes(),
        (sealed_dir / "import-manifest.json").read_bytes(),
    )
    repeated = run_cli(*qualification_command(sealed_dir, DATASET_V3_MANIFEST))
    assert repeated.returncode == 2
    assert (
        (sealed_dir / "qualification-receipt.json").read_bytes(),
        (sealed_dir / "import-manifest.json").read_bytes(),
    ) == original


def test_successor_qualification_rolls_back_both_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sealed_dir = _seal_exact_issue_36_pack(tmp_path / "staging", tmp_path / "sealed")
    qualification_os = cast(Any, qualification_module).os
    real_link = qualification_os.link

    def fail_import_link(source: Path, destination: Path) -> None:
        if Path(destination).name == "import-manifest.json":
            raise OSError("simulated publication failure")
        real_link(source, destination)

    monkeypatch.setattr(qualification_os, "link", fail_import_link)
    with pytest.raises(CorpusQualificationError, match="could not be published"):
        qualify_corpus_pack(
            sealed_dir=sealed_dir,
            dataset_manifest_path=DATASET_V3_MANIFEST,
            tenant_slug="braincrew-demo-tenant",
            demo_company_id="braincrew-demo-company",
        )
    assert not (sealed_dir / "qualification-receipt.json").exists()
    assert not (sealed_dir / "import-manifest.json").exists()


def test_historical_receipt_v1_replay_remains_supported(tmp_path: Path) -> None:
    assert hasattr(qualification_module, "_build_qualification_receipt_v1")
    assert hasattr(qualification_module, "_build_import_manifest_v1")
    staging_dir = tmp_path / "historical-staging"
    stage_qualification_pack(staging_dir)
    sealed_dir = seal_qualification_pack(staging_dir, tmp_path / "historical-sealed")
    validated, sealing_receipt_digest = qualification_module._validate_pack(
        sealed_dir,
        allowed_extra_files=qualification_module._SEALED_EXTRA_FILES,
    )
    historical = validate_dataset_bundle(DATASET_V2_MANIFEST)
    assert historical.snapshot is not None
    build_receipt = cast(Any, qualification_module)._build_qualification_receipt_v1
    receipt = build_receipt(
        validated=validated,
        sealing_receipt_digest=sealing_receipt_digest,
        snapshot=historical.snapshot,
    )
    receipt_path = sealed_dir / "qualification-receipt.json"
    receipt_bytes = canonical_json_bytes(receipt.model_dump(mode="json")) + b"\n"
    receipt_path.write_bytes(receipt_bytes)
    build_import = cast(Any, qualification_module)._build_import_manifest_v1
    import_manifest = build_import(
        receipt=receipt,
        qualification_receipt_digest=sha256_digest(receipt_bytes),
        tenant_slug="braincrew-demo-tenant",
        demo_company_id="braincrew-demo-company",
    )
    (sealed_dir / "import-manifest.json").write_bytes(
        canonical_json_bytes(import_manifest.model_dump(mode="json")) + b"\n"
    )

    replay = run_cli("replay", "--artifact", str(receipt_path))
    assert replay.returncode == 0, replay.stderr
    assert json.loads(replay.stdout)["receipt_schema_version"] == (
        "corpus-qualification-receipt-v1"
    )


def test_v1_and_v2_manifest_replay_dispatch_stays_separate() -> None:
    historical = validate_dataset_bundle(DATASET_V2_MANIFEST)
    successor = validate_dataset_bundle(DATASET_V3_MANIFEST)

    assert historical.state == "VALID"
    assert successor.state == "VALID"
    assert historical.snapshot is not None
    assert successor.snapshot is not None
    assert historical.snapshot.manifest.schema_version == "dataset-manifest-v1"
    assert historical.snapshot.manifest.source_corpus is None
    assert successor.snapshot.manifest.schema_version == "dataset-manifest-v2"
    assert successor.snapshot.manifest.source_corpus is not None


def test_wheel_contains_historical_v2_and_successor_v3_replay_resources(
    tmp_path: Path,
) -> None:
    completed = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        check=False,
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    wheel_path = next(tmp_path.glob("*.whl"))
    with zipfile.ZipFile(wheel_path) as wheel:
        names = set(wheel.namelist())
    assert {
        "braincrew/datasets/DATASET_CARD_V2.md",
        "braincrew/datasets/dataset_manifest_v2.json",
        "braincrew/datasets/parsing/parsing_cases_v1.json",
        "braincrew/datasets/retrieval/retrieval_cases_v1.json",
        "braincrew/datasets/grounded/grounded_cases_v1.json",
        "braincrew/datasets/DATASET_CARD_V3.md",
        "braincrew/datasets/dataset_manifest_v3.json",
        "braincrew/datasets/parsing/parsing_cases_v2.json",
        "braincrew/datasets/retrieval/retrieval_cases_v2.json",
        "braincrew/datasets/grounded/grounded_cases_v2.json",
    } <= names


@pytest.mark.parametrize(
    ("relative_path", "required_text"),
    [
        (
            "docs/superpowers/specs/2026-07-20-independent-evaluation-corpus-provisioning-design.md",
            "braincrew-evaluation-dataset@3.0.0",
        ),
        (
            "docs/superpowers/specs/2026-07-18-evidence-first-evaluation-plane-design.md",
            "dataset-manifest-v2",
        ),
        (
            "docs/interview/braincrew-data-portfolio-defense.md",
            "DHChe-successor-dataset-reviewer",
        ),
        (
            "docs/status/braincrew-delivery-workflow.md",
            "Issue #53 successor dataset review gate",
        ),
    ],
)
def test_canonical_docs_record_the_successor_contract(
    relative_path: str,
    required_text: str,
) -> None:
    assert required_text in (REPOSITORY_ROOT / relative_path).read_text("utf-8")


def test_canonical_docs_record_successor_qualification_outputs_and_freeze_state() -> None:
    provisioning_design = (
        REPOSITORY_ROOT
        / "docs/superpowers/specs/2026-07-20-independent-evaluation-corpus-provisioning-design.md"
    ).read_text("utf-8")
    delivery_status = (REPOSITORY_ROOT / "docs/status/braincrew-delivery-workflow.md").read_text(
        "utf-8"
    )

    assert "corpus-qualification-receipt-v2" in provisioning_design
    assert "seed_version = braincrew-evaluation-dataset-3.0.0" in provisioning_design
    assert "no dataset freeze claim" not in delivery_status


def test_dataset_review_checklist_binds_exact_candidate_bytes() -> None:
    snapshot = _require_successor()
    assert REVIEW_CHECKLIST.is_file()
    checklist = REVIEW_CHECKLIST.read_text("utf-8")
    assert "Status: APPROVED" in checklist
    assert "Decision: APPROVED" in checklist
    assert "DHChe-successor-dataset-reviewer" in checklist
    assert checklist.count("- [x]") == 8
    assert "- [ ]" not in checklist
    assert snapshot.dataset_digest in checklist
    assert snapshot.manifest.source_corpus is not None
    assert snapshot.manifest.source_corpus.sealed_content_digest in checklist
    for digest in snapshot.component_digests.values():
        assert digest in checklist
