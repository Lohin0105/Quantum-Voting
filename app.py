import streamlit as st
import hashlib, time, secrets, requests, os, base64
import cv2, numpy as np
from dotenv import load_dotenv
from datetime import datetime, timezone
import ui_assets
load_dotenv()
try:
    import openai
except ImportError:
    openai = None
try:
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    go = px = None
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None
from database import (
    get_user, user_exists, vote_id_taken, save_user,
    admin_key_valid, get_valid_voter, mark_voter_registered,
    mark_voted, save_vote, get_votes, get_vote_counts,
    total_votes_cast, total_eligible_voters, total_voted,
    get_candidates, get_candidate_names, add_candidate,
    remove_candidate, candidate_count,
    add_valid_voter, remove_valid_voter, get_all_valid_voters,
    get_all_users, delete_user, get_pending_users, approve_user, delete_pending_user, save_pending_user,
    get_queries, save_query, reply_query,
    get_election_end_time, set_election_end_time,
    get_winner_announced, set_winner_announced,
    log_activity, get_suspicious_ips, get_all_activity,
    save_receipt, get_receipt, get_setting, set_setting,
    create_poll, get_all_polls, get_poll, delete_poll, mark_poll_email_sent,
    get_active_poll, get_upcoming_poll, get_all_active_polls, get_all_upcoming_polls, get_past_polls,
    add_poll_candidate, get_poll_candidates, remove_poll_candidate, update_poll_candidate_image,
    save_poll_vote, has_voted_in_poll, get_poll_vote_counts, total_poll_votes,
    get_ended_unannounced_polls, mark_poll_results_announced, get_poll_vote_record,
    get_past_polls_for_voter
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

# ── UI ASSETS INJECTION ──────────────────────────────
ui_assets.inject_custom_css()


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
if "force_poll_id" not in st.session_state:
    st.session_state.force_poll_id = _qp.get("poll_id", None)
if "view_poll_result_id" not in st.session_state:
    st.session_state.view_poll_result_id = _qp.get("res_id", None)

# Remaining session defaults (OTP flow state)
for k, v in [("login_otp_sent", False), ("login_otp_verified", False), ("login_username", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are the QuVote official voter education assistant. Your job is to answer questions about the voting process, candidates, registration, and general election facts. Always maintain a neutral, helpful tone. You MUST reply in the language the user speaks. Answer concisely and accurately."},
        {"role": "assistant", "content": "Hello! I am the QuVote Education Assistant. How can I help you today?"}
    ]

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════
def get_grok_client():
    api_key = os.environ.get("GROK_API_KEY", "")
    if not api_key or openai is None:
        return None
    return openai.OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )

def generate_receipt(voter_id, candidate, salt="QuVote2025"):
    raw = f"{voter_id}|{candidate}|{salt}|{time.time()}"
    return hashlib.sha256(raw.encode()).hexdigest().upper()

def get_voter_ip():
    try:
        headers = st.context.headers
        ip = headers.get("X-Forwarded-For", headers.get("X-Real-IP", "unknown"))
        return ip.split(",")[0].strip()
    except Exception:
        return "unknown"

def send_results_email_blast(poll_name, winner, vote_counts, total):
    """Send an automated blast email with election results to all users."""
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY', ''))
        from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'quantumvoting@outlook.com')
        breakdown = "".join([
            f"<tr><td style='padding:8px;border-bottom:1px solid #1e293b;'>{c}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #1e293b;text-align:center;color:#a5b4fc;font-weight:700;'>{v}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #1e293b;text-align:center;color:#64748b;'>{round(v/total*100,1) if total else 0}%</td></tr>"
            for c, v in vote_counts.items()
        ])
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;background:#0f172a;color:#e2e8f0;border-radius:12px;overflow:hidden;">
          <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:28px;text-align:center;">
            <h2 style="margin:0;color:#fff;">⚛️ QuVote — Election Results</h2>
          </div>
          <div style="padding:32px;">
            <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);border-radius:12px;padding:20px;text-align:center;margin-bottom:24px;">
              <div style="font-size:1rem;color:#6ee7b7;margin-bottom:4px;">🏆 WINNER</div>
              <div style="font-size:2rem;font-weight:800;color:#fff;">{winner}</div>
            </div>
            <p style="color:#94a3b8;">Total votes cast: <strong style="color:#a5b4fc;">{total}</strong></p>
            <table style="width:100%;border-collapse:collapse;margin-top:12px;">
              <thead><tr>
                <th style="text-align:left;padding:8px;color:#64748b;font-size:0.85rem;">Candidate</th>
                <th style="text-align:center;padding:8px;color:#64748b;font-size:0.85rem;">Votes</th>
                <th style="text-align:center;padding:8px;color:#64748b;font-size:0.85rem;">Share</th>
              </tr></thead>
              <tbody>{breakdown}</tbody>
            </table>
            <p style="margin-top:24px;color:#475569;font-size:0.82rem;">This is an automated message from QuVote. Thank you for participating in our democratic process.</p>
          </div>
        </div>"""
        users = get_all_users()
        sent = 0
        for u in users:
            email = u.get("email")
            if email:
                msg = Mail(from_email=from_email, to_emails=email,
                           subject="QuVote — Election Results Announced!", html_content=html)
                try:
                    sg.send(msg)
                    sent += 1
                except Exception:
                    pass
        return sent
    except Exception as e:
        print(f"[BLAST ERROR] {e}")
        return 0

def check_and_announce_poll_winners():
    """Check if any specific polls have ended and announce results if not done yet."""
    ended = get_ended_unannounced_polls()
    announced_any = False
    for p in ended:
        poll_id = p["poll_id"]
        poll_name = p["name"]
        
        vote_counts = get_poll_vote_counts(poll_id)
        if vote_counts:
            winner = max(vote_counts, key=vote_counts.get)
            total = total_poll_votes(poll_id)
            mark_poll_results_announced(poll_id)
            send_results_email_blast(poll_name, winner, vote_counts, total)
            announced_any = True
        else:
            # If no votes were cast but election ended, we still mark it announced to prevent loop
            mark_poll_results_announced(poll_id)
    return announced_any


def generate_symbol_image(symbol_name):
    """Generate high-quality election symbol images via AI with cache bypassing."""
    try:
        import urllib.parse, random
        # Enhanced prompt for better artistic quality and professional iconography
        prompt = (f"{symbol_name} election symbol, professional flat vector icon, "
                  "vibrant colors, minimalist clean luxury aesthetic, white background, "
                  "high resolution, symmetrical design, masterpiece quality")
        prompt_enc = urllib.parse.quote(prompt)
        # Random seed ensures a unique generation attempt every time to bypass server caching
        seed = random.randint(1000, 99999)
        url = f"https://image.pollinations.ai/prompt/{prompt_enc}?width=512&height=512&nologo=true&seed={seed}&model=flux"
        
        resp = requests.get(url, timeout=25)
        if resp.status_code == 200:
            return base64.b64encode(resp.content).decode()
    except Exception as e:
        print(f"[IMAGE GEN ERROR] {e}")
    return ""


def send_poll_announcement_email(poll_name, description, start_time, end_time):
    """Email all registered voters about a new election poll."""
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY', ''))
        from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'quantumvoting@outlook.com')
        start_str = start_time.strftime('%d %b %Y, %I:%M %p UTC') if hasattr(start_time, 'strftime') else str(start_time)
        end_str = end_time.strftime('%d %b %Y, %I:%M %p UTC') if hasattr(end_time, 'strftime') else str(end_time)
        html_body = (
            "<div style='font-family:Arial,sans-serif;max-width:560px;margin:0 auto;"
            "background:#0f172a;color:#e2e8f0;border-radius:12px;overflow:hidden;'>"
            "<div style='background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:28px;text-align:center;'>"
            "<h2 style='margin:0;color:#fff;'>QuVote - New Election Announced!</h2></div>"
            "<div style='padding:32px;'>"
            f"<div style='background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);"
            f"border-radius:12px;padding:20px;margin-bottom:20px;'>"
            f"<div style='font-size:1.2rem;font-weight:700;color:#a5b4fc;'>{poll_name}</div>"
            f"<div style='color:#94a3b8;margin-top:8px;'>{description}</div></div>"
            f"<p style='color:#94a3b8;'>Voting Opens: <strong style='color:#e2e8f0;'>{start_str}</strong></p>"
            f"<p style='color:#94a3b8;'>Voting Closes: <strong style='color:#e2e8f0;'>{end_str}</strong></p>"
            "<p style='margin-top:20px;color:#475569;font-size:0.82rem;'>"
            "Login to QuVote with your Voter ID and OTP to cast your vote.</p>"
            "</div></div>"
        )
        users = get_all_users()
        sent = 0
        for u in users:
            email = u.get('email')
            if email:
                msg = Mail(
                    from_email=from_email,
                    to_emails=email,
                    subject=f'QuVote - New Election: {poll_name}',
                    html_content=html_body
                )
                try:
                    sg.send(msg)
                    sent += 1
                except Exception:
                    pass
        return sent
    except Exception as e:
        print(f"[POLL EMAIL ERROR] {e}")
        return 0


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
# SPLASH SCREEN (shown once for 2 seconds on first load)
# ═══════════════════════════════════════════════════════════
import base64, pathlib
logo_path = pathlib.Path("logo.png")
if not st.session_state.get("splash_done", False):
    st.session_state.splash_done = True
    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
        st.markdown(f"""
        <style>
        #splash-overlay {{
            position:fixed;top:0;left:0;width:100vw;height:100vh;
            background:#0f172a;display:flex;flex-direction:column;
            align-items:center;justify-content:center;z-index:99999;
            animation: splashFade 0.5s ease 1.8s forwards;
        }}
        .splash-icon {{
            animation: splashZoom 1.8s ease forwards;
            border-radius: 50%;
        }}
        @keyframes splashZoom {{
            0%   {{ transform: scale(0.2); opacity:0; }}
            40%  {{ transform: scale(1.15); opacity:1; }}
            70%  {{ transform: scale(0.95); opacity:1; }}
            100% {{ transform: scale(1.05); opacity:1; }}
        }}
        @keyframes splashFade {{ to {{ opacity:0; pointer-events:none; }} }}
        </style>
        <div id="splash-overlay">
            <img class="splash-icon" src="data:image/png;base64,{logo_b64}"
                 style="height:260px;width:260px;object-fit:contain;
                 border-radius:50%;filter:drop-shadow(0 0 40px rgba(99,102,241,0.9));">
        </div>
        """, unsafe_allow_html=True)
        time.sleep(2)
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

# Auto-check winner announcement on every page load
check_and_announce_poll_winners()

# ═══════════════════════════════════════════════════════════
# PAGE: HOME
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "home":

    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-title">QuVote</div>
        <p class="hero-sub" style="max-width:900px;margin:0 auto;text-align:center;line-height:1.9;">
            Your vote is your voice. Cast it with confidence — every ballot is
            biometrically verified &amp; quantum-encrypted.
            <span style="color:#a5b4fc;font-weight:600;"> Democracy, reimagined for the digital age.</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.markdown(f"""
        <div class="panel-card">
            <span class="icon">{ui_assets.ICON_USER}</span>
            <h3>Voter Portal</h3>
            <p>Register, verify your identity, and cast your secure quantum vote.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Voter Portal", key="home_user", use_container_width=True):
            goto("user")

    with col2:
        st.markdown(f"""
        <div class="panel-card">
            <span class="icon">{ui_assets.ICON_ADMIN}</span>
            <h3>Admin Console</h3>
            <p>Manage candidates, voter rolls, and live election results.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Admin Console", key="home_admin", use_container_width=True):
            goto("admin")

    with col3:
        st.markdown(f"""
        <div class="panel-card">
            <span class="icon">{ui_assets.ICON_AI}</span>
            <h3>Education Bot</h3>
            <p>Ask our multilingual AI any questions about the voting process.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ask Assistant", key="home_bot", use_container_width=True):
            goto("assistant")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # (Winner Banner removed to focus on live polls)

    # Active poll featured banner
    active_poll = get_active_poll()
    if active_poll:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.05));
             border:1px solid rgba(99,102,241,0.3); border-radius:20px; padding:2rem; text-align:center; margin:1rem 0;">
            <div style="display:inline-block; padding:4px 12px; border-radius:100px; background:rgba(99,102,241,0.15); color:#a5b4fc; font-size:0.75rem; font-weight:700; text-transform:uppercase; margin-bottom:12px;">🔴 Live Election</div>
            <h2 style="margin:0; color:#fff; font-size:1.8rem; font-weight:800;">{active_poll['name']}</h2>
            <p style="color:#94a3b8; font-size:0.95rem; margin:10px 0 20px;">{active_poll.get('description', 'Cast your vote in the ongoing election.')}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗳️ Cast Your Vote", key="home_vote_now", use_container_width=True):
            goto("user_login")

    # Election Countdown Timer
    end_time = get_election_end_time()
    if end_time and not get_winner_announced() and not active_poll:
        # Show global countdown only if no specific active poll is featured (or could be integrated)
        import pytz
        end_iso = end_time.strftime('%Y-%m-%dT%H:%M:%SZ') if hasattr(end_time, 'strftime') else str(end_time)
        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.2);
             border-radius:16px;padding:1.4rem;text-align:center;margin:1rem 0;">
            <div style="color:#94a3b8;font-size:0.85rem;margin-bottom:6px;">⏳ Polls close in</div>
            <div id="countdown" style="font-family:'Space Grotesk',sans-serif;font-size:2rem;
                 font-weight:800;color:#a5b4fc;letter-spacing:0.05em;">Loading...</div>
        </div>
        <script>
        (function(){{
            var end = new Date('{end_iso}').getTime();
            function update(){{
                var now = new Date().getTime();
                var diff = end - now;
                if(diff <= 0){{ document.getElementById('countdown').innerHTML='Polls Closed'; return; }}
                var d=Math.floor(diff/86400000);
                var h=Math.floor((diff%86400000)/3600000);
                var m=Math.floor((diff%3600000)/60000);
                var s=Math.floor((diff%60000)/1000);
                document.getElementById('countdown').innerHTML=
                    (d>0?d+'d ':'')+('0'+h).slice(-2)+'h '+('0'+m).slice(-2)+'m '+('0'+s).slice(-2)+'s';
            }}
            update(); setInterval(update,1000);
        }})();
        </script>
        """, unsafe_allow_html=True)

    # Live stats (Now only visible when a poll is active)
    if active_poll:
        ap_id = active_poll['poll_id']
        ev = total_eligible_voters()
        vt = total_poll_votes(ap_id)
        cc = len(get_poll_candidates(ap_id))
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
    hc1, hc2 = st.columns(2)
    with hc1:
        if st.button("❓ FAQ", key="home_faq", use_container_width=True):
            goto("faq")
    with hc2:
        st.markdown('<p style="text-align:center;color:#334155;font-size:0.75rem;padding-top:0.6rem;">📧 quantumvoting@gmail.com</p>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# PAGE: USER PANEL
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "user":
    st.markdown('<div class="section-title">Voter Portal Menu</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Choose an action below to proceed.</div>', unsafe_allow_html=True)
    
    uc1, uc2 = st.columns(2, gap="medium")
    with uc1:
        st.markdown("""
        <div class="panel-card">
            <span class="icon">
                <svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(16,185,129,0.4));">
                    <defs>
                        <linearGradient id="regGrad" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#10b981"/>
                            <stop offset="1" stop-color="#059669"/>
                        </linearGradient>
                    </defs>
                    <path d="M12 4C14.2091 4 16 5.79086 16 8C16 10.2091 14.2091 12 12 12C9.79086 12 8 10.2091 8 8C8 5.79086 9.79086 4 12 4Z" fill="url(#regGrad)" fill-opacity="0.9" stroke="#6ee7b7" stroke-width="1.2"/>
                    <path d="M4 20C4 16.6863 7.58172 14 12 14C16.4183 14 20 16.6863 20 20H4Z" fill="url(#regGrad)" fill-opacity="0.9" stroke="#6ee7b7" stroke-width="1.2"/>
                    <path d="M19 8V12M17 10H21" stroke="#6ee7b7" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </span>
            <h3>Register Voter</h3>
            <p>Enroll for a new official voter identity verification.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Proceed to Register", key="menu_reg", use_container_width=True):
            goto("user_register")
            
    with uc2:
        st.markdown("""
        <div class="panel-card">
            <span class="icon">
                <svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(245,158,11,0.4));">
                    <defs>
                        <linearGradient id="logGrad" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#f59e0b"/>
                            <stop offset="1" stop-color="#d97706"/>
                        </linearGradient>
                    </defs>
                    <path d="M15 3H7C5.89543 3 5 3.89543 5 5V19C5 20.1046 5.89543 21 7 21H15C16.1046 21 17 20.1046 17 19V14" stroke="url(#logGrad)" stroke-width="2" stroke-linecap="round"/>
                    <path d="M10 12H21M21 12L18 9M21 12L18 15" stroke="url(#logGrad)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </span>
            <h3>Login to Account</h3>
            <p>Sign in using your biometric and OTP credentials.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Proceed to Login", key="menu_login", use_container_width=True):
            goto("user_login")

if st.session_state.page == "user_register":
    st.markdown('<div class="section-title">🆕 Voter Registration</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Submit your details to enroll.</div>', unsafe_allow_html=True)
    st.markdown("---")
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
        elif not voter_doc:
            st.error("❌ Voter ID not found in the authorized database. Please contact the administrator.")
        elif "face_b64" not in voter_doc or not voter_doc["face_b64"]:
            st.error("❌ No reference photo found for this Voter ID. The administrator must upload a reference photo for you before you can register.")
        else:
            face_b64 = get_face_b64(img.getvalue())
            if not face_b64:
                st.error("❌ No face detected. Ensure good lighting and look directly at the camera.")
            else:
                new_face_arr = extract_face(img.getvalue())
                saved_face = decode_face_b64(voter_doc["face_b64"])
                if saved_face is not None and new_face_arr is not None and compare_faces(new_face_arr, saved_face):
                    save_pending_user(uname, {
                        "vote_id": vid, 
                        "email": email, 
                        "password": hash_data(pwd), 
                        "role": "user", 
                        "face_b64": face_b64,
                        "status": "pending"
                    })
                    st.success("✅ **Details sent to Admin!** Biometric match successful. Your registration is in progress. The administrator will verify your info and send you an email. You can login only after verification.")
                else:
                    st.error("❌ Identity mismatch: Your live face capture does not match the authorized reference photo for this Voter ID.")

    if st.button("← Back to Menu", key="back_from_reg"):
        goto("user")

if st.session_state.page == "user_login":
    st.markdown('<div class="section-title">🔐 Voter Login</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Sign in using your Voter ID and Email.</div>', unsafe_allow_html=True)
    st.markdown("---")
    l_vid = st.text_input("Voter ID", placeholder="Your official Voter ID", key="l_vid", disabled=st.session_state.get('login_otp_verified', False))
    l_email = st.text_input("Email", placeholder="Registered email address", key="l_email", disabled=st.session_state.get('login_otp_verified', False))

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
    else:
        st.markdown('<h4 style="color:#10b981; margin:0;">✅ OTP Verified — Logging you in...</h4>', unsafe_allow_html=True)
        username = st.session_state.get("login_username")
        st.session_state.login_otp_sent = False
        st.session_state.login_otp_verified = False
        st.session_state.user = username
        time.sleep(1)
        goto("vote")

    if st.button("← Back to Menu", key="back_from_login"):
        goto("user")

# ═══════════════════════════════════════════════════════════
# PAGE: VOTE
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "vote":

    _user_v   = st.session_state.user
    _udoc     = get_user(_user_v)
    _vid      = _udoc["vote_id"] if _udoc else None
    _full_name = _udoc.get("name", _user_v) if _udoc else _user_v
    
    _force_pid = st.session_state.get("force_poll_id")
    _active = get_poll(_force_pid) if _force_pid else get_active_poll()

    # Back navigation at top
    if st.button("← Back to Voter Dashboard", key="ballot_top_back"):
        goto("voter_dashboard")

    st.markdown(f'<div class="section-title">Welcome, {_full_name} 👋</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">Voter ID: <span style="color:#a5b4fc;font-weight:600">{_vid}</span></div>', unsafe_allow_html=True)

    if _active:
        _pid   = _active["poll_id"]
        _pcands = get_poll_candidates(_pid)
        _already = has_voted_in_poll(_pid, _vid) if _vid else False

        _start = _active.get("start_time")
        _end   = _active.get("end_time")
        _start_str = _start.strftime('%d %b %Y, %H:%M') if hasattr(_start, 'strftime') else str(_start)
        _end_str   = _end.strftime('%d %b %Y, %H:%M') if hasattr(_end, 'strftime') else str(_end)
        
        import datetime
        now = datetime.datetime.utcnow()
        if hasattr(_end, 'timestamp'):
            rem = _end - now
            if rem.total_seconds() > 0:
                hrs, rem_sec = divmod(rem.total_seconds(), 3600)
                mins, _ = divmod(rem_sec, 60)
                rem_str = f"{int(hrs)}h {int(mins)}m remaining"
            else:
                rem_str = "Poll Ended"
        else:
            rem_str = "N/A"

        _tot_votes = total_poll_votes(_pid)

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(139,92,246,0.05));
             border:1px solid rgba(99,102,241,0.2);border-radius:20px;padding:2rem;margin:1rem auto;max-width:800px;box-shadow:0 10px 30px rgba(0,0,0,0.2);">
          <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:0.8rem;color:#6366f1;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:8px;">🟢 Active Election Ballot</div>
            <div style="font-size:2rem;font-weight:800;color:#e2e8f0;margin-bottom:10px;">{_active["name"]}</div>
            <div style="color:#94a3b8;font-size:0.95rem;line-height:1.6;max-width:600px;margin:0 auto 20px auto;">{_active.get("description","No description provided.")}</div>
          </div>
          
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;background:rgba(255,255,255,0.03);padding:24px;border-radius:16px;border:1px solid rgba(255,255,255,0.06);">
              <div style="text-align:center;padding:10px;border-right:1px solid rgba(255,255,255,0.05);">
                <div style="color:#64748b;font-size:0.7rem;text-transform:uppercase;margin-bottom:6px;letter-spacing:0.05em;">⏱️ Start Time</div>
                <div style="color:#cbd5e1;font-size:0.9rem;font-weight:600;">{_start_str}</div>
              </div>
              <div style="text-align:center;padding:10px;">
                <div style="color:#64748b;font-size:0.7rem;text-transform:uppercase;margin-bottom:6px;letter-spacing:0.05em;">🏁 End Time</div>
                <div style="color:#cbd5e1;font-size:0.9rem;font-weight:600;">{_end_str}</div>
              </div>
              <div style="text-align:center;padding:10px;border-right:1px solid rgba(255,255,255,0.05);border-top:1px solid rgba(255,255,255,0.05);">
                <div style="color:#64748b;font-size:0.7rem;text-transform:uppercase;margin-bottom:6px;letter-spacing:0.05em;">📊 Participation</div>
                <div style="color:#10b981;font-size:1.1rem;font-weight:700;">{_tot_votes} Votes</div>
              </div>
              <div style="text-align:center;padding:10px;border-top:1px solid rgba(255,255,255,0.05);">
                <div style="color:#64748b;font-size:0.7rem;text-transform:uppercase;margin-bottom:6px;letter-spacing:0.05em;">⏳ Time Left</div>
                <div style="color:#f43f5e;font-size:1.1rem;font-weight:700;">{rem_str}</div>
              </div>
          </div>
        </div>""", unsafe_allow_html=True)

        if _already:
            vote_rec = get_poll_vote_record(_pid, _vid)
            c_voted = vote_rec.get("candidate", "—") if vote_rec else "—"
            v_time = vote_rec.get("timestamp") if vote_rec else None
            t_str = v_time.strftime("%d %b %Y, %H:%M:%S") if hasattr(v_time, "strftime") else str(v_time)
            r_str = get_receipt(_vid, _pid) or "No receipt found."

            st.markdown("""
            <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);
                 border-radius:16px;padding:2rem;text-align:center;margin:1rem 0;">
                <div style="font-size:3rem;margin-bottom:0.5rem;">✅</div>
                <div style="font-size:1.2rem;font-weight:700;color:#6ee7b7;">Vote Already Cast in this Election</div>
                <div style="color:#64748b;margin-top:0.4rem;font-size:0.9rem;">
                    Your vote has been securely recorded. Thank you for participating.
                </div>
            </div>""", unsafe_allow_html=True)
            
            receip_content = f"QuVote Official Election Receipt\n--------------------------------\nElection : {_active['name']}\nVoter ID : {_vid}\nCandidate: {c_voted}\nTime Cast: {t_str}\nHash     : {r_str}\n\nKeep this receipt as cryptographic proof of your vote."
            st.download_button("⬇️ Download Vote Receipt", data=receip_content, file_name=f"QuVote_Receipt_{_pid}.txt", mime="text/plain", use_container_width=True)

        elif not _pcands:
            st.warning("⚠️ No candidates have been added to this election yet. Contact the admin.")
        else:
            st.markdown("**Select your candidate:**")
            for _pc in _pcands:
                _ib = _pc.get("symbol_image_b64", "")
                if _ib:
                    _card_img = f"<img src='data:image/png;base64,{_ib}' width='64' height='64' style='border-radius:10px;object-fit:cover;'>"
                else:
                    _card_img = f"<span style='font-size:2.8rem;'>{_pc.get('symbol','🗳️')}</span>"
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                     border-radius:14px;padding:1rem 1.2rem;display:flex;align-items:center;
                     gap:16px;margin:6px 0;transition:all 0.2s;">
                  {_card_img}
                  <div>
                    <div style="font-weight:700;color:#e2e8f0;font-size:1rem;">{_pc["name"]}</div>
                    <div style="color:#94a3b8;font-size:0.82rem;">{_pc.get("party","Independent")}</div>
                    <div style="color:#64748b;font-size:0.75rem;">Symbol: {_pc.get("symbol","")}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

            _choice_p = st.radio("Cast your vote for:", [c["name"] for c in _pcands], key="poll_vote_radio")
            if st.button("🗳️ Submit Vote", key="submit_poll_vote"):
                save_poll_vote(_pid, _vid, _choice_p)
                mark_voted(_vid)
                _rct = generate_receipt(_vid, _choice_p)
                save_receipt(_vid, _pid, _rct)
                log_activity(_vid, get_voter_ip(), "vote")
                st.session_state["last_receipt"] = _rct
                st.session_state["last_choice"]  = _choice_p
                st.success(f"✅ Vote submitted for **{_choice_p}**!")
                st.rerun()

    else:
        st.info("⏳ No active election available right now.")
        
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📩 Submit a Query", key="query_btn"):
            goto("query")
    with col2:
        if st.button("👤 My Dashboard", key="voter_dash_btn"):
            goto("voter_dashboard")
    with col3:
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
# PAGE: ADMIN ACCESS (LOGIN/REGISTER)
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "admin":
    if not st.session_state.admin:
        st.markdown('<div class="section-title">Admin Access</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Authorized personnel only. Choose an action.</div>', unsafe_allow_html=True)
        
        ac1, ac2 = st.columns(2, gap="medium")
        with ac1:
            st.markdown(f"""
            <div class="panel-card">
                <span class="icon">{ui_assets.ICON_ADMIN_LOGIN}</span>
                <h3>Admin Login</h3>
                <p>Manage the election system with root privileges.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Proceed to Login", key="adm_login_btn", use_container_width=True):
                st.session_state.admin_action = "login"
        
        with ac2:
            st.markdown(f"""
            <div class="panel-card">
                <span class="icon">{ui_assets.ICON_ADMIN_REG}</span>
                <h3>Admin Registration</h3>
                <p>Create a new administrator account (Master Key required).</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Register New Admin", key="adm_reg_btn", use_container_width=True):
                st.session_state.admin_action = "register"

        st.markdown("---")
        action = st.session_state.get("admin_action")
        if action == "login":
            st.markdown("#### 🔐 Admin Login")
            a_user = st.text_input("Username", key="a_login_u")
            a_pass = st.text_input("Password", type="password", key="a_login_p")
            if st.button("Login", key="a_login_submit"):
                user = get_user(a_user)
                if user and user.get("role") == "admin" and user.get("password") == hash_data(a_pass):
                    st.session_state.admin = a_user
                    goto("dashboard")
                else:
                    st.error("❌ Invalid admin credentials.")
        elif action == "register":
            st.markdown("#### 🆕 Admin Registration")
            r_user = st.text_input("Username", key="a_reg_u")
            r_pass = st.text_input("Password", type="password", key="a_reg_p")
            r_key  = st.text_input("Master Admin Key", type="password", key="a_reg_k")
            if st.button("Register Admin", key="a_reg_submit"):
                if not r_user or not r_pass:
                    st.warning("Provide username and password.")
                elif admin_key_valid(r_key):
                    if user_exists(r_user):
                        st.error("Admin already exists.")
                    else:
                        save_user(r_user, hash_data(r_pass), "admin")
                        st.success("✅ Admin registered successfully! Proceed to login.")
                else:
                    st.error("❌ Invalid Master Administrative Key.")
    else:
        goto("dashboard")

# ═══════════════════════════════════════════════════════════
# PAGE: ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "dashboard":
    if not st.session_state.admin:
        goto("admin")
    
    st.markdown('<div class="section-title">Admin Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">Welcome back, <span style="color:#a5b4fc;font-weight:600;">{st.session_state.admin}</span></div>', unsafe_allow_html=True)
    
    t1, t2, t3, t4, t5, t6, t7 = st.tabs(["📊 Results", "👥 Candidates", "📜 Voter Roll", "📩 Queries", "👤 Users", "⏳ Pending", "🗳️ Polls"])

    # ── TAB 1: RESULTS ────────────────────────────────────
    with t1:
        all_polls_r = get_all_polls()
        now_r = datetime.now()

        # Initialize session state for poll toggles
        if "expanded_live_poll_id" not in st.session_state:
            st.session_state.expanded_live_poll_id = None
        if "expanded_prev_poll_id" not in st.session_state:
            st.session_state.expanded_prev_poll_id = None

        if not all_polls_r:
            st.info("No election polls found in the system.")
        else:
            # Categorize Polls
            live_polls = [p for p in all_polls_r if p["start_time"] <= now_r <= p["end_time"]]
            previous_polls = [p for p in all_polls_r if now_r > p["end_time"]]

            # — SECTION 1: LIVE POLLING ———————————————————
            st.markdown("### 🔴 Live Polling")
            if not live_polls:
                st.caption("No polls are currently active.")
            else:
                # Button Grid for Live Polls
                l_cols = st.columns(3)
                for i, lp in enumerate(live_polls):
                    if l_cols[i % 3].button(f"🗳️ {lp['name']}", key=f"btn_live_{lp['poll_id']}", use_container_width=True):
                        st.session_state.expanded_live_poll_id = lp['poll_id'] if st.session_state.expanded_live_poll_id != lp['poll_id'] else None

                # Details for selected Live Poll
                exp_l_id = st.session_state.expanded_live_poll_id
                if exp_l_id:
                    lp = next((p for p in live_polls if p['poll_id'] == exp_l_id), None)
                    if lp:
                        lpid = lp["poll_id"]
                        lp_votes = get_poll_vote_counts(lpid)
                        lp_total = sum(lp_votes.values()) if lp_votes else 0
                        lp_cands = get_poll_candidates(lpid)
                        lp_eligible = total_eligible_voters()

                        st.markdown(f"""
                        <div style='background:rgba(99,102,241,0.05); border:1px solid rgba(99,102,241,0.2); border-radius:16px; padding:1.5rem; margin-top:1rem;'>
                            <div style='font-size:1.3rem; font-weight:800; color:#a5b4fc; margin-bottom:0.5rem;'>{lp['name']}</div>
                            <div style='color:#94a3b8; font-size:0.95rem; margin-bottom:1.2rem;'>{lp.get('description', 'No description available.')}</div>
                            <div class='divider' style='margin:1rem 0;'></div>
                        """, unsafe_allow_html=True)
                        
                        # Candidates List
                        st.markdown("#### Candidates")
                        if lp_cands:
                            for c in lp_cands:
                                c_name = c["name"]
                                c_votes = lp_votes.get(c_name, 0)
                                c_img = c.get("symbol_image_b64", "")
                                c_sym = c.get("symbol", "🗳️")
                                
                                symbol_html = (f"<img src='data:image/png;base64,{c_img}' width='36' height='36' style='border-radius:6px;'>" 
                                              if c_img else f"<span style='font-size:1.8rem;'>{c_sym}</span>")
                                
                                st.markdown(f"""
                                <div style='display:flex; align-items:center; background:rgba(255,255,255,0.03); padding:12px 20px; border-radius:12px; margin-bottom:8px; border:1px solid rgba(255,255,255,0.05);'>
                                    <div style='flex: 1; font-weight:700; color:#e2e8f0; font-size:1.1rem;'>{c_name}</div>
                                    <div style='margin: 0 40px; display: flex; align-items: center;'>{symbol_html}</div>
                                    <div style='font-weight:800; color:#a5b4fc; font-size:1.2rem; min-width:100px; text-align:right;'>{c_votes} <span style='font-size:0.8rem; color:#64748b; font-weight:400;'>votes</span></div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Metrics and Lead
                        st.markdown("<br>", unsafe_allow_html=True)
                        mc1, mc2 = st.columns(2)
                        with mc1:
                            st.metric("👥 Total Eligible Voters", lp_eligible)
                            st.metric("📥 Voters Participated", lp_total)
                        with mc2:
                            # Plotly analytics
                            ui_assets.render_poll_analytics(lp_votes)

                        if lp_votes and len(lp_votes) > 1:
                            sorted_v = sorted(lp_votes.items(), key=lambda x: x[1], reverse=True)
                            leader_name, leader_v = sorted_v[0]
                            runner_up_name, runner_up_v = sorted_v[1]
                            diff = leader_v - runner_up_v
                            if diff > 0:
                                st.success(f"🚀 **{leader_name}** is leading by **{diff}** votes over {runner_up_name}")
                            else:
                                st.warning(f"⚖️ **{leader_name}** and **{runner_up_name}** are currently tied!")
                        elif lp_votes and len(lp_votes) == 1:
                            st.info(f"🏆 **{list(lp_votes.keys())[0]}** is leading")
                        
                        st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # — SECTION 2: PREVIOUS POLLING ———————————————————
            st.markdown("### 📂 Previous Polling")
            if not previous_polls:
                st.caption("No previous polls found.")
            else:
                # Button Grid for Previous Polls
                p_cols = st.columns(3)
                for i, pp in enumerate(previous_polls):
                    if p_cols[i % 3].button(f"📜 {pp['name']}", key=f"btn_prev_{pp['poll_id']}", use_container_width=True):
                        st.session_state.expanded_prev_poll_id = pp['poll_id'] if st.session_state.expanded_prev_poll_id != pp['poll_id'] else None

                # Details for selected Previous Poll
                exp_p_id = st.session_state.expanded_prev_poll_id
                if exp_p_id:
                    pp = next((p for p in previous_polls if p['poll_id'] == exp_p_id), None)
                    if pp:
                        ppid = pp["poll_id"]
                        pp_votes = get_poll_vote_counts(ppid)
                        pp_total = sum(pp_votes.values()) if pp_votes else 0
                        pp_cands = get_poll_candidates(ppid)
                        pp_eligible = total_eligible_voters()

                        st.markdown(f"""
                        <div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:1.5rem; margin-top:1rem;'>
                            <div style='font-size:1.3rem; font-weight:800; color:#e2e8f0; margin-bottom:0.5rem;'>{pp['name']}</div>
                            <div style='color:#64748b; font-size:0.9rem; margin-bottom:1.2rem;'>{pp.get('description', 'No description available.')}</div>
                            <div class='divider' style='margin:1rem 0;'></div>
                        """, unsafe_allow_html=True)

                        # Standings
                        st.markdown("#### Final Standings")
                        if pp_cands:
                            for c in sorted(pp_cands, key=lambda x: pp_votes.get(x["name"],0), reverse=True):
                                c_name = c["name"]
                                c_votes = pp_votes.get(c_name, 0)
                                c_img = c.get("symbol_image_b64", "")
                                c_sym = c.get("symbol", "🗳️")
                                
                                symbol_html = (f"<img src='data:image/png;base64,{c_img}' width='32' height='32' style='border-radius:6px;'>" 
                                              if c_img else f"<span style='font-size:1.5rem;'>{c_sym}</span>")
                                
                                st.markdown(f"""
                                <div style='display:flex; align-items:center; background:rgba(255,255,255,0.02); padding:10px 18px; border-radius:10px; margin-bottom:6px; border:1px solid rgba(255,255,255,0.05);'>
                                    <div style='flex: 1; font-weight:600; color:#cbd5e1;'>{c_name}</div>
                                    <div style='margin: 0 40px; display: flex; align-items: center;'>{symbol_html}</div>
                                    <div style='font-weight:700; color:#818cf8; min-width:80px; text-align:right;'>{c_votes} votes</div>
                                </div>
                                """, unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)
                        pmc1, pmc2 = st.columns(2)
                        with pmc1:
                            st.metric("👥 Total Eligible Voters", pp_eligible)
                            st.metric("📥 Voters Participated", pp_total)
                        with pmc2:
                            # Plotly analytics
                            ui_assets.render_poll_analytics(pp_votes)

                        if pp_votes:
                            winner = max(pp_votes, key=pp_votes.get)
                            st.success(f"🎊 **Final Verdict:** **{winner}** has won the election!")
                        
                        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 2: CANDIDATE MANAGER ────────────────────────────
    with t2:
        # — Poll candidates grouped by poll —─────────────
        all_polls_c = get_all_polls()
        if all_polls_c:
            st.markdown("### 🗳️ Poll Candidates (grouped by election)")
            for _pc_poll in all_polls_c:
                _pc_pid   = _pc_poll["poll_id"]
                _pc_pname = _pc_poll["name"]
                _pc_cands = get_poll_candidates(_pc_pid)
                with st.expander(f"🏛️ {_pc_pname}  —  {len(_pc_cands)} candidate(s)", expanded=True):
                    if not _pc_cands:
                        st.caption("No candidates added to this poll yet. Use the Polls tab to add them.")
                    else:
                        for _pcc in _pc_cands:
                            _pcc_img  = _pcc.get("symbol_image_b64","")
                            _pcc_thumb = (f"<img src='data:image/png;base64,{_pcc_img}' width='48' height='48' "
                                          f"style='border-radius:8px;object-fit:cover;'>" if _pcc_img
                                          else f"<span style='font-size:2.2rem;'>{_pcc.get('symbol','🗳️')}</span>")
                            st.markdown(f"""
                            <div class='cand-card' style='margin:4px 0;'>
                              {_pcc_thumb}
                              <div class='cand-info'>
                                <h4>{_pcc['name']}</h4>
                                <p>{_pcc.get('party','Independent')} &bull; Symbol: {_pcc.get('symbol','')}</p>
                              </div>
                            </div>""", unsafe_allow_html=True)
            st.markdown("---")

        # — Legacy global candidates ——————————————————
        with st.expander("📋 Legacy Global Candidates (old system)", expanded=not all_polls_c):
            ca, cb, cc_ = st.columns([3,3,2])
            with ca:
                c_name   = st.text_input("Candidate Name", key="c_name", placeholder="Full name")
            with cb:
                c_party  = st.text_input("Party / Alliance", key="c_party", placeholder="Party name")
            with cc_:
                c_symbol = st.text_input("Symbol (emoji)", key="c_symbol", placeholder="e.g. 🌸")
            if st.button("➕ Add Legacy Candidate", key="add_cand"):
                if not c_name.strip():
                    st.error("Candidate name is required.")
                else:
                    if add_candidate(c_name.strip(), c_party.strip() or "Independent", c_symbol.strip() or "🗳️"):
                        st.success(f"✅ {c_name} added.")
                        st.rerun()
                    else:
                        st.error("Candidate already exists.")
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            cands_leg = get_candidates()
            if not cands_leg:
                st.info("No legacy candidates added.")
            else:
                for c in cands_leg:
                    r1, r2 = st.columns([5, 1])
                    with r1:
                        st.markdown(f"""
                        <div class="cand-card" style="margin:4px 0">
                            <span class="cand-symbol">{c.get('symbol','🗳️')}</span>
                            <div class="cand-info">
                                <h4>{c['name']}</h4>
                                <p>{c.get('party','Independent')}</p>
                            </div>
                        </div>""", unsafe_allow_html=True)
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
        
        st.markdown("**Voter Reference Photo (Required)**")
        photo_tab1, photo_tab2 = st.tabs(["📁 Upload Image", "📷 Capture from Camera"])
        with photo_tab1:
            new_vface_upload = st.file_uploader("Select Image File", type=["jpg", "png", "jpeg"], key="new_vface_up", label_visibility="collapsed")
        with photo_tab2:
            new_vface_cam = st.camera_input("Take Photo", key="new_vface_cam", label_visibility="collapsed")
            
        new_vface = new_vface_upload or new_vface_cam

        if st.button("➕ Add to Voter Roll", key="add_voter"):
            if not new_vid.strip() or not new_vname.strip():
                st.error("Both Voter ID and Name are required.")
            elif not new_vface:
                st.error("Voter reference photo is required.")
            else:
                face_b64 = get_face_b64(new_vface.getvalue())
                if not face_b64:
                    st.error("❌ No face detected in the uploaded image. Please ensure a clear view of the face.")
                else:
                    add_valid_voter(new_vid.strip().upper(), new_vname.strip(), face_b64)
                    st.success(f"✅ Voter **{new_vid.upper()}** added to the roll with reference photo.")
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
                    status = "Voted" if v.get("voted") else "Not Voted"
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



    # ── TAB 7: POLLS ──────────────────────────────────────
    with t7:
        st.markdown("### 🗳️ Create New Election Poll")
        with st.form("create_poll_form"):
            poll_name_f   = st.text_input("Election Name", placeholder="e.g. 2025 General Election")
            poll_desc_f   = st.text_area("Description", placeholder="Brief description for voters...")
            col_sd, col_sti = st.columns(2)
            with col_sd:
                p_start_date = st.date_input("Start Date", key="p_start_date")
            with col_sti:
                p_start_ti = st.time_input("Start Time", key="p_start_time")
            col_ed, col_eti = st.columns(2)
            with col_ed:
                p_end_date = st.date_input("End Date", key="p_end_date")
            with col_eti:
                p_end_ti = st.time_input("End Time", key="p_end_time")
            poll_submitted = st.form_submit_button("🚀 Create Poll & Notify All Voters")
        if poll_submitted:
            if not poll_name_f.strip():
                st.error("Poll name is required.")
            else:
                p_start = datetime.combine(p_start_date, p_start_ti)
                p_end   = datetime.combine(p_end_date, p_end_ti)
                if p_end <= p_start:
                    st.error("End time must be after start time.")
                else:
                    new_pid = create_poll(poll_name_f.strip(), poll_desc_f.strip(),
                                          p_start, p_end, st.session_state.get("admin",""))
                    with st.spinner("Sending email to all voters..."):
                        sc = send_poll_announcement_email(poll_name_f.strip(), poll_desc_f.strip(), p_start, p_end)
                        mark_poll_email_sent(new_pid)
                    st.success(f"Poll **{poll_name_f}** created! ID:`{new_pid}` — 📧 {sc} voters notified.")
                    st.rerun()

        st.markdown("---")
        st.markdown("### 🏛️ Manage Existing Polls")
        all_polls_list = get_all_polls()
        if not all_polls_list:
            st.info("No polls yet. Create one above!")
        else:
            for p in all_polls_list:
                sel_pid = p["poll_id"]
                now_u = datetime.now()
                status_lbl = ("🟢 Active"    if p["start_time"] <= now_u <= p["end_time"]
                              else ("🔜 Upcoming" if now_u < p["start_time"] else "🔴 Ended"))
                
                expander_label = f"🗳️ {p['name']}  —  {status_lbl}"
                with st.expander(expander_label):
                    st.markdown(
                        f"**ID:** `{sel_pid}` | **Window:** {p['start_time']} → {p['end_time']}<br>"
                        f"_{p.get('description', 'No description')}_", 
                        unsafe_allow_html=True
                    )
                    st.markdown("---")
                    
                    # Cand list
                    pcands = get_poll_candidates(sel_pid)
                    if pcands:
                        st.markdown(f"**Candidates ({len(pcands)}):**")
                        for pc in pcands:
                            pca, pcb = st.columns([5, 1])
                            with pca:
                                ib = pc.get("symbol_image_b64","")
                                img_tag = (f"<img src='data:image/png;base64,{ib}' width='44' height='44' "
                                           f"style='border-radius:6px;margin-right:10px;vertical-align:middle;'>"
                                           if ib else "<span style='font-size:1.8rem;margin-right:10px;'>🗳️</span>")
                                st.markdown(f"<div style='display:flex;align-items:center;background:rgba(255,255,255,0.03);"
                                            f"border-radius:8px;padding:0.5rem;margin:2px 0;'>"
                                            f"{img_tag}<div><b style='color:#e2e8f0;'>{pc['name']}</b><br>"
                                            f"<span style='color:#94a3b8;font-size:0.78rem;'>{pc.get('party','Independent')} • {pc.get('symbol','')}</span></div></div>",
                                            unsafe_allow_html=True)
                            with pcb:
                                if st.button("❌", key=f"rpc_{sel_pid}_{pc['name']}"):
                                    remove_poll_candidate(sel_pid, pc["name"])
                                    st.rerun()
                    else:
                        st.info("No candidates added to this poll yet.")

                    # Add Candidate
                    st.markdown("<br>**➕ Add Candidate to this Poll:**", unsafe_allow_html=True)
                    ia, ib2, ic = st.columns(3)
                    with ia:
                        nc_name  = st.text_input("Name", key=f"pc_nm_{sel_pid}")
                    with ib2:
                        nc_party = st.text_input("Party", key=f"pc_pty_{sel_pid}")
                    with ic:
                        nc_sym   = st.text_input("Symbol (describe)", key=f"pc_sym_{sel_pid}", placeholder="lotus, hand, sun...")

                    g1, g2 = st.columns(2)
                    with g1:
                        if st.button("🎨 Generate Image", key=f"gen_sym_{sel_pid}"):
                            if nc_sym.strip():
                                with st.spinner(f"AI generating image for '{nc_sym}' (~10s)..."):
                                    gimg = ui_assets.generate_symbol_image(nc_sym.strip())
                                if gimg:
                                    st.session_state[f"prev_img_{sel_pid}"] = gimg
                                    st.session_state[f"prev_sym_{sel_pid}"] = nc_sym.strip()
                                    st.success("✅ Image generated! Preview below.")
                                else:
                                    st.error("Generation failed. Check internet.")
                            else:
                                st.warning("Enter symbol description first.")

                    img_key = f"prev_img_{sel_pid}"
                    sym_key = f"prev_sym_{sel_pid}"
                    if st.session_state.get(img_key):
                        st.image(f"data:image/png;base64,{st.session_state[img_key]}",
                                 caption=f"Symbol: {st.session_state.get(sym_key,'')}",
                                 width=130)

                    with g2:
                        if st.button("💾 Save Candidate", key=f"apc_btn_{sel_pid}"):
                            if not nc_name.strip():
                                st.error("Candidate Name is required to save.")
                            else:
                                simg = st.session_state.get(img_key,"")
                                if add_poll_candidate(sel_pid, nc_name.strip(),
                                                       nc_party.strip() or "Independent",
                                                       nc_sym.strip(), simg):
                                    st.session_state.pop(img_key, None)
                                    st.session_state.pop(sym_key, None)
                                    st.success(f"✅ {nc_name} successfully added to this poll!")
                                    st.rerun()
                                else:
                                    st.error("Candidate already exists in this poll.")

                    st.markdown("---")
                    col_del, _ = st.columns([1, 3])
                    with col_del:
                        if st.button("🗑️ Delete Entire Poll", key=f"dp_{sel_pid}"):
                            delete_poll(sel_pid)
                            st.warning(f"Poll '{p['name']}' deleted.")
                            st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    if st.button("🚪 Logout", key="admin_logout"):
        st.session_state.clear()
        st.query_params.clear()
        goto("home")

# ═══════════════════════════════════════════════════════════
# PAGE: ASSISTANT
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "assistant":
    st.markdown('<div class="section-title">Voter Education Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Ask any questions about the voting process, candidates, or eligibility. I speak all languages!</div>', unsafe_allow_html=True)

    # Display chat messages from history on app rerun
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # React to user input
    if prompt := st.chat_input("Type your question here..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        client = get_grok_client()
        if not client:
            has_key = bool(os.environ.get("GROK_API_KEY"))
            st.error(f"Grok Error: API Key configured: {has_key} | `openai` library loaded: {openai is not None}. If `openai` is False, please restart your terminal/Streamlit or ensure pip and python match.")
        else:
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                try:
                    # Request stream from Groq
                    stream = client.chat.completions.create(
                        model="llama-3.3-70b-versatile", 
                        messages=st.session_state.messages,
                        stream=True,
                    )
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    st.error(f"Error communicating with AI: {str(e)}")

# ═══════════════════════════════════════════════════════════
# PAGE: VOTER DASHBOARD
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "voter_dashboard":
    username = st.session_state.get("user")
    if not username:
        st.warning("Please login first.")
        if st.button("Back to Home", key="vd_back_anon"): goto("home")
    else:
        user_doc = get_user(username)
        vid = user_doc.get("vote_id", "") if user_doc else ""
        vv = get_valid_voter(vid) if vid else None
        
        st.markdown('<div class="section-title">👤 Voter Dashboard</div>', unsafe_allow_html=True)
        
        # Calculate Stats
        active_c = len(get_all_active_polls())
        past_voted_c = len(get_past_polls_for_voter(vid)) if vid else 0
        total_p = len(get_all_polls())
        participation = round((past_voted_c / total_p * 100), 1) if total_p > 0 else 0

        st.markdown(f"""
        <div style="display:grid;grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:1.2rem; margin-bottom:2rem;">
            <div class="stat-box">
                <div class="label">Identity</div>
                <div class="value" style="font-size:1.1rem;color:#a5b4fc;">{user_doc.get('name','—')}</div>
                <div style="color:#64748b;font-size:0.7rem;margin-top:4px;">UID: {vid}</div>
            </div>
            <div class="stat-box">
                <div class="label">Live Polls</div>
                <div class="value">{active_c}</div>
                <div style="color:#10b981;font-size:0.7rem;margin-top:4px;">Ready to Cast</div>
            </div>
            <div class="stat-box">
                <div class="label">Participation</div>
                <div class="value">{past_voted_c} <span style="font-size:0.8rem;color:#94a3b8;font-weight:400;">/{total_p}</span></div>
                <div style="color:#6366f1;font-size:0.7rem;margin-top:4px;">{participation}% Activity</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)

        tab_active, tab_past = st.tabs(["🟢 Active & Upcoming", "📜 Election History"])

        with tab_active:
            active_polls = get_all_active_polls()
            upcoming_polls = get_all_upcoming_polls()
            if not active_polls and not upcoming_polls:
                st.markdown('<div style="text-align:center;padding:4rem 2rem;color:#64748b;font-style:italic;">No live or scheduled elections found.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="poll-grid">', unsafe_allow_html=True)
                # Active
                for ap in active_polls:
                    pid = ap["poll_id"]
                    voted = has_voted_in_poll(pid, vid)
                    cands = get_poll_candidates(pid)
                    cand_html = ""
                    if cands:
                        items = "".join([f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px;'><span style='font-size:1rem;'>{c.get('symbol','🗳️')}</span><span style='color:#cbd5e1;font-size:0.85rem;'>{c['name']}</span></div>" for c in cands])
                        cand_html = f"<div style='margin:1.2rem 0;padding:1rem 0;border-top:1px solid rgba(255,255,255,0.06);border-bottom:1px solid rgba(255,255,255,0.06);'>{items}</div>"
                    
                    st.markdown(f"""
                    <div class="poll-card-block">
                        <span style="display:inline-block;padding:3px 10px;border-radius:100px;background:rgba(16,185,129,0.1);color:#6ee7b7;font-size:0.7rem;font-weight:700;text-transform:uppercase;margin-bottom:10px;">🟢 Live Now</span>
                        <h3 style="margin:0;color:#f8fafc;font-size:1.2rem;font-weight:700;">{ap['name']}</h3>
                        <p style="color:#94a3b8;font-size:0.8rem;margin:8px 0;height:38px;overflow:hidden;line-height:1.5;">{ap.get('description','')}</p>
                        {cand_html}
                        <div style="color:#f87171;font-size:0.75rem;margin-bottom:1.5rem;display:flex;align-items:center;gap:6px;font-weight:500;">⏱️ Ends: {ap['end_time'].strftime('%d %b, %H:%M') if hasattr(ap['end_time'],'strftime') else ap['end_time']}</div>
                        <div style="margin-top:auto;">
                            <a href="?page=vote&user={username}&poll_id={pid}" target="_self" class="{'btn-premium-outline' if voted else 'btn-premium'}">{'View Ballot' if voted else '🗳️ Cast Vote'}</a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Upcoming
                for up in upcoming_polls:
                    st.markdown(f"""
                    <div class="poll-card-block" style="opacity:0.75;">
                        <span style="display:inline-block;padding:3px 10px;border-radius:100px;background:rgba(148,163,184,0.1);color:#94a3b8;font-size:0.7rem;font-weight:700;text-transform:uppercase;margin-bottom:10px;">⏳ Scheduled</span>
                        <h3 style="margin:0;color:#cbd5e1;font-size:1.1rem;font-weight:700;">{up['name']}</h3>
                        <p style="color:#64748b;font-size:0.8rem;margin:8px 0;height:38px;overflow:hidden;line-height:1.5;">{up.get('description','')}</p>
                        <div style="margin:1.2rem 0;color:#64748b;font-size:0.75rem;background:rgba(255,255,255,0.02);padding:10px;border-radius:8px;border:1px dashed rgba(255,255,255,0.08);">📅 Starts: {up['start_time'].strftime('%d %b, %H:%M') if hasattr(up['start_time'],'strftime') else up['start_time']}</div>
                        <div style="margin-top:auto;">
                            <div class="btn-premium-outline" style="cursor:not-allowed;opacity:0.5;border-style:dashed;color:#475569 !important;">Awaiting Start</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        with tab_past:
            past_polls = get_past_polls()
            if not past_polls:
                st.markdown('<div style="text-align:center;padding:4rem 2rem;color:#64748b;font-style:italic;">No election history available.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="poll-grid">', unsafe_allow_html=True)
                for pp in past_polls:
                    pid = pp["poll_id"]
                    vc = get_poll_vote_counts(pid)
                    winner = max(vc, key=vc.get) if vc else "Decision Pending"
                    voted = has_voted_in_poll(pid, vid)
                    
                    st.markdown(f"""
                    <div class="poll-card-block">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                            <span style="display:inline-block;padding:3px 10px;border-radius:100px;background:rgba(99,102,241,0.1);color:#a5b4fc;font-size:0.7rem;font-weight:700;text-transform:uppercase;">📜 Completed</span>
                            {f'<span style="font-size:0.65rem;background:rgba(16,185,129,0.1);color:#10b981;padding:2px 8px;border-radius:100px;font-weight:600;">✅ Voted</span>' if voted else '<span style="font-size:0.65rem;background:rgba(244,63,94,0.1);color:#f43f5e;padding:2px 8px;border-radius:100px;font-weight:600;">❌ Missed</span>'}
                        </div>
                        <h3 style="margin:0;color:#e2e8f0;font-size:1.15rem;font-weight:700;">{pp['name']}</h3>
                        <div style="margin:1rem 0;color:#6ee7b7;font-size:0.85rem;background:rgba(16,185,129,0.05);padding:12px;border-radius:10px;border:1px solid rgba(16,185,129,0.1);">
                            <span style="color:#64748b;font-size:0.7rem;display:block;margin-bottom:2px;">WINNER</span>
                            <span style="font-weight:700;font-size:1rem;">🏆 {winner}</span>
                        </div>
                        <div style="color:#64748b;font-size:0.75rem;margin-bottom:1.5rem;">📅 Ended: {pp['end_time'].strftime('%d %b %Y') if hasattr(pp['end_time'],'strftime') else pp['end_time']}</div>
                        <div style="margin-top:auto;">
                            <a href="?page=results&user={username}&res_id={pid}" target="_self" class="btn-premium-outline">📈 View Analytics</a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-top:3rem;"></div>', unsafe_allow_html=True)
        logout_col1, logout_col2, logout_col3 = st.columns([1, 1.5, 1])
        with logout_col2:
            if st.button("🚪 Logout to Voter Portal", key="vd_logout_btn_final", use_container_width=True):
                st.session_state.clear()
                st.query_params.clear()
                goto("user")


# ═══════════════════════════════════════════════════════════
# PAGE: FAQ
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "faq":
    st.markdown('<div class="section-title">❓ Frequently Asked Questions</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Everything you need to know about voting on QuVote.</div>', unsafe_allow_html=True)
    st.markdown("---")
    faqs = [
        ("How do I register to vote?", "Click 'Enter Voter Portal' on the homepage, then select 'Register Voter'. Fill in your Voter ID, full name, email, and password. Your registration will be reviewed by the admin and you will be emailed once approved."),
        ("What is OTP verification?", "OTP stands for One-Time Password — a 6-digit code sent to your email. QuVote uses a Quantum Random Number Generator to produce truly unpredictable OTPs, making your login impossible to guess."),
        ("How long is the OTP valid?", "Each OTP is valid for 5 minutes only. If it expires, click 'Resend OTP' to receive a new one."),
        ("Can I change my vote after submitting?", "No. Once you submit your vote, it is permanently and securely recorded. Each Voter ID can only cast one vote to ensure election integrity."),
        ("How is my vote kept secure?", "Your vote is encrypted using SHA-256 hashing and stored in a secure MongoDB Atlas database. A unique receipt hash is generated for every vote."),
        ("What is a Vote Receipt?", "After voting, QuVote generates a unique SHA-256 encrypted string — your vote receipt. It proves your vote was recorded without revealing your candidate choice."),
        ("What if my registration was rejected?", "You will receive an email with the reason. Contact the admin at quantumvoting@gmail.com for clarification. Common reasons: Voter ID mismatch or unverified identity."),
        ("When do polls close?", "The election admin sets the poll closing time. You can see a live countdown timer on the homepage. Once closed, no new votes are accepted."),
        ("How are results announced?", "When polls close, QuVote automatically calculates the winner and emails all registered voters with the full results — winner name, total votes, and per-candidate breakdown."),
        ("Who can I contact for help?", "Submit a query via the 'Submit a Query' button on the vote page, email quantumvoting@gmail.com, or ask our 24/7 Education Bot on the homepage.")
    ]
    for q, a in faqs:
        with st.expander(f"🔹 {q}"):
            st.markdown(f'<p style="color:#94a3b8;line-height:1.8;">{a}</p>', unsafe_allow_html=True)
    st.markdown("---")

# ═══════════════════════════════════════════════════════════
# PAGE: LIVE RESULTS
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "results":
    view_pid = st.session_state.get("view_poll_result_id")
    if view_pid:
        _poll = get_poll(view_pid)
        if not _poll:
            st.session_state.view_poll_result_id = None
            st.rerun()
            
        st.markdown(f'<div class="section-title">📊 {_poll["name"]} Analytics</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-sub">{_poll.get("description","")}</div>', unsafe_allow_html=True)
        if st.button("← Back to Completed Polls", key="res_back_btn"):
            st.session_state.view_poll_result_id = None
            st.rerun()
            
        st.markdown("---")
        vote_counts = get_poll_vote_counts(view_pid)
        total = total_poll_votes(view_pid)
        
        tab_over, tab_cand, tab_charts, tab_export = st.tabs(["Overview & Winner", "Candidate Breakdown", "Charts & Turnout", "Export Data"])
        
        with tab_over:
            if not vote_counts:
                st.info("No votes were cast in this election.")
            else:
                winner = max(vote_counts, key=vote_counts.get)
                st.markdown(f'''
                <div style="background:linear-gradient(135deg,rgba(16,185,129,0.15),rgba(99,102,241,0.1));
                     border:1px solid rgba(16,185,129,0.4);border-radius:16px;padding:2rem;text-align:center;margin-bottom:1rem;">
                  <div style="font-size:3rem;margin-bottom:10px;">🏆</div>
                  <div style="color:#6ee7b7;font-weight:700;font-size:1.5rem;">Winner: {winner}</div>
                  <div style="color:#94a3b8;margin-top:10px;">Total Election Votes: {total}</div>
                </div>''', unsafe_allow_html=True)

        with tab_cand:
            st.markdown("### Candidate Vote Counts")
            for c, v in sorted(vote_counts.items(), key=lambda item: item[1], reverse=True):
                pct = round(v/total*100, 1) if total else 0
                st.markdown(f"**{c}**: {v} votes ({pct}%)")
                st.progress(pct/100)
                
        with tab_charts:
            eligible = total_eligible_voters()
            participated = total
            turnout_pct = (participated / eligible * 100) if eligible > 0 else 0
            
            st.markdown("### 📈 Turnout Analysis")
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Total Eligible", eligible)
            with col_m2:
                st.metric("Votes Cast", participated)
            with col_m3:
                st.metric("Turnout %", f"{round(turnout_pct, 1)}%", delta=f"{participated} Voted", delta_color="normal")
            
            st.markdown('<div style="margin-top:2rem;"></div>', unsafe_allow_html=True)
            
            if total > 0:
                inner_col1, inner_col2 = st.columns([1, 1])
                
                with inner_col1:
                    st.markdown("#### 🗳️ Vote Distribution")
                    if go:
                        cands_list = list(vote_counts.keys())
                        counts_list = list(vote_counts.values())
                        cols_palette = ["#6366f1","#06b6d4","#10b981","#f59e0b","#f43f5e"]
                        fig = go.Figure(go.Pie(
                            labels=cands_list, values=counts_list, hole=0.45,
                            marker=dict(colors=cols_palette[:len(cands_list)], line=dict(color='#0f172a', width=3)),
                            textinfo="label+percent", textfont=dict(color="#e2e8f0", size=14),
                        ))
                        fig.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0", family="Inter"),
                            margin=dict(t=10,b=10,l=10,r=10), showlegend=True,
                            legend=dict(font=dict(color="#94a3b8", size=12), bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.1),
                            annotations=[dict(text=f"<b>{total}</b><br><span style='font-size:10px'>Votes</span>",
                                              font=dict(size=18, color="#a5b4fc"), showarrow=False)]
                        )
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.warning("Plotly visualization unavailable. Please check installation.")
                
                with inner_col2:
                    st.markdown("#### 📊 Participation Rate")
                    non_voters = eligible - participated
                    if go:
                        fig_turnout = go.Figure(go.Pie(
                            labels=["Voted", "Not Voted"],
                            values=[participated, max(0, non_voters)],
                            marker=dict(colors=["#6366f1", "rgba(148, 163, 184, 0.1)"], line=dict(color='#0f172a', width=2)),
                            textinfo="none", hole=0.7
                        ))
                        fig_turnout.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                            margin=dict(t=10,b=10,l=10,r=10),
                            annotations=[dict(text=f"<b>{round(turnout_pct, 1)}%</b>",
                                              font=dict(size=24, color="#6366f1", family="Inter"), showarrow=False)]
                        )
                        st.plotly_chart(fig_turnout, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.progress(turnout_pct / 100)
                        st.markdown(f'<div style="text-align:center;color:#94a3b8;">{round(turnout_pct, 1)}% Participation</div>', unsafe_allow_html=True)
            else:
                st.info("No votes have been cast yet. Analytics will appear once election starts.")
                
        with tab_export:
            st.markdown("### 📄 Download Election Results Report")
            if not vote_counts:
                st.info("No votes cast yet.")
            else:
                winner_pdf = max(vote_counts, key=vote_counts.get)
                gen_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

                import csv, io
                csv_buf = io.StringIO()
                writer = csv.writer(csv_buf)
                writer.writerow([f"QuVote - Official Election Results: {_poll['name']}"])
                writer.writerow(["Generated", gen_time])
                writer.writerow([])
                writer.writerow(["Candidate", "Votes", "Share %"])
                for c, v in sorted(vote_counts.items(), key=lambda item: item[1], reverse=True):
                    pct = round(v/total*100, 2) if total else 0
                    writer.writerow([c, v, f"{pct}%"])
                writer.writerow([])
                writer.writerow(["Total Votes Cast", total])
                writer.writerow(["WINNER", winner_pdf])
                
                st.download_button("⬇️ Download CSV Report", data=csv_buf.getvalue(), file_name=f"QuVote_Results_{view_pid}.csv", mime="text/csv", use_container_width=True)

                rows_html = "".join([
                    f"<tr><td>{c}</td><td style='text-align:center'>{v}</td><td style='text-align:center'>{round(v/total*100,2) if total else 0}%</td></tr>"
                    for c, v in sorted(vote_counts.items(), key=lambda item: item[1], reverse=True)
                ])
                html_report = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>QuVote Results</title>
<style>
  body{{font-family:Arial,sans-serif;background:#0f172a;color:#e2e8f0;padding:40px;}}
  h1{{color:#a5b4fc;text-align:center;}} h3{{color:#6ee7b7;text-align:center;}}
  table{{width:100%;border-collapse:collapse;margin-top:20px;}}
  th{{background:#1e293b;color:#a5b4fc;padding:10px;border:1px solid #334155;}}
  td{{padding:10px;border:1px solid #334155;}}
  .meta{{color:#64748b;text-align:center;margin-bottom:20px;font-size:0.9rem;}}
  .winner{{background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);border-radius:8px;padding:16px;text-align:center;margin-top:24px;}}
</style></head><body>
<h1>⚛️ QuVote — Official Election Results: {_poll['name']}</h1>
<p class="meta">Generated: {gen_time} &nbsp;|&nbsp; Total Votes Cast: <strong>{total}</strong></p>
<table><thead><tr><th>Candidate</th><th>Votes</th><th>Share %</th></tr></thead><tbody>{rows_html}</tbody></table>
<div class="winner"><h3>🏆 Winner: {winner_pdf}</h3></div>
</body></html>"""
                st.download_button("🖨️ Download HTML Report (Print to PDF)", data=html_report, file_name=f"QuVote_Results_{view_pid}.html", mime="text/html", use_container_width=True)

    else:
        st.markdown('<div class="section-title">📜 Completed Polls</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Select an election to view detailed occupancy analytics.</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        past_polls = get_past_polls()
        if not past_polls:
            st.info("No completed elections found.")
        else:
            for pp in past_polls:
                vc = get_poll_vote_counts(pp["poll_id"])
                total_v = sum(vc.values()) if vc else 0
                winner_t = max(vc, key=vc.get) if vc else "N/A"
                st.markdown(f'''
                <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
                     border-radius:12px;padding:1.5rem;margin-bottom:1rem;display:flex;justify-content:space-between;align-items:center;">
                  <div>
                    <h3 style="margin:0;color:#e2e8f0;">{pp["name"]}</h3>
                    <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:rgba(16,185,129,0.1);color:#6ee7b7;font-size:0.75rem;margin:8px 0;font-weight:600;">✅ Completed</span>
                    <div style="color:#64748b;font-size:0.85rem;">Ended: {pp["end_time"].strftime("%d %b %Y, %H:%M") if hasattr(pp["end_time"], "strftime") else pp["end_time"]}</div>
                    <div style="color:#94a3b8;font-size:0.9rem;margin-top:8px;">Total Votes: {total_v} &bull; Winner: <b>{winner_t}</b></div>
                  </div>
                </div>''', unsafe_allow_html=True)
                if st.button("📊 View Details", key=f"view_res_{pp['poll_id']}"):
                    st.session_state.view_poll_result_id = pp["poll_id"]
                    st.rerun()

        st.markdown("---")
        if st.button("← Back to Voter Dashboard", key="results_back"): goto("voter_dashboard")
