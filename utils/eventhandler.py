import json
import time
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
        self.jw_links = []

    @override
    def on_text_delta(self, delta, snapshot):
        if self.tool_id == None:
            self.socketio.emit('response', {'message': delta.value})

    @override
    def on_end(self):        
        self.socketio.emit('response', {
            'status': 'end'
        })

        self.socketio.emit('response', {
            'jw_links': self.jw_links
        })

        self.jw_links = []

    @override
    def on_message_delta(self, delta, snapshot):
        if self.tool_id:
            content_entry = delta.content[0].text
            message_delta = content_entry.value
            
            if content_entry.annotations:
                for annotation in content_entry.annotations:
                    if annotation.type == "file_citation":
                        cited_file = self.openai_client.files.retrieve(annotation.file_citation.file_id)
                        
                        if "nwt" not in cited_file.filename:
                            message_delta = str(message_delta).replace(annotation.text, "")
                            
                            self.socketio.emit('response', {
                                'pub': {
                                    "url": None,
                                    "title": pubs.get_publication(cited_file.filename)["title"],
                                    "image": pubs.get_publication(cited_file.filename)["image"]
                                }
                            })
            self.socketio.emit('response', {'message': message_delta})

    @override
    def on_tool_call_created(self, tool_call):       
        self.tool_id = tool_call.id

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

        print("status", keep_retrieving_run.status)
             
        # search on JW.ORG
        if keep_retrieving_run.status == "requires_action":
            tools_outputs = []

            for tool_call in keep_retrieving_run.required_action.submit_tool_outputs.tool_calls:
                if tool_call.function.name == "search_jw_org":
                    arguments = json.loads(tool_call.function.arguments)

                    print(f"Running tool - '{tool_call.function.name}' | With args - {arguments}")
                    output = model_functions.search_jw_org(self.openai_client, arguments, self.socketio)

                    print("output", output, " now fetching content...")

                    output = model_functions.fetch_jw_content({"url": output, "question": arguments['question']}, self.socketio)

                    print("fetched ")

                    self.jw_links.append(output[1])
                    
                    tool_output = {"tool_call_id":tool_call.id, "output": str(output)}
                    tools_outputs.append(tool_output)
                elif tool_call.function.name == "fetch_jw_content":
                    arguments = json.loads(tool_call.function.arguments)

                    print(f"Running tool - '{tool_call.function.name}' | With args - {arguments}")
                    output = model_functions.fetch_jw_content(arguments, self.socketio)[0]

                    tool_output = {"tool_call_id":tool_call.id, "output": str(output)}
                    tools_outputs.append(tool_output)
                else:
                    tool_output = {"tool_call_id":tool_call.id}
                    tools_outputs.append(tool_output)

            with self.openai_client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=self.thread_id,
                run_id=self.run_id,
                tool_outputs=tools_outputs,
                event_handler=EventHandler(self.openai_client, self.thread_id, self.assistant_id, self.socketio)
                ) as stream:
                    stream.until_done()

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

