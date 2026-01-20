import streamlit as st
from streamlit_server_state import server_state, server_state_lock
from streamlit_autorefresh import st_autorefresh
import random

# 1. إعداد الصفحة والتحديث التلقائي
st.set_page_config(page_title="Loup-Garou Online", layout="wide")
st_autorefresh(interval=3000, key="datarefresh") # تحديث كل 3 ثوانٍ لمزامنة الدردشة والتحركات

# 2. تهيئة البيانات العالمية (Server State)
with server_state_lock["global_state"]:
    if "rooms" not in server_state:
        server_state["rooms"] = {}

# 3. واجهة الدخول
st.title("🐺 قرية المستذئبين المباشرة")

with st.sidebar:
    st.header("🔑 الدخول")
    room_id = st.text_input("رمز الغرفة (مثلاً: Game101)").strip()
    user_name = st.text_input("اسمك المستعار").strip()
    st.divider()
    admin_pass = st.text_input("كلمة سر المسؤول (اختياري)", type="password")
    is_admin = (admin_pass == "123") # كلمة السر الافتراضية

if not room_id or not user_name:
    st.info("الرجاء إدخال رمز الغرفة واسمك للانضمام.")
    st.stop()

# 4. إدارة الغرف
with server_state_lock["room_management"]:
    if room_id not in server_state["rooms"]:
        server_state["rooms"][room_id] = {
            "players": [],
            "roles": {},
            "phase": "Lobby",
            "logs": [],
            "chats": [],
            "alive": [],
            "victim": None,
            "turn_idx": 0
        }

room = server_state["rooms"][room_id]

# انضمام اللاعب
if user_name not in room["players"] and room["phase"] == "Lobby":
    with server_state_lock["player_join"]:
        room["players"].append(user_name)
        room["logs"].append(f"👋 انضم {user_name} للقرية")

# 5. تقسيم الواجهة
col_game, col_chat = st.columns([2, 1])

# --- قسم اللعبة ---
with col_game:
    st.subheader(f"📍 الغرفة: {room_id} | الحالة: {room['phase']}")
    
    if room["phase"] == "Lobby":
        st.write("اللاعبون حالياً:", ", ".join(room["players"]))
        if is_admin and len(room["players"]) >= 4:
            if st.button("🚀 بدء اللعبة (للأدمن)"):
                with server_state_lock["start_game"]:
                    p_list = room["players"].copy()
                    random.shuffle(p_list)
                    # توزيع أدوار متقدمة
                    advanced_roles = ["مستذئب", "عرافة", "ساحرة", "صياد"] + ["قروي"]*(len(p_list)-4)
                    random.shuffle(advanced_roles)
                    room["roles"] = dict(zip(p_list, advanced_roles))
                    room["alive"] = p_list.copy()
                    room["phase"] = "Night"
                    room["logs"].append("🌑 بدأ الليل.. الكل ينام.")
                st.rerun()
        elif len(room["players"]) < 4:
            st.warning("ننتظر انضمام 4 لاعبين على الأقل...")

    elif room["phase"] == "Night":
        my_role = room["roles"].get(user_name, "مشاهد")
        st.info(f"🕵️ دورك السري هو: {my_role}")
        
        if user_name not in room["alive"]:
            st.error("💀 أنت ميت الآن.. يمكنك مشاهدة الدردشة فقط.")
        else:
            # منطق ليل مبسط (يمكن توسيعه)
            if my_role == "مستذئب":
                targets = [p for p in room["alive"] if room["roles"][p] != "مستذئب"]
                victim = st.selectbox("اختر فريستك:", targets)
                if st.button("تأكيد القتل"):
                    room["victim"] = victim
                    room["phase"] = "Day"
                    room["logs"].append(f"🐺 هجم المستذئبون في الظلام...")
                    st.rerun()
            else:
                st.write("انتظر حتى ينتهي المستذئبون من اختيار ضحيتهم...")

    elif room["phase"] == "Day":
        st.error(f"☀️ طلع النهار.. وجدنا جثة {room['victim']}!")
        if room["victim"] in room["alive"]:
            room["alive"].remove(room["victim"])
        
        if st.button("بدء التصويت"):
            room["phase"] = "Voting"
            st.rerun()

    elif room["phase"] == "Voting":
        st.subheader("⚖️ ساحة الإعدام")
        target = st.selectbox("من تريد طرده؟", room["alive"])
        if st.button("تصويت"):
            room["logs"].append(f"⚖️ قررت القرية طرد {target}")
            if room["roles"][target] == "مستذئب":
                room["phase"] = "End"
                room["logs"].append("🎉 فازت القرية! تم طرد المستذئب.")
            else:
                room["alive"].remove(target)
                room["phase"] = "Night"
            st.rerun()

# --- قسم الدردشة ---
with col_chat:
    st.subheader("💬 الدردشة الجماعية")
    
    # نموذج إرسال الرسائل
    with st.form("chat_box", clear_on_submit=True):
        msg = st.text_input("اكتب شيئاً...")
        if st.form_submit_button("إرسال") and msg:
            room["chats"].append({"user": user_name, "msg": msg})
            st.rerun()

    # عرض الرسائل بشكل عكسي (الأحدث فوق)
    chat_display = st.container(height=400)
    for c in reversed(room["chats"]):
        chat_display.write(f"**{c['user']}:** {c['msg']}")

# --- لوحة تحكم الأدمن (أسفل الصفحة) ---
if is_admin:
    with st.expander("🛠️ لوحة تحكم المسؤول"):
        if st.button("🧹 إعادة ضبط الغرفة"):
            room["phase"] = "Lobby"
            room["players"] = []
            room["chats"] = []
            st.rerun()
        st.write("الأدوار الحالية:", room["roles"])

# سجل الأحداث
with st.expander("📜 سجل القرية الكامل"):
    for log in reversed(room["logs"]):
        st.write(log)