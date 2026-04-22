import streamlit as st
import random, base64, requests
try:
    import plotly.graph_objects as go
except ImportError:
    go = None

# ── PREMIUM CSS ──────────────────────────────────────────
PREMIUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');

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

#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.4); border-radius: 3px; }

.hero-wrap { text-align: center; padding: 3rem 1rem 2.5rem; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.3);
  border-radius: 100px; padding: 6px 18px; font-size: 0.78rem; font-weight: 600;
  color: #a5b4fc; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 1.5rem;
}
.hero-title {
  font-family: 'Space Grotesk', sans-serif; font-size: clamp(2.6rem, 6vw, 4rem);
  font-weight: 800; line-height: 1.1;
  background: linear-gradient(135deg, #a5b4fc 0%, #c4b5fd 50%, #67e8f9 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: 1rem;
}
.hero-sub { color: #64748b; font-size: 1.05rem; line-height: 1.7; max-width: 900px; margin: 0 auto 2.5rem; }

.card {
  background: rgba(255,255,255,0.03); backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 24px;
  padding: 2rem; margin: 1rem 0; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.card:hover { border-color: rgba(99,102,241,0.4); background: rgba(255,255,255,0.05); box-shadow: 0 20px 40px rgba(0,0,0,0.3); }

.poll-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; margin: 2rem 0; }
.poll-card-block {
  background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
  backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px;
  padding: 1.8rem; height: 100%; display: flex; flex-direction: column; transition: all 0.3s ease;
  position: relative; overflow: hidden;
}
.poll-card-block:hover { transform: translateY(-5px); border-color: rgba(99,102,241,0.3); box-shadow: 0 15px 35px rgba(0,0,0,0.4); }
.poll-card-block::before { content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: var(--grad); opacity: 0.8; }

.btn-premium {
  display: inline-flex; align-items: center; justify-content: center; padding: 12px 24px;
  background: var(--grad); color: white !important; border-radius: 12px; font-weight: 700;
  text-decoration: none !important; transition: all 0.2s ease; border: none; cursor: pointer;
  width: 100%; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.85rem;
}
.btn-premium:hover { transform: scale(1.02); filter: brightness(1.1); box-shadow: 0 8px 20px rgba(99,102,241,0.4); }

.panel-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
  border: 1px solid var(--border); border-radius: 24px; padding: 2.2rem; text-align: center;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); cursor: pointer; height: 280px;
  display: flex; flex-direction: column; justify-content: space-between; align-items: center;
  position: relative; overflow: hidden;
}
.panel-card:hover { border-color: rgba(99,102,241,0.4); transform: translateY(-8px) scale(1.02); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); background: rgba(255,255,255,0.06); }

.section-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.3rem; }
.section-sub { color: #64748b; font-size: 0.9rem; margin-bottom: 1.8rem; }
.divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(99,102,241,0.4), transparent); margin: 1.8rem 0; }

.stat-chip {
  flex: 1; min-width: 110px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px; padding: 1rem 1.2rem; text-align: center;
}
.stat-chip .num { font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; color: #a5b4fc; display: block; }
.stat-chip .lbl { font-size: 0.78rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }

.cand-card {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px; padding: 1.1rem 1.4rem; display: flex; align-items: center; gap: 14px; margin: 8px 0; transition: all 0.2s ease;
}
.cand-card:hover { border-color: rgba(99,102,241,0.4); background: rgba(99,102,241,0.06); }

div[data-baseweb="input"], div[data-baseweb="textarea"] {
  background: rgba(15, 23, 42, 0.6) !important; border: 1px solid rgba(99, 102, 241, 0.3) !important;
  border-radius: 12px !important; transition: all 0.3s ease !important;
}
.stButton > button {
  background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.1) !important;
  border-radius: 12px !important; color: #c7d2fe !important; font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important; transition: all 0.2s ease !important; width: 100% !important;
}
.stButton > button:hover { background: rgba(99,102,241,0.15) !important; border-color: rgba(99,102,241,0.5) !important; transform: translateY(-1px) !important; }

[data-testid="stMetric"] { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 16px !important; padding: 1.2rem !important; }
[data-testid="stMetricValue"] { font-family: 'Space Grotesk', sans-serif !important; color: #a5b4fc !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: rgba(255,255,255,0.03) !important; border-radius: 14px !important; padding: 5px !important; }
.stTabs [aria-selected="true"] { background: rgba(99,102,241,0.18) !important; color: #a5b4fc !important; }

@media (max-width: 768px) {
  .block-container { padding: 1.5rem 1rem 3rem !important; }
  .hero-title { font-size: 2.2rem !important; }
  .stat-chip { min-width: 46%; }
}
</style>
"""

# ── SVG ASSETS ──────────────────────────────────────────
ICON_USER = """
<svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(6,182,212,0.4));">
    <defs><linearGradient id="userGrad" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse"><stop stop-color="#06b6d4"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
    <circle cx="12" cy="7" r="4.5" fill="url(#userGrad)" fill-opacity="0.9" stroke="#a5f3fc" stroke-width="1.2"/>
    <path d="M4.5 20.5C4.5 16.9101 7.85786 14 12 14C16.1421 14 19.5 16.9101 19.5 20.5C19.5 20.7761 19.2761 21 19 21H5C4.72386 21 4.5 20.7761 4.5 20.5Z" fill="url(#userGrad)" fill-opacity="0.9" stroke="#a5f3fc" stroke-width="1.2"/>
</svg>
"""

ICON_ADMIN = """
<svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(139,92,246,0.4));">
    <defs><linearGradient id="shieldGrad" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse"><stop stop-color="#8b5cf6"/><stop offset="1" stop-color="#6366f1"/></linearGradient></defs>
    <path d="M12 22C12 22 20 18 20 12V5L12 2L4 5V12C4 18 12 22 12 22Z" fill="url(#shieldGrad)" fill-opacity="0.9" stroke="#c4b5fd" stroke-width="1.5" stroke-linejoin="round"/>
    <path d="M12 8C10.8954 8 10 8.89543 10 10V11H9.5C8.67157 11 8 11.6716 8 12.5V14.5C8 15.3284 8.67157 16 9.5 16H14.5C15.3284 16 16 15.3284 16 14.5V12.5C16 11.6716 15.3284 11 14.5 11H14V10C14 8.89543 13.1046 8 12 8ZM11 10C11 9.44772 11.4477 9 12 9C12.5523 9 13 9.44772 13 10V11H11V10Z" fill="#ffffff"/>
