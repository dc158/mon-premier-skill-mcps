from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
import json
import os
import random
import sys
import urllib.request
import xml.etree.ElementTree as ET

# ─────────────────────────────────────────────
# IMAGE
# ─────────────────────────────────────────────

def generer_image_url(sujet: str, reseau: str = "instagram") -> str:
    seed = (
        sujet.lower()
        .replace("é", "e").replace("è", "e").replace("ê", "e")
        .replace("à", "a").replace("â", "a").replace("ô", "o")
        .replace("û", "u").replace("ç", "c").replace("'", "")
        .replace(" ", "-").replace("&", "and").replace("/", "-")
    )[:40]
    dimensions = {"instagram": "1080/1080", "tiktok": "1080/1920", "linkedin": "1200/628"}
    dim = dimensions.get(reseau, "1200/628")
    return f"https://picsum.photos/seed/{seed}/{dim}"


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

MAKE_WEBHOOK_URL = os.environ.get(
    "MAKE_WEBHOOK_URL",
    "https://hook.eu1.make.com/5uob38x8gtk2tsgdsqvslh3tdjg58yw5"
)
RENDER_URL = os.environ.get(
    "RENDER_URL",
    "https://mon-premier-skill-mcps.onrender.com"
)
LOG_FILE = "/tmp/publications_log.json"

# Google Sheets — variables d'environnement à configurer dans Render :
#   GOOGLE_SERVICE_ACCOUNT_JSON : contenu JSON complet du service account
#   GOOGLE_SHEET_ID             : ID de la Google Sheet (dans l'URL)
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
SHEETS_WORKSHEET = "Publications"


# ─────────────────────────────────────────────
# 1. ROTATION MENSUELLE — 28 sujets uniques par marché
# ─────────────────────────────────────────────

SUJETS_FRANCE_28 = [
    # Semaine 1 — Identité & branding
    "identité visuelle pour PME françaises",
    "création de logo professionnel",
    "charte graphique et cohérence de marque",
    "personal branding pour dirigeants français",
    "refonte de site web : avant / après",
    "pourquoi votre site web ne convertit pas",
    "site web mobile-first en 2025",
    # Semaine 2 — SEO & visibilité
    "SEO local pour commerces français",
    "Google My Business pour PME",
    "stratégie de contenu pour gagner en visibilité",
    "LinkedIn B2B pour PME françaises",
    "Instagram pour attirer des clients en France",
    "TikTok : levier de croissance pour les PME",
    "publicité digitale avec petit budget",
    # Semaine 3 — E-commerce & conversion
    "e-commerce pour boutiques françaises",
    "UX et expérience utilisateur qui convertit",
    "témoignages clients : la preuve sociale qui vend",
    "tunnel de vente pour PME",
    "automatisation marketing pour gagner du temps",
    "IA et outils digitaux pour PME en 2025",
    "email marketing : toujours rentable en 2025",
    # Semaine 4 — Expertise & storytelling
    "les erreurs fatales du webdesign en France",
    "comment doubler son CA grâce au digital",
    "success story : PME française transformée",
    "tendances design à adopter en 2025",
    "présence digitale : checklist complète pour PME",
    "investir dans son image : ROI du design pro",
    "bilan digital de l'année pour les PME françaises",
]

SUJETS_DUBAI_28 = [
    # Semaine 1 — Luxury & prestige
    "luxury branding et prestige digital à Dubai",
    "identité visuelle bilingue FR-EN pour Dubai",
    "création de logo pour entreprises du Golfe",
    "personal branding pour entrepreneurs francophones",
    "refonte de site web pour le marché émirati",
    "site web premium pour la clientèle Dubai",
    "charte graphique adaptée au marché du Moyen-Orient",
    # Semaine 2 — E-commerce & marché
    "e-commerce au Moyen-Orient : opportunités 2025",
    "Shopify vs solutions locales à Dubai",
    "stratégie digitale pour les expatriés francophones",
    "LinkedIn pour les professionnels de Dubai",
    "Instagram et TikTok pour les marques de Dubai",
    "marketing digital halal et inclusif",
    "SEO pour entreprises francophones à Dubai",
    # Semaine 3 — Tech & innovation
    "IA et startups tech à Dubai",
    "transformation digitale des PME émirati",
    "automatisation et croissance pour entreprises Dubai",
    "UX et design pour la clientèle premium du Golfe",
    "témoignages : entrepreneurs francophones à Dubai",
    "tunnel de vente pour le marché Dubai",
    "publicité digitale ciblée Moyen-Orient",
    # Semaine 4 — Expertise & storytelling
    "les erreurs à éviter pour réussir à Dubai",
    "comment développer sa marque au Golfe",
    "success story : entreprise francophone à Dubai",
    "tendances webdesign et digital à Dubai 2025",
    "présence digitale : guide complet pour Dubai",
    "ROI du design pro pour entreprises émirati",
    "bilan digital pour les francophones du Golfe",
]


# ─────────────────────────────────────────────
# 3. VARIATION DU TON — 5 tons en rotation
# ─────────────────────────────────────────────

TONS_ROTATION = ["professionnel", "educatif", "inspirant", "promotionnel", "storytelling"]

def choisir_ton() -> str:
    # Rotation quotidienne : chaque ton dure 1 jour sur 5
    return TONS_ROTATION[datetime.now().timetuple().tm_yday % len(TONS_ROTATION)]


# ─────────────────────────────────────────────
# 2. MÉMOIRE DES PUBLICATIONS — Google Sheets (persistant) + /tmp/ (fallback)
# ─────────────────────────────────────────────

_publications_log: list = []


def _get_sheets_worksheet():
    """Retourne le worksheet gspread, ou None si non configuré."""
    if not GOOGLE_SERVICE_ACCOUNT_JSON or not GOOGLE_SHEET_ID:
        return None
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        sa_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(GOOGLE_SHEET_ID)
        try:
            return sh.worksheet(SHEETS_WORKSHEET)
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title=SHEETS_WORKSHEET, rows=2000, cols=6)
            ws.append_row(["timestamp", "sujet", "marche", "reseau", "ton", "source"])
            return ws
    except Exception as e:
        print(f"[SHEETS] Connexion échouée : {e}")
        return None


def charger_log():
    """Charge l'historique : Google Sheets en priorité, /tmp/ en fallback."""
    global _publications_log
    ws = _get_sheets_worksheet()
    if ws:
        try:
            rows = ws.get_all_records()
            _publications_log = [
                {
                    "sujet": r.get("sujet", ""),
                    "marche": r.get("marche", ""),
                    "reseau": r.get("reseau", ""),
                    "ton": r.get("ton", ""),
                    "timestamp": r.get("timestamp", ""),
                }
                for r in rows if r.get("sujet")
            ]
            print(f"[LOG] {len(_publications_log)} entrées chargées depuis Google Sheets")
            return
        except Exception as e:
            print(f"[SHEETS] Lecture échouée, fallback /tmp/ : {e}")
    # Fallback /tmp/
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            _publications_log = json.load(f)
        print(f"[LOG] {len(_publications_log)} entrées chargées depuis /tmp/")
    except (FileNotFoundError, json.JSONDecodeError):
        _publications_log = []


def enregistrer_publication(sujet: str, marche: str, reseau: str, ton: str = "", source: str = ""):
    """Enregistre dans Google Sheets (persistant) + /tmp/ (cache local)."""
    entry = {
        "sujet": sujet,
        "marche": marche,
        "reseau": reseau,
        "ton": ton,
        "source": source,
        "timestamp": datetime.now().isoformat(),
    }
    _publications_log.append(entry)

    # Persistance Google Sheets
    ws = _get_sheets_worksheet()
    if ws:
        try:
            ws.append_row([
                entry["timestamp"], sujet, marche, reseau, ton, source
            ])
            print(f"[SHEETS] Enregistré : {sujet[:40]}")
        except Exception as e:
            print(f"[SHEETS] Écriture échouée : {e}")

    # Cache /tmp/ (toujours écrit, sert de fallback)
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(_publications_log[-500:], f, ensure_ascii=False)
    except Exception:
        pass


def sujet_deja_publie_recemment(sujet: str, marche: str, jours: int = 14) -> bool:
    seuil = datetime.now() - timedelta(days=jours)
    for entry in _publications_log:
        try:
            ts = datetime.fromisoformat(entry["timestamp"])
        except (KeyError, ValueError):
            continue
        if entry.get("sujet") == sujet and entry.get("marche") == marche and ts > seuil:
            return True
    return False


# ─────────────────────────────────────────────
# 4. VEILLE CONCURRENTIELLE — RSS Google News
# ─────────────────────────────────────────────

TENDANCES_VEILLE: dict = {"france": [], "dubai": [], "usa": []}
FAILLES_VEILLE: dict = {"france": [], "dubai": [], "usa": []}

RSS_QUERIES = {
    "france": "webdesign+agence+digitale+PME+identité+visuelle",
    "dubai": "web+design+digital+agency+Dubai+francophone",
    "usa": "web+design+agency+lead+generation+automation+AI",
}

# Requêtes ciblées sur les failles concurrentielles (formulaires statiques, relances manuelles, leads perdus)
RSS_QUERIES_CONCURRENTS = {
    "france": "agence+web+formulaire+contact+leads+perdus+relance+manuelle",
    "dubai": "digital+agency+Dubai+lead+response+time+contact+form+automation",
    "usa": "agency+static+contact+form+lost+leads+manual+follow+up+CRM",
}

