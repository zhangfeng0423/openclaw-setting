#!/usr/bin/env python3
"""Export a richer sanitized OpenClaw configuration snapshot.

This repository is meant for GitHub backup and review, not direct secret restore.
It keeps configuration shape, routing, models, workspaces, skills, and operational
summaries while redacting credentials, tokens, private keys, logs, memory, and raw sessions.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

SRC = Path(os.environ.get("OPENCLAW_HOME", "/Users/zhangfeng/.openclaw"))
OUT = Path(os.environ.get("OPENCLAW_BACKUP_REPO", "/Users/zhangfeng/openclaw-config-backup"))

SENSITIVE_PARTS = (
    "apikey",
    "api_key",
    "key",
    "token",
    "secret",
    "password",
    "authorization",
    "private",
    "pem",
)
TEXT_EXTS = {
    ".md", ".txt", ".json", ".json5", ".toml", ".yaml", ".yml",
    ".py", ".js", ".ts", ".tsx", ".html", ".css", ".sh", ".bash",
    ".zsh", ".fish", ".ps1", ".org", ".lock", ".gitignore",
}
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", ".cache",
}
EXCLUDE_FILE_GLOBS = {
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.sqlite", "*.db",
    "*.log", "*.bak*", "*.tmp*", ".DS_Store",
}


def is_sensitive_key(key: str) -> bool:
    lower = key.lower()
    return any(part in lower for part in SENSITIVE_PARTS)


def scrub(value: Any, key: str = "") -> Any:
    if is_sensitive_key(key):
        if isinstance(value, dict):
            # Preserve shape for nested auth objects, but redact leaf values.
            return {k: scrub(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [scrub(v, key) for v in value]
        return "${REDACTED}"
    if isinstance(value, dict):
        return {k: scrub(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v, key) for v in value]
    if isinstance(value, str):
        return scrub_secret_patterns(value)
    return value


def scrub_secret_patterns(text: str) -> str:
    text = re.sub(r"AIza[0-9A-Za-z_-]{10,}", "${REDACTED_GOOGLE_API_KEY}", text)
    text = re.sub(r"AQ\.[0-9A-Za-z_-]+", "${REDACTED_API_KEY}", text)
    text = re.sub(r"\b[0-9a-fA-F]{32,}\b", "${REDACTED_HEX_SECRET}", text)
    text = re.sub(r"-----BEGIN [^-]+PRIVATE KEY-----.*?-----END [^-]+PRIVATE KEY-----", "${REDACTED_PRIVATE_KEY}", text, flags=re.S)
    return text


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def copy_json(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    with src.open(encoding="utf-8") as f:
        write_json(dst, scrub(json.load(f)))


def copy_text(src: Path, dst: Path, redact: bool = True) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8", errors="ignore")
    if redact:
        text = scrub_secret_patterns(text)
    dst.write_text(text, encoding="utf-8")


def clean_generated_paths() -> None:
    for rel in [
        "agents", "workspaces", "ops", "completions", "openclaw.json",
        "README.md", "RESTORE.md", "MANIFEST.json",
    ]:
        p = OUT / rel
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()


def copy_workspace(agent: str, ws: Path) -> dict[str, Any]:
    target = OUT / "workspaces" / agent
    summary: dict[str, Any] = {"source": str(ws), "instructionFiles": [], "docs": [], "skills": []}
    for fn in ["AGENTS.md", "SOUL.md", "TOOLS.md", "IDENTITY.md", "USER.md", "HEARTBEAT.md", "BOOTSTRAP.openclaw-default.md"]:
        p = ws / fn
        if not p.exists():
            continue
        summary["instructionFiles"].append(fn)
        if fn == "USER.md":
            (target / fn).parent.mkdir(parents=True, exist_ok=True)
            (target / fn).write_text("# USER.md\n\n${REDACTED_PERSONAL_CONTEXT}\n", encoding="utf-8")
        elif fn == "MEMORY.md":
            continue
        else:
            copy_text(p, target / fn)

    docs = ws / "docs"
    if docs.exists():
        for src in sorted(docs.rglob("*")):
            if src.is_file() and should_copy_text_file(src):
                rel = src.relative_to(ws)
                copy_text(src, target / rel)
                summary["docs"].append(str(rel))

    config = ws / "config"
    if config.exists():
        for src in sorted(config.rglob("*")):
            if src.is_file() and should_copy_text_file(src):
                rel = src.relative_to(ws)
                if src.suffix == ".json":
                    copy_json(src, target / rel)
                else:
                    copy_text(src, target / rel)

    skills = ws / "skills"
    if skills.exists():
        for src in sorted(skills.rglob("*")):
            if src.is_file() and should_copy_text_file(src):
                rel = src.relative_to(ws)
                copy_target = target / rel
                if src.suffix == ".json":
                    copy_json(src, copy_target)
                else:
                    copy_text(src, copy_target)
                parts = rel.parts
                if len(parts) >= 2 and parts[0] == "skills" and parts[1] not in summary["skills"]:
                    summary["skills"].append(parts[1])

    write_json(target / "workspace-summary.json", summary)
    return summary


def should_copy_text_file(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return False
    name = path.name
    if any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_FILE_GLOBS):
        return False
    return path.suffix in TEXT_EXTS or name in {"README", "LICENSE"}


def summarize_sessions(agent: str) -> None:
    src = SRC / "agents" / agent / "sessions" / "sessions.json"
    if not src.exists():
        return
    data = json.loads(src.read_text(encoding="utf-8"))
    summary = {}
    for key, item in data.items():
        if not isinstance(item, dict):
            continue
        summary[key] = {
            "sessionId": item.get("sessionId"),
            "updatedAt": item.get("updatedAt"),
            "displayName": item.get("displayName"),
            "chatType": item.get("chatType"),
            "channel": item.get("channel"),
            "groupId": item.get("groupId"),
            "modelProvider": item.get("modelProvider"),
            "model": item.get("model"),
            "fallbackNoticeSelectedModel": item.get("fallbackNoticeSelectedModel"),
            "fallbackNoticeActiveModel": item.get("fallbackNoticeActiveModel"),
        }
    write_json(OUT / "agents" / agent / "sessions-summary.json", scrub(summary))


def export_ops() -> None:
    copy_json(SRC / "cron" / "jobs.json", OUT / "ops" / "cron" / "jobs.json")
    copy_json(SRC / "discord" / "model-picker-preferences.json", OUT / "ops" / "discord" / "model-picker-preferences.json")
    copy_json(SRC / "update-check.json", OUT / "ops" / "update-check.json")

    # Device and identity summaries keep topology only; real restore needs the encrypted full backup.
    paired = SRC / "devices" / "paired.json"
    if paired.exists():
        raw = json.loads(paired.read_text(encoding="utf-8"))
        devices = []
        for item in raw.values():
            if not isinstance(item, dict):
                continue
            devices.append({
                "deviceId": "${REDACTED_DEVICE_ID}",
                "publicKey": "${REDACTED_PUBLIC_KEY}",
                "platform": item.get("platform"),
                "clientId": item.get("clientId"),
                "clientMode": item.get("clientMode"),
                "role": item.get("role"),
                "roles": item.get("roles"),
                "scopes": item.get("scopes"),
                "approvedScopes": item.get("approvedScopes"),
                "createdAtMs": item.get("createdAtMs"),
                "approvedAtMs": item.get("approvedAtMs"),
            })
        write_json(OUT / "ops" / "devices" / "paired-summary.json", devices)
    pending = SRC / "devices" / "pending.json"
    if pending.exists():
        write_json(OUT / "ops" / "devices" / "pending-summary.json", {"count": len(json.loads(pending.read_text(encoding="utf-8")))})

    device = SRC / "identity" / "device.json"
    if device.exists():
        raw = json.loads(device.read_text(encoding="utf-8"))
        write_json(OUT / "ops" / "identity" / "device-summary.json", {
            "version": raw.get("version"),
            "deviceId": "${REDACTED_DEVICE_ID}",
            "hasPublicKey": bool(raw.get("publicKeyPem")),
            "hasPrivateKey": bool(raw.get("privateKeyPem")),
            "createdAtMs": raw.get("createdAtMs"),
        })
    auth = SRC / "identity" / "device-auth.json"
    if auth.exists():
        raw = json.loads(auth.read_text(encoding="utf-8"))
        write_json(OUT / "ops" / "identity" / "device-auth-summary.json", {
            "version": raw.get("version"),
            "deviceId": "${REDACTED_DEVICE_ID}",
            "tokenRoles": sorted((raw.get("tokens") or {}).keys()),
        })

    for launch_agent in [
        Path("/Users/zhangfeng/Library/LaunchAgents/local.openclaw.config-backup.plist"),
        Path("/Users/zhangfeng/Library/LaunchAgents/local.openclaw.reaction-actions.plist"),
    ]:
        if launch_agent.exists():
            copy_text(launch_agent, OUT / "ops" / "launchd" / launch_agent.name)

    reaction_dir = SRC / "reaction-actions"
    if reaction_dir.exists():
        for src in [reaction_dir / "config.json", reaction_dir / "watcher.js"]:
            if src.exists():
                if src.suffix == ".json":
                    copy_json(src, OUT / "ops" / "reaction-actions" / src.name)
                else:
                    copy_text(src, OUT / "ops" / "reaction-actions" / src.name)

    comp = SRC / "completions"
    if comp.exists():
        for src in sorted(comp.iterdir()):
            if src.is_file() and should_copy_text_file(src):
                copy_text(src, OUT / "completions" / src.name)


def write_docs(manifest: dict[str, Any]) -> None:
    (OUT / ".gitignore").write_text("""# never commit real runtime state or secrets\n.env\n*.bak*\n*.tmp*\n*.log\nlogs/\nsessions/\ncredentials/\ndelivery-queue/\nmedia/\nmemory/\n**/MEMORY.md\n**/memory/\n**/node_modules/\n**/.git/\n""", encoding="utf-8")
    (OUT / "README.md").write_text("""# OpenClaw Config Backup\n\nRicher sanitized OpenClaw configuration snapshot. This repository is designed for version control and upgrade recovery reference. Secrets, API keys, tokens, private keys, raw session logs, credentials, delivery queues, binary browser state, and memory databases are excluded or redacted.\n\n## What Is Included\n\n- Global `openclaw.json` routing and provider structure with secrets redacted.\n- Per-agent `models.json` and `auth-profiles.json` structure.\n- Session index summaries, without raw conversation transcripts.\n- Workspace instruction files, docs, config, and text-based skill source files.\n- Cron jobs, Discord model picker preferences, device/identity summaries, update status, and shell completions.\n\n## What Is Not Included\n\n- Real API keys, tokens, private keys, credentials, logs, raw sessions, media, browser data, SQLite memory, and personal `USER.md` content.\n\n## Update\n\n```bash\ncd ~/openclaw-config-backup\npython3 scripts/export-sanitized.py\ngit diff\ngit add .\ngit commit -m "Update OpenClaw config backup"\ngit push\n```\n""", encoding="utf-8")
    (OUT / "RESTORE.md").write_text("""# Restore Notes\n\nThis repo is not a direct full restore archive because secrets are redacted. Use it to reconstruct routing, agents, workspace instructions, skills, and operational configuration after an OpenClaw upgrade.\n\nFor a direct disaster restore, keep a separate encrypted full backup of `~/.openclaw`.\n\n## Key Runtime Layout\n\n- `openclaw.json`: global routing, providers, defaults, bindings.\n- `agents/<agent>/agent/models.json`: models each agent can select.\n- `agents/<agent>/agent/auth-profiles.json`: auth profile shape; real keys must be reinserted locally.\n- `workspaces/<agent>` and `workspace`: agent instruction files, docs, config, and skills.\n- `ops`: cron, Discord picker preferences, device/identity summaries.\n\n## Current Model Intent\n\n- Global default: `google/gemini-2.5-flash`\n- `first-principles`: `cliproxyapi/gemini-3.1-flash-lite-preview`\n- `dev`: `cliproxyapi/gemini-3.1-flash-lite-preview`\n""", encoding="utf-8")
    write_json(OUT / "MANIFEST.json", manifest)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    clean_generated_paths()

    copy_json(SRC / "openclaw.json", OUT / "openclaw.json")
    agents = ["main", "first-principles", "dev"]
    for agent in agents:
        for name in ["models.json", "auth-profiles.json"]:
            copy_json(SRC / "agents" / agent / "agent" / name, OUT / "agents" / agent / "agent" / name)
        summarize_sessions(agent)

    workspaces = {
        "main": SRC / "workspace",
        "first-principles": SRC / "workspaces" / "first-principles",
        "dev": SRC / "workspaces" / "dev",
    }
    ws_summary = {agent: copy_workspace(agent, path) for agent, path in workspaces.items() if path.exists()}
    export_ops()

    manifest = {
        "source": str(SRC),
        "agents": agents,
        "workspaces": ws_summary,
        "excluded": [
            "credentials", "logs", "raw sessions", "memory sqlite", "browser data",
            "media", "delivery-queue", "real tokens and private keys",
        ],
    }
    write_docs(manifest)
    print(f"exported sanitized snapshot to {OUT}")


if __name__ == "__main__":
    main()
