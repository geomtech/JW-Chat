import json
import concurrent.futures
import requests
from bs4 import BeautifulSoup
from utils.eventhandler import EventHandler


def search_jw_org(openai_client, self, tool_call, socketio):
    articles_urls = []
    wol_articles_urls = []

    query = json.loads(tool_call.function.arguments)['query']

    get_bearer_token = requests.get("https://b.jw-cdn.org/tokens/jworg.jwt")
    bearer_token = get_bearer_token.text

    print(f"\nassistant > '{query}' on JW.ORG\n", flush=True)
    socketio.emit('response', {'status': f"Recherche de '{query}' via l'API JW.ORG..."})

    jw_url = f"https://b.jw-cdn.org/apis/search/results/F/all?q={str(query)}&limit=5"

    try:
        r = requests.get(jw_url, headers={"Authorization": f"Bearer {bearer_token}"})
        r = r.json()

        results = r.get("results", [])
        
        for result in results:
            label = result.get("label", None)

            if label == "Vidéos":
                socketio.emit('response', {'status': "Analyse des vidéos en cours..."})
                pass

            if label == "Rubriques de l'Index":
                socketio.emit('response', {'status': "Analyse des rubriques de l'index en cours..."})
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
                                continue
                        else:
                            if links.get("wol"):
                                url = links.get("wol")
                                if url:
                                    wol_articles_urls.append(url)

    except Exception as e:
        print(f"\error search_jw_org > {str(e)}\n", flush=True)

    socketio.emit('response', {'status': f"{len(articles_urls)} articles trouvés sur JW.ORG et {len(wol_articles_urls)} articles trouvés sur la Bibliothèque en ligne."})

    if len(articles_urls) > 0 or len(wol_articles_urls) > 0:
        headers = {
            "Accept": "text/html",
            # Add a user agent to mimic a web browser
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        def fetch_article_content(url, headers, content_class):
            response = requests.get(url, headers=headers)
            article_content = BeautifulSoup(response.text, 'html.parser')
            article_text = article_content.find('div', class_=content_class).get_text()
            article_title = article_content.title.string
            return article_title, article_text
        
        output = []
        sources = []

        # Process articles from articles_urls
        for article in articles_urls:
            article_title, article_text = fetch_article_content(article, headers, 'contentBody')
            output.append({
                "context": "JW.ORG",
                "title": article_title,
                "content": article_text,
                "url": article
            })

        # Process articles from wol_articles_urls
        for article in wol_articles_urls:
            article_title, article_text = fetch_article_content(article, headers, 'content')
            output.append({
                "context": "Bibliothèque en ligne",
                "title": article_title,
                "content": article_text,
                "url": article
            })

        for article in output:
            jw_doc_id = article['url'].split("docid=")[-1].split("&")
            jw_article_image = f"https://cms-imgp.jw-cdn.org/img/p/{jw_doc_id}/univ/art/{jw_doc_id}_univ_sqs_lg.jpg"

            jw_article_image_valid = requests.head(jw_article_image)
            if jw_article_image_valid.status_code != 200:
                jw_article_image = "/static/img/article.png"

            sources.append({
                "url": article,
                "title": article_title,
                "image": jw_article_image
            })

        self.output = str(output[0])

        def chunk_data(data, chunk_size=5000):
            for i in range(0, len(data), chunk_size):
                yield data[i:i + chunk_size]

        chunks = list(chunk_data(self.output))
        for chunk in chunks:
            with openai_client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=self.thread_id,
                run_id=self.run_id,
                tool_outputs=[{
                    "tool_call_id": tool_call.id,
                    "output": chunk,
                }],
                event_handler=EventHandler(self.openai_client, self.thread_id, self.assistant_id, socketio)
            ) as stream:
                stream.until_done()

        print(sources)
        socketio.emit('response', {'article': sources})
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