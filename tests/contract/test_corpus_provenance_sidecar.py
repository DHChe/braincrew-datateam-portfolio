from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any

import pytest

from ..corpus_pack_v1_fixture import (
    canonical_json_bytes,
    provenance_sidecar,
    run_cli,
    sha256_digest,
    stage_valid_pack,
)


def write_sidecar(
    path: Path,
    payload: dict[str, Any],
    *,
    immutable: bool = True,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    if immutable:
        path.chmod(0o444)


def seal(
    staging_dir: Path,
    output_root: Path,
    provenance_sidecar: Path | None = None,
) -> CompletedProcess[str]:
    arguments = [
        "seal-corpus",
        "--staging-dir",
        str(staging_dir),
        "--output-root",
        str(output_root),
    ]
    if provenance_sidecar is not None:
        arguments.extend(["--provenance-sidecar", str(provenance_sidecar)])
    return run_cli(*arguments)


def test_sealing_requires_a_provenance_sidecar(tmp_path: Path) -> None:
    staging_dir = tmp_path / "staging"
    stage_valid_pack(staging_dir)

    result = seal(staging_dir, tmp_path / "sealed")

    assert result.returncode == 2
    assert "CORPUS_PROVENANCE_SIDECAR_REQUIRED" in result.stderr


def test_sealing_preserves_an_immutable_sidecar_and_replay_revalidates_it(
    tmp_path: Path,
) -> None:
    staging_dir = tmp_path / "staging"
    manifest = stage_valid_pack(staging_dir)
    sidecar_path = tmp_path / "review" / "provenance-review.json"
    write_sidecar(sidecar_path, provenance_sidecar(manifest))

    result = seal(staging_dir, tmp_path / "sealed", sidecar_path)

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    receipt_path = Path(summary["receipt_path"])
    sealed_sidecar = receipt_path.parent / "provenance-review.json"
    assert summary["provenance_digest"] == provenance_sidecar(manifest)["provenance_digest"]
    assert sealed_sidecar.read_bytes() == sidecar_path.read_bytes()

    replay = run_cli("replay", "--artifact", str(receipt_path))

    assert replay.returncode == 0, replay.stderr
    assert json.loads(replay.stdout)["provenance_digest"] == summary["provenance_digest"]

    tampered = json.loads(sealed_sidecar.read_text(encoding="utf-8"))
    tampered["reviews"][0]["reviewer_identity"] = "reviewer-002"
    sealed_sidecar.chmod(0o644)
    sealed_sidecar.write_bytes(canonical_json_bytes(tampered) + b"\n")
    sealed_sidecar.chmod(0o444)

    tampered_replay = run_cli("replay", "--artifact", str(receipt_path))

    assert tampered_replay.returncode == 2
    assert "CORPUS_PROVENANCE_SIDECAR_DIGEST_MISMATCH" in tampered_replay.stderr


@pytest.mark.parametrize(
    ("mutate", "immutable", "expected_code"),
    [
        (
            lambda payload: payload["reviews"][0].__setitem__("decision", "pending"),
            True,
            "CORPUS_PROVENANCE_SIDECAR_INVALID",
        ),
        (
            lambda payload: payload["reviews"][0].__setitem__(
                "content_sha256", "sha256:" + "0" * 64
            ),
            True,
            "CORPUS_PROVENANCE_SIDECAR_BINDING_MISMATCH",
        ),
        (lambda payload: None, False, "CORPUS_PROVENANCE_SIDECAR_MUTABLE"),
    ],
)
def test_sealing_fails_closed_for_invalid_or_mutable_provenance_evidence(
    tmp_path: Path,
    mutate: Any,
    immutable: bool,
    expected_code: str,
) -> None:
    staging_dir = tmp_path / "staging"
    manifest = stage_valid_pack(staging_dir)
    payload = provenance_sidecar(manifest)
    mutate(payload)
    payload["provenance_digest"] = sha256_digest(
        canonical_json_bytes(
            {key: value for key, value in payload.items() if key != "provenance_digest"}
        )
    )
    sidecar_path = tmp_path / "review" / "provenance-review.json"
    write_sidecar(sidecar_path, payload, immutable=immutable)

    result = seal(staging_dir, tmp_path / "sealed", sidecar_path)

    assert result.returncode == 2
    assert expected_code in result.stderr
    assert not (tmp_path / "sealed" / manifest["corpus_id"] / manifest["corpus_version"]).exists()


def test_sealing_rejects_a_sidecar_inside_the_staged_pack(tmp_path: Path) -> None:
    staging_dir = tmp_path / "staging"
    manifest = stage_valid_pack(staging_dir)
    sidecar_path = staging_dir / "provenance-review.json"
    write_sidecar(sidecar_path, provenance_sidecar(manifest))

    result = seal(staging_dir, tmp_path / "sealed", sidecar_path)

    assert result.returncode == 2
    assert "CORPUS_PROVENANCE_SIDECAR_PATH_INVALID" in result.stderr
