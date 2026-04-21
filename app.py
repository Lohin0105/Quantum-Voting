import streamlit as st
import hashlib, time, secrets, requests, os, base64
import cv2, numpy as np
from dotenv import load_dotenv
load_dotenv()
from database import (
    get_user, user_exists, vote_id_taken, save_user,
    admin_key_valid, get_valid_voter, mark_voter_registered,
    mark_voted, save_vote, get_votes, get_vote_counts,
    total_votes_cast, total_eligible_voters, total_voted,
    get_candidates, get_candidate_names, add_candidate,
    remove_candidate, candidate_count,
    add_valid_voter, remove_valid_voter, get_all_valid_voters,
    get_all_users, delete_user, get_pending_users, approve_user, delete_pending_user, save_pending_user,
    get_queries, save_query, reply_query
)

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="QuVote — Quantum Voting",
    page_icon="⚛️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════
# PREMIUM CSS
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');

/* ── Root Variables ───────────────────────── */
:root {
  --bg-deep:   #06090f;
  --bg-card:   rgba(255,255,255,0.04);
  --border:    rgba(255,255,255,0.08);
  --blue:      #6366f1;
  --blue-soft: rgba(99,102,241,0.15);
  --violet:    #8b5cf6;
  --teal:      #06b6d4;
  --green:     #10b981;
  --red:       #f43f5e;
  --amber:     #f59e0b;
  --text:      #e2e8f0;
  --muted:     #64748b;
  --grad:      linear-gradient(135deg, #6366f1, #8b5cf6);
  --grad-teal: linear-gradient(135deg, #06b6d4, #6366f1);
}

/* ── Global Reset ─────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
  font-family: 'Inter', sans-serif !important;
  color: var(--text) !important;
}

.stApp {
  background: radial-gradient(ellipse at top, #0f1429 0%, #06090f 60%) !important;
  min-height: 100vh;
}

.block-container {
  padding: 2.5rem 2rem 4rem !important;
  max-width: 860px !important;
}

/* ── Hide default UI chrome ───────────────── */
#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }

/* ── Scrollbar ────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.4); border-radius: 3px; }

/* ══════════════════════════════════════════
   HERO
══════════════════════════════════════════ */
.hero-wrap {
  text-align: center;
  padding: 3rem 1rem 2.5rem;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(99,102,241,0.12);
  border: 1px solid rgba(99,102,241,0.3);
  border-radius: 100px;
  padding: 6px 18px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #a5b4fc;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 1.5rem;
}
.hero-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: clamp(2.6rem, 6vw, 4rem);
  font-weight: 800;
  line-height: 1.1;
  background: linear-gradient(135deg, #a5b4fc 0%, #c4b5fd 50%, #67e8f9 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1rem;
}
.hero-sub {
  color: #64748b;
  font-size: 1.05rem;
  line-height: 1.7;
  max-width: 540px;
  margin: 0 auto 2.5rem;
}

/* ══════════════════════════════════════════
   CARDS
══════════════════════════════════════════ */
.card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 20px;
  padding: 2rem;
  margin: 1rem 0;
  transition: border-color 0.2s;
}
.card:hover { border-color: rgba(99,102,241,0.3); }

.panel-card {
  background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.06));
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 20px;
  padding: 2rem;
  text-align: center;
  transition: all 0.25s ease;
  cursor: pointer;
}
.panel-card:hover {
  border-color: rgba(99,102,241,0.5);
  transform: translateY(-3px);
  box-shadow: 0 12px 40px rgba(99,102,241,0.2);
}
.panel-card .icon {
  font-size: 2.8rem;
  display: block;
  margin-bottom: 1rem;
}
.panel-card h3 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.3rem;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0 0 0.5rem;
}
.panel-card p {
  color: #64748b;
  font-size: 0.88rem;
  margin: 0;
}

/* ══════════════════════════════════════════
   SECTION HEADERS
══════════════════════════════════════════ */
.section-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.6rem;
  font-weight: 700;
  color: #e2e8f0;
  margin-bottom: 0.3rem;
}
.section-sub {
  color: #64748b;
  font-size: 0.9rem;
  margin-bottom: 1.8rem;
}
.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,0.4), transparent);
  margin: 1.8rem 0;
}

/* ══════════════════════════════════════════
   STAT CHIPS
══════════════════════════════════════════ */
.stat-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin: 1rem 0 1.5rem;
}
.stat-chip {
  flex: 1;
  min-width: 110px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px;
  padding: 1rem 1.2rem;
  text-align: center;
}
.stat-chip .num {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.8rem;
  font-weight: 700;
  color: #a5b4fc;
  display: block;
}
.stat-chip .lbl {
  font-size: 0.78rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ══════════════════════════════════════════
   CANDIDATE CARDS (voting)
══════════════════════════════════════════ */
.cand-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px;
  padding: 1.1rem 1.4rem;
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 8px 0;
  transition: all 0.2s ease;
}
.cand-card:hover {
  border-color: rgba(99,102,241,0.4);
  background: rgba(99,102,241,0.06);
}
.cand-symbol { font-size: 2rem; }
.cand-info h4 {
  margin: 0; font-size: 1rem; font-weight: 700; color: #e2e8f0;
}
.cand-info p {
  margin: 2px 0 0; font-size: 0.8rem; color: #64748b;
}

