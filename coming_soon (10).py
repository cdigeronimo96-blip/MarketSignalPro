
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
    columns = ["timestamp", "first_name", "last_name", "name", "email", "source"]
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


def save_signup(first_name: str, last_name: str, email: str, source: str = "coming_soon"):
    df = load_signups()
    clean_first = " ".join(first_name.strip().split())
    clean_last = " ".join(last_name.strip().split())
    clean_name = f"{clean_first} {clean_last}".strip()
    clean_email = email.strip().lower()

    if not clean_first:
        return False, "Please enter your first name."

    if not clean_last:
        return False, "Please enter your last name."

    if not is_valid_email(clean_email):
        return False, "Please enter a valid email address."

    if not df.empty and clean_email in df["email"].astype(str).str.lower().values:
        return False, "You are already on the early-access list."

    row = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "first_name": clean_first,
        "last_name": clean_last,
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


def send_user_confirmation_email(row: dict):
    """Send a branded welcome email to the person who just signed up."""
    if not RESEND_API_KEY:
        return False, "RESEND_API_KEY not configured."

    first = (row.get("first_name") or row.get("name") or "there").strip().split(" ")[0] or "there"

    html = f"""
    <div style="background:#07090f;padding:40px 20px;font-family:Inter,Arial,sans-serif;">
      <div style="max-width:560px;margin:0 auto;background:linear-gradient(180deg,#0d1424,#080b14);border:1px solid rgba(96,165,250,.18);border-radius:18px;overflow:hidden;">

        <div style="padding:32px 36px 14px;border-bottom:1px solid rgba(255,255,255,.06);">
          <div style="font-size:22px;font-weight:900;letter-spacing:-.5px;color:#ffffff;">
            Market<span style="background:linear-gradient(90deg,#60a5fa,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">Signal</span>Pro
          </div>
          <div style="margin-top:6px;font-size:11px;font-weight:700;letter-spacing:2px;color:#60a5fa;text-transform:uppercase;">
            Welcome to the early-access list
          </div>
        </div>

        <div style="padding:30px 36px 12px;">
          <h2 style="margin:0 0 14px;font-size:24px;font-weight:900;color:#ffffff;letter-spacing:-.6px;">
            You're in, {first}.
          </h2>
          <p style="margin:0 0 18px;font-size:15px;line-height:1.7;color:#cbd5e1;">
            Thanks for joining the MarketSignalPro early-access list. You're officially one of our founding users —
            which means you'll get first look at the platform, beta access opportunities, and an introductory offer
            before the public launch.
          </p>

          <div style="background:rgba(37,99,235,.08);border:1px solid rgba(96,165,250,.22);border-radius:12px;padding:18px 20px;margin:22px 0;">
            <div style="font-size:12px;font-weight:800;color:#fcd34d;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;">
              ⭐ Founding user perks
            </div>
            <ul style="margin:0;padding:0 0 0 18px;color:#cbd5e1;font-size:14px;line-height:1.8;">
              <li>Priority access when beta opens</li>
              <li>Founding-user pricing — locked in before public release</li>
              <li>Direct line to send feedback that actually shapes the product</li>
            </ul>
          </div>

          <p style="margin:18px 0 6px;font-size:14px;line-height:1.7;color:#7c8fae;">
            What's coming: composite signal categories (squeeze setups, hidden movers, sentiment flips, volume breakouts),
            score breakdowns with full BI analytics, and plain-English AI insights — built for traders who want clarity, not noise.
          </p>

          <p style="margin:22px 0 0;font-size:14px;line-height:1.7;color:#7c8fae;">
            We'll be in touch soon with launch updates. In the meantime, if you have questions or want to share what you'd like to see,
            just reply to this email or write to
            <a href="mailto:support@marketsignalpro.com" style="color:#60a5fa;text-decoration:none;">support@marketsignalpro.com</a>.
          </p>
        </div>

        <div style="padding:20px 36px 28px;border-top:1px solid rgba(255,255,255,.05);margin-top:14px;">
          <div style="font-size:12px;color:#475569;line-height:1.6;">
            — The MarketSignalPro Team<br>
            <a href="https://marketsignalpro.com" style="color:#60a5fa;text-decoration:none;">marketsignalpro.com</a>
          </div>
        </div>

      </div>

      <div style="max-width:560px;margin:14px auto 0;text-align:center;font-size:11px;color:#475569;line-height:1.5;">
        You're receiving this because you signed up for early access at marketsignalpro.com.<br>
        MarketSignalPro · AI-powered market intelligence
      </div>
    </div>
    """

    text = (
        f"You're in, {first}.\n\n"
        "Thanks for joining the MarketSignalPro early-access list. You're officially one of our founding users.\n\n"
        "FOUNDING USER PERKS:\n"
        "  • Priority access when beta opens\n"
        "  • Founding-user pricing — locked in before public release\n"
        "  • Direct line to send feedback that shapes the product\n\n"
        "We'll be in touch with launch updates. Questions? Reply to this email or write to "
        "support@marketsignalpro.com.\n\n"
        "— The MarketSignalPro Team\n"
        "marketsignalpro.com\n"
    )

    payload = {
        "from": FROM_EMAIL,
        "to": [row["email"]],
        "reply_to": ADMIN_EMAIL,
        "subject": "You're on the MarketSignalPro early-access list 🎉",
        "html": html,
        "text": text,
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
    width: min(1120px, calc(100% - 36px));
    margin: 0 auto;
}

