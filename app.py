import os
import time
import json
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
socketio = SocketIO(app, cors_allowed_origins="*")

OPEN_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-proj")
openai_client = OpenAI(api_key=OPEN_API_KEY)

openai_assistant_id = ""


def my_example_funtion():
   return json.dumps({
       "domain": [
           {
               "name": "hawkflow.ai",
               "data": {
                   "14-03-2024": "31.28%",
                   "15-03-2024": "28.8%",
                   "16-03-2024": "34.95%",
                   "17-03-2024": "32.67%",
                   "18-03-2024": "33.46%",
                   "19-03-2024": "33.23%",
                   "20-03-2024": "33.37%",
                   "21-03-2024": "34.46%"
               }
           }
       ]
   })

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
    def on_text_created(self, text) -> None:
        #print(f"\nassistant on_text_created > ", end="", flush=True)
        pass

    @override
    def on_text_delta(self, delta, snapshot):
        # print(f"\nassistant on_text_delta > {delta.value}", end="", flush=True)
        if "【" not in delta.value:
            socketio.emit('response', {'message': f"{delta.value}"})
        else:
            print(f"\nassistant on_text_delta > {delta.value}", end="", flush=True)

    @override
    def on_end(self):
        #print(f"\n end assistant > ",self.current_run_step_snapshot, end="", flush=True)
        socketio.emit('response', {'status': f"end"})

    @override
    def on_exception(self, exception: Exception) -> None:
        """Fired whenever an exception happens during streaming"""
        print(f"\nassistant > {exception}\n", end="", flush=True)

    @override
    def on_message_created(self, message: Message) -> None:
        #print(f"\nassistant on_message_created > {message}\n", end="", flush=True)
        pass

    @override
    def on_message_done(self, message: Message) -> None:
        #print(f"\nassistant on_message_done > {message}\n", end="", flush=True)
        pass

    @override
    def on_message_delta(self, delta: MessageDelta, snapshot: Message) -> None:
        # print(f"\nassistant on_message_delta > {delta}\n", end="", flush=True)
        pass

    def on_tool_call_created(self, tool_call):
        # 4
        print(f"\nassistant on_tool_call_created > {tool_call}")

        if tool_call.type == FunctionToolCall:
            self.function_name = tool_call.function.name

            self.tool_id = tool_call.id
            print(f"\non_tool_call_created > run_step.status > {self.run_step.status}")

            print(f"\nassistant > {tool_call.type} {self.function_name}\n", flush=True)

            keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=self.run_id
            )

            while keep_retrieving_run.status in ["queued", "in_progress"]:
                keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=self.run_id
                )

                print(f"\nSTATUS: {keep_retrieving_run.status}")

        print(f"\nassistant > {tool_call.type} Utilisation de la \n", flush=True)

    @override
    def on_tool_call_done(self, tool_call: ToolCall) -> None:
        keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
            thread_id=self.thread_id,
            run_id=self.run_id
        )

        print(f"\nDONE STATUS: {keep_retrieving_run.status}")

        if keep_retrieving_run.status == "completed":
            all_messages = openai_client.beta.threads.messages.list(thread_id=self.thread_id)

            print(all_messages.data[0].content[0].text.value, "", "")
            return

        elif keep_retrieving_run.status == "requires_action":
            print("here you would call your function")

            if self.function_name == "example_blog_post_function":
                function_data = my_example_funtion()

                self.output = function_data

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
            else:
                print("unknown function")
                return

    @override
    def on_run_step_created(self, run_step: RunStep) -> None:
        # 2
        #print(f"on_run_step_created")
        self.run_id = run_step.run_id
        self.run_step = run_step
        #print("The type ofrun_step run step is ", type(run_step), flush=True)
        #print(f"\n run step created assistant > {run_step}\n", flush=True)

    @override
    def on_run_step_done(self, run_step: RunStep) -> None:
        #print(f"\n run step done assistant > {run_step}\n", flush=True)
        pass

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'function':
            # the arguments stream thorugh here and then you get the requires action event
            print(delta.function.arguments, end="", flush=True)
            self.arguments += delta.function.arguments
        elif delta.type == 'code_interpreter':
            print(f"on_tool_call_delta > code_interpreter")
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)
        else:
            print("ELSE")
            print(delta, end="", flush=True)

    @override
    def on_event(self, event: AssistantStreamEvent) -> None:
        # print("In on_event of event is ", event.event, flush=True)

        if event.event == "thread.run.requires_action":
            print("\nthread.run.requires_action > submit tool call")
            print(f"ARGS: {self.arguments}")


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

    try:
        new_thread = None
        if thread_id:
            new_thread = openai_client.beta.threads.retrieve(thread_id=thread_id)
        else:
            new_thread = openai_client.beta.threads.create()

        socketio.emit('response', {'thread_id': f"{new_thread.id}"})
        
        openai_client.beta.threads.messages.create(
            thread_id=new_thread.id, role="user", content=prompt)

        with openai_client.beta.threads.runs.stream(
            thread_id=new_thread.id,
            assistant_id=openai_assistant_id,
            event_handler=EventHandler(new_thread.id, openai_assistant_id),
        ) as stream:
            stream.until_done()

    except Exception as e:
        socketio.emit('response', {'error': f"Erreur : {str(e)}"})


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)
