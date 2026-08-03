FROM python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install --no-install-recommends --yes git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.10.8

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --all-groups --no-install-project

COPY . .

# Fixture acceptance tests read Git provenance. This is an image-local source snapshot,
# not a copy of the developer's .git directory or a published-artifact provenance claim.
RUN git init --quiet \
    && git config user.email "container@braincrew.invalid" \
    && git config user.name "Braincrew container" \
    && git add --all \
    && git commit --quiet -m "container source snapshot" \
    && uv sync --frozen --all-groups

CMD ["sh", "-c", "uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest -q && uv run pytest tests/acceptance/test_cli_fixture_gate.py -q"]
