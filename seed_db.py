"""
seed_db.py — Run ONCE to migrate all JSON data into MongoDB Atlas.
Usage:  python seed_db.py
"""
import json, os
from database import (
    users_col, votes_col, valid_voters_col,
    admin_keys_col, queries_col
)

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

# ── Clear existing collections (fresh seed) ──────────────────
print("Clearing existing collections...")
users_col.delete_many({})
votes_col.delete_many({})
valid_voters_col.delete_many({})
admin_keys_col.delete_many({})
queries_col.delete_many({})

# ── Users ─────────────────────────────────────────────────────
users = load_json("users.json") or {}
if users:
    docs = [{"username": k, **v} for k, v in users.items()]
    users_col.insert_many(docs)
    print(f"  ✅ Inserted {len(docs)} users")

# ── Votes ─────────────────────────────────────────────────────
votes = load_json("votes.json") or {}
if votes:
    docs = [{"vote_id": k, **v} for k, v in votes.items()]
    votes_col.insert_many(docs)
    print(f"  ✅ Inserted {len(docs)} votes")

# ── Valid Voters ───────────────────────────────────────────────
valid_voters = load_json("valid_voters.json") or {}
if valid_voters:
    docs = [{"vote_id": k, **v} for k, v in valid_voters.items()]
    valid_voters_col.insert_many(docs)
    print(f"  ✅ Inserted {len(docs)} valid voters")

# ── Admin Keys ─────────────────────────────────────────────────
admin_keys = load_json("admin_keys.json") or []
if admin_keys:
    docs = [{"key": k} for k in admin_keys]
    admin_keys_col.insert_many(docs)
    print(f"  ✅ Inserted {len(docs)} admin keys")

# ── Queries ────────────────────────────────────────────────────
queries = load_json("queries.json") or {}
if queries:
    from datetime import datetime
    docs = [
        {
            "user": v["user"],
            "question": v["question"],
            "reply": v.get("reply", "Pending"),
            "created_at": datetime.utcnow()
        }
        for v in queries.values()
    ]
    queries_col.insert_many(docs)
    print(f"  ✅ Inserted {len(docs)} queries")

print("\n🎉 Migration complete! All JSON data is now in MongoDB Atlas.")
