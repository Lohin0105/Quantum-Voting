import streamlit as st
import hashlib, time, secrets, requests, os, base64
import cv2, numpy as np
from dotenv import load_dotenv
from datetime import datetime, timezone
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
  max-width: 900px;
  margin: 0 auto 2.5rem;
}

/* ══════════════════════════════════════════
   CARDS
══════════════════════════════════════════ */
/* ── CARDS & PANELS ───────────────────────── */
.card {
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 24px;
  padding: 2rem;
  margin: 1rem 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.card:hover { 
  border-color: rgba(99,102,241,0.4);
  background: rgba(255,255,255,0.05);
  box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}

.poll-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.poll-card-block {
  background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 1.8rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}
.poll-card-block:hover {
  transform: translateY(-5px);
  border-color: rgba(99,102,241,0.3);
  box-shadow: 0 15px 35px rgba(0,0,0,0.4);
}
.poll-card-block::before {
  content: "";
  position: absolute;
  top: 0; left: 0; width: 100%; height: 4px;
  background: var(--grad);
  opacity: 0.8;
}

.btn-premium {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  background: var(--grad);
  color: white !important;
  border-radius: 12px;
  font-weight: 700;
  text-decoration: none !important;
  transition: all 0.2s ease;
  border: none;
  cursor: pointer;
  width: 100%;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.85rem;
}
.btn-premium:hover {
  transform: scale(1.02);
  filter: brightness(1.1);
  box-shadow: 0 8px 20px rgba(99,102,241,0.4);
}
.btn-premium-outline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 11px 23px;
  background: transparent;
  color: #a5b4fc !important;
  border: 1px solid rgba(99,102,241,0.4);
  border-radius: 12px;
  font-weight: 600;
  text-decoration: none !important;
  transition: all 0.2s ease;
  cursor: pointer;
  width: 100%;
  font-size: 0.85rem;
}
.btn-premium-outline:hover {
  background: rgba(99,102,241,0.1);
  border-color: rgba(99,102,241,0.8);
}

