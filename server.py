from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
import json
import os
import random
import sys
import urllib.request

MAKE_WEBHOOK_URL = os.environ.get(
    "MAKE_WEBHOOK_URL",
    "https://hook.eu1.make.com/5uob38x8gtk2tsgdsqvslh3tdjg58yw5"
)


def envoyer_vers_make(payload: dict) -> dict:
    """Envoie un payload JSON vers le webhook Make.com et retourne la réponse."""
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
    ton : 'professionnel', 'inspirant' ou 'humoristique'.
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
        "inspirant": [
            f"Et si {sujet} était la clé de votre croissance en {marche.capitalize()} ? ✨",
            f"Nous avons transformé des PME grâce à {sujet}. Voici leur histoire 👇",
            f"La réussite digitale commence par {sujet}. On vous explique tout. {drapeau}",
        ],
        "humoristique": [
            f"On ne va pas se mentir… {sujet}, c'est souvent le chaos 😅",
            f"Avant Webdesign & Co : galère. Après : chef d'œuvre 🎨 #{sujet.replace(' ', '')}",
            f"Si {sujet} était un plat, ce serait… un plat raté sans nous 🍽️😂",
        ],
    }

    hook = random.choice(hooks.get(ton, hooks["professionnel"]))
    hashtags = " ".join(HASHTAGS_BASE[reseau][marche][:5])

    if reseau == "tiktok":
        contenu = (
            f"🎬 SCRIPT TIKTOK — Webdesign & Co {drapeau}\n"
            f"{'='*50}\n\n"
            f"⏱️ DURÉE CONSEILLÉE : 30-45 secondes\n\n"
            f"🎯 ACCROCHE (0-3 sec) :\n« {hook} »\n\n"
            f"📖 DÉVELOPPEMENT (3-25 sec) :\n"
            f"Chez Webdesign & Co, on aide les PME {drapeau} à se démarquer grâce à {sujet}.\n"
            f"Résultat : plus de visibilité, plus de clients, plus de chiffre d'affaires.\n"
            f"On ne fait pas que du design — on crée votre image de marque.\n\n"
            f"💡 CONSEIL CLÉ (25-40 sec) :\n"
            f"Pour réussir avec {sujet}, voici ce qu'il faut absolument faire :\n"
            f"✅ Définir une identité visuelle forte\n"
            f"✅ Être cohérent sur tous vos canaux\n"
            f"✅ Mesurer vos résultats chaque semaine\n\n"
            f"🔚 CALL TO ACTION (40-45 sec) :\n"
            f"« Suivez-nous pour plus de conseils ! Lien en bio pour un audit gratuit. »\n\n"
            f"#️⃣ HASHTAGS :\n{hashtags} #WebdesignAndCo\n"
        )

    elif reseau == "linkedin":
        contenu = (
            f"💼 POST LINKEDIN — Webdesign & Co {drapeau}\n"
            f"{'='*50}\n\n"
            f"📌 ACCROCHE :\n{hook}\n\n"
            f"📝 CORPS DU POST :\n"
            f"En tant que dirigeant de PME en {marche.capitalize()}, vous savez que {sujet} est devenu incontournable.\n\n"
            f"Chez Webdesign & Co, nous accompagnons les entreprises francophones {drapeau} dans leur transformation digitale.\n\n"
            f"Voici ce que nous observons sur le terrain :\n\n"
            f"→ 78% des PME perdent des clients à cause d'un manque de présence en ligne\n"
            f"→ Un design professionnel augmente la confiance client de 60%\n"
            f"→ {sujet} est le levier n°1 de croissance digitale en 2025\n\n"
            f"Notre approche chez Webdesign & Co :\n"
            f"✦ Audit de votre présence digitale\n"
            f"✦ Stratégie sur mesure pour votre marché\n"
            f"✦ Création & déploiement de votre identité visuelle\n"
            f"✦ Suivi & optimisation en continu\n\n"
            f"🎯 Vous souhaitez développer votre activité grâce à {sujet} ?\n"
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
            f"Chez Webdesign & Co, on transforme votre vision en identité visuelle percutante.\n"
            f"Parce qu'un beau design, c'est bien — un design qui convertit, c'est mieux. 💪\n\n"
            f"Ce qu'on vous offre :\n"
            f"🎨 Design sur mesure\n"
            f"📱 Stratégie réseaux sociaux\n"
            f"🚀 Visibilité & croissance garanties\n\n"
            f"👇 Commentez 'AUDIT' pour recevoir votre diagnostic gratuit !\n\n"
            f"#️⃣ HASHTAGS :\n{hashtags} #WebdesignAndCo\n"
        )

    return contenu


@mcp.tool()
def planifier_calendrier(
    marche: str = "france",
    semaine_debut: str = ""
) -> str:
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
def suggerer_hashtags(
    sujet: str,
    reseau: str,
    marche: str = "france",
    nb_hashtags: int = 15
) -> str:
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
def generer_legende(
    sujet: str,
    reseau: str,
    marche: str = "france",
    objectif: str = "engagement"
) -> str:
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
            "linkedin": "🔔 Suivez Webdesign & Co pour ne manquer aucun conseil. Et vous, quelle est votre expérience sur ce sujet ?",
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


