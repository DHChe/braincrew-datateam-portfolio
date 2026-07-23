from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from ..contract.test_successor_dataset_freeze import (
    DATASET_V3_MANIFEST,
    _seal_exact_issue_36_pack,
)
from ..corpus_qualification_v2_fixture import (
    canonical_json_bytes,
    import_digest,
    qualification_command,
    run_cli,
    sha256_digest,
)

DATASET_ID = "braincrew-evaluation-dataset"
DATASET_VERSION = "3.0.0"
SEED_VERSION = "braincrew-evaluation-dataset-3.0.0"


def read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_cli_qualifies_all_100_cases_and_creates_sanitized_bound_outputs(
    tmp_path: Path,
) -> None:
    dataset_manifest = DATASET_V3_MANIFEST
    sealed_dir = _seal_exact_issue_36_pack(tmp_path / "staging", tmp_path / "sealed")
    sealed_inputs = {
        path.relative_to(sealed_dir): path.read_bytes()
        for path in sealed_dir.rglob("*")
        if path.is_file()
    }

    result = run_cli(*qualification_command(sealed_dir, dataset_manifest))

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    receipt_path = sealed_dir / "qualification-receipt.json"
    import_path = sealed_dir / "import-manifest.json"
    receipt = read_json(receipt_path)
    import_manifest = read_json(import_path)
    assert summary["receipt_path"] == "qualification-receipt.json"
    assert summary["import_manifest_path"] == "import-manifest.json"
    assert receipt["schema_version"] == "corpus-qualification-receipt-v2"
    assert receipt["dataset"] == {
        "case_count": 100,
        "component_digests": receipt["dataset"]["component_digests"],
        "content_digest": receipt["dataset"]["content_digest"],
        "id": DATASET_ID,
        "version": DATASET_VERSION,
    }
    assert receipt["required_source_count"] > 0
    assert receipt["distractor_source_count"] > 0
    assert set(receipt["required_role_counts"]) == {
        "Employee",
        "Executive",
        "HRPractitioner",
    }
    assert import_manifest["schema_version"] == "ax-synthetic-seed-pack-v1"
    assert import_manifest["seed_version"] == SEED_VERSION
    assert import_manifest["sealed_content_digest"] == receipt["corpus"]["sealed_content_digest"]
    assert import_manifest["qualification_receipt_digest"] == sha256_digest(
        receipt_path.read_bytes()
    )
    assert import_manifest["import_digest"] == import_digest(import_manifest)
    assert (
        summary["qualification_receipt_digest"] == import_manifest["qualification_receipt_digest"]
    )
    for relative_path, original_bytes in sealed_inputs.items():
        assert (sealed_dir / relative_path).read_bytes() == original_bytes

    retained_text = (
        result.stdout
        + receipt_path.read_text(encoding="utf-8")
        + import_path.read_text(encoding="utf-8")
    )
    for forbidden in (
        "즉시 해고할 수 있나요?",
        "연차휴가 신청 절차",
        "vector",
        "credential",
        "authorization",
        "postgresql://",
        str(tmp_path),
    ):
        assert forbidden not in retained_text


def test_cli_qualification_outputs_are_create_only(tmp_path: Path) -> None:
    dataset_manifest = DATASET_V3_MANIFEST
    sealed_dir = _seal_exact_issue_36_pack(tmp_path / "staging", tmp_path / "sealed")
    arguments = qualification_command(sealed_dir, dataset_manifest)
    first = run_cli(*arguments)
    assert first.returncode == 0, first.stderr
    receipt_path = sealed_dir / "qualification-receipt.json"
    import_path = sealed_dir / "import-manifest.json"
    original = (receipt_path.read_bytes(), import_path.read_bytes())

    second = run_cli(*arguments)

    assert second.returncode == 2
    assert (receipt_path.read_bytes(), import_path.read_bytes()) == original


def test_replay_reproduces_qualification_and_rejects_import_tampering(
    tmp_path: Path,
) -> None:
    dataset_manifest = DATASET_V3_MANIFEST
    sealed_dir = _seal_exact_issue_36_pack(tmp_path / "staging", tmp_path / "sealed")
    qualified = run_cli(*qualification_command(sealed_dir, dataset_manifest))
    assert qualified.returncode == 0, qualified.stderr
    summary = json.loads(qualified.stdout)
    receipt_path = sealed_dir / "qualification-receipt.json"

    replay = run_cli("replay", "--artifact", str(receipt_path))

    assert replay.returncode == 0, replay.stderr
    replay_summary = json.loads(replay.stdout)
    assert replay_summary["artifact_path"] == "qualification-receipt.json"
    assert str(tmp_path) not in replay.stdout
    assert replay_summary["receipt_digest"] == summary["receipt_digest"]
    assert replay_summary["qualification_receipt_digest"] == summary["qualification_receipt_digest"]
    assert replay_summary["import_digest"] == summary["import_digest"]

    import_path = sealed_dir / "import-manifest.json"
    tampered = read_json(import_path)
    tampered["tenant_slug"] = "tampered-tenant"
    import_path.write_bytes(canonical_json_bytes(tampered) + b"\n")

    rejected = run_cli("replay", "--artifact", str(receipt_path))

    assert rejected.returncode == 2
    assert "CORPUS_PACK_DIGEST_MISMATCH" in rejected.stderr
