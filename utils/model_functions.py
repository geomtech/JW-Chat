import json
import concurrent.futures
import requests
from bs4 import BeautifulSoup
from utils.eventhandler import EventHandler


def search_jw_org(openai_client, self, tool_call, socketio):
    query = json.loads(tool_call.function.arguments)['query']
    question = json.loads(tool_call.function.arguments)['question']

    get_bearer_token = requests.get("https://b.jw-cdn.org/tokens/jworg.jwt")
    bearer_token = get_bearer_token.text

    print(f"\nassistant > '{query}' on JW.ORG\n", flush=True)
    socketio.emit('response', {'status': f"Recherche de '{query}' via l'API JW.ORG..."})

    jw_url = f"https://b.jw-cdn.org/apis/search/results/F/all?q={str(query)}&limit=5"

    try:
        r = requests.get(jw_url, headers={"Authorization": f"Bearer {bearer_token}"})
        r = r.json()

        results = r.get("results", [])
        results_output = []
        
        for result in results:
            label = result.get("label", None)

            if label == "Vidéos":
                #socketio.emit('response', {'status': "Analyse des vidéos en cours..."})
                pass

            if label == "Rubriques de l'Index":
                #socketio.emit('response', {'status': "Analyse des rubriques de l'index en cours..."})
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
            self.output = str(results_output)

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
                        "content": self.output
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

            self.output = completion.choices[0].message.content

            try:
                self.output = json.loads(self.output)["url"]
            except:
                self.output = "Aucun résultat"
        else:
            self.output = "Aucun résultat"

        with openai_client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.thread_id,
            run_id=self.run_id,
            tool_outputs=[{
                "tool_call_id": tool_call.id,
                "output": self.output,
            }],
            event_handler=EventHandler(self.openai_client, self.thread_id, self.assistant_id, socketio)
        ) as stream:
            stream.until_done()

    except Exception as e:
        print(f"\error search_jw_org > {str(e)}\n", flush=True)
        self.output = "Une erreur a été rencontré lors de la récupération des résultats."

        with openai_client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.thread_id,
            run_id=self.run_id,
            tool_outputs=[{
                "tool_call_id": tool_call.id,
                "output": self.output,
            }],
            event_handler=EventHandler(self.openai_client, self.thread_id, self.assistant_id, socketio)
        ) as stream:
            stream.until_done()

def fetch_jw_content(openai_client, self, tool_call, socketio):
    socketio.emit('response', {'status': "Lecture et réflexion en cours..."})

    jw_url = json.loads(tool_call.function.arguments)['url']
    article_text = "Contenu non récupéré"
    
    headers = {
        "Accept": "text/html",
        # Add a user agent to mimic a web browser
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    try:
        article = requests.get(jw_url, headers=headers)
        article_content = BeautifulSoup(article.text, 'html.parser')

        if "wol.jw.org" in jw_url:
            article_text = article_content.find('div', class_='content')
        else:
            article_text = article_content.find('div', class_='contentBody')
    except Exception as e:
        print(f"\nassistant > {str(e)}\n", flush=True)
        self.output = "Je n'ai pas pu récupérer le contenu de l'article."

    output = {            
        "url": jw_url,
        "content": article_text,
    }

    self.output = str(output)

    with openai_client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.thread_id,
            run_id=self.run_id,
            tool_outputs=[{
                "tool_call_id": tool_call.id,
                "output": self.output,
            }],
            event_handler=EventHandler(self.openai_client, self.thread_id, self.assistant_id, socketio)
        ) as stream:
            stream.until_done()