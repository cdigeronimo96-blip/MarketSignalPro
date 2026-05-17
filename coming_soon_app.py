
import os
import re
import json
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="MarketSignalPro | Coming Soon",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CONFIG
# ============================================================
ADMIN_EMAIL = st.secrets.get("ADMIN_EMAIL", "support@marketsignalpro.com")
RESEND_API_KEY = st.secrets.get("RESEND_API_KEY", "")
FROM_EMAIL = st.secrets.get("FROM_EMAIL", "MarketSignalPro <support@marketsignalpro.com>")
SIGNUPS_FILE = "marketsignalpro_signups.csv"


# ============================================================
# SIGNUP STORAGE + EMAIL
# ============================================================
def load_signups() -> pd.DataFrame:
    columns = ["timestamp", "name", "email", "source"]
    if not os.path.exists(SIGNUPS_FILE):
        return pd.DataFrame(columns=columns)

    try:
        df = pd.read_csv(SIGNUPS_FILE)
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df[columns]
    except Exception:
        return pd.DataFrame(columns=columns)


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()))


def save_signup(name: str, email: str, source: str = "coming_soon"):
    df = load_signups()
    clean_name = " ".join(name.strip().split())
    clean_email = email.strip().lower()

    if not clean_name:
        return False, "Please enter your name."

    if not is_valid_email(clean_email):
        return False, "Please enter a valid email address."

    if not df.empty and clean_email in df["email"].astype(str).str.lower().values:
        return False, "You are already on the early-access list."

    row = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "name": clean_name,
        "email": clean_email,
        "source": source,
    }

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(SIGNUPS_FILE, index=False)
    return True, row


