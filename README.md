# OpenClaw Config Backup

Sanitized OpenClaw configuration snapshot. Secrets, API keys, tokens, session logs, credentials, delivery queues, and memory files are intentionally excluded or redacted.

## Layout

- `openclaw.json`: global routing, providers, agent bindings, and defaults with secrets redacted.
- `agents/*/agent/models.json`: per-agent model registries.
- `agents/*/agent/auth-profiles.json`: auth profile structure with keys redacted.
- `workspaces/*`: selected workspace instruction files. Personal `USER.md` is redacted.

## Current Routing

- Global default: `google/gemini-2.5-flash`
- `first-principles`: `cliproxyapi/gemini-3.1-flash-lite-preview`
- `dev`: `cliproxyapi/gemini-3.1-flash-lite-preview`

## Restore Notes

Replace `${REDACTED}` placeholders with real secrets locally. Do not commit real secrets.
