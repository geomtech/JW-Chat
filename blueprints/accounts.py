from bson import ObjectId
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
import stripe
import os

accounts_bp = Blueprint('accounts', __name__, template_folder='templates')

stripe.api_key = os.getenv('STRIPE_API_KEY')

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGODB_URL)
db = client['jw_chat']
users_collection = db['users']

@accounts_bp.route('/account', methods=['GET'])
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_from_session()  # Function to get user from session
    return render_template('account.html', user=user)

@accounts_bp.route('/checkout/<amount>', methods=['GET'])
def checkout(amount):
    return render_template('checkout.html', amount=amount)

@accounts_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    price_id = ""
    amount = int(request.json['amount'])

    print(amount)

    if amount == 5:
        price_id = 'price_1Qm24oF1FXlcWZG7onkeYkyb'
    elif amount == 10:
        price_id = 'price_1Qm27AF1FXlcWZG7Ta6jOkhP'
    elif amount == 20:
        price_id = 'price_1Qm27AF1FXlcWZG7LUYfFcI9'
    
    try:
        session = stripe.checkout.Session.create(
            ui_mode = 'embedded',
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='payment',
            return_url=request.url_root + 'return?session_id={CHECKOUT_SESSION_ID}',
        )
    except Exception as e:
        return str(e)

    return jsonify(clientSecret=session.client_secret)


@accounts_bp.route('/session-status', methods=['GET'])
def session_status():
    session = stripe.checkout.Session.retrieve(request.args.get('session_id'))

    return jsonify(status=session.status, customer_email=session.customer_details.email)


@accounts_bp.route('/return', methods=['GET'])
def return_page():
    return render_template('return.html')


@accounts_bp.route('/<amount>/checkout.js', methods=['GET'])
def checkout_js(amount):
    return render_template('checkout.js', amount=amount)


def get_user_from_session():
    # Function to retrieve user from session
    user_id = session.get('user_id')
    if user_id:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        return user
    return None