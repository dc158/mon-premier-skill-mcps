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
def generer_script_audit_tiktok(
    marche: str = "france",
    angle: str = "site_web",
    duree: int = 60,
) -> str:
    """
    Génère un script TikTok/Reels 'Audit 60 sec' prêt à filmer pour Webdesign & Co.
    Intègre le mot-clé AUDIT pour ManyChat automation.
    marche : 'france' ou 'dubai'.
    angle : 'site_web', 'reseaux_sociaux', 'identite_visuelle', 'seo', 'ecommerce'.
    duree : durée cible en secondes (30, 45 ou 60).
    """
    marche = marche.lower()
    if marche not in MARCHES:
        return json.dumps({"erreur": "Marché inconnu. Utilisez 'france' ou 'dubai'."}, ensure_ascii=False)

    drapeau = MARCHES[marche]["emoji_drapeau"]

    angles = {
        "site_web": {
            "titre": "Audit de site web",
            "hook": "Votre site web fait FUIR vos clients sans que vous le sachiez.",
            "probleme": "80% des PME {marche} perdent des clients à cause d'un site lent, mal conçu ou pas mobile.",
            "preuve": "Un site qui met +3 secondes à charger = 53% des visiteurs qui partent. Pour de bon.",
            "solution": "En 60 secondes, je peux identifier les 3 erreurs qui vous coûtent des clients chaque jour.",
            "cta_verbal": "Commentez AUDIT sous cette vidéo — vous recevez votre diagnostic gratuit en 24h.",
        },
        "reseaux_sociaux": {
            "titre": "Audit réseaux sociaux",
            "hook": "Vous postez chaque semaine et personne ne vous voit. Voilà pourquoi.",
            "probleme": "Poster sans stratégie en {marche}, c'est comme crier dans le désert. Le contenu seul ne suffit plus.",
            "preuve": "L'algorithme favorise la cohérence, le bon format et les bons horaires. Sans ça : 0 portée.",
            "solution": "Je scanne votre présence sociale en 60 secondes et j'identifie ce qui bloque votre croissance.",
            "cta_verbal": "Tapez AUDIT en commentaire — audit de vos réseaux offert, sans engagement.",
        },
        "identite_visuelle": {
            "titre": "Audit identité visuelle",
            "hook": "Votre logo fait fuir des clients premium avant même qu'ils vous lisent.",
            "probleme": "En {marche}, le premier jugement se fait en 0,05 seconde. Une image amateur = client perdu.",
            "preuve": "Les entreprises avec une identité visuelle cohérente génèrent 33% de revenus en plus.",
            "solution": "Audit de votre image de marque en 60 secondes : logo, couleurs, cohérence, impact premium.",
            "cta_verbal": "Commentez AUDIT pour recevoir votre analyse visuelle gratuite — directement en DM.",
        },
        "seo": {
            "titre": "Audit SEO",
            "hook": "Vos concurrents apparaissent sur Google. Pas vous. Voici pourquoi.",
            "probleme": "93% des expériences en ligne commencent sur Google. Si vous n'êtes pas en page 1 en {marche}, vous n'existez pas.",
            "preuve": "Les 3 premiers résultats Google captent 75% des clics. La page 2 : quasi zéro trafic.",
            "solution": "J'analyse votre positionnement SEO en 60 secondes et vous donne les 3 actions prioritaires.",
            "cta_verbal": "Tapez AUDIT — vous recevez votre rapport SEO gratuit avec les mots-clés à cibler.",
        },
        "ecommerce": {
            "titre": "Audit e-commerce",
            "hook": "Votre boutique en ligne reçoit des visites mais ne vend pas. C'est réparable.",
            "probleme": "Le taux de conversion moyen d'un e-commerce est de 2%. En dessous ? Vous perdez de l'argent chaque jour.",
            "preuve": "Tunnel de vente mal optimisé, photos pauvres, absence de preuve sociale = panier abandonné.",
            "solution": "Audit complet de votre boutique en 60 secondes : UX, tunnel, confiance, conversion.",
            "cta_verbal": "Commentez AUDIT pour votre diagnostic e-commerce offert — réponse sous 24h.",
        },
    }

    a = angles.get(angle, angles["site_web"])
    probleme = a["probleme"].replace("{marche}", "France" if marche == "france" else "Dubai")

    timings = {
        30: {"hook": "0-2s", "probleme": "2-12s", "preuve": "12-22s", "solution": "22-27s", "cta": "27-30s"},
        45: {"hook": "0-3s", "probleme": "3-18s", "preuve": "18-33s", "solution": "33-40s", "cta": "40-45s"},
        60: {"hook": "0-3s", "probleme": "3-20s", "preuve": "20-38s", "solution": "38-50s", "cta": "50-60s"},
    }
    t = timings.get(duree, timings[60])

    hashtags_audit = {
        "france": "#AuditGratuit #PMEFrance #WebdesignAndCo #AgenceWeb #ConseilDigital #MarketingFrance #TipsEntrepreneur",
        "dubai": "#AuditGratuit #PMEDubai #WebdesignAndCo #AgenceWebDubai #FrancophonesDubai #DigitalDubai #EntrepreneurDubai",
    }

    script = (
        f"🎬 SCRIPT TIKTOK/REELS — {a['titre'].upper()} 60 SEC\n"
        f"Webdesign & Co {drapeau} | Mot-clé ManyChat : AUDIT\n"
        f"{'='*55}\n\n"
        f"⏱️ DURÉE : {duree} secondes | FORMAT : Vertical 9:16\n"
        f"🎥 DÉCOR CONSEILLÉ : Bureau pro / fond violet #7B2FFF / mockup laptop\n\n"
        f"━━━ [{t['hook']}] HOOK ━━━\n"
        f"(Texte à l'écran + voix) :\n"
        f'« {a["hook"]} »\n\n'
        f"━━━ [{t['probleme']}] PROBLÈME ━━━\n"
        f"(Voix off / face caméra) :\n"
        f'« {probleme} »\n\n'
        f"━━━ [{t['preuve']}] PREUVE / CHIFFRE ━━━\n"
        f"(Texte animé à l'écran + voix) :\n"
        f'« {a["preuve"]} »\n\n'
        f"━━━ [{t['solution']}] SOLUTION WEBDESIGN & CO ━━━\n"
        f"(Face caméra, ton direct) :\n"
        f'« {a["solution"]} »\n\n'
        f"━━━ [{t['cta']}] CALL TO ACTION MANYCHAT ━━━\n"
        f"(Texte GRAND à l'écran + voix forte) :\n"
        f'« {a["cta_verbal"]} »\n\n'
        f"📌 TEXTE ÉPINGLÉ EN COMMENTAIRE :\n"
        f"Tapez AUDIT pour recevoir votre diagnostic offert par Webdesign & Co {drapeau}\n\n"
        f"🔧 CONFIG MANYCHAT :\n"
        f"   Déclencheur  : Commentaire contient « AUDIT » (insensible à la casse)\n"
        f"   Réponse auto : DM avec lien vers formulaire d'audit\n"
        f"   Délai        : Immédiat (réponse < 1 min)\n"
        f"   Message DM   : « Bonjour ! Votre audit {a['titre']} est en cours de préparation. Réponse sous 24h. — Webdesign & Co {drapeau} »\n\n"
        f"#️⃣ HASHTAGS :\n{hashtags_audit[marche]}\n\n"
        f"{'='*55}\n"
        f"✅ Script validé — Filmez, montez, publiez. ManyChat fait le reste."
    )
    return script


