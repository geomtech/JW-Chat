from gzip import decompress
import json
import concurrent.futures
from flask import request
import requests
from bs4 import BeautifulSoup
from utils.eventhandler import EventHandler


def search_jw_org(openai_client, args, socketio):
    try:
        query = args['query']
        question = args['question']

        get_bearer_token = requests.get("https://b.jw-cdn.org/tokens/jworg.jwt")
        bearer_token = get_bearer_token.text

        socketio.emit('response', {'status': f"Recherche de '{query}' via l'API JW.ORG..."}, room=request.sid)

        jw_url = f"https://b.jw-cdn.org/apis/search/results/F/all?q={str(query)}&limit=5"

    
        r = requests.get(jw_url, headers={"Authorization": f"Bearer {bearer_token}"})
        r = r.json()

        results = r.get("results", [])
        results_output = []
        
        for result in results:
            label = result.get("label", None)

            if label == "Vidéos":
                #socketio.emit('response', {'status': "Analyse des vidéos en cours..."}, room=request.sid)
                pass

            if label == "Rubriques de l'Index":
                #socketio.emit('response', {'status': "Analyse des rubriques de l'index en cours..."}, room=request.sid)
                pass
            
            if label == None:
                results_in_result = result.get("results", [])
                for result_in_result in results_in_result:
                    if result_in_result.get("subtype", None) == "article":
                        links = result_in_result.get("links", None)

                        url = links.get("jw.org") or links.get("wol")

                        if "wol" in links:
                            results_output.append({
                                "context": result_in_result.get("context", None),
                                "source": "Bibliothèque en ligne",
                                "url": url,
                                "title": result_in_result.get("title", None),
                                "snippet": result_in_result.get("snippet", None)
                            })
                        elif "jw.org" in links:
                            results_output.append({
                                "context": result_in_result.get("context", None),
                                "source": "Bibliothèque JW.ORG",
                                "url": url,
                                "title": result_in_result.get("title", None),
                                "snippet": result_in_result.get("snippet", None)
                            })

        if len(results_output) > 0:
            output = str(results_output)

            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "Tu es un assistant pour les Témoins de Jéhovah souhaitant avoir des réponses à des recherches sur la Bible"
                    },
                    {
                        "role": "developer",
                        "content": f"Voici les résultats de la recherche '{query}' sur JW.ORG :"
                    },
                    {
                        "role": "developer",
                        "content": output
                    },
                    {
                        "role": "assistant",
                        "content": "Quel est l'article le plus pertinent pour la question suivante : '" + question + "' ?"
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "result_schema",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "description": "L'URL de l'article le plus pertinent",
                                    "type": "string"
                                },
                                "additionalProperties": False
                            }
                        }
                    }
                }
            )

            completion_output = completion.choices[0].message.content

            try:
                return json.loads(completion_output)["url"]
            except:
                return "Aucun résultat"
        else:
            return "Aucun résultat"

    except Exception as e:
        return "Une erreur a été rencontré lors de la récupération des résultats. Détails techniques : " + str(e)

def fetch_jw_content(args, socketio):
    socketio.emit('response', {'status': "Lecture et réflexion en cours..."}, room=request.sid)
    jw_links = {}
    jw_url = args['url']
    article_text = "Contenu non récupéré"
    
    try:
        article = requests.get(jw_url)
        article_content = BeautifulSoup(article.text, 'html.parser')

        if "wol.jw.org" in jw_url:
            article_text = article_content.find('div', class_='content')
        else:
            article_text = article_content.find('div', class_='contentBody')

        if article_text != "Contenu non récupéré":
            if article_text == None:
                article_text = article.text
            else:
                article_text = article_text.get_text()
        else:
            article_text = article_content.get_text()

        output = {
            "page_title": article_content.title.string, 
            "url": jw_url,
            "content": article_text,
        }

        image_url = None

        try:
            doc_id = jw_url.split('docid=')[1]
            doc_id = doc_id.split('&')[0]
            
            if "wol.jw.org" in jw_url:
                jw_image_url = f"/jw-image/{doc_id}/wol"
            else:
                jw_image_url = f"/jw-image/{doc_id}/jw"
            
            image_url = jw_image_url
        except:
            if "wol.jw.org" in jw_url:
                image_url = f"/jw-image/null/wol"
            else:
                image_url = f"/jw-image/null/jw"

        jw_links = {
            "url": jw_url,
            "title": article_content.title.string,
            "image": image_url
        }
    except Exception as e:
        output = {
            "page_title": "Erreur lors de la récupération du contenu", 
            "url": jw_url,
            "content": "Contenu non récupéré"
        }
        print(e)

    return [str(output), jw_links]