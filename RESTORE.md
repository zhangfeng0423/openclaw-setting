# Restore Notes

This repo is not a direct full restore archive because secrets are redacted. Use it to reconstruct routing, agents, workspace instructions, skills, and operational configuration after an OpenClaw upgrade.

For a direct disaster restore, keep a separate encrypted full backup of `~/.openclaw`.

## Key Runtime Layout

- `openclaw.json`: global routing, providers, defaults, bindings.
- `agents/<agent>/agent/models.json`: models each agent can select.
- `agents/<agent>/agent/auth-profiles.json`: auth profile shape; real keys must be reinserted locally.
- `workspaces/<agent>` and `workspace`: agent instruction files, docs, config, and skills.
- `ops`: cron, Discord picker preferences, device/identity summaries.

## Current Model Intent

- Global default: `google/gemini-2.5-flash`
- `first-principles`: `cliproxyapi/gemini-3.1-flash-lite-preview`
- `dev`: `cliproxyapi/gemini-3.1-flash-lite-preview`
