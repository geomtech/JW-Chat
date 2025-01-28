import math
from bson import ObjectId
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
import stripe
import os

from utils import costs

accounts_bp = Blueprint('accounts', __name__, template_folder='templates')

stripe.api_key = os.getenv('STRIPE_API_KEY')

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGODB_URL)
db = client['jw_chat']
users_collection = db['users']
payments_collection = db['payments']
usage_collection = db['usage']
prices_collection = db['prices']

@accounts_bp.route('/account', methods=['GET'])
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_from_session()  # Function to get user from session
    prices = prices_collection.find({})
    return render_template('account.html', user=user, prices=prices)

@accounts_bp.route('/checkout/<amount>', methods=['GET'])
def checkout(amount):
    return render_template('checkout.html', amount=amount)

@accounts_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    price_id = ""
    amount = int(request.json['amount'])

    prices = prices_collection.find({})

    for price in prices:
        if price['amount'] == amount:
            price_id = price['price_id']
            break
    
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
    try:
        stripe_session = stripe.checkout.Session.retrieve(request.args.get('session_id'))

        print(stripe_session.payment_status)
        if stripe_session.payment_status == 'paid':
            if not payments_collection.find_one({'payment_id': request.args.get('session_id')}):
                payments_collection.insert_one({
                    'user_id': ObjectId(session.get('user_id')),
                    'amount': stripe_session.amount_total / 100,
                    'payment_method': stripe_session.payment_method_types[0],
                    'payment_status': stripe_session.payment_status,
                    'payment_id': request.args.get('session_id')
                })

        return jsonify(status=stripe_session.status, customer_email=stripe_session.customer_details.email)
    except:
        return jsonify(status='failed')


@accounts_bp.route('/return', methods=['GET'])
def return_page():
    return render_template('return.html')


@accounts_bp.route('/<amount>/checkout.js', methods=['GET'])
def checkout_js(amount):
    stripe_public_key = os.getenv('STRIPE_PUBLIC_KEY', None)
    if not stripe_public_key:
        return 'Error: Stripe public key not set', 400
    print(stripe_public_key)
    return render_template('checkout.js', amount=amount, stripe_public_key=stripe_public_key)


@accounts_bp.route('/api/v1/balance', methods=['GET'])
def balance():
    user = get_user_from_session()
    if user:
        balance = costs.balance_for_user(user['_id'])

        return jsonify(balance=balance)
    return jsonify(balance=0)


def get_user_from_session():
    # Function to retrieve user from session
    user_id = session.get('user_id')
    if user_id:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        return user
    return None