from gevent import monkey
monkey.patch_all()

import os
import time
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from pymongo import MongoClient
from bson.objectid import ObjectId
from redis import Redis
from cachelib.file import FileSystemCache

from openai import OpenAI

from utils import costs, eventhandler, email, db
from utils.email import send_admin_notification

from blueprints import accounts, admin

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent', manage_session=False)
bcrypt = Bcrypt(app)
mail = Mail(app)

SESSION_TYPE = 'redis'
SESSION_REDIS = Redis.from_url(os.environ.get('REDIS_URL', 'redis://'))
app.config.from_object(__name__)
Session(app)

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017/")
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "your_brevo_api_key")

client = MongoClient(MONGODB_URL)
db = client['jw_chat']
users_collection = db['users']

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "sk-proj..."))
openai_assistant_id = ""

app.register_blueprint(accounts.accounts_bp)
app.register_blueprint(admin.admin_bp)

@app.route('/auth', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({"email": email})

        if user and bcrypt.check_password_hash(user['password'], password):
            if user['is_active']:
                session['is_logged'] = True
                session['user_id'] = str(user['_id'])
                session.permanent = True
                return redirect('/')
            else:
                return render_template('message.html', message="Votre compte n'a pas encore été validé par un administrateur.")
        else:
            return render_template('message.html', message="Identifiants incorrects.")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        rgpd_accept = request.form.get('rgpd_accept')

        if password != confirm_password:
            return render_template('register.html', error="Les mots de passe ne correspondent pas.")

        if not rgpd_accept:
            return render_template('register.html', error="Vous devez accepter la politique de confidentialité et de protection des données.")

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        user = {
            "email": email,
            "password": hashed_password,
            "is_active": False,
            "registration_date": time.strftime('%Y-%m-%d %H:%M:%S')
        }

        users_collection.insert_one(user)
        send_admin_notification(email, BREVO_API_KEY)
        return render_template('message.html', message="Votre inscription a été prise en compte. Un administrateur validera votre compte prochainement.")

    return render_template('register.html')

@app.route('/data-privacy', methods=['GET'])
def data_privacy():
    return render_template('data-privacy.html')

@app.route('/')
def index():
    if 'is_logged' not in session:
        return redirect('/auth')
    
    if costs.balance_for_user(session.get('user_id', None)) <= 0:
        return redirect('/accounts')
    
    session.pop('thread_id', None)
    
    db = client['jw_chat']
    history_collection = db['history']
    user_id = session.get('user_id', None)

    user_history = None

    if user_id:
        user_history = history_collection.find({"user_id": user_id})
        
    return render_template('index.html', user_history=user_history)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/auth')


@app.route('/api/v1/history', methods=['GET', 'POST'])
def get_history():
    if 'is_logged' not in session:
        return "Unauthorized", 401

    db = client['jw_chat']
    history_collection = db['history']
    user_id = session.get('user_id', None)

    if request.method == 'POST':
        data = request.json
        user_id = session.get('user_id', None)
        user_input = data.get('user_input', None)
        thread_id = data.get('thread_id', None)
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

        if user_id and user_input and thread_id:
            history_found = history_collection.find_one({"user_id": user_id, "thread_id": thread_id})
            if history_found:
                return "OK", 200

            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "Tu es un assistant pour les Témoins de Jéhovah souhaitant avoir des réponses à des recherches sur la Bible"
                    },
                    {
                        "role": "developer",
                        "content": f"Génère un titre concernant la discussion suivante : '{user_input}'"
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "result_schema",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "description": "Titre de la discussion",
                                    "type": "string"
                                },
                                "additionalProperties": False
                            }
                        }
                    }
                }
            )

            history_collection.insert_one({
                "user_id": user_id,
                "title": json.loads(completion.choices[0].message.content)["title"],
                "thread_id": thread_id,
                "timestamp": timestamp
            })

            return "OK", 200

    user_history = []

    if user_id:
        user_history = list(history_collection.find({"user_id": user_id}, {"_id": 0, "user_id": 0}))
        
    return jsonify(user_history)


@app.route('/api/v1/history/<thread_id>', methods=['GET', 'DELETE'])
def get_thread_history(thread_id):
    if 'is_logged' not in session:
        return "Unauthorized", 401
    
    if request.method == 'DELETE':
        db = client['jw_chat']
        history_collection = db['history']
        user_id = session.get('user_id', None)

        if user_id:
            try:
                history_collection.delete_many(
                    {"user_id": user_id, "thread_id": thread_id})
                openai_client.beta.threads.delete(thread_id=thread_id)
                return "OK", 200
            except Exception as e:
                return str(e), 500
    
    session['thread_id'] = thread_id

    messages_list = []
    user_history = []

    if thread_id:
        messages = openai_client.beta.threads.messages.list(thread_id=thread_id, limit=30)
        for message in messages:
            messages_list.append({
                "role": message.role,
                "content": message.content[0].text.value,
                "timestamp": message.created_at
            })

    if messages_list:
        user_history = messages_list
        user_history = sorted(user_history, key=lambda x: x['timestamp'])
        
    return jsonify(user_history)


@socketio.on('action')
def handle_action(data):
    if data == "new_chat":
        session.pop('thread_id', None)
        socketio.emit('response', {'status': 'new_chat_started'}, room=request.sid)
        

@socketio.on('ask_openai')
def handle_ask_openai(data):
    if 'is_logged' in session:
        try:
            prompt = data.get("user_input")
            thread_id = session.get('thread_id', None)

            if costs.balance_for_user(session.get('user_id', None)) <= 0:
                socketio.emit('response', {'error': "Votre solde est insuffisant pour continuer."}, room=request.sid)
                return

            assistants = openai_client.beta.assistants.list()
            openai_assistant_id = str(assistants.data[0].id)

            openai_client.beta.assistants.retrieve(assistant_id=openai_assistant_id)

            new_thread = None
            if thread_id:
                try:
                    new_thread = openai_client.beta.threads.retrieve(thread_id=thread_id)
                except Exception as e:
                    socketio.emit('response', {'error': f"Thread ID not found: {str(e)}"}, room=request.sid)
                    return
            else:
                new_thread = openai_client.beta.threads.create()
                session['thread_id'] = new_thread.id

            socketio.emit('response', {'thread_id': f"{new_thread.id}"}, room=request.sid)
            
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
            socketio.emit('response', {'error': f"Une erreur s'est produite: {str(e)}"}, room=request.sid)


@app.route('/jw-image/<doc_id>/<site>')
def jw_image(doc_id, site):
    jw_image_url = f"https://cms-imgp.jw-cdn.org/img/p/{doc_id}/univ/art/{doc_id}_univ_sqs_lg.jpg"

    if doc_id != "null":
        if requests.head(jw_image_url).ok:
            return redirect(jw_image_url)
    
    if site == "wol":
        return redirect("/static/img/wol.png")
    return redirect("/static/img/jw.png")


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True, port=int(os.getenv("PORT", default=5000)))
