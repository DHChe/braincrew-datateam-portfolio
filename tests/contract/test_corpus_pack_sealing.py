from __future__ import annotations

import hashlib
import json
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

import pytest

from ..corpus_pack_v1_fixture import (
    canonical_json_bytes,
    run_cli,
    stage_valid_pack,
    write_manifest,
)

REPOSITORY_ROOT = Path(__file__).parents[2]
SCHEMA_DIR = REPOSITORY_ROOT / "schemas"
EXPECTED_SCHEMA_CONTRACTS = {
    "ax-synthetic-seed-content-v1.schema.json": (
        3699,
        "372118334771854c867d3e7168331ed4cabb9380db95d4aa624345bbe004b1cb",
    ),
    "ax-synthetic-seed-pack-v1.schema.json": (
        2241,
        "4ddc71d7408324bfed6e7a25024899a7f689431f5f024fb2329f3f844352bffa",
    ),
}


def seal(staging_dir: Path, output_root: Path) -> subprocess.CompletedProcess[str]:
    return run_cli(
        "seal-corpus",
        "--staging-dir",
        str(staging_dir),
        "--output-root",
        str(output_root),
    )


def test_vendored_ax_schema_bytes_and_declared_digests_match_merge_contract() -> None:
    for schema_name, (expected_size, expected_hex_digest) in EXPECTED_SCHEMA_CONTRACTS.items():
        schema_path = SCHEMA_DIR / schema_name
        digest_path = schema_path.with_suffix(".sha256")

        assert schema_path.exists(), schema_path
        assert digest_path.exists(), digest_path
        schema_bytes = schema_path.read_bytes()

        assert len(schema_bytes) == expected_size
        assert hashlib.sha256(schema_bytes).hexdigest() == expected_hex_digest
        assert digest_path.read_bytes() == f"sha256:{expected_hex_digest}\n".encode()


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (lambda payload: payload.__setitem__("unexpected", True), "CORPUS_PACK_SCHEMA_INVALID"),
        (
            lambda payload: payload["sources"][0].__setitem__("expected_answer", "leak"),
            "CORPUS_PACK_UNSAFE_CONTENT",
        ),
        (
            lambda payload: payload["sources"][0]["applicability_scope"].__setitem__(
                "nested", {"query": "leak"}
            ),
            "CORPUS_PACK_UNSAFE_CONTENT",
        ),
        (
            lambda payload: payload["sources"][0].__setitem__("license", "MIT"),
            "CORPUS_PACK_SCHEMA_INVALID",
        ),
        (
            lambda payload: payload["sources"][0].__setitem__("provenance_status", "pending"),
            "CORPUS_PACK_SCHEMA_INVALID",
        ),
        (
            lambda payload: payload["sources"][0].__setitem__("synthetic", False),
            "CORPUS_PACK_SCHEMA_INVALID",
        ),
        (
            lambda payload: payload["sources"][0].__setitem__("path", "../escape.md"),
            "CORPUS_PACK_PATH_INVALID",
        ),
        (
            lambda payload: payload["sources"][0]["applicability_scope"].__setitem__("weight", 1.5),
            "CORPUS_PACK_SCHEMA_INVALID",
        ),
    ],
)
def test_manifest_contract_rejects_invalid_or_evaluation_derived_content(
    tmp_path: Path,
    mutate: Any,
    expected_code: str,
) -> None:
    staging_dir = tmp_path / "staging"
    payload = stage_valid_pack(staging_dir)
    mutate(payload)
    write_manifest(staging_dir, payload)

    result = seal(staging_dir, tmp_path / "sealed")

    assert result.returncode == 2
    assert expected_code in result.stderr
    assert not (tmp_path / "sealed" / payload["corpus_id"] / payload["corpus_version"]).exists()


@pytest.mark.parametrize(
    "source_bytes",
    [
        b"\xff",
        b"\xef\xbb\xbfsynthetic\n",
        b"synthetic\r\n",
        b"synthetic\r",
        unicodedata.normalize("NFD", "휴가").encode("utf-8"),
    ],
)
def test_source_byte_contract_rejects_noncanonical_input(
    tmp_path: Path,
    source_bytes: bytes,
) -> None:
    staging_dir = tmp_path / "staging"
    payload = stage_valid_pack(
        staging_dir,
        sources=[("synthetic-rule-001", "sources/rule.md", source_bytes)],
    )

    result = seal(staging_dir, tmp_path / "sealed")

    assert result.returncode == 2
    assert "CORPUS_PACK_CANONICAL_BYTES_INVALID" in result.stderr
    assert not (tmp_path / "sealed" / payload["corpus_id"] / payload["corpus_version"]).exists()


