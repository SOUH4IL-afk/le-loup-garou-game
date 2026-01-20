import streamlit as st
import random

# إعدادات الصفحة
st.set_page_config(page_title="Loup-Garou Pro", layout="centered")

# --- تعريف الأدوار وبياناتها ---
ROLES_DATA = {
    "مستذئب": "WhatsApp Image 2025-12-29 at 15.58.11 (1).jpeg",
    "عرافة": "WhatsApp Image 2025-12-29 at 15.58.10 (1).jpeg",
    "ساحرة": "WhatsApp Image 2025-12-29 at 15.58.09.jpeg",
    "صياد": "WhatsApp Image 2025-12-29 at 15.58.12.jpeg",
    "كيوبيد": "WhatsApp Image 2025-12-29 at 15.58.10.jpeg",
    "قروي": "WhatsApp Image 2025-12-29 at 15.58.13.jpeg"
}

# --- تهيئة الجلسة ---
if 'game_started' not in st.session_state:
    st.session_state.update({
        'game_started': False,
        'players': [],
        'roles': {},
        'phase': "setup",
        'logs': [],
        'alive_players': [],
        'night_actions': {"killed": None, "saved": None}
    })

def initialize_game(names):
    player_list = [n.strip() for n in names.split(",") if n.strip()]
    if len(player_list) < 5:
        st.error("يفضل وجود 5 لاعبين على الأقل لتفعيل كافة الأدوار!")
        return
    
    available_roles = ["مستذئب", "عرافة", "ساحرة", "صياد", "كيوبيد"] + ["قروي"] * (len(player_list) - 5)
    random.shuffle(available_roles)
    
    st.session_state.players = player_list
    st.session_state.alive_players = player_list.copy()
    st.session_state.roles = dict(zip(player_list, available_roles))
    st.session_state.game_started = True
    st.session_state.phase = "night_start"

# --- الواجهة الرسومية ---
st.title("🐺 قرية المستذئبين")

if not st.session_state.game_started:
    st.header("🎭 توزيع الأدوار")
    names_input = st.text_input("أسماء اللاعبين (مفصولة بفاصلة)")
    if st.button("توزيع الأدوار وبدء اللعبة"):
        initialize_game(names_input)
else:
    # عرض معلومات الدور الحالي سرا (اختياري للاعب الذي يمسك الجهاز)
    with st.sidebar:
        st.write("### 👤 قائمة الأحياء")
        st.write(st.session_state.alive_players)
        if st.button("إعادة ضبط"):
            st.session_state.clear()
            st.rerun()

    # --- إدارة مراحل الليل والنهار ---
    
    if st.session_state.phase == "night_start":
        st.subheader("🌙 حل الليل.. على الجميع إغلاق أعينهم")
        if st.button("بدء دور الأدوار الخاصة"):
            st.session_state.phase = "seer_turn"
            st.rerun()

    # 1. دور العرافة
    elif st.session_state.phase == "seer_turn":
        st.image(ROLES_DATA["عرافة"], width=200)
        st.header("🔮 دور العرافة")
        target = st.selectbox("اختار لاعب لكشف هويته:", st.session_state.alive_players)
        if st.button("كشف الهوية"):
            role = st.session_state.roles[target]
            st.success(f"هوية {target} هي: {role}")
            if st.button("إنهاء دور العرافة"):
                st.session_state.phase = "wolf_turn"
                st.rerun()

    # 2. دور المستذئب
    elif st.session_state.phase == "wolf_turn":
        st.image(ROLES_DATA["مستذئب"], width=200)
        st.header("🐺 دور المستذئب")
        target = st.selectbox("من ستفترس الليلة؟", st.session_state.alive_players)
        if st.button("تأكيد الهجوم"):
            st.session_state.night_actions["killed"] = target
            st.session_state.phase = "witch_turn"
            st.rerun()

    # 3. دور الساحرة
    elif st.session_state.phase == "witch_turn":
        st.image(ROLES_DATA["ساحرة"], width=200)
        st.header("🧪 دور الساحرة")
        st.write(f"المستذئبون اختاروا قتل: {st.session_state.night_actions['killed']}")
        action = st.radio("ماذا ستفعلين؟", ["لا شيء", "إنقاذ الضحية", "قتل شخص آخر"])
        
        if action == "قتل شخص آخر":
            poison_target = st.selectbox("اختار من تسممين:", st.session_state.alive_players)
        
        if st.button("تأكيد قرار الساحرة"):
            if action == "إنقاذ الضحية":
                st.session_state.night_actions["killed"] = None
            elif action == "قتل شخص آخر":
                st.session_state.night_actions["killed"] = [st.session_state.night_actions["killed"], poison_target]
            st.session_state.phase = "day_results"
            st.rerun()

    # 4. نتائج الصباح
    elif st.session_state.phase == "day_results":
        st.header("☀️ طلع النهار")
        killed = st.session_state.night_actions["killed"]
        
        if killed:
            if isinstance(killed, list):
                for k in killed:
                    if k in st.session_state.alive_players: st.session_state.alive_players.remove(k)
                st.error(f"للأسف، استيقظت القرية على موت: {', '.join(killed)}")
            else:
                st.session_state.alive_players.remove(killed)
                st.error(f"للأسف، استيقظت القرية على موت: {killed}")
        else:
            st.success("يا له من حظ! لم يمت أحد هذه الليلة.")
            
        if st.button("الانتقال للتصويت"):
            st.session_state.phase = "village_vote"
            st.rerun()

    # 5. تصويت القرية
    elif st.session_state.phase == "village_vote":
        st.header("⚖️ محكمة القرية")
        st.image(ROLES_DATA["قروي"], width=200)
        vote_target = st.selectbox("اتفقوا على طرد شخص واحد:", st.session_state.alive_players)
        if st.button("طرد"):
            role = st.session_state.roles[vote_target]
            st.session_state.alive_players.remove(vote_target)
            st.info(f"تم طرد {vote_target} وكان دوره {role}")
            
            if role == "مستذئب":
                st.balloons()
                st.success("انتصرت القرية!")
            else:
                st.session_state.phase = "night_start"
                st.rerun()