.stat-box {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  padding: 1.2rem;
  text-align: center;
}
.stat-box .label { color: var(--muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.stat-box .value { color: #f8fafc; font-size: 1.4rem; font-weight: 800; font-family: 'Space Grotesk', sans-serif; }

.panel-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 2.2rem;
  text-align: center;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  cursor: pointer;
  height: 280px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  position: relative;
  overflow: hidden;
}
.panel-card:hover {
  border-color: rgba(99,102,241,0.4);
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  background: rgba(255,255,255,0.06);
}
.panel-card::after {
  content: "";
  position: absolute;
  top: -50%; left: -50%; width: 200%; height: 200%;
  background: radial-gradient(circle, rgba(99,102,241,0.1) 0%, transparent 70%);
  opacity: 0; transition: opacity 0.3s;
}
.panel-card:hover::after { opacity: 1; }

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
div[data-baseweb="input"], div[data-baseweb="textarea"] {
  background: rgba(15, 23, 42, 0.6) !important;
  border: 1px solid rgba(99, 102, 241, 0.3) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease !important;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.1) !important;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within {
  border-color: #6366f1 !important;
  background: rgba(15, 23, 42, 0.9) !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
}
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
  color: #e2e8f0 !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 1.05rem !important;
  padding: 12px 16px !important;
  background: transparent !important;
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
    """Generate candidate symbol image via Pollinations.ai."""
    try:
        import urllib.parse
        prompt = symbol_name + " election symbol flat vector icon colorful white background clean simple"
        prompt_enc = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{prompt_enc}?width=256&height=256&nologo=true"
        resp = requests.get(url, timeout=20)
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
            <p>Manage candidates, voter rolls, and live election results.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Admin Console", key="home_admin", use_container_width=True):
            goto("admin")

    with col3:
        st.markdown("""
        <div class="panel-card">
            <span class="icon">
                <svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(16,185,129,0.4));">
                    <defs>
                        <linearGradient id="aiGrad" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#10b981"/>
                            <stop offset="1" stop-color="#059669"/>
                        </linearGradient>
                    </defs>
                    <rect x="4" y="6" width="16" height="12" rx="3" fill="url(#aiGrad)" fill-opacity="0.9" stroke="#6ee7b7" stroke-width="1.2"/>
                    <path d="M8 22H16" stroke="#6ee7b7" stroke-width="2" stroke-linecap="round"/>
                    <path d="M12 18V22" stroke="#6ee7b7" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="8" cy="11" r="1.5" fill="#ffffff"/>
                    <circle cx="16" cy="11" r="1.5" fill="#ffffff"/>
                    <path d="M10 14H14" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round"/>
                    <path d="M12 3V6" stroke="#6ee7b7" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="12" cy="2" r="1" fill="#6ee7b7"/>
                </svg>
            </span>
            <h3>Education Bot</h3>
            <p>Ask our multilingual AI any questions about the voting process.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ask Assistant", key="home_bot", use_container_width=True):
            goto("assistant")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Winner Banner
    if get_winner_announced():
        vote_counts = get_vote_counts()
        if vote_counts:
            winner = max(vote_counts, key=vote_counts.get)
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,rgba(16,185,129,0.15),rgba(99,102,241,0.1));
                 border:1px solid rgba(16,185,129,0.4);border-radius:16px;padding:1.5rem;text-align:center;margin:1rem 0;">
                <div style="font-size:2rem;margin-bottom:6px;">🏆</div>
                <div style="color:#6ee7b7;font-weight:700;font-size:1.1rem;">Election Results Declared!</div>
                <div style="color:#fff;font-size:1.6rem;font-weight:800;margin:8px 0;">{winner}</div>
                <div style="color:#64748b;font-size:0.88rem;">Results have been emailed to all registered voters.</div>
            </div>
            """, unsafe_allow_html=True)

    # Election Countdown Timer
    end_time = get_election_end_time()
    if end_time and not get_winner_announced():
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
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        if st.button("📊 Live Results", key="home_results", use_container_width=True):
            goto("results")
    with hc2:
        if st.button("❓ FAQ", key="home_faq", use_container_width=True):
            goto("faq")
    with hc3:
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

# PAGE: ADMIN MENU
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "admin":
    st.markdown('<div class="section-title">Admin Console Menu</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Authorized personnel only. Choose an action.</div>', unsafe_allow_html=True)
    
    ac1, ac2 = st.columns(2, gap="medium")
    with ac1:
        st.markdown("""
        <div class="panel-card">
            <span class="icon">
                <svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(139,92,246,0.4));">
                    <defs>
                        <linearGradient id="accGrad" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#8b5cf6"/>
                            <stop offset="1" stop-color="#6366f1"/>
                        </linearGradient>
                    </defs>
                    <path d="M12 12C14.2091 12 16 10.2091 16 8C16 5.79086 14.2091 4 12 4C9.79086 4 8 5.79086 8 8C8 10.2091 9.79086 12 12 12Z" fill="url(#accGrad)" fill-opacity="0.9" stroke="#c4b5fd" stroke-width="1.2"/>
                    <path d="M18 20V19C18 16.2386 15.7614 14 13 14H11C8.23858 14 6 16.2386 6 19V20" stroke="#c4b5fd" stroke-width="1.5" stroke-linecap="round"/>
                    <path d="M15 11L17 13L21 9" stroke="#6ee7b7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </span>
            <h3>Register Admin</h3>
            <p>Onboard a new authorized administrator.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Proceed to Register", key="menu_admin_reg", use_container_width=True):
            goto("admin_register")
            
    with ac2:
        st.markdown("""
        <div class="panel-card">
            <span class="icon">
                <svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(244,63,94,0.4));">
                    <defs>
                        <linearGradient id="alogGrad" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#f43f5e"/>
                            <stop offset="1" stop-color="#be123c"/>
                        </linearGradient>
                    </defs>
                    <rect x="5" y="11" width="14" height="10" rx="2" fill="url(#alogGrad)" fill-opacity="0.9" stroke="#fda4af" stroke-width="1.5"/>
                    <path d="M8 11V7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7V11" stroke="#fda4af" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="12" cy="16" r="1.5" fill="#ffffff"/>
                </svg>
            </span>
            <h3>Admin Login</h3>
            <p>Access the core election dashboard.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Proceed to Login", key="menu_admin_login", use_container_width=True):
            goto("admin_login")

if st.session_state.page == "admin_register":
    st.markdown('<div class="section-title">🆕 Register Admin</div>', unsafe_allow_html=True)
    st.markdown("---")
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

    if st.button("← Back to Menu", key="back_from_areg"):
        goto("admin")

if st.session_state.page == "admin_login":
    st.markdown('<div class="section-title">🔐 Admin Login</div>', unsafe_allow_html=True)
    st.markdown("---")
    a_name = st.text_input("Admin Username", key="admin_login_name")
    a_pwd  = st.text_input("Password", type="password", key="admin_login_pwd")
    if st.button("🔓 Login as Admin", key="admin_login_btn"):
        doc = get_user(a_name)
        if doc and doc["password"] == hash_data(a_pwd) and doc.get("role") == "admin":
            st.session_state.admin = a_name
            goto("dashboard")
        else:
            st.error("❌ Invalid credentials or not an admin account.")

    if st.button("← Back to Menu", key="back_from_alogin"):
        goto("admin")

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

    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "📊 Results", "🏛️ Candidates", "📋 Voter Roll", "💬 Queries", "👥 Users", "✅ Pending Users", "🗳️ Polls"
    ])

    # ── TAB 1: RESULTS ──────────────────────────────────────
    with t1:
        import datetime as _dt_r
        all_polls_r = get_all_polls()

        # — Poll-based results (grouped by poll) ————————————
        if all_polls_r:
            st.markdown("### 🗳️ Election Poll Results")
            for _pr in all_polls_r:
                _prid   = _pr["poll_id"]
                _prname = _pr["name"]
                _pr_total = total_poll_votes(_prid)
                _pr_votes = get_poll_vote_counts(_prid)
                _pr_cands = get_poll_candidates(_prid)
                _now_r = _dt_r.datetime.now()
                _status_r = ("🟢 Active"    if _pr["start_time"] <= _now_r <= _pr["end_time"]
                             else ("🔜 Upcoming" if _now_r < _pr["start_time"] else "🔴 Ended"))

                st.markdown(f"""
                <div style='background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.25);
                     border-radius:14px;padding:1rem 1.2rem;margin:0.8rem 0;'>
                  <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                      <span style='font-size:1rem;font-weight:700;color:#a5b4fc;'>{_prname}</span>
                      &nbsp;<span style='font-size:0.75rem;color:#64748b;'>{_status_r}</span>
                    </div>
                    <span style='font-size:0.82rem;color:#64748b;'>{_pr_total} votes</span>
                  </div>
                </div>""", unsafe_allow_html=True)

                if not _pr_cands:
                    st.caption("No candidates in this poll.")
                elif _pr_total == 0:
                    st.caption("No votes cast yet in this poll.")
                    for _prc in _pr_cands:
                        st.markdown(f"""
                        <div class='result-row'>
                          <span style='font-weight:600;color:#e2e8f0;'>{_prc['name']}</span>
                          <span style='color:#64748b;'>0 votes</span>
                        </div>""", unsafe_allow_html=True)
                else:
                    _pr_max = max(_pr_votes.values()) if _pr_votes else 0
                    for _prc in sorted(_pr_cands, key=lambda x: _pr_votes.get(x["name"],0), reverse=True):
                        _prc_cnt = _pr_votes.get(_prc["name"], 0)
                        _prc_pct = round(_prc_cnt / _pr_total * 100, 1) if _pr_total else 0
                        _is_lead = _prc_cnt == _pr_max and _pr_max > 0
                        _pill_l  = '<span class="pill pill-green">Leading</span>' if _is_lead else ''
                        _img_b   = _prc.get("symbol_image_b64","")
                        _thumb   = (f"<img src='data:image/png;base64,{_img_b}' width='32' height='32' "
                                    f"style='border-radius:6px;margin-right:10px;vertical-align:middle;'>" if _img_b
                                    else f"<span style='font-size:1.4rem;margin-right:10px;'>{_prc.get('symbol','🗳️')}</span>")
                        st.markdown(f"""
                        <div class='result-row' style='margin:4px 0;'>
                          <div style='display:flex;align-items:center;'>
                            {_thumb}
                            <span style='font-weight:600;color:#e2e8f0;'>{_prc["name"]}</span>
                            &nbsp;{_pill_l}
                          </div>
                          <div style='font-family:\'Space Grotesk\',sans-serif;font-size:1.1rem;
                               font-weight:700;color:#a5b4fc;'>{_prc_cnt}</div>
                        </div>
                        <div class='result-bar-wrap'>
                          <div class='result-bar' style='width:{_prc_pct}%;'></div>
                        </div>""", unsafe_allow_html=True)
                    # Poll pie chart
                    if go and _pr_total > 0:
                        _pc_labels = [c["name"] for c in _pr_cands]
                        _pc_values = [_pr_votes.get(c["name"],0) for c in _pr_cands]
                        _clrs_r    = ["#6366f1","#06b6d4","#10b981","#f59e0b","#f43f5e"]
                        _fig_r = go.Figure(go.Pie(
                            labels=_pc_labels, values=_pc_values, hole=0.45,
                            marker=dict(colors=_clrs_r[:len(_pc_labels)],
                                        line=dict(color='#0f172a',width=3)),
                            textinfo="label+percent",
                            textfont=dict(color="#e2e8f0",size=13),
                        ))
                        _fig_r.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#e2e8f0",family="Inter"),
                            margin=dict(t=20,b=20,l=20,r=20), showlegend=True,
                            legend=dict(font=dict(color="#94a3b8",size=11),bgcolor="rgba(0,0,0,0)"),
                            annotations=[dict(text=f"<b>{_pr_total}</b><br>votes",
                                             font=dict(size=14,color="#a5b4fc"),showarrow=False)]
                        )
                        st.plotly_chart(_fig_r, use_container_width=True, key=f"pie_{_prid}")
            st.markdown("---")

        # — Legacy global results ———————————————————
        votes  = get_vote_counts()
        cands  = get_candidate_names()
        if cands and vt > 0:
            with st.expander("📊 Legacy Global Votes", expanded=not all_polls_r):
                result = {c: votes.get(c, 0) for c in cands}
                max_v  = max(result.values()) if result else 0
                for cand, count in sorted(result.items(), key=lambda x: x[1], reverse=True):
                    pct_bar = (count / vt * 100) if vt > 0 else 0
                    is_lead = count == max_v and max_v > 0
                    pill = '<span class="pill pill-green">Leading</span>' if is_lead else ''
                    st.markdown(f"""
                    <div class="result-row">
                        <div><span style="font-weight:700;color:#e2e8f0">{cand}</span>&nbsp;{pill}</div>
                        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;
                             font-weight:700;color:#a5b4fc">{count}</div>
                    </div>
                    <div class="result-bar-wrap">
                        <div class="result-bar" style="width:{pct_bar:.1f}%"></div>
                    </div>""", unsafe_allow_html=True)
                winners = [k for k,v in result.items() if v==max_v and max_v>0]
                if len(winners)==1:
                    st.success(f"🏆 **{winners[0]}** leads with {max_v} votes")
                elif len(winners)>1:
                    st.warning(f"🤝 Tie: {', '.join(winners)}")
        elif not all_polls_r:
            st.info("No votes or candidates yet.")
    # ── TAB 2: CANDIDATE MANAGER ────────────────────────────
    with t2:
        # — Poll candidates grouped by poll ——————————————
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



    # ── TAB 7: POLLS ──────────────────────────────────────
    with t7:
        import datetime as dt_mod2
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
                p_start = dt_mod2.datetime.combine(p_start_date, p_start_ti)
                p_end   = dt_mod2.datetime.combine(p_end_date, p_end_ti)
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
                now_u = dt_mod2.datetime.now()
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
                                    gimg = generate_symbol_image(nc_sym.strip())
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
        
        # (Direct link box removed as per request)
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
    if st.button("← Back to Voter Dashboard", key="faq_back"):
        goto("voter_dashboard")

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
            if go and total > 0:
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
                    margin=dict(t=30,b=30,l=20,r=20), showlegend=True,
                    legend=dict(font=dict(color="#94a3b8", size=13), bgcolor="rgba(0,0,0,0)"),
                    annotations=[dict(text=f"<b>{total}</b><br><span style='font-size:10px'>Total Votes</span>",
                                      font=dict(size=18, color="#a5b4fc"), showarrow=False)]
                )
                st.plotly_chart(fig, use_container_width=True)
                
        with tab_export:
            st.markdown("### 📄 Download Election Results Report")
            if not vote_counts:
                st.info("No votes cast yet.")
            else:
                winner_pdf = max(vote_counts, key=vote_counts.get)
                gen_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

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
        st.markdown('<div class="section-sub">Select an election to view detailed module analytics.</div>', unsafe_allow_html=True)
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




