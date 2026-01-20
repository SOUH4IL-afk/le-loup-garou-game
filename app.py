# 🐺 Werewolf Online – Ultimate Clean Version
# Streamlit Multiplayer Game with State Machine, Timers, Roles, Chat & Victory System
# Author: Souhail By

import streamlit as st
from streamlit_server_state import server_state, server_state_lock
from streamlit_autorefresh import st_autorefresh
import random
import time

# ==============================
# CONFIG & STYLES
# ==============================

st.set_page_config(page_title="Werewolf Ultimate", page_icon="🐺", layout="wide")
st_autorefresh(interval=1000, key="refresh")

CUSTOM_CSS = """
<style>
body { background-color: #0f1117; color: white; }
.role-card {
    background: #1f2933;
    padding: 15px;
    border-radius: 15px;
    text-align: center;
}
.chat-box {
    background: #111827;
    padding: 10px;
    border-radius: 10px;
}
.timer {
    font-size: 28px;
    font-weight: bold;
    color: #fbbf24;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==============================
# ROLE IMAGES
# ==============================

ROLE_IMAGES = {
    "مستذئب": "https://r2.erweima.ai/ai_image/928c2538-4e17-4861-9f93-4889429712a7.jpg",
    "عرافة": "https://r2.erweima.ai/ai_image/c1c38e91-c27d-419b-9c7a-590f23f66f91.jpg",
    "ساحرة": "https://r2.erweima.ai/ai_image/3f7e1553-524f-409c-a124-783362a2123d.jpg",
    "قروي": "https://r2.erweima.ai/ai_image/0c7d4e32-5a2a-464e-9844-301986423588.jpg",
    "صياد": "https://r2.erweima.ai/ai_image/6d2e67a1-8d4e-4e8c-9c9e-5f9f6e6e6e6e.jpg",
    "كيوبيد": "https://r2.erweima.ai/ai_image/8e1e7e7e-7e7e-7e7e-7e7e-7e7e7e7e7e7e.jpg",
}

# ==============================
# CONSTANTS
# ==============================

PHASE_TIMES = {
    "Lobby": 0,
    "Night_Cupid": 20,
    "Night_Werewolf": 30,
    "Night_Seer": 20,
    "Night_Witch": 20,
    "Day": 30,
    "Voting": 40,
}

# ==============================
# HELPERS
# ==============================


def init_rooms():
    with server_state_lock["init"]:
        if "rooms" not in server_state:
            server_state["rooms"] = {}


def new_room(room_id, admin):
    return {
        "players": [admin],
        "roles": {},
        "alive": [],
        "phase": "Lobby",
        "admin": admin,
        "chats": [],
        "wolf_chats": [],
        "lovers": [],
        "actions": {"victim": None, "saved": None},
        "votes": {},
        "logs": [],
        "phase_start": time.time(),
        "pending_hunter": None,
    }


def log(room, msg):
    room["logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")


def distribute_roles(players):
    n = len(players)
    random.shuffle(players)

    num_wolves = 1 if n <= 5 else (2 if n <= 8 else 3)
    specials = ["عرافة", "ساحرة", "صياد", "كيوبيد"]

    roles = ["مستذئب"] * num_wolves + specials
    roles = roles[:n]
    roles += ["قروي"] * (n - len(roles))

    random.shuffle(roles)
    return dict(zip(players, roles))


def check_victory(room):
    alive = room["alive"]
    roles = room["roles"]

    wolves = [p for p in alive if roles[p] == "مستذئب"]
    villagers = [p for p in alive if roles[p] != "مستذئب"]

    if not wolves:
        return "Villagers", "🎉 فازت القرية! تم القضاء على جميع المستذئبين"
    if len(wolves) >= len(villagers):
        return "Werewolves", "🐺 فاز المستذئبون وسيطروا على القرية"
    return None, None


def phase_timer(room):
    limit = PHASE_TIMES.get(room["phase"], 0)
    if limit == 0:
        return None

    elapsed = int(time.time() - room["phase_start"])
    remaining = max(0, limit - elapsed)

    if remaining == 0:
        advance_phase(room)

    return remaining


def set_phase(room, phase):
    room["phase"] = phase
    room["phase_start"] = time.time()
    log(room, f"انتقلنا إلى المرحلة: {phase}")


# ==============================
# STATE MACHINE
# ==============================


def advance_phase(room):
    p = room["phase"]

    if p == "Night_Cupid":
        set_phase(room, "Night_Werewolf")

    elif p == "Night_Werewolf":
        set_phase(room, "Night_Seer")

    elif p == "Night_Seer":
        set_phase(room, "Night_Witch")

    elif p == "Night_Witch":
        set_phase(room, "Day")

    elif p == "Day":
        set_phase(room, "Voting")

    elif p == "Voting":
        execute_votes(room)
        set_phase(room, "Night_Werewolf")


# ==============================
# VOTING SYSTEM
# ==============================


def execute_votes(room):
    votes = room["votes"]
    room["votes"] = {}

    if not votes:
        log(room, "لم يتم التصويت من أحد")
        return

    result = {}
    for v in votes.values():
        result[v] = result.get(v, 0) + 1

    eliminated = max(result, key=result.get)

    if eliminated in room["alive"]:
        room["alive"].remove(eliminated)
        log(room, f"⚖️ تم إعدام {eliminated}")

        if room["roles"][eliminated] == "صياد":
            room["pending_hunter"] = eliminated


# ==============================
# INIT
# ==============================

init_rooms()

# ==============================
# LOGIN
# ==============================

if "room_id" not in st.session_state:
    st.title("🐺 Werewolf Online Ultimate")

    room_id = st.text_input("رمز الغرفة")
    name = st.text_input("اسمك")

    if st.button("دخول"):
        if room_id and name:
            with server_state_lock["rooms"]:
                if room_id not in server_state["rooms"]:
                    server_state["rooms"][room_id] = new_room(room_id, name)
                server_state["rooms"][room_id]["players"].append(name)

            st.session_state.room_id = room_id
            st.session_state.name = name
            st.rerun()

    st.stop()

# ==============================
# GAME
# ==============================

room = server_state["rooms"][st.session_state.room_id]
me = st.session_state.name
role = room["roles"].get(me, "مشاهد")
is_admin = me == room["admin"]

col_main, col_side = st.columns([3, 1])

# ==============================
# MAIN PANEL
# ==============================

with col_main:
    st.header(f"🏰 الغرفة: {st.session_state.room_id} | المرحلة: {room['phase']}")

    timer = phase_timer(room)
    if timer is not None:
        st.markdown(f"<div class='timer'>⏳ الوقت المتبقي: {timer}s</div>", unsafe_allow_html=True)

    winner, msg = check_victory(room)
    if winner:
        st.balloons()
        st.success(msg)
        if is_admin and st.button("إعادة اللعبة"):
            room.clear()
            server_state["rooms"][st.session_state.room_id] = new_room(st.session_state.room_id, me)
            st.rerun()
        st.stop()

    if room["phase"] == "Lobby":
        st.write("👥 اللاعبون:", ", ".join(room["players"]))
        if is_admin and st.button("🚀 بدء اللعبة"):
            room["roles"] = distribute_roles(room["players"].copy())
            room["alive"] = room["players"].copy()
            set_phase(room, "Night_Cupid")
            st.rerun()

    elif room["phase"] == "Night_Werewolf":
        if role == "مستذئب":
            target = st.selectbox("اختر الضحية", [p for p in room["alive"] if room["roles"][p] != "مستذئب"])
            if st.button("هجوم"):
                room["actions"]["victim"] = target
                log(room, f"🐺 الذئاب اختاروا {target}")
                advance_phase(room)
                st.rerun()
        else:
            st.info("🌙 الذئاب تتحرك في الظلام...")

    elif room["phase"] == "Voting":
        vote = st.selectbox("صوت ضد:", room["alive"])
        if st.button("تصويت"):
            room["votes"][me] = vote
            st.success("تم تسجيل صوتك")

# ==============================
# SIDE PANEL
# ==============================

with col_side:
    if room["phase"] != "Lobby":
        st.markdown("<div class='role-card'>", unsafe_allow_html=True)
        st.image(ROLE_IMAGES.get(role), width=150)
        st.write(f"دورك: **{role}**")
        st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("💬 الدردشة")
    with st.container(height=250):
        for c in reversed(room["chats"]):
            st.write(f"**{c['u']}**: {c['m']}")

    with st.form("chat"):
        msg = st.text_input("رسالة")
        if st.form_submit_button("إرسال"):
            room["chats"].append({"u": me, "m": msg})
            st.rerun()

    if role == "مستذئب":
        st.subheader("🐺 دردشة الذئاب")
        with st.container(height=150):
            for c in reversed(room["wolf_chats"]):
                st.write(f"🐺 {c['u']}: {c['m']}")

        with st.form("wolf"):
            w = st.text_input("رسالة سرية")
            if st.form_submit_button("إرسال"):
                room["wolf_chats"].append({"u": me, "m": w})
                st.rerun()

    st.subheader("📜 سجل الأحداث")
    with st.container(height=150):
        for l in reversed(room["logs"][-20:]):
            st.write(l)

# ==============================
# END
# ==============================
