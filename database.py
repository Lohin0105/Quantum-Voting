import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

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
settings_col      = db["settings"]
activity_log_col  = db["activity_log"]
receipts_col      = db["receipts"]
polls_col         = db["polls"]
poll_votes_col    = db["poll_votes"]
poll_candidates_col = db["poll_candidates"]

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
        {"$set": {"vote_id": vote_id, "candidate": candidate, "timestamp": datetime.utcnow()}},
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
        return False
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

# ============================================================
# SETTINGS (Election end time, winner announced)
# ============================================================
def get_setting(key, default=None):
    doc = settings_col.find_one({"key": key})
    return doc["value"] if doc else default

def set_setting(key, value):
    settings_col.update_one(
        {"key": key},
        {"$set": {"key": key, "value": value}},
        upsert=True
    )

def get_election_end_time():
    """Returns datetime or None."""
    return get_setting("election_end_time", None)

def set_election_end_time(dt):
    set_setting("election_end_time", dt)

def get_winner_announced():
    return get_setting("winner_announced", False)

def set_winner_announced(val):
    set_setting("winner_announced", val)

# ============================================================
# ACTIVITY LOG (Suspicious IP tracking)
# ============================================================
def log_activity(voter_id, ip, action):
    activity_log_col.insert_one({
        "voter_id": voter_id,
        "ip": ip,
        "action": action,
        "timestamp": datetime.utcnow()
    })

def get_suspicious_ips():
    """Returns list of IPs that appear with more than one voter_id."""
    pipeline = [
        {"$match": {"action": "vote"}},
        {"$group": {"_id": "$ip", "voter_ids": {"$addToSet": "$voter_id"}, "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    return list(activity_log_col.aggregate(pipeline))

def get_all_activity():
    return list(activity_log_col.find({}, {"_id": 0}).sort("timestamp", -1).limit(200))

# ============================================================
# VOTE RECEIPTS
# ============================================================
def save_receipt(voter_id, poll_id, receipt_hash):
    receipts_col.update_one(
        {"voter_id": voter_id, "poll_id": poll_id},
        {"$set": {"voter_id": voter_id, "poll_id": poll_id, "receipt": receipt_hash, "issued_at": datetime.utcnow()}},
        upsert=True
    )

def get_receipt(voter_id, poll_id):
    doc = receipts_col.find_one({"voter_id": voter_id, "poll_id": poll_id})
    return doc["receipt"] if doc else None


# ============================================================
# POLLS
# ============================================================
def create_poll(name, description, start_time, end_time, created_by):
    import uuid
    poll_id = str(uuid.uuid4())[:8].upper()
    polls_col.insert_one({
        "poll_id": poll_id, "name": name, "description": description,
        "start_time": start_time, "end_time": end_time,
        "created_by": created_by, "email_sent": False,
        "results_announced": False,
        "created_at": datetime.utcnow()
    })
    return poll_id

def get_all_polls():
    return list(polls_col.find({}, {"_id": 0}).sort("created_at", -1))

def get_poll(poll_id):
    return polls_col.find_one({"poll_id": poll_id}, {"_id": 0})

def delete_poll(poll_id):
    polls_col.delete_one({"poll_id": poll_id})
    poll_candidates_col.delete_many({"poll_id": poll_id})
    poll_votes_col.delete_many({"poll_id": poll_id})

def mark_poll_email_sent(poll_id):
    polls_col.update_one({"poll_id": poll_id}, {"$set": {"email_sent": True}})

def get_active_poll():
    now = datetime.now()
    return polls_col.find_one(
        {"start_time": {"$lte": now}, "end_time": {"$gte": now}},
        {"_id": 0}
    )

def get_all_active_polls():
    now = datetime.now()
    return list(polls_col.find(
        {"start_time": {"$lte": now}, "end_time": {"$gte": now}},
        {"_id": 0}
    ).sort("start_time", -1))

def get_past_polls():
    now = datetime.now()
    return list(polls_col.find(
        {"end_time": {"$lt": now}},
        {"_id": 0}
    ).sort("end_time", -1))

def get_ended_unannounced_polls():
    now = datetime.now()
    return list(polls_col.find(
        {"end_time": {"$lt": now}, "results_announced": {"$ne": True}},
        {"_id": 0}
    ))

def mark_poll_results_announced(poll_id):
    polls_col.update_one({"poll_id": poll_id}, {"$set": {"results_announced": True}})

def get_past_polls_for_voter(voter_id):
    pipeline = [
        {"$match": {"vote_id": voter_id}},
        {"$lookup": {
            "from": "polls",
            "localField": "poll_id",
            "foreignField": "poll_id",
            "as": "poll_info"
        }},
        {"$unwind": "$poll_info"},
        {"$project": {
            "_id": 0,
            "poll_id": 1,
            "candidate": 1,
            "timestamp": 1,
            "poll_name": "$poll_info.name",
            "end_time": "$poll_info.end_time",
            "start_time": "$poll_info.start_time"
        }},
        {"$sort": {"timestamp": -1}}
    ]
    return list(poll_votes_col.aggregate(pipeline))

def get_upcoming_poll():
    now = datetime.now()
    return polls_col.find_one(
        {"start_time": {"$gt": now}}, {"_id": 0},
        sort=[("start_time", 1)]
    )

def get_all_upcoming_polls():
    now = datetime.now()
    return list(polls_col.find(
        {"start_time": {"$gt": now}}, {"_id": 0}
    ).sort("start_time", 1))


# ============================================================
# POLL CANDIDATES (with AI symbol images)
# ============================================================
def add_poll_candidate(poll_id, name, party, symbol_name, symbol_image_b64=""):
    if poll_candidates_col.find_one({"poll_id": poll_id, "name": name}):
        return False
    poll_candidates_col.insert_one({
        "poll_id": poll_id, "name": name, "party": party,
        "symbol": symbol_name, "symbol_image_b64": symbol_image_b64,
        "added_at": datetime.utcnow()
    })
    return True

def get_poll_candidates(poll_id):
    return list(poll_candidates_col.find({"poll_id": poll_id}, {"_id": 0}))

def remove_poll_candidate(poll_id, name):
    poll_candidates_col.delete_one({"poll_id": poll_id, "name": name})

def update_poll_candidate_image(poll_id, name, image_b64):
    poll_candidates_col.update_one(
        {"poll_id": poll_id, "name": name},
        {"$set": {"symbol_image_b64": image_b64}}
    )


# ============================================================
# POLL VOTES
# ============================================================
def save_poll_vote(poll_id, vote_id, candidate):
    poll_votes_col.update_one(
        {"poll_id": poll_id, "vote_id": vote_id},
        {"$set": {"poll_id": poll_id, "vote_id": vote_id,
                  "candidate": candidate, "timestamp": datetime.utcnow()}},
        upsert=True
    )

def has_voted_in_poll(poll_id, vote_id):
    return poll_votes_col.find_one({"poll_id": poll_id, "vote_id": vote_id}) is not None

def get_poll_vote_record(poll_id, vote_id):
    return poll_votes_col.find_one({"poll_id": poll_id, "vote_id": vote_id}, {"_id": 0})
def get_poll_vote_counts(poll_id):
    pipeline = [
        {"$match": {"poll_id": poll_id}},
        {"$group": {"_id": "$candidate", "count": {"$sum": 1}}}
    ]
    result = {}
    for doc in poll_votes_col.aggregate(pipeline):
        result[doc["_id"]] = doc["count"]
    return result

def total_poll_votes(poll_id):
    return poll_votes_col.count_documents({"poll_id": poll_id})