# ─────────────────────────────────────────────
# DONNÉES CONCURRENCE FRANCOPHONE
# ─────────────────────────────────────────────

CONCURRENTS_DATA = {
    "eskimoz": {
        "nom": "Eskimoz",
        "pays": "France",
        "positionnement": "Agence SEO & SEM premium, grande entreprise",
        "forces": ["Forte notoriété SEO", "Blog technique très riche", "Clients grands comptes"],
        "failles": [
            "Trop technique, inaccessible aux PME",
            "Aucune présence Dubai / Moyen-Orient",
            "Tarifs enterprise uniquement (>5K€/mois)",
            "Peu de contenu social media / TikTok",
            "Pas de positionnement francophone international",
        ],
        "accroche_type": "Boostez votre trafic organique",
        "reseaux_forts": ["LinkedIn", "Blog"],
        "angle_contre": "Nous sommes l'agence SEO + design ACCESSIBLE aux PME, avec la dimension Dubai en bonus.",
    },
    "junto": {
        "nom": "Junto",
        "pays": "France",
        "positionnement": "Performance marketing & acquisition payante",
        "forces": ["Expertise Google Ads / Meta Ads", "Data-driven", "Résultats mesurables"],
        "failles": [
            "Zéro création de marque ou design",
            "Pas de stratégie organique / content",
            "Uniquement performance, pas de storytelling",
            "Audience limitée France uniquement",
            "Aucune offre PME africaine ou Dubai",
        ],
        "accroche_type": "Maximisez votre ROI publicitaire",
        "reseaux_forts": ["LinkedIn"],
        "angle_contre": "Nous combinons performance ET branding — la pub qui convertit grâce à une image qui inspire confiance.",
    },
    "linkeo": {
        "nom": "Linkeo",
        "pays": "France",
        "positionnement": "Création de site web pour TPE/PME, volume",
        "forces": ["Prix d'entrée bas", "Large réseau commercial", "Cible PME"],
        "failles": [
            "Templates génériques, aucune différenciation",
            "Contrat longue durée contraignant",
            "Support client médiocre (avis clients négatifs)",
            "Pas de stratégie digitale globale",
            "Image bas de gamme, pas premium",
        ],
        "accroche_type": "Votre site web en quelques jours",
        "reseaux_forts": ["Google Ads"],
        "angle_contre": "Nous créons des sites qui CONVERTISSENT, pas des vitrines génériques. Sur-mesure, premium, sans engagement abusif.",
    },
    "agence_boosteur": {
        "nom": "Agence Boosteur",
        "pays": "France/Afrique",
        "positionnement": "Marketing digital pour entrepreneurs francophones",
        "forces": ["Cible francophone", "Contenu pédagogique", "Prix accessibles"],
        "failles": [
            "Pas de présence Dubai / Golfe",
            "Design moyen, pas premium",
            "Faible autorité de domaine",
            "Peu d'études de cas chiffrées",
            "Pas d'expertise e-commerce avancée",
        ],
        "accroche_type": "Développez votre business en ligne",
        "reseaux_forts": ["Instagram", "YouTube"],
        "angle_contre": "Nous sommes francophones ET premium ET Dubai — la seule agence qui couvre France + Afrique + Golfe avec une image luxury.",
    },
    "webqam": {
        "nom": "Webqam",
        "pays": "France",
        "positionnement": "Agence web & marketing digital, ETI/PME",
        "forces": ["Expertise technique solide", "Portfolio varié", "Grenoble + Paris"],
        "failles": [
            "Aucune dimension internationale",
            "Peu actif sur TikTok / réseaux modernes",
            "Pas de positionnement niche / sectoriel clair",
            "Pas d'offre francophone Afrique ou Dubai",
            "Communication corporate froide",
        ],
        "accroche_type": "Votre partenaire digital de confiance",
        "reseaux_forts": ["LinkedIn", "Blog"],
        "angle_contre": "Nous avons la même expertise technique, mais avec un positionnement franco-émirati unique et une communication qui engage.",
    },
}


