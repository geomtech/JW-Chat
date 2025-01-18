import json
import requests
from bs4 import BeautifulSoup
from utils.eventhandler import EventHandler


def search_jw_org(openai_client, self, tool_call, socketio):
    articles_urls = []

    query = json.loads(tool_call.function.arguments)['query']

    get_bearer_token = requests.get("https://b.jw-cdn.org/tokens/jworg.jwt")
    bearer_token = get_bearer_token.text

    print(f"\nassistant > '{query}' on JW.ORG\n", flush=True)

    jw_url = f"https://b.jw-cdn.org/apis/search/results/F/all?q={str(query)}"

    try:
        r = requests.get(jw_url, headers={"Authorization": f"Bearer {bearer_token}"})
        r = r.json()

        results = r.get("results", [])

        if len(results) > 0:
            socketio.emit('response', {'status': f"{len(results)} résultats sur JW.ORG, récupérations des articles..."})
        
        for result in results:
            label = result.get("label", None)

            if label == "Vidéos":
                pass

            if label == "Rubriques de l'Index":
                pass
            
            if label == None:
                results_in_result = result.get("results", [])
                for result_in_result in results_in_result:
                    if result_in_result.get("subtype", None) == "article":
                        links = result_in_result.get("links", None)

                        if links.get("jw.org"):
                            url = links.get("jw.org")
                            if url:
                                articles_urls.append(url)

    except Exception as e:
        print(f"\nassistant > {str(e)}\n", flush=True)

    if len(articles_urls) > 0:
        output = []

        headers = {
            "Accept": "text/html",
            # Add a user agent to mimic a web browser
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        # get the first article
        article_url = articles_urls[0]
        article = requests.get(article_url, headers=headers)
        article_content = BeautifulSoup(article.text, 'html.parser')

        article_text = article_content.find('div', class_='contentBody').get_text()
        article_title = article_content.title.string

        output.append({
            "title": article_title,
            "content": article_text,
            "url": article_url
        })

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

        jw_doc_id = article_url.split("docid=")[-1].split("&")[0]
        jw_article_image = f"https://cms-imgp.jw-cdn.org/img/p/{jw_doc_id}/univ/art/{jw_doc_id}_univ_sqs_lg.jpg"

        jw_article_image_valid = requests.get(jw_article_image)
        if jw_article_image_valid.status_code != 200:
            jw_article_image = "/static/img/article.png"

        socketio.emit('response', {'article': {
            "url": article_url,
            "title": article_title,
            "image": jw_article_image
        }})
    else:
        with openai_client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.thread_id,
            run_id=self.run_id,
            tool_outputs=[{
                "tool_call_id": tool_call.id,
                "output": "Aucun résultat",
            }],
            event_handler=EventHandler(self.openai_client, self.thread_id, self.assistant_id, socketio)
        ) as stream:
            stream.until_done()

def fetch_jw_content(openai_client, self, tool_call, socketio):
    socketio.emit('response', {'status': "Lecture et réflexion en cours..."})

    jw_url = json.loads(tool_call.function.arguments)['url']
    
    headers = {
        "Accept": "text/html",
        # Add a user agent to mimic a web browser
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    try:
        article = requests.get(jw_url, headers=headers)
        article_content = BeautifulSoup(article.text, 'html.parser')
        article_text = article_content.find('div', class_='contentBody').get_text()
    except Exception as e:
        try:
            article = requests.get(jw_url, headers=headers)
            article_content = BeautifulSoup(article.text, 'html.parser')
            article_text = article_content.get_text()
        except Exception as e:
            print(f"\nassistant > {str(e)}\n", flush=True)
            self.output = "Je n'ai pas pu récupérer d'information."

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