</svg>
"""

ICON_AI = """
<svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(16,185,129,0.4));">
    <defs><linearGradient id="aiGrad" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse"><stop stop-color="#10b981"/><stop offset="1" stop-color="#059669"/></linearGradient></defs>
    <rect x="4" y="6" width="16" height="12" rx="3" fill="url(#aiGrad)" fill-opacity="0.9" stroke="#6ee7b7" stroke-width="1.2"/>
    <path d="M8 22H16" stroke="#6ee7b7" stroke-width="2" stroke-linecap="round"/><path d="M12 18V22" stroke="#6ee7b7" stroke-width="2" stroke-linecap="round"/>
    <circle cx="8" cy="11" r="1.5" fill="#ffffff"/><circle cx="16" cy="11" r="1.5" fill="#ffffff"/><path d="M10 14H14" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M12 3V6" stroke="#6ee7b7" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="2" r="1" fill="#6ee7b7"/>
</svg>
"""

ICON_ADMIN_LOGIN = """
<svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(139,92,246,0.4));">
    <defs><linearGradient id="accGrad" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse"><stop stop-color="#8b5cf6"/><stop offset="1" stop-color="#6366f1"/></linearGradient></defs>
    <path d="M12 12C14.2091 12 16 10.2091 16 8C16 5.79086 14.2091 4 12 4C9.79086 4 8 5.79086 8 8C8 10.2091 9.79086 12 12 12Z" fill="url(#accGrad)" fill-opacity="0.9" stroke="#c4b5fd" stroke-width="1.2"/><path d="M18 20V19C18 16.2386 15.7614 14 13 14H11C8.23858 14 6 16.2386 6 19V20" stroke="#c4b5fd" stroke-width="1.5" stroke-linecap="round"/>
</svg>
"""

ICON_ADMIN_REG = """
<svg width="68" height="68" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 8px 16px rgba(16,185,129,0.4));">
    <defs><linearGradient id="accRegReq" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse"><stop stop-color="#10b981"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
    <path d="M12 12C14.2091 12 16 10.2091 16 8C16 5.79086 14.2091 4 12 4C9.79086 4 8 5.79086 8 8C8 10.2091 9.79086 12 12 12Z" fill="url(#accRegReq)" fill-opacity="0.9" stroke="#6ee7b7" stroke-width="1.2"/><path d="M12 14C7.58172 14 4 16.6863 4 20H20C20 16.6863 16.4183 14 12 14Z" fill="url(#accRegReq)" fill-opacity="0.9" stroke="#6ee7b7" stroke-width="1.2"/><path d="M19 8V12M17 10H21" stroke="#6ee7b7" stroke-width="2" stroke-linecap="round"/>
</svg>
"""

# ── HELPERS ──────────────────────────────────────────────
def inject_custom_css():
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

def render_poll_analytics(votes_dict):
    """Render a beautiful Plotly pie chart for poll results."""
    if not go or not votes_dict or sum(votes_dict.values()) == 0:
        return
    
    labels = list(votes_dict.keys())
    values = list(votes_dict.values())
    
    # Custom color palette matching the glassmorphism theme
    colors = ['#8b5cf6', '#6366f1', '#06b6d4', '#10b981', '#f43f5e', '#f59e0b']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.4,
        marker=dict(colors=colors, line=dict(color='rgba(255,255,255,0.1)', width=2)),
        textinfo='label+percent',
        hoverinfo='label+value+percent'
    )])
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0', family='Inter, sans-serif'),
        margin=dict(t=30, b=0, l=0, r=0),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=320
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def generate_symbol_image(description):
    """Generate a high-fidelity candidate symbol using Pollinations AI with randomized seeding."""
    try:
        # Improved prompt for professional, clean election symbols
        clean_desc = description.strip().replace(" ", "+")
        seed = random.randint(1, 1000000)
        prompt = f"ultra-high+resolution+professional+election+symbol+of+{clean_desc},vector+style,minimalist+icon,white+background,sharp+edges"
        url = f"https://image.pollinations.ai/prompt/{prompt}?width=512&height=512&seed={seed}&nologo=true"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
    except Exception:
        pass
    return None
