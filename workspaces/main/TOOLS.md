# TOOLS.md - Local Notes

## 已配置的 Skills

- **notion** - 读写 Notion 数据库
- **web-content-fetcher** - 极速网页提取与解析 (完美支持微信公众号等国内平台)
- **weather** - 天气查询

## 环境变量

- `NOTION_API_KEY` - ~/.config/notion/api_key
- `TAVILY_API_KEY` - ~/.openclaw/.env

## 快捷命令

- Chrome Browser Relay: `openclaw browser extension install`

## OpenClaw Session Routing

- `session.dmScope: "per-channel-peer"`: isolate DM context by channel and peer, so every user and every entry point has an independent session by default.
- `session.identityLinks`: explicitly link only the user's own DM entry points, such as Telegram + Discord, to get internal continuity without leaking context across external users/channels.

## Discord Workbench

- 工作台配置与后续步骤: `docs/openclaw-discord-workbench.md`

---

_你的个人知识库索引_
