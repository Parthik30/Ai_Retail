import sys
import os

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.append(PROJECT_ROOT)

import streamlit as st
import pandas as pd
import numpy as np

from backend.services.dashboard_service import (
    get_dashboard_data, 
    get_demand_pattern_classification
)
import streamlit as st # Ensure streamlit is available for decorators

# ── Caching expensive service calls ──
@st.cache_data(ttl=300, show_spinner=False) # Cache for 5 minutes, hide technical name
def cached_get_dashboard_data(product):
    return get_dashboard_data(product)

@st.cache_data(ttl=600, show_spinner=False) # Cache for 10 minutes, hide technical name
def cached_get_demand_pattern_classification():
    return get_demand_pattern_classification()
import backend.services.inventory_service as inv_service
import backend.services.discount_service as disc_service
import backend.services.ai_service as ai_service
import matplotlib.pyplot as plt
import traceback
import sys
import datetime
import subprocess
import plotly.graph_objects as go
import plotly.express as px


# ------------------------------------------------------------------
# PAGE CONFIG  ← MUST be the very first Streamlit call in the script
# ------------------------------------------------------------------
st.set_page_config(
    page_title="IntelliStock",
    layout="wide",
    page_icon="📦"
)

# utility helpers

# OTP utilities

def generate_otp(length=6):
    import random, string
    return ''.join(random.choices(string.digits, k=length))


def send_otp_via_email(email, code):
    """Send OTP to the given email address.

    Uses SMTP settings from environment variables if available (``SMTP_SERVER``,
    ``SMTP_PORT``, ``SMTP_USER``, ``SMTP_PASS``).  When those are not set the
    function falls back to a console log so the app remains usable in
    development.
    """
    import smtplib
    from email.message import EmailMessage
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if smtp_server and smtp_user and smtp_pass:
        msg = EmailMessage()
        msg.set_content(f"Your IntelliStock password reset code is: {code}")
        msg["Subject"] = "IntelliStock OTP Code"
        msg["From"] = smtp_user
        msg["To"] = email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                smtp.starttls()
                smtp.login(smtp_user, smtp_pass)
                smtp.send_message(msg)
        except Exception as e:
            print(f"[OTP email] failed to send via SMTP: {e}")
            print(f"[OTP email] OTP {code} to {email}")
    else:
        print(f"[OTP email] Sending OTP {code} to {email} (SMTP not configured)")


def send_otp_via_sms(mobile, code):
    print(f"[OTP sms] Sending OTP {code} to {mobile}")

def safe_int(val, default=0):
    """Convert value to int, returning default for None/NaN/invalid."""
    if val is None:
        return default
    try:
        if pd.isna(val):
            return default
    except Exception:
        pass
    try:
        return int(val)
    except Exception:
        return default


# ----------------------------------
# STREAMLIT AUTHENTICATION LAYER
# ----------------------------------
from backend.db import SessionLocal, init_db
from backend.models import User, Registration, OTP
from sqlalchemy.exc import ProgrammingError, OperationalError

@st.cache_resource
def initialize_database():
    init_db()
    return True

# Ensure tables and initial seeding are done on first run
initialize_database()


def authenticate(username: str, password: str):
    """Return (True, user) if credentials match; otherwise (False, None).

    If the users table is missing a column (e.g. `registration_id`), a
    ProgrammingError will be raised by SQLAlchemy.  In that case we attempt
    to update the schema via ``init_db()`` and return False so that the
    calling Streamlit logic can rerun after the alteration.
    """
    session = SessionLocal()
    username_clean = username.strip() if username else ""
    password_clean = password.strip() if password else ""
    try:
        try:
            user = (
                session.query(User)
                .filter((User.username == username_clean) | (User.email == username_clean))
                .first()
            )
        except (ProgrammingError, OperationalError):
            session.rollback()
            init_db()
            return False, None
    finally:
        session.close()
    if user and user.password_hash.strip() == password_clean:
        return True, user
    return False, None


# initialize login state on first run
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

