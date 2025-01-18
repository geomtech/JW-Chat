from typing_extensions import override
from openai import AssistantEventHandler, OpenAI
from openai.types.beta.threads import Text, TextDelta
from openai.types.beta.threads.runs import ToolCall, ToolCallDelta
from openai.types.beta.threads import Message, MessageDelta
from openai.types.beta.threads.runs import ToolCall, RunStep, FunctionToolCall
from openai.types.beta import AssistantStreamEvent

from utils import pubs

class EventHandler(AssistantEventHandler):
    def __init__(self, openai_client, thread_id, assistant_id, socketio):
        super().__init__()
        self.output = None
        self.tool_id = None
        self.thread_id = thread_id
        self.assistant_id = assistant_id
        self.run_id = None
        self.run_step = None
        self.function_name = ""
        self.arguments = ""
        self.socketio = socketio
        self.openai_client = openai_client

    @override
    def on_text_delta(self, delta, snapshot):
        if self.tool_id == None:
            self.socketio.emit('response', {'message': delta.value})

    @override
    def on_end(self):
        self.socketio.emit('response', {'status': 'end'})

    @override
    def on_message_delta(self, delta, snapshot):
        if self.tool_id:
            print(f"\non_message_delta > {delta.content[0].text}\n", flush=True)
            self.socketio.emit('response', {'message': delta.content[0].text.value})

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
                cited_file = self.openai_client.files.retrieve(file_citation.file_id)

                if "nwt" in cited_file.filename:
                    url = f"https://www.jw.org/finder?pub=nwtsty&bible=20018000&wtlocale=F&srcid=share"
                    citations.append({
                        "url": url,
                        "title": f"[{index}] Traduction du Monde Nouveau"
                    })
                    self.socketio.emit('response', {'pub': {
                        "url": url,
                        "title": "Traduction du Monde Nouveau",
                        "image": "/static/img/bible.png"
                    }})
                else:
                    citations.append({
                        "url": None,
                        "title": f"[{index}] {pubs.get_publication(cited_file.filename)}",
                        "image": "/static/img/article.png"
                    })
                    self.socketio.emit('response', {'pub': {
                        "url": None,
                        "title": pubs.get_publication(cited_file.filename),
                        "image": "/static/img/article.png"
                    }})

        self.socketio.emit('response', {'sources': [], 'completed_message': message_content.value})

    @override
    def on_tool_call_created(self, tool_call):       
        self.tool_id = tool_call.id

        print(f"\non_tool_call_created > {tool_call.type} - {tool_call.id}\n", flush=True)

        if tool_call.type == "file_search":
            self.function_name = ""
            self.socketio.emit('response', {'status': "source_search"})
        elif tool_call.type == "function":
            self.function_name = tool_call.function.name
            self.socketio.emit('response', {'status': "function_call"})

            keep_retrieving_run = self.openai_client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=self.run_id
            )

            while keep_retrieving_run.status in ["queued", "in_progress"]: 
                keep_retrieving_run = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=self.run_id
                )

    @override
    def on_tool_call_done(self, tool_call):   
        from utils import model_functions

        keep_retrieving_run = self.openai_client.beta.threads.runs.retrieve(
            thread_id=self.thread_id,
            run_id=self.run_id
        )
             
        # search on JW.ORG
        if keep_retrieving_run.status == "requires_action":
            if tool_call.type == "function":
                if tool_call.function.name == "search_jw_org":
                    model_functions.search_jw_org(self.openai_client, self, tool_call, self.socketio)
                elif tool_call.function.name == "fetch_jw_content":
                    model_functions.fetch_jw_content(self.openai_client, self, tool_call, self.socketio)
            elif tool_call.type == "file_search":
                self.output = "Recherche dans les fichiers..."  # Define self.output before using it

                with self.openai_client.beta.threads.runs.submit_tool_outputs_stream(
                        thread_id=self.thread_id,
                        run_id=self.run_id,
                        tool_outputs=[{
                            "tool_call_id": tool_call.id
                        }],
                        event_handler=EventHandler(self.thread_id, self.assistant_id)
                    ) as stream:
                        stream.until_done()
            else :
                print(f"\nassistant > {tool_call.type}\n", flush=True)
        elif keep_retrieving_run.status == "failed":
            self.socketio.emit('response', {'error': "Une erreur s'est produite lors de la recherche"})
            print(f"\nassistant > {tool_call.type}\n", flush=True)
            print(f"\nassistant > {keep_retrieving_run.last_error}\n", flush=True)

        elif keep_retrieving_run.status == "in_progress":
            if tool_call.type == "function":
                if tool_call.function.name == "search_jw_org":
                    self.socketio.emit('response', {'status': "Recherche en cours..."})

    @override
    def on_run_step_created(self, run_step: RunStep) -> None:
        self.run_id = run_step.run_id
        self.run_step = run_step

