# README_TEMPLATE.md

> **Audience:** the next person writing or rewriting `README.md` for this project.
> **Goal:** every README follows the same ten sections, in this exact order.
> **Editing rule:** sections can be added at the *end*; their order is fixed.

The BRI README is a customer-facing document. Newcomers should be able to clone, run, ship a PR, and understand the project's stance on contributions without ever leaving the README.

---

## Section order

1. **Tagline** — one line, ≤ 80 characters, no period. The product's elevator pitch.
2. **Badges** — `shields.io` badges for: build status, license, Python version, downloads, container, coverage, and any project-defining dependency.
3. **One-paragraph positioning** — what the project is, who it's for, and what it replaces. Three sentences, max.
4. **Hero** — either a screenshot of the running application or an ASCII / Mermaid diagram of the architecture. Place directly under the positioning paragraph.
5. **30-second quickstart** — copy-paste-runnable instructions for the simplest viable deployment. One terminal block.
6. **5-minute tutorial** — slightly longer path: clone, configure, run, hit the first endpoint, query the first video. Three or four terminal blocks at most.
7. **Architecture diagram** — Mermaid `flowchart` or `sequence` showing user → UI → middle layer → API → tools → storage. The diagram MUST be Mermaid, not an image, so it stays reviewable in PRs.
8. **API surface table** — every public endpoint, every public tool, every public CLI command. Markdown table with columns: name, kind, description.
9. **Configuration table** — every environment variable documented in `.env.example`, plus a column describing default and side effects.
10. **Contributing pointer** — single link to `CONTRIBUTING.md` and a one-line summary.
11. **License** — single link to `LICENSE` and a one-line summary.

That is the entire template. Eleven sections.

---

## Writing rules

- **Sentence case in headings.** Capitalize only the first word and proper nouns.
- **No emoji in section headings.** Emoji inside prose (e.g. 💜 in product copy) is allowed.
- **One terminal block per logical step.** Do not paste a wall of commands.
- **Every command must work on a clean checkout.** If a command requires `.env` first, say so.
- **No "TODO" / "FIXME" / "Coming soon".** Either ship the feature or remove the section.
- **No images larger than 1 MB in the README.** Prefer SVG and Mermaid.
- **No marketing fluff.** The README is documentation, not a brochure.

---

## Template skeleton

```markdown
<div align="center">
  <img src="assets/icon.svg" alt="<Project> logo" width="112" />

# <Project> — <Tagline>

### <One-line value proposition, ≤ 12 words.>

[![Build](https://img.shields.io/github/actions/workflow/<owner>/<repo>/ci.yml?branch=master)](https://github.com/<owner>/<repo>/actions)
[![License: <SPDX>](https://img.shields.io/badge/License-<SPDX>-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python)](https://python.org)
[![Coverage](https://img.shields.io/codecov/c/github/<owner>/<repo>)](https://codecov.io/gh/<owner>/<repo>)
[![Container](https://img.shields.io/badge/ghcr.io-<owner>%2F<repo>-2496ed?logo=docker)](https://github.com/<owner>/<repo>/pkgs/container/<repo>)

</div>

<img src="assets/cover.svg" alt="<Project> cover" width="100%" />

<One-paragraph positioning: what it is, who it's for, what it replaces. Three sentences.>

## Hero

\```mermaid
flowchart LR
  A[User] --> B[UI]
  B --> C[API]
  C --> D[Tools]
\```

## 30-second quickstart

\```bash
git clone https://github.com/<owner>/<repo>.git
cd <repo>
cp .env.example .env       # add <REQUIRED_KEY> for live responses
docker compose up --build
\```

Open the UI at <http://localhost:8501> and the API at <http://localhost:8000>.

## 5-minute tutorial

\```bash
# 1. Install the package and dev extras.
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]

# 2. Initialize local state.
python scripts/init_db.py

# 3. Start the API and UI in two terminals.
uvicorn mcp_server.main:app --reload --port 8000
streamlit run app.py
\```

Upload a short video on the welcome screen, then ask the chat panel
"what happens at 0:15?" to see the tool chain in action.

## Architecture

\```mermaid
flowchart LR
  ...
\```

## API surface

| Endpoint | Kind | Description |
|---|---|---|
| `GET /health` | HTTP | Liveness probe and dependency status. |

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `<KEY>` | `<default>` | <Side effect.> |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Released under the [<SPDX> License](LICENSE).
```

---

## Acceptance checklist

Before merging a README change, verify:

- [ ] All eleven sections present, in order.
- [ ] Every terminal command works on a clean clone (CI runs the README check).
- [ ] Every public endpoint listed in the API surface section is reachable.
- [ ] Every env var in the configuration table exists in `.env.example`.
- [ ] No section is shorter than two lines.
- [ ] No broken link.
- [ ] `markdownlint README.md` returns zero warnings.
- [ ] Mermaid blocks render in the GitHub preview.