# ─────────────────────────────────────────────────────────────────
# MODERN LOGIN / REGISTER / FORGOT-PASSWORD UI
# ─────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown(
        """
        <style>
        /* ── Page ── */
        .stApp {
            background: #f0f2f8 !important;
            font-family: 'Times New Roman', Times, serif !important;
        }
        .block-container {
            padding: 3rem 1rem !important;
            max-width: 1020px !important;
        }

        /* ── Left column (form panel) — style the Streamlit column itself ── */
        div[data-testid="stHorizontalBlock"] > div:first-child > div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff !important;
            border-radius: 20px 0 0 20px !important;
            padding: 48px 44px !important;
            min-height: 540px !important;
            box-shadow: 0 20px 60px rgba(100,60,200,0.13), 0 4px 16px rgba(0,0,0,0.07) !important;
        }
        div[data-testid="stHorizontalBlock"] > div:first-child h1 {
            font-size: 30px; font-weight: 800;
            color: #1a1a2e; margin: 0 0 4px 0;
            letter-spacing: -0.5px;
            font-family: 'Times New Roman', Times, serif !important;
        }
        div[data-testid="stHorizontalBlock"] > div:first-child .subtitle {
            font-size: 13px; color: #8892b0; margin-bottom: 26px;
            font-family: 'Times New Roman', Times, serif !important;
        }

        /* ── Neumorphic pill inputs ── */
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"] > div {
            background: #f0f2f8 !important;
            border: none !important;
            border-radius: 50px !important;
            box-shadow: inset 3px 3px 8px rgba(170,170,200,0.35),
                        inset -3px -3px 8px #ffffff !important;
        }
        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input {
            background: transparent !important;
            border: none !important;
            border-radius: 50px !important;
            padding: 14px 20px 14px 44px !important;
            font-size: 14px !important;
            color: #1a1a2e !important;
            box-shadow: none !important;
            outline: none !important;
            font-family: 'Times New Roman', Times, serif !important;
        }
        div[data-baseweb="input"] input::placeholder {
            color: #a0aec0 !important;
            font-family: 'Times New Roman', Times, serif !important;
        }
        .stTextInput > label { display: none !important; }

        /* ── Radio tabs (Login / Register / Forgot) ── */
        .stRadio > label { display: none !important; }
        .stRadio > div {
            background: #f0f2f8 !important;
            border-radius: 50px !important;
            padding: 4px 6px !important;
            border: none !important;
            box-shadow: inset 2px 2px 6px rgba(170,170,200,0.3),
                        inset -2px -2px 6px #ffffff !important;
            margin-bottom: 24px !important;
        }
        .stRadio > div > label {
            border-radius: 50px !important;
            padding: 7px 18px !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            color: #8892b0 !important;
            transition: all 0.2s !important;
            cursor: pointer !important;
            font-family: 'Times New Roman', Times, serif !important;
        }
        .stRadio > div > label:has(input:checked) {
            background: linear-gradient(135deg, #7c3aed, #5b21b6) !important;
            color: white !important;
            box-shadow: 0 4px 14px rgba(124,58,237,0.4) !important;
        }

        /* ── Primary button (SIGN IN, etc.) ── */
        div.stButton > button {
            background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 50px !important;
            height: 50px !important;
            width: 100% !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            letter-spacing: 1.8px !important;
            text-transform: uppercase !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 8px 24px rgba(124,58,237,0.4) !important;
            margin-top: 10px !important;
            font-family: 'Times New Roman', Times, serif !important;
        }
        div.stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 14px 32px rgba(124,58,237,0.55) !important;
        }
        div.stButton > button:active { transform: translateY(0) !important; }

        /* ── Alerts ── */
        div[data-testid="stAlert"] { border-radius: 14px !important; font-size: 13px !important; font-family: 'Times New Roman', Times, serif !important;}

        /* ── Step pill ── */
        .step-pill {
            display: inline-block;
            background: rgba(124,58,237,0.1);
            border: 1px solid rgba(124,58,237,0.3);
            color: #7c3aed; border-radius: 999px;
            padding: 3px 14px; font-size: 12px; font-weight: 600;
            margin-bottom: 12px;
            font-family: 'Times New Roman', Times, serif !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialize fp_step
    if "fp_step" not in st.session_state:
        st.session_state.fp_step = 1

    # Handle mode-switch request from buttons (must happen BEFORE the radio widget)
    if st.session_state.get("_switch_mode"):
        _target = st.session_state.pop("_switch_mode")
        st.session_state.auth_mode = _target
        st.rerun()

    auth_options = ["Login", "Register", "Forgot Password"]
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "Login"
        
    current_mode = st.session_state.auth_mode

    # ── Two-column split: form left | purple deco right ──
    form_col, deco_col = st.columns([1, 1], gap="small")

    with form_col:

        # Mode radio tabs
        mode = st.radio(
            "Auth mode", auth_options,
            index=auth_options.index(current_mode) if current_mode in auth_options else 0,
            horizontal=True, label_visibility="collapsed",
        )
        if mode != current_mode:
            st.session_state.auth_mode = mode
            st.rerun()

        # ─── LOGIN ─────────────────────────────────────────
        if mode == "Login":
            st.markdown(
                "<h1>Hello! 👋</h1>"
                "<p class='subtitle'>Sign in to your account</p>",
                unsafe_allow_html=True,
            )
            st.markdown("<p style='color:#8892b0;font-size:12px;margin:0 0 2px 4px'>✉️ &nbsp;E-mail / Username</p>", unsafe_allow_html=True)
            uname = st.text_input("Email", placeholder="E-mail or username", key="login_uname", label_visibility="collapsed")
            uname_err = st.empty()
            st.markdown("<p style='color:#8892b0;font-size:12px;margin:8px 0 2px 4px'>🔒 &nbsp;Password</p>", unsafe_allow_html=True)
            pwd = st.text_input("Password", type="password", placeholder="Password", key="login_pwd", label_visibility="collapsed")
            pwd_err = st.empty()

            if st.button("SIGN IN", key="login_btn"):
                if not uname:
                    uname_err.markdown("<p style='color:#ef4444;font-size:13px;margin:4px 0 0 20px;'>User not registered</p>", unsafe_allow_html=True)
                elif not pwd:
                    pwd_err.markdown("<p style='color:#ef4444;font-size:13px;margin:4px 0 0 20px;'>Password is required</p>", unsafe_allow_html=True)
                else:
                    from backend.db import SessionLocal, init_db
                    from backend.models import User
                    from sqlalchemy.exc import ProgrammingError
                    session = SessionLocal()
                    try:
                        uname_clean = uname.strip()
                        pwd_clean = pwd.strip()
                        user = session.query(User).filter((User.username == uname_clean) | (User.email == uname_clean)).first()
                        if not user:
                            uname_err.markdown("<p style='color:#ef4444;font-size:13px;margin:4px 0 0 20px;'>User not registered</p>", unsafe_allow_html=True)
                            from backend.db import DATABASE_URL
                            dt = "PostgreSQL 🐘" if "postgres" in DATABASE_URL else "Local SQLite 📁"
                            st.error(f"❌ Invalid credentials. Please try again. (Currently connected to {dt})")
                        elif user.password_hash.strip() != pwd_clean:
                            pwd_err.markdown("<p style='color:#ef4444;font-size:13px;margin:4px 0 0 20px;'>Password is incorrect</p>", unsafe_allow_html=True)
                            from backend.db import DATABASE_URL
                            dt = "PostgreSQL 🐘" if "postgres" in DATABASE_URL else "Local SQLite 📁"
                            st.error(f"❌ Invalid credentials. Please try again. (Currently connected to {dt})")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.username = user.username
                            st.session_state.role = user.role or "User"
                            st.rerun()
                    except (ProgrammingError, OperationalError):
                        session.rollback()
                        init_db()
                        uname_err.markdown("<p style='color:#ef4444;font-size:13px;margin:4px 0 0 20px;'>Database uninitialized. Please try again.</p>", unsafe_allow_html=True)
                    finally:
                        session.close()

            st.markdown("<p style='text-align:center;color:#8892b0;font-size:13px;margin-top:20px'>Don't have an account?</p>", unsafe_allow_html=True)
            if st.button("Create one →", key="switch_to_register"):
                st.session_state._switch_mode = "Register"
                st.rerun()

        # ─── REGISTER ───────────────────────────────────────
        elif mode == "Register":
            st.markdown(
                "<h1>Create Account ✨</h1>"
                "<p class='subtitle'>Join IntelliStock today</p>",
                unsafe_allow_html=True,
            )
            r_uname    = st.text_input("Username",          placeholder="👤  Choose a username",        key="reg_uname",    label_visibility="collapsed")
            r_email    = st.text_input("Email",             placeholder="✉️  you@example.com",           key="reg_email",    label_visibility="collapsed")
            r_password = st.text_input("Password",          type="password", placeholder="🔒  Min 6 characters", key="reg_password", label_visibility="collapsed")
            r_mobile   = st.text_input("Mobile (optional)", placeholder="📱  +91 98765 43210",          key="reg_mobile",   label_visibility="collapsed")

            if st.button("CREATE ACCOUNT", key="reg_btn"):
                if not r_uname or not r_email or not r_password:
                    st.error("Username, email and password are required.")
                elif len(r_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    from backend.db import SessionLocal as _SL
                    _session = _SL()
                    try:
                        existing = _session.query(Registration).filter(
                            (Registration.email == r_email) | (Registration.username == r_uname)
                        ).first()
                        if existing:
                            st.error("An account with that username or email already exists.")
                        else:
                            reg = Registration(username=r_uname, email=r_email, password=r_password, mobileno=r_mobile)
                            _session.add(reg)
                            _session.commit()
                            _session.refresh(reg)
                            new_user = User(
                                user_id=f"R{reg.id:04d}",
                                username=r_uname, email=r_email, password_hash=r_password,
                                role="User", is_active=True,
                                created_at=datetime.datetime.utcnow(),
                                registration_id=str(reg.id),
                            )
                            _session.add(new_user)
                            _session.commit()
                            st.success("✅ Account created! You can now Sign In.")
                            st.session_state._switch_mode = "Login"
                            st.rerun()
                    except Exception as e:
                        _session.rollback()
                        st.error(f"Registration failed: {e}")
                    finally:
                        _session.close()

        # ─── FORGOT PASSWORD ────────────────────────────────
        else:
            st.markdown(
                "<h1>Reset Password 🔑</h1>",
                unsafe_allow_html=True,
            )
            step_labels = {
                1: "Step 1 of 3 — Identify Account",
                2: "Step 2 of 3 — Verify OTP",
                3: "Step 3 of 3 — Set New Password",
            }
            st.markdown(f"<div class='step-pill'>{step_labels.get(st.session_state.fp_step, '')}</div>", unsafe_allow_html=True)

            if st.session_state.fp_step == 1:
                fp_email = st.text_input("Email", placeholder="✉️  Your account email or username", key="fp_email", label_visibility="collapsed")
                if st.button("SEND OTP", key="fp_send"):
                    if not fp_email:
                        st.error("Please enter your username or email.")
                    else:
                        _s = SessionLocal()
                        user = _s.query(User).filter(
                            (User.username == fp_email) | (User.email == fp_email)
                        ).first()
                        if not user:
                            st.error("No account found with that username or email.")
                        else:
                            code = generate_otp()
                            expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
                            otp_rec = OTP(user_id=user.user_id, code=code, expires_at=expires, channel="email")
                            _s.add(otp_rec)
                            _s.commit()
                            send_otp_via_email(user.email, code)
                            st.success("📧 OTP sent to your email. Valid for 10 minutes.")
                            st.session_state.fp_step = 2
                            st.rerun()
                        _s.close()

            elif st.session_state.fp_step == 2:
                otp_in = st.text_input("OTP", placeholder="🔢  6-digit code from email", key="fp_otp", label_visibility="collapsed")
                if st.button("VERIFY OTP", key="fp_verify"):
                    if not otp_in:
                        st.error("Please enter the OTP.")
                    else:
                        _s = SessionLocal()
                        otp_row = _s.query(OTP).filter(OTP.code == otp_in, OTP.used == False).first()
                        if not otp_row or otp_row.expires_at < datetime.datetime.utcnow():
                            st.error("❌ Invalid or expired OTP. Please request a new one.")
                        else:
                            st.session_state.fp_user_id = otp_row.user_id
                            st.session_state.fp_step = 3
                            st.rerun()
                        _s.close()

            elif st.session_state.fp_step == 3:
                new_pwd = st.text_input("New Password",     type="password", placeholder="🔒  At least 6 characters",  key="fp_new",    label_visibility="collapsed")
                confirm = st.text_input("Confirm Password", type="password", placeholder="🔒  Repeat new password",    key="fp_confirm", label_visibility="collapsed")
                if st.button("RESET PASSWORD", key="fp_reset"):
                    if not new_pwd or not confirm:
                        st.error("Please fill both password fields.")
                    elif new_pwd != confirm:
                        st.error("Passwords do not match.")
                    elif len(new_pwd) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        _s = SessionLocal()
                        u = _s.query(User).filter(User.user_id == st.session_state.get("fp_user_id")).first()
                        if u:
                            u.password_hash = new_pwd
                            _s.add(u)
                            reg2 = _s.query(Registration).filter(Registration.email == u.email).first()
                            if reg2:
                                reg2.password = new_pwd
                                _s.add(reg2)
                            _s.query(OTP).filter(OTP.user_id == u.user_id, OTP.used == False).update({"used": True})
                            _s.commit()
                            st.success("✅ Password reset! Please sign in.")
                            st.session_state.fp_step = 1
                            st.session_state.auth_mode = "Login"
                            st.rerun()
                        else:
                            st.error("Account not found. Please start over.")
                        _s.close()

        st.markdown("</div>", unsafe_allow_html=True)

    with deco_col:
        # Purple gradient right panel with organic wave decorations matching reference
        st.markdown(
            """
            <div style='background:linear-gradient(155deg,#6B2DE2 0%,#8B5CF6 50%,#60A5FA 100%);
                        border-radius:0 20px 20px 0;min-height:540px;display:flex;
                        flex-direction:column;align-items:center;justify-content:center;
                        padding:48px 40px;text-align:center;position:relative;overflow:hidden;'>

              <!-- Cloud wave top-left (white organic shape) -->
              <svg style='position:absolute;top:0;left:0;width:65%;pointer-events:none'
                   viewBox='0 0 300 300' xmlns='http://www.w3.org/2000/svg'>
                <path d='M0,0 L300,0 L300,80
                         Q240,120 170,90 Q120,65 70,100 Q30,125 0,110 Z'
                      fill='white' opacity='0.18'/>
                <path d='M0,0 L180,0 Q130,50 50,70 Q20,78 0,70 Z'
                      fill='white' opacity='0.25'/>
              </svg>

              <!-- Cloud wave bottom-right -->
              <svg style='position:absolute;bottom:0;right:0;width:65%;pointer-events:none'
                   viewBox='0 0 300 300' xmlns='http://www.w3.org/2000/svg'>
                <path d='M300,300 L0,300 L0,220
                         Q60,180 130,210 Q180,235 230,200 Q270,175 300,190 Z'
                      fill='white' opacity='0.18'/>
                <path d='M300,300 L120,300 Q170,250 250,230 Q280,222 300,230 Z'
                      fill='white' opacity='0.25'/>
              </svg>

              <!-- Content -->
              <div style='position:relative;z-index:2; display:flex; justify-content:center; width:100%;'>
                <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&amp;display=swap" rel="stylesheet">
                <style>
                  .logo1 {
                    background:#03001a;
                    border:1px solid #1a00ff33;
                    border-radius:16px;
                    padding:30px;
                    display:flex;
                    align-items:center;
                    gap:20px;
                    font-family:'Orbitron',monospace;
                    text-align:left;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                  }
                  .logo1 .icon { width:58px; height:58px; flex-shrink:0; }
                  .logo1 .main { font-weight:900; font-size:16px; letter-spacing:3px; color:#4488ff; text-transform:uppercase; line-height:1.3; margin:0; }
                  .logo1 .main span { color:#00ddff; }
                  .logo1 .sub { font-size:9px; letter-spacing:5px; color:#334466; margin-top:6px; margin-bottom:0; }
                </style>
                <div class="logo1">
                  <div class="icon">
                    <svg viewBox="0 0 58 58">
                      <circle cx="29" cy="29" r="27" stroke="#4488ff" stroke-width="1.5" stroke-dasharray="4 2" fill="none"/>
                      <circle cx="29" cy="29" r="18" stroke="#00ddff" stroke-width="1" fill="none"/>
                      <circle cx="29" cy="29" r="5" fill="#00ddff"/>
                      <line x1="29" y1="2" x2="29" y2="12" stroke="#4488ff" stroke-width="2"/>
                      <line x1="29" y1="46" x2="29" y2="56" stroke="#4488ff" stroke-width="2"/>
                      <line x1="2" y1="29" x2="12" y2="29" stroke="#4488ff" stroke-width="2"/>
                      <line x1="46" y1="29" x2="56" y2="29" stroke="#4488ff" stroke-width="2"/>
                    </svg>
                  </div>
                  <div>
                    <div class="main">Predictive<br><span>Retail</span> Intelligence<br>Using AI</div>
                    <div class="sub">NEXT-GEN COMMERCE ANALYTICS</div>
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()



# Set up a global exception hook to capture uncaught exceptions to a log file
LOG_DIR = os.path.join(BACKEND_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "streamlit_error.log")

def _streamlit_excepthook(exc_type, exc_value, exc_tb):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("----\n")
            f.write(datetime.datetime.now().isoformat() + "\n")
            f.writelines(traceback.format_exception(exc_type, exc_value, exc_tb))
    except Exception:
        pass
    # call original excepthook
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _streamlit_excepthook

# PAGE CONFIG was moved to the very top of the file (before any st.* calls).

# ──────────────────────────────────────────────────────────────────
# GLOBAL DASHBOARD THEME  – Purple / White design system
# ──────────────────────────────────────────────────────────────────
def render_professional_table(df, title="", columns_style=None):
    """Render a professional styled HTML table matching reference design"""
    if df.empty:
        return ""
    
    # Default styling for columns
    if columns_style is None:
        columns_style = {}
    
    # Start HTML
    html = f'<div style="margin: 20px 0;">'
    if title:
        html += f'<h4 style="margin-bottom: 16px; color: #1a1a2e; font-weight: 700;">{title}</h4>'
    
    html += '<table style="width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px var(--kpi-shadow);">'
    
    # Header
    html += '<thead><tr style="background: var(--input-bg); border-bottom: 2px solid var(--border-color);">'
    for col in df.columns:
        align = columns_style.get(col, {}).get('align', 'left')
        html += f'<th style="padding: 14px 16px; text-align: {align}; font-weight: 700; color: #475569; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; font-family: \'Times New Roman\', Times, serif;">{col}</th>'
    html += '</tr></thead>'
    
    # Body
    html += '<tbody>'
    for idx, row in df.iterrows():
        html += '<tr style="border-bottom: 1px solid #f1f5f9; transition: background-color 0.2s;">'
        for col in df.columns:
            align = columns_style.get(col, {}).get('align', 'left')
            value = row[col]
            # Format value with styling
            cell_style = columns_style.get(col, {})
            bg_color = cell_style.get('bg_color', 'transparent')
            text_color = cell_style.get('color', 'var(--text-main)')
            
            html += f'<td style="padding: 12px 16px; text-align: {align}; color: {text_color}; background-color: {bg_color}; font-family: \'Times New Roman\', Times, serif; font-size: 14px; border-bottom: 1px solid var(--border-color);">{value}</td>'
        html += '</tr>'
    html += '</tbody>'
    html += '</table>'
    html += '</div>'
    
    return html


def render_styled_table_html(df, title="", header_style="gradient", row_alternating=False):
    """
    Render a professional styled HTML table with advanced options.
    
    Parameters:
    - df: DataFrame to display
    - title: Table title
    - header_style: "gradient", "solid", or "minimal"
    - row_alternating: Whether to alternate row colors
    """
    if df.empty:
        return ""
    
    # Determine header style
    if header_style == "gradient":
        header_bg = "linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)"
    elif header_style == "solid":
        header_bg = "#f1f5f9"
    else:
        header_bg = "#ffffff"
    
    html = f'<div style="margin: 24px 0; padding: 20px; background: var(--card-bg); border-radius: 14px; box-shadow: 0 4px 16px var(--kpi-shadow); border: 1px solid var(--border-color); overflow-x: auto;">'
    
    if title:
        html += f'<h4 style="margin: 0 0 16px 0; color: #1a1a2e; font-weight: 700; font-size: 16px;">{title}</h4>'
    
    html += '<table style="width: 100%; border-collapse: collapse; font-family: \'Times New Roman\', Times, serif;">'
    
    # Header
    html += f'<tr style="background: var(--input-bg); border-bottom: 2px solid var(--border-color);">'
    for col in df.columns:
        html += f'<th style="padding: 14px 16px; text-align: left; font-weight: 700; color: var(--text-muted); font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">{col}</th>'
    html += '</tr>'
    
    # Body
    for idx, row in df.iterrows():
        row_bg = "#f8fafc" if row_alternating and idx % 2 == 0 else "#ffffff"
        html += f'<tr style="border-bottom: 1px solid #f1f5f9; background-color: {row_bg}; transition: background-color 0.2s;">'
        for col in df.columns:
            value = row[col]
            # Determine alignment based on content
            if isinstance(value, (int, float)):
                align = "right"
            else:
                align = "left"
            html += f'<td style="padding: 12px 16px; text-align: {align}; color: var(--text-main); font-size: 14px;">{value}</td>'
        html += '</tr>'
    html += '</tbody>'
    html += '</table>'
    html += '</div>'
    
    return html

# ── Theme Variable Logic ──
is_dark = st.session_state.get("theme", "dark") == "dark"
theme_vars = {
    "bg_color": "#0f172a" if is_dark else "#f4f6fa",
    "card_bg": "#1e293b" if is_dark else "#ffffff",
    "text_main": "#f8fafc" if is_dark else "#1a1a2e",
    "text_muted": "#94a3b8" if is_dark else "#64748b",
    "border_color": "#334155" if is_dark else "#f1f5f9",
    "s_bg1": "#020617" if is_dark else "#5b21b6",
    "s_bg2": "#1e1b4b" if is_dark else "#7c3aed",
    "kpi_shadow": "rgba(0,0,0,0.3)" if is_dark else "rgba(0,0,0,0.08)",
    "input_bg": "#0f172a" if is_dark else "#f8fafc"
}

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Theme Variables (Dynamic) ── */
    :root {{
        --bg-color: {theme_vars['bg_color']};
        --card-bg: {theme_vars['card_bg']};
        --text-main: {theme_vars['text_main']};
        --text-muted: {theme_vars['text_muted']};
        --border-color: {theme_vars['border_color']};
        --sidebar-bg-1: {theme_vars['s_bg1']};
        --sidebar-bg-2: {theme_vars['s_bg2']};
        --kpi-shadow: {theme_vars['kpi_shadow']};
        --input-bg: {theme_vars['input_bg']};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    /* ── Page background ── */
    .stApp {
        background: var(--bg-color) !important;
        font-family: 'Times New Roman', Times, serif !important;
        color: var(--text-main) !important;
        transition: background-color 0.3s ease;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--sidebar-bg-1) 0%, var(--sidebar-bg-2) 100%) !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.15) !important;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-family: 'Times New Roman', Times, serif !important;
    }
    section[data-testid="stSidebar"] span[class*="material"],
    section[data-testid="stSidebar"] [class*="icon"],
    section[data-testid="stSidebar"] svg * {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    }
    section[data-testid="stSidebar"] .stRadio > div > label {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        margin-bottom: 6px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid rgba(255,255,255,0.0) !important;
    }
    section[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        transform: translateX(4px) !important;
    }
    section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
        background: rgba(255,255,255,0.2) !important;
        font-weight: 700 !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.15) !important;
    }
    section[data-testid="stSidebar"] .stExpander {
        background: rgba(0,0,0,0.1) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.15) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.25) !important;
        transform: translateY(-1px) !important;
    }
    
    .user-badge-container {
        background: rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        padding: 12px 14px !important;
        margin-bottom: 4px !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }
    .user-badge-container * {
        color: #ffffff !important;
    }
    .user-badge-name {
        font-size: 13px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        color: #ffffff !important;
    }
    .user-badge-role {
        margin-top: 6px !important;
        display: inline-block !important;
        font-size: 10px !important;
        font-weight: 700 !important;
        padding: 4px 12px !important;
        border-radius: 999px !important;
        letter-spacing: 0.5px !important;
        color: #ffffff !important;
    }

    /* ── Cards ── */
    .dashboard-card, .stock-info, .category-card {
        background: var(--card-bg) !important;
        border-radius: 20px !important;
        padding: 32px !important;
        box-shadow: 0 10px 40px var(--kpi-shadow), 0 2px 8px rgba(0,0,0,0.02) !important;
        border: 1px solid var(--border-color) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.3s ease !important;
    }
    .dashboard-card:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 16px 48px var(--kpi-shadow) !important;
    }

    /* ── KPI row ── */
    .kpi {
        border-radius: 18px !important;
        box-shadow: 0 10px 24px var(--kpi-shadow) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        backdrop-filter: blur(10px) !important;
    }
    .kpi .label { font-family: 'Times New Roman', Times, serif !important; letter-spacing: 0.5px !important; }
    .kpi .value { font-family: 'Times New Roman', Times, serif !important; letter-spacing: -0.5px !important; }

    /* ── Headings ── */
    h1, h2, h3, h4, p, span, div {
        color: var(--text-main) !important;
    }
    h1, h2, h3, h4 {
        font-family: 'Times New Roman', Times, serif !important;
        letter-spacing: -0.5px !important;
        font-weight: 800 !important;
    }

    /* ── Buttons (purple primary) ── */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-family: 'Times New Roman', Times, serif !important;
        padding: 10px 28px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 6px 20px rgba(124,58,237,0.3) !important;
        letter-spacing: 0.5px !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 28px rgba(124,58,237,0.45) !important;
    }

    /* ── Inputs & Selects ── */
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] > div,
    div[data-baseweb="select"] > div {
        border-radius: 12px !important;
        border: 1px solid var(--border-color) !important;
        background: var(--input-bg) !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease !important;
    }
    div[data-baseweb="input"] > div:hover,
    div[data-baseweb="base-input"] > div:hover,
    div[data-baseweb="select"] > div:hover {
        border-color: #cbd5e1 !important;
        background: var(--card-bg) !important;
    }
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input {
        font-family: 'Times New Roman', Times, serif !important;
        color: var(--text-main) !important;
        font-size: 14px !important;
    }

    /* ── Tables & DataFrames ── */
    .stDataFrame, .stTable {
        border-radius: 14px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 16px var(--kpi-shadow) !important;
        border: 1px solid var(--border-color) !important;
        background: var(--card-bg) !important;
    }
    .stDataFrame table th, .stTable table th {
        background: var(--input-bg) !important;
        color: var(--text-muted) !important;
        font-weight: 700 !important;
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding: 12px 16px !important;
    }
    .stDataFrame table td, .stTable table td {
        padding: 12px 16px !important;
        font-size: 14px !important;
        color: var(--text-main) !important;
        border-bottom: 1px solid var(--border-color) !important;
        font-family: 'Times New Roman', Times, serif !important;
    }
    
    /* ── Professional HTML Tables ── */
    table {
        border-collapse: collapse;
        width: 100%;
    }
    table tr:hover {
        background-color: #f8fafc !important;
        transition: background-color 0.2s ease !important;
    }
    table th {
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        font-family: 'Times New Roman', Times, serif !important;
    }
    table td, table th {
        font-family: 'Times New Roman', Times, serif !important;
    }

    /* ── Metrics ── */
    div[data-testid="stMetricValue"] {
        font-weight: 800 !important;
        color: var(--text-main) !important;
        font-size: 1.8rem !important;
        letter-spacing: -0.5px !important;
    }
    div[data-testid="stMetricLabel"] {
        font-family: 'Times New Roman', Times, serif !important;
        color: #64748b !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* ── Expanders ── */
    .stExpander {
        background: var(--card-bg) !important;
        border-radius: 14px !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02) !important;
    }
    .stExpander summary {
        font-weight: 600 !important;
        color: var(--text-main) !important;
        font-family: 'Times New Roman', Times, serif !important;
    }

    /* ── Dropdown Menus (Selectbox) ── */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"], ul[role="listbox"],
    div[data-baseweb="popover"] > div, div[data-baseweb="popover"] > div > div {
        background-color: var(--card-bg) !important;
        border-color: var(--border-color) !important;
    }
    div[data-baseweb="popover"] ul li, ul[data-baseweb="menu"] li, ul[role="listbox"] li {
        color: var(--text-main) !important;
        font-family: 'Times New Roman', Times, serif !important;
        background-color: transparent !important;
    }
    div[data-baseweb="popover"] ul li *, ul[data-baseweb="menu"] li *, ul[role="listbox"] li * {
        color: var(--text-main) !important;
        background-color: transparent !important;
    }
    div[data-baseweb="popover"] ul li:hover, ul[data-baseweb="menu"] li:hover, ul[role="listbox"] li:hover,
    div[data-baseweb="popover"] ul li[aria-selected="true"], ul[data-baseweb="menu"] li[aria-selected="true"], ul[role="listbox"] li[aria-selected="true"] {
        background-color: var(--border-color) !important;
        color: var(--text-main) !important;
    }

    /* ── Tabs & Header ── */
    header[data-testid="stHeader"] {
        background: var(--bg-color) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background: var(--border-color) !important;
        padding: 6px !important;
        border-radius: 12px !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        font-family: 'Times New Roman', Times, serif !important;
        font-weight: 600 !important;
        padding: 6px 16px !important;
        color: var(--text-muted) !important;
        border: none !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--card-bg) !important;
        color: var(--text-main) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    }

    /* ── Alerts ── */
    div[data-testid="stAlert"] { 
        border-radius: 14px !important; 
        border: none !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04) !important;
        font-family: 'Times New Roman', Times, serif !important;
    }

    /* ── Badge overrides ── */
    .badge { 
        font-family: 'Times New Roman', Times, serif !important; 
        padding: 6px 12px !important; 
        border-radius: 8px !important; 
        font-weight: 700 !important; 
        font-size: 11px !important; 
        text-transform: uppercase !important; 
        letter-spacing: 0.5px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
    }
    .badge.green { background: rgba(16, 185, 129, 0.1) !important; color: #10b981 !important; border: 1px solid rgba(16, 185, 129, 0.3) !important;}
    .badge.yellow { background: rgba(245, 158, 11, 0.1) !important; color: #f59e0b !important; border: 1px solid rgba(245, 158, 11, 0.3) !important;}
    .badge.red { background: rgba(239, 68, 68, 0.1) !important; color: #ef4444 !important; border: 1px solid rgba(239, 68, 68, 0.3) !important;}

    /* ── Progress bar ── */
    .stProgress > div > div { background: linear-gradient(90deg, #7c3aed, #ec4899) !important; border-radius: 999px !important; }
    
    /* ── Tooltips ── */
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted rgba(255,255,255,0.5);
        cursor: help;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 220px;
        background-color: var(--card-bg);
        color: var(--text-main);
        text-align: center;
        border-radius: 8px;
        padding: 8px;
        position: absolute;
        z-index: 100;
        bottom: 125%;
        left: 50%;
        margin-left: -110px;
        opacity: 0;
        transition: opacity 0.3s;
        box-shadow: 0 4px 20px var(--kpi-shadow);
        font-family: 'Inter', sans-serif !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        text-transform: none !important;
        border: 1px solid var(--border-color);
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }

    /* ── Skeleton Loaders ── */
    .skeleton-box {
        display: inline-block;
        height: 1em;
        position: relative;
        overflow: hidden;
        background-color: var(--input-bg);
        border-radius: 4px;
        width: 100%;
    }
    .skeleton-box::after {
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        transform: translateX(-100%);
        background-image: linear-gradient(
            90deg,
            rgba(255, 255, 255, 0) 0,
            rgba(255, 255, 255, 0.2) 20%,
            rgba(255, 255, 255, 0.5) 60%,
            rgba(255, 255, 255, 0)
        );
        animation: shimmer 2s infinite;
        content: '';
    }
    @keyframes shimmer {
        100% {
            transform: translateX(100%);
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "theme" not in st.session_state:
    st.session_state.theme = "light"

# ── Reliable theme: inject CSS variables directly from Python (no JS needed) ──
if st.session_state.theme == "dark":
    st.markdown(
        """
        <style>
        /* ── DARK MODE: CSS variable overrides ── */
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --sidebar-bg-1: #020617;
            --sidebar-bg-2: #1e1b4b;
            --kpi-shadow: rgba(0,0,0,0.3);
            --input-bg: #0f172a;
        }
        /* Main backgrounds */
        .stApp, [data-testid="stAppViewContainer"], .block-container {
            background-color: #0f172a !important;
        }
        /* Main content text — targeted, does NOT touch sidebar or inline-styled elements */
        [data-testid="stMainBlockContainer"] p,
        [data-testid="stMainBlockContainer"] span:not([class*="logo"]):not([class*="badge"]),
        [data-testid="stMainBlockContainer"] label,
        [data-testid="stMarkdownContainer"] > p,
        [data-testid="stMarkdownContainer"] > span,
        .stMarkdown p, .stMarkdown span, .stMarkdown label,
        .element-container p {
            color: #f8fafc !important;
        }
        /* Headings in main content */
        [data-testid="stMainBlockContainer"] h1,
        [data-testid="stMainBlockContainer"] h2,
        [data-testid="stMainBlockContainer"] h3,
        [data-testid="stMainBlockContainer"] h4 { color: #f8fafc !important; }
        /* Inputs */
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"] > div,
        div[data-baseweb="select"] > div {
            background: #1e293b !important;
            border-color: #334155 !important;
        }
        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input {
            color: #f8fafc !important;
            background: transparent !important;
        }
        /* Selectbox dropdown popup — all portals */
        [data-baseweb="popover"],
        [data-baseweb="popover"] > div,
        [data-baseweb="menu"],
        [role="listbox"] {
            background-color: #1e293b !important;
            border-color: #334155 !important;
        }
        [role="option"] {
            background-color: #1e293b !important;
            color: #f8fafc !important;
        }
        [role="option"]:hover,
        [role="option"][aria-selected="true"] {
            background-color: #334155 !important;
        }
        /* ── HTML tables (render_professional_table & inline HTML) ── */
        [data-testid="stMarkdownContainer"] table,
        [data-testid="stMarkdownContainer"] table thead,
        [data-testid="stMarkdownContainer"] table tbody,
        [data-testid="stMarkdownContainer"] table tr {
            background-color: #1e293b !important;
            border-color: #334155 !important;
        }
        [data-testid="stMarkdownContainer"] table td {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border-color: #334155 !important;
        }
        [data-testid="stMarkdownContainer"] table th {
            background-color: #0f172a !important;
            color: #94a3b8 !important;
            border-color: #334155 !important;
        }
        /* override inline white backgrounds inside markdown divs */
        [data-testid="stMarkdownContainer"] div {
            background-color: transparent;
        }
        [data-testid="stMarkdownContainer"] div[style*="background"] {
            background-color: #1e293b !important;
            background: #1e293b !important;
        }
        /* Streamlit stDataFrame */
        .stDataFrame table, .stTable table { background: #1e293b !important; }
        .stDataFrame table th, .stTable table th {
            background: #0f172a !important; color: #94a3b8 !important;
        }
        .stDataFrame table td, .stTable table td {
            color: #f8fafc !important; border-bottom-color: #334155 !important;
        }
        /* Cards */
        .dashboard-card, .stock-info, .category-card {
            background: #1e293b !important; border-color: #334155 !important;
        }
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] { background: #1e293b !important; }
        .stTabs [aria-selected="true"] { background: #0f172a !important; color: #f8fafc !important; }
        .stTabs [data-baseweb="tab"] { color: #94a3b8 !important; }
        /* Expanders */
        .stExpander { background: #1e293b !important; border-color: #334155 !important; }
        /* Alerts */
        div[data-testid="stAlert"] { background: #1e293b !important; }
        /* Metrics */
        div[data-testid="stMetricValue"] { color: #f8fafc !important; }
        div[data-testid="stMetricLabel"] { color: #94a3b8 !important; }
        /* Header */
        header[data-testid="stHeader"] { background: #0f172a !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    # Light mode — restore clean light defaults
    st.markdown(
        """
        <style>
        :root {
            --bg-color: #f4f6fa;
            --card-bg: #ffffff;
            --text-main: #1a1a2e;
            --text-muted: #64748b;
            --border-color: #f1f5f9;
            --sidebar-bg-1: #5b21b6;
            --sidebar-bg-2: #7c3aed;
            --kpi-shadow: rgba(0,0,0,0.08);
            --input-bg: #f8fafc;
        }
        .stApp, [data-testid="stAppViewContainer"], .block-container {
            background-color: #f4f6fa !important;
        }
        /* Inputs */
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"] > div,
        div[data-baseweb="select"] > div {
            background: #f8fafc !important; border-color: #f1f5f9 !important;
        }
        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input { color: #1a1a2e !important; }
        /* Dropdown popup */
        [data-baseweb="popover"], [role="listbox"] {
            background-color: #ffffff !important; border-color: #e2e8f0 !important;
        }
        [role="option"] { background-color: #ffffff !important; color: #1a1a2e !important; }
        [role="option"]:hover { background-color: #f1f5f9 !important; }
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] { background: #f1f5f9 !important; }
        .stTabs [aria-selected="true"] { background: #ffffff !important; color: #1a1a2e !important; }
        header[data-testid="stHeader"] { background: #f4f6fa !important; }
        .stExpander { background: #ffffff !important; border-color: #f1f5f9 !important; }
        div[data-testid="stMetricValue"] { color: #0f172a !important; }
        div[data-testid="stMetricLabel"] { color: #64748b !important; }
        /* Light mode: force HTML tables white */
        [data-testid="stMarkdownContainer"] table td { background-color: #ffffff !important; color: #1a1a2e !important; }
        [data-testid="stMarkdownContainer"] table th { background-color: #f8fafc !important; color: #475569 !important; }
        [data-testid="stMarkdownContainer"] div[style*="background"] { background-color: #ffffff !important; background: #ffffff !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.sidebar.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
    <style>
      .logo-sidebar {
        background:#03001a;
        border:1px solid #1a00ff33;
        border-radius:12px;
        padding:15px;
        display:flex;
        align-items:center;
        gap:10px;
        font-family:'Orbitron',monospace;
        text-align:left;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
      }
      .logo-sidebar .icon { width:40px; height:40px; flex-shrink:0; }
      .logo-sidebar .main { font-weight:900; font-size:12px; letter-spacing:2px; color:#4488ff; text-transform:uppercase; line-height:1.2; margin:0; }
      .logo-sidebar .main span { color:#00ddff; }
      .logo-sidebar .sub { font-size:7px; letter-spacing:3px; color:#334466; margin-top:4px; margin-bottom:0; }
    </style>
    <div class="logo-sidebar">
      <div class="icon">
        <svg viewBox="0 0 58 58">
          <circle cx="29" cy="29" r="27" stroke="#4488ff" stroke-width="1.5" stroke-dasharray="4 2" fill="none"/>
          <circle cx="29" cy="29" r="18" stroke="#00ddff" stroke-width="1" fill="none"/>
          <circle cx="29" cy="29" r="5" fill="#00ddff"/>
          <line x1="29" y1="2" x2="29" y2="12" stroke="#4488ff" stroke-width="2"/>
          <line x1="29" y1="46" x2="29" y2="56" stroke="#4488ff" stroke-width="2"/>
          <line x1="2" y1="29" x2="12" y2="29" stroke="#4488ff" stroke-width="2"/>
          <line x1="46" y1="29" x2="56" y2="29" stroke="#4488ff" stroke-width="2"/>
        </svg>
      </div>
      <div>
        <div class="main">Predictive<br><span>Retail</span></div>
        <div class="sub">INTELLIGENCE</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

nav_items = ["Dashboard", "Inventory", "Stockouts & Lost Sales", "AI Decision Support", "Management", "Pricing", "Reports"]
if st.session_state.get("role") == "super_admin":
    nav_items.append("User Management")

menu = st.sidebar.radio(
    "Navigation",
    nav_items,
    key="menu",
    index=nav_items.index(st.session_state.get("menu")) if st.session_state.get("menu") in nav_items else 0
)

st.sidebar.markdown("---")
if st.sidebar.button(f"🌙 Toggle {'Light' if st.session_state.theme == 'dark' else 'Dark'} Mode", key='toggle_theme'):
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
    st.rerun()

# ── Sidebar user info badge ──
_role_disp = st.session_state.get("role", "User")
_uname_disp = st.session_state.get("username", "User")
_role_badge_color = "#f59e0b" if _role_disp == "super_admin" else ("rgba(255,255,255,0.3)" if _role_disp == "Admin" else "#10b981")
_role_label = "⭐ Super Admin" if _role_disp == "super_admin" else ("🛡 Admin" if _role_disp == "Admin" else "👤 User")
st.sidebar.markdown(
    f"""
    <div class='user-badge-container'>
      <div class='user-badge-name'>{''.join(c[0].upper() for c in _uname_disp.split()[:2])} &nbsp;{_uname_disp}</div>
      <div class='user-badge-role' style='background:{_role_badge_color} !important;'>{_role_label}</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", key="logout_btn"):
    st.session_state.logged_in = False
    st.session_state.username = None
    if "fp_step" in st.session_state:
        st.session_state.fp_step = 1
    st.rerun()

# ---------------- DIAGNOSTICS (captures recent errors) ----------------
with st.sidebar.expander("Diagnostics / Error Log", expanded=False):
    if os.path.exists(LOG_FILE):
        try:
            _log = open(LOG_FILE, "r", encoding="utf-8").read()
        except Exception as e:
            _log = f"Failed to read log: {e}"
        st.text_area("Recent errors (tail)", value=_log[-20000:], height=240)

        # Detect missing package errors (ModuleNotFoundError or No module named)
        import re
        m = re.search(r"No module named '([^']+)'", _log) or re.search(r"ModuleNotFoundError: No module named '([^']+)'", _log)
        if m:
            pkg = m.group(1)
            st.warning(f"Missing package detected: {pkg}")
            if st.button(f"Install {pkg}"):
                with st.spinner(f"Installing {pkg} ..."):
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                        st.success(f"Install command for {pkg} executed. Please reload the app.")
                    except Exception as e:
                        st.error(f"Failed to install {pkg}: {e}")

        # ImportError for specific symbol
        m2 = re.search(r"cannot import name '([^']+)'", _log)
        if m2:
            sym = m2.group(1)
            st.warning(f"ImportError: cannot import name '{sym}'. Check the module for that symbol or version mismatch.")
    else:
        st.success("No runtime errors captured yet.")

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=60)  # Cache for 1 minute
def load_products():
    """Load products always from CSV (source of truth)."""
    return pd.read_csv(os.path.join(BACKEND_DIR, "data", "products.csv"))

df = load_products()
products = df["product_name"].tolist()

# ---------------- GLOBAL CSS (Whitespace fix) ----------------
st.markdown(
    """
    <style>
    /* Maximize space for an 'App' feeling (especially online) */
    .block-container { max-width: 100% !important; width: 100% !important; padding: 1rem 3rem !important; }
    .stApp { min-width: unset !important; }
    header[data-testid="stHeader"] { height: 3rem !important; }
    footer { visibility: hidden !important; }
    
    /* Neumorphic text inputs for global consistency */
    div[data-baseweb="input"] { border-radius: 8px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- DASHBOARD PAGE ----------------
if menu == "Dashboard":

    # --- Custom CSS for dashboard styling (cards, badges, layout) ---
    st.markdown(
        """
        <style>
        .dashboard-container {max-width:100%;margin:0 auto;padding:20px}
        
    /* KPI Row and individual KPI styling */
    .kpi-row{display:flex;gap:20px;margin-bottom:30px;flex-wrap:wrap}
    .kpi{
        flex:1;min-width:180px;padding:24px;border-radius:20px;
        color:white;font-weight:500;
        position: relative; overflow: hidden;
    }
    .kpi::after {
        content: ''; position: absolute; top: 0; right: 0; bottom: 0; left: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 100%);
        opacity: 0.5; pointer-events: none;
    }
    .kpi .label{font-size:13px;opacity:0.9;font-weight:600;letter-spacing:0.5px; text-transform: uppercase;}
    .kpi .value{font-weight:800;font-size:28px;margin-top:10px; letter-spacing: -0.5px;}
        
    /* KPI Color Classes - Apple-inspired premium gradients */
    .kpi.purple {background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); box-shadow: 0 12px 30px -5px rgba(147, 51, 234, 0.4);}
    .kpi.blue {background: linear-gradient(135deg, #3b82f6 0%, #0ea5e9 100%); box-shadow: 0 12px 30px -5px rgba(59, 130, 246, 0.4);}
    .kpi.cyan {background: linear-gradient(135deg, #f43f5e 0%, #f97316 100%); box-shadow: 0 12px 30px -5px rgba(244, 63, 94, 0.4);} 
    .kpi.green {background: linear-gradient(135deg, #10b981 0%, #14b8a6 100%); box-shadow: 0 12px 30px -5px rgba(16, 185, 129, 0.4);}
    .kpi.pink {background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%); box-shadow: 0 12px 30px -5px rgba(236, 72, 153, 0.4);}
        
    /* Section and content styling */
    .overview, .stock-info, .ai-insights, .top-selling {margin-bottom:32px;}
    .ai-tile{
        display:inline-block;width:150px;padding:16px;margin-right:12px;
        border-radius:14px;background: var(--card-bg);
        box-shadow: inset 0 2px 4px rgba(255,255,255,0.02), 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid var(--border-color); vertical-align:top; transition: transform 0.2s;
    }
    .ai-tile:hover { transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.1); }
    .ai-tile strong { color: var(--text-main); font-size: 14px; }
    .ai-tile small { color: var(--text-muted); font-weight: 500; }
    
    .top-selling .item{display:flex;align-items:center;justify-content:space-between;padding:14px 10px;border-bottom:1px solid var(--border-color); transition: background 0.2s;}
    .top-selling .item:hover { background: var(--input-bg); border-radius: 8px; }
        
    /* Table styling */
    .stTable, .stDataFrame, .dashboard-card .stTable, .dashboard-card .stDataFrame { overflow-x: auto; width: 100%; }
    .stTable table th, .stTable table td, .stDataFrame table th, .stDataFrame table td, .dashboard-card table th, .dashboard-card table td { overflow: visible; max-width: none; padding: 16px 18px !important; font-size: 15px !important; }
    .stTable table, .stDataFrame table, .dashboard-card table { table-layout: auto; width: 100%; }
        
    /* Responsive tweaks */
    @media (max-width: 1100px){ .kpi-row{flex-direction:column} .ai-tile{width:100%;margin-bottom:10px} }
    @media (max-width: 600px){ .dashboard-card{padding:16px} .kpi{min-width:100%}}

        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- Header / Product selector + KPI row ---
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        st.markdown("<h2 style='margin:0 0 4px 0'>Dashboard</h2>", unsafe_allow_html=True)
        selected_product = st.selectbox("Search product", products)
    # Col2 removed (logo)

    try:
        data = cached_get_dashboard_data(selected_product)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # Safe calculation for total revenue and other metrics
    total_sales = float(data.get("sales") or 0.0)
    total_price = float(data.get("final_price") or 0.0)
    total_revenue = total_sales * total_price
    units_sold = int(total_sales)
    avg_price = total_price
    turnover = data.get("turnover", "N/A")

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.markdown(f"<div class='kpi purple'><div class='label tooltip'>Total revenue<span class='tooltiptext'>Total gross income from sales in the period.</span></div><div class='value'>₹{total_revenue:,.2f}</div></div>", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"<div class='kpi blue'><div class='label tooltip'>Units sold (30d)<span class='tooltiptext'>Total individual items sold in the last 30 days.</span></div><div class='value'>{units_sold}</div></div>", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"<div class='kpi cyan'><div class='label tooltip'>Avg unit price<span class='tooltiptext'>Average final selling price across all transactions.</span></div><div class='value'>₹{avg_price:,.2f}</div></div>", unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"<div class='kpi green'><div class='label tooltip'>Inventory turnover<span class='tooltiptext'>Ratio showing how many times inventory was sold and replaced over the period.</span></div><div class='value'>{turnover}</div></div>", unsafe_allow_html=True)
    with kpi5:
        st.markdown(f"<div class='kpi pink'><div class='label tooltip'>Data health<span class='tooltiptext'>Quality score based on completeness and recency of product metadata.</span></div><div class='value'>{data.get('data_health_score','N/A')}%</div></div>", unsafe_allow_html=True)

    # --- Main content: left overview and right summary ---
    left, right = st.columns([3, 3])
    with left:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Income (this month)", "₹53,790", "+5.1%")
            st.progress(0.51)
        with col2:
            st.metric("Expenses (this month)", "₹10,701", "-2.3%")
            st.progress(0.29)
        
        st.markdown("<hr style='margin: 20px 0; opacity: 0.1;'>", unsafe_allow_html=True)
        
        st.markdown(f"<h4 style='margin-bottom:12px'>Product Overview</h4>", unsafe_allow_html=True)
        # show product name with classification badge(s)
        # display internal classification and AI prediction
        value_class = data.get('value_class', 'C')
        demand_pattern = data.get('demand_pattern', 'X')
        season = data.get('seasonality', '')
        ai_value = data.get('ai_value')
        ai_pattern = data.get('ai_pattern')
        ai_conf = data.get('ai_confidence', 0.0)

        badge_cls = 'green' if value_class == 'A' else ('yellow' if value_class == 'B' else 'red')
        pattern_cls = 'green' if demand_pattern == 'X' else ('yellow' if demand_pattern == 'Y' else 'red')
        season_cls = 'yellow' if season == 'SEASONAL' or season == 'FESTIVE' else 'green'

        # Maps for real categories
        v_map = {'A': 'High Value (A)', 'B': 'Medium Value (B)', 'C': 'Low Value (C)'}
        p_map = {'X': 'Steady (X)', 'Y': 'Variable (Y)', 'Z': 'Erratic (Z)'}
        s_map = {'REGULAR': 'Regular Demand', 'SEASONAL': 'Seasonal', 'FESTIVE': 'Festive'}
        
        display_vc = v_map.get(value_class, value_class)
        display_dp = p_map.get(demand_pattern, demand_pattern)
        display_s = s_map.get(season, season)

        # build label text including AI prediction
        ai_text = f" (AI: {ai_value}-{ai_pattern} conf:{int(ai_conf*100)}%)" if ai_value and ai_pattern else ""
        st.markdown(f"<strong style='font-size:20px'>{selected_product}</strong>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin: 8px 0;'><span class='badge {badge_cls}'>{display_vc}</span> <span class='badge {pattern_cls}' style='margin-left:6px'>{display_dp}</span> <span class='badge {season_cls}' style='margin-left:6px'>{display_s}</span><small style='margin-left:8px;color:#6b7280'>{ai_text}</small></div>", unsafe_allow_html=True)
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("Price", f"₹{data.get('price', 0):,.2f}")
        with m_col2:
            st.metric("Stock", int(data.get('stock', 0)))
        with m_col3:
            st.metric("Discount", f"{data.get('discount', 0)}%")

        # --- AI discount recommendation (Default: Profit) ---
        st.markdown("**AI Optimization (Profit Goal)**")
        objective = "profit"
        try:
            prod_row = df.loc[df['product_name'] == selected_product].iloc[0].to_dict()
            ai_rec = disc_service.ai_recommend_discount(prod_row, objective=objective.lower())
        except Exception:
            ai_rec = None

        if ai_rec:
            st.markdown(f"<div style='font-size:13px; color: #475569;'>Suggested: <b style='color:#2563eb'>{ai_rec['recommended_discount']}%</b> ({int(ai_rec['confidence']*100)}% conf)</div>", unsafe_allow_html=True)
            
            # --- SHOW OUTPUT DETAILS ---
            with st.expander("📊 View Projected Outcome"):
                st.markdown(f"""
                <div style='padding:10px; background:#f8fafc; border-radius:8px; border:1px solid #e2e8f0;'>
                    <div style='margin-bottom:8px'><small>Expected Sales</small><br><b>{ai_rec['expected_units']} units/mo</b></div>
                    <div style='margin-bottom:8px'><small>Expected Revenue</small><br><b>₹{ai_rec['expected_revenue']:,.0f}</b></div>
                    <div><small>Expected Profit</small><br><b style='color:#10b981'>₹{ai_rec['expected_profit']:,.0f}</b></div>
                </div>
                """, unsafe_allow_html=True)
                st.info("💡 You can apply this discount in the section at the bottom of the page.")


    with right:
        st.markdown(f"<h4 style='margin-bottom:12px'>Category Revenue</h4>", unsafe_allow_html=True)
        
        # --- Category selector and Revenue donut ---
        existing_cats = sorted(df["category"].dropna().unique().tolist())
        categories = ["All"] + existing_cats

        if "category_selected" not in st.session_state:
            st.session_state["category_selected"] = "All"
        try:
            prod_cat = df.loc[df["product_name"] == selected_product, "category"].iat[0]
        except Exception:
            prod_cat = None
        if st.session_state.get("_last_selected_product") != selected_product:
            st.session_state["_last_selected_product"] = selected_product
            if prod_cat:
                st.session_state["category_selected"] = prod_cat

        category_choice = st.selectbox("Select Category", options=categories, key="category_selected", label_visibility="collapsed")

        # Compute aggregated revenue
        if category_choice == "All":
            agg = (df.assign(revenue=df["selling_price"] * df["monthly_sales"])
                  .groupby("category")["revenue"].sum().sort_values(ascending=False))
            labels = agg.index.tolist()
            sizes = agg.values.tolist()
        else:
            agg = (df[df["category"] == category_choice]
                  .assign(revenue=lambda d: d["selling_price"] * d["monthly_sales"])
                  .groupby("product_name")["revenue"].sum().sort_values(ascending=False))
            labels = agg.index.tolist()
            sizes = agg.values.tolist()

        if not agg.empty:
            if len(labels) > 6:
                top = agg.iloc[:6]
                others = agg.iloc[6:].sum()
                labels = top.index.tolist() + ["Other"]
                sizes = list(top.values) + [others]

        if not agg.empty:
            import plotly.graph_objects as go
            fig = go.Figure(data=[go.Pie(
                labels=labels, values=sizes, hole=0.5,
                marker=dict(colors=px.colors.qualitative.Pastel),
                textinfo='percent', textposition='inside'
            )])
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                margin=dict(t=40, b=0, l=0, r=0),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

            breakdown_mini = pd.DataFrame({
                'Name': labels,
                'Revenue': [f"₹{s:,.0f}" for s in sizes]
            })
            with st.expander("Show detailed revenue list"):
                st.markdown(render_professional_table(breakdown_mini, columns_style={'Revenue': {'align': 'right'}}), unsafe_allow_html=True)

    # --- AI Insights (Full Width) ---
    st.markdown("<hr style='margin: 30px 0; opacity: 0.1;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#1a1a2e; font-weight:700; font-size:20px; margin-bottom: 20px;'>AI Insights</h4>", unsafe_allow_html=True)

    top_items = df.sort_values("monthly_sales", ascending=False).head(3)
    
    ins_col1, ins_col2, ins_col3 = st.columns(3)
    cols = [ins_col1, ins_col2, ins_col3]
    
    for i, (_, row) in enumerate(top_items.iterrows()):
        with cols[i]:
            stock_val = row['stock']
            stock_label = "🟢 In Stock" if stock_val > 20 else "🔴 Low Stock"
            st.markdown(
                f"""
                <div style='padding:24px; border-radius:18px; background:var(--card-bg); border:1px solid var(--border-color); box-shadow: 0 4px 12px var(--kpi-shadow); text-align:center;'>
                    <div style='color:var(--text-muted); font-size:12px; font-weight:700; text-transform:uppercase; margin-bottom:8px;'>Top Performer</div>
                    <div style='color:var(--text-main); font-size:18px; font-weight:800; margin-bottom:12px;'>{row['product_name']}</div>
                    <div style='color:var(--text-main); font-size:15px; font-weight:600; margin-bottom:12px;'>{int(row['monthly_sales'])} sold/mo</div>
                    <div style='color:#2563eb; font-weight:700;'>{stock_label}</div>
                </div>
                """,
                unsafe_allow_html=True
            )



    # Add Demand Pattern Classification table
    try:
        patterns = get_demand_pattern_classification(BACKEND_DIR)
        if not patterns.empty:
            st.markdown("---")
            # Rename columns for brevity and clarity
            display_df = patterns[['product_name', 'value_class', 'demand_pattern', 'seasonality', 'cv', 'ai_value', 'ai_pattern', 'ai_confidence']].copy()
            display_df.columns = ['Product', 'Class', 'Pattern', 'Season', 'CV', 'AI Val', 'AI Pat', 'AI Conf']
            display_df = display_df.sort_values(['Class','CV'], ascending=[True, False]).reset_index(drop=True)
            
            # Map to descriptive names
            display_df['Class'] = display_df['Class'].map({'A': 'High Value (A)', 'B': 'Medium Value (B)', 'C': 'Low Value (C)'}).fillna(display_df['Class'])
            display_df['Pattern'] = display_df['Pattern'].map({'X': 'Steady (X)', 'Y': 'Variable (Y)', 'Z': 'Erratic (Z)'}).fillna(display_df['Pattern'])
            display_df['Season'] = display_df['Season'].map({'REGULAR': 'Regular Demand', 'SEASONAL': 'Seasonal', 'FESTIVE': 'Festive'}).fillna(display_df['Season'])
            
            # Show core columns in main table
            core_cols = ['Product', 'Class', 'Pattern', 'Season']
            core_df = display_df[core_cols].copy()
            
            # Create professional HTML table with double-sticky header (Title + Columns)
            demand_html = '<div style="margin: 32px 0; padding: 0; background: var(--card-bg); border-radius: 14px; box-shadow: 0 4px 16px var(--kpi-shadow); border: 1px solid var(--border-color); overflow-x: auto; max-height: 520px; overflow-y: auto; position: relative;">'
            
            # 1. Sticky Title
            demand_html += '<div style="position: sticky; top: 0; background: var(--card-bg); z-index: 20; padding: 24px 28px 10px 28px; border-bottom: 1px solid var(--border-color);">'
            demand_html += f'<h4 style="margin: 0; color: var(--text-main); font-weight: 700; font-size: 18px; font-family: \'Times New Roman\', Times, serif;">Demand Pattern Classification</h4>'
            demand_html += '</div>'
            
            demand_html += '<table style="width: 100%; border-collapse: collapse; font-family: \'Times New Roman\', Times, serif;">'
            
            # 2. Sticky Table Header
            demand_html += f'<thead><tr style="background: var(--input-bg);">'
            for col in core_cols:
                demand_html += f'<th style="position: sticky; top: 60px; background: var(--input-bg); z-index: 10; padding: 18px 28px; text-align: left; font-weight: 700; color: var(--text-muted); font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid var(--border-color);">{col}</th>'
            demand_html += '</tr></thead>'
            
            demand_html += '<tbody>'
            for idx, row in core_df.iterrows():
                demand_html += '<tr style="border-bottom: 1px solid var(--border-color); transition: background-color 0.2s;">'
                for col in core_cols:
                    value = row[col]
                    demand_html += f'<td style="padding: 16px 28px; text-align: left; color: var(--text-main); font-size: 15px;">{value}</td>'
                demand_html += '</tr>'
            demand_html += '</tbody></table>'
            demand_html += '</div>'
            
            st.markdown(demand_html, unsafe_allow_html=True)
            
        else:
            st.info("No demand pattern data available.")

    except Exception as e:
        st.warning(f"Failed to load demand pattern classification: {e}")


    # ---------------- APPLY DISCOUNT ----------------
    st.markdown("---")
    if data.get("discount", 0) == 0:
        st.info("No discount recommended for this product.")
    else:
        st.markdown("<h4 style='margin:0 0 16px 0; color:#1a1a2e; font-size:18px;'>Apply Recommended Discount</h4>", unsafe_allow_html=True)
        persist = st.checkbox("Persist discount to CSV/DB (make change permanent)", value=False)
        if st.button("Apply Discount", key="apply_discount"):
            try:
                # Only persist if requested
                if persist:
                    # Try DB first
                    try:
                        from backend.db import SessionLocal
                        from backend.models import Product
                        session = SessionLocal()
                        prod = session.query(Product).filter(Product.product_name == selected_product).one_or_none()
                        if prod:
                            old = int(prod.discount or 0)
                            prod.discount = data["discount"]
                            prod.selling_price = data["final_price"]
                            session.add(prod)
                            session.commit()
                            session.close()
                            try:
                                disc_service.log_discount_change(selected_product, old, data["discount"], user=st.session_state.get('username', 'webui'), note='Applied via UI')
                            except Exception:
                                pass
                            st.success("Discount persisted to DB and applied.")
                            st.experimental_rerun()
                        else:
                            session.close()
                            st.error("Product not found in DB to persist discount.")
                    except Exception:
                        # fallback to CSV
                        csv_path = os.path.join(BACKEND_DIR, "data", "products.csv")
                        if not os.path.exists(csv_path):
                            st.error("Products CSV not found to persist discount.")
                        else:
                            csv_df = pd.read_csv(csv_path)
                            mask = csv_df["product_name"] == selected_product
                            if not mask.any():
                                st.error("Product not found in CSV to persist discount.")
                            else:
                                csv_df.loc[mask, "discount"] = data["discount"]
                                # update selling_price to reflect discounted price
                                csv_df.loc[mask, "selling_price"] = data["final_price"]
                                csv_df.to_csv(csv_path, index=False)
                                st.success("Discount persisted to CSV and applied.")
                                st.experimental_rerun()
                else:
                    st.success(f"Applied {data['discount']}% discount to {selected_product} (session-only). New price: ₹{data['final_price']:,.2f}")
            except Exception as e:
                st.error(f"Failed to apply discount: {e}")
    # Closing div removed

    st.markdown("<br>", unsafe_allow_html=True)

    # Keep Add Product expander (unchanged)
    st.markdown("---")
    st.markdown("<h4 style='color:#1a1a2e; font-size:18px;'>Quick Actions</h4>", unsafe_allow_html=True)
    with st.expander("Add new product to catalog", expanded=False):
        with st.form("add_product_form"):
            pid = st.text_input("Product ID")
            name = st.text_input("Product Name")

            # Category selector populated from existing CSV categories with an 'Other' option
            existing_cats = sorted(df["category"].dropna().unique().tolist())
            cat_options = ["Select category"] + existing_cats + ["Other"]
            category_choice = st.selectbox("Category", options=cat_options, index=0)
            if category_choice == "Other":
                category_in = st.text_input("Category (new)")
            elif category_choice == "Select category":
                category_in = ""
            else:
                category_in = category_choice

            cost_price = st.number_input("Cost Price", min_value=0.0, value=0.0, step=0.5)
            selling_price = st.number_input("Selling Price", min_value=0.0, value=0.0, step=0.5)
            discount_in = st.number_input("Discount (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            stock_in = st.number_input("Stock", min_value=0, value=0, step=1)
            monthly_sales_in = st.number_input("Monthly Sales", min_value=0, value=0, step=1)
            demand_level = st.selectbox("Demand Level", ["LOW", "MEDIUM", "HIGH"])
            rating_in = st.number_input("Rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
            supplier_lead = st.number_input("Supplier Lead Time (days)", min_value=0, value=7, step=1)

            submit_add = st.form_submit_button("Add Product")

            if submit_add:
                # Basic validation
                if not name or not pid:
                    st.error("Product ID and Product Name are required.")
                else:
                    # Try DB insert first
                    try:
                        from backend.db import SessionLocal
                        from backend.models import Product
                        session = SessionLocal()
                        # check duplicate by id or name
                        exists = session.query(Product).filter((Product.product_id == pid) | (Product.product_name == name)).one_or_none()
                        if exists:
                            st.error("Product with this ID or name already exists in DB.")
                            session.close()
                        else:
                            prod = Product(
                                product_id=pid,
                                product_name=name,
                                category=category_in,
                                cost_price=float(cost_price),
                                selling_price=float(selling_price),
                                discount=float(discount_in),
                                stock=int(stock_in),
                                monthly_sales=int(monthly_sales_in),
                                demand_level=demand_level,
                                rating=float(rating_in),
                                supplier_lead_time=int(supplier_lead)
                            )
                            session.add(prod)
                            session.commit()
                            session.close()
                            st.success(f"Product '{name}' added to catalog (DB).")
                            st.experimental_rerun()
                    except Exception:
                        # fallback to CSV
                        csv_path = os.path.join(BACKEND_DIR, "data", "products.csv")
                        try:
                            # Load or create CSV
                            if os.path.exists(csv_path):
                                csv_df = pd.read_csv(csv_path)
                            else:
                                csv_df = pd.DataFrame(columns=["product_id","product_name","category","cost_price","selling_price","discount","stock","monthly_sales","demand_level","rating","supplier_lead_time"])

                            # Check duplicate by product_name
                            if name in csv_df["product_name"].values:
                                st.error("Product with this name already exists in CSV.")
                            else:
                                new_row = {
                                    "product_id": pid,
                                    "product_name": name,
                                    "category": category_in,
                                    "cost_price": float(cost_price),
                                    "selling_price": float(selling_price),
                                    "discount": float(discount_in),
                                    "stock": int(stock_in),
                                    "monthly_sales": int(monthly_sales_in),
                                    "demand_level": demand_level,
                                    "rating": float(rating_in),
                                    "supplier_lead_time": int(supplier_lead)
                                }

                                csv_df = pd.concat([csv_df, pd.DataFrame([new_row])], ignore_index=True)
                                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                                csv_df.to_csv(csv_path, index=False)
                                st.success(f"Product '{name}' added to catalog (CSV fallback).")
                                st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Failed to add product: {e}")
    # Closing div removed




# ---------------- INVENTORY PAGE ----------------
elif menu == "Inventory":

    st.markdown("## Inventory")

    # Threshold selector
    low_threshold = st.slider("Low stock threshold", 1, 100, 20)

    # Summary metrics
    total_products = len(df)
    total_units = int(df["stock"].sum())
    low_stock_count = int((df["stock"] < low_threshold).sum())

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Products", total_products)
    m2.metric("Total Units", f"{total_units}")
    m3.metric(f"Low Stock Items (< {low_threshold})", low_stock_count)

    st.markdown("---")

    # Filters
    categories = ["All"] + sorted(df["category"].dropna().unique().tolist())
    cat = st.selectbox("Category", categories)

    df_filtered = df.copy()
    if cat != "All":
        df_filtered = df_filtered[df_filtered["category"] == cat]

    # Product selector (category-aware)
    product_options = ["All"] + sorted(df_filtered["product_name"].dropna().unique().tolist())
    product_select = st.selectbox("Product", product_options)
    if product_select != "All":
        df_filtered = df_filtered[df_filtered["product_name"] == product_select]

    # Reorder calculation
    def _compute_reorder(row):
        # robustly compute recommended reorder qty (handle NaN and missing values)
        try:
            lead = int(row.get("supplier_lead_time") or 0)
        except Exception:
            lead = 0
        monthly = row.get("monthly_sales", 0)
        try:
            monthly = float(monthly)
            if pd.isna(monthly) or monthly < 0:
                monthly = 0.0
        except Exception:
            monthly = 0.0
        demand_per_day = monthly / 30.0
        expected = demand_per_day * lead
        # safety buffer: at least 1 unit; use 10% of expected when meaningful
        safety = 1
        if pd.notna(expected) and expected > 0:
            safety = max(1, int(0.1 * expected))
        stock = int(row.get("stock") or 0)
        reorder = max(0, int(np.ceil(expected + safety - stock))) if expected > 0 else 0
        return reorder

    df_filtered = df_filtered.copy()
    df_filtered["reorder_qty"] = df_filtered.apply(_compute_reorder, axis=1)
    df_filtered["status"] = np.where(df_filtered["stock"] < low_threshold, "LOW", "OK")

    # Table
    st.subheader("Inventory Table")
    st.dataframe(df_filtered[["product_name", "category", "stock", "monthly_sales", "supplier_lead_time", "reorder_qty", "status"]].sort_values("stock"), use_container_width=True)

    st.markdown("---")

    st.subheader("Low stock items")
    low_df = df_filtered[df_filtered["stock"] < low_threshold].sort_values("stock")
    if low_df.empty:
        st.success("No items below the threshold.")
    else:
        st.dataframe(low_df[["product_name", "stock", "monthly_sales", "reorder_qty"]].reset_index(drop=True), use_container_width=True)

        # ---------------- MANAGE PRODUCT (Update / Delete) ----------------
        st.markdown("---")
        st.subheader("Manage Product")

        manage_products = df["product_name"].tolist()
        selected_manage = st.selectbox("Select product to manage", options=manage_products)

        if selected_manage:
            prod_row = df[df["product_name"] == selected_manage].iloc[0]

            with st.expander("Edit product details", expanded=False):
                with st.form("update_product_form"):
                    pid = prod_row.get("product_id", "")
                    st.text_input("Product ID", value=pid, key="manage_pid", disabled=True)

                    name = st.text_input("Product Name", value=prod_row.get("product_name", ""), key="manage_name")

                    # Category selector
                    existing_cats = sorted(df["category"].dropna().unique().tolist())
                    cat_options = ["Select category"] + existing_cats + ["Other"]
                    category_choice = st.selectbox("Category", options=cat_options, index=0, key="manage_cat_choice")
                    if category_choice == "Other":
                        category_in = st.text_input("Category (new)", value=prod_row.get("category", ""), key="manage_cat_new")
                    elif category_choice == "Select category":
                        category_in = prod_row.get("category", "")
                    else:
                        category_in = category_choice

                    cost_price = st.number_input("Cost Price", min_value=0.0, value=float(prod_row.get("cost_price") or 0.0), step=0.5, key="manage_cost")
                    selling_price = st.number_input("Selling Price", min_value=0.0, value=float(prod_row.get("selling_price") or 0.0), step=0.5, key="manage_sell")
                    discount_in = st.number_input("Discount (%)", min_value=0.0, max_value=100.0, value=float(prod_row.get("discount") or 0.0), step=0.5, key="manage_disc")
                    stock_in = st.number_input("Stock", min_value=0, value=int(prod_row.get("stock") or 0), step=1, key="manage_stock")
                    monthly_sales_in = st.number_input("Monthly Sales", min_value=0, value=int(prod_row.get("monthly_sales") or 0), step=1, key="manage_monthly")
                    demand_level = st.selectbox("Demand Level", ["LOW", "MEDIUM", "HIGH"], index=["LOW","MEDIUM","HIGH"].index(prod_row.get("demand_level", "MEDIUM")), key="manage_demand")
                    rating_in = st.number_input("Rating", min_value=0.0, max_value=5.0, value=float(prod_row.get("rating") or 0.0), step=0.1, key="manage_rating")
                    supplier_lead = st.number_input("Supplier Lead Time (days)", min_value=0, value=int(prod_row.get("supplier_lead_time") or 0), step=1, key="manage_lead")

                    submit_update = st.form_submit_button("Update Product")

                    if submit_update:
                        # Try DB update first
                        try:
                            from backend.db import SessionLocal
                            from backend.models import Product
                            session = SessionLocal()
                            # prefer product_id if available
                            prod = None
                            if pid:
                                prod = session.query(Product).filter(Product.product_id == str(pid)).one_or_none()
                            if prod is None:
                                prod = session.query(Product).filter(Product.product_name == selected_manage).one_or_none()

                            if prod is None:
                                session.close()
                                # fallback to CSV
                                raise LookupError("not found in DB")

                            prod.product_name = name
                            prod.category = category_in
                            prod.cost_price = float(cost_price)
                            prod.selling_price = float(selling_price)
                            prod.discount = float(discount_in)
                            prod.stock = int(stock_in)
                            prod.monthly_sales = int(monthly_sales_in)
                            prod.demand_level = demand_level
                            prod.rating = float(rating_in)
                            prod.supplier_lead_time = int(supplier_lead)
                            session.add(prod)
                            session.commit()
                            session.close()
                            st.success(f"Product '{name}' updated successfully (DB).")
                            st.experimental_rerun()
                        except Exception:
                            # fallback to CSV
                            csv_path = os.path.join(BACKEND_DIR, "data", "products.csv")
                            try:
                                if not os.path.exists(csv_path):
                                    st.error("Products CSV not found to persist update.")
                                else:
                                    csv_df = pd.read_csv(csv_path)

                                    # Prefer product_id as identifier when available
                                    if pid and "product_id" in csv_df.columns and pid in csv_df["product_id"].astype(str).values:
                                        mask = csv_df["product_id"].astype(str) == str(pid)
                                    else:
                                        mask = csv_df["product_name"] == selected_manage

                                    if not mask.any():
                                        st.error("Product not found in CSV to update.")
                                    else:
                                        csv_df.loc[mask, "product_name"] = name
                                        csv_df.loc[mask, "category"] = category_in
                                        csv_df.loc[mask, "cost_price"] = float(cost_price)
                                        csv_df.loc[mask, "selling_price"] = float(selling_price)
                                        csv_df.loc[mask, "discount"] = float(discount_in)
                                        csv_df.loc[mask, "stock"] = int(stock_in)
                                        csv_df.loc[mask, "monthly_sales"] = int(monthly_sales_in)
                                        csv_df.loc[mask, "demand_level"] = demand_level
                                        csv_df.loc[mask, "rating"] = float(rating_in)
                                        csv_df.loc[mask, "supplier_lead_time"] = int(supplier_lead)

                                        csv_df.to_csv(csv_path, index=False)
                                        st.success(f"Product '{name}' updated successfully (CSV fallback).")
                                        st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Failed to update product: {e}")

            with st.expander("Delete product", expanded=False):
                st.write(f"Delete **{selected_manage}** from catalog")
                confirm = st.checkbox("I understand this action cannot be undone", key="confirm_delete")
                if st.button("Delete Product"):
                    if not confirm:
                        st.error("Please confirm deletion by checking the box above.")
                    else:
                        # Try DB delete first
                        try:
                            from backend.db import SessionLocal
                            from backend.models import Product
                            session = SessionLocal()
                            pid_val = prod_row.get("product_id", "")
                            if pid_val:
                                prod = session.query(Product).filter(Product.product_id == str(pid_val)).one_or_none()
                            else:
                                prod = session.query(Product).filter(Product.product_name == selected_manage).one_or_none()

                            if prod is None:
                                session.close()
                                raise LookupError("not found in DB")

                            session.delete(prod)
                            session.commit()
                            session.close()
                            st.success(f"Product '{selected_manage}' deleted from catalog (DB).")
                            st.experimental_rerun()
                        except Exception:
                            # fallback to CSV
                            csv_path = os.path.join(BACKEND_DIR, "data", "products.csv")
                            try:
                                if not os.path.exists(csv_path):
                                    st.error("Products CSV not found to persist delete.")
                                else:
                                    csv_df = pd.read_csv(csv_path)

                                    # Prefer product_id if present
                                    pid = prod_row.get("product_id", "")
                                    if pid and "product_id" in csv_df.columns and pid in csv_df["product_id"].astype(str).values:
                                        mask = csv_df["product_id"].astype(str) == str(pid)
                                    else:
                                        mask = csv_df["product_name"] == selected_manage

                                    if not mask.any():
                                        st.error("Product not found in CSV to delete.")
                                    else:
                                        csv_df = csv_df.loc[~mask]
                                        csv_df.to_csv(csv_path, index=False)
                                        st.success(f"Product '{selected_manage}' deleted from catalog (CSV fallback).")
                                        st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Failed to delete product: {e}")

        # ---------------- BULK APPLY DISCOUNTS ----------------
        st.markdown("---")
        st.subheader("Bulk Apply Discounts")

        candidates = low_df["product_name"].tolist()
        selected = st.multiselect("Select products to apply recommended discount", options=candidates)

        if selected:
            # Show preview
            preview = []
            for prod in selected:
                row = df[df["product_name"] == prod].iloc[0]
                stock = int(row.get("stock", 0))
                monthly = int(row.get("monthly_sales", 0))
                demand = "HIGH" if monthly > 150 else "MEDIUM"
                from backend.services.discount_service import recommend_discount, calculate_final_price, log_discount_change

                disc = recommend_discount(stock, demand)
                new_price = calculate_final_price(row.get("selling_price", row.get("selling_price", 0)), disc)
                preview.append({
                    "product_name": prod,
                    "current_discount": row.get("discount", 0),
                    "recommended_discount": disc,
                    "current_price": row.get("selling_price", 0),
                    "new_price": new_price
                })

            preview_df = pd.DataFrame(preview)
            st.table(preview_df)

            persist_bulk = st.checkbox("Persist discounts to CSV (make permanent)", value=False)
            user_name = st.text_input("User (for audit log)")

            if st.button("Apply discounts to selected"):
                try:
                    applied = []
                    if persist_bulk:
                        # Try DB updates first
                        try:
                            from backend.db import SessionLocal
                            from backend.models import Product
                            session = SessionLocal()
                            for item in preview:
                                prod_name = item["product_name"]
                                prod = session.query(Product).filter(Product.product_name == prod_name).one_or_none()
                                if prod is None:
                                    st.warning(f"Product not found in DB: {prod_name}")
                                    continue
                                old_disc = int(prod.discount or 0)
                                new_disc = int(item["recommended_discount"])
                                prod.discount = new_disc
                                prod.selling_price = item["new_price"]
                                session.add(prod)
                                # write audit
                                try:
                                    log_discount_change(prod_name, old_disc, new_disc, user=user_name)
                                except Exception:
                                    pass
                                applied.append(prod_name)
                            session.commit()
                            session.close()
                            st.success(f"Discounts persisted for: {', '.join(applied)}")
                            st.experimental_rerun()
                        except Exception:
                            # fallback to CSV path
                            csv_path = os.path.join(BACKEND_DIR, "data", "products.csv")
                            if not os.path.exists(csv_path):
                                st.error("Products CSV not found to persist discounts.")
                            else:
                                csv_df = pd.read_csv(csv_path)
                                applied = []
                                for item in preview:
                                    prod = item["product_name"]
                                    mask = csv_df["product_name"] == prod
                                    if not mask.any():
                                        st.warning(f"Product not found in CSV: {prod}")
                                        continue

                                    old_disc = int(csv_df.loc[mask, "discount"].iloc[0]) if "discount" in csv_df.columns else 0
                                    new_disc = int(item["recommended_discount"]) if persist_bulk else old_disc

                                    # If persisting, update discount and selling_price
                                    if persist_bulk:
                                        csv_df.loc[mask, "discount"] = new_disc
                                        csv_df.loc[mask, "selling_price"] = item["new_price"]
                                        # write audit
                                        log_discount_change(prod, old_disc, new_disc, user=user_name)
                                        applied.append(prod)

                                if persist_bulk:
                                    csv_df.to_csv(csv_path, index=False)
                                    st.success(f"Discounts persisted for: {', '.join(applied)}")
                                    st.experimental_rerun()
                                else:
                                    st.success("Discounts preview applied session-only.")
                    else:
                        st.success("Discounts preview applied session-only.")
                except Exception as e:
                    st.error(f"Failed to apply bulk discounts: {e}")
        else:
            st.info("Select one or more products to prepare bulk discount application.")

    # ---------------- AI STOCK FORECAST ----------------
    st.markdown("---")
    st.subheader("AI Stock Forecast")
    with st.expander("Run AI stock forecast and view category-wise pie chart", expanded=False):
        months = st.slider("Months ahead to predict", 1, 6, value=1)
        safety_pct = st.slider("Safety buffer (%)", 0, 100, value=20)
        target_cover = st.slider("Target cover months (0 = auto)", 0, 6, value=0)
        product_choices = st.multiselect("Products to plot (optional)", options=sorted(df["product_name"].dropna().unique().tolist()))
        run_forecast = st.button("Run Forecast")
        if run_forecast:
            try:
                results = []
                rows = []
                for _, r in df.iterrows():
                    info = inv_service.predict_stock_series(
                        safe_int(r.get("stock", 0)),
                        safe_int(r.get("monthly_sales", 0)),
                        months,
                        r.get("demand_level", "MEDIUM"),
                        safe_int(r.get("supplier_lead_time", 7)),
                        safety_stock_pct=(safety_pct / 100.0),
                        target_cover_months=(target_cover if target_cover > 0 else None)
                    )
                    series = info.get("series", [])

                    # recommended reorder (earliest if present)
                    recs = info.get("recommended_reorders", [])
                    if recs:
                        first = recs[0]
                        rec_qty = first.get("reorder_qty", 0)
                        eta_months = first.get("arrival_month")
                    else:
                        rec_qty = 0
                        eta_months = None

                    # pending deliveries summary
                    pending = info.get("pending_deliveries", {})
                    pending_summary = ", ".join([f"M{safe_int(k)}:{safe_int(v)}" for k, v in pending.items()]) if pending else ""

                    rows.append({
                        "product_name": r.get("product_name"),
                        "category": r.get("category"),
                        "stock": safe_int(r.get("stock", 0)),
                        "predicted_stock": safe_int(series[-1]) if series else safe_int(r.get("stock", 0)),
                        "stockout_months": safe_int(info.get("stockout_months", 0)),
                        "min_stock": safe_int(info.get("min_stock", 0)),
                        "series": series,
                        "recommended_reorder_qty": safe_int(rec_qty),
                        "reorder_eta_month": eta_months,
                        "pending_deliveries": pending_summary
                    })

                df_pred = pd.DataFrame(rows)
                st.subheader(f"Predicted stock after {months} month(s)")
                display_cols = ["product_name", "category", "stock", "predicted_stock", "recommended_reorder_qty", "reorder_eta_month", "stockout_months", "min_stock"]
                st.dataframe(df_pred[display_cols].sort_values("predicted_stock"), use_container_width=True)

                # Performance summary
                total = len(df_pred)
                at_risk = int((df_pred["stockout_months"] > 0).sum())
                pct_risk = round((at_risk / total) * 100, 1) if total else 0
                avg_change = round((df_pred["predicted_stock"].astype(float) - df_pred["stock"].astype(float)).mean(), 2)

                # simple confidence metric per product (lower stddev = higher confidence)
                def _conf(s):
                    s_arr = np.array(s)
                    mu = s_arr.mean() if s_arr.size else 0
                    std = s_arr.std() if s_arr.size else 0
                    var = std / (abs(mu) + 1e-6)
                    conf = int(max(30, min(100, 100 - var * 100)))
                    return conf

                df_pred["confidence"] = df_pred["series"].apply(_conf)
                avg_conf = int(df_pred["confidence"].mean()) if not df_pred.empty else 0

                c1, c2, c3 = st.columns(3)
                c1.metric("Products at risk (stockout months > 0)", f"{at_risk} ({pct_risk}%)")
                c2.metric("Avg predicted stock change", f"{avg_change:+}")
                c3.metric("Avg forecast confidence", f"{avg_conf}%")

                # Pie chart by category (non-negative totals)
                cat_df = df_pred.groupby("category", dropna=False)["predicted_stock"].sum().reset_index()
                cat_df["predicted_stock"] = cat_df["predicted_stock"].apply(lambda x: max(0, safe_int(x)))
                if cat_df["predicted_stock"].sum() == 0:
                    st.info("All predicted stocks are zero or negative (no stock expected).")
                else:
                    fig, ax = plt.subplots(figsize=(6, 6))
                    ax.pie(cat_df["predicted_stock"], labels=cat_df["category"].fillna("Unknown"), autopct="%1.1f%%", startangle=140, pctdistance=0.75, labeldistance=1.05, wedgeprops=dict(edgecolor='white'))
                    ax.set_title(f"Predicted Stock by Category (in {months} month(s))")
                    st.pyplot(fig)

                # Show per-product series charts for selected products
                if product_choices:
                    st.markdown("---")
                    st.subheader("Product forecast series")
                    plot_df = pd.DataFrame({})
                    for prod in product_choices:
                        prod_row = df_pred[df_pred["product_name"] == prod]
                        if not prod_row.empty:
                            series = prod_row.iloc[0]["series"]
                            plot_df[prod] = pd.Series(series)

                    if not plot_df.empty:
                        plot_df.index = [f"M{m+1}" for m in range(len(plot_df))]
                        st.line_chart(plot_df)

                        # Show small performance table for selected
                        perf_rows = []
                        for prod in product_choices:
                            prod_row = df_pred[df_pred["product_name"] == prod]
                            if not prod_row.empty:
                                pr = prod_row.iloc[0]
                                perf_rows.append({
                                    "product": prod,
                                    "stock": pr["stock"],
                                    "predicted": pr["predicted_stock"],
                                    "stockout_months": pr["stockout_months"],
                                    "min_stock": pr["min_stock"],
                                    "confidence%": pr["confidence"],
                                    "recommended_reorder_qty": pr["recommended_reorder_qty"],
                                    "reorder_eta_month": pr["reorder_eta_month"],
                                    "pending_deliveries": pr["pending_deliveries"]
                                })
                        st.table(pd.DataFrame(perf_rows).set_index("product"))

                # Reorder actions
                st.markdown("---")
                st.subheader("Reorder actions")
                sel = st.selectbox("Select product to place reorder", options=df_pred["product_name"].tolist()) if not df_pred.empty else None
                if sel:
                    row = df_pred[df_pred["product_name"] == sel].iloc[0]
                    st.write(f"Current stock: {row['stock']}, Recommended reorder: {row['recommended_reorder_qty']}, ETA (month index): {row['reorder_eta_month']}")
                    placed_by = st.text_input("Placed by (user)", value="system")
                    if st.button("Reorder now", key=f"reorder_now_{sel}"):
                        if int(row['recommended_reorder_qty']) <= 0:
                            st.warning("No recommended reorder quantity for this product.")
                        else:
                            success = inv_service.log_reorder(sel, int(row['recommended_reorder_qty']), int(row['reorder_eta_month']) if row['reorder_eta_month'] else None, placed_by=placed_by)
                            if success:
                                st.success(f"Reorder placed for {sel} (qty {row['recommended_reorder_qty']})")
                            else:
                                st.error("Failed to place reorder.")

                # Bulk place reorders for at-risk products
                if st.button("Place reorders for all recommended", key="place_reorders_all"):
                    placed = 0
                    for _, pr in df_pred.iterrows():
                        if int(pr['recommended_reorder_qty']) > 0:
                            ok = inv_service.log_reorder(pr['product_name'], int(pr['recommended_reorder_qty']), int(pr['reorder_eta_month']) if pr['reorder_eta_month'] else None, placed_by="bulk")
                            if ok:
                                placed += 1
                    st.success(f"Placed {placed} reorder(s).")

                # Show recent reorders log (DB preferred)
                try:
                    from backend.db import SessionLocal
                    from backend.models import Reorder
                    session = SessionLocal()
                    rows = session.query(Reorder).order_by(Reorder.created_at.desc()).limit(10).all()
                    session.close()
                    if rows:
                        re_df = pd.DataFrame([{
                            "id": r.id,
                            "product": r.product,
                            "quantity": r.quantity,
                            "eta_month": r.eta_month,
                            "placed_by": r.placed_by,
                            "created_at": r.created_at.isoformat() if r.created_at else ""
                        } for r in rows])
                        st.markdown("---")
                        st.subheader("Recent reorders")
                        st.table(re_df)
                    else:
                        st.info("No reorders logged yet.")
                except Exception:
                    try:
                        reorders_path = os.path.join(BACKEND_DIR, "data", "reorders.csv")
                        if os.path.exists(reorders_path):
                            re_df = pd.read_csv(reorders_path)
                            st.markdown("---")
                            st.subheader("Recent reorders")
                            st.table(re_df.tail(10))
                        else:
                            st.info("No reorders logged yet.")
                    except Exception:
                        st.warning("Unable to load reorders log.")

                # Download CSV
                csv_buf = df_pred[["product_name", "category", "stock", "predicted_stock", "recommended_reorder_qty", "reorder_eta_month", "stockout_months", "min_stock", "confidence"]].to_csv(index=False)
                st.download_button("Download forecast CSV", data=csv_buf, file_name=f"stock_forecast_{months}m.csv", mime="text/csv")

            except Exception as e:
                st.error(f"Failed to run forecast: {e}")

# ---------------- STOCKOUTS & LOST SALES PAGE ----------------
elif menu == "Stockouts & Lost Sales":
    st.markdown("## Inventory Stockouts & Lost Sales Analysis")

    # Date range selector (approx months for forecasting)
    today = datetime.date.today()
    default_start = today - datetime.timedelta(days=90)
    dr = st.date_input("Data range (approx)", value=(default_start, today))
    if isinstance(dr, (list, tuple)):
        start_date = dr[0] if len(dr) > 0 else default_start
        end_date = dr[1] if len(dr) > 1 else start_date
    else:
        start_date, end_date = dr, dr if dr else (default_start, today)
    days = max(1, (end_date - start_date).days)
    months = max(1, int(np.ceil(days / 30.0)))

    # Filters
    categories = ["All"] + sorted(df["category"].dropna().unique().tolist())
    cat = st.selectbox("Category", categories)
    product_options = ["All"] + sorted(df[df["category"] == cat]["product_name"].dropna().unique().tolist()) if cat != "All" else ["All"] + sorted(df["product_name"].dropna().unique().tolist())
    selected = st.selectbox("Product", product_options)
    channel = st.selectbox("Channel", ["All", "Online", "Store"])

    st.markdown("---")

    # Compute lost sales per product via monthly simulation
    rows = []
    for _, r in df.iterrows():
        if cat != "All" and r.get("category") != cat:
            continue
        if selected != "All" and r.get("product_name") != selected:
            continue

        price = float(r.get("selling_price") or 0.0)
        monthly = float(r.get("monthly_sales") or 0.0)
        stock = safe_int(r.get("stock"))
        lead = safe_int(r.get("supplier_lead_time"))
        demand = r.get("demand_level") or "MEDIUM"

        info = inv_service.predict_stock_series(stock, monthly, months, demand, lead, safety_stock_pct=0.2)
        series = info.get("series", [])
        lost_units = sum([abs(x) for x in series if x < 0])
        lost_revenue = lost_units * price
        stockout_months = info.get("stockout_months", 0)
        recs = info.get("recommended_reorders", [])
        first_reorder = recs[0]["reorder_qty"] if recs else 0

        # derive reason for accountability
        if lead and lead > 14:
            reason = "Supplier Delay"
        elif monthly > df["monthly_sales"].quantile(0.75):
            reason = "High Demand"
        elif lost_units > 0:
            reason = "Stockout"
        else:
            reason = "None"

        rows.append({
            "product_id": r.get("product_id"),
            "product_name": r.get("product_name"),
            "category": r.get("category"),
            "stock": stock,
            "monthly_sales": monthly,
            "lost_units": int(lost_units),
            "lost_revenue": float(lost_revenue),
            "stockout_months": int(stockout_months),
            "predicted_stock": int(series[-1]) if series else stock,
            "recommended_reorder": int(first_reorder),
            "reason": reason
        })

    res_df = pd.DataFrame(rows)

    total_products = len(res_df)
    total_lost_sales = res_df["lost_revenue"].sum() if not res_df.empty else 0.0
    pct_stockouts = round((res_df[res_df["lost_units"] > 0].shape[0] / max(1, total_products)) * 100, 1) if total_products else 0

    # Top KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("% of Stock Outs", f"{pct_stockouts}%")
    c2.metric("Amount of Lost Sales", f"₹{total_lost_sales:,.0f}")
    c3.metric("Products analysed", f"{total_products}")

    st.markdown("---")

    # Lost Sales Accountability
    if not res_df.empty:
        acct = res_df[res_df["reason"] != "None"].groupby(["reason","category"]).agg(
            stock_outs=("lost_units","count"),
            lost_revenue=("lost_revenue","sum")
        ).reset_index()
        acct_total = acct["lost_revenue"].sum() if not acct.empty else 0
        acct["%StockOut"] = ((acct["stock_outs"] / max(1, total_products)) * 100).round(1)
        acct["%LostSales"] = ((acct["lost_revenue"] / max(1, acct_total)) * 100).round(1) if acct_total else 0

        # Lost Sales Accountability - Professional HTML Table
        acct_display = acct.rename(columns={"reason":"Reason","category":"Department","stock_outs":"#Stock Outs","lost_revenue":"Total Sales Lost","%StockOut":"%Stock Out","%LostSales":"%Lost Sales"})
        acct_display["Total Sales Lost"] = acct_display["Total Sales Lost"].apply(lambda x: f"₹{x:,.0f}")
        
        acct_html = '<div style="margin: 32px 0; padding: 28px; background: var(--card-bg); border-radius: 14px; box-shadow: 0 4px 16px var(--kpi-shadow); border: 1px solid var(--border-color); overflow-x: auto;">' 
        acct_html += '<h4 style="margin: 0 0 20px 0; color: var(--text-main); font-weight: 700; font-size: 18px; font-family: \'Times New Roman\', Times, serif;">Lost Sales Accountability</h4>'
        acct_html += '<table style="width: 100%; border-collapse: collapse; font-family: \'Times New Roman\', Times, serif;">'
        acct_html += '<tr style="background: var(--input-bg); border-bottom: 2px solid var(--border-color);">'
        for col in acct_display.columns:
            acct_html += f'<th style="padding: 18px 20px; text-align: left; font-weight: 700; color: var(--text-muted); font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">{col}</th>'
        acct_html += '</tr>'
        for idx, row in acct_display.iterrows():
            acct_html += '<tr style="border-bottom: 1px solid var(--border-color); transition: background-color 0.2s;">'
            for col in acct_display.columns:
                value = row[col]
                align = 'right' if col in ['#Stock Outs', 'Total Sales Lost', '%Stock Out', '%Lost Sales'] else 'left'
                acct_html += f'<td style="padding: 16px 20px; text-align: {align}; color: var(--text-main); font-size: 15px;">{value}</td>'
            acct_html += '</tr>'
        acct_html += '</table></div>'
        st.markdown(acct_html, unsafe_allow_html=True)

    # Trend chart: lost sales (bar) and stockout % (line)
    months_range = list(range(1, months+1))
    monthly_lost = []
    monthly_pct = []
    for m in range(months):
        lost_m = 0.0
        cnt = 0
        for _, r in df.iterrows():
            if cat != "All" and r.get("category") != cat:
                continue
            if selected != "All" and r.get("product_name") != selected:
                continue
            info = inv_service.predict_stock_series(
                safe_int(r.get("stock")),
                float(r.get("monthly_sales") or 0),
                m+1,
                r.get("demand_level") or "MEDIUM",
                safe_int(r.get("supplier_lead_time")),
            )
            s = info.get("series", [])
            if not s:
                continue
            if s[m] < 0:
                lost_m += abs(s[m]) * float(r.get("selling_price") or 0)
                cnt += 1
        monthly_lost.append(lost_m)
        monthly_pct.append((cnt / max(1, total_products)) * 100 if total_products else 0)

    if any(monthly_lost) or any(monthly_pct):
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[f"M-{m+1}" for m in range(months)], y=monthly_lost, name="Lost Sales", marker_color='indigo'))
        fig.add_trace(go.Line(x=[f"M-{m+1}" for m in range(months)], y=monthly_pct, name="Stock Out%", yaxis='y2', marker_color='tomato'))
        fig.update_layout(yaxis2=dict(overlaying='y', side='right', range=[0,100]), legend=dict(orientation='h', y=-0.2))
        st.subheader("Lost Sales and Stock-out Trends")
        st.plotly_chart(fig, use_container_width=True)

    # Category-wise Lost Sales Summary - Professional HTML Table
    if not res_df.empty:
        cat_summary = res_df.groupby("category").agg(
            products=("product_id","nunique"),
            lost_sales=("lost_revenue","sum"),
            stock_outs=("lost_units","sum")
        ).reset_index()
        cat_summary["lost_sales_pct"] = ((cat_summary["lost_sales"] / cat_summary["lost_sales"].sum()) * 100).round(1)
        cat_summary["lost_sales"] = cat_summary["lost_sales"].apply(lambda x: f"₹{x:,.0f}")
        cat_summary["lost_sales_pct"] = cat_summary["lost_sales_pct"].apply(lambda x: f"{x:.1f}%")
        
        cat_display = cat_summary.rename(columns={
            "category": "Product Category",
            "products": "Total Products",
            "lost_sales": "Lost Sales",
            "stock_outs": "Stock Outs",
            "lost_sales_pct": "% Lost Sales"
        })
        
        cat_html = '<div style="margin: 32px 0; padding: 28px; background: var(--card-bg); border-radius: 14px; box-shadow: 0 4px 16px var(--kpi-shadow); border: 1px solid var(--border-color); overflow-x: auto;">'
        cat_html += '<h4 style="margin: 0 0 20px 0; color: var(--text-main); font-weight: 700; font-size: 18px; font-family: \'Times New Roman\', Times, serif;">Category-wise Lost Sales Summary</h4>'
        cat_html += '<table style="width: 100%; border-collapse: collapse; font-family: \'Times New Roman\', Times, serif;">'
        cat_html += '<tr style="background: var(--input-bg); border-bottom: 2px solid var(--border-color);">'
        for col in cat_display.columns:
            cat_html += f'<th style="padding: 18px 20px; text-align: left; font-weight: 700; color: var(--text-muted); font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">{col}</th>'
        cat_html += '</tr>'
        for idx, row in cat_display.iterrows():
            cat_html += '<tr style="border-bottom: 1px solid var(--border-color); transition: background-color 0.2s;">'
            for col in cat_display.columns:
                value = row[col]
                align = 'right' if col in ['Total Products', 'Lost Sales', 'Stock Outs', '% Lost Sales'] else 'left'
                cat_html += f'<td style="padding: 16px 20px; text-align: {align}; color: var(--text-main); font-size: 15px;">{value}</td>'
            cat_html += '</tr>'
        cat_html += '</table></div>'
        st.markdown(cat_html, unsafe_allow_html=True)

    # Stock Out Details - Professional HTML Table
    if not res_df.empty and res_df[res_df["lost_units"]>0].shape[0] > 0:
        details = res_df[res_df["lost_units"]>0].copy()
        details["avg_daily_sales"] = (details["monthly_sales"] / 30).astype(int)
        details["days_since_stockout_estimated"] = (details["stockout_months"] * 30).astype(int)
        
        details_display = details[["category","product_id","product_name","days_since_stockout_estimated","avg_daily_sales","predicted_stock","recommended_reorder","lost_units","lost_revenue" ]].sort_values("lost_revenue", ascending=False).copy()
        details_display = details_display.rename(columns={
            "category": "Category",
            "product_id": "Product ID",
            "product_name": "Product Name",
            "days_since_stockout_estimated": "Days Stockout",
            "avg_daily_sales": "Avg Daily Sales",
            "predicted_stock": "Predicted Stock",
            "recommended_reorder": "Rec. Reorder",
            "lost_units": "Lost Units",
            "lost_revenue": "Lost Revenue"
        })
        details_display["Lost Revenue"] = details_display["Lost Revenue"].apply(lambda x: f"₹{x:,.0f}")
        
        details_html = '<div style="margin: 32px 0; padding: 28px; background: var(--card-bg); border-radius: 14px; box-shadow: 0 4px 16px var(--kpi-shadow); border: 1px solid var(--border-color); overflow-x: auto; overflow-y: auto; max-height: 420px;">'
        details_html += '<h4 style="margin: 0 0 20px 0; color: var(--text-main); font-weight: 700; font-size: 18px; font-family: \'Times New Roman\', Times, serif;">Stock Out Details</h4>'
        details_html += '<table style="width: 100%; border-collapse: collapse; font-family: \'Times New Roman\', Times, serif;">'
        details_html += '<tr style="background: var(--input-bg); border-bottom: 2px solid var(--border-color);">'
        for col in details_display.columns:
            details_html += f'<th style="padding: 18px 20px; text-align: left; font-weight: 700; color: var(--text-muted); font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">{col}</th>'
        details_html += '</tr>'
        for idx, row in details_display.iterrows():
            details_html += '<tr style="border-bottom: 1px solid var(--border-color); transition: background-color 0.2s;">'
            for col in details_display.columns:
                value = row[col]
                align = 'right' if col in ['Product ID', 'Days Stockout', 'Avg Daily Sales', 'Predicted Stock', 'Rec. Reorder', 'Lost Units', 'Lost Revenue'] else 'left'
                details_html += f'<td style="padding: 16px 20px; text-align: {align}; color: var(--text-main); font-size: 15px;">{value}</td>'
            details_html += '</tr>'
        details_html += '</table></div>'
        st.markdown(details_html, unsafe_allow_html=True)

        # Download
        csv_buf = details.to_csv(index=False)
        st.download_button("Download stockout details CSV", data=csv_buf, file_name=f"stockout_details_{start_date}_{end_date}.csv", mime="text/csv")
    else:
        st.info("No stock out events detected for the selected filters and date range.")


# ---------------- AI DECISION SUPPORT PAGE ----------------
elif menu == "AI Decision Support":
    st.markdown("## AI Decision Support — Demand Forecast Lab")

    # selectors
    cat_options = ["All"] + sorted(df["category"].dropna().unique().tolist())
    cat_choice = st.selectbox("Category (for analysis)", cat_options)
    
    df_ai = df.copy()
    if cat_choice != "All":
        df_ai = df_ai[df_ai["category"] == cat_choice]

    products_options = ["All"] + sorted(df_ai["product_name"].dropna().unique().tolist())
    prod_choice = st.selectbox("Product (for analysis)", products_options)
    months_history = st.slider("History months (for model training)", 6, 36, 24)
    forecast_horizon = st.slider("Forecast horizon (months)", 1, 6, 3)

    st.markdown("---")

    # Helper: build sales series (DB SalesHistory preferred, fallback synthetic)
    def get_sales_series(product, months_history=24):
        import numpy as _np
        try:
            from backend.db import SessionLocal
            from backend.models import SalesHistory
            session = SessionLocal()
            rows = session.query(SalesHistory).filter(SalesHistory.product_name == product).order_by(SalesHistory.date.asc()).all()
            session.close()
            if rows:
                s = pd.DataFrame([{"date": r.date, "sales": r.sales} for r in rows])
                s["date"] = pd.to_datetime(s["date"]).dt.to_period('M').dt.to_timestamp()
                s = s.set_index("date").resample('M').sum().sales
                s = s.sort_index()
                if len(s) < months_history:
                    pad_len = months_history - len(s)
                    pad = pd.Series([s.mean() if not s.empty else 0] * pad_len, index=pd.date_range(end=s.index.min() - pd.offsets.MonthBegin(1), periods=pad_len, freq='M'))
                    s = pd.concat([pad, s])
                return s.tail(months_history)
        except Exception:
            pass

        # fallback: synthetic series based on current monthly_sales
        base_row = df[df['product_name'] == product]
        if base_row.empty:
            base = 0.0
        else:
            base = float(base_row.iloc[0].get('monthly_sales', 0) or 0.0)
        idx = pd.date_range(end=pd.Timestamp.today(), periods=months_history, freq='M')
        seasonal = (np.sin(np.linspace(0, 2*np.pi, months_history)) * (base * 0.12))
        noise = np.random.normal(0, max(1.0, base * 0.06), months_history)
        series = np.clip(base + seasonal + noise, a_min=0, a_max=None)
        return pd.Series(series, index=idx)

    # Model comparison utility
    def compare_models(series, horizon):
        results = {}
        y = series.values.astype(float)
        n = len(y)
        # train/test split: holdout last `horizon` points when possible
        h = min(horizon, max(1, n // 6))
        train, test = y[:-h], y[-h:]
        X_train = np.arange(len(train)).reshape(-1, 1)

        # 1) Linear regression on trend
        try:
            from sklearn.linear_model import LinearRegression
            lr = LinearRegression()
            lr.fit(X_train, train)
            X_fore = np.arange(len(train), len(train) + h).reshape(-1, 1)
            pred_lr = lr.predict(X_fore)
            pred_full_lr = np.concatenate([train, pred_lr])
            results['Linear Regression'] = {'pred': np.round(pred_full_lr,2), 'h_pred': pred_lr}
        except Exception:
            results['Linear Regression'] = None

        # 2) Trend model (ExponentialSmoothing) if available
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            model = ExponentialSmoothing(train, trend='add', seasonal=None)
            fit = model.fit(optimized=True)
            h_pred = fit.forecast(h)
            pred_full = np.concatenate([train, h_pred])
            results['Trend (ExpSmoothing)'] = {'pred': np.round(pred_full,2), 'h_pred': h_pred}
        except Exception:
            # fallback to simple moving average forecast
            ma = np.mean(train[-3:]) if len(train) >=3 else np.mean(train)
            h_pred = np.array([ma]*h)
            results['Trend (MA)'] = {'pred': np.round(np.concatenate([train, h_pred]),2), 'h_pred': h_pred}

        # 3) Random Forest (optional)
        try:
            from sklearn.ensemble import RandomForestRegressor
            # prepare lag features
            def make_lags(arr, lags=3):
                X, yv = [], []
                for i in range(lags, len(arr)):
                    X.append(arr[i-lags:i])
                    yv.append(arr[i])
                return np.array(X), np.array(yv)
            lags = 3
            Xf, yf = make_lags(train, lags=lags)
            if len(yf) > 5:
                rf = RandomForestRegressor(n_estimators=100, random_state=0)
                rf.fit(Xf, yf)
                # iterative forecast
                last = train[-lags:].tolist()
                h_pred = []
                for _ in range(h):
                    p = rf.predict(np.array(last).reshape(1, -1))[0]
                    h_pred.append(p)
                    last = last[1:] + [p]
                results['Random Forest'] = {'pred': np.round(np.concatenate([train, h_pred]),2), 'h_pred': np.array(h_pred)}
            else:
                results['Random Forest'] = None
        except Exception:
            results['Random Forest'] = None

        # Evaluate models where test exists
        evals = {}
        for name, res in results.items():
            if res is None:
                continue
            pred_h = np.array(res['h_pred']).astype(float)
            # map to test size
            if len(test) == 0:
                mape = None
                rmse = None
                acc = None
            else:
                try:
                    # Prefer sklearn if available
                    from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
                    mape = mean_absolute_percentage_error(test, pred_h)
                    rmse = mean_squared_error(test, pred_h, squared=False)
                    acc = max(0, 100 - (mape * 100))
                except Exception:
                    # Fallback numeric implementations using numpy (keeps numbers rather than blanks)
                    try:
                        import numpy as _np
                        test_a = _np.array(test, dtype=float)
                        pred_a = _np.array(pred_h, dtype=float)
                        # avoid division by zero for MAPE
                        denom = _np.where(test_a == 0, 1e-9, test_a)
                        mape = _np.mean(_np.abs((test_a - pred_a) / denom))
                        rmse = _np.sqrt(_np.mean((test_a - pred_a)**2))
                        acc = max(0, 100 - (float(mape) * 100))
                    except Exception:
                        mape = None
                        rmse = None
                        acc = None
            evals[name] = {'mape': mape, 'rmse': rmse, 'accuracy_pct': acc}

        # choose best by accuracy_pct
        best = None
        best_score = -1
        for name, e in evals.items():
            if e.get('accuracy_pct') is not None and e.get('accuracy_pct') > best_score:
                best = name
                best_score = e.get('accuracy_pct')

        return results, evals, best

    # Run models for selected product
    if prod_choice == 'All':
        st.info('Select a specific product to run model comparison and simulations.')
    else:
        series = get_sales_series(prod_choice, months_history)
        st.subheader(f"Sales series for {prod_choice} (last {months_history} months)")
        st.line_chart(series)

        # Prepare product row and key variables for downstream widgets
        try:
            prod_row = df[df['product_name'] == prod_choice].iloc[0].to_dict()
            price = float(prod_row.get('selling_price') or 0)
            cost = float(prod_row.get('cost_price') or 0)
            monthly = float(prod_row.get('monthly_sales') or 0)
            stock = int(prod_row.get('stock') or 0)
        except Exception:
            prod_row = None
            price = 0.0
            cost = 0.0
            monthly = 0.0
            stock = 0

        # Compare models
        models_res, models_eval, best_model = compare_models(series, forecast_horizon)

        # Plot forecast vs actual
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=series.index, y=series.values, name='Actual', mode='lines+markers'))
        # overlay model forecasts
        colors = {'Linear Regression':'blue', 'Trend (ExpSmoothing)':'green', 'Trend (MA)':'green', 'Random Forest':'purple'}
        for name, res in models_res.items():
            if not res:
                continue
            pred = res['pred']
            # construct index
            idx = pd.date_range(end=series.index[-1] + pd.offsets.MonthBegin(len(pred)-1), periods=len(pred), freq='M')
            fig.add_trace(go.Scatter(x=idx, y=pred, name=f'{name} (pred)', line=dict(dash='dash'), marker=dict(color=colors.get(name,'gray'))))
        fig.update_layout(title='Forecast vs Actual', xaxis_title='Month', yaxis_title='Units', legend=dict(orientation='h'))
        st.plotly_chart(fig, use_container_width=True)

        # Show evaluation table and Best model badge
        eval_table = []
        for name, e in models_eval.items():
            mape_v = f"{e['mape']*100:.1f}%" if e['mape'] is not None else "N/A"
            rmse_v = f"{e['rmse']:.2f}" if e['rmse'] is not None else "N/A"
            acc_v = f"{e['accuracy_pct']:.1f}%" if e['accuracy_pct'] is not None else "N/A"
            sort_val = e['accuracy_pct'] if e['accuracy_pct'] is not None else -1
            eval_table.append({'Model': name, 'MAPE': mape_v, 'RMSE': rmse_v, 'Accuracy': acc_v, '_sort': sort_val})
            
        eval_df = pd.DataFrame(eval_table).sort_values(by=['_sort'], ascending=False).drop(columns=['_sort'])
        st.subheader('Model evaluation')
        st.table(eval_df.set_index('Model'))
        if best_model:
            best_acc = models_eval[best_model].get('accuracy_pct')
            best_acc_str = f"{round(best_acc,1)}%" if best_acc is not None else 'N/A'
            st.success(f"🏆 Best model: {best_model} (accuracy: {best_acc_str})")

        # Explain why this is strong AI
        st.markdown('**Why this is strong AI** — We compare multiple models and show evaluation metrics (MAPE/RMSE) rather than only exposing a single prediction. This supports robust model selection and explainability for business decisions.')

        st.markdown('---')

        # 2. AI Recommendation Engine (rules)
        st.subheader('AI Recommendation Engine — Smart Actions')

        # Allow generating suggestions for single product or for catalog
        st.markdown('Select a product and click **Get Recommendations** or run across the catalog.')
        rec_cols = st.columns([2,1])
        with rec_cols[0]:
            run_single = st.button('Get recommendations for product', key='get_reco_single')
        with rec_cols[1]:
            run_all = st.button('Run recommendations for all products', key='get_reco_all')

        recommendations_df = pd.DataFrame(columns=['product','situation','suggestion','confidence','reason'])

        if run_single:
            try:
                if prod_choice and prod_choice != 'All':
                    row = df[df['product_name']==prod_choice].iloc[0].to_dict()
                    # annotate with quartile thresholds for scoring
                    row['_q25'] = df['monthly_sales'].quantile(0.25)
                    row['_q66'] = df['monthly_sales'].quantile(0.66)
                    row['_q75'] = df['monthly_sales'].quantile(0.75)
                    recs = ai_service.generate_recommendations(row)
                    if recs and len(recs) > 0:
                        recommendations_df = pd.DataFrame(recs)
                        st.success(f'Generated {len(recs)} recommendation(s) for {prod_choice}')
                    else:
                        st.info(f'No immediate AI recommendations for {prod_choice}.')
                else:
                    st.warning('Please select a specific product first.')
            except Exception as e:
                st.error(f'Failed to generate recommendations: {str(e)}')

        if run_all:
            try:
                recommendations_df = ai_service.bulk_recommendations(df)
                if not recommendations_df.empty:
                    st.success(f'Generated recommendations for catalog ({len(recommendations_df)} item(s))')
                else:
                    st.info('No recommendations found across catalog.')
            except Exception as e:
                st.error(f'Failed to generate bulk recommendations: {str(e)}')

        # Render table and action buttons
        if not recommendations_df.empty:
            st.write('**Recommendations Generated:**')
            st.dataframe(recommendations_df[['product','situation','suggestion','confidence','reason']].reset_index(drop=True), use_container_width=True)

            # Action area: allow applying per-row or bulk
            st.markdown('**Actions**')
            cols = st.columns([2,1])
            with cols[0]:
                apply_all = st.button('Apply all recommendations', key='apply_all_reco')

            # Per-row apply
            for i, row in recommendations_df.reset_index(drop=True).iterrows():
                pw = st.columns([3,1])
                with pw[0]:
                    st.write(f"{row['product']} — {row['situation']} → **{row['suggestion']}** (conf {row['confidence']*100:.0f}%)")
                with pw[1]:
                    if st.button('Apply', key=f"apply_{i}_{row['product']}"):
                        try:
                            res = ai_service.apply_action(row['product'], row['suggestion'], params={})
                            if res.get('ok'):
                                st.success(res.get('message'))
                            else:
                                st.error(res.get('message'))
                        except Exception as e:
                            st.error(f'Action failed: {e}')

            if apply_all:
                applied = []
                failed = []
                for _, r in recommendations_df.iterrows():
                    try:
                        res = ai_service.apply_action(r['product'], r['suggestion'], params={})
                        if res.get('ok'):
                            applied.append(f"{r['product']}:{r['suggestion']}")
                        else:
                            failed.append({"product": r['product'], "error": res.get('message')})
                    except Exception as e:
                        failed.append({"product": r['product'], "error": str(e)})

                st.success(f"Applied for: {', '.join(applied)}")
                if failed:
                    st.error(f"Failed for: {failed}")
        else:
            st.info('No recommendations to show. Click "Get recommendations for product" or "Run recommendations for all products" to begin.')

        st.markdown('---')

        # 3. AI Risk Prediction Panel
        st.subheader('AI Risk Prediction')
        # Predict stock-out in next 30 days and overstock in next 60 days using ai_service
        try:
            if prod_choice and prod_choice != 'All':
                row = df_ai[df_ai['product_name']==prod_choice].iloc[0].to_dict()
                risk = ai_service.predict_risk(row, window_days_stockout=30, window_days_overstock=60)
            else:
                st.caption(f'Aggregated Risk Prediction for all products in Category: {cat_choice}')
                if not df_ai.empty:
                    agg_stock = 0.0
                    agg_over = 0.0
                    agg_score = 0
                    
                    sample_df = df_ai if len(df_ai) <= 100 else df_ai.sample(100)
                    for _, r in sample_df.iterrows():
                        res = ai_service.predict_risk(r.to_dict(), window_days_stockout=30, window_days_overstock=60)
                        agg_stock += res.get('stockout_prob', 0)
                        agg_over += res.get('overstock_prob', 0)
                        agg_score += res.get('risk_score', 0)
                        
                    n = len(sample_df)
                    score = int(agg_score / n)
                    label = 'Safe' if score < 30 else ('Warning' if score < 65 else 'Critical')
                    risk = {
                        'stockout_prob': agg_stock / n,
                        'overstock_prob': agg_over / n,
                        'risk_score': score,
                        'label': label,
                        'details': {'reason': f'Aggregated average over {n} products.'}
                    }
                else:
                    risk = {'stockout_prob': 0.0, 'overstock_prob': 0.0, 'risk_score': 0, 'label': 'Safe', 'details': {}}
        except Exception as e:
            st.warning(f'Risk prediction unavailable: {e}')
            risk = {'stockout_prob': 0.0, 'overstock_prob': 0.0, 'risk_score': 0, 'label': 'Safe', 'details': {}}

        # Display KPIs and color badge
        rscore = risk.get('risk_score', 0)
        rlabel = risk.get('label', 'Safe')
        stockout_pct = int(risk.get('stockout_prob', 0.0) * 100)
        overstock_pct = int(risk.get('overstock_prob', 0.0) * 100)

        # color mapping for small visual badge
        if rlabel == 'Safe':
            badge = "🟢 Safe"
        elif rlabel == 'Warning':
            badge = "🟡 Warning"
        else:
            badge = "🔴 Critical"

        c1, c2, c3 = st.columns(3)
        c1.metric('Risk Score', f'{rscore} / 100', delta=badge)
        c2.metric('Stock-out (30d)', f'{stockout_pct}%')
        c3.metric('Overstock (60d)', f'{overstock_pct}%')

        # Expandable details with better formatting
        with st.expander('Risk details (diagnostics)', expanded=False):
            details = risk.get('details', {})
            if details:
                cols = st.columns(2)
                with cols[0]:
                    st.write("**Stock Analysis:**")
                    st.write(f"- Current Stock: {details.get('predicted_stock_stockout_window', 'N/A')} units")
                    st.write(f"- Stock Ratio: {details.get('stock_ratio', 'N/A')}x monthly sales")
                    st.write(f"- Demand Level: {details.get('demand_level', 'N/A')}")
                with cols[1]:
                    st.write("**Supply Chain:**")
                    st.write(f"- Supplier Lead Time: {details.get('supplier_lead_time_days', 'N/A')} days")
                    st.write(f"- Stockout Months: {details.get('stockout_months', 0)}/{details.get('sim_months_stockout', 0)}")
                    st.write(f"- Overstock Months: {details.get('over_months', 0)}/{details.get('sim_months_overstock', 0)}")
                
                if details.get('heuristic_risk_factor', 0) > 0:
                    st.write(f"**Heuristic Risk Factor:** {details.get('heuristic_risk_factor', 0)}")
                
                if details.get('error'):
                    st.warning(f"Error: {details.get('error')}")
            else:
                st.json(risk)

        # Catalog view: show risk for all products with color-coded labels and download
        if st.button('Compute risk for catalog'):
            try:
                all_rows = []
                for _, p in df.iterrows():
                    rr = ai_service.predict_risk(p.to_dict(), window_days_stockout=30, window_days_overstock=60)
                    all_rows.append({
                        'product': p.get('product_name'),
                        'category': p.get('category'),
                        'risk_score': rr.get('risk_score', 0),
                        'label': rr.get('label'),
                        'stockout_prob': rr.get('stockout_prob'),
                        'overstock_prob': rr.get('overstock_prob')
                    })
                risk_df = pd.DataFrame(all_rows).sort_values('risk_score', ascending=False)
                # color badge column
                risk_df['badge'] = risk_df['label'].map({'Safe':'🟢','Warning':'🟡','Critical':'🔴'})
                st.subheader('Catalog risk summary')
                st.dataframe(risk_df[['product','category','risk_score','label','stockout_prob','overstock_prob']].reset_index(drop=True), use_container_width=True)
                csv_buf = risk_df.to_csv(index=False)
                st.download_button('Download risk CSV', data=csv_buf, file_name='product_risk.csv', mime='text/csv')
            except Exception as e:
                st.error(f'Failed to compute catalog risk: {e}')
        st.markdown('---')

        # 4. AI Profit Simulator (What-if)
        with st.expander('AI Profit Simulator (What-if)', expanded=True):
            # Ensure product-level values are available
            try:
                prod_row = df[df['product_name']==prod_choice].iloc[0]
                price = float(prod_row.get('selling_price') or 0)
                cost = float(prod_row.get('cost_price') or 0)
                monthly = float(prod_row.get('monthly_sales') or 0)
            except Exception:
                prod_row = None
                price = 0.0
                cost = 0.0
                monthly = 0.0

            if prod_row is None or (price == 0 and monthly == 0):
                st.info('Select a specific product with sales data to use the Profit Simulator.')
            else:
                disc = st.slider('Discount (%)', 0, 50, 10)
                price_change = st.slider('Price change (%)', -50, 50, 0)
                # simple elasticity assumptions
                cls = 'Impulse' if (price < 2000 and monthly > 50) else ('Value' if price < 20000 else 'Premium')
                elasticity = -1.8 if cls == 'Impulse' else (-1.2 if cls == 'Value' else -0.8)
                # apply discount and price change
                new_price = price * (1 - disc/100.0) * (1 + price_change/100.0)
                # guard division by zero
                if price == 0:
                    demand_delta_pct = 0
                else:
                    demand_delta_pct = -elasticity * ((new_price - price) / price) * 100
                demand_factor = 1 + (demand_delta_pct/100.0)
                new_units = max(0, monthly * demand_factor)
                new_revenue = new_price * new_units
                new_profit = (new_price - cost) * new_units
                cols = st.columns(3)
                cols[0].metric('New revenue', f'₹{new_revenue:,.0f}')
                cols[1].metric('New profit', f'₹{new_profit:,.0f}')
                cols[2].metric('Demand change', f'{(demand_factor-1)*100:+.1f}%')

        st.markdown('---')

        # 5. AI Customer Behavior Analysis
        st.subheader('AI Customer Behavior (simulated)')
        if prod_row is None:
            st.info('Select a product to see customer behaviour classification')
        else:
            if price < 2000 and monthly > 100:
                cust_type = 'Impulse buy'
            elif price < 20000 and monthly >= 30 and prod_row.get('rating',0) >= 4:
                cust_type = 'Value buy'
            else:
                cust_type = 'Premium buy'
            st.info(f'Classified as: {cust_type}')

        st.markdown('---')

        # 6. AI Alert Intelligence
        st.subheader('AI Alerts')
        alerts = []
        # Use computed risk values
        if rlabel == 'Critical':
            alerts.append(f'⚠ AI predicts that {prod_choice} may face stock-out risk in {forecast_horizon*30} days (risk score {rscore}).')
        if overstock_pct > 75:
            alerts.append(f'⚠ AI predicts overstock risk for {prod_choice} based on inventory and demand.')
        if alerts:
            for a in alerts:
                st.warning(a)
        else:
            st.success('No immediate AI alerts.')

        st.markdown('---')

        # 7. AI Insight Generator (text-based)
        st.subheader('AI Insight Generator')
        insights = []

        # Attempt to compute category month-over-month sales change using SalesHistory if available
        try:
            from backend.models import SalesHistory
            from backend.db import SessionLocal
            session = SessionLocal()
            # aggregate by month and category
            rows = session.query(SalesHistory).all()
            session.close()
            if rows:
                sh = pd.DataFrame([{"date": r.date, "product_name": r.product_name, "sales": r.sales} for r in rows])
                sh["date"] = pd.to_datetime(sh["date"]).dt.to_period('M').dt.to_timestamp()
                # join category from df
                prod_cat = df.set_index('product_name')['category'].to_dict()
                sh['category'] = sh['product_name'].map(prod_cat)
                cat_month = sh.groupby(['category','date'])['sales'].sum().reset_index()
                latest_month = cat_month['date'].max()
                prev_month = latest_month - pd.offsets.MonthBegin(1)

                cat_latest = cat_month[cat_month['date']==latest_month].set_index('category')['sales']
                cat_prev = cat_month[cat_month['date']==prev_month].set_index('category')['sales']
                for c in sorted(df['category'].dropna().unique()):
                    v_latest = float(cat_latest.get(c, 0.0))
                    v_prev = float(cat_prev.get(c, 0.0))
                    if v_prev == 0 and v_latest == 0:
                        continue
                    if v_prev == 0:
                        pct_change = 100.0
                    else:
                        pct_change = (v_latest - v_prev) / v_prev * 100.0
                    if abs(pct_change) >= 5.0:
                        sign = 'increased' if pct_change > 0 else 'decreased'
                        insights.append(f'Sales for {c} category {sign} by {abs(pct_change):.0f}% this month.')
        except Exception:
            # fallback: approximate using monthly_sales (no precise month-over-month available)
            try:
                cat_sales = df.groupby('category')['monthly_sales'].sum()
                top = cat_sales.sort_values(ascending=False).head(3)
                insights.append(f'Top categories by monthly sales: {", ".join(top.index.tolist())}.')
            except Exception:
                pass

        # Category margin & stock risk
        try:
            cat_stats = df.groupby('category').apply(lambda g: pd.Series({
                'avg_margin': ((g['selling_price'] - g['cost_price']) / g['selling_price']).mean(),
                'avg_stock_ratio': (g['stock'] / (g['monthly_sales'].replace(0,1))).mean()
            })).reset_index()
            # compute risk for top categories using ai_service
            high_margin_cats = cat_stats[cat_stats['avg_margin'] > 0.25]
            for _, rcat in cat_stats.iterrows():
                # compute category-level risk by averaging product risk scores
                cat_products = df[df['category'] == rcat['category']]
                scores = []
                for _, p in cat_products.iterrows():
                    pr = ai_service.predict_risk(p.to_dict())
                    scores.append(pr.get('risk_score',0))
                avg_score = (sum(scores)/len(scores)) if scores else 0
                if avg_score >= 60:
                    insights.append(f'{rcat["category"]} category shows rising stock risk (avg risk {avg_score:.0f}).')
                if rcat['avg_margin'] > 0.30 and avg_score >= 40:
                    insights.append(f'{rcat["category"]} category shows high margin but rising stock risk.')
        except Exception:
            pass

        # Discount recommendations for slow-moving categories
        try:
            slow = cat_stats[cat_stats['avg_stock_ratio'] > 3]
            for _, s in slow.iterrows():
                insights.append(f'Apply 10% discount on slow-moving {s["category"]} products to clear excess stock.')
        except Exception:
            pass

        # Present insights
        if not insights:
            st.info('No automated insights available. Add more historical sales data to enable richer insights.')
        else:
            for ins in insights:
                st.write('•', ins)

        st.markdown('---')

# ---------------- Management page ----------------
elif menu == "Management":
    st.header('Management Layer — AI-driven Visualization & Decision Support')

    st.markdown('**Purpose:** Provide managers with high-level visuals: demand vs stock, dynamic pricing simulator, risk heatmap and revenue comparison (static vs AI-driven).')

    # Demand vs Stock
    st.subheader('Demand vs Stock')
    try:
        # Aggregate demand and stock by category for a cleaner, readable chart
        agg_df = df.groupby('category', as_index=False).agg(
            total_stock=('stock', 'sum'),
            total_sales=('monthly_sales', 'sum')
        )
        # Melt to show nicely in grouped bar chart
        melted = agg_df.melt(id_vars='category', value_vars=['total_sales', 'total_stock'], var_name='Metric', value_name='Amount')
        melted['Metric'] = melted['Metric'].replace({'total_sales': 'Monthly Demand', 'total_stock': 'Current Stock'})
        
        fig = px.bar(
            melted, 
            x='category', 
            y='Amount', 
            color='Metric', 
            barmode='group', 
            height=420,
            color_discrete_sequence=['#4338ca', '#10b981'],
            labels={'category': 'Product Category', 'Amount': 'Total Units'}
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f'Failed to render Demand vs Stock: {e}')

    st.markdown('---')

    # Dynamic pricing and discount panels
    st.subheader('Dynamic Pricing & Discount Simulator')
    col1, col2 = st.columns([2,1])
    with col1:
        target = st.selectbox('Target', ['Catalog', 'Product'] )
        if target == 'Product':
            p_choice = st.selectbox('Product', ['All'] + sorted(df['product_name'].dropna().unique().tolist()))
        else:
            p_choice = 'Catalog'
        disc = st.slider('Discount (%)', 0, 50, 10)
        price_delta = st.slider('Price change (%)', -50, 50, 0)

        if p_choice != 'All' and p_choice != 'Catalog':
            row = df[df['product_name']==p_choice].iloc[0].to_dict()
            sim = ai_service.simulate_pricing_effect(row, discount_pct=disc, price_change_pct=price_delta)
            st.metric('Projected change in demand', f"{sim['demand_change_pct']:+.1f}%")
            st.metric('Projected revenue', f"₹{sim['new_revenue']:,.0f}")
            st.metric('Projected profit', f"₹{sim['new_profit']:,.0f}")
        else:
            sim_df = ai_service.simulate_catalog_scenario(df, discount_pct=disc, price_change_pct=price_delta)
            total_base = sim_df['base_revenue'].sum()
            total_new = sim_df['new_revenue'].sum()
            st.metric('Catalog revenue (base → new)', f"₹{total_base:,.0f} → ₹{total_new:,.0f}")
            
            # Format display table nicely
            display_sim = sim_df.sort_values('delta_revenue', ascending=False).head(10).copy()
            for col in ['base_revenue', 'new_revenue', 'delta_revenue', 'base_profit', 'new_profit']:
                if col in display_sim.columns:
                    display_sim[col] = display_sim[col].apply(lambda x: f"₹{x:,.0f}")
            display_sim.columns = [c.replace('_', ' ').title() for c in display_sim.columns]
            
            st.dataframe(display_sim, use_container_width=True)
            csv_out = sim_df.to_csv(index=False)
            st.download_button('Download scenario CSV', data=csv_out, file_name='pricing_scenario.csv', mime='text/csv')

    with col2:
        st.markdown('**Quick actions**')
        st.markdown('- Preview impact before applying changes')
        st.markdown('- Use Apply actions cautiously. Use audit trails on changes.')

    st.markdown('---')

    # Risk heatmap
    st.subheader('Risk Heatmap (by Category)')
    try:
        heat = ai_service.aggregate_risk_heatmap(df)
        if heat.empty:
            st.info('No risk data available.')
        else:
            fig2 = px.bar(heat.sort_values('avg_risk_score', ascending=False), x='category', y='avg_risk_score', color='avg_risk_score', color_continuous_scale='RdYlGn_r', height=320)
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(heat)
    except Exception as e:
        st.warning(f'Failed to compute heatmap: {e}')

    st.markdown('---')

    # Revenue comparison
    st.subheader('Revenue comparison: Static vs AI-driven')
    try:
        scenario = ai_service.simulate_catalog_scenario(df, discount_pct=disc, price_change_pct=price_delta)
        catagg = scenario.groupby('category', as_index=False).agg(base_revenue=('base_revenue','sum'), new_revenue=('new_revenue','sum'))
        catagg['delta'] = catagg['new_revenue'] - catagg['base_revenue']
        fig3 = px.bar(catagg.sort_values('delta', ascending=False), x='category', y=['base_revenue','new_revenue'], barmode='group', height=420)
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(catagg)
    except Exception as e:
        st.warning(f'Failed revenue comparison: {e}')

    st.markdown('---')

    st.info('Management panel is experimental. Use the download buttons to export scenarios and review before applying any changes.')

# ---------------- PRICING PAGE ----------------
elif menu == "Pricing":


    st.markdown("## Pricing")

    # Filters
    categories = ["All"] + sorted(df["category"].dropna().unique().tolist())
    cat = st.selectbox("Category", categories)

    df_price = df.copy()
    if cat != "All":
        df_price = df_price[df_price["category"] == cat]

    # Product selector (category-aware). Choose a specific product or All.
    product_options = ["All"] + sorted(df_price["product_name"].dropna().unique().tolist())
    product_select = st.selectbox("Product", product_options)
    if product_select != "All":
        df_price = df_price[df_price["product_name"] == product_select]

    st.markdown("**Pricing Strategy**")
    desc_map = {
        "Target Margin %": "Target Margin % (Target profit margin as % of selling price)",
        "Markup %": "Markup % (Add flat percentage on top of unit cost)",
        "Increase by %": "Increase by % (Directly bump current selling price by %)"
    }
    strategy = st.radio("Strategy", ["Target Margin %", "Markup %", "Increase by %"], index=0, format_func=lambda x: desc_map.get(x, x))

    if strategy == "Target Margin %":
        target_margin = st.number_input("Target margin (%)", min_value=0.0, max_value=95.0, value=20.0, step=0.5)
    elif strategy == "Markup %":
        markup = st.number_input("Markup (%)", min_value=0.0, max_value=500.0, value=20.0, step=0.5)
    else:
        incr_pct = st.number_input("Increase by (%)", min_value=-100.0, max_value=500.0, value=5.0, step=0.5)

    # Select products
    candidates = df_price["product_name"].tolist()
    selected = st.multiselect("Select products to update price", options=candidates)

    # Build preview
    preview = []
    for prod in selected or candidates:
        row = df[df["product_name"] == prod].iloc[0]
        cost = float(row.get("cost_price") or row.get("cost") or 0)
        cur_price = float(row.get("selling_price") or 0)
        if strategy == "Target Margin %":
            # price = cost / (1 - margin)
            if target_margin >= 100:
                rec_price = cur_price
            else:
                rec_price = round(cost / (1 - target_margin / 100), 2) if (1 - target_margin / 100) > 0 else cur_price
        elif strategy == "Markup %":
            rec_price = round(cost * (1 + markup / 100), 2)
        else:
            rec_price = round(cur_price * (1 + incr_pct / 100), 2)

        margin = round((cur_price - cost) / cur_price * 100, 2) if cur_price else 0
        preview.append({
            "product_name": prod,
            "cost": cost,
            "current_price": cur_price,
            "current_margin%": margin,
            "recommended_price": rec_price
        })

    if preview:
        st.subheader("Pricing Preview")
        df_preview = pd.DataFrame(preview).rename(columns={
            "product_name": "Product Name",
            "cost": "Cost",
            "current_price": "Current Price",
            "current_margin%": "Current Margin %",
            "recommended_price": "Recommended Price"
        })
        
        # Cleanly format numbers to fix table spacing and sizing
        df_preview["Cost"] = df_preview["Cost"].apply(lambda x: f"₹{x:,.0f}")
        df_preview["Current Price"] = df_preview["Current Price"].apply(lambda x: f"₹{x:,.0f}")
        df_preview["Recommended Price"] = df_preview["Recommended Price"].apply(lambda x: f"₹{x:,.0f}")
        df_preview["Current Margin %"] = df_preview["Current Margin %"].apply(lambda x: f"{x:.1f}%")

        with st.container(height=450):
            st.table(df_preview)

        persist_price = st.checkbox("Persist prices to CSV (make permanent)", value=False)
        user_name = st.text_input("User (for audit log for price changes)")
        note = st.text_input("Note (optional)")

        if st.button("Apply pricing changes"):
            try:
                applied = []
                if persist_price:
                    # Try DB updates first
                    try:
                        from backend.db import SessionLocal
                        from backend.models import Product
                        session = SessionLocal()
                        for item in preview:
                            prod_name = item["product_name"]
                            prod = session.query(Product).filter(Product.product_name == prod_name).one_or_none()
                            if not prod:
                                st.warning(f"Product not found in DB: {prod_name}")
                                continue
                            old_price = float(prod.selling_price or 0.0)
                            new_price = float(item["recommended_price"])
                            prod.selling_price = new_price
                            session.add(prod)
                            try:
                                disc_service.log_price_change(prod_name, old_price, new_price, user=user_name, note=note)
                            except Exception:
                                pass
                            applied.append(prod_name)
                        session.commit()
                        session.close()
                        st.success(f"Prices persisted for: {', '.join(applied)}")
                        st.experimental_rerun()
                    except Exception:
                        # fallback to CSV
                        csv_path = os.path.join(BACKEND_DIR, "data", "products.csv")
                        if not os.path.exists(csv_path):
                            st.error("Products CSV not found to persist prices.")
                        else:
                            csv_df = pd.read_csv(csv_path)
                            applied = []
                            import csv as _csv
                            for item in preview:
                                prod = item["product_name"]
                                mask = csv_df["product_name"] == prod
                                if not mask.any():
                                    st.warning(f"Product not found in CSV: {prod}")
                                    continue
                                old_price = float(csv_df.loc[mask, "selling_price"].iloc[0])
                                new_price = float(item["recommended_price"]) if persist_price else old_price
                                if persist_price:
                                    csv_df.loc[mask, "selling_price"] = new_price
                                    # append price audit
                                    audit_path = os.path.join(BACKEND_DIR, "data", "price_audit.csv")
                                    header = ["timestamp", "product", "old_price", "new_price", "user", "note"]
                                    row = [__import__('datetime').date.today().isoformat(), prod, old_price, new_price, user_name or "", note or ""]
                                    write_header = not os.path.exists(audit_path)
                                    os.makedirs(os.path.dirname(audit_path), exist_ok=True)
                                    with open(audit_path, "a", newline='', encoding='utf-8') as f:
                                        writer = _csv.writer(f)
                                        if write_header:
                                            writer.writerow(header)
                                        writer.writerow(row)
                                    applied.append(prod)

                            if persist_price:
                                csv_df.to_csv(csv_path, index=False)
                                st.success(f"Prices persisted for: {', '.join(applied)}")
                                st.experimental_rerun()
                            else:
                                st.success("Pricing preview applied session-only.")
                else:
                    st.success("Pricing preview applied session-only.")
            except Exception as e:
                st.error(f"Failed to apply pricing changes: {e}")
    else:
        st.info("Select products to preview pricing changes.")

# ---------------- AI DECISION SUPPORT PAGE ----------------
elif menu == "AI Decision Support":
    st.markdown("<h2 style='margin:0 0 4px 0'>🤖 AI Decision Support</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;margin-top:-4px;margin-bottom:24px;'>AI-powered recommendations, risk analysis, and pricing simulations across your entire inventory.</p>", unsafe_allow_html=True)

    ai_tab1, ai_tab2, ai_tab3 = st.tabs(["💡 Recommendations", "⚠️ Risk Heatmap", "📊 Pricing Simulation"])

    # ── TAB 1: RECOMMENDATIONS ──
    with ai_tab1:
        st.markdown("### AI Recommendations")
        st.caption("Automatically generated actionable insights for your product catalog.")

        try:
            with st.spinner("Generating recommendations..."):
                rec_df = ai_service.bulk_recommendations(df)

            if rec_df.empty:
                st.info("✅ All products are in good shape — no critical actions needed right now.")
            else:
                # Summary KPIs
                rk1, rk2, rk3, rk4 = st.columns(4)
                rk1.metric("Total Recommendations", len(rec_df))
                rk2.metric("High Confidence (≥80%)", int((rec_df["confidence"] >= 0.8).sum()))
                rk3.metric("Products Flagged", rec_df["product"].nunique())
                rk4.metric("Top Action", rec_df["suggestion"].mode().iloc[0] if not rec_df.empty else "—")

                st.markdown("<br>", unsafe_allow_html=True)

                # Filter controls
                filter_col1, filter_col2 = st.columns(2)
                with filter_col1:
                    action_filter = st.multiselect(
                        "Filter by Action",
                        options=sorted(rec_df["suggestion"].unique()),
                        default=sorted(rec_df["suggestion"].unique()),
                        key="ai_action_filter"
                    )
                with filter_col2:
                    min_conf = st.slider("Min. Confidence", 0.0, 1.0, 0.0, 0.05, key="ai_conf_slider")

                filtered = rec_df[
                    (rec_df["suggestion"].isin(action_filter)) &
                    (rec_df["confidence"] >= min_conf)
                ].copy()

                if filtered.empty:
                    st.info("No recommendations match the current filters.")
                else:
                    # Color-coded badge per action
                    def _badge(action):
                        colors = {
                            "Increase reorder": ("#dbeafe", "#1d4ed8"),
                            "Apply discount":   ("#fef3c7", "#d97706"),
                            "Increase price":   ("#dcfce7", "#15803d"),
                            "Improve product quality": ("#fce7f3", "#be185d"),
                        }
                        bg, fg = colors.get(action, ("#f1f5f9", "#475569"))
                        return f"<span style='background:{bg};color:{fg};padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700;'>{action}</span>"

                    def _conf_bar(c):
                        pct = int(c * 100)
                        clr = "#10b981" if pct >= 80 else ("#f59e0b" if pct >= 60 else "#ef4444")
                        return f"<div style='background:var(--input-bg);border-radius:999px;height:8px;width:100px;display:inline-block;vertical-align:middle'><div style='background:{clr};border-radius:999px;height:8px;width:{pct}px'></div></div> <span style='font-size:12px;color:var(--text-muted)'>{pct}%</span>"

                    rows_html = ""
                    for _, row in filtered.iterrows():
                        rows_html += f"""
                        <tr style='border-bottom:1px solid var(--border-color);'>
                            <td style='padding:12px 16px;font-weight:600;color:var(--text-main);font-size:14px;'>{row['product']}</td>
                            <td style='padding:12px 16px;color:var(--text-muted);font-size:13px;'>{row['situation']}</td>
                            <td style='padding:12px 16px;'>{_badge(row['suggestion'])}</td>
                            <td style='padding:12px 16px;'>{_conf_bar(row['confidence'])}</td>
                            <td style='padding:12px 16px;color:var(--text-muted);font-size:12px;'>{row['reason']}</td>
                        </tr>"""

                    table_html = f"""
                    <div style='overflow-x:auto;border-radius:14px;border:1px solid var(--border-color);box-shadow:0 4px 16px var(--kpi-shadow);'>
                    <table style='width:100%;border-collapse:collapse;background:var(--card-bg);font-family:Times New Roman,serif;'>
                        <thead>
                        <tr style='background:var(--input-bg);border-bottom:2px solid var(--border-color);'>
                            <th style='padding:14px 16px;text-align:left;font-size:12px;color:#475569;text-transform:uppercase;letter-spacing:0.5px;'>Product</th>
                            <th style='padding:14px 16px;text-align:left;font-size:12px;color:#475569;text-transform:uppercase;letter-spacing:0.5px;'>Situation</th>
                            <th style='padding:14px 16px;text-align:left;font-size:12px;color:#475569;text-transform:uppercase;letter-spacing:0.5px;'>Action</th>
                            <th style='padding:14px 16px;text-align:left;font-size:12px;color:#475569;text-transform:uppercase;letter-spacing:0.5px;'>Confidence</th>
                            <th style='padding:14px 16px;text-align:left;font-size:12px;color:#475569;text-transform:uppercase;letter-spacing:0.5px;'>Reason</th>
                        </tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                    </table></div>"""
                    st.markdown(table_html, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # One-click apply action
                    st.markdown("#### ⚡ Apply Action")
                    ac1, ac2, ac3 = st.columns([2, 2, 1])
                    with ac1:
                        apply_product = st.selectbox("Select product", filtered["product"].unique(), key="ai_apply_prod")
                    with ac2:
                        apply_suggestion = st.selectbox(
                            "Select action",
                            filtered[filtered["product"] == apply_product]["suggestion"].unique(),
                            key="ai_apply_sugg"
                        )
                    with ac3:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("Apply ✅", key="ai_apply_btn", use_container_width=True):
                            with st.spinner("Applying..."):
                                result = ai_service.apply_action(
                                    apply_product,
                                    apply_suggestion,
                                    user=st.session_state.get("username", "webui")
                                )
                            if result.get("ok"):
                                st.success(result["message"])
                            else:
                                st.error(result["message"])
        except Exception as e:
            st.error(f"Failed to generate recommendations: {e}")

    # ── TAB 2: RISK HEATMAP ──
    with ai_tab2:
        st.markdown("### Inventory Risk Heatmap")
        st.caption("Stockout and overstock risk scores per category, computed by the AI risk engine.")

        try:
            with st.spinner("Computing risk scores..."):
                heat_df = ai_service.aggregate_risk_heatmap(df)

            if heat_df.empty:
                st.info("No risk data available.")
            else:
                # KPIs
                h1, h2, h3 = st.columns(3)
                h1.metric("Avg Risk Score", f"{heat_df['avg_risk_score'].mean():.1f} / 100")
                critical_cats = heat_df[heat_df['avg_risk_score'] >= 65]
                h2.metric("Critical Categories", len(critical_cats))
                h3.metric("Categories Analysed", len(heat_df))

                st.markdown("<br>", unsafe_allow_html=True)

                # Risk bar chart
                import plotly.express as px
                heat_df_sorted = heat_df.sort_values("avg_risk_score", ascending=True)
                fig_heat = px.bar(
                    heat_df_sorted,
                    x="avg_risk_score",
                    y="category",
                    orientation="h",
                    color="avg_risk_score",
                    color_continuous_scale=[[0,"#10b981"],[0.3,"#f59e0b"],[0.65,"#ef4444"],[1,"#7c3aed"]],
                    range_color=[0, 100],
                    text="avg_risk_score",
                    labels={"avg_risk_score": "Avg Risk Score", "category": "Category"},
                    title="Risk Score by Category"
                )
                fig_heat.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                fig_heat.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_family="Times New Roman",
                    coloraxis_showscale=False,
                    height=max(300, len(heat_df) * 45),
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                st.plotly_chart(fig_heat, use_container_width=True)

                # Product-level risk table
                st.markdown("#### Product-level Risk Detail")
                prod_risk_rows = []
                for _, row in df.iterrows():
                    r = ai_service.predict_risk(row.to_dict())
                    prod_risk_rows.append({
                        "Product": row["product_name"],
                        "Category": row.get("category", "—"),
                        "Risk Score": r["risk_score"],
                        "Label": r["label"],
                        "Stockout Prob": f"{r['stockout_prob']*100:.1f}%",
                        "Overstock Prob": f"{r['overstock_prob']*100:.1f}%",
                    })
                prod_risk_df = pd.DataFrame(prod_risk_rows).sort_values("Risk Score", ascending=False)

                def _risk_label_style(label):
                    if label == "Critical":
                        return "🔴 Critical"
                    elif label == "Warning":
                        return "🟡 Warning"
                    return "🟢 Safe"

                prod_risk_df["Label"] = prod_risk_df["Label"].apply(_risk_label_style)
                st.dataframe(prod_risk_df.reset_index(drop=True), use_container_width=True)

        except Exception as e:
            st.error(f"Failed to compute risk heatmap: {e}")

    # ── TAB 3: PRICING SIMULATION ──
    with ai_tab3:
        st.markdown("### Catalog-Wide Pricing Simulation")
        st.caption("Simulate the revenue and profit impact of applying a discount or price change across the entire catalog.")

        sim_c1, sim_c2 = st.columns(2)
        with sim_c1:
            sim_discount = st.slider("Discount (%)", 0.0, 50.0, 0.0, 1.0, key="ai_sim_discount")
        with sim_c2:
            sim_price_chg = st.slider("Price change (%)", -30.0, 30.0, 0.0, 1.0, key="ai_sim_price")

        if st.button("▶ Run Simulation", key="ai_sim_run", use_container_width=True):
            try:
                with st.spinner("Running AI pricing simulation..."):
                    sim_result = ai_service.simulate_catalog_scenario(df, discount_pct=sim_discount, price_change_pct=sim_price_chg)

                total_base_rev = sim_result["base_revenue"].sum()
                total_new_rev  = sim_result["new_revenue"].sum()
                total_base_pft = sim_result["base_profit"].sum()
                total_new_pft  = sim_result["new_profit"].sum()

                s1, s2, s3, s4 = st.columns(4)
                s1.metric("Base Revenue",  f"₹{total_base_rev:,.0f}")
                s2.metric("Simulated Revenue", f"₹{total_new_rev:,.0f}", delta=f"₹{total_new_rev - total_base_rev:+,.0f}")
                s3.metric("Base Profit",    f"₹{total_base_pft:,.0f}")
                s4.metric("Simulated Profit",  f"₹{total_new_pft:,.0f}", delta=f"₹{total_new_pft - total_base_pft:+,.0f}")

                st.markdown("<br>", unsafe_allow_html=True)

                # Category summary chart
                cat_sim = sim_result.groupby("category", as_index=False).agg(
                    base_revenue=("base_revenue", "sum"),
                    new_revenue=("new_revenue", "sum")
                )
                fig_sim = px.bar(
                    cat_sim,
                    x="category",
                    y=["base_revenue", "new_revenue"],
                    barmode="group",
                    labels={"value": "Revenue (₹)", "category": "Category", "variable": "Scenario"},
                    title="Revenue: Baseline vs Simulated",
                    color_discrete_sequence=["#cbd5e1", "#7c3aed"]
                )
                fig_sim.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_family="Times New Roman",
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                st.plotly_chart(fig_sim, use_container_width=True)

                # Product-level simulation table
                display_sim = sim_result[["product_name", "category", "base_revenue", "new_revenue", "delta_revenue", "base_profit", "new_profit", "delta_profit"]].copy()
                for col in ["base_revenue", "new_revenue", "delta_revenue", "base_profit", "new_profit", "delta_profit"]:
                    display_sim[col] = display_sim[col].apply(lambda x: f"₹{x:,.0f}")
                display_sim.columns = ["Product", "Category", "Base Rev", "Sim Rev", "Δ Revenue", "Base Profit", "Sim Profit", "Δ Profit"]
                st.dataframe(display_sim.reset_index(drop=True), use_container_width=True)

            except Exception as e:
                st.error(f"Simulation failed: {e}")
        else:
            st.info("Adjust the sliders above and click **Run Simulation** to see the impact on revenue and profit.")


# ---------------- REPORTS PAGE ----------------
elif menu == "Reports":
    st.markdown("## 📊 Reports & Analytics")

    tab_perf, tab_audit = st.tabs(["📉 Business Performance", "📋 Audit Logs"])

    with tab_perf:
        # Summary KPIs
        total_revenue = (df["selling_price"] * df["monthly_sales"]).sum()
        avg_margin = ((df["selling_price"] - df["cost_price"]) / df["selling_price"]).replace([np.inf, -np.inf], 0).fillna(0).mean() * 100
        total_units_sold = int(df["monthly_sales"].sum())

        r1, r2, r3 = st.columns(3)
        r1.metric("💰 Total Revenue (monthly)", f"₹{total_revenue:,.2f}")
        r2.metric("📈 Avg Margin (%)", f"{avg_margin:.2f}%")
        r3.metric("📦 Total Units Sold", f"{total_units_sold:,}")

        st.markdown("---")

        col_charts1, col_charts2 = st.columns(2)
        with col_charts1:
            st.subheader("Sales by Category")
            sales_cat = (df.assign(revenue=df["selling_price"] * df["monthly_sales"]) 
                           .groupby("category", as_index=False)["revenue"].sum())
            try:
                import plotly.express as px
                fig_pie = px.pie(sales_cat, names='category', values='revenue', hole=0.4, 
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)
            except ImportError:
                st.bar_chart(sales_cat.set_index("category"))

        with col_charts2:
            st.subheader("Top Products by Revenue")
            top_selling = df.assign(revenue=df["selling_price"] * df["monthly_sales"]).sort_values("revenue", ascending=False).head(10).copy()
            top_selling["selling_price"] = top_selling["selling_price"].apply(lambda x: f"₹{x:,.2f}")
            top_selling["revenue"] = top_selling["revenue"].apply(lambda x: f"₹{x:,.0f}")
            top_selling = top_selling[["product_name", "monthly_sales", "selling_price", "revenue"]].reset_index(drop=True)
            top_selling.columns = ["Product", "Units/Mo", "Unit Price", "Gross Revenue"]
            st.dataframe(top_selling, use_container_width=True)

    with tab_audit:

    # Audit viewers
        st.subheader("Discount Audit")
        import csv, io
        try:
            from backend.db import SessionLocal
            from backend.models import DiscountAudit
            session = SessionLocal()
            rows = session.query(DiscountAudit).order_by(DiscountAudit.timestamp.desc()).limit(200).all()
            session.close()
            if rows:
                disc_df = pd.DataFrame([{
                    "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                    "product": r.product,
                    "old_discount": r.old_discount,
                    "new_discount": r.new_discount,
                    "user": r.user,
                    "note": r.note
                } for r in rows])
                st.dataframe(disc_df, use_container_width=True)
                csv_buf = io.StringIO()
                disc_df.to_csv(csv_buf, index=False)
                st.download_button("Download discount audit CSV", data=csv_buf.getvalue(), file_name="discount_audit.csv", mime="text/csv")
            else:
                st.info("No discount audit records found.")
        except Exception:
            discount_audit_path = os.path.join(BACKEND_DIR, "data", "discount_audit.csv")
            if os.path.exists(discount_audit_path):
                disc_df = pd.read_csv(discount_audit_path)
                st.dataframe(disc_df, use_container_width=True)
                csv_buf = io.StringIO()
                disc_df.to_csv(csv_buf, index=False)
                st.download_button("Download discount audit CSV", data=csv_buf.getvalue(), file_name="discount_audit.csv", mime="text/csv")
            else:
                st.info("No discount audit records found.")

        st.markdown("---")

        st.subheader("Price Audit")
        try:
            from backend.db import SessionLocal
            from backend.models import PriceAudit
            session = SessionLocal()
            rows = session.query(PriceAudit).order_by(PriceAudit.timestamp.desc()).limit(200).all()
            session.close()
            if rows:
                price_df = pd.DataFrame([{
                    "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                    "product": r.product,
                    "old_price": r.old_price,
                    "new_price": r.new_price,
                    "user": r.user,
                    "note": r.note
                } for r in rows])
                st.dataframe(price_df, use_container_width=True)
                csv_buf2 = io.StringIO()
                price_df.to_csv(csv_buf2, index=False)
                st.download_button("Download price audit CSV", data=csv_buf2.getvalue(), file_name="price_audit.csv", mime="text/csv")
            else:
                st.info("No price audit records found.")
        except Exception:
            price_audit_path = os.path.join(BACKEND_DIR, "data", "price_audit.csv")
            if os.path.exists(price_audit_path):
                price_df = pd.read_csv(price_audit_path)
                st.dataframe(price_df, use_container_width=True)
                csv_buf2 = io.StringIO()
                price_df.to_csv(csv_buf2, index=False)
                st.download_button("Download price audit CSV", data=csv_buf2.getvalue(), file_name="price_audit.csv", mime="text/csv")
            else:
                st.info("No price audit records found.")

# ──────────────────────────────────────────────────────────────────
# USER MANAGEMENT PAGE  (super_admin only)
# ──────────────────────────────────────────────────────────────────
elif menu == "User Management" and st.session_state.get("role") == "super_admin":

    st.markdown(
        """
        <style>
        .admin-hero {
            background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 50%, #a855f7 100%);
            border-radius: 20px;
            padding: 32px 36px;
            margin-bottom: 28px;
            display: flex;
            align-items: center;
            gap: 20px;
            box-shadow: 0 12px 40px rgba(124,58,237,0.35);
            font-family: 'Times New Roman', Times, serif !important;
        }
        .admin-hero h1 { color: white !important; margin: 0 !important; font-size: 28px !important; font-family: 'Times New Roman', Times, serif !important; }
        .admin-hero p  { color: rgba(255,255,255,0.8) !important; margin: 4px 0 0 0 !important; font-size: 14px !important; font-family: 'Times New Roman', Times, serif !important; }
        
        .admin-kpi {
            background: var(--card-bg) !important;
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: 0 4px 20px var(--kpi-shadow);
            border: 1px solid var(--border-color);
            text-align: center;
            font-family: 'Times New Roman', Times, serif !important;
        }
        .admin-kpi .ak-val { font-size: 32px; font-weight: 800; color: var(--text-main); letter-spacing: -1px; font-family: 'Times New Roman', Times, serif !important; }
        .admin-kpi .ak-lbl { font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; font-family: 'Times New Roman', Times, serif !important; }
        .admin-kpi .ak-ico { font-size: 24px; margin-bottom: 6px; }
        
        .sect-card {
            background: var(--card-bg) !important;
            border-radius: 18px;
            padding: 28px;
            box-shadow: 0 4px 20px var(--kpi-shadow);
            border: 1px solid var(--border-color);
            margin-bottom: 24px;
            font-family: 'Times New Roman', Times, serif !important;
        }
        .sect-card h3 { font-size: 17px !important; font-weight: 800 !important;
                         color: var(--text-main) !important; margin: 0 0 16px 0 !important; font-family: 'Times New Roman', Times, serif !important; }
        
        .role-badge-sa  { background:#fef3c7; color:#b45309; padding:3px 10px;
                          border-radius:999px; font-size:11px; font-weight:700; border:1px solid #fde68a; font-family: 'Times New Roman', Times, serif !important; }
        .role-badge-ad  { background:#ede9fe; color:#6d28d9; padding:3px 10px;
                          border-radius:999px; font-size:11px; font-weight:700; border:1px solid #ddd6fe; font-family: 'Times New Roman', Times, serif !important; }
        .role-badge-us  { background:#f0fdf4; color:#166534; padding:3px 10px;
                          border-radius:999px; font-size:11px; font-weight:700; border:1px solid #bbf7d0; font-family: 'Times New Roman', Times, serif !important; }
        
        .status-on  { color:#10b981; font-weight:700; font-family: 'Times New Roman', Times, serif !important; }
        .status-off { color:#ef4444; font-weight:700; font-family: 'Times New Roman', Times, serif !important; }
        
        /* Ensure table text inside admin pages also uses Times New Roman */
        .admin-table-container table { font-family: 'Times New Roman', Times, serif !important; }
        </style>
        """, unsafe_allow_html=True
    )

    # ── Hero banner ──
    st.markdown(
        """
        <div class='admin-hero'>
          <div style='font-size:48px;'>🛡️</div>
          <div>
            <h1>User Management</h1>
            <p>Create, edit, assign roles and control every account in the system.</p>
          </div>
        </div>
        """, unsafe_allow_html=True
    )

    from backend.db import SessionLocal as _SASL
    from backend.models import User as _SAUser, Registration as _SAReg

    _sa_session = _SASL()

    try:
        all_users = _sa_session.query(_SAUser).order_by(_SAUser.created_at.desc()).all()

        # ── KPI row ──
        total_u   = len(all_users)
        active_u  = sum(1 for u in all_users if u.is_active)
        inactive_u = total_u - active_u
        admins_u  = sum(1 for u in all_users if u.role in ("super_admin", "Admin"))
        normal_u  = total_u - admins_u

        kc1, kc2, kc3, kc4 = st.columns(4)
        for col, ico, val, lbl, clr in [
            (kc1, "👥", total_u,    "Total Accounts",  "#7c3aed"),
            (kc2, "🟢", active_u,   "Active",           "#10b981"),
            (kc3, "🔴", inactive_u, "Inactive",         "#ef4444"),
            (kc4, "⭐", admins_u,   "Admins / Superusers", "#f59e0b"),
        ]:
            col.markdown(
                f"""<div class='admin-kpi'>
                       <div class='ak-ico'>{ico}</div>
                       <div class='ak-val' style='color:{clr}'>{val}</div>
                       <div class='ak-lbl'>{lbl}</div>
                     </div>""",
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ──────────────────────────────────────────────────
        # TABS
        # ──────────────────────────────────────────────────
        tab_list, tab_edit, tab_create, tab_audit = st.tabs([
            "📋  All Users",
            "✏️  Edit / Role",
            "➕  Create User",
            "📜  Audit Log",
        ])

        # ── TAB 1: ALL USERS ──────────────────────────────
        with tab_list:
            st.markdown("<div class='sect-card'>", unsafe_allow_html=True)
            st.markdown("<h3>User Directory</h3>", unsafe_allow_html=True)

            # Search bar
            search_term = st.text_input("🔍  Search by username or email", placeholder="Type to filter…", key="um_search")

            # Role filter
            role_filter = st.selectbox("Filter by Role", ["All", "User", "Admin", "super_admin"], key="um_role_filter")

            # Build table rows
            def _role_badge(r):
                if r == "super_admin":   return "<span class='role-badge-sa'>⭐ Super Admin</span>"
                elif r == "Admin":       return "<span class='role-badge-ad'>🛡 Admin</span>"
                else:                    return "<span class='role-badge-us'>👤 User</span>"

            rows_html = ""
            count = 0
            for u in all_users:
                if search_term and search_term.lower() not in u.username.lower() and search_term.lower() not in (u.email or "").lower():
                    continue
                if role_filter != "All" and u.role != role_filter:
                    continue
                count += 1
                joined = u.created_at.strftime("%b %d, %Y") if u.created_at else "—"
                last   = u.last_login.strftime("%b %d, %Y %H:%M") if u.last_login else "Never"
                status_cls  = "status-on"  if u.is_active else "status-off"
                status_txt  = "● Active"   if u.is_active else "● Inactive"
                rows_html += f"""
                <tr style='border-bottom:1px solid var(--border-color)'>
                  <td style='padding:12px 14px;font-weight:600;color:var(--text-main)'>{u.username}</td>
                  <td style='padding:12px 14px;color:var(--text-muted)'>{u.email or '—'}</td>
                  <td style='padding:12px 14px;text-align:center'>{_role_badge(u.role)}</td>
                  <td style='padding:12px 14px;text-align:center' class='{status_cls}'>{status_txt}</td>
                  <td style='padding:12px 14px;color:var(--text-muted);font-size:12px'>{joined}</td>
                  <td style='padding:12px 14px;color:var(--text-muted);font-size:12px'>{last}</td>
                </tr>"""

            table_html = f"""
            <table style='width:100%;border-collapse:collapse;font-family:"Times New Roman",serif;'>
              <thead>
                <tr style='background:var(--input-bg);border-bottom:2px solid var(--border-color)'>
                  <th style='padding:12px 14px;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted)'>Username</th>
                  <th style='padding:12px 14px;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted)'>Email</th>
                  <th style='padding:12px 14px;text-align:center;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted)'>Role</th>
                  <th style='padding:12px 14px;text-align:center;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted)'>Status</th>
                  <th style='padding:12px 14px;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted)'>Joined</th>
                  <th style='padding:12px 14px;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted)'>Last Login</th>
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>"""

            st.markdown(f"<div class='admin-table-container'>{table_html}</div>", unsafe_allow_html=True)
            if count == 0:
                st.info("No users match your search/filter criteria.")
            else:
                st.caption(f"Showing {count} of {total_u} accounts")

            st.markdown("</div>", unsafe_allow_html=True)

        # ── TAB 2: EDIT / ROLE ────────────────────────────
        with tab_edit:
            st.markdown("<div class='sect-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Edit Account</h3>", unsafe_allow_html=True)

            usernames = [u.username for u in all_users]
            edit_target = st.selectbox("Select account to edit", usernames, key="um_edit_sel")
            edit_u = _sa_session.query(_SAUser).filter(_SAUser.username == edit_target).first()

            if edit_u:
                # Info row
                info_c1, info_c2 = st.columns(2)
                info_c1.info(f"**User ID:** `{edit_u.user_id}`  \n**Email:** {edit_u.email}")
                info_c2.info(f"**Joined:** {edit_u.created_at.strftime('%b %d, %Y') if edit_u.created_at else 'N/A'}  \n**Last Login:** {edit_u.last_login.strftime('%b %d, %Y %H:%M') if edit_u.last_login else 'Never'}")

                st.markdown("<br>", unsafe_allow_html=True)

                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    roles_avail = ["User", "Admin", "super_admin"]
                    cur_idx = roles_avail.index(edit_u.role) if edit_u.role in roles_avail else 0
                    new_role_val = st.selectbox("Role", roles_avail, index=cur_idx, key="um_new_role",
                                               help="super_admin gets the User Management page.")
                with ec2:
                    new_email_val = st.text_input("Email", value=edit_u.email or "", key="um_new_email")
                with ec3:
                    new_username_val = st.text_input("Username", value=edit_u.username, key="um_new_uname")

                is_active_val = st.toggle("Account Active", value=edit_u.is_active, key="um_active_toggle",
                                          help="Inactive users cannot log in.")

                st.markdown("<br>", unsafe_allow_html=True)

                save_c, del_c = st.columns([3, 1])
                with save_c:
                    if st.button("💾  SAVE CHANGES", use_container_width=True, type="primary", key="um_save"):
                        # Prevent self-demotion from super_admin
                        if edit_target == st.session_state.username and new_role_val != "super_admin":
                            st.error("🔒 You cannot change your own role while logged in.")
                        else:
                            edit_u.role      = new_role_val
                            edit_u.email     = new_email_val.strip()
                            edit_u.username  = new_username_val.strip()
                            edit_u.is_active = is_active_val
                            _sa_session.commit()
                            st.success(f"✅ Account **{edit_target}** updated successfully!")
                            st.rerun()

                with del_c:
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander("🗑 Delete", expanded=False):
                        st.warning("This action is **permanent** and cannot be undone.")
                        confirm_del = st.text_input("Type the username to confirm", key="um_del_confirm")
                        if st.button("DELETE ACCOUNT", type="primary", key="um_del_btn"):
                            if confirm_del != edit_target:
                                st.error("Username does not match. Deletion cancelled.")
                            elif edit_target == st.session_state.username:
                                st.error("🔒 Cannot delete your own account while logged in.")
                            else:
                                _sa_session.delete(edit_u)
                                _sa_session.commit()
                                st.success(f"Deleted **{edit_target}**.")
                                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

            # ── Reset Password sub-section ──
            st.markdown("<div class='sect-card'>", unsafe_allow_html=True)
            st.markdown("<h3>🔑  Reset User Password</h3>", unsafe_allow_html=True)
            st.caption("Force-reset any user's password. They must be notified separately.")

            rp_col1, rp_col2 = st.columns(2)
            with rp_col1:
                rp_user = st.selectbox("Select user", usernames, key="um_rp_user")
            with rp_col2:
                rp_new_pwd = st.text_input("New password (min 6 chars)", type="password", key="um_rp_pwd")

            if st.button("🔑  RESET PASSWORD", key="um_rp_btn", use_container_width=True):
                if not rp_new_pwd or len(rp_new_pwd) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    rp_u = _sa_session.query(_SAUser).filter(_SAUser.username == rp_user).first()
                    if rp_u:
                        rp_u.password_hash = rp_new_pwd
                        # Also update Registration table if linked
                        rp_reg = _sa_session.query(_SAReg).filter(_SAReg.email == rp_u.email).first()
                        if rp_reg:
                            rp_reg.password = rp_new_pwd
                        _sa_session.commit()
                        st.success(f"✅ Password for **{rp_user}** has been reset.")

            st.markdown("</div>", unsafe_allow_html=True)

        # ── TAB 3: CREATE USER ────────────────────────────
        with tab_create:
            st.markdown("<div class='sect-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Create New Account</h3>", unsafe_allow_html=True)
            st.caption("This will create both a Registration record and a User account instantly.")

            cu_c1, cu_c2 = st.columns(2)
            with cu_c1:
                cu_uname = st.text_input("Username *", placeholder="johndoe", key="cu_uname")
                cu_email = st.text_input("Email *", placeholder="john@example.com", key="cu_email")
            with cu_c2:
                cu_pwd   = st.text_input("Password *", type="password", placeholder="Min 6 characters", key="cu_pwd")
                cu_mobile = st.text_input("Mobile (optional)", placeholder="+91 98765 43210", key="cu_mobile")

            cu_role  = st.selectbox("Assign Role", ["User", "Admin", "super_admin"], key="cu_role")
            cu_active = st.toggle("Account Active", value=True, key="cu_active")

            if st.button("➕  CREATE ACCOUNT", use_container_width=True, type="primary", key="cu_btn"):
                if not cu_uname or not cu_email or not cu_pwd:
                    st.error("Username, email and password are required.")
                elif len(cu_pwd) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    existing = _sa_session.query(_SAUser).filter(
                        (_SAUser.username == cu_uname.strip()) | (_SAUser.email == cu_email.strip())
                    ).first()
                    if existing:
                        st.error("A user with that username or email already exists.")
                    else:
                        try:
                            new_reg = _SAReg(
                                username=cu_uname.strip(),
                                email=cu_email.strip(),
                                password=cu_pwd,
                                mobileno=cu_mobile.strip() or None,
                                created_at=datetime.datetime.utcnow()
                            )
                            _sa_session.add(new_reg)
                            _sa_session.flush()
                            # Generate unique user_id
                            import random as _rand
                            _uid = f"U{_rand.randint(1000,9999)}"
                            while _sa_session.query(_SAUser).filter(_SAUser.user_id == _uid).first():
                                _uid = f"U{_rand.randint(1000,9999)}"
                            new_user = _SAUser(
                                user_id=_uid,
                                username=cu_uname.strip(),
                                email=cu_email.strip(),
                                password_hash=cu_pwd,
                                role=cu_role,
                                is_active=cu_active,
                                created_at=datetime.datetime.utcnow(),
                                registration_id=str(new_reg.id)
                            )
                            _sa_session.add(new_user)
                            _sa_session.commit()
                            st.success(f"✅ Account **{cu_uname}** created with role **{cu_role}**!")
                            st.rerun()
                        except Exception as _ce:
                            _sa_session.rollback()
                            st.error(f"Failed to create account: {_ce}")

            st.markdown("</div>", unsafe_allow_html=True)

        # ── TAB 4: AUDIT LOG ──────────────────────────────
        with tab_audit:
            st.markdown("<div class='sect-card'>", unsafe_allow_html=True)
            st.markdown("<h3>System Overview</h3>", unsafe_allow_html=True)

            # Role distribution chart
            role_counts = {}
            for u in all_users:
                r = u.role or "User"
                role_counts[r] = role_counts.get(r, 0) + 1

            rc_df = pd.DataFrame(list(role_counts.items()), columns=["Role", "Count"])
            try:
                import plotly.express as _px_sa
                fig_roles = _px_sa.pie(
                    rc_df, names="Role", values="Count",
                    color_discrete_map={"super_admin": "#f59e0b", "Admin": "#7c3aed", "User": "#10b981"},
                    title="Role Distribution"
                )
                fig_roles.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_family="Times New Roman",
                    margin=dict(t=40, b=0, l=0, r=0)
                )
                st.plotly_chart(fig_roles, use_container_width=True)
            except ImportError:
                st.dataframe(rc_df, use_container_width=True)

            st.markdown("---")
            st.markdown("<h3>Account Register (Full)</h3>", unsafe_allow_html=True)

            full_rows = []
            for u in all_users:
                full_rows.append({
                    "User ID":    u.user_id,
                    "Username":   u.username,
                    "Email":      u.email or "—",
                    "Role":       u.role or "User",
                    "Active":     "Yes" if u.is_active else "No",
                    "Joined":     u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "—",
                    "Last Login": u.last_login.strftime("%Y-%m-%d %H:%M") if u.last_login else "Never",
                })

            full_df = pd.DataFrame(full_rows)
            st.dataframe(full_df, use_container_width=True, hide_index=True)

            import io as _io_sa
            _csv_buf = _io_sa.StringIO()
            full_df.to_csv(_csv_buf, index=False)
            st.download_button(
                "📥  Download User Register (CSV)",
                data=_csv_buf.getvalue(),
                file_name="user_register.csv",
                mime="text/csv",
                use_container_width=True
            )

            st.markdown("</div>", unsafe_allow_html=True)

    finally:
        _sa_session.close()

# ---------------- OTHER PAGES ----------------
elif menu not in nav_items:
    st.info("This section will be implemented next.")


