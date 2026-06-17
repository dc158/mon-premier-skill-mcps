# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A Python MCP (Model Context Protocol) server that acts as an automated community manager for "Webdesign & Co". It exposes 10 MCP tools to Claude and 11 FastAPI webhook endpoints consumed by Make.com. It handles social media content generation, publication scheduling, and competitive intelligence across three markets (France, Dubai, USA) and three platforms (TikTok, LinkedIn, Instagram).

## Running the Server

```bash
# MCP server mode — used when Claude connects to it as a tool server
python server.py

# Webhook + scheduler mode — used in Render.com deployment
python server.py --webhook
```

There are no build steps, no test suite, and no linter configured. Verify changes by running the server locally and hitting the `/health` endpoint.

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `WEBHOOK_SECRET` | Yes (webhook mode) | Validates `X-Webhook-Secret` header on all POST endpoints |
| `APIFY_TOKEN` | Optional | Enables TikTok scraping via Apify actors |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Optional | Google Sheets logging (falls back to `/tmp/publications_log.json`) |
| `GOOGLE_SHEET_ID` | Optional | Target sheet for publication log |
| `MAKE_WEBHOOK_URL` | Optional | Make.com webhook URL (has a hardcoded default) |
| `RENDER_URL` | Optional | Used by the self-ping keep-alive job |
| `PORT` | Optional | FastAPI port (default: 10000) |

## Architecture

All logic lives in two files:

- **`server.py`** (521 lines) — the entire application
- **`fetch_apify.py`** (46 lines) — standalone TikTok scraping utility used by `server.py`

### Dual execution modes

`server.py` uses `sys.argv` to switch between two modes:
- **MCP mode**: Creates a `FastMCP` server and exposes 10 `@mcp.tool()` functions. Claude calls these interactively.
- **Webhook mode**: Creates a FastAPI app, starts APScheduler, and exposes HTTP endpoints for Make.com to call.

The same content-generation logic (subject selection, hashtag lookup, post formatting) is shared by both modes.

### Market-driven data model

Everything is parameterized by `marche` (france / dubai / usa). The `MARCHES` dict centralizes per-market config: timezone, language, posting schedule, and hashtag pools per platform. The 28-topic rotation lists (`SUJETS_FRANCE_28`, `SUJETS_DUBAI_28`, `SUJETS_USA_28`) and competitor surveillance targets are defined as module-level constants.

### Subject selection with anti-duplication

`choisir_sujet(marche, reseau)` applies this priority order:
1. Current RSS trends (from `TENDANCES_VEILLE`) if not published in last 14 days
2. Deterministic day-of-year rotation through the 28-topic list
3. Forced fallback if all subjects were recently published

`sujet_deja_publie_recemment()` enforces the 14-day deduplication window against the publication log.

### Competitive intelligence layers

`surveiller_concurrence()` aggregates three layers:
1. **Sector trends** — Google News RSS queries on industry keywords
2. **Generic flaws** — RSS queries for competitor weakness signals (forms, CRM gaps, etc.)
3. **Named competitors** — RSS queries per named agency (Digidop, Eskimoz, Nexa, etc.)

The static `FAILLES_CONCURRENTS_BASE` list defines 4 known competitor weaknesses with `stat_choc` proof points and mapped Make.com responses. `generer_post_concurrent()` uses these to produce attack-style posts.

### Persistence

Publications are stored in two places simultaneously:
- **Google Sheets** (primary, if credentials provided) — appended on each publication
- **`/tmp/publications_log.json`** (fallback) — capped at 500 entries

`charger_log()` loads from Sheets at startup; `enregistrer_publication()` writes to both.

### APScheduler (webhook mode only)

`demarrer_scheduler()` registers CronTrigger jobs for France and Dubai (UTC offsets used; Dubai jobs are staggered +10 min to avoid collisions). Two background jobs:
- **Daily 06:00 UTC**: `rafraichir_veille()` — refreshes all three surveillance layers
- **Every 14 min**: `self_ping()` — prevents Render free tier from sleeping

### Make.com integration

`envoyer_vers_make(payload)` sends a JSON POST to `MAKE_WEBHOOK_URL`. The scheduler calls this automatically after each content generation. The `/webhook/envoyer-vers-make` endpoint also allows manual pushes.

## Deployment

Hosted on Render.com (free tier, Frankfurt). Defined in `render.yaml`. The `Procfile` mirrors the same start command for Heroku compatibility. The `/health` endpoint is the Render health check target.

## Key Conventions

- All user-facing text (post content, captions, hashtags) is in French for the France market, English for Dubai/USA. Keep language consistent when editing content templates.
- Tone names are fixed: `professionnel`, `educatif`, `inspirant`, `promotionnel`, `storytelling`. These are used as dict keys throughout.
- Platform names are fixed: `tiktok`, `linkedin`, `instagram`. Used as dict keys for hashtag pools and posting schedules.
- The `reseau` parameter always means social network/platform; `marche` always means geographic market.
- Image URLs are procedurally generated via Picsum Photos using a seed derived from the subject text — no image uploads involved.
