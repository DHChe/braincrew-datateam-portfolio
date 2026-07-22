from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def sha256_digest(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "braincrew.cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def source_descriptor(
    *,
    source_id: str,
    path: str,
    source_bytes: bytes,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "path": path,
        "source_uri": f"demo://braincrew/{source_id}",
        "source_title": f"Synthetic source {source_id}",
        "source_type": "policy",
        "source_class": "company_rule",
        "document_version": "1.0.0",
        "effective_date": None,
        "revision_date": None,
        "applicability_scope": {"jurisdiction": "synthetic"},
        "visibility_scope": {"roles": ["Employee", "HRPractitioner"]},
        "content_sha256": sha256_digest(source_bytes),
        "license": "CC0-1.0",
        "provenance_status": "reviewed",
        "synthetic": True,
        "demo_company": True,
        "corpus_mode": "demo",
    }


def corpus_manifest(
    sources: list[dict[str, Any]],
    *,
    corpus_id: str = "braincrew-independent-corpus",
    corpus_version: str = "1.0.0",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "ax-synthetic-seed-content-v1",
        "corpus_id": corpus_id,
        "corpus_version": corpus_version,
        "synthetic": True,
        "demo_company": True,
        "corpus_mode": "demo",
        "license": "CC0-1.0",
        "provenance_status": "reviewed",
        "sources": sources,
    }
    payload["sealed_content_digest"] = sha256_digest(canonical_json_bytes(payload))
    return payload


def write_manifest(staging_dir: Path, payload: dict[str, Any]) -> None:
    digest_payload = dict(payload)
    digest_payload.pop("sealed_content_digest", None)
    payload["sealed_content_digest"] = sha256_digest(canonical_json_bytes(digest_payload))
    (staging_dir / "corpus-manifest.json").write_bytes(canonical_json_bytes(payload))


def stage_valid_pack(
    staging_dir: Path,
    *,
    sources: list[tuple[str, str, bytes]] | None = None,
    corpus_version: str = "1.0.0",
) -> dict[str, Any]:
    staged_sources = sources or [
        ("synthetic-rule-001", "sources/synthetic-rule-001.md", "휴가 규정 예시\n".encode()),
    ]
    staging_dir.mkdir(parents=True)
    descriptors: list[dict[str, Any]] = []
    for source_id, relative_path, source_bytes in staged_sources:
        source_path = staging_dir / relative_path
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(source_bytes)
        descriptors.append(
            source_descriptor(
                source_id=source_id,
                path=relative_path,
                source_bytes=source_bytes,
            )
        )
    payload = corpus_manifest(descriptors, corpus_version=corpus_version)
    write_manifest(staging_dir, payload)
    return payload
