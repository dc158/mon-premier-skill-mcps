---
name: community-manager-webdesign-co
description: Use this skill whenever the user wants to create social media content, plan an editorial calendar, generate posts, analyze trends, suggest hashtags, write captions, or monitor competitor activity for Webdesign & Co across France, Dubai, and USA markets (TikTok, LinkedIn, Instagram). Also use when the user mentions Make.com automation, competitor weaknesses, or social media publishing workflows for a web design agency.
---

# Community Manager — Webdesign & Co

MCP server that automates content creation and competitive intelligence for Webdesign & Co across three markets: France 🇫🇷, Dubai 🇦🇪, and USA 🇺🇸.

## Available MCP Tools

### `analyser_tendances(marche, nb_tendances)`
Returns the top viral trends with engagement scores for a given market.
- `marche`: `france` | `dubai` | `usa` (default: `france`)
- `nb_tendances`: 1–7 (default: 5)

### `generer_contenu(sujet, reseau, marche, ton)`
Generates a ready-to-publish post for a specific network and market.
- `reseau`: `tiktok` | `linkedin` | `instagram`
- `marche`: `france` | `dubai` | `usa`
- `ton`: `professionnel` | `educatif` | `inspirant` | `promotionnel` | `storytelling`

### `planifier_calendrier(marche, semaine_debut)`
Produces a full week editorial calendar with optimal posting times.
- `semaine_debut`: date in `JJ/MM/AAAA` format (defaults to next Monday)

### `suggerer_hashtags(sujet, reseau, marche, nb_hashtags)`
Returns a ranked list of hashtags tailored to the subject, network, and market.
- `nb_hashtags`: 5–20 (default: 15)

### `generer_legende(sujet, reseau, marche, objectif)`
Generates a copy-paste caption optimised for a specific goal.
- `objectif`: `engagement` | `vente` | `notoriete`

### `surveiller_concurrence(marche, inclure_tiktok, mot_cle_tiktok)`
Competitive intelligence report: static flaws + RSS signals + named competitor surveillance.
- `inclure_tiktok`: `true` to add TikTok viral posts (requires APIFY_TOKEN)

### `generer_post_concurrent(faille, marche, reseau)`
Generates a high-conversion attack post targeting a specific competitor flaw.
- `faille`: `formulaire_statique` | `relance_manuelle` | `audit_manuel` | `reporting_manuel`

## Typical Workflows

**Create content for today:**
1. Call `analyser_tendances` to pick a hot topic.
2. Call `generer_contenu` with that topic for each network.
3. Call `suggerer_hashtags` to complete the post.

**Weekly planning:**
1. Call `planifier_calendrier` to get the full schedule.
2. Use `generer_contenu` to produce each post.

**Competitive attack:**
1. Call `surveiller_concurrence` to identify active signals.
2. Call `generer_post_concurrent` for the target flaw and network.
3. The returned JSON is webhook-ready for Make.com (`webhook_ready: true`).

## Markets & Networks at a Glance

| Market  | Language  | Networks                      |
|---------|-----------|-------------------------------|
| france  | French    | TikTok, LinkedIn, Instagram   |
| dubai   | French    | TikTok, LinkedIn, Instagram   |
| usa     | English   | TikTok, LinkedIn, Instagram   |
