# Governance

BRI is an open-source project maintained by a small set of volunteer
maintainers. This document describes how decisions are made, how to
become a maintainer, and what the project expects from each role.

## Roles

| Role | Responsibility |
|---|---|
| **User** | Files issues, opens PRs, gives feedback. No obligations. |
| **Contributor** | Has had at least one PR merged. Eligible to triage issues. |
| **Maintainer** | Owns one or more areas of the codebase (see `MAINTAINERS.md`). Can merge PRs, cut releases, and vote on governance changes. |
| **Lead Maintainer** | One person who has the final say on disputes and represents the project externally. |

## How decisions get made

Most decisions are made by lazy consensus on the PR or issue thread:

1. Open an issue or PR with a clear proposal.
2. Wait at least **three business days** for feedback.
3. If nobody objects, the relevant maintainer merges.

For larger changes (architecture, breaking changes, governance):

1. Open a GitHub Discussion with the `[rfc]` tag.
2. A maintainer is assigned as the decision owner.
3. The owner writes a final comment with the decision and rationale.
4. The change is implemented in a follow-up PR.

Disputes are resolved by a simple majority vote of all active
maintainers, with the lead maintainer breaking ties.

## Becoming a maintainer

You are eligible after:

1. Three or more merged PRs of substance.
2. Six or more months of active contribution.
3. A nomination by an existing maintainer, seconded by another.

The lead maintainer opens a vote in a private maintainers channel; the
candidate becomes a maintainer on a simple majority.

Maintainers may step down at any time by opening a PR against
`MAINTAINERS.md` that removes their entry.

## Becoming the lead maintainer

The lead maintainer role rotates when the incumbent steps down. The
incumbent nominates a successor from among the current maintainers; if
no nominee is available, the maintainers elect one by simple majority.

## Code of conduct

Enforcement is the responsibility of the lead maintainer. Complaints
are kept confidential; see [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Project assets

- The `alexi5000/bri-mcp` and `alexi5000/bri-ui` GitHub Container
  Registry packages are owned by the lead maintainer and transferred
  on leadership change.
- The PyPI package `bri-video-agent` is owned by the lead maintainer.
- Trademarks and the BRI wordmark/logo are owned by the project; any
  commercial use requires written permission from the lead maintainer.

## Amendments

Amendments to this document require a simple majority vote of all
active maintainers and a public comment period of at least seven days.