def send_signup_email(row: dict):
    if not RESEND_API_KEY:
        return False, "Signup saved, but RESEND_API_KEY is not set in Streamlit secrets."

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;background:#07090f;color:#e2e8f0;padding:32px;border-radius:14px;">
      <h2 style="margin:0 0 14px;color:#ffffff;">Market<span style="color:#f59e0b;">Signal</span>Pro</h2>
      <h3 style="margin:0 0 20px;color:#60a5fa;">New early-access signup</h3>
      <p><strong>Name:</strong> {row["name"]}</p>
      <p><strong>Email:</strong> {row["email"]}</p>
      <p><strong>Time:</strong> {row["timestamp"]}</p>
      <p style="color:#7c8fae;font-size:12px;margin-top:24px;">This was submitted from the MarketSignalPro coming-soon page.</p>
    </div>
    """

    payload = {
        "from": FROM_EMAIL,
        "to": [ADMIN_EMAIL],
        "subject": "New MarketSignalPro early-access signup",
        "html": html,
        "text": (
            "New MarketSignalPro early-access signup\n\n"
            f"Name: {row['name']}\n"
            f"Email: {row['email']}\n"
            f"Time: {row['timestamp']}\n"
        ),
    }

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=12,
        )

        if response.status_code in (200, 201):
            return True, None

        return False, f"Resend error {response.status_code}: {response.text}"
    except Exception as exc:
        return False, f"Resend request failed: {exc}"


# ============================================================
# GLOBAL CSS
# ============================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700;800&display=swap');

:root {
    --bg: #05070d;
    --panel: rgba(11,18,32,.78);
    --line: rgba(255,255,255,.10);
    --text: #edf4ff;
    --muted: #7c8fae;
    --blue: #2563eb;
    --blue2: #60a5fa;
    --gold: #f59e0b;
    --green: #22c55e;
}

* { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 16% 16%, rgba(37,99,235,.18), transparent 30%),
        radial-gradient(circle at 88% 12%, rgba(245,158,11,.16), transparent 25%),
        radial-gradient(circle at 70% 86%, rgba(34,197,94,.13), transparent 28%),
        linear-gradient(180deg, #04060b 0%, #070a12 48%, #05070d 100%) !important;
    color: var(--text) !important;
    font-family: Inter, sans-serif !important;
}

[data-testid="stHeader"], #MainMenu, footer, [data-testid="stDecoration"] {
    display: none !important;
}

.block-container {
    max-width: 100% !important;
    padding: 0 !important;
}

.main .block-container {
    padding-top: 0 !important;
}

.msp-bg-grid {
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image:
        linear-gradient(rgba(255,255,255,.032) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.032) 1px, transparent 1px);
    background-size: 48px 48px;
    mask-image: radial-gradient(circle at center, black, transparent 80%);
    opacity: .42;
    z-index: 0;
}

.msp-shell {
    position: relative;
    z-index: 1;
    width: min(1180px, calc(100% - 44px));
    margin: 0 auto;
}

.msp-topbar {
    padding: 28px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
}

.msp-brand {
    display: inline-flex;
    align-items: center;
    gap: 12px;
}

.msp-brand-mark {
    width: 42px;
    height: 42px;
    display: grid;
    place-items: center;
    border-radius: 14px;
    background:
        linear-gradient(135deg, rgba(37,99,235,.95), rgba(96,165,250,.35)),
        radial-gradient(circle at 70% 20%, rgba(245,158,11,.9), transparent 34%);
    box-shadow: 0 12px 38px rgba(37,99,235,.35);
    border: 1px solid rgba(255,255,255,.16);
    font-weight: 900;
    letter-spacing: -1px;
}

.msp-brand-text {
    font-weight: 900;
    letter-spacing: -.8px;
    font-size: clamp(21px, 2vw, 28px);
    white-space: nowrap;
}

.msp-brand-text span { color: var(--gold); }

.msp-top-pill {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    border: 1px solid var(--line);
    background: rgba(255,255,255,.045);
    color: #b8c8e6;
    padding: 11px 15px;
    border-radius: 999px;
    font-size: 13px;
    backdrop-filter: blur(18px);
}

.msp-pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--green);
    animation: pulse 1.7s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(34,197,94,.38); }
    70% { box-shadow: 0 0 0 12px rgba(34,197,94,0); }
    100% { box-shadow: 0 0 0 0 rgba(34,197,94,0); }
}

.msp-hero-wrap {
    position: relative;
    z-index: 1;
    padding: 38px 0 36px;
    min-height: calc(100vh - 130px);
    display: flex;
    align-items: center;
}

.msp-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: var(--blue2);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 22px;
}

.msp-eyebrow::before {
    content: "";
    width: 34px;
    height: 2px;
    background: linear-gradient(90deg, var(--blue), var(--gold));
    border-radius: 999px;
}

.msp-h1 {
    margin: 0;
    font-size: clamp(48px, 6.7vw, 94px);
    line-height: .95;
    letter-spacing: -4px;
    max-width: 760px;
    font-weight: 900;
}

.msp-gradient-text {
    display: inline-block;
    background: linear-gradient(90deg, #ffffff 0%, #8db9ff 34%, #2563eb 56%, #f59e0b 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.msp-subhead {
    margin: 28px 0 0;
    max-width: 640px;
    font-size: clamp(17px, 1.65vw, 22px);
    line-height: 1.75;
    color: var(--muted);
}

.msp-launch-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 14px;
    color: #dbeafe;
    font-weight: 900;
    font-size: 15px;
}

.msp-early-badge {
    color: #071018;
    background: linear-gradient(90deg, var(--gold), #fde68a);
    padding: 7px 11px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 900;
    white-space: nowrap;
}

.msp-form-note {
    margin: 12px 0 0;
    color: #536781;
    font-size: 12px;
    line-height: 1.6;
}

.msp-proof {
    margin-top: 30px;
    display: flex;
    flex-wrap: wrap;
    gap: 13px;
}

.msp-proof span {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border: 1px solid rgba(255,255,255,.09);
    background: rgba(255,255,255,.035);
    border-radius: 999px;
    color: #a2b2ca;
    font-size: 13px;
}

.msp-ticker-tape {
    position: relative;
    z-index: 1;
    width: 100%;
    overflow: hidden;
    border-block: 1px solid rgba(255,255,255,.08);
    background: rgba(255,255,255,.025);
    margin-top: 40px;
    padding: 18px 0;
}

.msp-ticker-track {
    display: flex;
    gap: 16px;
    width: max-content;
    animation: marquee 28s linear infinite;
}

.msp-ticker-track:hover { animation-play-state: paused; }

@keyframes marquee {
    from { transform: translateX(0); }
    to { transform: translateX(-50%); }
}

.msp-ticker-chip {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    min-width: 170px;
    padding: 12px 14px;
    border: 1px solid rgba(255,255,255,.09);
    background: rgba(11,18,32,.8);
    border-radius: 16px;
    box-shadow: 0 12px 38px rgba(0,0,0,.25);
}

.msp-ticker-chip b {
    font-family: "JetBrains Mono", monospace;
    color: var(--text);
}

.msp-ticker-chip span {
    color: #4ade80;
    font-weight: 800;
    font-size: 13px;
}

.msp-section {
    position: relative;
    z-index: 1;
    width: min(1180px, calc(100% - 44px));
    margin: 90px auto;
}

.msp-section-head {
    max-width: 780px;
    margin-bottom: 28px;
}

.msp-section-kicker {
    color: var(--gold);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 12px;
}

.msp-section h3,
.msp-cta-final h3 {
    margin: 0;
    font-size: clamp(34px, 4vw, 56px);
    line-height: 1;
    letter-spacing: -2px;
    font-weight: 900;
}

.msp-section p,
.msp-cta-final p {
    color: var(--muted);
    font-size: 17px;
    line-height: 1.75;
}

.msp-cta-final {
    position: relative;
    z-index: 1;
    width: min(960px, calc(100% - 44px));
    margin: 100px auto 70px;
    text-align: center;
    padding: 48px;
    border-radius: 34px;
    background:
        radial-gradient(circle at 20% 10%, rgba(37,99,235,.22), transparent 34%),
        linear-gradient(180deg, rgba(13,21,37,.82), rgba(5,8,16,.72));
    border: 1px solid rgba(255,255,255,.12);
    box-shadow: 0 30px 100px rgba(0,0,0,.55);
}

.msp-footer {
    position: relative;
    z-index: 1;
    width: min(1180px, calc(100% - 44px));
    margin: 0 auto;
    padding: 34px 0 46px;
    border-top: 1px solid rgba(255,255,255,.08);
    color: #536781;
    font-size: 12px;
    display: flex;
    justify-content: space-between;
    gap: 20px;
    flex-wrap: wrap;
}

.msp-footer a {
    color: #7c8fae;
    text-decoration: none;
}

/* Streamlit form card styling */
[data-testid="stForm"] {
    border: 1px solid var(--line) !important;
    padding: 20px !important;
    background: linear-gradient(180deg, rgba(13,21,37,.78), rgba(8,12,22,.65)) !important;
    border-radius: 22px !important;
    box-shadow: 0 30px 100px rgba(0,0,0,.55) !important;
    backdrop-filter: blur(18px) !important;
    max-width: 640px !important;
    margin-top: 34px !important;
}

[data-testid="stTextInput"] label {
    display: none !important;
}

[data-testid="stTextInput"] input {
    height: 50px !important;
    border: 1px solid rgba(255,255,255,.14) !important;
    background: rgba(255,255,255,.055) !important;
    color: #edf4ff !important;
    border-radius: 14px !important;
    font-size: 14px !important;
}

[data-testid="stTextInput"] input:focus {
    border-color: rgba(96,165,250,.9) !important;
    box-shadow: 0 0 0 4px rgba(37,99,235,.16) !important;
}

[data-testid="stFormSubmitButton"] button,
.stButton button {
    height: 50px !important;
    border: 0 !important;
    border-radius: 14px !important;
    padding: 0 18px !important;
    font-weight: 900 !important;
    color: #fff !important;
    cursor: pointer !important;
    background: linear-gradient(135deg, #2563eb, #1d4ed8 55%, #f59e0b 160%) !important;
    box-shadow: 0 18px 40px rgba(37,99,235,.32) !important;
    transition: transform .18s ease, box-shadow .18s ease, filter .18s ease !important;
    white-space: nowrap !important;
    width: 100% !important;
}

[data-testid="stFormSubmitButton"] button:hover,
.stButton button:hover {
    transform: translateY(-2px) !important;
    filter: brightness(1.08) !important;
    box-shadow: 0 24px 56px rgba(37,99,235,.43) !important;
}

@media (max-width: 980px) {
    .msp-hero-wrap {
        min-height: auto;
        padding-bottom: 50px;
    }

    .msp-top-pill {
        display: none;
    }
}

@media (max-width: 620px) {
    .msp-shell,
    .msp-section,
    .msp-cta-final,
    .msp-footer {
        width: min(100% - 28px, 1180px);
    }

    .msp-h1 {
        letter-spacing: -2px;
    }

    [data-testid="stForm"],
    .msp-cta-final {
        padding: 18px !important;
    }

    .msp-launch-title {
        flex-direction: column;
        align-items: flex-start;
    }
}
</style>
<div class="msp-bg-grid"></div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# TOPBAR
# ============================================================
st.markdown(
    """
