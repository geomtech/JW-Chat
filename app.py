from gevent import monkey
monkey.patch_all()

import os
import time
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, redirect, render_template, request, session
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from pymongo import MongoClient
from bson.objectid import ObjectId

from openai import OpenAI

from utils import eventhandler, email, db
from utils.email import send_admin_notification

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
bcrypt = Bcrypt(app)
mail = Mail(app)

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017/")
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "your_brevo_api_key")

client = MongoClient(MONGODB_URL)
db = client['jw_chat']
users_collection = db['users']

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "sk-proj..."))
openai_assistant_id = ""

@app.route('/auth', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({"email": email})

        if os.environ.get("local", "") == "adacruz@macbook-alexy":
            session['is_logged'] = True
            session['user_id'] = str(user['_id'])
            session.permanent = True
            return redirect('/')

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

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'is_logged' not in session:
        return redirect('/auth')

    user = users_collection.find_one({"_id": ObjectId(session['user_id'])})
    if not user or not user.get('is_admin', False):
        return "Accès refusé."

    if request.method == 'POST':
        user_id = request.form['user_id']
        users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_active": True, "validation_date": time.strftime('%Y-%m-%d %H:%M:%S')}})
        return redirect('/admin')

    pending_users = users_collection.find({"is_active": False})
    return render_template('admin.html', pending_users=pending_users)

@app.route('/data-privacy', methods=['GET'])
def data_privacy():
    return render_template('data-privacy.html')

@app.route('/')
def index():
    if 'is_logged' not in session:
        return redirect('/auth')
    
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/auth')


@socketio.on('ask_openai')
def handle_ask_openai(data):
    if 'is_logged' not in session:
        socketio.emit('response', {'message': f"Vous n'êtes pas connecté"})
    else:
        try:
            prompt = data.get("user_input")
            thread_id = session.get("thread_id", None)

            assistants = openai_client.beta.assistants.list()
            openai_assistant_id = str(assistants.data[0].id)

            openai_client.beta.assistants.retrieve(assistant_id=openai_assistant_id)

            new_thread = None
            if thread_id:
                try:
                    new_thread = openai_client.beta.threads.retrieve(thread_id=thread_id)
                except Exception as e:
                    socketio.emit('response', {'error': f"Thread ID not found: {str(e)}"})
                    return
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
