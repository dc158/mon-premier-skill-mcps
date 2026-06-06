from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
import json
import os
import random
import sys
import urllib.request
import xml.etree.ElementTree as ET

def generer_image_url(sujet: str, reseau: str = "instagram") -> str:
    seed = (sujet.lower().replace("é","e").replace("è","e").replace("ê","e").replace("à","a").replace("â","a").replace("ô","o").replace("û","u").replace("ç","c").replace("'","").replace(" ","-").replace("&","and").replace("/","-"))[:40]
    dim = {"instagram":"1080/1080","tiktok":"1080/1920","linkedin":"1200/628"}.get(reseau,"1200/628")
    return f"https://picsum.photos/seed/{seed}/{dim}"

MAKE_WEBHOOK_URL = os.environ.get("MAKE_WEBHOOK_URL","https://hook.eu1.make.com/5uob38x8gtk2tsgdsqvslh3tdjg58yw5")
RENDER_URL = os.environ.get("RENDER_URL","https://mon-premier-skill-mcps.onrender.com")
LOG_FILE = "/tmp/publications_log.json"
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON","")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID","")
SHEETS_WORKSHEET = "Publications"

SUJETS_FRANCE_28 = [
    "identité visuelle pour PME françaises","création de logo professionnel","charte graphique et cohérence de marque",
    "personal branding pour dirigeants français","refonte de site web : avant / après","pourquoi votre site web ne convertit pas",
    "site web mobile-first en 2025","SEO local pour commerces français","Google My Business pour PME",
    "stratégie de contenu pour gagner en visibilité","LinkedIn B2B pour PME françaises","Instagram pour attirer des clients en France",
    "TikTok : levier de croissance pour les PME","publicité digitale avec petit budget","e-commerce pour boutiques françaises",
    "UX et expérience utilisateur qui convertit","témoignages clients : la preuve sociale qui vend","tunnel de vente pour PME",
    "automatisation marketing pour gagner du temps","IA et outils digitaux pour PME en 2025","email marketing : toujours rentable en 2025",
    "les erreurs fatales du webdesign en France","comment doubler son CA grâce au digital","success story : PME française transformée",
    "tendances design à adopter en 2025","présence digitale : checklist complète pour PME","investir dans son image : ROI du design pro",
    "bilan digital de l'année pour les PME françaises",
]

SUJETS_DUBAI_28 = [
    "luxury branding et prestige digital à Dubai","identité visuelle bilingue FR-EN pour Dubai","création de logo pour entreprises du Golfe",
    "personal branding pour entrepreneurs francophones","refonte de site web pour le marché émirati","site web premium pour la clientèle Dubai",
    "charte graphique adaptée au marché du Moyen-Orient","e-commerce au Moyen-Orient : opportunités 2025","Shopify vs solutions locales à Dubai",
    "stratégie digitale pour les expatriés francophones","LinkedIn pour les professionnels de Dubai","Instagram et TikTok pour les marques de Dubai",
    "marketing digital halal et inclusif","SEO pour entreprises francophones à Dubai","IA et startups tech à Dubai",
    "transformation digitale des PME émirati","automatisation et croissance pour entreprises Dubai","UX et design pour la clientèle premium du Golfe",
    "témoignages : entrepreneurs francophones à Dubai","tunnel de vente pour le marché Dubai","publicité digitale ciblée Moyen-Orient",
    "les erreurs à éviter pour réussir à Dubai","comment développer sa marque au Golfe","success story : entreprise francophone à Dubai",
    "tendances webdesign et digital à Dubai 2025","présence digitale : guide complet pour Dubai","ROI du design pro pour entreprises émirati",
    "bilan digital pour les francophones du Golfe",
]

SUJETS_USA_28 = [
    "visual identity for US startups","professional logo design for American businesses","brand guidelines and consistency",
    "personal branding for US founders","website redesign: before and after","why your website is not converting",
    "mobile-first web design in 2025","local SEO for US small businesses","Google Business Profile optimization",
    "content strategy for US market visibility","LinkedIn B2B for US companies","Instagram for US business growth",
    "TikTok: growth lever for small businesses","digital ads on a small budget","e-commerce for US boutiques",
    "UX design that converts","social proof and customer testimonials","sales funnel for small businesses",
    "AI marketing automation to save time","AI tools for US small businesses in 2025","email marketing: still profitable in 2025",
    "fatal web design mistakes in the US","how to double revenue through digital","success story: US business transformed",
    "design trends to adopt in 2025","digital presence: complete checklist for US SMBs","investing in professional design: ROI breakdown",
    "year-end digital review for US small businesses",
]

TONS_ROTATION = ["professionnel","educatif","inspirant","promotionnel","storytelling"]
def choisir_ton(): return TONS_ROTATION[datetime.now().timetuple().tm_yday % len(TONS_ROTATION)]

_publications_log: list = []

def _get_sheets_worksheet():
    if not GOOGLE_SERVICE_ACCOUNT_JSON or not GOOGLE_SHEET_ID: return None
    try:
        import gspread; from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_info(json.loads(GOOGLE_SERVICE_ACCOUNT_JSON),scopes=["https://www.googleapis.com/auth/spreadsheets"])
        gc = gspread.authorize(creds); sh = gc.open_by_key(GOOGLE_SHEET_ID)
        try: return sh.worksheet(SHEETS_WORKSHEET)
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title=SHEETS_WORKSHEET,rows=2000,cols=6)
            ws.append_row(["timestamp","sujet","marche","reseau","ton","source"]); return ws
    except Exception as e: print(f"[SHEETS] {e}"); return None

def charger_log():
    global _publications_log
    ws = _get_sheets_worksheet()
    if ws:
        try:
            rows = ws.get_all_records()
            _publications_log = [{"sujet":r.get("sujet",""),"marche":r.get("marche",""),"reseau":r.get("reseau",""),"ton":r.get("ton",""),"timestamp":r.get("timestamp","")} for r in rows if r.get("sujet")]
            print(f"[LOG] {len(_publications_log)} depuis Sheets"); return
        except Exception as e: print(f"[SHEETS] {e}")
    try:
        with open(LOG_FILE,"r",encoding="utf-8") as f: _publications_log = json.load(f)
    except: _publications_log = []

def enregistrer_publication(sujet,marche,reseau,ton="",source=""):
    entry={"sujet":sujet,"marche":marche,"reseau":reseau,"ton":ton,"source":source,"timestamp":datetime.now().isoformat()}
    _publications_log.append(entry)
    ws=_get_sheets_worksheet()
    if ws:
        try: ws.append_row([entry["timestamp"],sujet,marche,reseau,ton,source])
        except Exception as e: print(f"[SHEETS] {e}")
    try:
        with open(LOG_FILE,"w",encoding="utf-8") as f: json.dump(_publications_log[-500:],f,ensure_ascii=False)
    except: pass

def sujet_deja_publie_recemment(sujet,marche,jours=14):
    seuil=datetime.now()-timedelta(days=jours)
    for e in _publications_log:
        try: ts=datetime.fromisoformat(e["timestamp"])
        except: continue
        if e.get("sujet")==sujet and e.get("marche")==marche and ts>seuil: return True
    return False

