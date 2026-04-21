"""
setup.py — Run ONCE to initialise the system.
Only seeds the admin secret keys needed to create the first admin account.
NO voter data, NO candidates — all managed via the Admin Console.

Usage:  python setup.py
"""
import json, os
from database import add_admin_key, add_valid_voter, mark_voted

# ── Add your secret admin key(s) here ─────────────────────
# Share these ONLY with trusted admins. They use this key to register.
ADMIN_KEYS = [
    "QVOTE-ADMIN-2025",   # change/add your own secure keys
]

for key in ADMIN_KEYS:
    add_admin_key(key)
    print(f"  ✅ Admin key seeded: {key}")

if os.path.exists('valid_voters.json'):
    try:
        with open('valid_voters.json', 'r') as f:
            data = json.load(f)
            for vid, info in data.items():
                add_valid_voter(vid, info.get("name", "Unknown"))
                if info.get("voted"):
                    mark_voted(vid)
        print("  ✅ Seeded valid_voters.json into MongoDB.")
    except Exception as e:
        print(f"  ❌ Error seeding valid_voters.json: {e}")

print("\n🔐 Setup complete!")
print("   Go to the app → Admin Console → Register Admin")
print(f"   Use key: {ADMIN_KEYS[0]}")
print("\n   Then use the Admin Console to:")
print("   1. Add candidates (Candidates tab)")
print("   2. Add eligible voters (Voter Roll tab)")
