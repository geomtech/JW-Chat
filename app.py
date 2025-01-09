from gevent import monkey
monkey.patch_all()

import os
import time
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from openai import OpenAI
from typing_extensions import override
from openai import AssistantEventHandler, OpenAI
from openai.types.beta.threads import Text, TextDelta
from openai.types.beta.threads.runs import ToolCall, ToolCallDelta
from openai.types.beta.threads import Message, MessageDelta
from openai.types.beta.threads.runs import ToolCall, RunStep, FunctionToolCall
from openai.types.beta import AssistantStreamEvent

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

OPEN_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-proj")
openai_client = OpenAI(api_key=OPEN_API_KEY)

openai_assistant_id = ""

class EventHandler(AssistantEventHandler):
    def __init__(self, thread_id, assistant_id):
        super().__init__()
        self.output = None
        self.tool_id = None
        self.thread_id = thread_id
        self.assistant_id = assistant_id
        self.run_id = None
        self.run_step = None
        self.function_name = ""
        self.arguments = ""

    @override
    def on_text_delta(self, delta, snapshot):
        if self.tool_id == None:
            print(f"\non_text_delta > {delta.value}\n", flush=True)
            socketio.emit('response', {'message': delta.value})

    @override
    def on_end(self):
        socketio.emit('response', {'status': 'end'})

    @override
    def on_message_delta(self, delta, snapshot):
        if self.tool_id:
            print(f"\non_message_delta > {delta.content[0].text}\n", flush=True)
            socketio.emit('response', {'message': delta.content[0].text.value})

    @override
    def on_message_done(self, message) -> None:
        # print a citation to the file searched
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = openai_client.files.retrieve(file_citation.file_id)

                if "nwt" in cited_file.filename:
                    url = f"https://www.jw.org/finder?pub=nwtsty&bible=20018000&wtlocale=F&srcid=share"
                    citations.append({
                        "url": url,
                        "title": f"[{index}] Traduction du Monde Nouveau"
                    })

        socketio.emit('response', {'sources': citations, 'completed_message': message_content.value})

    @override
    def on_tool_call_created(self, tool_call):       
        self.tool_id = tool_call.id

        if tool_call.type == "file_search":
            socketio.emit('response', {'status': "source_search"})
        elif tool_call.type == "function":
            self.function_name = tool_call.function.name
            socketio.emit('response', {'status': "function_call"})

            keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=self.run_id
            )

            while keep_retrieving_run.status in ["queued", "in_progress"]: 
                keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=self.run_id
                )

    @override
    def on_tool_call_done(self, tool_call):   
        keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
            thread_id=self.thread_id,
            run_id=self.run_id
        )
             
        # search on JW.ORG
        if keep_retrieving_run.status == "requires_action":
            if tool_call.type == "function":
                if tool_call.function.name == "search_jw_org":
                    articles_urls = []

                    query = json.loads(tool_call.function.arguments)['query']

                    get_bearer_token = requests.get("https://b.jw-cdn.org/tokens/jworg.jwt")
                    bearer_token = get_bearer_token.text

                    jw_url = f"https://b.jw-cdn.org/apis/search/results/F/all?q={str(query)}"

                    try:
                        r = requests.get(jw_url, headers={"Authorization": f"Bearer {bearer_token}"})
                        r = r.json()

                        results = r.get("results", [])

                        if len(results) > 0:
                            socketio.emit('response', {'status': "Résultats trouvés..."})
                        
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
                                            articles_urls.append(url)
                    except Exception as e:
                        print(f"\nassistant > {str(e)}\n", flush=True)

                    if len(articles_urls) > 0:
                        print("plusieurs articles trouvés", flush=True)
                        # get the first article
                        article_url = articles_urls[0]
                        article = requests.get(article_url, headers={"User-Agent": "Mozilla/5.0"})
                        article_content = BeautifulSoup(article.text, 'html.parser')
                        for script in article_content(["script", "style"]):
                            script.decompose()
                        article_text = article_content.get_text()
                        article_title = article_content.title.string

                        self.output = {
                            "title": article_title,
                            "content": article_text,
                            "url": article_url,
                            "other_articles": articles_urls
                        }

                        with openai_client.beta.threads.runs.submit_tool_outputs_stream(
                            thread_id=self.thread_id,
                            run_id=self.run_id,
                            tool_outputs=[{
                                "tool_call_id": self.tool_id,
                                "output": self.output,
                            }],
                            event_handler=EventHandler(self.thread_id, self.assistant_id)
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

    @override
    def on_run_step_created(self, run_step: RunStep) -> None:
        self.run_id = run_step.run_id
        self.run_step = run_step


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('ask_openai')
def handle_ask_openai(data):
    prompt = data.get("user_input")
    thread_id = data.get("thread_id", None)

    assistants = openai_client.beta.assistants.list()
    openai_assistant_id = str(assistants.data[0].id)

    openai_client.beta.assistants.retrieve(assistant_id=openai_assistant_id)

    new_thread = None
    if thread_id:
        new_thread = openai_client.beta.threads.retrieve(thread_id=thread_id)
    else:
        new_thread = openai_client.beta.threads.create()

    socketio.emit('response', {'thread_id': f"{new_thread.id}"})
    
    openai_client.beta.threads.messages.create(thread_id=new_thread.id, role="user", content=prompt)

    with openai_client.beta.threads.runs.stream(
        thread_id=new_thread.id,
        assistant_id=openai_assistant_id,
        event_handler=EventHandler(
            thread_id=new_thread.id,
            assistant_id=openai_assistant_id
        ),
    ) as stream:
        stream.until_done()


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True, port=int(os.getenv("PORT", default=5000)))
