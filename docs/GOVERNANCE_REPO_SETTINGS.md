# Repository settings — copy/paste checklist for the GitHub UI

This is a one-time setup guide for whoever owns the GitHub repository.
The contents below should be applied through the web UI at
**Settings → General**, **Settings → Pages**, and the social-preview
metadata. None of this is committed to the repo itself.

## About

| Field | Value |
|---|---|
| Description | Empathetic multimodal video intelligence — Streamlit UI, FastAPI MCP server, and optional local BLIP/Whisper/YOLOv8 tools. |
| Website | https://alexi5000.github.io/Bri |
| Topics | `video-intelligence` `streamlit` `fastapi` `mcp` `groq` `blip` `whisper` `yolov8` `python` `multimodal` `open-source` `agent` `pydantic` `sqlite` `mcp-server` |

## Social preview

Upload `assets/cover.svg` (or `assets/cover.png`) at
**Settings → General → Social preview → Upload an image…**. The PNG is
1240×620 and renders cleanly as the GitHub card.

## Releases

`v1.0.0` shipped 2025-10-16. `v1.1.0` is the next release on
`master` once CI is green on a tag. Subsequent releases follow
[Semantic Versioning](https://semver.org/).

## Default branch

`master`. Branch protection on `master` requires:

- ✅ Pull request reviews (1 approval minimum)
- ✅ All required status checks (`ci`, `docs`, `codeql`)
- ✅ Linear history (no merge commits)
- ✅ Force-push disabled
- ✅ Deletion disabled

## Pages

Source: **GitHub Actions**. The `docs.yml` workflow publishes
`mkdocs-material` output to `ghcr.io/alexi5000/bri-pages` and the
GitHub Pages environment.

## Code security

- Dependabot alerts: enabled (pip + docker + github-actions).
- Dependabot security updates: enabled.
- Secret scanning: enabled.
- Push protection: enabled.
- Code scanning: CodeQL (`codeql.yml` workflow).

## Packages

- `ghcr.io/alexi5000/bri-mcp` — FastAPI MCP image, multi-arch.
- `ghcr.io/alexi5000/bri-ui` — Streamlit UI image, multi-arch.