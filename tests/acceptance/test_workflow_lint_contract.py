import re
from pathlib import Path
from typing import cast

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AGENTS_PATH = REPOSITORY_ROOT / "AGENTS.md"
WORKFLOW_PATH = REPOSITORY_ROOT / ".github/workflows/python-ci.yml"
ACTIONLINT_IMAGE_PATTERN: re.Pattern[str] = re.compile(
    r"docker\.io/rhysd/actionlint@sha256:[0-9a-f]{64}",
)


def _actionlint_image_reference(path: Path) -> str:
    references = ACTIONLINT_IMAGE_PATTERN.findall(path.read_text(encoding="utf-8"))
    assert len(references) == 1, (
        f"{path.relative_to(REPOSITORY_ROOT)} must contain exactly one "
        f"digest-pinned actionlint image reference, found {references}"
    )
    return cast(str, references[0])


def test_documented_actionlint_image_matches_the_ci_workflow() -> None:
    assert _actionlint_image_reference(AGENTS_PATH) == _actionlint_image_reference(
        WORKFLOW_PATH,
    )
