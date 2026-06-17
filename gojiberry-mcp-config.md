# Configuration MCP Gojiberry — Claude Desktop

## État de la vérification (17 juin 2026)

### Package npm

| Package testé | Résultat |
|---|---|
| `gojiberry-mcp` | ❌ Inexistant sur npm |
| `@gojiberry/mcp` | ❌ Inexistant sur npm |
| `@gojiberry/mcp-server` | ❌ Inexistant sur npm |
| `@openpets/gojiberry` | ⚠️ Existe mais ce n'est PAS un serveur MCP Claude |

Le package `@openpets/gojiberry` est un plugin pour l'écosystème OpenPets/OpenCode,
pas un serveur MCP compatible avec Claude Desktop.

### Ce qu'est un vrai serveur MCP

Un serveur MCP pour Claude Desktop doit :
- Utiliser `@modelcontextprotocol/sdk` comme dépendance
- Exposer un binaire exécutable (via `npx` ou `node`)
- Être configuré dans `claude_desktop_config.json`

## Template de configuration Claude Desktop

Fichier à modifier : `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "gojiberry": {
      "command": "npx",
      "args": ["-y", "PACKAGE_MCP_GOJIBERRY"],
      "env": {
        "GOJIBERRY_API_KEY": "ta-cle-api-ici"
      }
    }
  }
}
```

**Remplace `PACKAGE_MCP_GOJIBERRY`** par le bon nom de package une fois que
Gojiberry publie son serveur MCP officiel.

## Prochaines étapes

1. Consulter la documentation officielle Gojiberry : https://www.gojiberry.ai/
2. Chercher un serveur MCP dans leur GitHub si disponible
3. Contacter le support Gojiberry pour connaître le nom exact du package MCP
4. Une fois le bon package trouvé, mettre à jour ce fichier et la config locale

## Redémarrage de Claude Desktop

Après toute modification de `claude_desktop_config.json` :
- Fermer complètement Claude Desktop (icône dans la barre des tâches → Quitter)
- Relancer Claude Desktop
- Vérifier dans Paramètres > MCP que le serveur "gojiberry" apparaît avec un statut vert
