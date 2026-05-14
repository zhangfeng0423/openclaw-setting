#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const WebSocket = require("ws");
const { HttpsProxyAgent } = require("https-proxy-agent");

const CONFIG_PATH = process.env.OPENCLAW_REACTION_CONFIG || "/Users/zhangfeng/.openclaw/reaction-actions/config.json";
const OPENCLAW_CONFIG = process.env.OPENCLAW_CONFIG || "/Users/zhangfeng/.openclaw/openclaw.json";
const LOG_FILE = "/Users/zhangfeng/.openclaw/reaction-actions/logs/watcher.log";
const NODE_NAME = "openclaw-reaction-actions";

function log(...args) {
  const line = `[${new Date().toISOString()}] ${args.map((x) => typeof x === "string" ? x : JSON.stringify(x)).join(" ")}\n`;
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
  fs.appendFileSync(LOG_FILE, line);
  process.stdout.write(line);
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function loadRuntime() {
  const cfg = readJson(CONFIG_PATH);
  const openclaw = readJson(OPENCLAW_CONFIG);
  const discord = openclaw.channels?.discord || {};
  if (!discord.token) throw new Error("Missing Discord token in openclaw.json");
  return { cfg, token: discord.token, proxy: discord.proxy || cfg.notion?.proxy || null };
}

function emojiKey(emoji) {
  if (!emoji) return "";
  if (emoji.id) return `${emoji.name}:${emoji.id}`;
  return emoji.name || "";
}

function discordApiBase() {
  return "https://discord.com/api/v10";
}

async function requestDiscord(method, route, body) {
  const { token, proxy } = loadRuntime();
  const url = `${discordApiBase()}${route}`;
  const opts = {
    method,
    headers: {
      Authorization: `Bot ${token}`,
      "Content-Type": "application/json",
      "User-Agent": `${NODE_NAME}/1.0`,
    },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const text = await res.text();
  if (!res.ok) throw new Error(`Discord ${method} ${route} ${res.status}: ${text.slice(0, 500)}`);
  return text ? JSON.parse(text) : null;
}

async function fetchMessage(channelId, messageId) {
  return requestDiscord("GET", `/channels/${channelId}/messages/${messageId}`);
}

async function fetchChannel(channelId) {
  return requestDiscord("GET", `/channels/${channelId}`);
}

async function sendMessage(channelId, content) {
  return requestDiscord("POST", `/channels/${channelId}/messages`, { content });
}

async function addOwnReaction(channelId, messageId, emoji) {
  const encoded = encodeURIComponent(emoji);
  return requestDiscord("PUT", `/channels/${channelId}/messages/${messageId}/reactions/${encoded}/@me`);
}

function messageUrl(guildId, channelId, messageId) {
  return `https://discord.com/channels/${guildId}/${channelId}/${messageId}`;
}

function appendTodo(kind, payload) {
  const file = payload.todoMarkdown;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const content = [
    `\n## ${new Date().toISOString()} ${kind}`,
    `- [ ] ${payload.content?.split(/\r?\n/)[0]?.slice(0, 160) || "Review OpenClaw reply"}`,
    `- URL: ${payload.url}`,
    `- Channel: ${payload.channelId}`,
    `- Message: ${payload.messageId}`,
    `- Author: ${payload.author}`,
    "",
    payload.content || "(no text content)",
    "",
  ].join("\n");
  fs.appendFileSync(file, content);
}

async function createNotionPage(cfg, payload) {
  const notionKeyPath = path.join(process.env.HOME || "/Users/zhangfeng", ".config/notion/api_key");
  const parentPageId = cfg.notion?.parentPageId;
  if (!cfg.notion?.enabled || !parentPageId || !fs.existsSync(notionKeyPath)) {
    return false;
  }
  const token = fs.readFileSync(notionKeyPath, "utf8").trim();
  const body = {
    parent: { page_id: parentPageId },
    properties: {
      title: [{ text: { content: `Discord archive ${new Date().toISOString().slice(0, 10)}` } }],
    },
    children: [
      { object: "block", type: "paragraph", paragraph: { rich_text: [{ text: { content: payload.url } }] } },
      { object: "block", type: "paragraph", paragraph: { rich_text: [{ text: { content: payload.content?.slice(0, 1900) || "(no text content)" } }] } },
    ],
  };
  const opts = {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Notion-Version": "2022-06-28",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  };
  if (cfg.notion?.proxy) opts.dispatcher = new (require("undici").ProxyAgent)(cfg.notion.proxy);
  const res = await fetch("https://api.notion.com/v1/pages", opts);
  const text = await res.text();
  if (!res.ok) throw new Error(`Notion create page failed ${res.status}: ${text.slice(0, 500)}`);
  return true;
}

function runBackup(script) {
  return new Promise((resolve) => {
    const child = spawn("/bin/zsh", [script], { stdio: ["ignore", "pipe", "pipe"] });
    child.stdout.on("data", (d) => log("backup stdout", d.toString().trim()));
    child.stderr.on("data", (d) => log("backup stderr", d.toString().trim()));
    child.on("close", (code) => resolve(code));
  });
}

async function allowedChannel(cfg, channelId) {
  if (cfg.allowedParentChannelIds.includes(channelId)) return true;
  try {
    const channel = await fetchChannel(channelId);
    return Boolean(channel?.parent_id && cfg.allowedParentChannelIds.includes(channel.parent_id));
  } catch (err) {
    log("channel lookup failed", channelId, String(err.message || err));
    return false;
  }
}

async function handleReaction(event, botUserId) {
  const { cfg } = loadRuntime();
  if (!cfg.ownerUserIds.includes(event.user_id)) return;
  if (!(await allowedChannel(cfg, event.channel_id))) return;

  const emoji = emojiKey(event.emoji);
  const action = cfg.emojiActions[emoji];
  if (!action) return;

  const msg = await fetchMessage(event.channel_id, event.message_id);
  if (msg?.author?.id !== botUserId) {
    log("ignored reaction on non-OpenClaw message", emoji, event.channel_id, event.message_id, msg?.author?.id);
    return;
  }

  const content = msg.content || "";
  const url = messageUrl(cfg.guildId, event.channel_id, event.message_id);
  const payload = {
    url,
    channelId: event.channel_id,
    messageId: event.message_id,
    author: `${msg.author?.username || "unknown"} (${msg.author?.id || "unknown"})`,
    content,
    todoMarkdown: cfg.todoMarkdown,
  };

  log("action", action, emoji, url);
  try {
    if (action === "backup") {
      const code = await runBackup(cfg.backupScript);
      await addOwnReaction(event.channel_id, event.message_id, code === 0 ? "☑️" : "⚠️");
    } else if (action === "archive") {
      const notionOk = await createNotionPage(cfg, payload);
      await addOwnReaction(event.channel_id, event.message_id, notionOk ? "📥" : "⚠️");
    } else if (action === "first_principles") {
      await sendMessage(cfg.firstPrinciplesChannelId, `请用第一性原理分析这条 OpenClaw 回复：\n${url}\n\n${content.slice(0, 1600)}`);
      await addOwnReaction(event.channel_id, event.message_id, "🧾");
    } else if (action === "pin_local") {
      appendTodo("todo", payload);
      await addOwnReaction(event.channel_id, event.message_id, "📍");
    }
  } catch (err) {
    log("action failed", action, String(err.stack || err.message || err));
    try { await addOwnReaction(event.channel_id, event.message_id, "⚠️"); } catch {}
  }
}

async function main() {
  const { token, proxy } = loadRuntime();
  const me = await requestDiscord("GET", "/users/@me");
  const botUserId = me.id;
  log("starting watcher", { botUserId });

  let ws;
  let heartbeatTimer;
  let seq = null;
  const agent = undefined;

  function connect() {
    ws = new WebSocket("wss://gateway.discord.gg/?v=10&encoding=json", agent ? { agent } : {});
    ws.on("open", () => log("gateway open"));
    ws.on("message", async (raw) => {
      const packet = JSON.parse(raw.toString());
      if (packet.s !== null && packet.s !== undefined) seq = packet.s;
      if (packet.op === 10) {
        const interval = packet.d.heartbeat_interval;
        clearInterval(heartbeatTimer);
        heartbeatTimer = setInterval(() => ws.send(JSON.stringify({ op: 1, d: seq })), interval);
        ws.send(JSON.stringify({
          op: 2,
          d: {
            token,
            intents: 1 | 1024,
            properties: { os: "darwin", browser: NODE_NAME, device: NODE_NAME },
          },
        }));
      } else if (packet.t === "READY") {
        log("gateway ready", packet.d?.user?.id);
      } else if (packet.t === "MESSAGE_REACTION_ADD") {
        handleReaction(packet.d, botUserId).catch((err) => log("reaction error", String(err.stack || err.message || err)));
      }
    });
    ws.on("close", (code, reason) => {
      log("gateway close", code, reason?.toString?.() || "");
      clearInterval(heartbeatTimer);
      setTimeout(connect, 5000);
    });
    ws.on("error", (err) => log("gateway error", String(err.message || err)));
  }

  connect();
}

main().catch((err) => {
  log("fatal", String(err.stack || err.message || err));
  process.exit(1);
});