def test_manifest_strings_must_already_be_nfc_and_lf_only(tmp_path: Path) -> None:
    staging_dir = tmp_path / "staging"
    payload = stage_valid_pack(staging_dir)
    payload["sources"][0]["source_title"] = unicodedata.normalize("NFD", "휴가 규정")
    write_manifest(staging_dir, payload)

    result = seal(staging_dir, tmp_path / "sealed")

    assert result.returncode == 2
    assert "CORPUS_PACK_CANONICAL_BYTES_INVALID" in result.stderr


def test_single_byte_source_mutation_is_rejected_before_sealing(tmp_path: Path) -> None:
    staging_dir = tmp_path / "staging"
    payload = stage_valid_pack(staging_dir)
    source_path = staging_dir / payload["sources"][0]["path"]
    source_path.write_bytes(source_path.read_bytes() + b"x")

    result = seal(staging_dir, tmp_path / "sealed")

    assert result.returncode == 2
    assert "CORPUS_PACK_DIGEST_MISMATCH" in result.stderr


def test_backslash_source_path_is_rejected_as_non_posix(tmp_path: Path) -> None:
    staging_dir = tmp_path / "staging"
    payload = stage_valid_pack(staging_dir)
    original_path = staging_dir / payload["sources"][0]["path"]
    backslash_path = staging_dir / "sources\\rule.md"
    original_path.rename(backslash_path)
    payload["sources"][0]["path"] = "sources\\rule.md"
    write_manifest(staging_dir, payload)

    result = seal(staging_dir, tmp_path / "sealed")

    assert result.returncode == 2
    assert "CORPUS_PACK_PATH_INVALID" in result.stderr


def test_ordered_source_manifest_changes_the_sealed_content_digest(tmp_path: Path) -> None:
    first_staging = tmp_path / "first"
    second_staging = tmp_path / "second"
    sources = [
        ("synthetic-rule-001", "sources/one.md", b"one\n"),
        ("synthetic-rule-002", "sources/two.md", b"two\n"),
    ]
    first = stage_valid_pack(first_staging, sources=sources)
    second = stage_valid_pack(second_staging, sources=list(reversed(sources)))

    assert first["sealed_content_digest"] != second["sealed_content_digest"]


def test_schema_drift_fails_closed_even_if_declared_digest_is_also_changed(tmp_path: Path) -> None:
    staging_dir = tmp_path / "staging"
    stage_valid_pack(staging_dir)
    schema_name = "ax-synthetic-seed-content-v1.schema.json"
    schema_path = SCHEMA_DIR / schema_name
    digest_path = schema_path.with_suffix(".sha256")
    original_schema = schema_path.read_bytes()
    original_digest = digest_path.read_bytes()
    try:
        drifted_schema = original_schema.replace(b'"corpus_mode"', b'"corpus_m0de"', 1)
        schema_path.write_bytes(drifted_schema)
        digest_path.write_text(
            f"sha256:{hashlib.sha256(drifted_schema).hexdigest()}\n",
            encoding="utf-8",
        )

        result = seal(staging_dir, tmp_path / "sealed")

        assert result.returncode == 2
        assert "AX_SCHEMA_DRIFT" in result.stderr
    finally:
        schema_path.write_bytes(original_schema)
        digest_path.write_bytes(original_digest)


def test_staging_must_be_isolated_from_repository_and_output(tmp_path: Path) -> None:
    repository_staging = REPOSITORY_ROOT / ".issue-31-forbidden-staging"
    output_root = tmp_path / "sealed"
    try:
        stage_valid_pack(repository_staging)

        result = seal(repository_staging, output_root)

        assert result.returncode == 2
        assert "CORPUS_STAGING_NOT_ISOLATED" in result.stderr
        assert not output_root.exists()
    finally:
        for path in sorted(repository_staging.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            else:
                path.rmdir()
        if repository_staging.exists():
            repository_staging.rmdir()


def test_staging_rejects_undeclared_files(tmp_path: Path) -> None:
    staging_dir = tmp_path / "staging"
    stage_valid_pack(staging_dir)
    (staging_dir / "undeclared.txt").write_text("not declared\n", encoding="utf-8")

    result = seal(staging_dir, tmp_path / "sealed")

    assert result.returncode == 2
    assert "CORPUS_PACK_UNDECLARED_FILE" in result.stderr


def test_manifest_bytes_must_be_canonical_json(tmp_path: Path) -> None:
    staging_dir = tmp_path / "staging"
    payload = stage_valid_pack(staging_dir)
    (staging_dir / "corpus-manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = seal(staging_dir, tmp_path / "sealed")

    assert result.returncode == 2
    assert "CORPUS_PACK_CANONICAL_BYTES_INVALID" in result.stderr
    assert canonical_json_bytes(payload) != (staging_dir / "corpus-manifest.json").read_bytes()