@mcp.tool()
def analyser_concurrence(concurrent: str = "tous", marche: str = "france") -> str:
    """
    Analyse concurrentielle intégrée des agences digitales francophones.
    concurrent : 'eskimoz', 'junto', 'linkeo', 'agence_boosteur', 'webqam', ou 'tous'.
    marche : 'france' ou 'dubai' (positionne l'analyse selon le marché cible).
    """
    marche = marche.lower()
    drapeau = MARCHES.get(marche, MARCHES["france"])["emoji_drapeau"]

    if concurrent != "tous" and concurrent not in CONCURRENTS_DATA:
        connus = ", ".join(CONCURRENTS_DATA.keys())
        return json.dumps({"erreur": f"Concurrent inconnu. Options : {connus}, tous"}, ensure_ascii=False)

    cibles = CONCURRENTS_DATA if concurrent == "tous" else {concurrent: CONCURRENTS_DATA[concurrent]}

    lignes = [
        f"🔍 ANALYSE CONCURRENTIELLE — Webdesign & Co {drapeau}",
        f"Marché cible : {marche.upper()} | {len(cibles)} concurrent(s) analysé(s)",
        "=" * 60,
        "",
    ]

    for slug, c in cibles.items():
        lignes += [
            f"🏢 {c['nom'].upper()} ({c['pays']})",
            f"   Positionnement : {c['positionnement']}",
            f"   Réseaux forts  : {', '.join(c['reseaux_forts'])}",
            f"   Accroche type  : « {c['accroche_type']} »",
            "",
            f"   ✅ FORCES :",
        ]
        for f in c["forces"]:
            lignes.append(f"      + {f}")
        lignes += ["", f"   ⚠️  FAILLES À EXPLOITER :"]
        for faille in c["failles"]:
            lignes.append(f"      ✗ {faille}")
        lignes += [
            "",
            f"   🎯 ANGLE WEBDESIGN & CO CONTRE {c['nom'].upper()} :",
            f"      → {c['angle_contre']}",
            "",
            "─" * 60,
            "",
        ]

    lignes += [
        "🏆 AVANTAGES UNIQUES WEBDESIGN & CO — NON RÉPLICABLES :",
        "   ① Seule agence francophone avec ancrage Dubai réel (Claire Chali)",
        "   ② PME + premium : qualité luxury à prix PME",
        "   ③ Coverage France + Afrique francophone + Golfe (3 marchés en 1)",
        "   ④ Machine de contenu social : TikTok / LinkedIn / Instagram automatisés",
        "   ⑤ Lead magnet audit offert : entrée à coût zéro pour le prospect",
        "",
        "📌 MESSAGE CLÉ À MARTELER (tous réseaux) :",
        f'   « L\'agence digitale premium qui parle votre langue, de Paris à Dubai. » {drapeau}🇫🇷🇦🇪',
    ]

    return "\n".join(lignes)


