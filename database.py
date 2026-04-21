import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["quantum_voting"]

# ─── Collections ────────────────────────────────────────────
users_col         = db["users"]
pending_users_col = db["pending_users"]
votes_col         = db["votes"]
valid_voters_col  = db["valid_voters"]
admin_keys_col    = db["admin_keys"]
candidates_col    = db["candidates"]
queries_col       = db["queries"]

# ============================================================
# USERS
# ============================================================
def get_user(username):
    doc = users_col.find_one({"username": username})
    if doc:
        return {k: v for k, v in doc.items() if k not in ("_id", "username")}
    return None

def user_exists(username):
    return users_col.find_one({"username": username}) is not None

def vote_id_taken(vote_id):
    return users_col.find_one({"vote_id": vote_id}) is not None

def save_user(username, data):
    users_col.update_one(
        {"username": username},
        {"$set": {**data, "username": username}},
        upsert=True
    )

def get_all_users():
    return list(users_col.find({}, {"_id": 0}))

def delete_user(username):
    users_col.delete_one({"username": username})

# ============================================================
# PENDING USERS
# ============================================================
def save_pending_user(username, data):
    pending_users_col.update_one(
        {"username": username},
        {"$set": {**data, "username": username}},
        upsert=True
    )

def get_pending_users():
    return list(pending_users_col.find({}, {"_id": 0}))

def approve_user(username):
    doc = pending_users_col.find_one({"username": username})
    if doc:
        doc.pop("_id", None)
        doc["status"] = "approved"
        users_col.insert_one(doc)
        pending_users_col.delete_one({"username": username})

def delete_pending_user(username):
    pending_users_col.delete_one({"username": username})

# ============================================================
# VOTES
# ============================================================
def get_votes():
    return {doc["vote_id"]: {"candidate": doc["candidate"]}
            for doc in votes_col.find()}

def save_vote(vote_id, candidate):
    votes_col.update_one(
        {"vote_id": vote_id},
        {"$set": {"vote_id": vote_id, "candidate": candidate}},
        upsert=True
    )

def get_vote_counts():
    """Returns {candidate_name: count} for all cast votes."""
    pipeline = [
        {"$group": {"_id": "$candidate", "count": {"$sum": 1}}}
    ]
    result = {}
    for doc in votes_col.aggregate(pipeline):
        result[doc["_id"]] = doc["count"]
    return result

def total_votes_cast():
    return votes_col.count_documents({})

# ============================================================
# VALID VOTERS
# ============================================================
def get_valid_voter(vote_id):
    doc = valid_voters_col.find_one({"vote_id": vote_id})
    if doc:
        return {"name": doc["name"], "voted": doc["voted"]}
    return None

def add_valid_voter(vote_id, name):
    """Admin adds a real voter to the roll."""
    valid_voters_col.update_one(
        {"vote_id": vote_id},
        {"$setOnInsert": {"vote_id": vote_id, "name": name, "voted": False}},
        upsert=True
    )

def remove_valid_voter(vote_id):
    valid_voters_col.delete_one({"vote_id": vote_id})

def mark_voter_registered(vote_id):
    valid_voters_col.update_one({"vote_id": vote_id}, {"$set": {"voted": False}})

def mark_voted(vote_id):
    valid_voters_col.update_one({"vote_id": vote_id}, {"$set": {"voted": True}})

def get_all_valid_voters():
    return list(valid_voters_col.find({}, {"_id": 0}))

def total_eligible_voters():
    return valid_voters_col.count_documents({})

def total_voted():
    return valid_voters_col.count_documents({"voted": True})

# ============================================================
# CANDIDATES
# ============================================================
def get_candidates():
    return list(candidates_col.find({}, {"_id": 0}))

def get_candidate_names():
    return [doc["name"] for doc in candidates_col.find()]

def add_candidate(name, party, symbol):
    if candidates_col.find_one({"name": name}):
        return False  # already exists
    candidates_col.insert_one({"name": name, "party": party, "symbol": symbol})
    return True

def remove_candidate(name):
    candidates_col.delete_one({"name": name})

def candidate_count():
    return candidates_col.count_documents({})

# ============================================================
# ADMIN KEYS
# ============================================================
def admin_key_valid(key):
    return admin_keys_col.find_one({"key": key}) is not None

def add_admin_key(key):
    admin_keys_col.update_one({"key": key}, {"$set": {"key": key}}, upsert=True)

# ============================================================
# QUERIES
# ============================================================
def get_queries():
    return list(queries_col.find({}, {"_id": 1, "user": 1, "question": 1, "reply": 1, "created_at": 1}))

def save_query(user, question):
    from datetime import datetime
    queries_col.insert_one({
        "user": user,
        "question": question,
        "reply": "Pending",
        "created_at": datetime.utcnow()
    })

def reply_query(query_id, reply_text):
    from bson import ObjectId
    queries_col.update_one(
        {"_id": ObjectId(query_id)},
        {"$set": {"reply": reply_text}}
    )