def run_webhook_server():
    """Serveur HTTP pour Make.com — lance avec : python server.py --webhook"""
    from fastapi import FastAPI, Request, HTTPException, Header
    from fastapi.responses import JSONResponse
    import uvicorn

    WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "webdesign-co-secret")

    app = FastAPI(
        title="Webdesign & Co — Webhook Make.com",
        description="API webhook pour publier automatiquement sur TikTok, LinkedIn et Instagram",
        version="1.0.0",
    )

    def verifier_secret(x_webhook_secret: str = Header(default="")):
        if x_webhook_secret != WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Secret invalide.")

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "Webdesign & Co Webhook"}

    @app.post("/webhook/generer-contenu")
    async def webhook_generer_contenu(request: Request):
        """
        Génère un post complet pour un réseau social.
        Body JSON : { "sujet": "...", "reseau": "tiktok|linkedin|instagram",
                      "marche": "france|dubai", "ton": "professionnel|inspirant|humoristique" }
        Header requis : X-Webhook-Secret
        """
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
        """
        Génère le contenu pour TikTok, LinkedIn et Instagram en une seule requête.
        Body JSON : { "sujet": "...", "marche": "france|dubai", "ton": "professionnel|inspirant|humoristique",
                      "image_url": "https://...", "date_publication": "2025-01-15T10:00:00" }
        Header requis : X-Webhook-Secret
        """
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        sujet = data.get("sujet", "")
        if not sujet:
            raise HTTPException(status_code=400, detail="Le champ 'sujet' est requis.")
        marche = data.get("marche", "france")
        ton = data.get("ton", "professionnel")
        image_url = data.get("image_url", "")
        date_publication = data.get("date_publication", "")
        return JSONResponse({
            "status": "success",
            "sujet": sujet,
            "marche": marche,
            "image_url": image_url,
            "date_publication": date_publication,
            "publications": {
                "tiktok": generer_contenu(sujet=sujet, reseau="tiktok", marche=marche, ton=ton),
                "linkedin": generer_contenu(sujet=sujet, reseau="linkedin", marche=marche, ton=ton),
                "instagram": generer_contenu(sujet=sujet, reseau="instagram", marche=marche, ton=ton),
            },
            "hashtags": {
                "tiktok": suggerer_hashtags(sujet=sujet, reseau="tiktok", marche=marche, nb_hashtags=8),
                "linkedin": suggerer_hashtags(sujet=sujet, reseau="linkedin", marche=marche, nb_hashtags=5),
                "instagram": suggerer_hashtags(sujet=sujet, reseau="instagram", marche=marche, nb_hashtags=15),
            },
        })

    @app.post("/webhook/analyser-tendances")
    async def webhook_analyser_tendances(request: Request):
        """
        Retourne les tendances virales pour un marché.
        Body JSON : { "marche": "france|dubai", "nb_tendances": 5 }
        Header requis : X-Webhook-Secret
        """
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
        """
        Génère un calendrier éditorial hebdomadaire.
        Body JSON : { "marche": "france|dubai", "semaine_debut": "JJ/MM/AAAA" }
        Header requis : X-Webhook-Secret
        """
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
        """
        Génère une légende prête à copier-coller.
        Body JSON : { "sujet": "...", "reseau": "tiktok|linkedin|instagram",
                      "marche": "france|dubai", "objectif": "engagement|vente|notoriete" }
        Header requis : X-Webhook-Secret
        """
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
        """
        Génère le contenu pour TikTok, LinkedIn et Instagram, puis l'envoie
        automatiquement vers le webhook Make.com configuré.
        Body JSON : { "sujet": "...", "marche": "france|dubai", "ton": "professionnel|inspirant|humoristique" }
        Header requis : X-Webhook-Secret
        """
        verifier_secret(request.headers.get("x-webhook-secret", ""))
        data = await request.json()
        sujet = data.get("sujet", "")
        if not sujet:
            raise HTTPException(status_code=400, detail="Le champ 'sujet' est requis.")
        marche = data.get("marche", "france")
        ton = data.get("ton", "professionnel")

        payload = {
            "sujet": sujet,
            "marche": marche,
            "publications": {
                "tiktok": generer_contenu(sujet=sujet, reseau="tiktok", marche=marche, ton=ton),
                "linkedin": generer_contenu(sujet=sujet, reseau="linkedin", marche=marche, ton=ton),
                "instagram": generer_contenu(sujet=sujet, reseau="instagram", marche=marche, ton=ton),
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
    print(f"🚀 Webhook Webdesign & Co démarré sur http://0.0.0.0:{port}")
    print(f"📖 Documentation : http://0.0.0.0:{port}/docs")
    print(f"🔐 Secret actif  : {WEBHOOK_SECRET}")
    print(f"📡 Make.com URL  : {MAKE_WEBHOOK_URL}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    if "--webhook" in sys.argv:
        run_webhook_server()
    else:
        mcp.run()