@mcp.tool()
def generer_campagne_semaine(
    marche: str = "france",
    semaine_debut: str = "",
    objectif: str = "leads",
) -> str:
    """
    Génère la campagne complète d'une semaine : 3 posts LinkedIn + scripts TikTok + stratégie.
    marche : 'france' ou 'dubai'.
    semaine_debut : date JJ/MM/AAAA (optionnel, défaut = lundi prochain).
    objectif : 'leads', 'notoriete' ou 'engagement'.
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
    sujets_28 = SUJETS_FRANCE_28 if marche == "france" else SUJETS_DUBAI_28
    jour = debut.timetuple().tm_yday

    # 3 sujets LinkedIn distincts sur la semaine
    sujets_linkedin = [
        sujets_28[(jour + i * 9) % len(sujets_28)] for i in range(3)
    ]
    # 2 angles TikTok Audit
    angles_tiktok = ["site_web", "reseaux_sociaux"]

    cta_objectif = {
        "leads": "📩 Commentez AUDIT pour votre diagnostic gratuit.",
        "notoriete": "♻️ Partagez si cela peut aider un entrepreneur de votre réseau.",
        "engagement": "💬 Quel est votre plus grand défi digital en ce moment ?",
    }
    cta = cta_objectif.get(objectif, cta_objectif["leads"])

    lignes = [
        f"📅 CAMPAGNE SEMAINE — Webdesign & Co {drapeau} {marche.upper()}",
        f"Du {debut.strftime('%d/%m/%Y')} — Objectif : {objectif.upper()}",
        "=" * 60,
        "",
        "━━━ LUNDI — POST LINKEDIN #1 (Insight Expert) ━━━",
        f"📌 Sujet : {sujets_linkedin[0]}",
        f"⏰ Heure : {MARCHES[marche]['horaires']['linkedin'][0]}",
        "",
        generer_contenu(sujets_linkedin[0], "linkedin", marche, "professionnel"),
        "",
        "━━━ MERCREDI — POST LINKEDIN #2 (Étude de Cas) ━━━",
        f"📌 Sujet : {sujets_linkedin[1]}",
        f"⏰ Heure : {MARCHES[marche]['horaires']['linkedin'][1]}",
        "",
        generer_contenu(sujets_linkedin[1], "linkedin", marche, "storytelling"),
        "",
        "━━━ VENDREDI — POST LINKEDIN #3 (Engagement) ━━━",
        f"📌 Sujet : {sujets_linkedin[2]}",
        f"⏰ Heure : {MARCHES[marche]['horaires']['linkedin'][2]}",
        "",
        generer_contenu(sujets_linkedin[2], "linkedin", marche, "educatif"),
        "",
        "━━━ TIKTOK/REELS #1 (Mardi) — Audit Site Web ━━━",
        f"⏰ Heure : {MARCHES[marche]['horaires']['tiktok'][1]}",
        "",
        generer_script_audit_tiktok(marche, angles_tiktok[0], 60),
        "",
        "━━━ TIKTOK/REELS #2 (Jeudi) — Audit Réseaux Sociaux ━━━",
        f"⏰ Heure : {MARCHES[marche]['horaires']['tiktok'][2]}",
        "",
        generer_script_audit_tiktok(marche, angles_tiktok[1], 45),
        "",
        "=" * 60,
        f"📊 RÉCAP CAMPAGNE SEMAINE {drapeau} :",
        f"   💼 LinkedIn : 3 posts (Lundi / Mercredi / Vendredi)",
        f"   🎬 TikTok   : 2 scripts Audit (Mardi / Jeudi)",
        f"   🎯 CTA unifié : {cta}",
        f"   🤖 ManyChat : Mot-clé AUDIT actif sur tous les TikTok",
        "",
        "💡 Conseil : Filmez les 2 TikTok le même jour (lundi matin), programmez le reste.",
    ]

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
# AUDIT DE SITE WEB
# ─────────────────────────────────────────────

def _fetch_html(url: str, timeout: int = 15) -> tuple:
    """Récupère le HTML d'une URL. Retourne (html_str, error_str)."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace"), None
    except Exception as e:
        return "", str(e)