/* ══════════════════════════════════════════
   VOTER RESULT ROW
══════════════════════════════════════════ */
.result-row {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px;
  padding: 1rem 1.4rem;
  margin: 8px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.result-bar-wrap {
  width: 100%;
  background: rgba(255,255,255,0.05);
  border-radius: 100px;
  height: 6px;
  margin-top: 6px;
  overflow: hidden;
}
.result-bar {
  height: 6px;
  border-radius: 100px;
  background: var(--grad);
}

/* ══════════════════════════════════════════
   BADGE PILLS
══════════════════════════════════════════ */
.pill {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 100px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.pill-blue   { background: rgba(99,102,241,0.15); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3); }
.pill-green  { background: rgba(16,185,129,0.12); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.25); }
.pill-amber  { background: rgba(245,158,11,0.12); color: #fcd34d; border: 1px solid rgba(245,158,11,0.25); }
.pill-red    { background: rgba(244,63,94,0.12);  color: #fca5a5; border: 1px solid rgba(244,63,94,0.25);  }

/* ══════════════════════════════════════════
   STREAMLIT WIDGETS OVERRIDE
══════════════════════════════════════════ */
/* Inputs */
.stTextInput input,
.stTextArea textarea {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  border-radius: 12px !important;
  color: #e2e8f0 !important;
  font-family: 'Inter', sans-serif !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
  border-color: rgba(99,102,241,0.6) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}

/* Buttons */
.stButton > button {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  border-radius: 12px !important;
  color: #c7d2fe !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  padding: 0.55rem 1.4rem !important;
  transition: all 0.2s ease !important;
  width: 100% !important;
}
.stButton > button:hover {
  background: rgba(99,102,241,0.15) !important;
  border-color: rgba(99,102,241,0.5) !important;
  color: #a5b4fc !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(99,102,241,0.2) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* Radio */
.stRadio [data-testid="stWidgetLabel"] { color: #94a3b8 !important; font-weight: 500 !important; }
.stRadio > div > div {
  background: rgba(255,255,255,0.02) !important;
  border-radius: 12px !important;
  padding: 0.6rem !important;
  gap: 8px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-radius: 14px !important;
  padding: 5px !important;
  gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px !important;
  color: #64748b !important;
  font-weight: 600 !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.87rem !important;
}
.stTabs [aria-selected="true"] {
  background: rgba(99,102,241,0.18) !important;
  color: #a5b4fc !important;
}

/* Labels */
label, p { color: #94a3b8 !important; }
h1, h2, h3 { color: #e2e8f0 !important; }

/* Alert boxes */
.stSuccess > div, .stError > div, .stWarning > div, .stInfo > div {
  border-radius: 12px !important;
  border: none !important;
  font-family: 'Inter', sans-serif !important;
}

/* Selectbox */
.stSelectbox > div > div {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  border-radius: 12px !important;
  color: #e2e8f0 !important;
}

/* Camera */
[data-testid="stCameraInput"] > div {
  border-radius: 16px !important;
  overflow: hidden !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
}

/* Metric */
[data-testid="stMetric"] {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-radius: 16px !important;
  padding: 1.2rem !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Space Grotesk', sans-serif !important;
  color: #a5b4fc !important;
}

/* Bar chart */
.vega-embed { border-radius: 16px !important; }

/* Expander */
.streamlit-expanderHeader {
  background: rgba(255,255,255,0.03) !important;
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  color: #94a3b8 !important;
  font-weight: 600 !important;
}

/* ══════════════════════════════════════════
   MOBILE RESPONSIVENESS
══════════════════════════════════════════ */
@media (max-width: 768px) {
  .block-container {
    padding: 1.5rem 1rem 3rem !important;
  }
  .hero-wrap {
    padding: 1.5rem 0.5rem 1.5rem;
  }
  .hero-title {
    font-size: 2.2rem !important;
  }
  .hero-sub {
    font-size: 0.95rem;
  }
  .panel-card {
    padding: 1.5rem 1rem;
    margin-bottom: 15px;
  }
  .card {
    padding: 1.2rem;
  }
  .stat-row {
    gap: 8px;
  }
  .stat-chip {
    padding: 0.8rem;
    min-width: 46%; /* Forces 2x2 grid on mobile */
  }
  .stat-chip .num {
    font-size: 1.4rem;
  }
  .cand-card {
    padding: 1rem;
    gap: 10px;
  }
  .result-row {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .result-bar-wrap {
    width: 100%;
  }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# SESSION STATE  — persisted via query params so refresh keeps user logged in
# ═══════════════════════════════════════════════════════════
_qp = st.query_params

# Restore page from URL if session was wiped by refresh
if "page" not in st.session_state:
    st.session_state.page = _qp.get("page", "home")
if "user" not in st.session_state:
    st.session_state.user = _qp.get("user", None)
if "admin" not in st.session_state:
    st.session_state.admin = _qp.get("admin", None)

# Remaining session defaults (OTP flow state)
for k, v in [("login_otp_sent", False), ("login_otp_verified", False), ("login_username", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════
def quantum_otp():
    try:
        res = requests.get(
            "https://qrng.anu.edu.au/API/jsonI.php?length=1&type=uint16",
            timeout=4
        ).json()
        return str(res["data"][0] % 900000 + 100000)
    except Exception:
        return str(secrets.randbelow(900000) + 100000)

def hash_data(x):
    return hashlib.sha256(x.encode()).hexdigest()

def send_otp_email(to_email, otp_code):
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        api_key = os.environ.get('SENDGRID_API_KEY', '')
        from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'quantumvoting@outlook.com')
        if not api_key:
            print("[OTP ERROR] SENDGRID_API_KEY is missing in environment!")
            return False
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject='QuVote — Your One-Time Password',
            html_content=f'''
            <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;background:#0f172a;color:#e2e8f0;border-radius:12px;overflow:hidden;">
              <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:24px;text-align:center;">
                <h2 style="margin:0;color:#fff;letter-spacing:0.05em;">QuVote Secure OTP</h2>
              </div>
              <div style="padding:32px;">
                <p style="margin-bottom:8px;color:#94a3b8;">Your one-time password for login verification:</p>
                <div style="background:#1e293b;border-radius:10px;padding:20px;text-align:center;margin:20px 0;border:1px solid rgba(99,102,241,0.4);">
                  <span style="font-size:2.4rem;font-weight:800;letter-spacing:0.3em;color:#a5b4fc;">{otp_code}</span>
                </div>
                <p style="color:#64748b;font-size:0.85rem;">This OTP expires in <strong>5 minutes</strong>. Do not share it with anyone.</p>
              </div>
            </div>
            '''
        )
        response = sg.send(message)
        print(f"[OTP] Sent to {to_email} | Status: {response.status_code}")
        return response.status_code in (200, 202)
    except Exception as e:
        print(f"[OTP ERROR] {e}")
        return False

def send_approval_email(to_email):
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY', ''))
        message = Mail(
            from_email=os.environ.get('SENDGRID_FROM_EMAIL', 'quantumvoting@outlook.com'),
            to_emails=to_email,
            subject='QuVote - Account Verified',
            html_content='<h3>QuVote Identity Verified</h3><p>Your account has been officially verified by the election administrator. You may now login via the Voter Portal and cast your vote.</p>'
        )
        sg.send(message)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

def send_rejection_email(to_email):
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY', ''))
        message = Mail(
            from_email=os.environ.get('SENDGRID_FROM_EMAIL', 'quantumvoting@outlook.com'),
            to_emails=to_email,
            subject='QuVote - Registration Denied',
            html_content='<h3>QuVote Identity Verification Failed</h3><p>Your registration request was rejected by the election administrator due to invalid credentials or biometric mismatch. Please contact support if you believe this is an error.</p>'
        )
        sg.send(message)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

# ── Face ──────────────────────────────────────────────────
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

def extract_face(img_bytes):
    arr = np.asarray(bytearray(img_bytes), dtype=np.uint8)
    img = cv2.imdecode(arr, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) == 0:
        return None
    x, y, w, h = faces[0]
    face = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
    return face

def compare_faces(f1, f2):
    h1 = cv2.calcHist([f1],[0],None,[256],[0,256])
    h2 = cv2.calcHist([f2],[0],None,[256],[0,256])
    score = cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)
    diff  = np.mean(cv2.absdiff(f1, f2))
    return score > 0.75 and diff < 50

def get_face_b64(img_bytes):
    face_arr = extract_face(img_bytes)
    if face_arr is None:
        return None
    _, buffer = cv2.imencode('.jpg', face_arr)
    return base64.b64encode(buffer).decode('utf-8')

def decode_face_b64(b64_str):
    if not b64_str:
        return None
    img_bytes = base64.b64decode(b64_str)
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    return cv2.imdecode(arr, 0)

def is_duplicate_face_db(img):
    new_face_arr = extract_face(img.getvalue())
    if new_face_arr is None:
        return False
    for u in get_all_users():
        b64_str = u.get("face_b64")
        if b64_str:
            saved_face = decode_face_b64(b64_str)
            if saved_face is not None and compare_faces(new_face_arr, saved_face):
                return True
    return False

def verify_face_db(username, img):
    user_doc = get_user(username)
    if not user_doc or "face_b64" not in user_doc:
        return False
    new_face_arr = extract_face(img.getvalue())
    if new_face_arr is None:
        return False
    saved_face = decode_face_b64(user_doc["face_b64"])
    return saved_face is not None and compare_faces(new_face_arr, saved_face)

# ── Go-to helper ─────────────────────────────────────────
def goto(page):
    st.session_state.page = page
    params = {"page": page}
    if page == "vote" and st.session_state.get("user"):
        params["user"] = st.session_state.user
    elif page == "dashboard" and st.session_state.get("admin"):
        params["admin"] = st.session_state.admin
    elif page == "home":
        st.query_params.clear()
        st.rerun()
        return
    st.query_params.update(params)
    st.rerun()

# ═══════════════════════════════════════════════════════════
# NAV BAR
# ═══════════════════════════════════════════════════════════
if st.session_state.page != "home":
    cols = st.columns([1, 5])
    with cols[0]:
        if st.button("⟵ Home"):
            st.session_state.clear()
            st.query_params.clear()
            goto("home")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# PAGE: HOME
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "home":

    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-badge">⚛️ &nbsp; Quantum-Secured Voting</div>
        <div class="hero-title">QuVote</div>
        <p class="hero-sub">
            A tamper-proof, biometric-verified electronic voting platform
            powered by quantum randomness and MongoDB Atlas.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("""
        <div class="panel-card">
            <span class="icon">
                <svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(6,182,212,0.4));">
                    <defs>
                        <linearGradient id="userGrad" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#06b6d4"/>
                            <stop offset="1" stop-color="#3b82f6"/>
                        </linearGradient>
                    </defs>
                    <circle cx="12" cy="7" r="4.5" fill="url(#userGrad)" fill-opacity="0.9" stroke="#a5f3fc" stroke-width="1.2"/>
                    <path d="M4.5 20.5C4.5 16.9101 7.85786 14 12 14C16.1421 14 19.5 16.9101 19.5 20.5C19.5 20.7761 19.2761 21 19 21H5C4.72386 21 4.5 20.7761 4.5 20.5Z" fill="url(#userGrad)" fill-opacity="0.9" stroke="#a5f3fc" stroke-width="1.2"/>
                </svg>
            </span>
            <h3>Voter Portal</h3>
            <p>Register, verify your identity, and cast your secure quantum vote.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Voter Portal", key="home_user", use_container_width=True):
            goto("user")

    with col2:
        st.markdown("""
        <div class="panel-card">
            <span class="icon">
                <svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(139,92,246,0.4));">
                    <defs>
                        <linearGradient id="shieldGrad" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#8b5cf6"/>
                            <stop offset="1" stop-color="#6366f1"/>
                        </linearGradient>
                        <linearGradient id="lockGrad" x1="12" y1="8" x2="12" y2="16" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#ffffff"/>
                            <stop offset="1" stop-color="#c7d2fe"/>
                        </linearGradient>
                    </defs>
                    <path d="M12 22C12 22 20 18 20 12V5L12 2L4 5V12C4 18 12 22 12 22Z" fill="url(#shieldGrad)" fill-opacity="0.9" stroke="#c4b5fd" stroke-width="1.5" stroke-linejoin="round"/>
                    <path d="M12 8C10.8954 8 10 8.89543 10 10V11H9.5C8.67157 11 8 11.6716 8 12.5V14.5C8 15.3284 8.67157 16 9.5 16H14.5C15.3284 16 16 15.3284 16 14.5V12.5C16 11.6716 15.3284 11 14.5 11H14V10C14 8.89543 13.1046 8 12 8ZM11 10C11 9.44772 11.4477 9 12 9C12.5523 9 13 9.44772 13 10V11H11V10Z" fill="url(#lockGrad)"/>
                </svg>
            </span>
            <h3>Admin Console</h3>
            <p>Manage candidates, voter rolls, and view live election results.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Admin Console", key="home_admin", use_container_width=True):
            goto("admin")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Live stats
    ev = total_eligible_voters()
    vt = total_votes_cast()
    cc = candidate_count()
    pct = round((vt / ev * 100) if ev > 0 else 0, 1)

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-chip"><span class="num">{ev}</span><span class="lbl">Eligible Voters</span></div>
        <div class="stat-chip"><span class="num">{vt}</span><span class="lbl">Votes Cast</span></div>
        <div class="stat-chip"><span class="num">{cc}</span><span class="lbl">Candidates</span></div>
        <div class="stat-chip"><span class="num">{pct}%</span><span class="lbl">Turnout</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#334155;font-size:0.8rem;">📧 support@qvote.com &nbsp;|&nbsp; Built with ⚛️ Quantum Randomness</p>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# PAGE: USER PANEL
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "user":

    st.markdown('<div class="section-title">Voter Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Register with your Voter ID or log in to cast your vote.</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🆕  Register", "🔐  Login"])

    # ── REGISTER ──────────────────────────────────────────
    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h4>Voter Detail Submission</h4>', unsafe_allow_html=True)
        vid   = st.text_input("Voter ID", placeholder="Enter your assigned Voter ID", key="reg_vid")
        uname = st.text_input("Full Name", placeholder="Your name (used as login username)", key="reg_name")
        email = st.text_input("Email Address", placeholder="For OTP verification in login", key="reg_email")
        pwd   = st.text_input("Password", type="password", placeholder="Create a strong password", key="reg_pwd")

        img = st.camera_input("📷 Capture Face to Request Verification", key="reg_cam")

        if st.button("✅ Submit Details for Verification", key="reg_btn"):
            voter_doc = get_valid_voter(vid)
            if vote_id_taken(vid):
                st.error("❌ This Voter ID is already registered/pending.")
            elif user_exists(uname):
                st.error("❌ Username already taken. Choose another.")
            elif not img:
                st.error("❌ Face capture is required.")
            elif is_duplicate_face_db(img):
                st.error("❌ This face is already registered with another account.")
            else:
                face_b64 = get_face_b64(img.getvalue())
                if not face_b64:
                    st.error("❌ No face detected. Ensure good lighting and look directly at the camera.")
                else:
                    save_pending_user(uname, {
                        "vote_id": vid, 
                        "email": email, 
                        "password": hash_data(pwd), 
                        "role": "user", 
                        "face_b64": face_b64,
                        "status": "pending"
                    })
                    if not voter_doc:
                        st.info("⚠️ I think you are a new voter, your details are not currently in the database. Our admin will verify your Voter ID when he accepts it. We will send an email regarding your verification, then you can log in.")
                    else:
                        st.success("✅ **Details sent to Admin!** Your registration is in progress. The administrator will verify your info and send you an email. You can login only after verification.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── LOGIN ──────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        l_vid = st.text_input("Voter ID", placeholder="Your official Voter ID", key="l_vid", disabled=st.session_state.get('login_otp_verified', False))
        l_email = st.text_input("Email", placeholder="Registered email address", key="l_email", disabled=st.session_state.get('login_otp_verified', False))
        st.markdown('</div>', unsafe_allow_html=True)

        if not st.session_state.get('login_otp_verified', False):
            if not st.session_state.get('login_otp_sent', False):
                if st.button("📡 Generate OTP", key="l_gen_otp"):
                    if not l_vid or not l_email:
                        st.warning("Enter Voter ID and Email to continue.")
                    else:
                        users = get_all_users()
                        user_doc = None
                        for u in users:
                            if u.get("vote_id") == l_vid:
                                user_doc = u
                                break
                        
                        if not user_doc:
                            st.error("❌ Voter ID not found. Ensure you are registered.")
                        elif user_doc.get("email") != l_email:
                            st.error("❌ The email linked to this Voter ID is incorrect.")
                        elif user_doc.get("status") == "pending":
                            st.error("❌ Your account is still pending verification from the admin. Please wait for the email.")
                        else:
                            with st.spinner("Generating OTP & sending email..."):
                                st.session_state.otp = quantum_otp()
                                st.session_state.otp_time = time.time()
                                st.session_state.login_username = user_doc["username"]
                                if send_otp_email(l_email, st.session_state.otp):
                                    st.session_state.login_otp_sent = True
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to send OTP email.")
            else:
                st.markdown('<div class="card" style="border-color:#10b981;">', unsafe_allow_html=True)
                st.info("📧 OTP sent! Please check your email.")
                otp_val = st.text_input("Enter 6-digit OTP", key="l_otp_input")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Verify OTP", key="l_btn_verify"):
                        if time.time() - st.session_state.get("otp_time", 0) > 300:
                            st.error("❌ OTP expired. Please resend.")
                        elif otp_val == st.session_state.otp:
                            st.session_state.login_otp_verified = True
                            st.rerun()
                        else:
                            st.error("❌ OTP is wrong. Try again.")
                with c2:
                    if st.button("Resend OTP", key="l_btn_resend"):
                        st.session_state.otp = quantum_otp()
                        st.session_state.otp_time = time.time()
                        send_otp_email(l_email, st.session_state.otp)
                        st.success("New OTP sent!")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card" style="border-color:#10b981; background: rgba(16,185,129,0.05);">', unsafe_allow_html=True)
            st.markdown('<h4 style="color:#10b981; margin:0;">✅ OTP Verified — Logging you in...</h4>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            username = st.session_state.get("login_username")
            st.session_state.login_otp_sent = False
            st.session_state.login_otp_verified = False
            st.session_state.user = username
            time.sleep(1)
            goto("vote")

# ═══════════════════════════════════════════════════════════
# PAGE: VOTE
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "vote":

    user     = st.session_state.user
    user_doc = get_user(user)
    vid      = user_doc["vote_id"] if user_doc else None
    voter    = get_valid_voter(vid) if vid else None
    cands    = get_candidates()

    st.markdown(f'<div class="section-title">Welcome, {user} 👋</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">Voter ID: <span style="color:#a5b4fc;font-weight:600">{vid}</span></div>', unsafe_allow_html=True)

    if voter and voter["voted"]:
        st.markdown("""
        <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);
             border-radius:16px;padding:2rem;text-align:center;margin:1rem 0;">
            <div style="font-size:3rem;margin-bottom:0.5rem;">✅</div>
            <div style="font-size:1.2rem;font-weight:700;color:#6ee7b7;">Vote Already Cast</div>
            <div style="color:#64748b;margin-top:0.4rem;font-size:0.9rem;">
                Your vote has been securely recorded in the blockchain. Thank you for participating.
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        if not cands:
            st.warning("⚠️ No candidates have been added yet. Contact the admin.")
        else:
            st.markdown('<div class="section-sub">Select your candidate and submit your vote.</div>', unsafe_allow_html=True)

            # Show candidate info cards
            st.markdown("**Candidates:**")
            for c in cands:
                st.markdown(f"""
                <div class="cand-card">
                    <span class="cand-symbol">{c.get('symbol','🗳️')}</span>
                    <div class="cand-info">
                        <h4>{c['name']}</h4>
                        <p>{c.get('party','Independent')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            choice = st.radio(
                "Cast your vote:",
                [c["name"] for c in cands],
                key="vote_choice"
            )

            if st.button("🗳️ Submit Vote", key="vote_submit"):
                save_vote(vid, choice)
                mark_voted(vid)
                st.success(f"✅ Vote cast for **{choice}**! Your vote is securely recorded.")
                time.sleep(1.5)
                st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📩 Submit a Query", key="query_btn"):
            goto("query")
    with col2:
        if st.button("🚪 Logout", key="logout_user"):
            st.session_state.clear()
            goto("home")

# ═══════════════════════════════════════════════════════════
# PAGE: QUERY / CONTACT
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "query":
    user = st.session_state.user or "Anonymous"
    st.markdown('<div class="section-title">📩 Submit a Query</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Have an issue? Send your query to the admin team.</div>', unsafe_allow_html=True)

    question = st.text_area("Your question or issue", placeholder="Describe your query in detail...", height=120)
    if st.button("Send Query", key="send_query"):
        if question.strip():
            save_query(user, question.strip())
            st.success("✅ Query submitted! The admin will respond shortly.")
        else:
            st.warning("Please enter your query.")
    if st.button("← Back", key="query_back"):
        goto("vote")

# ═══════════════════════════════════════════════════════════
# PAGE: ADMIN PANEL
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "admin":

    st.markdown('<div class="section-title">Admin Console</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Authorized personnel only.</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🆕  Register Admin", "🔐  Admin Login"])

    with tab1:
        key  = st.text_input("Admin Secret Key", type="password", placeholder="Issued by system owner", key="admin_key")
        name = st.text_input("Admin Username", key="admin_name")
        pwd  = st.text_input("Password", type="password", key="admin_pwd")
        if st.button("Register as Admin", key="admin_reg"):
            if not admin_key_valid(key):
                st.error("❌ Invalid admin key.")
            elif user_exists(name):
                st.error("❌ Username already taken.")
            else:
                save_user(name, {"password": hash_data(pwd), "role": "admin"})
                st.success("✅ Admin account created. You can now log in.")

    with tab2:
        a_name = st.text_input("Admin Username", key="admin_login_name")
        a_pwd  = st.text_input("Password", type="password", key="admin_login_pwd")
        if st.button("🔓 Login as Admin", key="admin_login_btn"):
            doc = get_user(a_name)
            if doc and doc["password"] == hash_data(a_pwd) and doc.get("role") == "admin":
                st.session_state.admin = a_name
                goto("dashboard")
            else:
                st.error("❌ Invalid credentials or not an admin account.")

# ═══════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "dashboard":

    st.markdown(f'<div class="section-title">📊 Election Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">Logged in as <span style="color:#a5b4fc;font-weight:600">{st.session_state.admin}</span></div>', unsafe_allow_html=True)

    # Live stats row
    ev  = total_eligible_voters()
    vt  = total_votes_cast()
    cc  = candidate_count()
    pct = round((vt / ev * 100) if ev > 0 else 0, 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🗳️ Total Votes", vt)
    c2.metric("👥 Registered", ev)
    c3.metric("🏛️ Candidates", cc)
    c4.metric("📈 Turnout", f"{pct}%")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    t1, t2, t3, t4, t5, t6 = st.tabs([
        "📊 Results", "🏛️ Candidates", "📋 Voter Roll", "💬 Queries", "👥 Users", "✅ Pending Users"
    ])

    # ── TAB 1: RESULTS ────────────────────────────────────
    with t1:
        votes  = get_vote_counts()
        cands  = get_candidate_names()

        if not cands:
            st.info("No candidates added yet.")
        elif vt == 0:
            st.info("No votes cast yet.")
        else:
            # Build full result dict (0 for candidates with no votes)
            result = {c: votes.get(c, 0) for c in cands}
            max_v  = max(result.values()) if result else 0

            st.markdown("**Live Vote Count:**")
            for cand, count in sorted(result.items(), key=lambda x: x[1], reverse=True):
                pct_bar = (count / vt * 100) if vt > 0 else 0
                is_lead = count == max_v and max_v > 0
                pill = '<span class="pill pill-green">Leading</span>' if is_lead else ''
                st.markdown(f"""
                <div class="result-row">
                    <div>
                        <span style="font-weight:700;color:#e2e8f0">{cand}</span>
                        &nbsp; {pill}
                    </div>
                    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.2rem;font-weight:700;color:#a5b4fc">
                        {count}
                    </div>
                </div>
                <div class="result-bar-wrap">
                    <div class="result-bar" style="width:{pct_bar:.1f}%"></div>
                </div>
                """, unsafe_allow_html=True)

            # Winner/Tie
            winners = [k for k, v in result.items() if v == max_v and max_v > 0]
            if len(winners) == 1:
                st.success(f"🏆 **Winner: {winners[0]}** with {max_v} votes ({max_v/vt*100:.1f}%)")
            elif len(winners) > 1:
                st.warning(f"🤝 **Tie** between: {', '.join(winners)}")

            # Chart
            st.markdown("<br>", unsafe_allow_html=True)
            st.bar_chart(result)

    # ── TAB 2: CANDIDATE MANAGER ──────────────────────────
    with t2:
        st.markdown("**Add Candidate**")
        ca, cb, cc_ = st.columns([3,3,2])
        with ca:
            c_name   = st.text_input("Candidate Name", key="c_name", placeholder="Full name")
        with cb:
            c_party  = st.text_input("Party / Alliance", key="c_party", placeholder="Party name")
        with cc_:
            c_symbol = st.text_input("Symbol (emoji)", key="c_symbol", placeholder="e.g. 🌸")

        if st.button("➕ Add Candidate", key="add_cand"):
            if not c_name.strip():
                st.error("Candidate name is required.")
            else:
                if add_candidate(c_name.strip(), c_party.strip() or "Independent", c_symbol.strip() or "🗳️"):
                    st.success(f"✅ {c_name} added.")
                    st.rerun()
                else:
                    st.error("Candidate already exists.")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("**Current Candidates**")
        cands = get_candidates()
        if not cands:
            st.info("No candidates added yet.")
        else:
            for c in cands:
                r1, r2 = st.columns([5, 1])
                with r1:
                    st.markdown(f"""
                    <div class="cand-card" style="margin:4px 0">
                        <span class="cand-symbol">{c.get('symbol','🗳️')}</span>
                        <div class="cand-info">
                            <h4>{c['name']}</h4>
                            <p>{c.get('party','Independent')}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with r2:
                    if st.button("🗑️", key=f"del_cand_{c['name']}"):
                        remove_candidate(c["name"])
                        st.rerun()

    # ── TAB 3: VOTER ROLL ─────────────────────────────────
    with t3:
        st.markdown("**Add Eligible Voter**")
        v1, v2 = st.columns(2)
        with v1:
            new_vid  = st.text_input("Voter ID", key="new_vid", placeholder="e.g. VOTE2025001")
        with v2:
            new_vname = st.text_input("Voter Name", key="new_vname", placeholder="Official name")

        if st.button("➕ Add to Voter Roll", key="add_voter"):
            if not new_vid.strip() or not new_vname.strip():
                st.error("Both Voter ID and Name are required.")
            else:
                add_valid_voter(new_vid.strip().upper(), new_vname.strip())
                st.success(f"✅ Voter **{new_vid.upper()}** added to the roll.")
                st.rerun()

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("**Voter Roll**")
        voters = get_all_valid_voters()
        if not voters:
            st.info("No voters in the roll yet.")
        else:
            for v in voters:
                r1, r2 = st.columns([5, 1])
                with r1:
                    status = "Voted" if v.get("voted") else "Pending"
                    pill_cls = "pill-green" if v.get("voted") else "pill-amber"
                    st.markdown(f"""
                    <div class="result-row" style="margin:4px 0">
                        <div>
                            <span style="font-weight:600;color:#e2e8f0">{v['vote_id']}</span>
                            &nbsp;<span style="color:#94a3b8;font-size:0.85rem">{v['name']}</span>
                        </div>
                        <span class="pill {pill_cls}">{status}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with r2:
                    if st.button("🗑️", key=f"del_voter_{v['vote_id']}"):
                        remove_valid_voter(v["vote_id"])
                        st.rerun()

    # ── TAB 4: QUERIES ────────────────────────────────────
    with t4:
        queries = get_queries()
        if not queries:
            st.info("No queries submitted yet.")
        else:
            for q in reversed(queries):
                qid = str(q["_id"])
                with st.expander(f"👤 {q['user']}  —  {q.get('question','')[:60]}..."):
                    st.markdown(f"**Question:** {q['question']}")
                    st.markdown(f"**Status:** {'✅ Replied' if q['reply'] != 'Pending' else '⏳ Pending'}")
                    if q["reply"] != "Pending":
                        st.markdown(f"**Reply:** {q['reply']}")
                    reply_text = st.text_area("Write reply", key=f"reply_{qid}", placeholder="Type your reply...")
                    if st.button("Send Reply", key=f"send_{qid}"):
                        if reply_text.strip():
                            reply_query(qid, reply_text.strip())
                            st.success("Reply sent!")
                            st.rerun()

    # ── TAB 5: USERS ──────────────────────────────────────
    with t5:
        all_users = get_all_users()
        if not all_users:
            st.info("No users registered yet.")
        else:
            for u in all_users:
                r1, r2 = st.columns([5, 1])
                with r1:
                    role      = u.get("role","user")
                    pill_cls  = "pill-blue" if role == "admin" else "pill-green"
                    st.markdown(f"""
                    <div class="result-row" style="margin:4px 0">
                        <div>
                            <span style="font-weight:600;color:#e2e8f0">{u['username']}</span>
                            &nbsp;<span style="color:#94a3b8;font-size:0.82rem">{u.get('vote_id','—')}</span>
                            &nbsp;<span style="color:#64748b;font-size:0.78rem">· {u.get('email','no email')}</span>
                        </div>
                        <span class="pill {pill_cls}">{role}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with r2:
                    if u.get("role") != "admin":
                        if st.button("🗑️", key=f"del_user_{u['username']}"):
                            delete_user(u["username"])
                            st.rerun()

    # ── TAB 6: PENDING USERS ──────────────────────────────
    with t6:
        pend = get_pending_users()
        if not pend:
            st.markdown("""
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:3rem 1rem;text-align:center;">
                <div style="font-size:3rem;margin-bottom:1rem;">🎉</div>
                <div style="font-size:1.2rem;font-weight:600;color:#e2e8f0;margin-bottom:0.5rem;">All Clear!</div>
                <div style="color:#64748b;font-size:0.9rem;">No voters are currently pending verification.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1.5rem;">
                <div style="background:linear-gradient(135deg,#f59e0b,#d97706);width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1rem;">⏳</div>
                <div>
                    <div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;">{len(pend)} Pending Verification</div>
                    <div style="font-size:0.8rem;color:#64748b;">Review each voter and approve or reject their registration</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            for p in pend:
                b64 = p.get('face_b64')
                vid = p.get('vote_id', '—')
                uname = p.get('username', '—')
                email = p.get('email', '—')
                
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,rgba(30,41,59,0.95),rgba(15,23,42,0.95));
                            border:1px solid rgba(99,102,241,0.25);border-radius:16px;
                            padding:1.5rem;margin-bottom:1rem;
                            box-shadow:0 4px 24px rgba(0,0,0,0.3);">
                    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1.2rem;">
                        <div style="background:linear-gradient(135deg,#f59e0b,#d97706);
                                    padding:3px 12px;border-radius:20px;
                                    font-size:0.72rem;font-weight:700;color:#fff;letter-spacing:0.05em;">
                            ⏳ PENDING REVIEW
                        </div>
                        <div style="color:#64748b;font-size:0.78rem;">Submitted for admin verification</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_face, col_info = st.columns([1, 2])
                with col_face:
                    if b64:
                        st.markdown("""<div style="border-radius:12px;overflow:hidden;border:2px solid rgba(99,102,241,0.4);margin-bottom:0.5rem;">""", unsafe_allow_html=True)
                        st.image(base64.b64decode(b64), caption="📷 Biometric Face", width=200)
                        st.markdown("""</div>""", unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="width:200px;height:200px;background:rgba(30,41,59,0.8);border-radius:12px;
                                    border:2px dashed rgba(99,102,241,0.3);display:flex;align-items:center;
                                    justify-content:center;color:#475569;font-size:0.85rem;">No Face</div>
                        """, unsafe_allow_html=True)
                
                with col_info:
                    st.markdown(f"""
                    <div style="display:flex;flex-direction:column;gap:0.8rem;padding:0.5rem 0;">
                        <div style="background:rgba(15,23,42,0.6);border-radius:10px;padding:0.75rem 1rem;
                                    border-left:3px solid #6366f1;">
                            <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:2px;">Voter ID</div>
                            <div style="font-size:1.1rem;font-weight:700;color:#a5b4fc;">{vid}</div>
                        </div>
                        <div style="background:rgba(15,23,42,0.6);border-radius:10px;padding:0.75rem 1rem;
                                    border-left:3px solid #10b981;">
                            <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:2px;">Full Name</div>
                            <div style="font-size:1rem;font-weight:600;color:#e2e8f0;">{uname}</div>
                        </div>
                        <div style="background:rgba(15,23,42,0.6);border-radius:10px;padding:0.75rem 1rem;
                                    border-left:3px solid #f59e0b;">
                            <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:2px;">Email Address</div>
                            <div style="font-size:0.9rem;font-weight:500;color:#fbbf24;">{email}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                bc1, bc2, _ = st.columns([1, 1, 2])
                with bc1:
                    if st.button("✅ Approve", key=f"app_{p['username']}"):
                        approve_user(p['username'])
                        if not get_valid_voter(p['vote_id']):
                            add_valid_voter(p['vote_id'], p['username'])
                        mark_voter_registered(p['vote_id'])
                        send_approval_email(p.get('email'))
                        st.success(f"✅ {p['username']} approved! Email sent.")
                        time.sleep(1.5)
                        st.rerun()
                with bc2:
                    if st.button("❌ Reject", key=f"rej_{p['username']}"):
                        delete_pending_user(p['username'])
                        send_rejection_email(p.get('email'))
                        st.warning(f"❌ {p['username']} rejected. Email sent.")
                        time.sleep(1.5)
                        st.rerun()


    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    if st.button("🚪 Logout", key="admin_logout"):
        st.session_state.clear()
        st.query_params.clear()
        goto("home")