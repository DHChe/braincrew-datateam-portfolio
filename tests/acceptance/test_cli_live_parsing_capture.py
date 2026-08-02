from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import httpx
import pytest
from typer.testing import CliRunner

from braincrew.dataset_registry import validate_dataset_bundle
from braincrew.repository import RepositoryState

PROJECT_ROOT = Path(__file__).parents[2]
DATASET_MANIFEST = PROJECT_ROOT / "datasets" / "dataset_manifest_v3.json"
PINNED_AX_SHA = "3bb27f870d244fbc8debba91eb408e825caa9e03"
TENANT_ID = "ae09ec7f-e2b8-4f83-99bb-7031ef5eb6e2"
USER_ID = "12171ca4-a001-40da-881b-b87cce42e9b2"
CAPTURED_AT = datetime(2026, 8, 2, 6, 0, tzinfo=UTC)


def _check(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _sha256_text(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def _validated_dataset() -> Any:
    validation = validate_dataset_bundle(DATASET_MANIFEST)
    _check(validation.state == "VALID", "frozen v3 dataset must validate")
    _check(validation.snapshot is not None, "valid dataset must carry its snapshot")
    return validation


def _poison_parsing_expected_values(validation: Any) -> Any:
    snapshot = validation.snapshot
    _check(snapshot is not None, "poisoning requires a dataset snapshot")
    poisoned_cases = tuple(
        case.model_copy(
            update={
                "expected": case.expected.model_copy(
                    update={
                        "structure": case.expected.structure.model_copy(
                            update={"headings": ["answer-key-poison"]}
                        ),
                        "metadata": {"answer-key": "poison"},
                        "evidence_spans": [
                            span.model_copy(update={"text": "answer-key-poison"})
                            for span in case.expected.evidence_spans
                        ],
                    }
                )
            }
        )
        if case.split == "verification"
        else case
        for case in snapshot.parsing_dataset.cases
    )
    return validation.model_copy(
        update={
            "snapshot": snapshot.model_copy(
                update={
                    "parsing_dataset": snapshot.parsing_dataset.model_copy(
                        update={"cases": poisoned_cases}
                    )
                }
            )
        }
    )


def test_live_parsing_capture_uses_only_the_ax_response_not_dataset_expected_values(
    tmp_path: Path,
) -> None:
    from braincrew.live_experiment import (
        ReviewedPrincipalBinding,
        SutStateSubject,
        SutStateWarrant,
        capture_live_parsing_observations,
        write_live_parsing_observation_capture,
    )

    validation = _poison_parsing_expected_values(_validated_dataset())
    snapshot = validation.snapshot
    _check(snapshot is not None, "live parsing capture requires a dataset snapshot")
    cases = {
        case.id: case for case in snapshot.parsing_dataset.cases if case.split == "verification"
    }
    attachment_ids = {case.document.id: f"attachment-{case.id}" for case in cases.values()}
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        case_id = request.headers["x-eval-case-id"]
        case = cases[case_id]
        attachment_id = attachment_ids[case.document.id]
        calls.append((request.url.path, case_id))
        _check(request.method == "GET", "parsing capture must use AX's read-only parse operation")
        _check(
            request.url.path == f"/v1/evaluation/attachments/{attachment_id}/parse-observation",
            "attachment identity must come from the reviewed mapping",
        )
        _check(
            request.headers["x-ax-roles"] == "HRPractitioner",
            "parsing capture must use the reviewed parsing role",
        )
        source_text = case.document.canonical_text
        span_text = source_text[:24]
        return httpx.Response(
            200,
            json={
                "schema_version": "ax-parse-observation-v1",
                "attachment_id": attachment_id,
                "lifecycle_state": "approved",
                "parse_state": "completed",
                "materialization_state": "ready",
                "parse_available": True,
                "parser_name": "utf8-text",
                "parser_version": "stdlib-1",
                "failure_code": None,
                "extracted_text": source_text,
                "extracted_text_digest": _sha256_text(source_text),
                "text_truncated": False,
                "evidence_spans": [
                    {
                        "id": f"observed-{case_id}",
                        "text": span_text,
                        "start_char": 0,
                        "end_char": len(span_text),
                        "source_text_digest": _sha256_text(source_text),
                    }
                ],
                "headings": [f"observed:{case_id}"],
                "metadata": {"observed_document": case.document.id},
                "table": None,
                "list": None,
                "unavailable_fields": [],
            },
        )

    capture = capture_live_parsing_observations(
        run_id="issue-131-parsing-v3",
        captured_at=CAPTURED_AT,
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=True),
        sut_state=SutStateWarrant(
            schema_version="sut-state-warrant-v1",
            method="read-only-git-check",
            subject=SutStateSubject(
                repository="AX_portfolio",
                checkout_path=str(tmp_path / "ax"),
                checked_at=CAPTURED_AT,
            ),
            commit_sha=PINNED_AX_SHA,
            dirty_worktree=False,
        ),
        base_url="https://ax.example.test",
        principal=ReviewedPrincipalBinding(tenant_id=TENANT_ID, user_id=USER_ID),
        attachment_ids_by_document_id=attachment_ids,
        dataset_validation=validation,
        transport=httpx.MockTransport(handler),
    )

    _check(
        capture.observations.adapter_version == "ax-sut-http-v1",
        "a live AX response must not be labelled as a fixture adapter",
    )
    _check(
        capture.observations.parser_version == "stdlib-1",
        "the batch parser version must come from AX",
    )
    _check(
        capture.manifest.evaluation_plane_dirty is True,
        "an uncommitted capture implementation must remain observable in its provenance",
    )
    _check(
        capture.manifest.sut_state_warrant.commit_sha == PINNED_AX_SHA,
        "the capture must bind the exact under-test AX commit",
    )
    _check(
        {observation.case_id for observation in capture.observations.observations} == set(cases),
        "the bundle must cover exactly the six v3 Verification parsing cases",
    )
    for observation in capture.observations.observations:
        _check(
            observation.headings == [f"observed:{observation.case_id}"],
            "headings must come from AX rather than the dataset answer key",
        )
        _check(
            observation.metadata.get("answer-key") is None,
            "the dataset answer key must never appear in a live observation",
        )
        _check(
            all(span.text != "answer-key-poison" for span in observation.evidence_spans),
            "evidence span text must come from AX rather than the dataset answer key",
        )
        _check(
            observation.table is None and observation.list is None,
            "table and list must reflect the AX response, which supplies neither here",
        )
    _check(
        calls
        == [
            (
                f"/v1/evaluation/attachments/{attachment_ids[cases[case_id].document.id]}/parse-observation",
                case_id,
            )
            for case_id in sorted(cases)
        ],
        "capture must issue exactly the six parsing requests and no answer or retrieval request",
    )
    artifact_paths = write_live_parsing_observation_capture(capture, tmp_path / "artifacts")
    _check(
        [path.name for path in artifact_paths]
        == [
            "issue-131-parsing-v3.parsing-capture-manifest.json",
            "issue-131-parsing-v3.parsing-observations.json",
        ],
        "live parsing capture must preserve sibling create-only artifact names",
    )
    _check(
        all(path.is_file() for path in artifact_paths),
        "live parsing capture must write both declared artifacts",
    )
    with pytest.raises(FileExistsError, match="live parsing capture artifact already exists"):
        write_live_parsing_observation_capture(capture, tmp_path / "artifacts")


def test_live_parsing_capture_refuses_a_response_for_a_different_frozen_document(
    tmp_path: Path,
) -> None:
    from braincrew.live_experiment import (
        ReviewedPrincipalBinding,
        SutStateSubject,
        SutStateWarrant,
        capture_live_parsing_observations,
    )

    validation = _validated_dataset()
    snapshot = validation.snapshot
    _check(snapshot is not None, "live parsing capture requires a dataset snapshot")
    cases = tuple(
        sorted(
            (case for case in snapshot.parsing_dataset.cases if case.split == "verification"),
            key=lambda case: case.id,
        )
    )
    attachment_ids = {case.document.id: f"attachment-{case.id}" for case in cases}
    observed_case = cases[0]
    wrong_document = cases[1].document.canonical_text

    def handler(request: httpx.Request) -> httpx.Response:
        _check(
            request.headers["x-eval-case-id"] == observed_case.id,
            "capture must reject the first mismatched response before a second request",
        )
        return httpx.Response(
            200,
            json={
                "schema_version": "ax-parse-observation-v1",
                "attachment_id": attachment_ids[observed_case.document.id],
                "lifecycle_state": "approved",
                "parse_state": "completed",
                "materialization_state": "ready",
                "parse_available": True,
                "parser_name": "utf8-text",
                "parser_version": "stdlib-1",
                "failure_code": None,
                "extracted_text": wrong_document,
                "extracted_text_digest": _sha256_text(wrong_document),
                "text_truncated": False,
                "evidence_spans": [],
                "headings": [],
                "metadata": {},
                "table": None,
                "list": None,
                "unavailable_fields": [],
            },
        )

    with pytest.raises(
        ValueError,
        match="live parsing response text does not match the frozen parsing document",
    ):
        capture_live_parsing_observations(
            run_id="issue-131-document-mismatch",
            captured_at=CAPTURED_AT,
            evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
            sut_state=SutStateWarrant(
                schema_version="sut-state-warrant-v1",
                method="read-only-git-check",
                subject=SutStateSubject(
                    repository="AX_portfolio",
                    checkout_path=str(tmp_path / "ax"),
                    checked_at=CAPTURED_AT,
                ),
                commit_sha=PINNED_AX_SHA,
                dirty_worktree=False,
            ),
            base_url="https://ax.example.test",
            principal=ReviewedPrincipalBinding(tenant_id=TENANT_ID, user_id=USER_ID),
            attachment_ids_by_document_id=attachment_ids,
            dataset_validation=validation,
            transport=httpx.MockTransport(handler),
        )


@pytest.mark.parametrize(
    ("violation", "message"),
    [
        ("attachment", "live parsing response attachment identity does not match the mapping"),
        ("text", "live parsing response text does not match the frozen parsing document"),
        ("digest", "live parsing response digest does not match the frozen parsing document"),
        ("span", "live parsing evidence span digest does not match the frozen document"),
        (
            "mapping",
            "attachment mapping must cover exactly the Verification parsing documents",
        ),
    ],
)
def test_live_parsing_capture_refuses_each_independent_identity_guard(
    violation: str,
    message: str,
    tmp_path: Path,
) -> None:
    from braincrew.live_experiment import (
        ReviewedPrincipalBinding,
        SutStateSubject,
        SutStateWarrant,
        capture_live_parsing_observations,
    )

    validation = _validated_dataset()
    snapshot = validation.snapshot
    _check(snapshot is not None, "live parsing capture requires a dataset snapshot")
    cases = {
        case.id: case for case in snapshot.parsing_dataset.cases if case.split == "verification"
    }
    attachment_ids = {case.document.id: f"attachment-{case.id}" for case in cases.values()}
    if violation == "mapping":
        attachment_ids["not-a-v3-document"] = "attachment-outside-v3"

    def handler(request: httpx.Request) -> httpx.Response:
        case = cases[request.headers["x-eval-case-id"]]
        source_text = case.document.canonical_text
        attachment_id = f"attachment-{case.id}"
        payload: dict[str, object] = {
            "schema_version": "ax-parse-observation-v1",
            "attachment_id": attachment_id,
            "lifecycle_state": "approved",
            "parse_state": "completed",
            "materialization_state": "ready",
            "parse_available": True,
            "parser_name": "utf8-text",
            "parser_version": "stdlib-1",
            "failure_code": None,
            "extracted_text": source_text,
            "extracted_text_digest": _sha256_text(source_text),
            "text_truncated": False,
            "evidence_spans": [
                {
                    "id": f"observed-{case.id}",
                    "text": source_text[:1],
                    "start_char": 0,
                    "end_char": 1,
                    "source_text_digest": _sha256_text(source_text),
                }
            ],
            "headings": [],
            "metadata": {},
            "table": None,
            "list": None,
            "unavailable_fields": [],
        }
        if violation == "attachment":
            payload["attachment_id"] = "attachment-for-a-different-document"
        if violation == "text":
            payload["extracted_text"] = f"{source_text} mismatch"
        if violation == "digest":
            payload["extracted_text_digest"] = "sha256:" + "0" * 64
        if violation == "span":
            payload["evidence_spans"] = [
                {
                    "id": f"observed-{case.id}",
                    "text": source_text[:1],
                    "start_char": 0,
                    "end_char": 1,
                    "source_text_digest": "sha256:" + "0" * 64,
                }
            ]
        return httpx.Response(200, json=payload)

    with pytest.raises(ValueError, match=message):
        capture_live_parsing_observations(
            run_id=f"issue-131-{violation}-mismatch",
            captured_at=CAPTURED_AT,
            evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
            sut_state=SutStateWarrant(
                schema_version="sut-state-warrant-v1",
                method="read-only-git-check",
                subject=SutStateSubject(
                    repository="AX_portfolio",
                    checkout_path=str(tmp_path / "ax"),
                    checked_at=CAPTURED_AT,
                ),
                commit_sha=PINNED_AX_SHA,
                dirty_worktree=False,
            ),
            base_url="https://ax.example.test",
            principal=ReviewedPrincipalBinding(tenant_id=TENANT_ID, user_id=USER_ID),
            attachment_ids_by_document_id=attachment_ids,
            dataset_validation=validation,
            transport=httpx.MockTransport(handler),
        )


def test_live_parsing_capture_cli_derives_identity_and_accepts_only_a_versioned_mapping(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from braincrew import cli
    from braincrew.live_experiment import (
        LiveParsingAttachmentMapping,
        ReviewedPrincipalBinding,
    )

    captured: dict[str, object] = {}
    mapping = LiveParsingAttachmentMapping(
        schema_version="live-parsing-attachment-mapping-v1",
        document_attachment_ids={f"demo-{index}": f"attachment-{index}" for index in range(1, 7)},
    )

    def fake_binding(path: Path) -> ReviewedPrincipalBinding:
        captured["receipt"] = path
        return ReviewedPrincipalBinding(tenant_id=TENANT_ID, user_id=USER_ID)

    def fake_repository_state(path: Path | None = None) -> RepositoryState:
        if path is None:
            return RepositoryState(commit_sha="a" * 40, dirty_worktree=True)
        captured["sut_checkout"] = path
        return RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False)

    def fake_mapping(path: Path) -> LiveParsingAttachmentMapping:
        captured["mapping_path"] = path
        return mapping

    def fake_capture(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace(manifest=SimpleNamespace(logical_digest="sha256:" + "b" * 64))

    def fake_write(capture: object, output_dir: Path) -> tuple[Path, Path]:
        captured["capture"] = capture
        captured["output_dir"] = output_dir
        return (
            output_dir / "parsing-live.parsing-capture-manifest.json",
            output_dir / "parsing-live.parsing-observations.json",
        )

    monkeypatch.setattr(cli, "load_reviewed_principal_binding", fake_binding)
    monkeypatch.setattr(cli, "capture_repository_state", fake_repository_state)
    monkeypatch.setattr(cli, "load_live_parsing_attachment_mapping", fake_mapping)
    monkeypatch.setattr(cli, "capture_live_parsing_observations", fake_capture)
    monkeypatch.setattr(cli, "write_live_parsing_observation_capture", fake_write)
    receipt = tmp_path / "handoff.json"
    receipt.write_text("{}\n", encoding="utf-8")
    mapping_path = tmp_path / "mapping.json"
    mapping_path.write_text("{}\n", encoding="utf-8")
    sut_checkout = tmp_path / "ax"
    sut_checkout.mkdir()

    result = CliRunner().invoke(
        cli.app,
        [
            "capture-live-parsing",
            "--output-dir",
            str(tmp_path / "output"),
            "--run-id",
            "parsing-live",
            "--base-url",
            "https://ax.example.test",
            "--handoff-receipt",
            str(receipt),
            "--attachment-mapping",
            str(mapping_path),
            "--sut-checkout",
            str(sut_checkout),
        ],
    )

    _check(result.exit_code == 0, f"CLI failed: {result.output}")
    _check(captured["receipt"] == receipt, "CLI must derive the principal from its receipt")
    _check(captured["mapping_path"] == mapping_path, "CLI must load the versioned mapping input")
    _check(captured["sut_checkout"] == sut_checkout, "CLI must inspect the SUT checkout")
    _check(
        captured["attachment_ids_by_document_id"] == mapping.document_attachment_ids,
        "CLI must pass the mapping unchanged to the converter",
    )
    _check(
        cast(RepositoryState, captured["evaluation_state"]).dirty_worktree is True,
        "CLI must record a dirty Evaluation Plane rather than invent a clean state",
    )
    _check("--tenant-id" not in result.output, "CLI must not expose a caller-supplied principal")


def test_integrated_provenance_keeps_live_label_and_fixture_run_refuses_it() -> None:
    from braincrew.dataset_run import DatasetAdapterProvenance
    from braincrew.result_store import build_parsing_run_artifact

    provenance = DatasetAdapterProvenance(
        execution_mode="live",
        parsing_version="ax-sut-http-v1",
        retrieval_version="ax-sut-http-v1",
        grounded_version="ax-sut-http-v1",
    )
    _check(
        provenance.parsing_version == "ax-sut-http-v1",
        "the integrated 30-case artifact must retain the actual parser adapter label",
    )
    with pytest.raises(
        ValueError,
        match="standalone parsing-run artifacts require fixture parsing observations",
    ):
        build_parsing_run_artifact(
            dataset=cast(Any, object()),
            observations=cast(
                Any,
                SimpleNamespace(adapter_version="ax-sut-http-v1"),
            ),
            evaluation=cast(Any, object()),
            run_id="issue-131-live-parsing",
            evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
            sut_sha=PINNED_AX_SHA,
        )
