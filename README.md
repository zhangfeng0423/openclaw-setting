# OpenClaw Config Backup

Richer sanitized OpenClaw configuration snapshot. This repository is designed for version control and upgrade recovery reference. Secrets, API keys, tokens, private keys, raw session logs, credentials, delivery queues, binary browser state, and memory databases are excluded or redacted.

## What Is Included

- Global `openclaw.json` routing and provider structure with secrets redacted.
- Per-agent `models.json` and `auth-profiles.json` structure.
- Session index summaries, without raw conversation transcripts.
- Workspace instruction files, docs, config, and text-based skill source files.
- Cron jobs, Discord model picker preferences, device/identity summaries, update status, and shell completions.

## What Is Not Included

- Real API keys, tokens, private keys, credentials, logs, raw sessions, media, browser data, SQLite memory, and personal `USER.md` content.

## Update

```bash
cd ~/openclaw-config-backup
python3 scripts/export-sanitized.py
git diff
git add .
git commit -m "Update OpenClaw config backup"
git push
```
