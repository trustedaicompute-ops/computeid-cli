# Changelog

## 2.0.0 (unreleased)

The first release whose authenticated commands work against the live ComputeID API. 1.1.0 was never published, so its changes are part of this release.

### Breaking
- **`computeid login` takes an API key instead of an admin password.**
  - The old login called `/api/admin/login`, which the API does not serve, so no 1.x install could log in.
  - The key is checked with `GET /v1/agents` before it's saved to `~/.computeid/config.json`.
  - That file is now written owner-only (mode 600).
  - Run `computeid login` once after upgrading.
- **API-key auth only.** All authenticated requests send `X-API-Key`. 1.x sent `Authorization: Bearer <token>`, which the API ignores, or no credentials at all, so `agent list/issue/check/log/audit/revoke` and `logs` returned 401.
- **The module is renamed `cli` → `computeid_cli`.**
  - The old top-level module name `cli` could clash with other packages.
  - The `computeid` command is unchanged.
  - `python -m computeid_cli` also works.
- **Python 3.9+** (3.8 is end-of-life).

### Added
- **`COMPUTEID_API_KEY`** environment variable overrides the saved key, for CI.
- **`computeid logout`** removes the saved key.

### Fixed
- **License metadata.** It now says Apache-2.0, matching `LICENSE`; 1.x metadata said MIT.
- **Project URLs** point at this repository (1.x pointed at computeid-sdk).
- **Version.** `--version` now matches the package version; 1.x reported 1.0.1 for 1.0.2.
- **Docs.** The README and `INTEGRATION.md` list only commands that exist (1.x documented `device …` commands that were never shipped) and include the API key in every authenticated example.

### Packaging
- Built from `pyproject.toml` (replaces `setup.py`).
- Published from GitHub Actions with PyPI trusted publishing (no stored token).

## 1.0.2
Last release before 2.0.0 (on PyPI).