# Concurrents ciblés par marché pour la surveillance
CONCURRENTS_CIBLES = {
    "france": ["Digidop", "Eskimoz", "Junto", "Plezi", "Nile"],
    "dubai": ["Nexa", "Blue Beetle", "Chain Reaction", "Digital Gravity"],
    "usa": ["NoGood", "Single Grain", "Ignite Visibility", "WebFX", "Thrive"],
}

# Mots-clés de pertinence secteur — un titre doit contenir au moins un de ces termes
MOTS_CLES_SECTEUR = [
    "webdesign", "web design", "agence web", "agence digitale",
    "site web", "création site", "refonte site",
    "identité visuelle", "logo", "charte graphique", "branding",
    "pme", "entrepreneur", "startup",
    "seo", "référencement", "google",
    "marketing digital", "réseaux sociaux", "community manager",
    "e-commerce", "boutique en ligne", "shopify",
    "ux", "expérience utilisateur", "conversion",
    "dubai", "émirats", "golfe", "moyen-orient",
    "digital", "numérique", "transformation digitale",
    # Lead generation & automation (veille concurrentielle)
    "lead", "formulaire", "contact form", "crm", "automation",
    "whatsapp", "sms", "relance", "follow-up", "pipeline",
    "make.com", "zapier", "n8n", "webhook", "workflow",
    "intelligence artificielle", "ia", "ai", "chatgpt",
    "taux de conversion", "leads perdus", "qualification",
    "réponse automatique", "bot", "séquence email",
]

# Failles concurrentielles statiques (enrichi au démarrage par la veille RSS)
FAILLES_CONCURRENTS_BASE = [
    {
        "faille": "formulaire_statique",
        "description": "Formulaire de contact statique sans automation CRM",
        "stat_choc": "73% des leads ne reçoivent pas de réponse dans les 5 premières minutes — passé ce délai, la conversion chute de 21x.",
        "solution_make": "Formulaire → Make.com → WhatsApp/SMS < 90 sec + relances J+1/J+3/J+7 automatiques",
        "cta_keyword": "BLUEPRINT",
        "marches": ["france", "dubai", "usa"],
    },
    {
        "faille": "relance_manuelle",
        "description": "Relances prospects 100% manuelles sans séquence automatisée",
        "stat_choc": "92% des agences relancent leurs prospects à la main. Résultat : 67% des leads chauds oubliés après 48h.",
        "solution_make": "CRM → Make.com → Séquence WhatsApp/Email/SMS multi-canal + scoring IA automatique",
        "cta_keyword": "WORKFLOW",
        "marches": ["france", "dubai", "usa"],
    },
    {
        "faille": "audit_manuel",
        "description": "Audit client réalisé manuellement, sans outil d'analyse automatisé",
        "stat_choc": "Les agences traditionnelles passent 4h en moyenne sur un audit client. Nous : 12 minutes grâce à l'IA.",
        "solution_make": "URL client → Make.com + Claude AI → Rapport d'audit complet + Loom personnalisé auto-envoyé",
        "cta_keyword": "AUDIT",
        "marches": ["france", "dubai", "usa"],
    },
    {
        "faille": "reporting_manuel",
        "description": "Reporting mensuel client préparé manuellement sous Excel/PDF",
        "stat_choc": "8h/mois de reporting manuel par client. Nos concurrents le font encore à la main en 2025.",
        "solution_make": "Google Analytics + Semrush → Make.com → Rapport PDF auto-généré + envoi client automatique",
        "cta_keyword": "REPORTING",
        "marches": ["france", "dubai", "usa"],
    },
]


def filtrer_titres_rss(titres: list) -> list:
    """
    Filtre les titres RSS bruts pour ne garder que ceux pertinents
    au secteur webdesign/PME. Nettoie aussi le format "Titre - Source".
    """
    result = []
    for titre in titres:
        titre_lower = titre.lower()
        if any(kw in titre_lower for kw in MOTS_CLES_SECTEUR):
            # Google News format : "Titre de l'article - Nom du média"
            sujet = titre.split(" - ")[0].strip()
            # Ignorer les titres trop courts ou trop longs
            if 15 <= len(sujet) <= 120:
                result.append(sujet)
    return result


def scraper_tendances_rss(marche: str = "france") -> list:
    """Scrappe Google News RSS et retourne uniquement les titres pertinents au secteur."""
    query = RSS_QUERIES.get(marche, RSS_QUERIES["france"])
    url = f"https://news.google.com/rss/search?q={query}&hl=fr&gl=FR&ceid=FR:fr"
    titres_bruts = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item")[:20]:
            titre_el = item.find("title")
            if titre_el is not None and titre_el.text:
                titres_bruts.append(titre_el.text.strip())
    except Exception as e:
        print(f"[VEILLE] RSS {marche} échoué : {e}")
        return []
    filtres = filtrer_titres_rss(titres_bruts)
    print(f"[VEILLE] {marche.upper()} — {len(titres_bruts)} bruts → {len(filtres)} pertinents")
    return filtres


def scraper_failles_concurrents_rss(marche: str = "france") -> list:
    """
    Scrape Google News RSS sur les failles concurrentielles (formulaires, leads, relances).
    Retourne une liste de titres pertinents enrichis du contexte concurrent.
    """
    query = RSS_QUERIES_CONCURRENTS.get(marche, RSS_QUERIES_CONCURRENTS["france"])
    lang = "fr" if marche in ["france", "dubai"] else "en"
    gl = "FR" if marche == "france" else ("AE" if marche == "dubai" else "US")
    url = f"https://news.google.com/rss/search?q={query}&hl={lang}&gl={gl}&ceid={gl}:{lang}"
    titres = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item")[:15]:
            titre_el = item.find("title")
            if titre_el is not None and titre_el.text:
                titre = titre_el.text.strip().split(" - ")[0].strip()
                if 15 <= len(titre) <= 140:
                    titres.append(titre)
    except Exception as e:
        print(f"[VEILLE CONCURRENTS] RSS {marche} échoué : {e}")
    print(f"[VEILLE CONCURRENTS] {marche.upper()} — {len(titres)} failles détectées")
    return titres


def scraper_tiktok_concurrent(query: str, max_results: int = 5) -> list:
    """
    Scrape TikTok via Apify pour surveiller les posts viraux de concurrents
    sur des mots-clés liés aux failles (formulaires, leads, automation).
    Nécessite APIFY_TOKEN en variable d'environnement.
    """
    apify_token = os.environ.get("APIFY_TOKEN")
    if not apify_token:
        print("[APIFY] APIFY_TOKEN manquant — scraping TikTok désactivé")
        return []
    try:
        from apify_client import ApifyClient
        client = ApifyClient(apify_token)
        run = client.actor("clockworks/tiktok-scraper").call(
            run_input={"searchQueries": [query], "resultsPerPage": max_results},
            timeout_secs=90,
        )
        posts = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            likes = item.get("diggCount", 0)
            comments = item.get("commentCount", 0)
            shares = item.get("shareCount", 0)
            posts.append({
                "auteur": item.get("author", {}).get("nickname", "Inconnu"),
                "texte": item.get("desc", "")[:200],
                "url": item.get("webVideoUrl", ""),
                "engagement": likes + (comments * 2) + (shares * 3),
                "metrics": {"likes": likes, "comments": comments, "shares": shares},
            })
        posts.sort(key=lambda x: x["engagement"], reverse=True)
        print(f"[APIFY] TikTok '{query}' — {len(posts)} posts récupérés")
        return posts
    except Exception as e:
        print(f"[APIFY] Erreur TikTok scraping : {e}")
        return []


def rafraichir_veille():
    """Appelé chaque matin à 06h00 UTC pour mettre à jour les tendances et la veille concurrentielle."""
    for marche in ["france", "dubai", "usa"]:
        titres = scraper_tendances_rss(marche)
        TENDANCES_VEILLE[marche] = titres
        failles = scraper_failles_concurrents_rss(marche)
        FAILLES_VEILLE[marche] = failles


# ─────────────────────────────────────────────
# 5. SÉLECTION INTELLIGENTE DU SUJET
# ─────────────────────────────────────────────

def choisir_sujet(marche: str) -> tuple:
    """
    Retourne (sujet, source) en suivant la priorité :
    1. Veille RSS (si non déjà publié)
    2. Rotation mensuelle 28 sujets (si non déjà publié)
    3. Rotation forcée (fallback)
    """
    sujets_map = {"france": SUJETS_FRANCE_28, "dubai": SUJETS_DUBAI_28, "usa": SUJETS_USA_28}
    sujets_28 = sujets_map.get(marche, SUJETS_FRANCE_28)

    # Priorité 1 : sujet issu de la veille RSS
    for titre in TENDANCES_VEILLE.get(marche, []):
        if not sujet_deja_publie_recemment(titre, marche):
            return titre, "veille_rss"

    # Priorité 2 : rotation mensuelle sans doublon
    jour = datetime.now().timetuple().tm_yday
    for i in range(len(sujets_28)):
        sujet = sujets_28[(jour + i) % len(sujets_28)]
        if not sujet_deja_publie_recemment(sujet, marche):
            return sujet, "rotation_mensuelle"

    # Priorité 3 : fallback rotation forcée
    return sujets_28[jour % len(sujets_28)], "rotation_forcee"


