from flask import Blueprint, render_template, request, redirect, session
from bson.objectid import ObjectId
from pymongo import MongoClient
import time
import os

admin_bp = Blueprint('admin', __name__, template_folder='templates')

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGODB_URL)
db = client['jw_chat']
users_collection = db['users']
usage_collection = db['usage']
payments_collection = db['payments']

@admin_bp.route('/admin', methods=['GET', 'POST'])
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
    return render_template('admin/admin.html', pending_users=pending_users)

@admin_bp.route('/admin/user/<user_id>', methods=['GET'])
def user_details(user_id):
    if 'is_logged' not in session:
        return redirect('/auth')

    user = users_collection.find_one({"_id": ObjectId(session['user_id'])})
    if not user or not user.get('is_admin', False):
        return "Accès refusé."

    user_details = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user_details:
        return "Utilisateur non trouvé."

    payments = list(payments_collection.find({'user_id': ObjectId(user_id)}))
    usage = list(usage_collection.find({'user_id': ObjectId(user_id)}))

    balance = sum([payment['amount'] for payment in payments])
    total_usage = sum([u['cost'] for u in usage])

    balance -= total_usage

    return render_template('admin/user_details.html', user=user_details, payments=payments, usage=usage, balance=balance, total_usage=total_usage)


@admin_bp.route('/admin/user/<user_id>/credit', methods=['GET', 'POST'])
def credit_user(user_id):
    if 'is_logged' not in session:
        return redirect('/auth')

    user = users_collection.find_one({"_id": ObjectId(session['user_id'])})
    if not user or not user.get('is_admin', False):
        return "Accès refusé."

    amount = request.form['amount']
    payments_collection.insert_one({
        "user_id": ObjectId(user_id),
        "amount": float(amount),
        "timestamp": int(time.time())
    })

    return redirect(f'/admin/user/{user_id}')


@admin_bp.route('/admin/users')
def users_list():
    if 'is_logged' not in session:
        return redirect('/auth')

    user = users_collection.find_one({"_id": ObjectId(session['user_id'])})
    if not user or not user.get('is_admin', False):
        return "Accès refusé."

    users = users_collection.find()
    return render_template('admin/users_list.html', users=users)