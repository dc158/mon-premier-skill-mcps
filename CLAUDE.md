# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Serveur **community manager automatisé** pour Webdesign & Co, ciblant deux marchés francophones : **France** et **Dubai**. Il fonctionne en deux modes :

- **Mode MCP** (`python server.py`) — expose des outils via le protocole MCP (FastMCP) pour être utilisé directement par Claude.
- **Mode Webhook** (`python server.py --webhook`) — lance une API FastAPI qui reçoit des appels de Make.com et publie automatiquement sur TikTok, LinkedIn et Instagram.

## Lancer le serveur

```bash
# Installer les dépendances
pip install -r requirements.txt

# Mode MCP (utilisé par Claude)
python server.py

# Mode webhook HTTP (utilisé en production sur Render)
python server.py --webhook
```

L'API est disponible sur `http://localhost:8000` et sa doc interactive sur `/docs`.

## Variables d'environnement

| Variable | Rôle | Obligatoire |
|---|---|---|
| `MAKE_WEBHOOK_URL` | URL du webhook Make.com | Non (valeur par défaut codée en dur) |
| `WEBHOOK_SECRET` | Header `x-webhook-secret` pour authentifier les appels entrants | Non (défaut : `webdesign-co-secret`) |
| `RENDER_URL` | URL publique Render pour le self-ping | Non |
| `PORT` | Port d'écoute (Render l'injecte automatiquement à `10000`) | Non (défaut : `8000`) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | JSON complet du service account Google | Non (sans : fallback `/tmp/`) |
| `GOOGLE_SHEET_ID` | ID de la Google Sheet pour la persistance des publications | Non |
| `APIFY_TOKEN` | Token Apify pour `fetch_apify.py` | Non |

## Architecture

### `server.py` — fichier unique, deux interfaces

Tout le code métier est dans `server.py`. Les deux interfaces partagent les mêmes fonctions.

**Couche données / mémoire**
- `charger_log()` / `enregistrer_publication()` — persistance à deux niveaux : Google Sheets (primaire) → `/tmp/publications_log.json` (fallback, éphémère sur Render).
- `sujet_deja_publie_recemment()` — anti-doublon sur 14 jours.

**Sélection du contenu**
- `choisir_sujet(marche)` — priorité : 1. veille RSS Google News → 2. rotation mensuelle de 28 sujets → 3. fallback forcé.
- `choisir_ton()` — rotation quotidienne parmi 5 tons (`TONS_ROTATION`).
- `scraper_tendances_rss()` + `filtrer_titres_rss()` — scrape Google News et filtre par mots-clés secteur.

**Génération de contenu**
- `generer_contenu(sujet, reseau, marche, ton)` — produit le texte formaté pour tiktok / linkedin / instagram.
- `generer_image_url(sujet, reseau)` — URL Picsum déterministe basée sur le sujet (pas d'appel réseau à la génération).
- `suggerer_hashtags()`, `generer_legende()`, `analyser_tendances()`, `planifier_calendrier()` — outils MCP exposés via `@mcp.tool()`.

**Automatisation**
- `publier_automatiquement(marche, reseau)` — orchestre sélection + génération + log + envoi Make.com.
- `demarrer_scheduler()` — APScheduler (background) avec des slots UTC précalculés pour France (UTC+2) et Dubai (UTC+4). Rafraîchit la veille RSS à 06h00 UTC. Self-ping `/health` toutes les 10 min pour éviter le spin-down de Render Free.

**Endpoints HTTP** (mode webhook, tous protégés par `x-webhook-secret`) :
- `GET /health` — santé du service
- `GET /scheduler/status` — liste des jobs APScheduler
- `GET /log/publications` — 50 dernières publications
- `GET /veille/tendances` — tendances RSS en cache
- `POST /scheduler/publier-maintenant` — déclenche une publication immédiate
- `POST /webhook/publier-tous-reseaux` — génère contenu pour les 3 réseaux
- `POST /webhook/envoyer-vers-make` — génère + envoie vers Make.com
- `POST /webhook/generer-contenu|legende|analyser-tendances|planifier-calendrier`

### `fetch_apify.py`

Script autonome (non importé par `server.py`). Scrape les top posts TikTok via l'acteur Apify `clockworks/tiktok-scraper`. Calcule un score d'engagement pondéré (likes + commentaires×2 + partages×3).

```bash
python fetch_apify.py "webdesign PME"
```

### Déploiement Render

Défini dans `render.yaml` : service web Python, région Frankfurt, plan gratuit. `startCommand` = `python server.py --webhook`. Le port est injecté via `PORT=10000`.

## Points d'attention

- **Persistance** : le plan Render Free réinitialise `/tmp/` à chaque redémarrage. Sans Google Sheets configuré, l'historique anti-doublon est perdu à chaque déploiement.
- **Marchés valides** : uniquement `"france"` et `"dubai"` (minuscules). Les fonctions retournent une erreur JSON pour toute autre valeur.
- **Réseaux valides** : `"tiktok"`, `"linkedin"`, `"instagram"` (minuscules).
- **Self-ping** : le scheduler pinge `/health` toutes les 10 min pour maintenir le service actif sur le plan gratuit Render.
