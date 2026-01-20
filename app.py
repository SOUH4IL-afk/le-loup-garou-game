import streamlit as st
import random

# إعدادات الصفحة
st.set_page_config(page_title="لعبة المستذئب - Loup-Garou", layout="centered")

# --- تهيئة متغيرات اللعبة (Session State) ---
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
    st.session_state.players = []
    st.session_state.roles = {}
    st.session_state.phase = "setup"  # setup, night_wolf, day_vote
    st.session_state.victim = None
    st.session_state.logs = []

def start_game(names):
    player_list = [name.strip() for name in names.split(",") if name.strip()]
    if len(player_list) < 3:
        st.error("يجب أن يكون هناك 3 لاعبين على الأقل!")
        return
    
    st.session_state.players = player_list
    # توزيع الأدوار (مستذئب واحد والباقي قرويين في هذه النسخة المبسطة)
    roles_list = ["مستذئب"] + ["قروي"] * (len(player_list) - 1)
    random.shuffle(roles_list)
    st.session_state.roles = dict(zip(player_list, roles_list))
    st.session_state.game_started = True
    st.session_state.phase = "night_wolf"
    st.session_state.logs.append("بدأت اللعبة! حل الليل على القرية...")

# --- واجهة المستخدم ---
st.title("🐺 لعبة Loup-Garou")

if not st.session_state.game_started:
    st.header("⚙️ إعداد اللعبة")
    names_input = st.text_input("أدخل أسماء اللاعبين (مفصولة بفاصلة ,)")
    if st.button("بدء اللعبة"):
        start_game(names_input)

else:
    # عرض سجل الأحداث
    with st.expander("📜 سجل الأحداث"):
        for log in st.session_state.logs:
            st.write(log)

    # --- مرحلة الليل (دور المستذئب) ---
    if st.session_state.phase == "night_wolf":
        st.header("🌙 الليل: دور المستذئب")
        st.warning("يجب على الجميع إغلاق أعينهم، باستثناء المستذئب!")
        
        target = st.selectbox("يا مستذئب، اختر ضحيتك:", st.session_state.players)
        if st.button("تأكيد القتل"):
            st.session_state.victim = target
            st.session_state.logs.append(f"لقد هاجم المستذئب شخصاً ما في الليل...")
            st.session_state.phase = "day_vote"
            st.rerun()

    # --- مرحلة النهار (التصويت) ---
    elif st.session_state.phase == "day_vote":
        st.header("☀️ النهار: استيقظت القرية")
        st.error(f"خبر عاجل: لقد وجدنا جثة {st.session_state.victim}! لقد مات.")
        
        # إزالة الضحية من قائمة اللاعبين
        if st.session_state.victim in st.session_state.players:
            st.session_state.players.remove(st.session_state.victim)

        st.subheader("التصويت للطرد")
        vote_target = st.selectbox("من تشكون أنه المستذئب؟", st.session_state.players)
        
        if st.button("طرد اللاعب"):
            chosen_role = st.session_state.roles[vote_target]
            st.session_state.logs.append(f"القرية قررت طرد {vote_target}. كان دوره: {chosen_role}")
            
            if chosen_role == "مستذئب":
                st.success("🎉 فازت القرية! تم القضاء على المستذئب.")
                if st.button("لعبة جديدة"):
                    st.session_state.clear()
                    st.rerun()
            else:
                st.session_state.players.remove(vote_target)
                st.session_state.phase = "night_wolf"
                st.session_state.logs.append("أخطأت القرية.. حل الليل مرة أخرى.")
                st.rerun()

    # خيار لإعادة ضبط اللعبة
    if st.sidebar.button("إعادة ضبط اللعبة"):
        st.session_state.clear()
        st.rerun()