from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
import json
import os
import random
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# ─────────────────────────────────────────────
# IMAGE
# ─────────────────────────────────────────────

_drive_image_ids: list = []


def _charger_images_drive() -> list:
    """Liste et met en cache les IDs d'images du dossier Google Drive dédié."""
    global _drive_image_ids
    if _drive_image_ids:
        return _drive_image_ids
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        print("[DRIVE] GOOGLE_SERVICE_ACCOUNT_JSON non défini — images Drive indisponibles.")
        return []
    try:
        from google.oauth2.service_account import Credentials
        from google.auth.transport.requests import Request as GoogleRequest
        sa_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )
        creds.refresh(GoogleRequest())
        q = urllib.parse.quote(f"'{GOOGLE_DRIVE_IMAGES_FOLDER_ID}' in parents and mimeType contains 'image/'")
        url = f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)&pageSize=100"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {creds.token}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        _drive_image_ids = [f["id"] for f in data.get("files", [])]
        print(f"[DRIVE] {len(_drive_image_ids)} images chargées (dossier {GOOGLE_DRIVE_IMAGES_FOLDER_ID})")
    except Exception as e:
        print(f"[DRIVE] Erreur chargement images : {e}")
    return _drive_image_ids


def _choisir_query_pexels(sujet: str, reseau: str) -> str:
    """Sélectionne la requête Pexels la plus pertinente selon le sujet et le réseau."""
    s = sujet.lower()
    if any(k in s for k in ["dubai", "emirat", "émirat", "golfe", "moyen-orient", "gulf"]):
        return "Dubai business skyline modern"
    if reseau == "linkedin" or any(k in s for k in ["b2b", "dirigeant", "professionnel", "réunion", "management"]):
        return "business professional meeting office"
    if any(k in s for k in ["marketing", "seo", "référencement", "community", "réseaux sociaux", "campagne", "publicité"]):
        return "digital marketing laptop professional"
    return "web design agency purple digital"


def generer_image_url(sujet: str, reseau: str = "instagram") -> str:
    """Pexels (priorité absolue, requête thématique) → Google Drive. Jamais Picsum."""
    # Priorité 1 : Pexels API — toujours en premier
    if PEXELS_API_KEY:
        query = _choisir_query_pexels(sujet, reseau)
        orientations = {"tiktok": "portrait", "instagram": "square", "linkedin": "landscape"}
        orientation = orientations.get(reseau, "landscape")
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote_plus(query)}&per_page=15&orientation={orientation}"
        try:
            req = urllib.request.Request(url, headers={"Authorization": PEXELS_API_KEY})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            photos = data.get("photos", [])
            if photos:
                photo = photos[sum(ord(c) for c in sujet) % len(photos)]
                sizes = {"instagram": "large2x", "tiktok": "portrait", "linkedin": "large2x"}
                return photo["src"].get(sizes.get(reseau, "large2x"), photo["src"]["original"])
        except Exception as e:
            print(f"[PEXELS] Erreur image {reseau} : {e}")

    # Priorité 2 : Google Drive (dossier dédié Webdesign & Co)
    ids = _charger_images_drive()
    if ids:
        file_id = ids[sum(ord(c) for c in sujet + reseau) % len(ids)]
        return f"https://drive.google.com/uc?export=view&id={file_id}"

    print(f"[IMAGE] Aucune source disponible (Pexels KO, Drive KO) pour {reseau} — {sujet[:30]}")
    return ""


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
POSTS_USED_FILE = "posts_used.json"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
GOOGLE_DRIVE_IMAGES_FOLDER_ID = "17mBms_qbrP0oZNBfikFTHbtiIGvaHdt-"

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


_posts_used: set = set()


def charger_posts_used():
    global _posts_used
    try:
        with open(POSTS_USED_FILE, "r", encoding="utf-8") as f:
            _posts_used = set(json.load(f))
        print(f"[POSTS_USED] {len(_posts_used)} entrées chargées")
    except (FileNotFoundError, json.JSONDecodeError):
        _posts_used = set()


def marquer_post_utilise(sujet: str, marche: str, reseau: str):
    _posts_used.add(f"{sujet}|{marche}|{reseau}")
    try:
        with open(POSTS_USED_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(_posts_used), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[POSTS_USED] Sauvegarde échouée : {e}")


def post_deja_publie(sujet: str, marche: str, reseau: str) -> bool:
    return f"{sujet}|{marche}|{reseau}" in _posts_used


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

TENDANCES_VEILLE: dict = {"france": [], "dubai": []}

RSS_QUERIES = {
    "france": "webdesign+agence+digitale+PME+identité+visuelle",
    "dubai": "web+design+digital+agency+Dubai+francophone",
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


def rafraichir_veille():
    """Appelé chaque matin à 06h00 UTC pour mettre à jour les tendances."""
    for marche in ["france", "dubai"]:
        titres = scraper_tendances_rss(marche)
        TENDANCES_VEILLE[marche] = titres


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
    sujets_28 = SUJETS_FRANCE_28 if marche == "france" else SUJETS_DUBAI_28

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
}

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
    },
}

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
# CAPTION SOCIALE (sans headers structurels)
# ─────────────────────────────────────────────

