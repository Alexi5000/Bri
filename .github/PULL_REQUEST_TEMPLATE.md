## Summary

<!-- One paragraph: what does this PR do and why? -->

## Type of change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds capability)
- [ ] Breaking change (fix or feature that changes existing behaviour)
- [ ] Documentation update
- [ ] Refactor / chore (no user-visible change)

## Linked issues

<!-- Use "Closes #NN" to auto-close issues. -->

## Test plan

- [ ] `pytest tests/` passes locally
- [ ] `ruff check .` is clean
- [ ] `ruff format --check .` is clean
- [ ] `mypy mcp_server services tools storage ui models config` passes
- [ ] New behaviour is covered by tests (unit, integration, or contract)
- [ ] Snapshot updates are intentional (`pytest --snapshot-update`)

## Documentation

- [ ] Public functions have docstrings (mkdocs reference stays current)
- [ ] `CHANGELOG.md` has an entry under `[Unreleased]`
- [ ] README / docs pages affected by this PR have been updated
- [ ] New environment variables are documented in `.env.example`

## Checklist

- [ ] The branch is rebased on the latest `master`
- [ ] Commit messages follow Conventional Commits
- [ ] No destructive operations against tracked files
- [ ] No secrets, credentials, or `.env` files are committed

## Reviewer notes

<!-- Anything the reviewer should pay particular attention to. -->