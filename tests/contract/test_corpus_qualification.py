from __future__ import annotations

import subprocess
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

import braincrew.corpus_qualification as qualification_module
from braincrew.corpus_qualification import CorpusQualificationError, qualify_corpus_pack
from braincrew.dataset_registry import validate_dataset_bundle

from ..corpus_qualification_v2_fixture import (
    DATASET_V1_MANIFEST,
    DATASET_V2_MANIFEST,
    qualification_command,
    rewrite_manifest,
    run_cli,
    seal_qualification_pack,
    stage_dataset_v2_bundle,
    stage_qualification_pack,
)

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_dataset_v2_manifest_reuses_the_frozen_100_case_components() -> None:
    assert DATASET_V2_MANIFEST.exists()
    v1 = validate_dataset_bundle(DATASET_V1_MANIFEST)
    v2 = validate_dataset_bundle(DATASET_V2_MANIFEST)

    assert v1.state == "VALID"
    assert v2.state == "VALID"
    assert v1.snapshot is not None
    assert v2.snapshot is not None
    assert v2.snapshot.manifest.dataset_version == "2.0.0"
    assert len(v2.snapshot.case_records) == 100
    assert v2.snapshot.component_digests == v1.snapshot.component_digests
    assert v2.snapshot.dataset_digest != v1.snapshot.dataset_digest
    assert v2.snapshot.manifest.dataset_card.path == "DATASET_CARD_V2.md"
    dataset_card = DATASET_V2_MANIFEST.with_name("DATASET_CARD_V2.md").read_text("utf-8")
    assert "Dataset version: `2.0.0`" in dataset_card
    assert v2.snapshot.dataset_digest in dataset_card


def test_wheel_contains_the_exact_dataset_v2_replay_bundle(tmp_path: Path) -> None:
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
    } <= names


def test_qualification_rolls_back_both_outputs_if_pair_publication_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_manifest = stage_dataset_v2_bundle(tmp_path / "dataset")
    staging_dir = tmp_path / "staging"
    stage_qualification_pack(staging_dir)
    sealed_dir = seal_qualification_pack(staging_dir, tmp_path / "sealed")
    qualification_os = cast(Any, qualification_module).os
    real_link = qualification_os.link

    def fail_import_link(source: Path, destination: Path) -> None:
        if Path(destination).name == "import-manifest.json":
            raise OSError("simulated publication failure")
        real_link(source, destination)

    monkeypatch.setattr(qualification_os, "link", fail_import_link)

    with pytest.raises(
        CorpusQualificationError,
        match="CORPUS_PACK_SCHEMA_INVALID",
    ):
        qualify_corpus_pack(
            sealed_dir=sealed_dir,
            dataset_manifest_path=dataset_manifest,
            tenant_slug="braincrew-demo-tenant",
            demo_company_id="braincrew-demo-company",
        )

    assert not (sealed_dir / "qualification-receipt.json").exists()
    assert not (sealed_dir / "import-manifest.json").exists()


Mutation = Callable[[Path], None]


def _source_mutation(relative_path: str) -> Mutation:
    def mutate(sealed_dir: Path) -> None:
        source_path = sealed_dir / relative_path
        source_path.write_bytes(source_path.read_bytes() + b"x")

    return mutate


def _manifest_mutation(change: Callable[[dict[str, Any]], None]) -> Mutation:
    return lambda sealed_dir: rewrite_manifest(sealed_dir, change)


@pytest.mark.parametrize(
    ("pack_options", "mutate", "expected_blocker"),
    [
        ({"omit_source_id": "synthetic-rule-001"}, None, "CORPUS_REQUIRED_SOURCE_MISSING"),
        (
            {"mismatched_source_id": "synthetic-rule-001"},
            None,
            "CORPUS_SOURCE_TEXT_DIGEST_MISMATCH",
        ),
        (
            {"missing_required_role": ("synthetic-rule-001", "HRPractitioner")},
            None,
            "CORPUS_REQUIRED_VISIBILITY_MISMATCH",
        ),
        (
            {"exposed_forbidden_role": ("rule-va-001", "Employee")},
            None,
            "CORPUS_FORBIDDEN_VISIBILITY_MISMATCH",
        ),
        ({"include_distractor": False}, None, "CORPUS_REQUIRED_SOURCE_MISSING"),
        (
            {},
            _manifest_mutation(
                lambda payload: payload["sources"][0].__setitem__("provenance_status", "pending")
            ),
            "CORPUS_PROVENANCE_REVIEW_REQUIRED",
        ),
        (
            {},
            _manifest_mutation(lambda payload: payload.__setitem__("unexpected", True)),
            "CORPUS_PACK_SCHEMA_INVALID",
        ),
        ({}, _source_mutation("sources/synthetic-rule-001.md"), "CORPUS_PACK_DIGEST_MISMATCH"),
    ],
)
def test_qualification_fails_closed_with_typed_blockers_and_no_outputs(
    tmp_path: Path,
    pack_options: dict[str, Any],
    mutate: Mutation | None,
    expected_blocker: str,
) -> None:
    dataset_manifest = stage_dataset_v2_bundle(tmp_path / "dataset")
    staging_dir = tmp_path / "staging"
    stage_qualification_pack(staging_dir, **pack_options)
    sealed_dir = seal_qualification_pack(staging_dir, tmp_path / "sealed")
    if mutate is not None:
        mutate(sealed_dir)
    before = {
        path.relative_to(sealed_dir): path.read_bytes()
        for path in sealed_dir.rglob("*")
        if path.is_file()
    }

    result = run_cli(*qualification_command(sealed_dir, dataset_manifest))

    assert result.returncode == 2
    assert expected_blocker in result.stderr
    assert not (sealed_dir / "qualification-receipt.json").exists()
    assert not (sealed_dir / "import-manifest.json").exists()
    assert {
        path.relative_to(sealed_dir): path.read_bytes()
        for path in sealed_dir.rglob("*")
        if path.is_file()
    } == before


def test_qualification_rejects_the_wrong_dataset_identity(tmp_path: Path) -> None:
    staging_dir = tmp_path / "staging"
    stage_qualification_pack(staging_dir)
    sealed_dir = seal_qualification_pack(staging_dir, tmp_path / "sealed")

    result = run_cli(*qualification_command(sealed_dir, DATASET_V1_MANIFEST))

    assert result.returncode == 2
    assert "CORPUS_PACK_SCHEMA_INVALID" in result.stderr
    assert "braincrew-evaluation-dataset@2.0.0" in result.stderr
    assert not (sealed_dir / "qualification-receipt.json").exists()
    assert not (sealed_dir / "import-manifest.json").exists()