# ─── VEILLE CONCURRENTIELLE v2.2 ─────────────────────────────────────────────
# 3 couches : tendances secteur + failles génériques + surveillance nominative
TENDANCES_VEILLE: dict = {"france":[],"dubai":[],"usa":[]}
FAILLES_VEILLE: dict = {"france":[],"dubai":[],"usa":[]}
CONCURRENTS_VEILLE: dict = {"france":[],"dubai":[],"usa":[]}  # NOUVEAU v2.2

RSS_QUERIES = {
    "france":"webdesign+agence+digitale+PME+identite+visuelle+branding",
    "dubai":"web+design+digital+agency+Dubai+francophone+branding",
    "usa":"web+design+agency+lead+generation+automation+AI+branding",
}
RSS_QUERIES_FAILLES = {
    "france":"agence+web+formulaire+contact+leads+perdus+relance+manuelle+CRM",
    "dubai":"digital+agency+Dubai+lead+response+contact+form+automation+CRM",
    "usa":"agency+contact+form+lost+leads+manual+follow+up+CRM+automation",
}
# NOUVEAU v2.2 — Requêtes nominatives par concurrent
RSS_CONCURRENTS_NOMMES = {
    "france":["Digidop+agence+web","Eskimoz+SEO+referencement","Junto+agence+digitale","Plezi+marketing+automation","Nile+agence+web+France"],
    "dubai":["Nexa+digital+agency+Dubai","Blue+Beetle+web+Dubai","Chain+Reaction+digital+Dubai","Digital+Gravity+agency+UAE","agence+digitale+Dubai+francophone+2025"],
    "usa":["NoGood+digital+agency","Single+Grain+marketing+agency","Ignite+Visibility+SEO","WebFX+digital+marketing","Thrive+Internet+Marketing"],
}

CONCURRENTS_CIBLES = {
    "france":["Digidop","Eskimoz","Junto","Plezi","Nile"],
    "dubai":["Nexa","Blue Beetle","Chain Reaction","Digital Gravity"],
    "usa":["NoGood","Single Grain","Ignite Visibility","WebFX","Thrive"],
}

MOTS_CLES_SECTEUR = [
    "webdesign","web design","agence web","agence digitale","site web","creation site","refonte site",
    "identite visuelle","logo","charte graphique","branding","pme","entrepreneur","startup",
    "seo","referencement","google","marketing digital","reseaux sociaux","community manager",
    "e-commerce","boutique en ligne","shopify","ux","experience utilisateur","conversion",
    "dubai","emirats","golfe","moyen-orient","digital","numerique","transformation digitale",
    "lead","formulaire","contact form","crm","automation","whatsapp","sms","relance","follow-up",
    "pipeline","make.com","zapier","n8n","webhook","workflow","intelligence artificielle","ia","ai",
    "chatgpt","taux de conversion","leads perdus","qualification","reponse automatique","bot","sequence email",
    "digidop","eskimoz","junto","plezi","nile","nexa","blue beetle","chain reaction","digital gravity",
    "nogood","single grain","ignite visibility","webfx","thrive",
]

FAILLES_CONCURRENTS_BASE = [
    {"faille":"formulaire_statique","description":"Formulaire de contact statique sans automation CRM","stat_choc":"73% des leads ne reçoivent pas de réponse dans les 5 premières minutes — passé ce délai, la conversion chute de 21x.","solution_make":"Formulaire → Make.com → WhatsApp/SMS < 90 sec + relances J+1/J+3/J+7 automatiques","cta_keyword":"BLUEPRINT","marches":["france","dubai","usa"]},
    {"faille":"relance_manuelle","description":"Relances prospects 100% manuelles sans séquence automatisée","stat_choc":"92% des agences relancent leurs prospects à la main. Résultat : 67% des leads chauds oubliés après 48h.","solution_make":"CRM → Make.com → Séquence WhatsApp/Email/SMS multi-canal + scoring IA automatique","cta_keyword":"WORKFLOW","marches":["france","dubai","usa"]},
    {"faille":"audit_manuel","description":"Audit client réalisé manuellement, sans outil d'analyse automatisé","stat_choc":"Les agences traditionnelles passent 4h en moyenne sur un audit client. Nous : 12 minutes grâce à l'IA.","solution_make":"URL client → Make.com + Claude AI → Rapport d'audit complet + Loom personnalisé auto-envoyé","cta_keyword":"AUDIT","marches":["france","dubai","usa"]},
    {"faille":"reporting_manuel","description":"Reporting mensuel client préparé manuellement sous Excel/PDF","stat_choc":"8h/mois de reporting manuel par client. Nos concurrents le font encore à la main en 2025.","solution_make":"Google Analytics + Semrush → Make.com → Rapport PDF auto-généré + envoi client automatique","cta_keyword":"REPORTING","marches":["france","dubai","usa"]},
]

def _scraper_rss(url, max_items=20, strict=True):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=15) as resp: xml_data=resp.read()
        root=ET.fromstring(xml_data); channel=root.find("channel")
        if channel is None: return []
        titres=[]
        for item in channel.findall("item")[:max_items]:
            el=item.find("title")
            if el is not None and el.text: titres.append(el.text.strip())
        result=[]
        for t in titres:
            if not strict or any(kw in t.lower() for kw in MOTS_CLES_SECTEUR):
                s=t.split(" - ")[0].strip()
                if 15<=len(s)<=140: result.append(s)
        return result
    except Exception as e: print(f"[RSS] {e}"); return []

