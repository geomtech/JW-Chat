import time
from bson import ObjectId
from flask import session
from pymongo import MongoClient
from app import MONGODB_URL
from utils import db
from openai.types.beta.threads.runs.run_step import Usage
import math

client = MongoClient(MONGODB_URL)
db = client['jw_chat']
usage_collection = db['usage']
users_collection = db['users']
payments_collection = db['payments']


def addUsage(tokens_count, usage_type: str):
    """
    Add a usage to the database for the given user.
    """
    user_id = session.get("user_id", None)
    
    cost = calculate_cost_from_usage(tokens_count, usage_type)
    
    usage = {
        "user_id": ObjectId(user_id),
        "cost": cost,
        "tokens": tokens_count,
        "usage_type": usage_type,
        "timestamp": int(time.time())
    }

    usage_collection.insert_one(usage)


def calculate_cost_from_usage(tokens_count: int, usage_type: str = "default") -> float:
    """
    Calcule le coût d'utilisation de gpt-4o-mini basé sur les tokens utilisés.

    Args:
        usage (Usage): Une instance de la classe Usage avec les tokens utilisés.
        usage_type (str): Type d'utilisation ('processing', 'cache', ou 'training').

    Returns:
        float: Coût total en dollars.
    """
    # Prix par 1M tokens pour gpt-4o-mini
    prices = {
        'completion': 0.15,  # $0.15 par 1M tokens
        'cache': 0.075,      # $0.075 par 1M tokens
        'prompt': 0.60,     # $0.60 par 1M tokens
        'default': 0.30,     # $0.30 par 1M tokens
    }

    if usage_type not in prices:
        raise ValueError(
            "Type d'utilisation invalide. Choisir entre 'processing', 'cache', ou 'training'.")

    # Calcul du coût par 1M tokens
    cost_per_million = prices[usage_type]
    cost = (tokens_count / 1_000_000) * cost_per_million

    return cost


def balance_for_user(user_id: str):
    if user_id:
        user_found = users_collection.find_one({'_id': ObjectId(user_id)})
        if user_found:
            payments = list(payments_collection.find({'user_id': user_found['_id']}))
            balance = sum([payment['amount'] for payment in payments])

            usage = list(usage_collection.find({'user_id': user_found['_id']}))
            usage = math.fsum([u['cost'] for u in usage])

            # add TVA to usage
            usage = usage * 1.2

            # add fees to usage of 25%
            usage = usage * 1.25

            # add margin of 10%
            usage = usage * 1.1

            balance -= usage

            balance = round(balance, 2)

            return balance
    return 0