.msp-topbar {
    padding: 22px 0 12px;
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
    padding: 8px 0 20px;
    min-height: auto;
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

.msp-eyebrow-row {
    display: flex;
    justify-content: center;
    width: 100%;
    margin-bottom: 6px;
    margin-top: 8px;
}
.msp-eyebrow-row .msp-eyebrow {
    margin: 0 !important;
    max-width: none !important;
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
    font-size: clamp(44px, 5.6vw, 78px);
    line-height: .95;
    letter-spacing: -4px;
    max-width: 590px;
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
    margin: 22px 0 0;
    max-width: 560px;
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
    margin-top: 22px;
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
    margin-top: 12px;
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
    width: min(1180px, calc(100% - 36px));
    margin: 80px auto;
}

.msp-section-feature {
    margin-top: 70px;
    margin-bottom: 70px;
}

.msp-section-head {
    max-width: 720px;
    margin: 0 auto 44px;
    text-align: center;
}

.msp-section-kicker {
    color: var(--gold);
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 3.5px;
    text-transform: uppercase;
    margin-bottom: 14px;
    opacity: .9;
}

.msp-section h3 {
    margin: 0;
    font-size: clamp(32px, 4vw, 52px);
    line-height: 1.05;
    letter-spacing: -2px;
    font-weight: 900;
}

.msp-section p {
    color: var(--muted);
    font-size: 16px;
    line-height: 1.7;
    margin: 18px auto 0;
    max-width: 620px;
}

.msp-feature-row {
    margin-top: 4px;
    margin-bottom: 28px;
}

.msp-gallery-wrap {
    margin-top: 12px;
    opacity: .92;
}

.msp-footer {
    position: relative;
    z-index: 1;
    width: min(1180px, calc(100% - 36px));
    margin: 70px auto 0;
    padding: 38px 0 44px;
    border-top: 1px solid rgba(255,255,255,.06);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 18px;
    text-align: center;
}

.msp-footer-brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: #cbd5e1;
    font-weight: 900;
    font-size: 15px;
    letter-spacing: -.3px;
}

.msp-footer-mark {
    width: 28px;
    height: 28px;
    display: grid;
    place-items: center;
    border-radius: 9px;
    background: linear-gradient(135deg, var(--blue), #1e40af);
    color: #fff;
    font-size: 13px;
    font-weight: 900;
    box-shadow: 0 4px 14px rgba(37,99,235,.35);
}

.msp-disclaimer {
    max-width: 720px;
    margin: 0 auto;
    color: #5f7491;
    font-size: 11.5px;
    line-height: 1.7;
    letter-spacing: .1px;
}

.msp-footer-meta {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: #475569;
    font-size: 11.5px;
    flex-wrap: wrap;
    justify-content: center;
}

.msp-footer-dot {
    color: #334155;
}

.msp-footer a {
    color: #7c8fae;
    text-decoration: none;
    transition: color .2s ease;
}

.msp-footer a:hover {
    color: var(--blue2);
}

/* Feature cards rendered natively (so they stack on mobile via Streamlit columns) */
.msp-feature {
    min-height: 220px;
    padding: 26px 24px;
    border: 1px solid rgba(255,255,255,.095);
    background: linear-gradient(180deg, rgba(13,21,37,.78), rgba(9,13,24,.62));
    border-radius: 24px;
    box-shadow: 0 22px 70px rgba(0,0,0,.28);
    position: relative;
    overflow: hidden;
    height: 100%;
}
.msp-feature::after {
    content: "";
    position: absolute;
    inset: auto -30% -40% -30%;
    height: 120px;
    background: radial-gradient(circle, rgba(37,99,235,.18), transparent 65%);
    pointer-events: none;
}
.msp-feature-icon {
    width: 46px;
    height: 46px;
    border-radius: 16px;
    display: grid;
    place-items: center;
    background: rgba(37,99,235,.14);
    border: 1px solid rgba(96,165,250,.25);
    font-size: 22px;
    margin-bottom: 20px;
}
.msp-feature h4 {
    margin: 0 0 10px;
    font-size: 19px;
    letter-spacing: -.4px;
    font-weight: 900;
    color: #edf4ff;
}
.msp-feature p {
    margin: 0;
    font-size: 14px;
    color: #7386a4;
    line-height: 1.75;
}

/* Streamlit form card styling */
[data-testid="stForm"] {
    border: 1px solid var(--line) !important;
    padding: 18px !important;
    background: linear-gradient(180deg, rgba(13,21,37,.78), rgba(8,12,22,.65)) !important;
    border-radius: 22px !important;
    box-shadow: 0 30px 100px rgba(0,0,0,.55) !important;
    backdrop-filter: blur(18px) !important;
    max-width: 520px !important;
    margin-top: 22px !important;
}

[data-testid="stTextInput"] label {
    display: none !important;
}

/* Hide Streamlit's "Press Enter to submit form" hint under inputs */
[data-testid="InputInstructions"],
[data-testid="stWidgetInstructions"],
[data-testid="stFormSubmitButton"] ~ [data-testid="InputInstructions"],
.stTextInput div[data-baseweb="form-control-caption"],
div[data-testid="stForm"] small {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}

[data-testid="stTextInput"] {
    margin-bottom: 10px !important;
    width: 100% !important;
}

[data-testid="stTextInput"] > div,
[data-testid="stTextInput"] > div > div {
    width: 100% !important;
}

[data-testid="stTextInput"] input {
    height: 48px !important;
    min-height: 48px !important;
    width: 100% !important;
    max-width: 100% !important;
    border: 1px solid rgba(255,255,255,.18) !important;
    background: rgba(255,255,255,.075) !important;
    color: #edf4ff !important;
    border-radius: 13px !important;
    font-size: 14px !important;
    line-height: 48px !important;
    padding: 0 14px !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.08) !important;
}

[data-testid="stTextInput"] input:focus {
    border-color: rgba(96,165,250,.9) !important;
    box-shadow: 0 0 0 4px rgba(37,99,235,.16) !important;
}

[data-testid="stFormSubmitButton"] {
    margin-top: 8px !important;
}