def scraper_tendances_rss(marche="france"):
    q=RSS_QUERIES.get(marche,RSS_QUERIES["france"])
    lang="fr" if marche in["france","dubai"] else "en"
    gl="FR" if marche=="france" else("AE" if marche=="dubai" else "US")
    r=_scraper_rss(f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={gl}&ceid={gl}:{lang}",20,True)
    print(f"[VEILLE TENDANCES] {marche.upper()} — {len(r)} pertinents"); return r

def scraper_failles_rss(marche="france"):
    q=RSS_QUERIES_FAILLES.get(marche,RSS_QUERIES_FAILLES["france"])
    lang="fr" if marche in["france","dubai"] else "en"
    gl="FR" if marche=="france" else("AE" if marche=="dubai" else "US")
    r=_scraper_rss(f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={gl}&ceid={gl}:{lang}",15,False)
    print(f"[VEILLE FAILLES] {marche.upper()} — {len(r)} signaux"); return r

def scraper_concurrents_nommes(marche="france"):
    """NOUVEAU v2.2 — Surveillance nominative Google News par nom de concurrent."""
    queries=RSS_CONCURRENTS_NOMMES.get(marche,[])
    lang="fr" if marche in["france","dubai"] else "en"
    gl="FR" if marche=="france" else("AE" if marche=="dubai" else "US")
    signaux=[]
    for q in queries:
        try:
            req=urllib.request.Request(f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={gl}&ceid={gl}:{lang}",headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=12) as resp: xml_data=resp.read()
            root=ET.fromstring(xml_data); channel=root.find("channel")
            if channel is None: continue
            for item in channel.findall("item")[:3]:
                el=item.find("title"); pd=item.find("pubDate")
                if el is not None and el.text:
                    t=el.text.strip().split(" - ")[0].strip()
                    if 15<=len(t)<=140:
                        signaux.append({"concurrent":q.split("+")[0],"titre":t,"date":pd.text[:16] if pd is not None and pd.text else ""})
        except Exception as e: print(f"[CONCURRENTS] {q[:25]} : {e}")
    print(f"[VEILLE CONCURRENTS NOMMES] {marche.upper()} — {len(signaux)} signaux"); return signaux

def scraper_tiktok_concurrent(query, max_results=5):
    apify_token=os.environ.get("APIFY_TOKEN")
    if not apify_token: return []
    try:
        from apify_client import ApifyClient; client=ApifyClient(apify_token)
        run=client.actor("clockworks/tiktok-scraper").call(run_input={"searchQueries":[query],"resultsPerPage":max_results},timeout_secs=90)
        posts=[]
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            l=item.get("diggCount",0); c=item.get("commentCount",0); s=item.get("shareCount",0)
            posts.append({"auteur":item.get("author",{}).get("nickname","?"),"texte":item.get("desc","")[:200],"url":item.get("webVideoUrl",""),"engagement":l+(c*2)+(s*3),"metrics":{"likes":l,"comments":c,"shares":s}})
        posts.sort(key=lambda x:x["engagement"],reverse=True); return posts
    except Exception as e: print(f"[APIFY] {e}"); return []

def rafraichir_veille():
    """3 couches : tendances secteur + failles génériques + surveillance nominative concurrents."""
    for m in ["france","dubai","usa"]:
        TENDANCES_VEILLE[m]=scraper_tendances_rss(m)
        FAILLES_VEILLE[m]=scraper_failles_rss(m)
        CONCURRENTS_VEILLE[m]=scraper_concurrents_nommes(m)  # NOUVEAU v2.2
    print(f"[VEILLE] OK — FR:{len(TENDANCES_VEILLE['france'])}t/{len(CONCURRENTS_VEILLE['france'])}c | AE:{len(TENDANCES_VEILLE['dubai'])}t/{len(CONCURRENTS_VEILLE['dubai'])}c | US:{len(TENDANCES_VEILLE['usa'])}t/{len(CONCURRENTS_VEILLE['usa'])}c")

def choisir_sujet(marche):
    sujets_map={"france":SUJETS_FRANCE_28,"dubai":SUJETS_DUBAI_28,"usa":SUJETS_USA_28}
    sujets_28=sujets_map.get(marche,SUJETS_FRANCE_28)
    for t in TENDANCES_VEILLE.get(marche,[]):
        if not sujet_deja_publie_recemment(t,marche): return t,"veille_rss"
    jour=datetime.now().timetuple().tm_yday
    for i in range(len(sujets_28)):
        s=sujets_28[(jour+i)%len(sujets_28)]
        if not sujet_deja_publie_recemment(s,marche): return s,"rotation_mensuelle"
    return sujets_28[jour%len(sujets_28)],"rotation_forcee"

def envoyer_vers_make(payload):
    data=json.dumps(payload).encode("utf-8")
    req=urllib.request.Request(MAKE_WEBHOOK_URL,data=data,headers={"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=10) as resp:
            return {"status":"envoyé","make_response":resp.read().decode("utf-8"),"http_code":resp.status}
    except Exception as e: return {"status":"erreur","detail":str(e)}

def self_ping():
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{RENDER_URL}/health",headers={"User-Agent":"self-ping/1.0"},method="GET"),timeout=10) as resp:
            print(f"[PING] OK HTTP {resp.status}")
    except Exception as e: print(f"[PING] {e}")

mcp = FastMCP("webdesign-co-community-manager")

MARCHES = {
    "france":{"timezone":"Europe/Paris","langue":"français","emoji_drapeau":"🇫🇷","horaires":{"tiktok":["07h00","12h00","19h00","21h00"],"linkedin":["08h05","12h35","17h35"],"instagram":["08h10","13h05","18h05","21h05"]}},
    "dubai":{"timezone":"Asia/Dubai","langue":"français","emoji_drapeau":"🇦🇪","horaires":{"tiktok":["08h10","13h10","20h10","22h10"],"linkedin":["09h15","13h15","18h10"],"instagram":["09h20","13h20","19h10","21h40"]}},
    "usa":{"timezone":"America/New_York","langue":"anglais","emoji_drapeau":"🇺🇸","horaires":{"tiktok":["08h00","12h00","19h00","21h00"],"linkedin":["08h00","12h00","17h00"],"instagram":["08h00","13h00","18h00","21h00"]}},
}

TENDANCES_BASE = {
    "france":[{"sujet":"IA & automatisation pour PME","score":97,"hashtag_cle":"#PMEFrance"},{"sujet":"Identité visuelle minimaliste","score":94,"hashtag_cle":"#WebDesign"},{"sujet":"Site web mobile-first en 2025","score":91,"hashtag_cle":"#MobileFrance"},{"sujet":"Personal branding pour dirigeants","score":89,"hashtag_cle":"#PersonalBranding"},{"sujet":"SEO local pour commerces français","score":86,"hashtag_cle":"#SEOLocal"},{"sujet":"UX / expérience utilisateur & conversions","score":85,"hashtag_cle":"#UXDesign"},{"sujet":"Réseaux sociaux B2B en France","score":82,"hashtag_cle":"#MarketingFrance"}],
    "dubai":[{"sujet":"Luxury branding & prestige digital","score":98,"hashtag_cle":"#DubaiLuxury"},{"sujet":"E-commerce & boutiques en ligne au Moyen-Orient","score":95,"hashtag_cle":"#EcommerceDubai"},{"sujet":"IA & startups tech à Dubai","score":93,"hashtag_cle":"#DubaiTech"},{"sujet":"Personal branding pour entrepreneurs francophones","score":90,"hashtag_cle":"#FrancophonesDubai"},{"sujet":"Identité visuelle bilingue FR/EN","score":87,"hashtag_cle":"#DesignDubai"},{"sujet":"Marketing digital halal & inclusif","score":84,"hashtag_cle":"#HalalMarketing"},{"sujet":"Réseaux sociaux pour les expatriés francophones","score":81,"hashtag_cle":"#ExpatsFrancophones"}],
    "usa":[{"sujet":"AI automation for US small businesses","score":98,"hashtag_cle":"#AIAutomation"},{"sujet":"Lead generation with Make.com workflows","score":95,"hashtag_cle":"#LeadGen"},{"sujet":"Luxury branding for US market","score":92,"hashtag_cle":"#USBranding"},{"sujet":"Personal branding for US founders","score":89,"hashtag_cle":"#PersonalBranding"},{"sujet":"Mobile-first web design 2025","score":86,"hashtag_cle":"#WebDesignUSA"},{"sujet":"WhatsApp & SMS lead automation","score":84,"hashtag_cle":"#SalesAutomation"},{"sujet":"B2B LinkedIn strategy for US agencies","score":81,"hashtag_cle":"#LinkedInUSA"}],
}

HASHTAGS_BASE = {
    "tiktok":{"france":["#WebDesignFrance","#PMEFrance","#ConseilMarketing","#TipsDigital","#EntrepreneurFrancais","#DesignFR","#AgenceWeb","#MarketingDigital","#CommunityManager","#TiktokBusiness"],"dubai":["#WebDesignDubai","#FrancophonesDubai","#EntrepreneurDubai","#DigitalDubai","#PMEDubai","#DesignDubai","#AgenceWebDubai","#DubaiMarketing","#FrancaisDubai","#DubaiTech"],"usa":["#WebDesignUSA","#AIAutomation","#LeadGenTips","#MakeComWorkflow","#DigitalAgencyUSA","#SmallBusinessTips","#SalesAutomation","#GrowthHacks","#MarketingUSA","#AgencyLife"]},
    "linkedin":{"france":["#WebDesign","#MarketingDigital","#PME","#TransformationDigitale","#Entrepreneuriat","#BrandingFrance","#CommunicationDigitale","#AgenceWeb","#SEO","#UXDesign"],"dubai":["#DubaiBusiness","#WebDesignDubai","#MarketingDubai","#EntrepreneurDubai","#FrancophonesDubai","#LuxuryBranding","#StartupDubai","#DigitalMarketing","#UAEBusiness","#BrandingDubai"],"usa":["#AIAutomation","#LeadGeneration","#WebDesignUSA","#B2BMarketing","#SalesAutomation","#MakeComWorkflow","#DigitalTransformation","#GrowthMarketing","#AgencyLife","#StartupUSA"]},
    "instagram":{"france":["#WebDesignFrance","#AgenceWebParis","#DesignGraphique","#PMEFrance","#MarketingDigital","#BrandingFR","#CommunityManager","#ContentCreator","#EntrepreneurFrancais","#Graphisme","#IdentiteVisuelle","#LogoDesign"],"dubai":["#DubaiDesign","#WebDesignDubai","#DubaiMarketing","#FrancaisDubai","#LuxuryDesign","#DesignDubai","#DubaiEntrepreneur","#UAEDesign","#FrancophonesDubai","#DubaiAgency","#BrandingDubai","#DubaiLuxury"],"usa":["#WebDesignUSA","#DigitalAgency","#LeadGeneration","#AIAutomation","#SmallBusiness","#StartupUSA","#MarketingAutomation","#SalesAutomation","#MakeComWorkflow","#GrowthHacking","#B2BMarketing","#AgencyLife"]},
}

JOURS_SEMAINE = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]

@mcp.tool()
def analyser_tendances(marche: str = "france", nb_tendances: int = 5) -> str:
    marche=marche.lower()
    if marche not in MARCHES: return json.dumps({"erreur":"Marché inconnu."},ensure_ascii=False)
    nb=max(1,min(nb_tendances,7)); t=TENDANCES_BASE[marche][:nb]; d=MARCHES[marche]["emoji_drapeau"]
    lignes=[f"📊 TENDANCES VIRALES — Webdesign & Co {d} {marche.upper()}\n"]
    for i,td in enumerate(t,1):
        b="█"*(td["score"]//10)+"░"*(10-td["score"]//10)
        lignes.append(f"#{i} {td['sujet']}\n   Score viral : {b} {td['score']}/100\n   Hashtag clé : {td['hashtag_cle']}\n")
    lignes.append("💡 Surfez sur la tendance #1 cette semaine."); return "\n".join(lignes)

@mcp.tool()
def surveiller_concurrence(marche: str = "france", inclure_tiktok: bool = False, mot_cle_tiktok: str = "") -> str:
    """Surveillance concurrentielle v2.2 : failles statiques + RSS failles + surveillance nominative + TikTok."""
    marche=marche.lower()
    if marche not in MARCHES: return json.dumps({"erreur":"Marché inconnu."},ensure_ascii=False)
    d=MARCHES[marche]["emoji_drapeau"]; c=CONCURRENTS_CIBLES.get(marche,[])
    lignes=[f"🔍 SURVEILLANCE CONCURRENTIELLE v2.2 — {d} {marche.upper()}",f"Concurrents surveillés : {', '.join(c)}","="*65,"","⚠️  FAILLES DÉTECTÉES :"]
    for i,f in enumerate([f for f in FAILLES_CONCURRENTS_BASE if marche in f["marches"]],1):
        lignes+=[f"  #{i} [{f['faille'].upper()}]",f"     Stat choc : {f['stat_choc']}",f"     Notre fix : {f['solution_make']}",f"     CTA : « {f['cta_keyword']} »",""]
    fr=FAILLES_VEILLE.get(marche,[])
    if fr: lignes+=["📡 SIGNAUX RSS FAILLES :",*[f"  • {t}" for t in fr[:5]],""]
    sc=CONCURRENTS_VEILLE.get(marche,[])
    if sc:
        lignes.append("🎯 SIGNAUX NOMINATIFS CONCURRENTS (v2.2) :")
        for s in sc[:8]: lignes.append(f"  [{s['concurrent']}] {s['titre']}"+(f" ({s['date']})" if s["date"] else ""))
        lignes+=["","💡 Counter-attaque → generer_post_concurrent()",""]
    else: lignes.append("🎯 Veille nominative : rafraîchissement à 06h00 UTC\n")
    if inclure_tiktok:
        q=mot_cle_tiktok or("agence web formulaire automatisation" if marche=="france" else("digital agency lead automation" if marche=="usa" else "digital agency Dubai automation"))
        posts=scraper_tiktok_concurrent(q,max_results=3)
        if posts:
            lignes+=[f"🎬 TIKTOK VIRAL '{q}' :"]
            for p in posts: lignes.append(f"  @{p['auteur']} | {p['metrics']['likes']}❤️ | {p['texte'][:80]}…")
            lignes.append("")
        else: lignes.append("🎬 TikTok : APIFY_TOKEN manquant\n")
    lignes+=["="*65,"💡 generer_post_concurrent() → post haute-conversion."]
    return "\n".join(lignes)

@mcp.tool()
def generer_post_concurrent(faille: str, marche: str = "france", reseau: str = "linkedin") -> str:
    marche=marche.lower(); reseau=reseau.lower()
    if marche not in MARCHES: return json.dumps({"erreur":"Marché inconnu."},ensure_ascii=False)
    d=MARCHES[marche]["emoji_drapeau"]
    fd=next((f for f in FAILLES_CONCURRENTS_BASE if f["faille"]==faille and marche in f["marches"]),None)
    T={
        "formulaire_statique":{"linkedin":"{stat_choc}\n\nLa plupart des agences à {marche_label} ont un formulaire de contact.\nAucune n'a construit le moteur d'automation derrière.\n\n→ Soumission formulaire\n→ Make.com capte le lead en temps réel\n→ WhatsApp + SMS en < 90 secondes\n→ Relance automatique J+1 / J+3 / J+7\n→ Lead scoré par IA\n\n+340% de leads contactés dans la fenêtre critique.\n\nCommentez « {cta_keyword} » pour le blueprint complet.\n\n#AIAutomation #LeadGeneration #WebdesignAndCo","instagram":"{stat_choc}\n\nVotre formulaire coûte des clients. Le fix :\n\n✅ Make.com capte chaque lead\n✅ WhatsApp/SMS < 90 secondes\n✅ Relances auto multi-canal\n✅ Zéro intervention manuelle\n\n👇 Commentez « {cta_keyword} »\n\n#AIAutomation #LeadGeneration #WebdesignAndCo","tiktok":"ACCROCHE : « {stat_choc} »\n\nVotre formulaire fait perdre des clients. Make.com répond en 90 sec.\n\nCommentez {cta_keyword} !\n\n#AIAutomation #LeadGeneration #WebdesignAndCo"},
        "relance_manuelle":{"linkedin":"{stat_choc}\n\nEn 2025, relancer à la main = travail de stagiaire.\n\n→ CRM mis à jour auto\n→ Email J+0\n→ WhatsApp J+1\n→ SMS J+3\n→ Email J+7\n→ IA adapte le message\n\n67% de leads récupérés.\n\nCommentez « {cta_keyword} »\n\n#SalesAutomation #MakeComWorkflow #WebdesignAndCo","instagram":"{stat_choc}\n\n✅ J+0 : Email IA\n✅ J+1 : WhatsApp\n✅ J+3 : SMS\n✅ J+7 : Email final\n✅ 0 action manuelle\n\n👇 Commentez « {cta_keyword} »\n\n#SalesAutomation #MakeComWorkflow #WebdesignAndCo","tiktok":"ACCROCHE : « {stat_choc} »\n\nSéquence auto : email J+0, WhatsApp J+1, SMS J+3, IA J+7.\n\nCommentez {cta_keyword} !\n\n#SalesAutomation #MakeComWorkflow #WebdesignAndCo"},
        "audit_manuel":{"linkedin":"{stat_choc}\n\nNotre audit automatisé :\n→ URL → Make.com + Semrush + PageSpeed\n→ Claude AI compile le rapport\n→ Loom personnalisé généré\n→ Email + WhatsApp envoyés\n\n12 minutes. Taux de closing : 68%.\n\nCommentez « {cta_keyword} »\n\n#AIAutomation #SalesProcess #WebdesignAndCo","instagram":"{stat_choc}\n\n✅ Analyse SEO auto\n✅ Rapport IA rédigé\n✅ Loom généré\n✅ WhatsApp automatique\n\n👇 Commentez « {cta_keyword} »\n\n#AIAutomation #SalesProcess #WebdesignAndCo","tiktok":"ACCROCHE : « {stat_choc} »\n\n12 min vs 4h. Make.com + IA. Analyse, rapport, Loom, WhatsApp.\n\nCommentez {cta_keyword} !\n\n#AIAutomation #AgencyLife #WebdesignAndCo"},
        "reporting_manuel":{"linkedin":"{stat_choc}\n\nNotre reporting auto :\n→ GA4 + Search Console → Make.com\n→ Semrush → KPIs agrégés\n→ Claude AI → commentaire exécutif\n→ PDF branded auto-généré\n→ Email + WhatsApp le 1er du mois\n\n0 minute. +41% satisfaction client.\n\nCommentez « {cta_keyword} »\n\n#AgencyAutomation #ClientReporting #WebdesignAndCo","instagram":"{stat_choc}\n\n✅ GA4 + Semrush → Make.com\n✅ Rapport IA\n✅ PDF branded auto\n✅ Envoi client auto\n✅ 0 minute de travail\n\n👇 Commentez « {cta_keyword} »\n\n#AgencyAutomation #ClientReporting #WebdesignAndCo","tiktok":"ACCROCHE : « {stat_choc} »\n\nRapport auto chaque mois — GA4, Semrush, IA, PDF, WhatsApp. Zéro Excel.\n\nCommentez {cta_keyword} !\n\n#AgencyAutomation #AgencyLife #WebdesignAndCo"},
    }
    if fd: stat_choc=fd["stat_choc"]; cta_keyword=fd["cta_keyword"]; solution_make=fd["solution_make"]
    else: stat_choc=f"Les agences à {marche.capitalize()} perdent des leads qualifiés faute d'automation."; cta_keyword="BLUEPRINT"; solution_make="Make.com + IA → automatisation complète"
    ml={"france":"France","dubai":"Dubai","usa":"USA"}.get(marche,marche.capitalize())
    tp=T.get(faille,T["formulaire_statique"]); tmpl=tp.get(reseau,tp["linkedin"])
    texte=tmpl.format(stat_choc=stat_choc,marche_label=ml,cta_keyword=cta_keyword,solution_make=solution_make,drapeau=d)
    hp=HASHTAGS_BASE.get(reseau,HASHTAGS_BASE["linkedin"]).get(marche,[])
    ht=" ".join(hp[:3 if reseau=="linkedin" else(5 if reseau=="tiktok" else 8)])
    return json.dumps({"type":"post_concurrent","faille":faille,"marche":marche,"reseau":reseau,"drapeau":d,"cta_keyword":cta_keyword,"texte_post":texte,"hashtags":ht,"image_url":generer_image_url(faille.replace("_"," "),reseau),"timestamp":datetime.now().isoformat(),"webhook_ready":True},ensure_ascii=False,indent=2)

@mcp.tool()
def generer_contenu(sujet: str, reseau: str, marche: str = "france", ton: str = "professionnel") -> str:
    reseau=reseau.lower(); marche=marche.lower()
    if reseau not in ["tiktok","linkedin","instagram"]: return json.dumps({"erreur":"Réseau inconnu."},ensure_ascii=False)
    if marche not in MARCHES: return json.dumps({"erreur":"Marché inconnu."},ensure_ascii=False)
    d=MARCHES[marche]["emoji_drapeau"]
    hooks={"professionnel":[f"Votre entreprise mérite le meilleur design. Voici pourquoi ▼",f"Ce que personne ne vous dit sur {sujet} en {marche.capitalize()}.",f"3 erreurs fatales à éviter sur {sujet} pour les PME {d}"],"educatif":[f"📚 Saviez-vous que {sujet} peut transformer votre business ? ▼",f"Leçon du jour : tout ce que vous devez savoir sur {sujet}.",f"Guide complet : {sujet} pour les PME {d} — 3 points essentiels"],"inspirant":[f"Et si {sujet} était la clé de votre croissance ? ✨",f"Nous avons transformé des PME grâce à {sujet}. Voici leur histoire 👇",f"La réussite digitale commence par {sujet}. {d}"],"promotionnel":[f"🎯 Offre exclusive Webdesign & Co sur {sujet}. Places limitées !",f"💥 Audit GRATUIT de votre {sujet} pour les PME {d}",f"Transformez votre image avec {sujet} — Diagnostic offert cette semaine !"],"storytelling":[f"Il y a 6 mois, cette PME {d} galérait avec {sujet}. Aujourd'hui, elle cartonne. 👇",f"On a tout misé sur {sujet} pour un client en {marche.capitalize()}. Voici ce qui s'est passé…",f"De 0 à 10K abonnés grâce à {sujet} — l'histoire vraie d'une PME {d}"]}
    hook=random.choice(hooks.get(ton,hooks["professionnel"]))
    ht=" ".join(HASHTAGS_BASE[reseau][marche][:5])
    corps={"educatif":f"📖 POURQUOI C'EST IMPORTANT :\n{sujet} est l'un des leviers les plus puissants pour les PME {d} en 2025.\n\n🔍 CE QUE VOUS DEVEZ SAVOIR :\n✅ 78% des PME sans stratégie digitale perdent des clients en ligne\n✅ Un design professionnel augmente la confiance de 60%\n✅ {sujet} = visibilité + crédibilité + croissance\n\n","promotionnel":f"🚀 NOTRE OFFRE DU MOMENT :\nWebdesign & Co accompagne les PME {d} sur {sujet}.\n\n✨ CE QUE VOUS OBTENEZ :\n🎁 Audit gratuit\n🎁 Stratégie personnalisée\n🎁 Accompagnement A à Z\n\n⏰ Offre valable cette semaine seulement !\n\n","storytelling":f"📖 L'HISTOIRE :\nUn client en {marche.capitalize()} {d} : personne ne connaissait son entreprise, malgré 10 ans d'expérience.\n\n🔧 NOTRE INTERVENTION :\nNous avons repensé toute sa présence digitale en 6 semaines.\n\n📈 LE RÉSULTAT :\n✅ +300% de visibilité en ligne\n✅ 3 nouveaux clients en 30 jours\n✅ Une image de marque qui inspire confiance\n\n"}.get(ton,f"Chez Webdesign & Co, nous accompagnons les PME {d} dans leur transformation digitale.\n\nNotre approche sur {sujet} :\n❆ Audit de votre présence digitale\n❆ Stratégie sur mesure\n❆ Création & déploiement\n❆ Suivi & optimisation\n\n")
    if reseau=="tiktok": return f"🎬 SCRIPT TIKTOK — Webdesign & Co {d}\n{'='*50}\n\n⏱️ DURÉE CONSEILLÉE : 30-45 secondes\n\n🎯 ACCROCHE (0-3 sec) :\n« {hook} »\n\n📖 DÉVELOPPEMENT (3-35 sec) :\n{corps}🔚 CALL TO ACTION (35-45 sec) :\n« Suivez-nous ! Lien en bio pour un audit gratuit. »\n\n#️⃣ HASHTAGS :\n{ht} #WebdesignAndCo\n"
    elif reseau=="linkedin": return f"💼 POST LINKEDIN — Webdesign & Co {d}\n{'='*50}\n\n📌 ACCROCHE :\n{hook}\n\n📝 CORPS DU POST :\nEn tant que dirigeant de PME en {marche.capitalize()}, {sujet} est devenu incontournable.\n\n{corps}🎯 Prêt à passer à l'étape suivante ?\nContactez-nous pour un audit offert → lien en commentaire.\n\n♻️ Partagez si cela peut aider votre réseau !\n\n#️⃣ HASHTAGS :\n{ht} #WebdesignAndCo\n"
    else: return f"📸 POST INSTAGRAM — Webdesign & Co {d}\n{'='*50}\n\n🖼️ VISUEL CONSEILLÉ : Mockup design / Avant-Après / Chiffres clés\n\n✍️ LÉGENDE :\n{hook}\n\n✨ {sujet} : le secret des PME qui cartonnent en {marche.capitalize()} {d}\n\n{corps}👇 Commentez AUDIT pour votre diagnostic gratuit !\n\n#️⃣ HASHTAGS :\n{ht} #WebdesignAndCo\n"

@mcp.tool()
def planifier_calendrier(marche: str = "france", semaine_debut: str = "") -> str:
    marche=marche.lower()
    if marche not in MARCHES: return json.dumps({"erreur":"Marché inconnu."},ensure_ascii=False)
    if semaine_debut:
        try: debut=datetime.strptime(semaine_debut,"%d/%m/%Y")
        except: return json.dumps({"erreur":"Format invalide. Utilisez JJ/MM/AAAA."},ensure_ascii=False)
    else:
        ah=datetime.now(); jlm=(7-ah.weekday())%7 or 7; debut=ah+timedelta(days=jlm)
    d=MARCHES[marche]["emoji_drapeau"]; h=MARCHES[marche]["horaires"]
    planning={0:[("linkedin",h["linkedin"][0],"Conseil expert / Insight marché"),("instagram",h["instagram"][2],"Inspiration / Moodboard design")],1:[("tiktok",h["tiktok"][1],"Tuto rapide / Tip du jour"),("instagram",h["instagram"][0],"Témoignage client / Avant-Après")],2:[("linkedin",h["linkedin"][1],"Étude de cas / Résultats clients"),("tiktok",h["tiktok"][2],"Tendance virale / POV agence web")],3:[("instagram",h["instagram"][1],"Coulisses de l'agence / BTS"),("linkedin",h["linkedin"][2],"Question / Sondage engagement")],4:[("tiktok",h["tiktok"][0],"Top 3 conseils de la semaine"),("instagram",h["instagram"][3],"Post récapitulatif / Best of")],5:[("instagram",h["instagram"][2],"Contenu inspirant / Citation"),("tiktok",h["tiktok"][3],"Récap tendances / À venir")],6:[("linkedin",h["linkedin"][0],"Réflexion du dimanche / Vision 2025")]}
    ic={"tiktok":"🎬","linkedin":"💼","instagram":"📸"}
    lignes=[f"📅 CALENDRIER ÉDITORIAL — Webdesign & Co {d} {marche.upper()}",f"Semaine du {debut.strftime('%d/%m/%Y')} au {(debut+timedelta(days=6)).strftime('%d/%m/%Y')}","="*55,""]
    for i in range(7):
        dj=debut+timedelta(days=i); lignes.append(f"📆 {JOURS_SEMAINE[i].upper()} {dj.strftime('%d/%m')}")
        for r,hh,t in planning[i]: lignes.append(f"   {ic[r]} {r.upper()} — {hh} → {t}")
        lignes.append("")
    lignes+=["="*55,f"📊 TOTAL : {sum(len(p) for p in planning.values())} publications cette semaine","","💡 Préparez vos visuels le dimanche !"]; return "\n".join(lignes)

@mcp.tool()
def suggerer_hashtags(sujet: str, reseau: str, marche: str = "france", nb_hashtags: int = 15) -> str:
    reseau=reseau.lower(); marche=marche.lower()
    if reseau not in ["tiktok","linkedin","instagram"]: return json.dumps({"erreur":"Réseau inconnu."},ensure_ascii=False)
    if marche not in MARCHES: return json.dumps({"erreur":"Marché inconnu."},ensure_ascii=False)
    nb=max(5,min(nb_hashtags,20)); d=MARCHES[marche]["emoji_drapeau"]
    hs="#"+sujet.replace(" ","").replace("'","").replace("é","e").replace("è","e").replace("ê","e").replace("à","a").capitalize()
    pool=HASHTAGS_BASE[reseau][marche].copy(); pool.insert(0,hs); pool.append("#WebdesignAndCo")
    limites={"tiktok":"5-10 hashtags","linkedin":"3-5 hashtags","instagram":"20-30 hashtags"}
    return f"#️⃣ HASHTAGS — {d} {marche.upper()} | {reseau.upper()}\nSujet : {sujet}\n{'='*50}\n\n✅ RECOMMANDÉS ({nb}) :\n{' '.join(pool[:nb])}\n\n📊 Limite conseillée : {limites[reseau]}\n"

@mcp.tool()
def generer_legende(sujet: str, reseau: str, marche: str = "france", objectif: str = "engagement") -> str:
    reseau=reseau.lower(); marche=marche.lower()
    if reseau not in ["tiktok","linkedin","instagram"]: return json.dumps({"erreur":"Réseau inconnu."},ensure_ascii=False)
    if marche not in MARCHES: return json.dumps({"erreur":"Marché inconnu."},ensure_ascii=False)
    d=MARCHES[marche]["emoji_drapeau"]
    ctas={"engagement":{"tiktok":"💬 Et toi, ta plus grande galère avec ça ? Dis-le en commentaire !","linkedin":"🔔 Suivez Webdesign & Co pour ne manquer aucun conseil.","instagram":"❤️ Likez si vous êtes d'accord ! Taguez un entrepreneur. 👇"},"vente":{"tiktok":"🔗 Lien en bio pour un audit GRATUIT. Places limitées !","linkedin":"📩 Envoyez AUDIT en DM pour votre diagnostic offert.","instagram":"📲 Commentez DEVIS pour notre offre personnalisée en 24h. 💌"},"notoriete":{"tiktok":"➕ Suivez-nous pour des conseils webdesign chaque semaine !","linkedin":"♻️ Partagez si cela peut aider votre réseau.","instagram":"📌 Épinglez ce post — il vous servira ! 🔖"}}
    if objectif not in ctas: objectif="engagement"
    cta=ctas[objectif][reseau]; ht=" ".join(HASHTAGS_BASE[reseau][marche][:8])+" #WebdesignAndCo"; ei={"tiktok":"🎬","linkedin":"💼","instagram":"✨"}
    return f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📋 LÉGENDE — Webdesign & Co {d} | {reseau.upper()} | {objectif.upper()}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{ei[reseau]} {sujet.upper()} : ce que vous devez savoir en {marche.capitalize()} {d}\n\nVous dirigez une PME et voulez vous démarquer en ligne ?\nWebdesign & Co est là pour vous. 🚀\n\n🎨 Identité visuelle sur mesure\n💻 Sites web qui convertissent\n📱 Stratégie réseaux sociaux\n📈 Croissance digitale garantie\n\n{sujet} n'est plus une option — c'est une nécessité en 2025.\n\n{cta}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{ht}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✅ COPIER-COLLER DIRECTEMENT."

def publier_automatiquement(marche, reseau):
    sujet,source=choisir_sujet(marche); ton=choisir_ton()
    payload={"sujet":sujet,"marche":marche,"reseau_principal":reseau,"ton":ton,"source_sujet":source,"publications":{"tiktok":{"contenu":generer_contenu(sujet=sujet,reseau="tiktok",marche=marche,ton=ton),"image_url":generer_image_url(sujet,"tiktok")},"linkedin":{"contenu":generer_contenu(sujet=sujet,reseau="linkedin",marche=marche,ton=ton),"image_url":generer_image_url(sujet,"linkedin")},"instagram":{"contenu":generer_contenu(sujet=sujet,reseau="instagram",marche=marche,ton=ton),"image_url":generer_image_url(sujet,"instagram")}},"hashtags":{"tiktok":suggerer_hashtags(sujet=sujet,reseau="tiktok",marche=marche,nb_hashtags=8),"linkedin":suggerer_hashtags(sujet=sujet,reseau="linkedin",marche=marche,nb_hashtags=5),"instagram":suggerer_hashtags(sujet=sujet,reseau="instagram",marche=marche,nb_hashtags=15)},"declencheur":"scheduler_automatique","timestamp":datetime.now().isoformat()}
    result=envoyer_vers_make(payload)
    if result.get("status")=="envoyé": enregistrer_publication(sujet,marche,reseau,ton=ton,source=source)
    print(f"[SCHEDULER] {marche.upper()} {reseau.upper()} | ton={ton} | {sujet[:40]} → {result.get('status')}")

def demarrer_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    charger_log(); scheduler=BackgroundScheduler(timezone="UTC")
    # France (UTC+2 été) — créneaux espacés anti-doublons v2.2
    hf={"tiktok":[("05","00"),("10","00"),("17","00"),("19","00")],"linkedin":[("06","05"),("10","35"),("15","35")],"instagram":[("06","10"),("11","05"),("16","05"),("19","05")]}
    # Dubai (UTC+4) — décalé +10 min anti-collision v2.2
    hd={"tiktok":[("04","10"),("09","10"),("16","10"),("18","10")],"linkedin":[("05","15"),("09","15"),("14","10")],"instagram":[("05","20"),("09","20"),("15","10"),("17","40")]}
    for reseau,slots in hf.items():
        for h,m in slots: scheduler.add_job(publier_automatiquement,CronTrigger(hour=int(h),minute=int(m)),args=["france",reseau],id=f"france_{reseau}_{h}{m}",replace_existing=True)
    for reseau,slots in hd.items():
        for h,m in slots: scheduler.add_job(publier_automatiquement,CronTrigger(hour=int(h),minute=int(m)),args=["dubai",reseau],id=f"dubai_{reseau}_{h}{m}",replace_existing=True)
    # Veille 3 couches chaque matin 06h00 UTC
    scheduler.add_job(rafraichir_veille,CronTrigger(hour=6,minute=0),id="veille_rss",replace_existing=True)
    # Self-ping toutes les 14 min (décalé du Keep-Alive Make à 15 min)
    scheduler.add_job(self_ping,CronTrigger(minute="*/14"),id="self_ping",replace_existing=True)
    scheduler.start()
    total=sum(len(s) for s in hf.values())+sum(len(s) for s in hd.values())
    print(f"⏰ Scheduler v2.2 démarré — {total} publications/jour")
    print(f"🔍 Veille nominative active : Digidop/Eskimoz/Junto/Plezi/Nile | Nexa/BlueBeetle/ChainReaction/DigitalGravity | NoGood/SingleGrain/IgniteVisibility/WebFX/Thrive")
    return scheduler

def run_webhook_server():
    from fastapi import FastAPI,Request,HTTPException,Header; from fastapi.responses import JSONResponse; import uvicorn
    WEBHOOK_SECRET=os.environ.get("WEBHOOK_SECRET","webdesign-co-secret")
    app=FastAPI(title="Webdesign & Co — Webhook Make.com",version="2.2.0")
    def verifier_secret(x_webhook_secret: str=Header(default="")):
        if x_webhook_secret!=WEBHOOK_SECRET: raise HTTPException(status_code=401,detail="Secret invalide.")
    scheduler=demarrer_scheduler()

    @app.get("/health")
    async def health():
        return {"status":"ok","version":"2.2.0","scheduler":"running","publications_loggees":len(_publications_log),"tendances_veille":{m:len(t) for m,t in TENDANCES_VEILLE.items()},"concurrents_veille":{m:len(c) for m,c in CONCURRENTS_VEILLE.items()}}

    @app.get("/scheduler/status")
    async def scheduler_status():
        return JSONResponse({"scheduler":"running","total_jobs":len(scheduler.get_jobs()),"jobs":[{"id":j.id,"next_run":j.next_run_time.isoformat() if j.next_run_time else None} for j in scheduler.get_jobs()]})

    @app.get("/log/publications")
    async def log_publications(): return JSONResponse({"total":len(_publications_log),"publications":_publications_log[-50:]})

    @app.get("/veille/tendances")
    async def veille_tendances(): return JSONResponse({"tendances":TENDANCES_VEILLE,"concurrents":CONCURRENTS_VEILLE,"failles":FAILLES_VEILLE})

    @app.post("/veille/rafraichir")
    async def veille_rafraichir(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret","")); rafraichir_veille()
        return JSONResponse({"status":"ok","tendances":TENDANCES_VEILLE,"concurrents":CONCURRENTS_VEILLE})

    @app.post("/scheduler/publier-maintenant")
    async def scheduler_publier_maintenant(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret","")); data=await request.json()
        publier_automatiquement(data.get("marche","france"),data.get("reseau","instagram"))
        return JSONResponse({"status":"déclenché"})

    @app.post("/webhook/publier-tous-reseaux")
    async def webhook_publier_tous_reseaux(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret","")); data=await request.json()
        sujet=data.get("sujet","")
        if not sujet: raise HTTPException(status_code=400,detail="Champ sujet requis.")
        marche=data.get("marche","france"); ton=data.get("ton",choisir_ton()); image_url=data.get("image_url",""); date_pub=data.get("date_publication","")
        return JSONResponse({"status":"success","sujet":sujet,"marche":marche,"ton":ton,"publications":{"tiktok":{"contenu":generer_contenu(sujet=sujet,reseau="tiktok",marche=marche,ton=ton),"image_url":image_url or generer_image_url(sujet,"tiktok"),"date_publication":date_pub},"linkedin":{"contenu":generer_contenu(sujet=sujet,reseau="linkedin",marche=marche,ton=ton),"image_url":image_url or generer_image_url(sujet,"linkedin"),"date_publication":date_pub},"instagram":{"contenu":generer_contenu(sujet=sujet,reseau="instagram",marche=marche,ton=ton),"image_url":image_url or generer_image_url(sujet,"instagram"),"date_publication":date_pub}},"hashtags":{"tiktok":suggerer_hashtags(sujet=sujet,reseau="tiktok",marche=marche,nb_hashtags=8),"linkedin":suggerer_hashtags(sujet=sujet,reseau="linkedin",marche=marche,nb_hashtags=5),"instagram":suggerer_hashtags(sujet=sujet,reseau="instagram",marche=marche,nb_hashtags=15)}})

    @app.post("/webhook/generer-contenu")
    async def webhook_generer_contenu(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret","")); data=await request.json()
        sujet=data.get("sujet","")
        if not sujet: raise HTTPException(status_code=400,detail="Champ sujet requis.")
        return JSONResponse({"status":"success","contenu":generer_contenu(sujet=sujet,reseau=data.get("reseau","instagram"),marche=data.get("marche","france"),ton=data.get("ton","professionnel"))})

    @app.post("/webhook/surveiller-concurrence")
    async def webhook_surveiller_concurrence(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret","")); data=await request.json()
        return JSONResponse({"status":"success","rapport":surveiller_concurrence(marche=data.get("marche","france"),inclure_tiktok=data.get("inclure_tiktok",False),mot_cle_tiktok=data.get("mot_cle_tiktok",""))})

    @app.post("/webhook/post-concurrent")
    async def webhook_post_concurrent(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret","")); data=await request.json()
        faille=data.get("faille","formulaire_statique"); marche=data.get("marche","france"); reseau=data.get("reseau","linkedin")
        post_json=generer_post_concurrent(faille=faille,marche=marche,reseau=reseau); payload=json.loads(post_json)
        make_result={}
        if data.get("envoyer_make",True):
            make_result=envoyer_vers_make(payload)
            if make_result.get("status")=="envoyé": enregistrer_publication(faille,marche,reseau,ton="concurrent",source="post_concurrent")
        return JSONResponse({"status":"success","post":payload,"make_result":make_result})

    @app.post("/webhook/envoyer-vers-make")
    async def webhook_envoyer_vers_make(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret","")); data=await request.json()
        sujet=data.get("sujet","")
        if not sujet: raise HTTPException(status_code=400,detail="Champ sujet requis.")
        marche=data.get("marche","france"); ton=data.get("ton",choisir_ton()); image_url=data.get("image_url","")
        payload={"sujet":sujet,"marche":marche,"ton":ton,"publications":{"tiktok":{"contenu":generer_contenu(sujet=sujet,reseau="tiktok",marche=marche,ton=ton),"image_url":image_url or generer_image_url(sujet,"tiktok")},"linkedin":{"contenu":generer_contenu(sujet=sujet,reseau="linkedin",marche=marche,ton=ton),"image_url":image_url or generer_image_url(sujet,"linkedin")},"instagram":{"contenu":generer_contenu(sujet=sujet,reseau="instagram",marche=marche,ton=ton),"image_url":image_url or generer_image_url(sujet,"instagram")}},"hashtags":{"tiktok":suggerer_hashtags(sujet=sujet,reseau="tiktok",marche=marche,nb_hashtags=8),"linkedin":suggerer_hashtags(sujet=sujet,reseau="linkedin",marche=marche,nb_hashtags=5),"instagram":suggerer_hashtags(sujet=sujet,reseau="instagram",marche=marche,nb_hashtags=15)},"calendrier":planifier_calendrier(marche=marche)}
        make_result=envoyer_vers_make(payload)
        return JSONResponse({"status":"success","make_result":make_result,"payload_envoye":payload})

    @app.post("/webhook/analyser-tendances")
    async def webhook_analyser_tendances(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret","")); data=await request.json()
        return JSONResponse({"status":"success","tendances":analyser_tendances(marche=data.get("marche","france"),nb_tendances=int(data.get("nb_tendances",5)))})

    @app.post("/webhook/planifier-calendrier")
    async def webhook_planifier_calendrier(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret","")); data=await request.json()
        return JSONResponse({"status":"success","calendrier":planifier_calendrier(marche=data.get("marche","france"),semaine_debut=data.get("semaine_debut",""))})

    @app.post("/webhook/generer-legende")
    async def webhook_generer_legende(request: Request):
        verifier_secret(request.headers.get("x-webhook-secret","")); data=await request.json()
        sujet=data.get("sujet","")
        if not sujet: raise HTTPException(status_code=400,detail="Champ sujet requis.")
        return JSONResponse({"status":"success","legende":generer_legende(sujet=sujet,reseau=data.get("reseau","instagram"),marche=data.get("marche","france"),objectif=data.get("objectif","engagement"))})

    port=int(os.environ.get("PORT",8000))
    print(f"🚀 Webhook Webdesign & Co v2.2 démarré sur http://0.0.0.0:{port}")
    uvicorn.run(app,host="0.0.0.0",port=port)

if __name__ == "__main__":
    if "--webhook" in sys.argv: run_webhook_server()
    else: mcp.run()
