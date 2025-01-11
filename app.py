from gevent import monkey
monkey.patch_all()

import os
import time
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, redirect, render_template, request, session
from flask_socketio import SocketIO, emit

from openai import OpenAI

from utils import eventhandler

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
OPEN_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-proj...")
openai_client = OpenAI(api_key=OPEN_API_KEY)
openai_assistant_id = ""

@app.route('/auth', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['api_key'] == OPEN_API_KEY:
            session['is_logged'] = True
            session.permanent = True
            return redirect('/')

    return render_template('login.html')

@app.route('/')
def index():
    if 'is_logged' not in session:
        return redirect('/auth')
    
    thread_id = session.get('thread_id', None)

    if thread_id:
        thread_found = openai_client.beta.threads.retrieve(thread_id=thread_id)

        if thread_found:
            messages = openai_client.beta.threads.messages.list(thread_id=thread_id)
            messages = messages.data

            for message in messages:
                if message.role == "user":
                    print(f"\nuser > {message.content}\n", flush=True)
    return render_template('index.html')


@socketio.on('ask_openai')
def handle_ask_openai(data):
    if 'is_logged' not in session:
        socketio.emit('response', {'message': f"Vous n'êtes pas connecté"})
    else:
        try:
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
            session['thread_id'] = str(new_thread.id)
            
            openai_client.beta.threads.messages.create(thread_id=new_thread.id, role="user", content=prompt)

            with openai_client.beta.threads.runs.stream(
                thread_id=new_thread.id,
                assistant_id=openai_assistant_id,
                event_handler=eventhandler.EventHandler(
                    openai_client=openai_client,
                    thread_id=new_thread.id,
                    assistant_id=openai_assistant_id,
                    socketio=socketio
                ),
            ) as stream:
                stream.until_done()
        except Exception as e:
            socketio.emit('response', {'error': f"Une erreur s'est produite: {str(e)}"})


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True, port=int(os.getenv("PORT", default=5000)))