# ─────────────────────────────────────────────
# MAKE.COM
# ─────────────────────────────────────────────

def envoyer_vers_make(payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MAKE_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return {"status": "envoyé", "make_response": body, "http_code": resp.status}
    except Exception as e:
        return {"status": "erreur", "detail": str(e)}

def self_ping():
    try:
        req = urllib.request.Request(
            f"{RENDER_URL}/health",
            headers={"User-Agent": "self-ping/1.0"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[PING] Self-ping OK — HTTP {resp.status}")
    except Exception as e:
        print(f"[PING] Self-ping échoué : {e}")


# ─────────────────────────────────────────────
# MCP
# ─────────────────────────────────────────────

mcp = FastMCP("webdesign-co-community-manager")

MARCHES = {
    "france": {
        "timezone": "Europe/Paris",
        "langue": "français",
        "emoji_drapeau": "🇫🇷",
        "horaires": {
            "tiktok": ["07h00", "12h00", "19h00", "21h00"],
            "linkedin": ["08h00", "12h30", "17h30"],
            "instagram": ["08h00", "13h00", "18h00", "21h00"],
        },
    },
    "dubai": {
        "timezone": "Asia/Dubai",
        "langue": "français",
        "emoji_drapeau": "🇦🇪",
        "horaires": {
            "tiktok": ["08h00", "13h00", "20h00", "22h00"],
            "linkedin": ["09h00", "13h00", "18h00"],
            "instagram": ["09h00", "13h00", "19h00", "21h30"],
        },
    },
    "usa": {
        "timezone": "America/New_York",
        "langue": "anglais",
        "emoji_drapeau": "🇺🇸",
        "horaires": {
            "tiktok": ["08h00", "12h00", "19h00", "21h00"],
            "linkedin": ["08h00", "12h00", "17h00"],
            "instagram": ["08h00", "13h00", "18h00", "21h00"],
        },
    },
}

SUJETS_USA_28 = [
    # Week 1 — Identity & branding
    "visual identity for US startups",
    "professional logo design for American businesses",
    "brand guidelines and consistency",
    "personal branding for US founders",
    "website redesign: before & after",
    "why your website isn't converting",
    "mobile-first web design in 2025",
    # Week 2 — SEO & visibility
    "local SEO for US small businesses",
    "Google Business Profile optimization",
    "content strategy for US market visibility",
    "LinkedIn B2B for US companies",
    "Instagram for US business growth",
    "TikTok: growth lever for small businesses",
    "digital ads on a small budget",
    # Week 3 — Lead gen & automation
    "e-commerce for US boutiques",
    "UX design that converts",
    "social proof and customer testimonials",
    "sales funnel for small businesses",
    "AI marketing automation to save time",
    "AI tools for US small businesses in 2025",
    "email marketing: still profitable in 2025",
    # Week 4 — Expertise & storytelling
    "fatal web design mistakes in the US",
    "how to double revenue through digital",
    "success story: US business transformed",
    "design trends to adopt in 2025",
    "digital presence: complete checklist for US SMBs",
    "investing in professional design: ROI breakdown",
]

TENDANCES_BASE = {
    "france": [
        {"sujet": "IA & automatisation pour PME", "score": 97, "hashtag_cle": "#PMEFrance"},
        {"sujet": "Identité visuelle minimaliste", "score": 94, "hashtag_cle": "#WebDesign"},
        {"sujet": "Site web mobile-first en 2025", "score": 91, "hashtag_cle": "#MobileFrance"},
        {"sujet": "Personal branding pour dirigeants", "score": 89, "hashtag_cle": "#PersonalBranding"},
        {"sujet": "SEO local pour commerces français", "score": 86, "hashtag_cle": "#SEOLocal"},
        {"sujet": "UX / expérience utilisateur & conversions", "score": 85, "hashtag_cle": "#UXDesign"},
        {"sujet": "Réseaux sociaux B2B en France", "score": 82, "hashtag_cle": "#MarketingFrance"},
    ],
    "usa": [
        {"sujet": "AI automation for US small businesses", "score": 98, "hashtag_cle": "#AIAutomation"},
        {"sujet": "Lead generation with Make.com workflows", "score": 95, "hashtag_cle": "#LeadGen"},
        {"sujet": "Luxury branding for US market", "score": 92, "hashtag_cle": "#USBranding"},
        {"sujet": "Personal branding for US founders", "score": 89, "hashtag_cle": "#PersonalBranding"},
        {"sujet": "Mobile-first web design 2025", "score": 86, "hashtag_cle": "#WebDesignUSA"},
        {"sujet": "WhatsApp & SMS lead automation", "score": 84, "hashtag_cle": "#SalesAutomation"},
        {"sujet": "B2B LinkedIn strategy for US agencies", "score": 81, "hashtag_cle": "#LinkedInUSA"},
    ],
    "dubai": [
        {"sujet": "Luxury branding & prestige digital", "score": 98, "hashtag_cle": "#DubaiLuxury"},
        {"sujet": "E-commerce & boutiques en ligne au Moyen-Orient", "score": 95, "hashtag_cle": "#EcommerceDubai"},
        {"sujet": "IA & startups tech à Dubai", "score": 93, "hashtag_cle": "#DubaiTech"},
        {"sujet": "Personal branding pour entrepreneurs francophones", "score": 90, "hashtag_cle": "#FrancophonesDubai"},
        {"sujet": "Identité visuelle bilingue FR/EN", "score": 87, "hashtag_cle": "#DesignDubai"},
        {"sujet": "Marketing digital halal & inclusif", "score": 84, "hashtag_cle": "#HalalMarketing"},
        {"sujet": "Réseaux sociaux pour les expatriés francophones", "score": 81, "hashtag_cle": "#ExpatsFrancophones"},
    ],
}

HASHTAGS_BASE = {
    "tiktok": {
        "france": ["#WebDesignFrance", "#PMEFrance", "#ConseilMarketing", "#TipsDigital",
                   "#EntrepreneurFrancais", "#DesignFR", "#AgenceWeb", "#MarketingDigital",
                   "#CommunityManager", "#TiktokBusiness"],
        "dubai": ["#WebDesignDubai", "#FrancophonesDubai", "#EntrepreneurDubai", "#DigitalDubai",
                  "#PMEDubai", "#DesignDubai", "#AgenceWebDubai", "#DubaiMarketing",
                  "#FrancaisDubai", "#DubaiTech"],
    },
    "linkedin": {
        "france": ["#WebDesign", "#MarketingDigital", "#PME", "#TransformationDigitale",
                   "#Entrepreneuriat", "#BrandingFrance", "#CommunicationDigitale",
                   "#AgenceWeb", "#SEO", "#UXDesign"],
        "dubai": ["#DubaiBusiness", "#WebDesignDubai", "#MarketingDubai", "#EntrepreneurDubai",
                  "#FrancophonesDubai", "#LuxuryBranding", "#StartupDubai",
                  "#DigitalMarketing", "#UAEBusiness", "#BrandingDubai"],
    },
    "instagram": {
        "france": ["#WebDesignFrance", "#AgenceWebParis", "#DesignGraphique", "#PMEFrance",
                   "#MarketingDigital", "#BrandingFR", "#CommunityManager", "#ContentCreator",
                   "#EntrepreneurFrancais", "#Graphisme", "#IdentiteVisuelle", "#LogoDesign"],
        "dubai": ["#DubaiDesign", "#WebDesignDubai", "#DubaiMarketing", "#FrancaisDubai",
                  "#LuxuryDesign", "#DesignDubai", "#DubaiEntrepreneur", "#UAEDesign",
                  "#FrancophonesDubai", "#DubaiAgency", "#BrandingDubai", "#DubaiLuxury"],
        "usa": ["#WebDesignUSA", "#DigitalAgency", "#LeadGeneration", "#AIAutomation",
                "#SmallBusiness", "#StartupUSA", "#MarketingAutomation", "#SalesAutomation",
                "#MakeComWorkflow", "#GrowthHacking", "#B2BMarketing", "#AgencyLife"],
    },
}

HASHTAGS_BASE["tiktok"]["usa"] = [
    "#WebDesignUSA", "#AIAutomation", "#LeadGenTips", "#MakeComWorkflow",
    "#DigitalAgencyUSA", "#SmallBusinessTips", "#SalesAutomation", "#GrowthHacks",
    "#MarketingUSA", "#AgencyLife",
]
HASHTAGS_BASE["linkedin"]["usa"] = [
    "#AIAutomation", "#LeadGeneration", "#WebDesignUSA", "#B2BMarketing",
    "#SalesAutomation", "#MakeComWorkflow", "#DigitalTransformation",
    "#GrowthMarketing", "#AgencyLife", "#StartupUSA",
]

JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


@mcp.tool()
def analyser_tendances(marche: str = "france", nb_tendances: int = 5) -> str:
    """
    Détecte les tendances virales actuelles pour Webdesign & Co sur un marché donné.
    Marché : 'france' ou 'dubai'. nb_tendances : nombre de tendances à retourner (1-7).
    """
    marche = marche.lower()
    if marche not in MARCHES:
        return json.dumps({"erreur": "Marché inconnu. Utilisez 'france' ou 'dubai'."}, ensure_ascii=False)

    nb = max(1, min(nb_tendances, 7))
    tendances = TENDANCES_BASE[marche][:nb]
    drapeau = MARCHES[marche]["emoji_drapeau"]

    lignes = [f"📊 TENDANCES VIRALES — Webdesign & Co {drapeau} {marche.upper()}\n"]
    for i, t in enumerate(tendances, 1):
        barre = "█" * (t["score"] // 10) + "░" * (10 - t["score"] // 10)
        lignes.append(
            f"#{i} {t['sujet']}\n"
            f"   Score viral : {barre} {t['score']}/100\n"
            f"   Hashtag clé : {t['hashtag_cle']}\n"
        )

    lignes.append("💡 Conseil : Surfez sur la tendance #1 cette semaine pour maximiser votre portée.")
    return "\n".join(lignes)


@mcp.tool()
def surveiller_concurrence(
    marche: str = "france",
    inclure_tiktok: bool = False,
    mot_cle_tiktok: str = "",
) -> str:
    """
    Surveille les failles concurrentielles sur un marché donné (France/Dubai/USA).
    Agrège : failles statiques connues + veille RSS en temps réel + TikTok viral (si APIFY_TOKEN configuré).
    marche : 'france', 'dubai' ou 'usa'.
    inclure_tiktok : active le scraping TikTok via Apify (nécessite APIFY_TOKEN).
    mot_cle_tiktok : mot-clé personnalisé pour TikTok (défaut auto selon marché).
    """
    marche = marche.lower()
    if marche not in MARCHES:
        return json.dumps({"erreur": "Marché inconnu. Utilisez 'france', 'dubai' ou 'usa'."}, ensure_ascii=False)

    drapeau = MARCHES[marche]["emoji_drapeau"]
    concurrents = CONCURRENTS_CIBLES.get(marche, [])

    lignes = [
        f"🔍 SURVEILLANCE CONCURRENTIELLE — {drapeau} {marche.upper()}",
        f"Concurrents ciblés : {', '.join(concurrents)}",
        "=" * 60,
        "",
        "⚠️  FAILLES DÉTECTÉES (base statique) :",
    ]

    failles_marche = [f for f in FAILLES_CONCURRENTS_BASE if marche in f["marches"]]
    for i, f in enumerate(failles_marche, 1):
        lignes += [
            f"  #{i} [{f['faille'].upper()}]",
            f"     Faille    : {f['description']}",
            f"     Stat choc : {f['stat_choc']}",
            f"     Notre fix : {f['solution_make']}",
            f"     CTA       : Commentez « {f['cta_keyword']} »",
            "",
        ]

    # Veille RSS temps réel
    failles_rss = FAILLES_VEILLE.get(marche, [])
    if failles_rss:
        lignes += [
            "📡 SIGNAUX RSS TEMPS RÉEL (failles concurrentielles) :",
            *[f"  • {t}" for t in failles_rss[:5]],
            "",
        ]
    else:
        lignes.append("📡 Veille RSS : aucun signal frais (lancer rafraichir_veille ou attendre 06h00 UTC)\n")

    # TikTok viral via Apify
    if inclure_tiktok:
        query = mot_cle_tiktok or (
            "agence web formulaire automatisation" if marche == "france"
            else ("digital agency lead automation" if marche == "usa"
                  else "digital agency Dubai automation")
        )
        posts = scraper_tiktok_concurrent(query, max_results=3)
        if posts:
            lignes += [f"🎬 TIKTOK VIRAL — top posts '{query}' :"]
            for p in posts:
                lignes.append(
                    f"  @{p['auteur']} | {p['metrics']['likes']}❤️ {p['metrics']['comments']}💬 "
                    f"| {p['texte'][:80]}…"
                )
            lignes.append("")
        else:
            lignes.append("🎬 TikTok : APIFY_TOKEN manquant ou aucun résultat.\n")

    lignes += [
        "=" * 60,
        "💡 Action recommandée : utilisez generer_post_concurrent() pour transformer",
        "   une faille en post LinkedIn haute-conversion prêt pour votre webhook Make.",
    ]
    return "\n".join(lignes)


@mcp.tool()
def generer_post_concurrent(
    faille: str,
    marche: str = "france",
    reseau: str = "linkedin",
) -> str:
    """
    Génère un post haute-conversion qui attaque une faille concurrentielle.
    Respecte le tone of voice de Webdesign & Co : hook froid (stat choc), fix Make.com précis, CTA « Comment ».
    faille : 'formulaire_statique' | 'relance_manuelle' | 'audit_manuel' | 'reporting_manuel' | texte libre.
    marche : 'france', 'dubai' ou 'usa'.
    reseau : 'linkedin' (défaut), 'instagram', 'tiktok'.
    Retourne un JSON structuré prêt à être envoyé au webhook Make.com.
    """
    marche = marche.lower()
    reseau = reseau.lower()
    if marche not in MARCHES:
        return json.dumps({"erreur": "Marché inconnu."}, ensure_ascii=False)

    drapeau = MARCHES[marche]["emoji_drapeau"]

    # Cherche la faille dans la base statique
    faille_data = next(
        (f for f in FAILLES_CONCURRENTS_BASE if f["faille"] == faille and marche in f["marches"]),
        None,
    )

    # Templates de posts par faille et réseau
    POSTS_TEMPLATES = {
        "formulaire_statique": {
            "linkedin": (
                "{stat_choc}\n\n"
                "La plupart des agences à {marche_label} ont un formulaire de contact.\n"
                "Aucune n'a construit le moteur d'automation derrière.\n\n"
                "Voici exactement ce que nous avons déployé :\n\n"
                "→ Soumission formulaire\n"
                "→ Make.com capte le lead en temps réel\n"
                "→ WhatsApp + SMS envoyé au prospect en < 90 secondes\n"
                "→ Si pas de réponse : relance automatique J+1 / J+3 / J+7\n"
                "→ Lead scoré par IA et routé vers le bon commercial\n\n"
                "Résultat sur 90 jours : +340% de leads contactés dans la fenêtre critique.\n\n"
                "Commentez « {cta_keyword} » et notre automation vous envoie le blueprint complet en DM.\n\n"
                "#AIAutomation #LeadGeneration #WebdesignAndCo"
            ),
            "instagram": (
                "{stat_choc}\n\n"
                "Votre formulaire de contact vous coûte des clients. Voici le fix :\n\n"
                "✅ Make.com capte chaque lead\n"
                "✅ WhatsApp/SMS < 90 secondes\n"
                "✅ Relances automatiques multi-canal\n"
                "✅ Zéro intervention manuelle\n\n"
                "👇 Commentez « {cta_keyword} » pour recevoir le blueprint gratuit\n\n"
                "#AIAutomation #LeadGeneration #WebdesignAndCo"
            ),
            "tiktok": (
                "🎬 SCRIPT TIKTOK\n"
                "ACCROCHE (0-3s) : « {stat_choc} »\n\n"
                "DÉVELOPPEMENT (3-35s) :\n"
                "Votre formulaire de contact vous fait perdre des clients. "
                "Nous avons automatisé la réponse en 90 secondes avec Make.com. "
                "WhatsApp instantané. Relances automatiques. Zéro travail manuel.\n\n"
                "CTA (35-45s) : « Commentez {cta_keyword} pour le blueprint ! »\n\n"
                "#AIAutomation #LeadGeneration #WebdesignAndCo"
            ),
        },
        "relance_manuelle": {
            "linkedin": (
                "{stat_choc}\n\n"
                "En 2025, relancer ses prospects à la main, c'est du travail de stagiaire.\n"
                "Voici la séquence que nous avons automatisée pour nos clients :\n\n"
                "→ Lead entrant → CRM mis à jour automatiquement\n"
                "→ Email de bienvenue personnalisé : J+0 (immédiat)\n"
                "→ WhatsApp de suivi : J+1\n"
                "→ SMS de relance douce : J+3\n"
                "→ Email de dernière chance : J+7\n"
                "→ IA analyse le taux d'ouverture et adapte le prochain message\n\n"
                "Résultat : 67% de leads récupérés qui auraient été abandonnés.\n\n"
                "Commentez « {cta_keyword} » et notre automation vous envoie le schéma Make.com complet.\n\n"
                "#SalesAutomation #MakeComWorkflow #WebdesignAndCo"
            ),
            "instagram": (
                "{stat_choc}\n\n"
                "Notre séquence de relance automatisée :\n\n"
                "✅ J+0 : Email personnalisé (IA)\n"
                "✅ J+1 : WhatsApp\n"
                "✅ J+3 : SMS\n"
                "✅ J+7 : Dernier email\n"
                "✅ 0 action manuelle requise\n\n"
                "👇 Commentez « {cta_keyword} » pour le workflow Make.com\n\n"
                "#SalesAutomation #MakeComWorkflow #WebdesignAndCo"
            ),
            "tiktok": (
                "🎬 SCRIPT TIKTOK\n"
                "ACCROCHE : « {stat_choc} »\n\n"
                "DÉVELOPPEMENT : Voici notre séquence de relance automatisée — "
                "email J+0, WhatsApp J+1, SMS J+3, relance IA J+7. Zéro action manuelle.\n\n"
                "CTA : « Commentez {cta_keyword} ! »\n\n"
                "#SalesAutomation #MakeComWorkflow #WebdesignAndCo"
            ),
        },
        "audit_manuel": {
            "linkedin": (
                "{stat_choc}\n\n"
                "Chaque heure passée à préparer un audit manuellement est une heure "
                "non facturée et un prospect qui attend.\n\n"
                "Notre process automatisé :\n\n"
                "→ URL du prospect soumise\n"
                "→ Make.com déclenche l'analyse (Semrush + PageSpeed + Screaming Frog)\n"
                "→ Claude AI compile le rapport en langage client\n"
                "→ Loom personnalisé généré automatiquement\n"
                "→ Email + WhatsApp envoyés au prospect avec le rapport\n\n"
                "Délai : 12 minutes. Résultat : taux de closing de nos audits = 68%.\n\n"
                "Commentez « {cta_keyword} » pour recevoir le blueprint de notre machine à audits.\n\n"
                "#AIAutomation #SalesProcess #WebdesignAndCo"
            ),
            "instagram": (
                "{stat_choc}\n\n"
                "Notre audit automatisé en 12 min :\n\n"
                "✅ Analyse SEO + Performance auto\n"
                "✅ Rapport IA rédigé pour le client\n"
                "✅ Loom personnalisé généré\n"
                "✅ Envoi WhatsApp automatique\n\n"
                "👇 Commentez « {cta_keyword} » pour le blueprint\n\n"
                "#AIAutomation #SalesProcess #WebdesignAndCo"
            ),
            "tiktok": (
                "🎬 SCRIPT TIKTOK\n"
                "ACCROCHE : « {stat_choc} »\n\n"
                "DÉVELOPPEMENT : Notre audit client prend 12 minutes grâce à Make.com + IA. "
                "Analyse automatique, rapport rédigé, Loom envoyé. L'agence d'en face en fait 4h.\n\n"
                "CTA : « Commentez {cta_keyword} ! »\n\n"
                "#AIAutomation #AgencyLife #WebdesignAndCo"
            ),
        },
        "reporting_manuel": {
            "linkedin": (
                "{stat_choc}\n\n"
                "Pendant que vos concurrents passent leurs week-ends sur Excel,\n"
                "voici notre pipeline de reporting automatisé :\n\n"
                "→ Google Analytics 4 + Search Console → Make.com\n"
                "→ Semrush API → agrégation des KPIs\n"
                "→ Claude AI → rédaction du commentaire exécutif\n"
                "→ PDF généré et branded automatiquement\n"
                "→ Email + WhatsApp client le 1er du mois à 09h00\n\n"
                "Temps passé : 0 minute. Satisfaction client : +41% vs reporting manuel.\n\n"
                "Commentez « {cta_keyword} » pour le workflow Make.com complet.\n\n"
                "#AgencyAutomation #ClientReporting #WebdesignAndCo"
            ),
            "instagram": (
                "{stat_choc}\n\n"
                "Notre reporting 100% automatisé :\n\n"
                "✅ GA4 + Semrush → Make.com\n"
                "✅ Rapport IA rédigé\n"
                "✅ PDF branded auto-généré\n"
                "✅ Envoi client automatique\n"
                "✅ 0 minute de travail manuel\n\n"
                "👇 Commentez « {cta_keyword} » pour le workflow\n\n"
                "#AgencyAutomation #ClientReporting #WebdesignAndCo"
            ),
            "tiktok": (
                "🎬 SCRIPT TIKTOK\n"
                "ACCROCHE : « {stat_choc} »\n\n"
                "DÉVELOPPEMENT : Notre rapport client se génère seul chaque mois — "
                "GA4, Semrush, IA, PDF, WhatsApp. Zéro Excel, zéro dimanche au bureau.\n\n"
                "CTA : « Commentez {cta_keyword} ! »\n\n"
                "#AgencyAutomation #AgencyLife #WebdesignAndCo"
            ),
        },
    }

    # Stat choc et CTA par défaut si faille libre (non dans la base)
    if faille_data:
        stat_choc = faille_data["stat_choc"]
        cta_keyword = faille_data["cta_keyword"]
        solution_make = faille_data["solution_make"]
    else:
        stat_choc = f"Les agences traditionnelles à {marche.capitalize()} perdent des leads qualifiés chaque jour faute d'automation."
        cta_keyword = "BLUEPRINT"
        solution_make = f"Make.com + IA → automatisation complète du pipeline pour les agences à {marche.capitalize()}"

    marche_label = {"france": "France", "dubai": "Dubai", "usa": "USA"}.get(marche, marche.capitalize())

    # Sélection du template
    template_pool = POSTS_TEMPLATES.get(faille, POSTS_TEMPLATES["formulaire_statique"])
    template = template_pool.get(reseau, template_pool["linkedin"])

    texte_post = template.format(
        stat_choc=stat_choc,
        marche_label=marche_label,
        cta_keyword=cta_keyword,
        solution_make=solution_make,
        drapeau=drapeau,
    )

    # Hashtags réseau (max 3 pour LinkedIn, conformément aux guidelines)
    hashtags_pool = HASHTAGS_BASE.get(reseau, HASHTAGS_BASE["linkedin"]).get(marche, [])
    nb_hashtags = 3 if reseau == "linkedin" else (5 if reseau == "tiktok" else 8)
    hashtags = " ".join(hashtags_pool[:nb_hashtags])

    payload = {
        "type": "post_concurrent",
        "faille": faille,
        "marche": marche,
        "reseau": reseau,
        "drapeau": drapeau,
        "cta_keyword": cta_keyword,
        "solution_make": solution_make,
        "texte_post": texte_post,
        "hashtags": hashtags,
        "image_url": generer_image_url(faille.replace("_", " "), reseau),
        "timestamp": datetime.now().isoformat(),
        "webhook_ready": True,
    }

    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
def generer_contenu(
    sujet: str,
    reseau: str,
    marche: str = "france",
    ton: str = "professionnel"
) -> str:
    """
    Crée un post complet prêt à publier pour Webdesign & Co.
    reseau : 'tiktok', 'linkedin' ou 'instagram'.
    marche : 'france' ou 'dubai'.
    ton : 'professionnel', 'educatif', 'inspirant', 'promotionnel', 'storytelling'.
    """
    reseau = reseau.lower()
    marche = marche.lower()

    if reseau not in ["tiktok", "linkedin", "instagram"]:
        return json.dumps({"erreur": "Réseau inconnu. Utilisez 'tiktok', 'linkedin' ou 'instagram'."}, ensure_ascii=False)
    if marche not in MARCHES:
        return json.dumps({"erreur": "Marché inconnu. Utilisez 'france' ou 'dubai'."}, ensure_ascii=False)

    drapeau = MARCHES[marche]["emoji_drapeau"]

    hooks = {
        "professionnel": [
            f"Votre entreprise mérite le meilleur design. Voici pourquoi ▼",
            f"Ce que personne ne vous dit sur {sujet} en {marche.capitalize()}.",
            f"3 erreurs fatales à éviter sur {sujet} pour les PME {drapeau}",
        ],
        "educatif": [
            f"📚 Saviez-vous que {sujet} peut transformer votre business ? Voici comment ▼",
            f"Leçon du jour : tout ce que vous devez savoir sur {sujet} en {marche.capitalize()}.",
            f"Guide complet : {sujet} pour les PME {drapeau} — 3 points essentiels",
        ],
        "inspirant": [
            f"Et si {sujet} était la clé de votre croissance en {marche.capitalize()} ? ✨",
            f"Nous avons transformé des PME grâce à {sujet}. Voici leur histoire 👇",
            f"La réussite digitale commence par {sujet}. On vous explique tout. {drapeau}",
        ],
        "promotionnel": [
            f"🎯 Offre exclusive Webdesign & Co sur {sujet}. Places limitées !",
            f"💥 Ce mois-ci : audit GRATUIT de votre {sujet} pour les PME {drapeau}",
            f"Transformez votre image avec {sujet} — Diagnostic offert cette semaine !",
        ],
        "storytelling": [
            f"Il y a 6 mois, cette PME {drapeau} galérait avec {sujet}. Aujourd'hui, elle cartonne. 👇",
            f"On a tout misé sur {sujet} pour un client en {marche.capitalize()}. Voici ce qui s'est passé…",
            f"De 0 à 10K abonnés grâce à {sujet} — l'histoire vraie d'une PME {drapeau}",
        ],
        "humoristique": [
            f"On ne va pas se mentir… {sujet}, c'est souvent le chaos 😅",
            f"Avant Webdesign & Co : galère. Après : chef d'œuvre 🎨 #{sujet.replace(' ', '')}",
            f"Si {sujet} était un plat, ce serait… un plat raté sans nous 🍽️😂",
        ],
    }

    hook = random.choice(hooks.get(ton, hooks["professionnel"]))
    hashtags = " ".join(HASHTAGS_BASE[reseau][marche][:5])

    corps_ton = {
        "educatif": (
            f"📖 POURQUOI C'EST IMPORTANT :\n"
            f"{sujet} est l'un des leviers les plus puissants pour les PME {drapeau} en 2025.\n\n"
            f"🔍 CE QUE VOUS DEVEZ SAVOIR :\n"
            f"✅ 78% des PME sans stratégie digitale perdent des clients en ligne\n"
            f"✅ Un design professionnel augmente la confiance de 60%\n"
            f"✅ {sujet} = visibilité + crédibilité + croissance\n\n"
        ),
        "promotionnel": (
            f"🚀 NOTRE OFFRE DU MOMENT :\n"
            f"Webdesign & Co accompagne les PME {drapeau} sur {sujet}.\n\n"
            f"✨ CE QUE VOUS OBTENEZ :\n"
            f"🎁 Audit gratuit de votre présence digitale\n"
            f"🎁 Stratégie personnalisée pour votre marché\n"
            f"🎁 Accompagnement de A à Z\n\n"
            f"⏰ Offre valable cette semaine seulement — places limitées !\n\n"
        ),
        "storytelling": (
            f"📖 L'HISTOIRE :\n"
            f"Un de nos clients en {marche.capitalize()} {drapeau} nous a contactés avec un problème simple :\n"
            f"personne ne connaissait son entreprise, malgré 10 ans d'expérience.\n\n"
            f"🔧 NOTRE INTERVENTION sur {sujet} :\n"
            f"Nous avons repensé toute sa présence digitale en 6 semaines.\n\n"
            f"📈 LE RÉSULTAT :\n"
            f"✅ +300% de visibilité en ligne\n"
            f"✅ 3 nouveaux clients en 30 jours\n"
            f"✅ Une image de marque qui inspire confiance\n\n"
        ),
    }

    corps_defaut = (
        f"Chez Webdesign & Co, nous accompagnons les PME {drapeau} dans leur transformation digitale.\n\n"
        f"Notre approche sur {sujet} :\n"
        f"❆ Audit de votre présence digitale\n"
        f"❆ Stratégie sur mesure\n"
        f"❆ Création & déploiement\n"
        f"❆ Suivi & optimisation\n\n"
    )

    corps = corps_ton.get(ton, corps_defaut)

    if reseau == "tiktok":
        contenu = (
            f"🎬 SCRIPT TIKTOK — Webdesign & Co {drapeau}\n"
            f"{'='*50}\n\n"
            f"⏱️ DURÉE CONSEILLÉE : 30-45 secondes\n\n"
            f"🎯 ACCROCHE (0-3 sec) :\n« {hook} »\n\n"
            f"📖 DÉVELOPPEMENT (3-35 sec) :\n"
            f"{corps}"
            f"🔚 CALL TO ACTION (35-45 sec) :\n"
            f"« Suivez-nous pour plus de conseils ! Lien en bio pour un audit gratuit. »\n\n"
            f"#️⃣ HASHTAGS :\n{hashtags} #WebdesignAndCo\n"
        )

    elif reseau == "linkedin":
        contenu = (
            f"💼 POST LINKEDIN — Webdesign & Co {drapeau}\n"
            f"{'='*50}\n\n"
            f"📌 ACCROCHE :\n{hook}\n\n"
            f"📝 CORPS DU POST :\n"
            f"En tant que dirigeant de PME en {marche.capitalize()}, {sujet} est devenu incontournable.\n\n"
            f"{corps}"
            f"🎯 Prêt à passer à l'étape suivante ?\n"
            f"Contactez-nous pour un audit offert → lien en commentaire.\n\n"
            f"♻️ Partagez si cela peut aider un entrepreneur de votre réseau !\n\n"
            f"#️⃣ HASHTAGS :\n{hashtags} #WebdesignAndCo\n"
        )

    else:
        contenu = (
            f"📸 POST INSTAGRAM — Webdesign & Co {drapeau}\n"
            f"{'='*50}\n\n"
            f"🖼️ VISUEL CONSEILLÉ : Mockup design / Avant-Après / Chiffres clés\n\n"
            f"✍️ LÉGENDE :\n"
            f"{hook}\n\n"
            f"✨ {sujet} : le secret des PME qui cartonnent en {marche.capitalize()} {drapeau}\n\n"
            f"{corps}"
            f"👇 Commentez 'AUDIT' pour recevoir votre diagnostic gratuit !\n\n"
            f"#️⃣ HASHTAGS :\n{hashtags} #WebdesignAndCo\n"
        )

    return contenu


@mcp.tool()
def planifier_calendrier(marche: str = "france", semaine_debut: str = "") -> str:
    """
    Génère un calendrier éditorial hebdomadaire complet pour Webdesign & Co.
    marche : 'france' ou 'dubai'.
    semaine_debut : date de début au format JJ/MM/AAAA (optionnel, défaut = lundi prochain).
    """
    marche = marche.lower()
    if marche not in MARCHES:
        return json.dumps({"erreur": "Marché inconnu. Utilisez 'france' ou 'dubai'."}, ensure_ascii=False)

    if semaine_debut:
        try:
            debut = datetime.strptime(semaine_debut, "%d/%m/%Y")
        except ValueError:
            return json.dumps({"erreur": "Format de date invalide. Utilisez JJ/MM/AAAA."}, ensure_ascii=False)
    else:
        aujourd_hui = datetime.now()
        jours_jusqu_lundi = (7 - aujourd_hui.weekday()) % 7 or 7
        debut = aujourd_hui + timedelta(days=jours_jusqu_lundi)

    drapeau = MARCHES[marche]["emoji_drapeau"]
    horaires = MARCHES[marche]["horaires"]

    planning = {
        0: [("linkedin", horaires["linkedin"][0], "Conseil expert / Insight marché"),
            ("instagram", horaires["instagram"][2], "Inspiration / Moodboard design")],
        1: [("tiktok", horaires["tiktok"][1], "Tuto rapide / Tip du jour"),
            ("instagram", horaires["instagram"][0], "Témoignage client / Avant-Après")],
        2: [("linkedin", horaires["linkedin"][1], "Étude de cas / Résultats clients"),
            ("tiktok", horaires["tiktok"][2], "Tendance virale / POV agence web")],
        3: [("instagram", horaires["instagram"][1], "Coulisses de l'agence / BTS"),
            ("linkedin", horaires["linkedin"][2], "Question / Sondage engagement")],
        4: [("tiktok", horaires["tiktok"][0], "Top 3 conseils de la semaine"),
            ("instagram", horaires["instagram"][3], "Post récapitulatif / Best of")],
        5: [("instagram", horaires["instagram"][2], "Contenu inspirant / Citation"),
            ("tiktok", horaires["tiktok"][3], "Récap tendances / À venir la semaine prochaine")],
        6: [("linkedin", horaires["linkedin"][0], "Réflexion du dimanche / Vision 2025")],
    }

    lignes = [
        f"📅 CALENDRIER ÉDITORIAL — Webdesign & Co {drapeau} {marche.upper()}",
        f"Semaine du {debut.strftime('%d/%m/%Y')} au {(debut + timedelta(days=6)).strftime('%d/%m/%Y')}",
        "=" * 55,
        ""
    ]

    icones = {"tiktok": "🎬", "linkedin": "💼", "instagram": "📸"}

    for i in range(7):
        date_jour = debut + timedelta(days=i)
        posts = planning[i]
        lignes.append(f"📆 {JOURS_SEMAINE[i].upper()} {date_jour.strftime('%d/%m')}")
        for reseau, heure, theme in posts:
            lignes.append(f"   {icones[reseau]} {reseau.upper()} — {heure} → {theme}")
        lignes.append("")

    lignes += [
        "=" * 55,
        f"📊 RÉCAP HEBDOMADAIRE : {drapeau} {marche.capitalize()}",
        f"   🎬 TikTok   : {sum(1 for posts in planning.values() for r, _, _ in posts if r == 'tiktok')} posts",
        f"   💼 LinkedIn : {sum(1 for posts in planning.values() for r, _, _ in posts if r == 'linkedin')} posts",
        f"   📸 Instagram: {sum(1 for posts in planning.values() for r, _, _ in posts if r == 'instagram')} posts",
        f"   📌 TOTAL    : {sum(len(p) for p in planning.values())} publications",
        "",
        "💡 Conseil : Préparez tous vos visuels le dimanche précédent pour une semaine sans stress !",
    ]

    return "\n".join(lignes)


@mcp.tool()
def suggerer_hashtags(sujet: str, reseau: str, marche: str = "france", nb_hashtags: int = 15) -> str:
    """
    Propose des hashtags optimisés pour Webdesign & Co selon le réseau et le marché.
    reseau : 'tiktok', 'linkedin' ou 'instagram'.
    marche : 'france' ou 'dubai'.
    nb_hashtags : nombre de hashtags souhaités (5-20).
    """
    reseau = reseau.lower()
    marche = marche.lower()

    if reseau not in ["tiktok", "linkedin", "instagram"]:
        return json.dumps({"erreur": "Réseau inconnu. Utilisez 'tiktok', 'linkedin' ou 'instagram'."}, ensure_ascii=False)
    if marche not in MARCHES:
        return json.dumps({"erreur": "Marché inconnu. Utilisez 'france' ou 'dubai'."}, ensure_ascii=False)

    nb = max(5, min(nb_hashtags, 20))
    drapeau = MARCHES[marche]["emoji_drapeau"]

    hashtag_sujet = "#" + sujet.replace(" ", "").replace("'", "").replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").capitalize()

    pool = HASHTAGS_BASE[reseau][marche].copy()
    pool.insert(0, hashtag_sujet)
    pool.append("#WebdesignAndCo")

    selection = pool[:nb]

    limites = {"tiktok": "5-10 hashtags", "linkedin": "3-5 hashtags", "instagram": "20-30 hashtags"}
    portees = {
        "tiktok": {"volume": "Fort (1M-50M vues)", "frequence": "3-4x par jour"},
        "linkedin": {"volume": "Moyen (10K-500K abonnés)", "frequence": "1x par jour"},
        "instagram": {"volume": "Mixte (niche + large)", "frequence": "1-2x par jour"},
    }

    lignes = [
        f"#️⃣ HASHTAGS — Webdesign & Co {drapeau} {marche.upper()} | {reseau.upper()}",
        f"Sujet : {sujet}",
        "=" * 50,
        "",
        f"✅ HASHTAGS RECOMMANDÉS ({nb}) :",
        " ".join(selection),
        "",
        f"📊 INFOS RÉSEAU :",
        f"   Limite conseillée : {limites[reseau]}",
        f"   Volume d'audience : {portees[reseau]['volume']}",
        f"   Fréquence optimale : {portees[reseau]['frequence']}",
        "",
        f"💡 Stratégie {reseau.upper()} {drapeau} :",
    ]

    if reseau == "tiktok":
        lignes.append("   Mélangez 2 hashtags larges + 2 hashtags niche + #WebdesignAndCo pour maximiser la portée.")
    elif reseau == "linkedin":
        lignes.append("   Privilégiez 3-5 hashtags ultra-ciblés B2B. Évitez les hashtags trop génériques.")
    else:
        lignes.append("   Alternez hashtags populaires (>500K) + niche (<50K) + marque #WebdesignAndCo.")

    return "\n".join(lignes)


@mcp.tool()
def generer_legende(sujet: str, reseau: str, marche: str = "france", objectif: str = "engagement") -> str:
    """
    Crée une légende complète prête à copier-coller pour Webdesign & Co.
    reseau : 'tiktok', 'linkedin' ou 'instagram'.
    marche : 'france' ou 'dubai'.
    objectif : 'engagement', 'vente' ou 'notoriete'.
    """
    reseau = reseau.lower()
    marche = marche.lower()

    if reseau not in ["tiktok", "linkedin", "instagram"]:
        return json.dumps({"erreur": "Réseau inconnu. Utilisez 'tiktok', 'linkedin' ou 'instagram'."}, ensure_ascii=False)
    if marche not in MARCHES:
        return json.dumps({"erreur": "Marché inconnu. Utilisez 'france' ou 'dubai'."}, ensure_ascii=False)

    drapeau = MARCHES[marche]["emoji_drapeau"]

    ctas = {
        "engagement": {
            "tiktok": "💬 Et toi, c'est quoi ta plus grande galère avec ça ? Dis-le en commentaire !",
            "linkedin": "🔔 Suivez Webdesign & Co pour ne manquer aucun conseil. Et vous, quelle est votre expérience ?",
            "instagram": "❤️ Likez si vous êtes d'accord ! Taguez un entrepreneur qui a besoin de lire ça. 👇",
        },
        "vente": {
            "tiktok": "🔗 Lien en bio pour un audit GRATUIT de votre présence digitale. Places limitées !",
            "linkedin": "📩 Envoyez-moi un message privé avec le mot 'AUDIT' pour recevoir votre diagnostic offert.",
            "instagram": "📲 Commentez 'DEVIS' pour recevoir notre offre personnalisée en 24h. DM ouvert ! 💌",
        },
        "notoriete": {
            "tiktok": "➕ Suivez-nous pour des conseils webdesign chaque semaine ! On est là pour vous 🙌",
            "linkedin": "♻️ Partagez ce post si cela peut aider un entrepreneur de votre réseau. Merci !",
            "instagram": "📌 Épinglez ce post pour y revenir plus tard. Sauvegardez-le — il vous servira ! 🔖",
        },
    }

    if objectif not in ctas:
        objectif = "engagement"

    cta = ctas[objectif][reseau]
    hashtags = " ".join(HASHTAGS_BASE[reseau][marche][:8]) + " #WebdesignAndCo"
    emojis_intro = {"tiktok": "🎬", "linkedin": "💼", "instagram": "✨"}
    emoji = emojis_intro[reseau]

    legende = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 LÉGENDE PRÊTE À PUBLIER\n"
        f"Webdesign & Co {drapeau} | {reseau.upper()} | Objectif : {objectif.upper()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} {sujet.upper()} : ce que vous devez savoir en {marche.capitalize()} {drapeau}\n\n"
        f"Vous dirigez une PME et vous voulez vous démarquer en ligne ?\n"
        f"Webdesign & Co est là pour vous. 🚀\n\n"
        f"On accompagne les entrepreneurs francophones {drapeau} depuis des années :\n"
        f"🎨 Identité visuelle sur mesure\n"
        f"💻 Sites web qui convertissent\n"
        f"📱 Stratégie réseaux sociaux\n"
        f"📈 Croissance digitale garantie\n\n"
        f"{sujet} n'est plus une option — c'est une nécessité en 2025.\n\n"
        f"{cta}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{hashtags}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ COPIER-COLLER DIRECTEMENT — Aucune modification nécessaire."
    )

    return legende


# ─────────────────────────────────────────────
# PUBLICATION AUTOMATIQUE
# ─────────────────────────────────────────────

def publier_automatiquement(marche: str, reseau: str):
    """
    Appelé par le scheduler.
    1. Choisit un sujet intelligent (veille > rotation sans doublon)
    2. Choisit un ton en rotation automatique
    3. Génère le contenu pour les 3 réseaux
    4. Enregistre dans le log anti-doublon
    5. Envoie vers Make.com
    """
    sujet, source = choisir_sujet(marche)
    ton = choisir_ton()

    payload = {
        "sujet": sujet,
        "marche": marche,
        "reseau_principal": reseau,
        "ton": ton,
        "source_sujet": source,
        "publications": {
            "tiktok": {
                "contenu": generer_contenu(sujet=sujet, reseau="tiktok", marche=marche, ton=ton),
                "image_url": generer_image_url(sujet, "tiktok"),
            },
            "linkedin": {
                "contenu": generer_contenu(sujet=sujet, reseau="linkedin", marche=marche, ton=ton),
                "image_url": generer_image_url(sujet, "linkedin"),
            },
            "instagram": {
                "contenu": generer_contenu(sujet=sujet, reseau="instagram", marche=marche, ton=ton),
                "image_url": generer_image_url(sujet, "instagram"),
            },
        },
        "hashtags": {
            "tiktok": suggerer_hashtags(sujet=sujet, reseau="tiktok", marche=marche, nb_hashtags=8),
            "linkedin": suggerer_hashtags(sujet=sujet, reseau="linkedin", marche=marche, nb_hashtags=5),
            "instagram": suggerer_hashtags(sujet=sujet, reseau="instagram", marche=marche, nb_hashtags=15),
        },
        "declencheur": "scheduler_automatique",
        "timestamp": datetime.now().isoformat(),
    }

    result = envoyer_vers_make(payload)
    if result.get("status") == "envoyé":
        enregistrer_publication(sujet, marche, reseau, ton=ton, source=source)

    print(f"[SCHEDULER] {marche.upper()} {reseau.upper()} | ton={ton} | source={source} | {sujet[:40]} → {result.get('status')}")


# ─────────────────────────────────────────────
# SCHEDULER
# ─────────────────────────────────────────────

def demarrer_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    charger_log()

    scheduler = BackgroundScheduler(timezone="UTC")

    # France (UTC+2 été)
    horaires_france = {
        "tiktok":    [("05", "00"), ("10", "00"), ("17", "00"), ("19", "00")],
        "linkedin":  [("06", "00"), ("10", "30"), ("15", "30")],
        "instagram": [("06", "00"), ("11", "00"), ("16", "00"), ("19", "00")],
    }
    # Dubai (UTC+4)
    horaires_dubai = {
        "tiktok":    [("04", "00"), ("09", "00"), ("16", "00"), ("18", "00")],
        "linkedin":  [("05", "00"), ("09", "00"), ("14", "00")],
        "instagram": [("05", "00"), ("09", "00"), ("15", "00"), ("17", "30")],
    }

    for reseau, slots in horaires_france.items():
        for heure, minute in slots:
            scheduler.add_job(
                publier_automatiquement,
                CronTrigger(hour=int(heure), minute=int(minute)),
                args=["france", reseau],
                id=f"france_{reseau}_{heure}{minute}",
                replace_existing=True,
            )

    for reseau, slots in horaires_dubai.items():
        for heure, minute in slots:
            scheduler.add_job(
                publier_automatiquement,
                CronTrigger(hour=int(heure), minute=int(minute)),
                args=["dubai", reseau],
                id=f"dubai_{reseau}_{heure}{minute}",
                replace_existing=True,
            )

    # Veille RSS chaque matin à 06h00 UTC
    scheduler.add_job(
        rafraichir_veille,
        CronTrigger(hour=6, minute=0),
        id="veille_rss",
        replace_existing=True,
    )

    # Self-ping toutes les 10 minutes
    scheduler.add_job(
        self_ping,
        CronTrigger(minute="*/10"),
        id="self_ping",
        replace_existing=True,
    )

    scheduler.start()
    total = sum(len(s) for s in horaires_france.values()) + sum(len(s) for s in horaires_dubai.values())
    print(f"⏰ Scheduler démarré — {total} publications/jour + veille RSS 06h00 + self-ping /10min")
    return scheduler


# ─────────────────────────────────────────────
# SERVEUR HTTP
# ─────────────────────────────────────────────

def run_webhook_server():
    from fastapi import FastAPI, Request, HTTPException, Header
    from fastapi.responses import JSONResponse
    import uvicorn

    WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "webdesign-co-secret")

    app = FastAPI(
        title="Webdesign & Co — Webhook Make.com",
        description="API webhook pour publier automatiquement sur TikTok, LinkedIn et Instagram",
        version="2.0.0",
    )

    def verifier_secret(x_webhook_secret: str = Header(default="")):
        if x_webhook_secret != WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Secret invalide.")

    scheduler = demarrer_scheduler()

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "service": "Webdesign & Co Webhook",
            "scheduler": "running",
            "publications_loggees": len(_publications_log),
            "tendances_veille": {m: len(t) for m, t in TENDANCES_VEILLE.items()},
        }

    @app.get("/scheduler/status")
    async def scheduler_status():
        jobs = [
            {"id": job.id, "next_run": job.next_run_time.isoformat() if job.next_run_time else None}
            for job in scheduler.get_jobs()
        ]
        return JSONResponse({
            "scheduler": "running",
            "total_jobs": len(jobs),
            "make_webhook": MAKE_WEBHOOK_URL,
            "jobs": jobs,
        })

    @app.get("/log/publications")
    async def log_publications():
        return JSONResponse({
            "total": len(_publications_log),
            "publications": _publications_log[-50:],
        })

    @app.get("/veille/tendances")
    async def veille_tendances():
        return JSONResponse({"tendances": TENDANCES_VEILLE})

    @app.post("/veille/rafraichir")
    async def veille_rafraichir(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        rafraichir_veille()
        return JSONResponse({"status": "ok", "tendances": TENDANCES_VEILLE})

    @app.post("/scheduler/publier-maintenant")
    async def scheduler_publier_maintenant(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        marche = data.get("marche", "france")
        reseau = data.get("reseau", "instagram")
        publier_automatiquement(marche, reseau)
        return JSONResponse({"status": "déclenché", "marche": marche, "reseau": reseau})

    @app.post("/webhook/generer-contenu")
    async def webhook_generer_contenu(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        sujet = data.get("sujet", "")
        if not sujet:
            raise HTTPException(status_code=400, detail="Le champ 'sujet' est requis.")
        contenu = generer_contenu(
            sujet=sujet,
            reseau=data.get("reseau", "instagram"),
            marche=data.get("marche", "france"),
            ton=data.get("ton", "professionnel"),
        )
        return JSONResponse({"status": "success", "reseau": data.get("reseau"), "marche": data.get("marche"), "contenu": contenu})

    @app.post("/webhook/publier-tous-reseaux")
    async def webhook_publier_tous_reseaux(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        sujet = data.get("sujet", "")
        if not sujet:
            raise HTTPException(status_code=400, detail="Le champ 'sujet' est requis.")
        marche = data.get("marche", "france")
        ton = data.get("ton", choisir_ton())
        image_url = data.get("image_url", "")
        date_publication = data.get("date_publication", "")
        return JSONResponse({
            "status": "success",
            "sujet": sujet,
            "marche": marche,
            "ton": ton,
            "image_url": image_url or generer_image_url(sujet, "instagram"),
            "date_publication": date_publication,
            "publications": {
                "tiktok": {
                    "contenu": generer_contenu(sujet=sujet, reseau="tiktok", marche=marche, ton=ton),
                    "image_url": image_url or generer_image_url(sujet, "tiktok"),
                    "date_publication": date_publication,
                },
                "linkedin": {
                    "contenu": generer_contenu(sujet=sujet, reseau="linkedin", marche=marche, ton=ton),
                    "image_url": image_url or generer_image_url(sujet, "linkedin"),
                    "date_publication": date_publication,
                },
                "instagram": {
                    "contenu": generer_contenu(sujet=sujet, reseau="instagram", marche=marche, ton=ton),
                    "image_url": image_url or generer_image_url(sujet, "instagram"),
                    "date_publication": date_publication,
                },
            },
            "hashtags": {
                "tiktok": suggerer_hashtags(sujet=sujet, reseau="tiktok", marche=marche, nb_hashtags=8),
                "linkedin": suggerer_hashtags(sujet=sujet, reseau="linkedin", marche=marche, nb_hashtags=5),
                "instagram": suggerer_hashtags(sujet=sujet, reseau="instagram", marche=marche, nb_hashtags=15),
            },
        })

    @app.post("/webhook/analyser-tendances")
    async def webhook_analyser_tendances(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        return JSONResponse({
            "status": "success",
            "tendances": analyser_tendances(
                marche=data.get("marche", "france"),
                nb_tendances=int(data.get("nb_tendances", 5)),
            ),
        })

    @app.post("/webhook/planifier-calendrier")
    async def webhook_planifier_calendrier(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        return JSONResponse({
            "status": "success",
            "calendrier": planifier_calendrier(
                marche=data.get("marche", "france"),
                semaine_debut=data.get("semaine_debut", ""),
            ),
        })

    @app.post("/webhook/generer-legende")
    async def webhook_generer_legende(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        sujet = data.get("sujet", "")
        if not sujet:
            raise HTTPException(status_code=400, detail="Le champ 'sujet' est requis.")
        return JSONResponse({
            "status": "success",
            "legende": generer_legende(
                sujet=sujet,
                reseau=data.get("reseau", "instagram"),
                marche=data.get("marche", "france"),
                objectif=data.get("objectif", "engagement"),
            ),
        })

    @app.post("/webhook/surveiller-concurrence")
    async def webhook_surveiller_concurrence(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        marche = data.get("marche", "france")
        inclure_tiktok = data.get("inclure_tiktok", False)
        mot_cle_tiktok = data.get("mot_cle_tiktok", "")
        return JSONResponse({
            "status": "success",
            "rapport": surveiller_concurrence(
                marche=marche,
                inclure_tiktok=inclure_tiktok,
                mot_cle_tiktok=mot_cle_tiktok,
            ),
        })

    @app.post("/webhook/post-concurrent")
    async def webhook_post_concurrent(request: Request):
        """
        Génère et envoie vers Make un post LinkedIn/IG/TikTok attaquant une faille concurrentielle.
        Body JSON : { "faille": "formulaire_statique", "marche": "dubai", "reseau": "linkedin", "envoyer_make": true }
        Failles disponibles : formulaire_statique | relance_manuelle | audit_manuel | reporting_manuel | texte libre
        """
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        faille = data.get("faille", "formulaire_statique")
        marche = data.get("marche", "france")
        reseau = data.get("reseau", "linkedin")
        envoyer_make = data.get("envoyer_make", True)

        post_json = generer_post_concurrent(faille=faille, marche=marche, reseau=reseau)
        payload = json.loads(post_json)

        make_result = {}
        if envoyer_make:
            make_result = envoyer_vers_make(payload)
            if make_result.get("status") == "envoyé":
                enregistrer_publication(faille, marche, reseau, ton="concurrent", source="post_concurrent")

        return JSONResponse({
            "status": "success",
            "post": payload,
            "make_result": make_result,
        })

    @app.post("/webhook/envoyer-vers-make")
    async def webhook_envoyer_vers_make(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        sujet = data.get("sujet", "")
        if not sujet:
            raise HTTPException(status_code=400, detail="Le champ 'sujet' est requis.")
        marche = data.get("marche", "france")
        ton = data.get("ton", choisir_ton())
        image_url_fournie = data.get("image_url", "")

        payload = {
            "sujet": sujet,
            "marche": marche,
            "ton": ton,
            "publications": {
                "tiktok": {
                    "contenu": generer_contenu(sujet=sujet, reseau="tiktok", marche=marche, ton=ton),
                    "image_url": image_url_fournie or generer_image_url(sujet, "tiktok"),
                },
                "linkedin": {
                    "contenu": generer_contenu(sujet=sujet, reseau="linkedin", marche=marche, ton=ton),
                    "image_url": image_url_fournie or generer_image_url(sujet, "linkedin"),
                },
                "instagram": {
                    "contenu": generer_contenu(sujet=sujet, reseau="instagram", marche=marche, ton=ton),
                    "image_url": image_url_fournie or generer_image_url(sujet, "instagram"),
                },
            },
            "hashtags": {
                "tiktok": suggerer_hashtags(sujet=sujet, reseau="tiktok", marche=marche, nb_hashtags=8),
                "linkedin": suggerer_hashtags(sujet=sujet, reseau="linkedin", marche=marche, nb_hashtags=5),
                "instagram": suggerer_hashtags(sujet=sujet, reseau="instagram", marche=marche, nb_hashtags=15),
            },
            "calendrier": planifier_calendrier(marche=marche),
        }

        make_result = envoyer_vers_make(payload)
        return JSONResponse({
            "status": "success",
            "make_webhook": MAKE_WEBHOOK_URL,
            "make_result": make_result,
            "payload_envoye": payload,
        })

    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Webhook Webdesign & Co v2.0 démarré sur http://0.0.0.0:{port}")
    print(f"📖 Documentation : http://0.0.0.0:{port}/docs")
    print(f"🔐 Secret actif  : {WEBHOOK_SECRET}")
    print(f"📡 Make.com URL  : {MAKE_WEBHOOK_URL}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    if "--webhook" in sys.argv:
        run_webhook_server()
    else:
        mcp.run()
