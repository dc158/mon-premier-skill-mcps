from mcp.server.fastmcp import FastMCP

mcp = FastMCP("analyseur-priorite")


@mcp.tool()
def analyser_priorite(tache: str, urgence: int, importance: int) -> str:
    """Détermine la priorité d'une tâche selon son urgence et son importance (notes de 1 à 10)."""
    score = urgence * importance
    if score > 70:
        return f"🔥 PRIORITÉ MAX : '{tache}' (Score: {score}/100)"
    elif score > 40:
        return f"📅 À PLANIFIER : '{tache}' (Score: {score}/100)"
    else:
        return f"☕ TRÈS CALME : '{tache}' (Score: {score}/100)"


if __name__ == "__main__":
    mcp.run()
