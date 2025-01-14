from pymongo import MongoClient

def get_db():
    client = MongoClient(os.environ.get("MONGODB_URL", "mongodb://localhost:27017/"))
    db = client['jw_chat']
    return db

def get_users_collection():
    db = get_db()
    return db['users']
