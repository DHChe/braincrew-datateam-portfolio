from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, cast

from ..corpus_pack_v1_fixture import run_cli, stage_valid_pack, write_provenance_sidecar


def read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def seal(
    staging_dir: Path,
    output_root: Path,
    manifest: dict[str, Any],
) -> CompletedProcess[str]:
    provenance_sidecar = write_provenance_sidecar(
        output_root.parent / f"{staging_dir.name}-provenance-review.json",
        manifest,
    )
    return run_cli(
        "seal-corpus",
        "--staging-dir",
        str(staging_dir),
        "--output-root",
        str(output_root),
        "--provenance-sidecar",
        str(provenance_sidecar),
    )


def test_cli_seals_exact_staged_bytes_with_a_sanitized_create_only_receipt(
    tmp_path: Path,
) -> None:
    staging_dir = tmp_path / "isolated-staging"
    source_bytes = "합성 데모 취업규칙\n휴가는 승인 후 사용한다.\n".encode()
    manifest = stage_valid_pack(
        staging_dir,
        sources=[("synthetic-rule-001", "sources/rule.md", source_bytes)],
    )
    output_root = tmp_path / "sealed"

    result = seal(staging_dir, output_root, manifest)

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    receipt_path = Path(summary["receipt_path"])
    sealed_dir = receipt_path.parent
    receipt = read_json(receipt_path)

    assert sealed_dir == output_root / manifest["corpus_id"] / manifest["corpus_version"]
    assert (sealed_dir / "corpus-manifest.json").read_bytes() == (
        staging_dir / "corpus-manifest.json"
    ).read_bytes()
    assert (sealed_dir / "sources" / "rule.md").read_bytes() == source_bytes
    assert summary["sealed_content_digest"] == manifest["sealed_content_digest"]
    assert receipt["schema_version"] == "corpus-sealing-receipt-v2"
    assert receipt["corpus_id"] == manifest["corpus_id"]
    assert receipt["corpus_version"] == manifest["corpus_version"]
    assert receipt["sealed_content_digest"] == manifest["sealed_content_digest"]
    assert receipt["provenance_digest"] == summary["provenance_digest"]
    assert receipt["source_count"] == 1
    assert receipt["sources"] == [
        {
            "source_id": "synthetic-rule-001",
            "content_sha256": manifest["sources"][0]["content_sha256"],
        }
    ]
    receipt_text = receipt_path.read_text(encoding="utf-8")
    for forbidden in (
        source_bytes.decode(),
        "braincrew-evaluation-dataset@2.0.0",
        "query",
        "answer",
        "credential",
        "postgresql://",
        str(staging_dir),
    ):
        assert forbidden not in receipt_text


def test_cli_refuses_to_modify_an_existing_sealed_version(tmp_path: Path) -> None:
    staging_dir = tmp_path / "isolated-staging"
    manifest = stage_valid_pack(staging_dir)
    output_root = tmp_path / "sealed"
    first = seal(staging_dir, output_root, manifest)
    assert first.returncode == 0, first.stderr
    sealed_dir = output_root / manifest["corpus_id"] / manifest["corpus_version"]
    original_bytes = {
        path.relative_to(sealed_dir): path.read_bytes()
        for path in sealed_dir.rglob("*")
        if path.is_file()
    }

    second = seal(staging_dir, output_root, manifest)

    assert second.returncode == 2
    assert "SEALED_CORPUS_VERSION_EXISTS" in second.stderr
    assert {
        path.relative_to(sealed_dir): path.read_bytes()
        for path in sealed_dir.rglob("*")
        if path.is_file()
    } == original_bytes


def test_replay_reproduces_receipt_and_rejects_sealed_source_tampering(tmp_path: Path) -> None:
    staging_dir = tmp_path / "isolated-staging"
    manifest = stage_valid_pack(staging_dir)
    seal_result = seal(staging_dir, tmp_path / "sealed", manifest)
    assert seal_result.returncode == 0, seal_result.stderr
    summary = json.loads(seal_result.stdout)
    receipt_path = Path(summary["receipt_path"])

    replay = run_cli("replay", "--artifact", str(receipt_path))

    assert replay.returncode == 0, replay.stderr
    replay_summary = json.loads(replay.stdout)
    assert replay_summary["receipt_digest"] == summary["receipt_digest"]
    assert replay_summary["sealed_content_digest"] == summary["sealed_content_digest"]

    source_path = receipt_path.parent / "sources" / "synthetic-rule-001.md"
    source_path.write_bytes(source_path.read_bytes() + b"x")
    tampered_replay = run_cli("replay", "--artifact", str(receipt_path))

    assert tampered_replay.returncode == 2
    assert "CORPUS_PACK_DIGEST_MISMATCH" in tampered_replay.stderr