def _extract_tag(html: str, tag: str, attr: str = "", attr_val: str = "") -> str:
    """Extraction basique d'un tag HTML sans dépendance externe."""
    import re
    if attr and attr_val:
        pattern = rf'<{tag}[^>]*{attr}=["\']?{re.escape(attr_val)}["\']?[^>]*content=["\']([^"\']*)["\']'
        m = re.search(pattern, html, re.IGNORECASE)
        if not m:
            pattern = rf'<{tag}[^>]*content=["\']([^"\']*)["\'][^>]*{attr}=["\']?{re.escape(attr_val)}["\']?'
            m = re.search(pattern, html, re.IGNORECASE)
        return m.group(1).strip() if m else ""
    pattern = rf'<{tag}[^>]*>([^<]*)</{tag}>'
    m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else ""


def _count_pattern(html: str, pattern: str) -> int:
    import re
    return len(re.findall(pattern, html, re.IGNORECASE))


def _score_label(score: int) -> str:
    if score >= 80:
        return "🟢 BON"
    if score >= 50:
        return "🟡 MOYEN"
    return "🔴 CRITIQUE"


@mcp.tool()
def auditer_site_web(url: str, marche: str = "france") -> str:
    """
    Audit SEO & marketing complet d'un site web pour Webdesign & Co.
    Analyse : indexabilité, balises SEO, Open Graph, performance, mobile,
    contenu, CTA, réseaux sociaux, sécurité HTTPS.
    url    : URL complète ou domaine (ex: webdesignandco.org)
    marche : 'france' ou 'dubai' (adapte les recommandations)
    """
    import re

    marche = marche.lower()
    drapeau = MARCHES.get(marche, MARCHES["france"])["emoji_drapeau"]

    if not url.startswith("http"):
        url = "https://" + url

    html, error = _fetch_html(url)

    lignes = [
        f"🔍 AUDIT SITE WEB — Webdesign & Co {drapeau}",
        f"URL analysée : {url}",
        f"Date         : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "=" * 60,
        "",
    ]

    if error or not html:
        lignes += [
            "🔴 ACCÈS IMPOSSIBLE",
            f"   Erreur : {error or 'Contenu vide'}",
            "",
            "⚠️  DIAGNOSTIC : Le site bloque les crawlers automatiques.",
            "   → Cela signifie que Google ne peut probablement pas l'indexer non plus.",
            "   → Action urgente : vérifier Cloudflare / WAF et whitelister Googlebot.",
            "",
            "RECOMMANDATIONS BASÉES SUR LE DIAGNOSTIC D'ACCÈS :",
            "   1. Vérifier robots.txt (doit retourner HTTP 200, pas 403)",
            "   2. Whitelister Googlebot dans Cloudflare",
            "   3. Soumettre le sitemap.xml dans Google Search Console",
            "   4. Tester avec Google Search Console → Inspection d'URL",
        ]
        return "\n".join(lignes)

    # ── Extraction des signaux ──
    title = _extract_tag(html, "title")
    meta_desc = _extract_tag(html, "meta", "name", "description")
    meta_robots = _extract_tag(html, "meta", "name", "robots")
    canonical = ""
    m_can = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if m_can:
        canonical = m_can.group(1)

    og_title = _extract_tag(html, "meta", "property", "og:title")
    og_desc = _extract_tag(html, "meta", "property", "og:description")
    og_image = _extract_tag(html, "meta", "property", "og:image")
    og_type = _extract_tag(html, "meta", "property", "og:type")

    viewport = _extract_tag(html, "meta", "name", "viewport")
    https_ok = url.startswith("https://")

    h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
    h1_count = len(h1_matches)
    h1_text = re.sub(r'<[^>]+>', '', h1_matches[0]).strip() if h1_matches else ""
    h2_count = _count_pattern(html, r'<h2[^>]*>')
    img_total = _count_pattern(html, r'<img[^>]*>')
    img_no_alt = _count_pattern(html, r'<img(?![^>]*alt=["\'][^"\']+["\'])[^>]*>')
    script_count = _count_pattern(html, r'<script[^>]*src=')
    link_count = _count_pattern(html, r'<link[^>]*stylesheet')

    has_form = bool(re.search(r'<form', html, re.IGNORECASE))
    has_phone = bool(re.search(r'(\+\d{1,3}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?){3,5}', html))
    has_email = bool(re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', html))
    has_whatsapp = bool(re.search(r'wa\.me|whatsapp', html, re.IGNORECASE))
    has_linkedin = bool(re.search(r'linkedin\.com', html, re.IGNORECASE))
    has_instagram = bool(re.search(r'instagram\.com', html, re.IGNORECASE))
    has_tiktok = bool(re.search(r'tiktok\.com', html, re.IGNORECASE))
    has_cta_audit = bool(re.search(r'audit|gratuit|diagnostic|devis', html, re.IGNORECASE))

    word_count = len(re.sub(r'<[^>]+>', ' ', html).split())

    # ── Scoring ──
    score_seo = 0
    score_seo += 20 if title and 50 <= len(title) <= 65 else (10 if title else 0)
    score_seo += 20 if meta_desc and 120 <= len(meta_desc) <= 160 else (10 if meta_desc else 0)
    score_seo += 15 if h1_count == 1 else (5 if h1_count > 1 else 0)
    score_seo += 15 if canonical else 0
    score_seo += 15 if "noindex" not in meta_robots.lower() else 0
    score_seo += 15 if h2_count >= 2 else (8 if h2_count == 1 else 0)

    score_perf = 0
    score_perf += 30 if https_ok else 0
    score_perf += 30 if viewport else 0
    score_perf += 20 if script_count <= 5 else (10 if script_count <= 10 else 0)
    score_perf += 20 if img_no_alt == 0 else (10 if img_no_alt <= 3 else 0)

    score_conv = 0
    score_conv += 25 if has_form else 0
    score_conv += 20 if has_cta_audit else 0
    score_conv += 15 if has_phone else 0
    score_conv += 15 if has_email else 0
    score_conv += 15 if has_whatsapp else 0
    score_conv += 10 if word_count >= 500 else (5 if word_count >= 200 else 0)

    score_social = 0
    score_social += 25 if og_title else 0
    score_social += 25 if og_image else 0
    score_social += 15 if og_desc else 0
    score_social += 15 if has_linkedin else 0
    score_social += 10 if has_instagram else 0
    score_social += 10 if has_tiktok else 0

    score_global = (score_seo + score_perf + score_conv + score_social) // 4

    # ── Rapport ──
    lignes += [
        f"📊 SCORE GLOBAL : {score_global}/100 — {_score_label(score_global)}",
        "",
        f"   SEO           : {score_seo}/100 {_score_label(score_seo)}",
        f"   Performance   : {score_perf}/100 {_score_label(score_perf)}",
        f"   Conversion    : {score_conv}/100 {_score_label(score_conv)}",
        f"   Réseaux/OG    : {score_social}/100 {_score_label(score_social)}",
        "",
        "─" * 60,
        "🔎 DÉTAIL SEO",
        f"   Titre          : {'✅ ' + title[:55] + ('…' if len(title) > 55 else '') if title else '🔴 ABSENT'}",
        f"   Longueur titre : {'✅ ' + str(len(title)) + ' car.' if title and 50 <= len(title) <= 65 else '🟡 ' + str(len(title)) + ' car. (idéal: 50-65)' if title else '🔴 -'}",
        f"   Meta desc      : {'✅ OK' if meta_desc and 120 <= len(meta_desc) <= 160 else '🟡 ' + str(len(meta_desc)) + ' car. (idéal: 120-160)' if meta_desc else '🔴 ABSENTE'}",
        f"   H1             : {'✅ 1 H1 → ' + h1_text[:40] if h1_count == 1 else '🟡 ' + str(h1_count) + ' H1 (doit être unique)' if h1_count > 1 else '🔴 AUCUN H1'}",
        f"   H2             : {'✅ ' + str(h2_count) + ' H2' if h2_count >= 2 else '🟡 ' + str(h2_count) + ' H2 (min. 2 recommandé)'}",
        f"   Canonical      : {'✅ Présente' if canonical else '🟡 Absente'}",
        f"   Robots meta    : {'✅ ' + (meta_robots or 'index,follow') if 'noindex' not in meta_robots.lower() else '🔴 NOINDEX DÉTECTÉ'}",
        f"   Mots sur page  : {'✅ ' + str(word_count) if word_count >= 500 else '🟡 ' + str(word_count) + ' (min. 500 recommandé)'}",
        "",
        "─" * 60,
        "⚡ PERFORMANCE & MOBILE",
        f"   HTTPS          : {'✅ Activé' if https_ok else '🔴 NON SÉCURISÉ'}",
        f"   Balise viewport: {'✅ Mobile-ready' if viewport else '🔴 ABSENTE — site non mobile'}",
        f"   Scripts JS     : {'✅ ' + str(script_count) + ' scripts' if script_count <= 5 else '🟡 ' + str(script_count) + ' scripts (impact vitesse)'}",
        f"   Images sans alt: {'✅ Toutes renseignées' if img_no_alt == 0 else '🟡 ' + str(img_no_alt) + '/' + str(img_total) + ' images sans texte alt'}",
        "",
        "─" * 60,
        "🎯 CONVERSION & CTA",
        f"   Formulaire     : {'✅ Présent' if has_form else '🔴 ABSENT — aucun moyen de capturer des leads'}",
        f"   Offre audit    : {'✅ Mentionnée' if has_cta_audit else '🔴 ABSENTE — ajoutez un CTA audit gratuit'}",
        f"   Téléphone      : {'✅ Visible' if has_phone else '🟡 Non détecté'}",
        f"   Email          : {'✅ Visible' if has_email else '🟡 Non détecté'}",
        f"   WhatsApp       : {'✅ Intégré' if has_whatsapp else '🟡 Absent — fort potentiel PME'}",
        "",
        "─" * 60,
        "📱 OPEN GRAPH & RÉSEAUX SOCIAUX",
        f"   og:title       : {'✅ ' + og_title[:40] if og_title else '🔴 ABSENT — partages sans titre'}",
        f"   og:image       : {'✅ Présente' if og_image else '🔴 ABSENTE — partages sans visuel'}",
        f"   og:description : {'✅ Présente' if og_desc else '🟡 Absente'}",
        f"   LinkedIn       : {'✅ Lié' if has_linkedin else '🟡 Non détecté'}",
        f"   Instagram      : {'✅ Lié' if has_instagram else '🟡 Non détecté'}",
        f"   TikTok         : {'✅ Lié' if has_tiktok else '🟡 Non détecté'}",
        "",
        "=" * 60,
        "🚀 TOP 5 ACTIONS PRIORITAIRES — WEBDESIGN & CO",
    ]

    actions = []
    if not title or len(title) < 50:
        actions.append(f"① Réécrire le titre : « Agence Web & Design Premium | PME {marche.capitalize()} & Dubai | Webdesign & Co »")
    if not meta_desc:
        actions.append("② Ajouter une meta description (120-160 car.) avec mots-clés cibles et CTA")
    if not og_image:
        actions.append("③ Ajouter les balises Open Graph (og:image, og:title) pour des partages soignés")
    if not has_form:
        actions.append("④ Ajouter un formulaire de capture leads (audit gratuit) en homepage")
    if not has_whatsapp:
        actions.append("⑤ Intégrer un bouton WhatsApp flottant — conversion +35% sur mobile")
    if not has_tiktok:
        actions.append("⑥ Ajouter le lien TikTok pour fermer la boucle social → site")
    if score_seo < 60:
        actions.append("⑦ Audit SEO complet : structure H1/H2, contenu 800+ mots, balises schema.org")

    for i, a in enumerate(actions[:5], 1):
        if not a.startswith(f"⑤") and not a.startswith(f"⑥") and not a.startswith(f"⑦"):
            lignes.append(f"   {a}")
        else:
            lignes.append(f"   {a}")

    lignes += [
        "",
        "─" * 60,
        f"📋 RAPPORT GÉNÉRÉ PAR WEBDESIGN & CO {drapeau}",
        f"   Pour transformer ces recommandations en résultats :",
        f"   → webdesignandco.org | Audit complet offert",
    ]

    return "\n".join(lignes)


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

    @app.post("/webhook/audit-tiktok")
    async def webhook_audit_tiktok(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        return JSONResponse({
            "status": "success",
            "script": generer_script_audit_tiktok(
                marche=data.get("marche", "france"),
                angle=data.get("angle", "site_web"),
                duree=int(data.get("duree", 60)),
            ),
        })

    @app.get("/concurrence")
    async def get_concurrence(concurrent: str = "tous", marche: str = "france"):
        return JSONResponse({
            "status": "success",
            "analyse": analyser_concurrence(concurrent=concurrent, marche=marche),
        })

    @app.post("/webhook/campagne-semaine")
    async def webhook_campagne_semaine(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        return JSONResponse({
            "status": "success",
            "campagne": generer_campagne_semaine(
                marche=data.get("marche", "france"),
                semaine_debut=data.get("semaine_debut", ""),
                objectif=data.get("objectif", "leads"),
            ),
        })

    @app.post("/webhook/audit-site")
    async def webhook_audit_site(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        url = data.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="Le champ 'url' est requis.")
        return JSONResponse({
            "status": "success",
            "audit": auditer_site_web(
                url=url,
                marche=data.get("marche", "france"),
            ),
        })

    @app.get("/audit")
    async def get_audit(url: str, marche: str = "france"):
        if not url:
            raise HTTPException(status_code=400, detail="Paramètre 'url' requis.")
        return JSONResponse({
            "status": "success",
            "audit": auditer_site_web(url=url, marche=marche),
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
