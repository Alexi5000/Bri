# Security policy

## Supported versions

| Version | Supported |
|---|---|
| `main` | ✅ |
| `v1.1.x` | ✅ |
| `v1.0.x` | ✅ |
| `< v1.0` | ❌ |

Security fixes are back-ported to the latest two minor releases.

## Reporting a vulnerability

**Do not** file a public issue for security vulnerabilities.

Email **security@alexi5000.com** with:

1. A clear description of the issue and its impact.
2. Reproduction steps or a proof-of-concept.
3. Suggested severity (CVSS v3 if you have one).
4. Whether you'd like public credit in the advisory.

You should hear back within **three business days**. We will work with
you to confirm the issue, agree on a fix timeline, and coordinate
disclosure. We follow responsible disclosure: we publish a GHSA advisory
once a fix is available or after 90 days, whichever comes first.

## Coordinated disclosure

Once we confirm a vulnerability, we will:

1. Open a private GitHub Security Advisory.
2. Cut a fix on a maintenance branch.
3. Notify you when the fix is merged.
4. Publish the advisory with a CVE reference.
5. Add a credit line if you want one.

## Out of scope

- Denial-of-service attacks against a public deployment you do not own.
- Social engineering of maintainers.
- Reports about missing security headers on third-party hosts (e.g.
  Streamlit Cloud) — those are operator-side decisions.

## Security best practices for operators

- Rotate `GROQ_API_KEY` periodically and on personnel changes.
- Use a private `DATABASE_PATH` on a filesystem that supports WAL
  (`mode = wal` is the default).
- Set `APP_ENV=production` and never `DEBUG=true` together.
- Front the Streamlit UI with an authenticating reverse proxy when
  exposing it beyond localhost.
- Keep `.env` and `.streamlit/secrets.toml` out of version control
  (already in `.gitignore`).