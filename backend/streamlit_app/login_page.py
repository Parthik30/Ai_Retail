import sys
import os
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.append(PROJECT_ROOT)

import streamlit as st
import datetime

from backend.db import SessionLocal, init_db
from backend.models import User, Registration
from sqlalchemy.exc import ProgrammingError


def authenticate(username: str, password: str):
    session = SessionLocal()
    try:
        user = (
            session.query(User)
            .filter((User.username == username) | (User.email == username))
            .first()
        )
    except ProgrammingError:
        session.rollback()
        init_db()
        session.close()
        return False, None
    finally:
        # don't close before using `user` reference above
        pass

    session.close()
    if user and user.password_hash == password:
        return True, user
    return False, None


def register_user(username, email, password, mobile=""):
    session = SessionLocal()
    try:
        # check existing
        existing = session.query(Registration).filter((Registration.email == email) | (Registration.username == username)).first()
        if existing:
            return False, "Account with that username or email already exists"

        reg = Registration(username=username, email=email, password=password, mobileno=mobile)
        session.add(reg)
        session.commit()
        session.refresh(reg)

        user = User(user_id=f"R{reg.id:04d}", username=username, email=email, password_hash=password, role="User", is_active=True, created_at=datetime.datetime.utcnow(), registration_id=str(reg.id))
        session.add(user)
        session.commit()
        return True, "Registration successful"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


st.set_page_config(page_title="Login", layout="wide")

st.markdown("""
<style>

.stApp{
    background: linear-gradient(135deg,#8E2DE2,#4A00E0);
    color:white;
}

.block-container{
    padding-top:3rem;
}

.title{
    font-size:42px;
    font-weight:700;
}

.subtitle{
    opacity:0.8;
    margin-bottom:30px;
}

div[data-baseweb="input"] input{
    background:rgba(255,255,255,0.2)!important;
    color:white!important;
    border-radius:10px!important;
}

div.stButton>button{
    width:100%;
    height:48px;
    border-radius:10px;
    font-weight:600;
    background:white;
    color:#4A00E0;
    transition:0.3s;
}

div.stButton>button:hover{
    transform:translateY(-2px);
    box-shadow:0 10px 25px rgba(255,255,255,0.4);
}

</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1,1])

with col1:
    st.markdown("<div class='title'>IntelliStock</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>AI Retail Intelligence Platform</div>", unsafe_allow_html=True)

    uname = st.text_input("Email or Username")
    pwd = st.text_input("Password", type="password")

    if st.button("LOGIN"):
        if not uname or not pwd:
            st.error("Enter username and password")
        else:
            ok, user = authenticate(uname, pwd)
            if ok:
                st.success("Login successful!")
            else:
                st.error("Invalid credentials")

with col2:
    st.image("frontend/static/login_illustration.png", use_column_width=True)
