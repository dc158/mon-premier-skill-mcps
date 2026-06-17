# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP server + webhook automation system for Webdesign & Co, a digital agency publishing social media content across three markets (France, Dubai, USA) on TikTok, LinkedIn, and Instagram. Built on FastMCP + FastAPI, deployed on Render.com, integrated with Make.com for actual social posting.

## Running the Server

```bash
pip install -r requirements.txt

# Mode 1 — MCP server (Claude-facing, stdio)
python server.py

# Mode 2 — Webhook server (Make.com-facing, HTTP)
python server.py --webhook

# Standalone TikTok scraper utility
python fetch_apify.py "<search_query>"
```

The webhook server starts on port `$PORT` (default 8000, Render uses 10000). All `/webhook/*` endpoints require the `X-Webhook-Secret` header.

## Architecture

`server.py` is the entire application in a single file (~520 lines). It runs in one of two modes via `sys.argv`:

**MCP mode** — exposes 10 tools to Claude via stdio (FastMCP). Claude calls these to generate content, analyse trends, suggest hashtags, etc.

**Webhook mode** — starts a FastAPI server with 13 HTTP endpoints. APScheduler runs background cron jobs that call `publier_automatiquement()`, which generates content and POSTs a JSON payload to Make.com, which handles actual social media publishing.

```
Claude → [MCP stdio] → FastMCP tools
Make.com scheduler → [HTTP POST] → FastAPI webhook endpoints → Make.com webhook (MAKE_WEBHOOK_URL)
APScheduler (background) → publier_automatiquement() → Make.com webhook
```

### Key internal flow

1. `publier_automatiquement(marche, reseau)` — picks a subject (RSS trend → rotation → fallback), generates content for all 3 networks, POSTs to Make.com, logs to Google Sheets + `/tmp/publications_log.json`
2. `rafraichir_veille()` runs daily at 06:00 UTC — scrapes Google News RSS to populate in-memory caches `TENDANCES_VEILLE` and `FAILLES_VEILLE`
3. Duplicate prevention: `sujet_deja_publie_recemment()` checks the last 14 days across a max 500-entry log

### Scheduling (France + Dubai only; USA not yet implemented)

- France: 7 cron jobs/day (TikTok ×4, LinkedIn ×3, Instagram ×4 — some overlap)
- Dubai: same 7 jobs, offset +10 min to prevent collision
- Self-ping every 14 min via `RENDER_URL` to prevent Render free-tier sleep

## External Integrations

| Service | Env var | Purpose |
|---|---|---|
| Make.com | `MAKE_WEBHOOK_URL` | Receives content payloads for actual posting |
| Google Sheets | `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_SHEET_ID` | Persistent publication log |
| Apify | `APIFY_TOKEN` | TikTok scraper (`clockworks/tiktok-scraper` actor) |
| Google News RSS | — | Trend + competitor surveillance (no auth needed) |
| Picsum Photos | — | Dynamic placeholder images (seeded by subject name) |
| Render.com | `RENDER_URL`, `PORT`, `WEBHOOK_SECRET` | Deployment platform |

`MAKE_WEBHOOK_URL` and `RENDER_URL` have hardcoded defaults in the source (lines 15–16) — override via env vars in production.

## Data Structures

**Subject rotation** — 28 subjects per market defined as module-level lists (`SUJETS_FRANCE`, `SUJETS_DUBAI`, `SUJETS_USA`). Tone rotates by weekday across 5 options.

**Competitive failles** — static list of 4 competitor weaknesses (`FAILLES_CONCURRENTS_V2`) each with `faille`, `stat_choc`, `solution_make`, `cta_keyword`, and `marches`.

**Market config** — `CONFIG_MARCHES` dict keyed by `"france"/"dubai"/"usa"` containing timezone, language, flag emoji, and optimal posting times per network.

**Hashtag pools** — `HASHTAGS_PAR_RESEAU_MARCHE` nested dict: market → network → list of hashtags.

## Deployment

Render.com (Frankfurt, free tier). Push to the repo triggers auto-deploy:
1. `pip install -r requirements.txt`
2. `python server.py --webhook` (starts on port 10000)
3. `/health` endpoint used for health checks

Logs persist in Google Sheets; `/tmp/publications_log.json` is ephemeral (reset on redeploy).

The `.github/workflows/main.yml` file is unrelated to this application — it tests SSH connectivity to a separate WordPress/PHP server.
