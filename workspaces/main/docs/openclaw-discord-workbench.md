# OpenClaw Discord Workbench

This workspace follows the Discord-first OpenClaw workflow:

- Telegram is the lightweight mobile/quick-chat entry.
- Discord is the project workbench for parallel sessions, project channels, threads, automation, and multi-agent routing.

## Session Boundaries

- `session.dmScope: "per-channel-peer"` is enabled. DM context is isolated by channel and peer by default.
- `session.identityLinks.owner` links the owner's known DM identities. Current configured owner link:
  - `discord:1181866569429692537`

Use identity links only for identities owned by the same person. This gives external isolation and internal continuity.

## Discord Structure

Recommended channel classes:

- `#daily`: inbox for brainstorms and short-lived topics. Enable `autoThread: true` so every new top-level message becomes a thread.
- `#ai-product`: product/strategy work. Routed to the `first-principles` agent.
- `#coding`: implementation work. Routed to the `dev` agent.
- Optional writing work can live in a normal project channel when needed; no dedicated writing agent is configured.
- `#digest`: scheduled reading and summary output.
- `#heartbeat`: cron/heartbeat and automation status.
- `#log`: low-noise operational logs.

Created and configured channels:

- `#daily` (`autoThread: true`)
- `#digest`
- `#heartbeat`

The bot now has Manage Channels permission, and these channels were created successfully.

## Current Routing

- `#ai-product` -> `first-principles`
  - Model: `cliproxyapi/claude-opus-4-6-thinking`
  - Role: product/strategy mentor
- `#coding` -> `dev`
  - Model: `cliproxyapi/claude-sonnet-4-6`
  - Role: engineer agent

Existing guild channels have `includeThreadStarter: true` where configured, so thread sessions can retain the starting message context.

## AutoThread

Use this config shape after `#daily` exists:

```json
{
  "channels": {
    "discord": {
      "guilds": {
        "<guildId>": {
          "channels": {
            "<dailyChannelId>": {
              "enabled": true,
              "allow": true,
              "requireMention": false,
              "includeThreadStarter": true,
              "autoThread": true
            }
          }
        }
      }
    }
  }
}
```

This keeps the parent channel as a topic index and moves substantive work into threads.

## Reaction Automation

The guild has `reactionNotifications: "all"` enabled so reactions are visible to OpenClaw. Recommended next automation:

- Heart reaction: save or forward the reacted message into `#digest` or a dedicated favorites channel.
- Check reaction: convert message into a task/todo.
- Eyes reaction: ask the relevant agent to inspect or summarize.

Implement reaction actions through OpenClaw's natural-language config/workflow path rather than hand-editing low-level runtime files.

## Operational Notes

- Backup created before the Discord workbench update:
  `/Users/zhangfeng/.openclaw/openclaw.json.bak.discord-workbench-20260514163120`
- The setup script used for this pass:
  `/tmp/openclaw_discord_workbench.py`
- Backup created before channel creation:
  `/Users/zhangfeng/.openclaw/openclaw.json.bak.discord-channels-20260514164707`
