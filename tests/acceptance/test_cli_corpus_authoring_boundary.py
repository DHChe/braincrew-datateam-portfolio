from __future__ import annotations

import json
import re
import socket
import subprocess
from pathlib import Path

import pytest

from tests.authoring_boundary_fixture import (
    create_clean_braincrew_source,
    launch_arguments,
    run_cli,
    sandbox_backend_available,
    write_executable,
)


@pytest.mark.skipif(not sandbox_backend_available(), reason="no supported OS sandbox backend")
def test_cli_exposes_only_declared_inputs_and_denies_repository_network_and_feedback(
    tmp_path: Path,
) -> None:
    source_root = create_clean_braincrew_source(tmp_path)
    ax_root = tmp_path / "AX_portfolio"
    ax_root.mkdir()
    (ax_root / "private-source.py").write_text("ax-private-sentinel\n", encoding="utf-8")
    database_path = tmp_path / "authoring.db"
    database_path.write_text("database-sentinel\n", encoding="utf-8")
    undeclared_path = tmp_path / "undeclared.txt"
    undeclared_path.write_text("undeclared-filesystem-sentinel\n", encoding="utf-8")
    private_path = tmp_path / "private-company-document.txt"
    private_path.write_text("private-company-sentinel\n", encoding="utf-8")

    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]
        tool_path = write_executable(
            tmp_path / "boundary-probe",
            f"""import json
import os
import socket
from pathlib import Path

inputs = Path(os.environ["BRAINCREW_AUTHORING_INPUT_DIR"])
staging = Path(os.environ["BRAINCREW_AUTHORING_STAGING_DIR"])
braincrew_root = Path({str(source_root)!r})
expected_inputs = {{
    "authoring-brief.md",
    "ax-synthetic-seed-content-v1.schema.json",
    "ax-synthetic-seed-content-v1.schema.sha256",
    "input-digests.json",
}}
results = {{"allowed_inputs": sorted(path.name for path in inputs.iterdir())}}
targets = {{
    "braincrew_repository": (
        braincrew_root
        / "docs"
        / "corpus"
        / "braincrew-evaluation-corpus-v2-authoring-brief.md"
    ),
    "evaluation_dataset": braincrew_root / "datasets" / "evaluation.json",
    "test_fixture": braincrew_root / "tests" / "fixtures" / "case.json",
    "prior_artifact": braincrew_root / "artifacts" / "prior-run.json",
    "credential_file": braincrew_root / ".env",
    "system_credential_store": Path("/Library/Keychains/System.keychain"),
    "private_document": Path({str(private_path)!r}),
    "ax_repository": Path({str(ax_root)!r}) / "private-source.py",
    "database": Path({str(database_path)!r}),
    "undeclared_filesystem": Path({str(undeclared_path)!r}),
    "post_seal_feedback": braincrew_root / "post-seal" / "validator-result.json",
}}
for name, path in targets.items():
    try:
        path.read_bytes()
    except OSError:
        results[name] = "denied"
    else:
        results[name] = "allowed"
    try:
        path.stat()
    except OSError:
        results[f"{{name}}_metadata"] = "denied"
    else:
        results[f"{{name}}_metadata"] = "allowed"
try:
    socket.create_connection(("127.0.0.1", {port}), timeout=0.2)
except OSError:
    results["network"] = "denied"
else:
    results["network"] = "allowed"
results["credential_environment"] = (
    "denied" if os.environ.get("OPENAI_API_KEY") is None else "allowed"
)
results["input_set_exact"] = set(results["allowed_inputs"]) == expected_inputs
(staging / "capability-probe.json").write_text(
    json.dumps(results, sort_keys=True), encoding="utf-8"
)
""",
        )

        staging_dir = tmp_path / "empty-staging"
        staging_dir.mkdir()
        receipt_path = tmp_path / "receipts" / "independence.json"
        result = run_cli(
            *launch_arguments(
                source_root=source_root,
                staging_dir=staging_dir,
                receipt_path=receipt_path,
                tool_path=tool_path,
            ),
            environment={"OPENAI_API_KEY": "credential-sentinel"},
        )

    assert result.returncode == 0, result.stderr
    probe = json.loads((staging_dir / "capability-probe.json").read_text(encoding="utf-8"))
    assert probe.pop("allowed_inputs") == [
        "authoring-brief.md",
        "ax-synthetic-seed-content-v1.schema.json",
        "ax-synthetic-seed-content-v1.schema.sha256",
        "input-digests.json",
    ]
    assert probe.pop("input_set_exact") is True
    assert set(probe.values()) == {"denied"}

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    expected_sha = subprocess.run(
        ["git", "-C", source_root, "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert receipt["schema_version"] == "corpus-authoring-independence-receipt-v1"
    assert receipt["braincrew_commit_sha"] == expected_sha
    assert receipt["tool"]["name"] == "boundary-probe"
    assert receipt["tool"]["version"] == "1.0.0"
    assert receipt["tool"]["executable_sha256"].startswith("sha256:")
    assert receipt["tool"]["invocation_sha256"].startswith("sha256:")
    assert set(receipt["input_digests"]) == {
        "brief_sha256",
        "schema_sha256",
        "schema_digest_file_sha256",
        "declared_inputs_sha256",
    }
    assert set(receipt["denied_capability_classes"]) == {
        "ax_repository",
        "braincrew_repository",
        "credential_store",
        "database",
        "evaluation_dataset",
        "network",
        "post_seal_feedback",
        "prior_artifact",
        "private_document",
        "test_fixture",
        "undeclared_filesystem",
    }
    assert re.fullmatch(r"authoring-[0-9a-f]{32}", receipt["staging_run_id"])
    assert receipt["exit_state"] == {"exit_code": 0, "status": "COMPLETED"}
    assert receipt["output"]["file_count"] == 1
    assert receipt["output"]["files"][0]["ordinal"] == 0
    assert receipt["output"]["files"][0]["path_sha256"].startswith("sha256:")
    assert receipt["output"]["files"][0]["content_sha256"].startswith("sha256:")
    assert receipt["output"]["tree_sha256"].startswith("sha256:")
    assert receipt["receipt_digest"].startswith("sha256:")

    receipt_text = receipt_path.read_text(encoding="utf-8")
    for forbidden in (
        "credential-sentinel",
        "private-company-sentinel",
        "query-sentinel",
        "answer-sentinel",
        "expected-evidence-sentinel",
        "score-sentinel",
        "Verification",
        "post-seal-failure-sentinel",
        "Approved synthetic demo corpus authoring brief",
        str(source_root),
        str(ax_root),
        str(staging_dir),
        str(tool_path),
        str(private_path),
    ):
        assert forbidden not in receipt_text