def _generer_caption_sociale(sujet: str, reseau: str, marche: str = "france", ton: str = "professionnel") -> str:
    """Texte propre prêt à publier, sans séparateurs ni titres de section."""
    drapeau = MARCHES[marche]["emoji_drapeau"]
    hashtags = " ".join(HASHTAGS_BASE[reseau][marche][:8]) + " #WebdesignAndCo"

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
    }
    hook = random.choice(hooks.get(ton, hooks["professionnel"]))

    corps_ton = {
        "educatif": (
            f"📖 Pourquoi c'est important :\n"
            f"{sujet} est l'un des leviers les plus puissants pour les PME {drapeau} en 2025.\n\n"
            f"✅ 78% des PME sans stratégie digitale perdent des clients en ligne\n"
            f"✅ Un design professionnel augmente la confiance de 60%\n"
            f"✅ {sujet} = visibilité + crédibilité + croissance\n\n"
        ),
        "promotionnel": (
            f"🚀 Notre offre du moment :\n"
            f"🎁 Audit gratuit de votre présence digitale\n"
            f"🎁 Stratégie personnalisée pour votre marché\n"
            f"🎁 Accompagnement de A à Z\n\n"
            f"⏰ Offre valable cette semaine seulement — places limitées !\n\n"
        ),
        "storytelling": (
            f"Un de nos clients en {marche.capitalize()} {drapeau} nous a contactés : personne ne connaissait son entreprise malgré 10 ans d'expérience.\n\n"
            f"On a repensé toute sa présence digitale en 6 semaines.\n\n"
            f"✅ +300% de visibilité en ligne\n"
            f"✅ 3 nouveaux clients en 30 jours\n"
            f"✅ Une image de marque qui inspire confiance\n\n"
        ),
    }
    corps_defaut = (
        f"Chez Webdesign & Co, nous accompagnons les PME {drapeau} dans leur transformation digitale.\n\n"
        f"❆ Audit de votre présence digitale\n"
        f"❆ Stratégie sur mesure\n"
        f"❆ Création & déploiement\n"
        f"❆ Suivi & optimisation\n\n"
    )
    corps = corps_ton.get(ton, corps_defaut)

    if reseau == "tiktok":
        return (
            f"{hook}\n\n"
            f"{corps}"
            f"Suivez-nous pour plus de conseils ! Lien en bio pour un audit gratuit. 🔗\n\n"
            f"{hashtags}"
        )
    elif reseau == "linkedin":
        return (
            f"{hook}\n\n"
            f"En tant que dirigeant de PME en {marche.capitalize()}, {sujet} est devenu incontournable.\n\n"
            f"{corps}"
            f"Prêt à passer à l'étape suivante ?\n"
            f"Contactez-nous pour un audit offert → lien en commentaire.\n\n"
            f"♻️ Partagez si cela peut aider un entrepreneur de votre réseau !\n\n"
            f"{hashtags}"
        )
    else:
        return (
            f"{hook}\n\n"
            f"✨ {sujet} : le secret des PME qui cartonnent en {marche.capitalize()} {drapeau}\n\n"
            f"{corps}"
            f"👇 Commentez 'AUDIT' pour recevoir votre diagnostic gratuit !\n\n"
            f"{hashtags}"
        )


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

    if post_deja_publie(sujet, marche, reseau):
        print(f"[SCHEDULER] SKIP (déjà publié) : {marche.upper()} {reseau.upper()} | {sujet[:40]}")
        return

    payload = {
        "sujet": sujet,
        "marche": marche,
        "reseau_principal": reseau,
        "ton": ton,
        "source_sujet": source,
        "publications": {
            "tiktok": {
                "contenu": _generer_caption_sociale(sujet=sujet, reseau="tiktok", marche=marche, ton=ton),
                "image_url": generer_image_url(sujet, "tiktok"),
            },
            "linkedin": {
                "contenu": _generer_caption_sociale(sujet=sujet, reseau="linkedin", marche=marche, ton=ton),
                "image_url": generer_image_url(sujet, "linkedin"),
            },
            "instagram": {
                "contenu": _generer_caption_sociale(sujet=sujet, reseau="instagram", marche=marche, ton=ton),
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
        marquer_post_utilise(sujet, marche, reseau)

    print(f"[SCHEDULER] {marche.upper()} {reseau.upper()} | ton={ton} | source={source} | {sujet[:40]} → {result.get('status')}")


# ─────────────────────────────────────────────
# SCHEDULER
# ─────────────────────────────────────────────

def demarrer_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    charger_log()
    charger_posts_used()

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
