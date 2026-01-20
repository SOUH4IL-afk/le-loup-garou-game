import streamlit as st
from streamlit_server_state import server_state, server_state_lock
from streamlit_autorefresh import st_autorefresh
import random

# 1. إعدادات الصفحة والتحديث التلقائي (كل 3 ثوانٍ)
st.set_page_config(page_title="Loup-Garou Online", layout="centered")
st_autorefresh(interval=3000, key="datarefresh")

# 2. تعريف الصور والأدوار
ROLES_CONFIG = {
    "كيوبيد": "WhatsApp Image 2025-12-29 at 15.58.10.jpeg",
    "عرافة": "WhatsApp Image 2025-12-29 at 15.58.10 (1).jpeg",
    "مستذئب": "WhatsApp Image 2025-12-29 at 15.58.11 (1).jpeg",
    "ساحرة": "WhatsApp Image 2025-12-29 at 15.58.09.jpeg",
    "صياد": "WhatsApp Image 2025-12-29 at 15.58.12.jpeg",
    "قروي": "WhatsApp Image 2025-12-29 at 15.58.13.jpeg"
}

# 3. تهيئة الحالة المشتركة على السيرفر
with server_state_lock["game_state"]:
    if "phase" not in server_state:
        server_state.update({
            "phase": "Lobby",
            "players": [],
            "roles": {},
            "alive_players": [],
            "logs": [],
            "current_turn_idx": 0,
            "turn_order": ["كيوبيد", "عرافة", "مستذئب", "ساحرة"],
            "night_data": {"killed": None, "saved": False, "poisoned": None},
            "lovers": [],
            "hunter_dead": False
        })

# 4. دالة القتل الموحدة (أونلاين)
def online_kill(player_name):
    if player_name in server_state.alive_players:
        server_state.alive_players.remove(player_name)
        server_state.logs.append(f"💀 موت {player_name} ({server_state.roles[player_name]})")
        # منطق العشاق
        if player_name in server_state.lovers:
            other = [p for p in server_state.lovers if p != player_name][0]
            if other in server_state.alive_players:
                server_state.alive_players.remove(other)
                server_state.logs.append(f"💔 {other} مات حزناً على {player_name}")
        # منطق الصياد
        if server_state.roles[player_name] == "صياد":
            server_state.hunter_dead = True

# 5. واجهة الدخول
if "my_id" not in st.session_state:
    st.title("🐺 انضم لقرية المستذئبين")
    name = st.text_input("اسمك:")
    if st.button("دخول"):
        if name and name not in server_state.players:
            with server_state_lock["game_state"]:
                server_state.players.append(name)
            st.session_state.my_id = name
            st.rerun()
    st.stop()

my_name = st.session_state.my_id
my_role = server_state.roles.get(my_name)

# 6. محرك اللعبة الرئيسي
st.sidebar.title(f"👤 {my_name}")
if my_role: st.sidebar.info(f"دورك: {my_role}")

if server_state.phase == "Lobby":
    st.header("🏰 غرفة الانتظار")
    st.write("اللاعبون:", server_state.players)
    if len(server_state.players) >= 5 and st.button("بدء اللعبة"):
        with server_state_lock["game_state"]:
            p_list = server_state.players.copy()
            random.shuffle(p_list)
            roles = ["كيوبيد", "عرافة", "مستذئب", "ساحرة", "صياد"] + ["قروي"]*(len(p_list)-5)
            server_state.roles = dict(zip(p_list, roles))
            server_state.alive_players = p_list
            server_state.phase = "Night"
        st.rerun()

elif server_state.phase == "Night":
    current_role = server_state.turn_order[server_state.current_turn_idx]
    st.header(f"🌙 ليل القرية - دور: {current_role}")
    
    if my_role == current_role and my_name in server_state.alive_players:
        st.success("إنه دورك! تصرف بسرعة.")
        st.image(ROLES_CONFIG[my_role], width=200)
        
        # منطق الأدوار الليلية
        if my_role == "كيوبيد" and not server_state.lovers:
            l1 = st.selectbox("عاشق 1", server_state.alive_players, key="c1")
            l2 = st.selectbox("عاشق 2", server_state.alive_players, key="c2")
            if st.button("ربط"):
                with server_state_lock["game_state"]:
                    server_state.lovers = [l1, l2]
                    server_state.current_turn_idx += 1
                st.rerun()
        
        elif my_role == "مستذئب":
            target = st.selectbox("ضحية الليل", server_state.alive_players)
            if st.button("افتراس"):
                with server_state_lock["game_state"]:
                    server_state.night_data["killed"] = target
                    server_state.current_turn_idx += 1
                st.rerun()
        
        # (يمكن إضافة بقية الأدوار هنا بنفس النمط)
        elif st.button("تخطي الدور"):
            with server_state_lock["game_state"]:
                server_state.current_turn_idx += 1
                if server_state.current_turn_idx >= len(server_state.turn_order):
                    server_state.phase = "Day"
            st.rerun()
    else:
        st.warning(f"الانتظار حتى ينهي {current_role} حركته...")

elif server_state.phase == "Day":
    st.header("☀️ طلع النهار")
    # معالجة النتائج (تظهر مرة واحدة)
    if st.button("كشف أحداث الليل"):
        with server_state_lock["game_state"]:
            victim = server_state.night_data["killed"]
            if victim and not server_state.night_data["saved"]:
                online_kill(victim)
            server_state.night_data = {"killed": None, "saved": False}
            server_state.current_turn_idx = 0 
            server_state.phase = "Voting"
        st.rerun()

elif server_state.phase == "Voting":
    st.header("⚖️ التصويت")
    target = st.selectbox("من المشتبه به؟", server_state.alive_players)
    if st.button("طرد"):
        with server_state_lock["game_state"]:
            online_kill(target)
            server_state.phase = "Night"
        st.rerun()

# منطق الصياد الطارئ
if server_state.hunter_dead:
    st.error("🎯 الصياد يطلق رصاصته الأخيرة!")
    if my_role == "صياد":
        h_target = st.selectbox("اقتل معك:", server_state.alive_players)
        if st.button("إطلاق"):
            with server_state_lock["game_state"]:
                online_kill(h_target)
                server_state.hunter_dead = False
            st.rerun()

st.sidebar.divider()
if st.sidebar.button("Reset Game"):
    server_state.clear()
    st.rerun()