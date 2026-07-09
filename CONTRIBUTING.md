# Contributing to BRI

Thank you for your interest in BRI. This document is the single source of
truth for environment setup, the test loop, the style guide, and the pull
request workflow. It is short on purpose; everything else is linked.

## Code of conduct

Every contributor is expected to follow [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
It is the Contributor Covenant v2.1.

## Environment setup — one command

```bash
make dev
```

`make dev` runs `pip install -e .[dev]` and confirms that `pytest`, `ruff`,
and `mypy` are on `PATH`. That is the only supported setup path; if your
shell can't run it, open an issue and we'll fix the Makefile, not the docs.

Optional extras:

| Extra | What it adds |
|---|---|
| `.[ai]` | BLIP captioning, Whisper transcription, YOLOv8 detection, sentence-transformers embeddings. Heavy — install only when you need local multimodal tools. |
| `.[docs]` | mkdocs-material + mkdocstrings for the docs site. |

## Test loop

```bash
make test         # full pytest run, ~4 minutes on cold cache
make smoke        # FastAPI smoke check against a running server
```

Fast inner loop while editing:

```bash
pytest tests/unit -q              # unit suite only
ruff check . && ruff format --check .
mypy mcp_server services tools storage ui models config
```

CI is the source of truth for the full matrix; locally, run the
narrowest command that catches your change.

## Style guide

- **Python:** [ruff](https://docs.astral.sh/ruff/) enforces lint and
  format. The config lives in `pyproject.toml`. Run `ruff format .`
  before committing.
- **Types:** [mypy](https://mypy-lang.org/) with per-module strict
  overrides in `pyproject.toml`. New code should add type annotations;
  CI enforces strict on `services/errors`, `mcp_server/response_models`,
  and the `models/` package.
- **Markdown:** [markdownlint](https://github.com/DavidAnson/markdownlint)
  via `markdownlint.json`. Run `markdownlint docs README.md` before
  committing.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/).
  Pre-commit enforces this on the commit-msg hook.
- **Docstrings:** every public function and every module get a one-line
  docstring stating the contract. The mkdocs site auto-generates an API
  reference from these.
- **Errors:** every exception subclasses `services.errors.BriError`.
  Catch only `BriError` at the UI / API boundary; let genuine bugs crash.

## Branch naming

| Prefix | Use for |
|---|---|
| `feat/<topic>` | New user-facing capability |
| `fix/<topic>` | Bug fix |
| `refactor/<topic>` | Internal change with no behaviour change |
| `docs/<topic>` | Documentation only |
| `chore/<topic>` | Tooling, CI, dependencies |
| `test/<topic>` | Tests only |

The branch must be fast-forwarded or rebased onto the latest `master`
before the review.

## Pull requests

1. Open a PR against `master` from your `feat/<topic>` branch.
2. Fill in the `.github/PULL_REQUEST_TEMPLATE.md` checklist.
3. Make sure `pytest tests/`, `ruff check`, and `mypy mcp_server
   services tools storage ui models config` pass locally before
   requesting review.
4. Wait for CI to pass. The required-check workflow is `.github/workflows/ci.yml`.
5. Address review feedback in additional commits; squash on merge.

## Review SLA

The maintainer team aims to give a first review within **two business
days** of opening the PR. If you don't hear back, ping the PR with a
`@reviewers` mention.

## Reporting security issues

See [`SECURITY.md`](SECURITY.md). Please **do not** open public issues
for security vulnerabilities.

## Maintainer roles

See [`MAINTAINERS.md`](MAINTAINERS.md) and [`GOVERNANCE.md`](GOVERNANCE.md).

## Changelog

Every PR that changes user-visible behaviour must add a one-line entry
to the unreleased section of [`CHANGELOG.md`](CHANGELOG.md). The format
follows [Keep a Changelog](https://keepachangelog.com/).