[data-testid="stFormSubmitButton"] button,
.stButton button {
    height: 48px !important;
    min-height: 48px !important;
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

@media (max-width: 820px) {
    .msp-shell,
    .msp-section,
    .msp-footer {
        width: calc(100% - 44px) !important;
    }
}

@media (max-width: 620px) {
    .msp-shell,
    .msp-section,
    .msp-footer {
        width: calc(100% - 36px) !important;
    }

    .msp-h1 {
        letter-spacing: -2px;
    }

    [data-testid="stForm"] {
        padding: 22px !important;
    }

    .msp-launch-title {
        flex-direction: column;
        align-items: flex-start;
    }

    .msp-section {
        margin: 60px auto !important;
    }

    .msp-section-head {
        margin-bottom: 32px;
    }

    .msp-feature {
        min-height: auto;
        padding: 22px 20px;
    }

    .msp-ticker-chip {
        min-width: 150px;
        padding: 10px 12px;
    }
}

/* ============================================================
   HERO LAYOUT — center the form & preview without relying on :has()
   or Streamlit's internal column DOM structure. Each hero element
   is targeted by its OWN class (.msp-eyebrow, .msp-h1, .msp-subhead,
   etc.) so the rule cannot be invalidated by Streamlit version
   changes. Forces max-width on the wrapping horizontal block too.
   ============================================================ */

/* The first horizontal block on the page IS the hero (after topbar) */
section.main div.stHorizontalBlock,
section.main [data-testid="stHorizontalBlock"] {
    align-items: center;
}

/* Constrain the hero block specifically (it contains .msp-eyebrow) */
section.main [data-testid="stHorizontalBlock"]:has(.msp-eyebrow),
section.main div.stHorizontalBlock:has(.msp-eyebrow) {
    max-width: 1080px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    gap: 2.5rem !important;
}

/* PRIMARY FIX: target hero elements directly by their class.
   These rules work no matter what DOM Streamlit wraps them in. */
.msp-eyebrow,
.msp-h1,
.msp-subhead,
.msp-proof {
    max-width: 520px !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}

/* Right-align the form to the column gutter */
[data-testid="stForm"]:has(.msp-launch-title) {
    max-width: 520px !important;
    margin-left: auto !important;
    margin-right: 0 !important;
    width: 100% !important;
    box-sizing: border-box !important;
}

/* Fallback for browsers without :has() — target the first form */
section.main > div > div > div > [data-testid="stForm"]:first-of-type {
    max-width: 520px !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}

/* Reset the First/Last name columns inside the form */
[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
    max-width: none !important;
    margin: 0 !important;
}
[data-testid="stForm"] [data-testid="stHorizontalBlock"] [data-testid="column"] {
    padding: 0 !important;
}
[data-testid="stForm"] [data-testid="stVerticalBlock"] {
    max-width: none !important;
    margin: 0 !important;
}

/* Left-align the preview iframe to the gutter on its side */
section.main iframe[title="streamlit_app"],
section.main iframe[srcdoc*="dashboard"] {
    margin-left: 0 !important;
}

@media (max-width: 980px) {
    section.main [data-testid="stHorizontalBlock"]:has(.msp-eyebrow),
    section.main div.stHorizontalBlock:has(.msp-eyebrow) {
        max-width: 100% !important;
        gap: 1rem !important;
    }
    .msp-eyebrow,
    .msp-h1,
    .msp-subhead,
    .msp-proof,
    [data-testid="stForm"]:has(.msp-launch-title),
    section.main > div > div > div > [data-testid="stForm"]:first-of-type {
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
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

# Eyebrow lives above the columns and is centered across the full page width
st.markdown(
    '<div class="msp-eyebrow-row"><div class="msp-eyebrow">AI Market Intelligence</div></div>',
    unsafe_allow_html=True,
)

left, right = st.columns([0.5, 0.5], gap="large", vertical_alignment="center")

with left:
    st.markdown(
        """
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

        c1, c2 = st.columns(2, gap="small")
        with c1:
            first_name = st.text_input("First name", placeholder="First name", label_visibility="collapsed")
        with c2:
            last_name = st.text_input("Last name", placeholder="Last name", label_visibility="collapsed")

        email = st.text_input("Email", placeholder="Email address", label_visibility="collapsed")
        submitted = st.form_submit_button("Join the Early List →", use_container_width=True)

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
            ok, result = save_signup(first_name, last_name, email)

            if ok:
                # 1. Notify the admin (support@marketsignalpro.com)
                sent, info = send_signup_email(result)
                # 2. Send a welcome/confirmation email to the user
                user_sent, user_info = send_user_confirmation_email(result)

                if sent and user_sent:
                    st.success("You're on the early-access list. Check your inbox for a confirmation — we'll be in touch soon.")
                elif user_sent:
                    st.success("You're on the early-access list. Check your inbox for a confirmation.")
                elif sent:
                    st.success("You're on the early-access list. We will be in touch soon.")
                    st.caption(f"(Confirmation email could not be delivered: {user_info})")
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
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800;900&family=JetBrains+Mono:wght@500;700;800&display=swap');
*{box-sizing:border-box}
body{margin:0;background:transparent;color:#edf4ff;font-family:Inter,sans-serif;overflow:hidden}
.visual{position:relative;min-height:740px;display:grid;align-items:center;justify-items:start;perspective:1200px;padding:20px 0 30px 0}
.orbit{position:absolute;width:520px;height:520px;border:1px solid rgba(96,165,250,.15);border-radius:999px;animation:spin 18s linear infinite;opacity:.85}
.orbit.two{width:660px;height:340px;transform:rotateX(67deg) rotateZ(18deg);border-color:rgba(245,158,11,.16);animation-duration:24s;animation-direction:reverse}
@keyframes spin{to{rotate:360deg}}
.dashboard{position:relative;width:min(100%,500px);border:1px solid rgba(255,255,255,.13);background:linear-gradient(180deg,rgba(13,21,37,.92),rgba(6,10,19,.88)),radial-gradient(circle at 80% 10%,rgba(37,99,235,.2),transparent 35%);border-radius:28px;box-shadow:0 40px 120px rgba(0,0,0,.65),0 0 80px rgba(37,99,235,.16);overflow:hidden;transform:rotateY(-5deg) rotateX(3deg)}
.dash-top{height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 18px;background:rgba(255,255,255,.035);border-bottom:1px solid rgba(255,255,255,.08)}
.traffic{display:flex;gap:7px}.traffic i{width:10px;height:10px;border-radius:999px;display:block}.traffic i:nth-child(1){background:#ef4444}.traffic i:nth-child(2){background:#f59e0b}.traffic i:nth-child(3){background:#22c55e}
.label{font-family:JetBrains Mono,monospace;color:#5f7491;font-size:11px;letter-spacing:.3px}.body{padding:20px}
.tabs{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px;color:#7890b4;font-size:11px;font-weight:800}.tabs span{padding:6px 9px;border-radius:999px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07)}.tabs .active{color:#fff;background:rgba(37,99,235,.22);border-color:rgba(96,165,250,.35)}
.title{display:flex;align-items:end;justify-content:space-between;gap:16px;margin-bottom:18px}.title h2{margin:0;font-size:28px;line-height:1;letter-spacing:-1px;font-weight:900}.title h2 span{color:#60a5fa}
.score{width:76px;height:76px;display:grid;place-items:center;border-radius:24px;background:linear-gradient(135deg,rgba(34,197,94,.18),rgba(37,99,235,.16));border:1px solid rgba(34,197,94,.25);color:#86efac;font-size:26px;font-weight:900;font-family:JetBrains Mono,monospace}
.stock-row{display:grid;grid-template-columns:68px 1fr auto;gap:12px;align-items:center;padding:14px;border:1px solid rgba(255,255,255,.07);background:rgba(2,6,23,.58);border-radius:16px;margin:10px 0}
.ticker{font-family:JetBrains Mono,monospace;color:#60a5fa;font-weight:900;font-size:17px}.bar{height:9px;border-radius:999px;background:rgba(255,255,255,.07);overflow:hidden}.bar span{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#2563eb,#22c55e);animation:grow 1.8s ease both}
@keyframes grow{from{width:0}}.tag{padding:5px 9px;border-radius:999px;color:#071018;background:#86efac;font-size:10px;font-weight:900;white-space:nowrap}
.mini-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}.mini-grid div{padding:12px;border-radius:14px;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.08)}.mini-grid b{display:block;color:#f59e0b;font-size:18px}.mini-grid span{display:block;color:#7c8fae;font-size:10px;margin-top:2px}
.insight{margin-top:12px;padding:14px;border-radius:20px;background:linear-gradient(135deg,rgba(37,99,235,.12),rgba(245,158,11,.08));border:1px solid rgba(255,255,255,.1)}.insight strong{color:#fff;display:block;margin-bottom:8px}.insight p{margin:0;color:#91a3be;line-height:1.45;font-size:12px}

/* Auto-cycling panel system */
.tabs span{cursor:default;transition:all .35s ease}
.panel-stack{position:relative;min-height:430px}
.panel{position:absolute;inset:0;opacity:0;visibility:hidden;transform:translateY(8px);transition:opacity .55s ease,transform .55s ease,visibility .55s ease}
.panel.active{opacity:1;visibility:visible;transform:translateY(0)}

/* Signal Categories panel */
.cat-row{padding:10px 12px;border:1px solid rgba(255,255,255,.07);background:rgba(2,6,23,.58);border-radius:14px;margin-bottom:8px;border-left:3px solid}
.cat-row.green{border-left-color:#22c55e}
.cat-row.orange{border-left-color:#f59e0b}
.cat-row.yellow{border-left-color:#fbbf24}
.cat-row.pink{border-left-color:#ec4899}
.cat-row.blue{border-left-color:#60a5fa}
.cat-head{display:flex;align-items:center;gap:8px;margin-bottom:4px}
.cat-icon{font-size:14px}
.cat-title{color:#edf4ff;font-weight:900;font-size:13px;flex:1;letter-spacing:-.2px}
.cat-badge{font-size:9px;font-weight:900;padding:3px 7px;border-radius:6px;letter-spacing:.4px}
.cat-badge.pro{background:rgba(245,158,11,.16);color:#fcd34d;border:1px solid rgba(245,158,11,.35)}
.cat-badge.free{background:rgba(34,197,94,.16);color:#86efac;border:1px solid rgba(34,197,94,.35)}
.cat-desc{font-size:10.5px;color:#7c8fae;line-height:1.4}

/* Smart Insights panel — tickers colored by status */
.si-row{display:grid;grid-template-columns:62px 1fr 70px;gap:10px;align-items:center;padding:11px 12px;border:1px solid rgba(255,255,255,.07);background:rgba(2,6,23,.58);border-radius:14px;margin-bottom:9px;border-left:3px solid}
.si-row.buy{border-left-color:#22c55e}.si-row.watch{border-left-color:#f59e0b}.si-row.avoid{border-left-color:#ef4444}
.si-tk{font-family:JetBrains Mono,monospace;font-weight:900;font-size:14px;letter-spacing:.2px}
.si-tk-buy{color:#86efac}
.si-tk-watch{color:#fcd34d}
.si-tk-avoid{color:#fca5a5}
.si-txt{font-size:11px;color:#91a3be;line-height:1.45}
.si-txt strong{color:#edf4ff;font-weight:800}
.si-txt em{font-style:italic}
.si-tag{padding:4px 0;border-radius:999px;font-size:10px;font-weight:900;text-align:center;letter-spacing:.3px}
.si-tag.buy{background:#86efac;color:#071018}
.si-tag.watch{background:#fcd34d;color:#1a0f00}
.si-tag.avoid{background:#fca5a5;color:#1a0707}
@media(max-width:980px){.dashboard{transform:none;width:min(100%,440px)}.visual{min-height:640px;padding:14px 0 24px 0}.orbit{width:380px;height:380px}.orbit.two{width:440px;height:240px}}
@media(max-width:520px){.dashboard{width:100%}.visual{min-height:600px}.orbit{width:320px;height:320px}.orbit.two{width:360px;height:200px}.body{padding:16px}.title h2{font-size:22px}.score{width:60px;height:60px;font-size:22px;border-radius:18px}.stock-row{grid-template-columns:56px 1fr auto;padding:11px;gap:9px}.mini-grid{gap:8px}.mini-grid div{padding:10px}.mini-grid b{font-size:16px}}
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
      <div class="tabs">
        <span class="tab active" data-tab="0">📊 Market Overview</span>
        <span class="tab" data-tab="1">⭐ Signal Categories</span>
        <span class="tab" data-tab="2">🧠 Smart Insights</span>
      </div>
      <div class="title">
        <h2>MarketSignalPro<br><span>Discovery Dashboard</span></h2>
        <div class="score">92</div>
      </div>

      <div class="panel-stack">

        <!-- Panel 0: Market Overview -->
        <div class="panel active" data-panel="0">
          <div class="stock-row"><div class="ticker">NVDA</div><div class="bar"><span style="width:92%"></span></div><div class="tag">Strong Buy</div></div>
          <div class="stock-row"><div class="ticker">TSLA</div><div class="bar"><span style="width:78%"></span></div><div class="tag">Squeeze Watch</div></div>
          <div class="stock-row"><div class="ticker">AMD</div><div class="bar"><span style="width:68%"></span></div><div class="tag">Momentum</div></div>
          <div class="mini-grid">
            <div><b>17</b><span>Signal categories</span></div>
            <div><b>5,000+</b><span>US stocks tracked</span></div>
            <div><b>AI</b><span>Plain-English insights</span></div>
          </div>
          <div class="insight"><strong>Example insight</strong><p>NVDA is showing strong trend, momentum, and sentiment confirmation. MarketSignalPro turns the signal stack into simple, readable context.</p></div>
        </div>

        <!-- Panel 1: Proprietary Signal Categories -->
        <div class="panel" data-panel="1">
          <div class="cat-row green">
            <div class="cat-head"><span class="cat-icon">💡</span><span class="cat-title">Hidden Movers</span><span class="cat-badge free">FREE</span></div>
            <div class="cat-desc">Strong technical scores with low social noise — find them before the crowd arrives.</div>
          </div>
          <div class="cat-row orange">
            <div class="cat-head"><span class="cat-icon">🔥</span><span class="cat-title">Squeeze + Buzz</span><span class="cat-badge pro">★ PRO</span></div>
            <div class="cat-desc">High short-float stocks trending on social — squeeze fuel meets momentum.</div>
          </div>
          <div class="cat-row yellow">
            <div class="cat-head"><span class="cat-icon">⚡</span><span class="cat-title">Volume Breakout</span><span class="cat-badge pro">★ PRO</span></div>
            <div class="cat-desc">Breaking above moving averages on unusually high volume — institutional confirmation.</div>
          </div>
          <div class="cat-row pink">
            <div class="cat-head"><span class="cat-icon">🎯</span><span class="cat-title">Triple Lock</span><span class="cat-badge pro">★ PRO</span></div>
            <div class="cat-desc">RSI + MACD + 50d trend + volume all simultaneously bullish — maximum conviction setup.</div>
          </div>
          <div class="insight"><strong>17 proprietary categories</strong><p>Each blends RSI, MACD, volume, short interest & social sentiment so you can scan a curated list instead of the whole market.</p></div>
        </div>

        <!-- Panel 2: Smart Insights — Plain Language -->
        <div class="panel" data-panel="2">
          <div class="si-row buy">
            <div class="si-tk si-tk-buy">TSLA</div>
            <div class="si-txt"><strong>The Moving Average</strong> is breaking out above an important price range, which can sometimes lead to further upside.</div>
            <div class="si-tag buy">● BUY</div>
          </div>
          <div class="si-row watch">
            <div class="si-tk si-tk-watch">PLUG</div>
            <div class="si-txt">There are a lot of <strong>traders</strong> betting against this stock, and <strong>momentum is building</strong>.</div>
            <div class="si-tag watch">● WATCH</div>
          </div>
          <div class="si-row avoid">
            <div class="si-tk si-tk-avoid">AAPL</div>
            <div class="si-txt">The stock <strong>may have risen too quickly</strong> and could be due for <em><strong>a pullback</strong></em>.</div>
            <div class="si-tag avoid">● AVOID</div>
          </div>
          <div class="mini-grid" style="margin-top:14px">
            <div><b>AI</b><span>Plain English</span></div>
            <div><b>17</b><span>Signal types</span></div>
            <div><b>Live</b><span>Updated daily</span></div>
          </div>
          <div class="insight"><strong>Plain-English clarity</strong><p>Every signal gets translated into one clear sentence so you understand what the chart, momentum, and sentiment are actually saying.</p></div>
        </div>

      </div>
    </div>
  </div>
</div>
<script>
(function(){
  var tabs = document.querySelectorAll('.tab');
  var panels = document.querySelectorAll('.panel');
  var i = 0;
  function activate(idx){
    tabs.forEach(function(t){ t.classList.toggle('active', t.dataset.tab == idx); });
    panels.forEach(function(p){
      var on = p.dataset.panel == idx;
      p.classList.toggle('active', on);
      if (on) {
        // Re-trigger bar grow animations when a panel becomes visible
        p.querySelectorAll('.bar span').forEach(function(b){
          var w = b.style.width;
          b.style.animation = 'none';
          b.offsetWidth; // force reflow
          b.style.animation = '';
          b.style.width = w;
        });
      }
    });
  }
  setInterval(function(){
    i = (i + 1) % panels.length;
    activate(i);
  }, 5000);
})();
</script>
</body>
</html>
"""
    components.html(preview_html, height=760, scrolling=False)

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
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800;900&display=swap');
*{box-sizing:border-box}body{margin:0;background:transparent;color:#edf4ff;font-family:Inter,sans-serif;overflow:hidden;padding:6px 0 14px}
.gallery-shell{overflow:hidden;border-radius:28px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.025);box-shadow:0 30px 100px rgba(0,0,0,.55);padding:16px}
.gallery-track{display:flex;gap:16px;width:max-content;animation:gallery 35s linear infinite}@keyframes gallery{from{transform:translateX(0)}to{transform:translateX(-50%)}}
/* Preview card frame — 320x220, dark fintech theme */
.ai-card{width:320px;height:220px;flex:0 0 auto;border-radius:22px;border:1px solid rgba(255,255,255,.12);position:relative;overflow:hidden;background:linear-gradient(180deg,#0b1322 0%,#070b14 100%);box-shadow:0 18px 50px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.04)}
.ai-card:before{content:"";position:absolute;inset:0;z-index:3;background:radial-gradient(ellipse at 50% 100%,rgba(0,0,0,.55),transparent 55%);pointer-events:none}
.ai-card:after{content:"";position:absolute;inset:0;z-index:2;background:linear-gradient(115deg,transparent 30%,rgba(255,255,255,.05) 50%,transparent 70%);pointer-events:none}
.mini-frame{position:absolute;inset:0;padding:11px 13px;filter:blur(1.6px) saturate(1.05);opacity:.92;z-index:1}
.mini-bar{display:flex;align-items:center;gap:7px;margin-bottom:9px}
.mini-bar .dots{display:flex;gap:3px}
.mini-bar .dots i{width:6px;height:6px;border-radius:50%;display:block}
.mini-bar .dots i:nth-child(1){background:#ef4444}.mini-bar .dots i:nth-child(2){background:#f59e0b}.mini-bar .dots i:nth-child(3){background:#22c55e}
.mini-bar .ttl{font-family:JetBrains Mono,monospace;font-size:8px;color:#5f7491;letter-spacing:.2px;flex:1;white-space:nowrap;overflow:hidden}
.mini-bar .badge{font-size:7px;font-weight:900;color:#fcd34d;background:rgba(245,158,11,.14);border:1px solid rgba(245,158,11,.3);padding:2px 5px;border-radius:6px;letter-spacing:.3px}
.mini-bar .big{font-size:18px;font-weight:900;color:#86efac;font-family:JetBrains Mono,monospace;line-height:1}
.mini-label{position:absolute;left:14px;bottom:12px;z-index:4;color:#eaf2ff;font-weight:900;font-size:12px;letter-spacing:-.2px;background:rgba(7,17,31,.86);padding:5px 10px;border-radius:8px;border:1px solid rgba(96,165,250,.22);backdrop-filter:blur(6px);text-shadow:0 1px 4px rgba(0,0,0,.8)}

/* Smart Insights mini — removed (now in live preview) */

/* Discovery mini — removed (now in live preview as Signal Categories) */

/* Matrix mini */
.matrix{display:grid;grid-template-columns:30px repeat(5,1fr);gap:2px}
.m-cell{font-size:7px;font-weight:900;text-align:center;padding:3px 1px;border-radius:2px;font-family:JetBrains Mono,monospace}
.m-head{font-size:6.5px;color:#7c8fae;text-align:center;padding:2px 0;font-weight:700}
.m-tk{font-size:7.5px;color:#60a5fa;font-weight:900;font-family:JetBrains Mono,monospace;display:flex;align-items:center;padding-left:2px}
.m-cell.hot{background:rgba(34,197,94,.55);color:#022c1a}
.m-cell.warm{background:rgba(34,197,94,.35);color:#dcfce7}
.m-cell.mid{background:rgba(34,197,94,.2);color:#86efac}
.m-cell.cool{background:rgba(34,197,94,.12);color:#86efac}
.m-cell.cold{background:rgba(11,18,32,.6);color:#475569;border:1px solid rgba(255,255,255,.04)}

/* Score Breakdown mini */
.sb-row{display:grid;grid-template-columns:60px 1fr 28px;gap:5px;align-items:center;margin-bottom:5px}
.sb-lab{font-size:6.5px;color:#7c8fae;line-height:1.2}
.sb-bar{height:5px;background:rgba(255,255,255,.06);border-radius:999px;overflow:hidden}
.sb-fill{height:100%;border-radius:999px}
.sb-fill.green{background:linear-gradient(90deg,#16a34a,#22c55e)}
.sb-fill.orange{background:linear-gradient(90deg,#d97706,#f59e0b)}
.sb-val{font-size:6.5px;font-weight:900;text-align:right;font-family:JetBrains Mono,monospace}
.sb-val.green{color:#86efac}.sb-val.orange{color:#fcd34d}

/* Signal Performance mini */
.perf-head{display:flex;align-items:center;gap:8px;margin-bottom:7px}
.perf-stat{font-family:JetBrains Mono,monospace;font-size:20px;font-weight:900;color:#86efac;line-height:1}
.perf-label{font-size:6.5px;color:#7c8fae;letter-spacing:.3px}
.perf-mini{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-bottom:6px}
.perf-mini div{padding:4px;border-radius:4px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);text-align:center}
.perf-mini b{display:block;font-size:9px;font-weight:900;font-family:JetBrains Mono,monospace}
.perf-mini b.green{color:#86efac}.perf-mini b.red{color:#fca5a5}.perf-mini b.blue{color:#93b4fd}
.perf-mini span{display:block;font-size:5.5px;color:#5f7491;margin-top:1px}
.perf-row{display:grid;grid-template-columns:1fr auto auto;gap:5px;align-items:center;padding:3px 4px;border-bottom:1px solid rgba(255,255,255,.04);font-size:7px}
.perf-row:last-child{border-bottom:0}
.perf-tk{color:#60a5fa;font-weight:900;font-family:JetBrains Mono,monospace}
.perf-pct{font-family:JetBrains Mono,monospace;font-weight:900}
.perf-pct.green{color:#86efac}.perf-pct.red{color:#fca5a5}
.perf-pill{padding:1px 4px;border-radius:3px;font-size:5.5px;font-weight:900}
.perf-pill.win{background:rgba(34,197,94,.2);color:#86efac}
.perf-pill.loss{background:rgba(239,68,68,.18);color:#fca5a5}

/* Smart Watchlist mini */
.wl-row{display:grid;grid-template-columns:34px 1fr auto auto;gap:5px;align-items:center;padding:4px 5px;border-radius:5px;background:rgba(255,255,255,.025);margin-bottom:3px;border-left:2px solid}
.wl-row.alert{border-left-color:#f59e0b}
.wl-row.buy{border-left-color:#22c55e}
.wl-row.hold{border-left-color:#60a5fa}
.wl-tk{font-family:JetBrains Mono,monospace;color:#60a5fa;font-weight:900;font-size:8px}
.wl-name{font-size:6px;color:#7c8fae;line-height:1.1}
.wl-score{font-family:JetBrains Mono,monospace;font-weight:900;font-size:8px}
.wl-score.green{color:#86efac}.wl-score.orange{color:#fcd34d}.wl-score.blue{color:#93b4fd}
.wl-alert{font-size:9px}

@media(max-width:680px){.ai-card{width:260px;height:200px}.gallery-shell{padding:12px;border-radius:22px}}
</style>
</head>
<body>
<div class="gallery-shell">
  <div class="gallery-track">
    <div class="ai-card"><div class="mini-frame"><div class="mini-bar"><div class="dots"><i></i><i></i><i></i></div><div class="ttl">Score Breakdown — NVDA</div><div class="big">88</div></div><div class="sb-row"><div class="sb-lab">Momentum (RSI)</div><div class="sb-bar"><div class="sb-fill green" style="width:80%"></div></div><div class="sb-val green">20/25</div></div><div class="sb-row"><div class="sb-lab">Trend (MA20/50)</div><div class="sb-bar"><div class="sb-fill green" style="width:90%"></div></div><div class="sb-val green">18/20</div></div><div class="sb-row"><div class="sb-lab">MACD Signal</div><div class="sb-bar"><div class="sb-fill green" style="width:86%"></div></div><div class="sb-val green">13/15</div></div><div class="sb-row"><div class="sb-lab">Volume Surge</div><div class="sb-bar"><div class="sb-fill orange" style="width:60%"></div></div><div class="sb-val orange">9/15</div></div><div class="sb-row"><div class="sb-lab">Sentiment</div><div class="sb-bar"><div class="sb-fill green" style="width:80%"></div></div><div class="sb-val green">12/15</div></div></div><div class="mini-label">Score Breakdown</div></div>
    <div class="ai-card"><div class="mini-frame"><div class="mini-bar"><div class="dots"><i></i><i></i><i></i></div><div class="ttl">Opportunity Matrix</div><div class="badge">EXCLUSIVE ✨</div></div><div class="matrix"><div></div><div class="m-head">Mom</div><div class="m-head">Trend</div><div class="m-head">Vol</div><div class="m-head">Sent</div><div class="m-head">Sq</div><div class="m-tk">NVDA</div><div class="m-cell hot">20</div><div class="m-cell hot">18</div><div class="m-cell mid">9</div><div class="m-cell warm">12</div><div class="m-cell cold">0</div><div class="m-tk">TSLA</div><div class="m-cell warm">14</div><div class="m-cell warm">16</div><div class="m-cell warm">13</div><div class="m-cell warm">10</div><div class="m-cell cool">6</div><div class="m-tk">GME</div><div class="m-cell hot">18</div><div class="m-cell cold">4</div><div class="m-cell warm">15</div><div class="m-cell warm">14</div><div class="m-cell warm">10</div></div></div><div class="mini-label">BI Opportunity Matrix</div></div>
    <div class="ai-card"><div class="mini-frame"><div class="mini-bar"><div class="dots"><i></i><i></i><i></i></div><div class="ttl">Signal Performance — 30d</div><div class="perf-stat">68%</div></div><div class="perf-label" style="margin-bottom:6px">Win rate · 47 trades tracked</div><div class="perf-mini"><div><b class="green">32</b><span>WINS</span></div><div><b class="red">15</b><span>LOSSES</span></div><div><b class="blue">+12.4%</b><span>AVG GAIN</span></div></div><div class="perf-row"><div class="perf-tk">NVDA</div><div class="perf-pct green">+18.2%</div><div class="perf-pill win">WIN</div></div><div class="perf-row"><div class="perf-tk">COIN</div><div class="perf-pct green">+9.7%</div><div class="perf-pill win">WIN</div></div><div class="perf-row"><div class="perf-tk">RIVN</div><div class="perf-pct red">-4.2%</div><div class="perf-pill loss">LOSS</div></div></div><div class="mini-label">Signal Performance</div></div>
    <div class="ai-card"><div class="mini-frame"><div class="mini-bar"><div class="dots"><i></i><i></i><i></i></div><div class="ttl">Smart Watchlist — Alerts</div></div><div class="wl-row alert"><div class="wl-tk">NVDA</div><div class="wl-name">Momentum confirmed</div><div class="wl-score green">92</div><div class="wl-alert">🔔</div></div><div class="wl-row buy"><div class="wl-tk">SOFI</div><div class="wl-name">Squeeze setup ready</div><div class="wl-score green">87</div><div class="wl-alert">⚡</div></div><div class="wl-row alert"><div class="wl-tk">PLTR</div><div class="wl-name">Trend break detected</div><div class="wl-score orange">74</div><div class="wl-alert">🔔</div></div><div class="wl-row buy"><div class="wl-tk">AMD</div><div class="wl-name">Volume surge active</div><div class="wl-score green">81</div><div class="wl-alert">⚡</div></div><div class="wl-row hold"><div class="wl-tk">META</div><div class="wl-name">Holding strong base</div><div class="wl-score blue">69</div><div class="wl-alert">👀</div></div></div><div class="mini-label">Smart Watchlist & Alerts</div></div>
    <div class="ai-card"><div class="mini-frame"><div class="mini-bar"><div class="dots"><i></i><i></i><i></i></div><div class="ttl">Score Breakdown — NVDA</div><div class="big">88</div></div><div class="sb-row"><div class="sb-lab">Momentum (RSI)</div><div class="sb-bar"><div class="sb-fill green" style="width:80%"></div></div><div class="sb-val green">20/25</div></div><div class="sb-row"><div class="sb-lab">Trend (MA20/50)</div><div class="sb-bar"><div class="sb-fill green" style="width:90%"></div></div><div class="sb-val green">18/20</div></div><div class="sb-row"><div class="sb-lab">MACD Signal</div><div class="sb-bar"><div class="sb-fill green" style="width:86%"></div></div><div class="sb-val green">13/15</div></div><div class="sb-row"><div class="sb-lab">Volume Surge</div><div class="sb-bar"><div class="sb-fill orange" style="width:60%"></div></div><div class="sb-val orange">9/15</div></div><div class="sb-row"><div class="sb-lab">Sentiment</div><div class="sb-bar"><div class="sb-fill green" style="width:80%"></div></div><div class="sb-val green">12/15</div></div></div><div class="mini-label">Score Breakdown</div></div>
    <div class="ai-card"><div class="mini-frame"><div class="mini-bar"><div class="dots"><i></i><i></i><i></i></div><div class="ttl">Opportunity Matrix</div><div class="badge">EXCLUSIVE ✨</div></div><div class="matrix"><div></div><div class="m-head">Mom</div><div class="m-head">Trend</div><div class="m-head">Vol</div><div class="m-head">Sent</div><div class="m-head">Sq</div><div class="m-tk">NVDA</div><div class="m-cell hot">20</div><div class="m-cell hot">18</div><div class="m-cell mid">9</div><div class="m-cell warm">12</div><div class="m-cell cold">0</div><div class="m-tk">TSLA</div><div class="m-cell warm">14</div><div class="m-cell warm">16</div><div class="m-cell warm">13</div><div class="m-cell warm">10</div><div class="m-cell cool">6</div><div class="m-tk">GME</div><div class="m-cell hot">18</div><div class="m-cell cold">4</div><div class="m-cell warm">15</div><div class="m-cell warm">14</div><div class="m-cell warm">10</div></div></div><div class="mini-label">BI Opportunity Matrix</div></div>
    <div class="ai-card"><div class="mini-frame"><div class="mini-bar"><div class="dots"><i></i><i></i><i></i></div><div class="ttl">Signal Performance — 30d</div><div class="perf-stat">68%</div></div><div class="perf-label" style="margin-bottom:6px">Win rate · 47 trades tracked</div><div class="perf-mini"><div><b class="green">32</b><span>WINS</span></div><div><b class="red">15</b><span>LOSSES</span></div><div><b class="blue">+12.4%</b><span>AVG GAIN</span></div></div><div class="perf-row"><div class="perf-tk">NVDA</div><div class="perf-pct green">+18.2%</div><div class="perf-pill win">WIN</div></div><div class="perf-row"><div class="perf-tk">COIN</div><div class="perf-pct green">+9.7%</div><div class="perf-pill win">WIN</div></div><div class="perf-row"><div class="perf-tk">RIVN</div><div class="perf-pct red">-4.2%</div><div class="perf-pill loss">LOSS</div></div></div><div class="mini-label">Signal Performance</div></div>
    <div class="ai-card"><div class="mini-frame"><div class="mini-bar"><div class="dots"><i></i><i></i><i></i></div><div class="ttl">Smart Watchlist — Alerts</div></div><div class="wl-row alert"><div class="wl-tk">NVDA</div><div class="wl-name">Momentum confirmed</div><div class="wl-score green">92</div><div class="wl-alert">🔔</div></div><div class="wl-row buy"><div class="wl-tk">SOFI</div><div class="wl-name">Squeeze setup ready</div><div class="wl-score green">87</div><div class="wl-alert">⚡</div></div><div class="wl-row alert"><div class="wl-tk">PLTR</div><div class="wl-name">Trend break detected</div><div class="wl-score orange">74</div><div class="wl-alert">🔔</div></div><div class="wl-row buy"><div class="wl-tk">AMD</div><div class="wl-name">Volume surge active</div><div class="wl-score green">81</div><div class="wl-alert">⚡</div></div><div class="wl-row hold"><div class="wl-tk">META</div><div class="wl-name">Holding strong base</div><div class="wl-score blue">69</div><div class="wl-alert">👀</div></div></div><div class="mini-label">Smart Watchlist & Alerts</div></div>
  </div>
</div>
</body>
</html>
"""

st.markdown(
    """
<section class="msp-section msp-section-feature">
  <div class="msp-section-head">
    <div class="msp-section-kicker">Preview of what is coming</div>
    <h3>Built around <span class="msp-gradient-text">real signals.</span></h3>
    <p>
      Composite signal categories, score breakdowns, watchlists, screeners, BI analytics,
      and plain-English AI insights — designed for traders who want clarity, not noise.
    </p>
  </div>

  <div class="msp-feature-row">
""",
    unsafe_allow_html=True,
)

# Feature cards rendered natively so Streamlit handles mobile stacking gracefully
fcol1, fcol2, fcol3 = st.columns(3, gap="medium")
with fcol1:
    st.markdown(
        """<article class="msp-feature">
        <div class="msp-feature-icon">🎯</div>
        <h4>Composite Signal Categories</h4>
        <p>Discover squeeze setups, hidden movers, sentiment flips, volume breakouts, and other proprietary categories.</p>
        </article>""",
        unsafe_allow_html=True,
    )
with fcol2:
    st.markdown(
        """<article class="msp-feature">
        <div class="msp-feature-icon">📊</div>
        <h4>Score Breakdowns & BI Analytics</h4>
        <p>See the trend, momentum, volume, sentiment, and signal logic behind each opportunity in one clean view.</p>
        </article>""",
        unsafe_allow_html=True,
    )
with fcol3:
    st.markdown(
        """<article class="msp-feature">
        <div class="msp-feature-icon">🧠</div>
        <h4>Plain-English AI Insights</h4>
        <p>Turn technical market data into readable explanations, watchlist ideas, and faster discovery.</p>
        </article>""",
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True)  # close .msp-feature-row

st.markdown('<div class="msp-gallery-wrap">', unsafe_allow_html=True)
components.html(gallery_html, height=290, scrolling=False)
st.markdown('</div></section>', unsafe_allow_html=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown(
    """
<footer class="msp-footer">
  <div class="msp-footer-brand">
    <span class="msp-footer-mark">M</span>
    <span>Market<span style="color:var(--gold);">Signal</span>Pro</span>
  </div>
  <p class="msp-disclaimer">
    MarketSignalPro is for informational and educational purposes only and is not financial, investment, tax, or legal advice.
    Nothing on this site constitutes a recommendation to buy, sell, or hold any security. Markets involve risk, including possible loss of principal.
    Always do your own research and consult a licensed financial professional before making investment decisions.
  </p>
  <div class="msp-footer-meta">
    <span>© 2026 MarketSignalPro. All rights reserved.</span>
    <span class="msp-footer-dot">·</span>
    <a href="mailto:support@marketsignalpro.com">support@marketsignalpro.com</a>
  </div>
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
