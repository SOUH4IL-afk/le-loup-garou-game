import streamlit as st
import random
import yaml
import pandas as pd
import streamlit_authenticator as stauth
from streamlit_server_state import server_state, server_state_lock


# ---------------- CONFIG ----------------
st.set_page_config(page_title="🐺 Werewolf Online", layout="centered")


# ---------------- MOBILE UI ----------------
MOBILE_CSS = """
<style>
body { background: #020617; color: white; }
.card { background: #020617; border-radius: 16px; padding: 12px; box-shadow: 0 0 15px rgba(0,0,0,0.5); margin-bottom: 10px; }
.timer { font-size: 26px; color: #22c55e; text-align: center; }
.bottom-nav { position: fixed; bottom: 0; width: 100%; display: flex; justify-content: space-around; background: #020617; padding: 8px; border-top: 1px solid #1e293b; }
.nav-btn { font-size: 12px; color: white; }
</style>
"""


st.markdown(MOBILE_CSS, unsafe_allow_html=True)


# ---------------- LOAD USERS ----------------
with open('users.yaml') as file:
config = yaml.safe_load(file)


authenticator = stauth.Authenticate(
config['credentials'],
config['cookie']['name'],
config['cookie']['key'],
config['cookie']['expiry_days']
)


name, auth_status, username = authenticator.login('Login', 'main')


if not auth_status:
st.stop()


st.sidebar.success(f"Welcome {name}")
authenticator.logout("Logout", "sidebar")


IS_ADMIN = username == 'admin'


# ---------------- SERVER STATE ----------------
with server_state_lock:
if 'rooms' not in server_state:
server_state['rooms'] = {}


# ---------------- HELPERS ----------------
def new_room(password=""):
return {
'players': [],
'roles': {},
'phase': 'lobby',
'votes': {},
'password': password,
'stats': {},
'log': []
}


# ---------------- UI ----------------
st.title("🐺 Werewolf Online")


mode = st.radio("Mode", ["Create Room", "Join Room"])
room_id = st.text_input("Room ID")
st.sidebar.metric("Users", len(config['credentials']['usernames']))