import json

# Voici ton premier outil personnalisé (Skill)
def analyser_priorite(tache, urgence, importance):
    score = int(urgence) * int(importance)
    if score > 70:
        return f"🔥 PRIORITÉ MAX : '{tache}' (Score: {score}/100)"
    elif score > 40:
        return f"📅 À PLANIFIER : '{tache}' (Score: {score}/100)"
    else:
        return f"☕ TRÈS CALME : '{tache}' (Score: {score}/100)"

# Métadonnées pour que Claude comprenne comment utiliser le skill
metadata = {
    "name": "analyseur_priorite",
    "description": "Détermine la priorité d'une tâche (notes de 1 à 10)",
    "parameters": ["tache", "urgence", "importance"]
}
