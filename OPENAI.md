# Instructions

Le prompt est disponible ici [PROMPT.md](PROMPT.md)

# Fonctions

Afin que JW Chat puisse récupérer des informations sur Internet, deux fonctions sont à créer dans l'espace de votre assistant sur l'interface web OpenAI. [OpenAI Assistants](https://platform.openai.com/assistants/)

# Paramètres

Recommandé : Température = 0.60 & Top P 1.0

## search_jw_org

```json
{
    "name": "search_jw_org",
    "description": "Effectue une recherche sur JW.ORG et réponds à la question de l'utilisateur grâce au contenu de ou des articles trouvés.",
    "strict": true,
    "parameters": {
        "type": "object",
        "required": [
            "query",
            "question"
        ],
        "properties": {
            "query": {
                "type": "string",
                "description": "Recherche en français a effectuer sur le site JW.ORG pour trouver une liste d'articles pouvant permettre de répondre à la question"
            },
            "question": {
                "type": "string",
                "description": "Question de l'utilisateur"
            }
        },
        "additionalProperties": false
    }
}
```

## fetch_jw_content

```json
{
  "name": "fetch_jw_content",
  "description": "L'utilisateur donne une URL JW.ORG ou WOL.JW.ORG, l'assistant prend le contenu de la page et répond à la question",
  "strict": true,
  "parameters": {
    "type": "object",
    "required": [
      "url"
    ],
    "properties": {
      "url": {
        "type": "string",
        "description": "URL of the JW.ORG or WOL.JW.ORG page to fetch content from"
      }
    },
    "additionalProperties": false
  }
}
```