<div class="msp-shell">
  <header class="msp-topbar">
    <div class="msp-brand">
      <span class="msp-brand-mark">M</span>
      <span class="msp-brand-text">Market<span>Signal</span>Pro</span>
    </div>
    <div class="msp-top-pill"><span class="msp-pulse-dot"></span> Private early-access list now open</div>
  </header>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HERO
# ============================================================
st.markdown('<div class="msp-shell"><div class="msp-hero-wrap">', unsafe_allow_html=True)
left, right = st.columns([1.03, 0.97], gap="large", vertical_alignment="center")

with left:
    st.markdown(
        """
<div class="msp-eyebrow">AI Market Intelligence</div>
<h1 class="msp-h1">AI-powered stock signals <span class="msp-gradient-text">made simple.</span></h1>
<p class="msp-subhead">
MarketSignalPro is building a cleaner way to spot momentum, squeeze candidates,
sentiment shifts, and market opportunities before they get crowded.
</p>
""",
        unsafe_allow_html=True,
    )

    with st.form("early_access_form", clear_on_submit=True):
        st.markdown(
            """
<div class="msp-launch-title">
  <span>Join the early-access list</span>
  <span class="msp-early-badge">Founding users get priority</span>
</div>
""",
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns([1.0, 1.1, 0.85], gap="small")
        with c1:
            name = st.text_input("Name", placeholder="Your name", label_visibility="collapsed")
        with c2:
            email = st.text_input("Email", placeholder="Your email", label_visibility="collapsed")
        with c3:
            submitted = st.form_submit_button("Join Early →", use_container_width=True)

        st.markdown(
            """
<p class="msp-form-note">
Early members will be first to receive launch updates, beta access opportunities,
and introductory offers. No spam — just MarketSignalPro updates.
</p>
""",
            unsafe_allow_html=True,
        )

        if submitted:
            ok, result = save_signup(name, email)

            if ok:
                sent, info = send_signup_email(result)
                if sent:
                    st.success("You're on the early-access list. We will be in touch soon.")
                else:
                    st.success("You're on the early-access list.")
                    st.info(info)
            else:
                st.info(result)

    st.markdown(
        """
<div class="msp-proof">
  <span>✓ AI-focused market discovery</span>
  <span>✓ Built for everyday traders</span>
  <span>✓ Early access before public launch</span>
</div>
""",
        unsafe_allow_html=True,
    )

with right:
    preview_html = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800;900&family=JetBrains+Mono:wght@500;700;800&display=swap');
*{box-sizing:border-box}
body{margin:0;background:transparent;color:#edf4ff;font-family:Inter,sans-serif;overflow:hidden}
.visual{position:relative;min-height:640px;display:grid;place-items:center;perspective:1200px}
.orbit{position:absolute;width:520px;height:520px;border:1px solid rgba(96,165,250,.15);border-radius:999px;animation:spin 18s linear infinite;opacity:.85}
.orbit.two{width:660px;height:340px;transform:rotateX(67deg) rotateZ(18deg);border-color:rgba(245,158,11,.16);animation-duration:24s;animation-direction:reverse}
@keyframes spin{to{rotate:360deg}}
.dashboard{position:relative;width:min(100%,560px);border:1px solid rgba(255,255,255,.13);background:linear-gradient(180deg,rgba(13,21,37,.92),rgba(6,10,19,.88)),radial-gradient(circle at 80% 10%,rgba(37,99,235,.2),transparent 35%);border-radius:28px;box-shadow:0 40px 120px rgba(0,0,0,.65),0 0 80px rgba(37,99,235,.16);overflow:hidden;transform:rotateY(-8deg) rotateX(4deg)}
.dash-top{height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 18px;background:rgba(255,255,255,.035);border-bottom:1px solid rgba(255,255,255,.08)}
.traffic{display:flex;gap:7px}.traffic i{width:10px;height:10px;border-radius:999px;display:block}.traffic i:nth-child(1){background:#ef4444}.traffic i:nth-child(2){background:#f59e0b}.traffic i:nth-child(3){background:#22c55e}
.label{font-family:JetBrains Mono,monospace;color:#5f7491;font-size:11px;letter-spacing:.3px}.body{padding:22px}
.title{display:flex;align-items:end;justify-content:space-between;gap:16px;margin-bottom:18px}.title h2{margin:0;font-size:28px;line-height:1;letter-spacing:-1px;font-weight:900}.title h2 span{color:#60a5fa}
.score{width:76px;height:76px;display:grid;place-items:center;border-radius:24px;background:linear-gradient(135deg,rgba(34,197,94,.18),rgba(37,99,235,.16));border:1px solid rgba(34,197,94,.25);color:#86efac;font-size:26px;font-weight:900;font-family:JetBrains Mono,monospace}
.stock-row{display:grid;grid-template-columns:68px 1fr auto;gap:12px;align-items:center;padding:14px;border:1px solid rgba(255,255,255,.07);background:rgba(2,6,23,.58);border-radius:16px;margin:10px 0}
.ticker{font-family:JetBrains Mono,monospace;color:#60a5fa;font-weight:900;font-size:17px}.bar{height:9px;border-radius:999px;background:rgba(255,255,255,.07);overflow:hidden}.bar span{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#2563eb,#22c55e);animation:grow 1.8s ease both}
@keyframes grow{from{width:0}}.tag{padding:5px 9px;border-radius:999px;color:#071018;background:#86efac;font-size:10px;font-weight:900;white-space:nowrap}
.insight{margin-top:20px;padding:18px;border-radius:20px;background:linear-gradient(135deg,rgba(37,99,235,.12),rgba(245,158,11,.08));border:1px solid rgba(255,255,255,.1)}.insight strong{color:#fff;display:block;margin-bottom:8px}.insight p{margin:0;color:#91a3be;line-height:1.65;font-size:14px}
@media(max-width:980px){.dashboard{transform:none}.visual{min-height:520px}}
</style>
</head>
<body>
<div class="visual">
  <div class="orbit"></div>
  <div class="orbit two"></div>
  <div class="dashboard">
    <div class="dash-top">
      <div class="traffic"><i></i><i></i><i></i></div>
      <div class="label">MARKETSIGNALPRO / LIVE PREVIEW</div>
    </div>
    <div class="body">
      <div class="title">
        <h2>Signal Matrix<br><span>Opportunity Radar</span></h2>
        <div class="score">92</div>
      </div>
      <div class="stock-row"><div class="ticker">NVDA</div><div class="bar"><span style="width:92%"></span></div><div class="tag">Strong Buy</div></div>
      <div class="stock-row"><div class="ticker">TSLA</div><div class="bar"><span style="width:78%"></span></div><div class="tag">Momentum</div></div>
      <div class="stock-row"><div class="ticker">AMD</div><div class="bar"><span style="width:68%"></span></div><div class="tag">Watch</div></div>
      <div class="insight"><strong>Plain-English insight</strong><p>Momentum, trend, volume, and sentiment are aligning. MarketSignalPro translates the signal stack into simple, actionable context.</p></div>
    </div>
  </div>
</div>
</body>
</html>
"""
    components.html(preview_html, height=660, scrolling=False)

st.markdown("</div></div>", unsafe_allow_html=True)


# ============================================================
# TICKER TAPE
# ============================================================
ticker_items = [
    ("AI Signals", "+ Early"),
    ("Momentum", "+ Radar"),
    ("Sentiment", "+ Shift"),
    ("Squeeze", "+ Watch"),
    ("Volume", "+ Surge"),
    ("Market", "+ Scan"),
] * 2

ticker_html = '<div class="msp-ticker-tape"><div class="msp-ticker-track">'
for label, value in ticker_items:
    ticker_html += f'<div class="msp-ticker-chip"><b>{label}</b><span>{value}</span></div>'
ticker_html += "</div></div>"
st.markdown(ticker_html, unsafe_allow_html=True)


# ============================================================
# FEATURES + GALLERY
# ============================================================
gallery_html = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800;900&display=swap');
*{box-sizing:border-box}body{margin:0;background:transparent;color:#edf4ff;font-family:Inter,sans-serif;overflow:hidden}
.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:34px}
.feature{min-height:220px;padding:24px;border:1px solid rgba(255,255,255,.095);background:linear-gradient(180deg,rgba(13,21,37,.78),rgba(9,13,24,.62));border-radius:24px;box-shadow:0 22px 70px rgba(0,0,0,.28);position:relative;overflow:hidden}
.feature:after{content:"";position:absolute;inset:auto -30% -40% -30%;height:120px;background:radial-gradient(circle,rgba(37,99,235,.18),transparent 65%)}
.icon{width:46px;height:46px;border-radius:16px;display:grid;place-items:center;background:rgba(37,99,235,.14);border:1px solid rgba(96,165,250,.25);font-size:22px;margin-bottom:20px}
h4{margin:0 0 10px;font-size:19px;letter-spacing:-.4px;font-weight:900}p{margin:0;font-size:14px;color:#7386a4;line-height:1.75}
.gallery-shell{overflow:hidden;border-radius:28px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.025);box-shadow:0 30px 100px rgba(0,0,0,.55);padding:16px}
.gallery-track{display:flex;gap:16px;width:max-content;animation:gallery 35s linear infinite}@keyframes gallery{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.ai-card{width:320px;height:220px;flex:0 0 auto;border-radius:22px;border:1px solid rgba(255,255,255,.12);position:relative;overflow:hidden;background:radial-gradient(circle at 30% 25%,rgba(96,165,250,.55),transparent 25%),radial-gradient(circle at 72% 68%,rgba(245,158,11,.32),transparent 24%),linear-gradient(135deg,#07111f,#030712)}
.ai-card:nth-child(2n){background:radial-gradient(circle at 70% 22%,rgba(34,197,94,.32),transparent 24%),radial-gradient(circle at 20% 78%,rgba(37,99,235,.5),transparent 26%),linear-gradient(135deg,#070b15,#100a1d)}
.ai-card:nth-child(3n){background:radial-gradient(circle at 50% 30%,rgba(245,158,11,.36),transparent 24%),radial-gradient(circle at 78% 70%,rgba(96,165,250,.42),transparent 22%),linear-gradient(135deg,#06101d,#090914)}
.ai-card:before{content:"";position:absolute;inset:0;background:linear-gradient(115deg,transparent 20%,rgba(255,255,255,.12),transparent 45%),repeating-linear-gradient(90deg,rgba(255,255,255,.045) 0 1px,transparent 1px 18px);opacity:.55}
.ai-card:after{content:attr(data-label);position:absolute;left:18px;bottom:18px;color:#eaf2ff;font-weight:900;letter-spacing:-.4px;text-shadow:0 2px 18px rgba(0,0,0,.75)}
@media(max-width:980px){.feature-grid{grid-template-columns:1fr}.ai-card{width:260px;height:180px}}
</style>
</head>
<body>
<div class="feature-grid">
  <article class="feature"><div class="icon">🤖</div><h4>AI-focused analysis</h4><p>Signals are organized into plain-English context so users do not have to decode every metric manually.</p></article>
  <article class="feature"><div class="icon">📡</div><h4>Momentum and sentiment</h4><p>Track attention, volume, and market movement in one place instead of jumping between tools.</p></article>
  <article class="feature"><div class="icon">⚡</div><h4>Built for speed</h4><p>Designed around quick discovery, cleaner watchlists, and faster decisions when markets are moving.</p></article>
</div>
<div class="gallery-shell">
  <div class="gallery-track">
    <div class="ai-card" data-label="AI Signal Engine"></div><div class="ai-card" data-label="Opportunity Radar"></div><div class="ai-card" data-label="Market Sentiment"></div><div class="ai-card" data-label="Momentum Scanner"></div><div class="ai-card" data-label="Smart Watchlists"></div><div class="ai-card" data-label="Signal Scoring"></div>
    <div class="ai-card" data-label="AI Signal Engine"></div><div class="ai-card" data-label="Opportunity Radar"></div><div class="ai-card" data-label="Market Sentiment"></div><div class="ai-card" data-label="Momentum Scanner"></div><div class="ai-card" data-label="Smart Watchlists"></div><div class="ai-card" data-label="Signal Scoring"></div>
  </div>
</div>
</body>
</html>
"""

st.markdown(
    """
<section class="msp-section">
  <div class="msp-section-head">
    <div class="msp-section-kicker">Built for the next era of trading tools</div>
    <h3>High-signal market discovery without the noise.</h3>
    <p>
      MarketSignalPro is designed to combine data signals into a cleaner view of what is moving,
      why it matters, and where attention is building.
    </p>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="msp-section" style="margin-top:-68px;">', unsafe_allow_html=True)
components.html(gallery_html, height=520, scrolling=False)
st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# CTA + FOOTER
# ============================================================
st.markdown(
    """
<section class="msp-cta-final">
  <h3>Get on the list before launch.</h3>
  <p>
    Early interest matters. Join now to be first in line for beta access, launch updates,
    and founding-user opportunities when MarketSignalPro opens.
  </p>
</section>

<footer class="msp-footer">
  <div>© 2026 MarketSignalPro. All rights reserved.</div>
  <div><a href="mailto:support@marketsignalpro.com">support@marketsignalpro.com</a></div>
</footer>
""",
    unsafe_allow_html=True,
)


# ============================================================
# OPTIONAL ADMIN VIEW: add ?admin=1
# ============================================================
try:
    if st.query_params.get("admin") == "1":
        st.markdown("---")
        st.subheader("Early-access signups")
        signups = load_signups()
        st.dataframe(signups, use_container_width=True)
        st.download_button(
            "Download signups CSV",
            signups.to_csv(index=False),
            file_name="marketsignalpro_signups.csv",
            mime="text/csv",
        )
except Exception:
    pass
