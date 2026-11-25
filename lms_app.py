import streamlit as st
import sqlite3
import pandas as pd
import base64
from datetime import datetime
from streamlit_quill import st_quill

# កំណត់រចនាសម្ព័ន្ធទំព័រ
st.set_page_config(page_title="ចំណេះដឹងគណិតវិទ្យា - LMS", page_icon="📐", layout="wide")

# បង្កើត និងភ្ជាប់ Database (SQLite)
conn = sqlite3.connect('school_lms.db', check_same_thread=False)
c = conn.cursor()

# បញ្ជីសប្តាហ៍ទាំង ៥ និងបញ្ជីថ្នាក់
WEEKS = ["សប្តាហ៍ទី ១", "សប្តាហ៍ទី ២", "សប្តាហ៍ទី ៣", "សប្តាហ៍ទី ៤", "សប្តាហ៍ទី ៥"]
CLASSES = ["ថ្នាក់ ក", "ថ្នាក់ ខ", "ថ្នាក់ គ", "ថ្នាក់ ឃ", "ថ្នាក់ ង", "ថ្នាក់ ច", "ថ្នាក់ ឆ", "ថ្នាក់ ជ"]

# បង្កើត និងអាប់ដេតតារាងទិន្នន័យ (ការពារទិន្នន័យចាស់ ១០០%)
def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, class_name TEXT, student_id TEXT, student_name TEXT, week TEXT, date TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lessons 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, week TEXT, category TEXT, title TEXT, content TEXT, video_url TEXT, pdf_name TEXT, pdf_data BLOB, v_question TEXT, v_opt_a TEXT, v_opt_b TEXT, v_opt_c TEXT, v_correct TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS quizzes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, week TEXT, question TEXT, opt_a TEXT, opt_b TEXT, opt_c TEXT, correct_opt TEXT, is_pretest INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, class_name TEXT, student_id TEXT, student_name TEXT, week TEXT, score INTEGER, total INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings 
                 (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS library 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, pdf_name TEXT, pdf_data BLOB, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS forum 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, week TEXT, class_name TEXT, author_name TEXT, role_tag TEXT, message TEXT, date TEXT)''')

    # អាប់ដេតជួរឈរសម្រាប់តារាងចាស់ៗ (ការពារកុំឲ្យបាត់ទិន្នន័យចាស់)
    for tbl in ['attendance', 'lessons', 'quizzes', 'scores']:
        c.execute(f"PRAGMA table_info({tbl})")
        cols = [col[1] for col in c.fetchall()]
        if 'week' not in cols:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN week TEXT DEFAULT 'សប្តាហ៍ទី ១'")
            
    for tbl in ['attendance', 'scores']:
        c.execute(f"PRAGMA table_info({tbl})")
        cols = [col[1] for col in c.fetchall()]
        if 'class_name' not in cols:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN class_name TEXT DEFAULT 'ថ្នាក់ ក'")

    c.execute("PRAGMA table_info(lessons)")
    l_cols = [col[1] for col in c.fetchall()]
    new_lesson_cols = {
        'category': "TEXT DEFAULT 'ខ្លឹមសារមេរៀន'",
        'pdf_name': "TEXT",
        'pdf_data': "BLOB",
        'v_question': "TEXT",
        'v_opt_a': "TEXT",
        'v_opt_b': "TEXT",
        'v_opt_c': "TEXT",
        'v_correct': "TEXT"
    }
    for col_name, col_type in new_lesson_cols.items():
        if col_name not in l_cols:
            c.execute(f"ALTER TABLE lessons ADD COLUMN {col_name} {col_type}")

    c.execute("PRAGMA table_info(quizzes)")
    q_cols = [col[1] for col in c.fetchall()]
    if 'is_pretest' not in q_cols:
        c.execute("ALTER TABLE quizzes ADD COLUMN is_pretest INTEGER DEFAULT 0")

    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('num_questions', '5')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('final_questions', '15')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('course_expectation', '<p>សូមស្វាគមន៍មកកាន់ប្រព័ន្ធសិក្សាអនឡាញ <b>ចំណេះដឹងគណិតវិទ្យា</b>!</p>')")
    conn.commit()

init_db()

def get_setting(key, default_val):
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = c.fetchone()
    return res[0] if res else default_val

# រចនាម៉ូដអក្សរខ្មែរ (Battambang) និងលាក់របារ GitHub ខាងលើ
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Battambang:wght@400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Battambang', sans-serif; }
    [data-testid="stToolbar"] { visibility: hidden; display: none; }
    header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

st.title("📐 ប្រព័ន្ធសិក្សាអនឡាញ៖ ចំណេះដឹងគណិតវិទ្យា")

# ម៉ឺនុយជ្រើសរើសតួនាទី (សិស្ស ឬ គ្រូ)
role = st.sidebar.selectbox("ជ្រើសរើសតួនាទីប្រើប្រាស់៖", ["👨‍🎓 ផ្នែកសម្រាប់សិស្ស (Student)", "👨‍🏫 ផ្នែកសម្រាប់គ្រូ (Teacher Admin)"])

# ==========================================
# ១. ផ្នែកសម្រាប់សិស្ស (STUDENT PORTAL)
# ==========================================
if role == "👨‍🎓 ផ្នែកសម្រាប់សិស្ស (Student)":
    # បង្ហាញសេចក្តីជូនដំណឹង (Notification)
    c.execute("SELECT message, date FROM notifications ORDER BY id DESC LIMIT 3")
    notifs = c.fetchall()
    if notifs:
        for msg, n_date in notifs:
            st.info(f"🔔 **សេចក្តីជូនដំណឹង ({n_date})៖** {msg}")

    # បង្ហាញការរំពឹងទុកពីវគ្គសិក្សា
    with st.expander("🎯 ការរំពឹងទុក និងគោលបំណងនៃវគ្គសិក្សា (សូមអានមុនចាប់ផ្តើម)", expanded=False):
        st.markdown(get_setting('course_expectation', ''), unsafe_allow_html=True)

    # ម៉ឺនុយមេសម្រាប់សិស្ស
    main_nav = st.radio(
        "ម៉ឺនុយមេ៖",
        ["📅 កម្មវិធីសិក្សាប្រចាំសប្តាហ៍ (១-៥)", "📝 បុរេតេស្ត (Pre-Test)", "🎓 តេស្តបញ្ចប់វគ្គ (Final Test)", "🏛️ បណ្ណាល័យឯកសារ (Library)"],
        horizontal=True
    )
    st.divider()

    # ------------------------------------------
    # ក. កម្មវិធីសិក្សាប្រចាំសប្តាហ៍ (រចនាបថ MoEYS PLP LMS)
    # ------------------------------------------
    if main_nav == "📅 កម្មវិធីសិក្សាប្រចាំសប្តាហ៍ (១-៥)":
        selected_week = st.selectbox("📅 ជ្រើសរើសសប្តាហ៍សិក្សា៖", WEEKS)
        
        # ម៉ឺនុយទាំង ៦ ក្នុងសប្តាហ៍នីមួយៗដូច PLP LMS
        w_tabs = st.tabs([
            "✅ ចុះវត្តមាន",
            "📌 សេចក្តីផ្តើម",
            "📖 ខ្លឹមសារមេរៀន (អាន/វីដេអូ)",
            "🧭 ស្វ័យសិក្សា",
            "💬 វេទិកាពិភាក្សា",
            "✍️ ការវាយតម្លៃ (តេស្ត)"
        ])

        # ១. ចុះវត្តមាន
        with w_tabs[0]:
            st.subheader(f"✅ ចុះវត្តមានប្រចាំ {selected_week}")
            with st.form("attendance_form"):
                s_class = st.selectbox("ជ្រើសរើសថ្នាក់របស់អ្នក", CLASSES)
                s_id = st.text_input("អត្តលេខសិស្ស (ឧ. S001)")
                s_name = st.text_input("គោត្តនាម និងនាម")
                status = st.selectbox("ស្ថានភាព", ["វត្តមាន", "សុំច្បាប់"])
                if st.form_submit_button("បញ្ជូនវត្តមាន"):
                    if s_id and s_name:
                        today = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute("INSERT INTO attendance (class_name, student_id, student_name, week, date, status) VALUES (?, ?, ?, ?, ?, ?)",
                                  (s_class, s_id.strip(), s_name.strip(), selected_week, today, status))
                        conn.commit()
                        st.success(f"ជោគជ័យ! បានកត់ត្រាវត្តមានសម្រាប់ {s_name} ({s_class} - {selected_week}) រួចរាល់។")
                    else:
                        st.error("សូមបញ្ចូលអត្តលេខ និងឈ្មោះរបស់អ្នក!")

        # ២. សេចក្តីផ្តើម (Introduction)
        with w_tabs[1]:
            st.subheader(f"📌 សេចក្តីផ្តើម និងគោលបំណងមេរៀន - {selected_week}")
            c.execute("SELECT id, title, content, pdf_name, pdf_data FROM lessons WHERE week = ? AND category = 'សេចក្តីផ្តើម' ORDER BY id DESC", (selected_week,))
            intro_data = c.fetchall()
            if not intro_data:
                st.info(f"មិនទាន់មានខ្លឹមសារសេចក្តីផ្តើមសម្រាប់ {selected_week} នៅឡើយទេ។")
            else:
                for i_id, title, content, pdf_name, pdf_data in intro_data:
                    st.markdown(f"### {title}")
                    st.markdown(content, unsafe_allow_html=True)
                    if pdf_data and pdf_name:
                        st.download_button(f"📥 ទាញយកឯកសារណែនាំ៖ {pdf_name}", data=pdf_data, file_name=pdf_name, mime="application/pdf", key=f"intro_pdf_{i_id}")

        # ៣. ខ្លឹមសារមេរៀន (ឯកសារអាន, វីដេអូ, វីដេអូភ្ជាប់សំណួរ)
        with w_tabs[2]:
            st.subheader(f"📖 ខ្លឹមសារមេរៀន - {selected_week}")
            c.execute("SELECT id, title, content, video_url, pdf_name, pdf_data, v_question, v_opt_a, v_opt_b, v_opt_c, v_correct FROM lessons WHERE week = ? AND (category = 'ខ្លឹមសារមេរៀន' OR category IS NULL) ORDER BY id ASC", (selected_week,))
            lessons_data = c.fetchall()
            if not lessons_data:
                st.info(f"មិនទាន់មានខ្លឹមសារមេរៀនសម្រាប់ {selected_week} នៅឡើយទេ។")
            else:
                for l_id, title, content, video_url, pdf_name, pdf_data, v_q, v_a, v_b, v_c, v_corr in lessons_data:
                    with st.expander(f"📘 {title}", expanded=True):
                        st.markdown(content, unsafe_allow_html=True)
                        
                        # ឯកសារអាន PDF
                        if pdf_data and pdf_name:
                            st.download_button(f"📥 ទាញយកឯកសារអាន (PDF)៖ {pdf_name}", data=pdf_data, file_name=pdf_name, mime="application/pdf", key=f"dl_pdf_{l_id}")
                            with st.expander("👁️ ចុចទីនេះដើម្បីអានឯកសារផ្ទាល់លើអេក្រង់"):
                                base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                                st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>', unsafe_allow_html=True)
                        
                        # វីដេអូបង្រៀន
                        if video_url:
                            st.video(video_url)
                            
                        # វីដេអូភ្ជាប់ជាមួយសំណួរអន្តរកម្ម (Interactive Video Question)
                        if v_q and v_a and v_b and v_c:
                            st.markdown("---")
                            st.markdown(f"**🎬 សំណួរបំផុសគំនិតភ្ជាប់ជាមួយវីដេអូ/មេរៀនខាងលើ៖**")
                            st.write(v_q)
                            ans_choice = st.radio("ជ្រើសរើសចម្លើយរបស់អ្នក៖", [v_a, v_b, v_c], key=f"vq_radio_{l_id}")
                            if st.button("ផ្ទៀងផ្ទាត់ចម្លើយ", key=f"vq_btn_{l_id}"):
                                if ans_choice == v_corr:
                                    st.success("🎉 ត្រឹមត្រូវ! ពូកែណាស់!")
                                else:
                                    st.error(f"❌ មិនទាន់ត្រឹមត្រូវទេ។ សូមទស្សនាវីដេអូ ឬអានមេរៀនម្តងទៀត! (ចម្លើយត្រូវគឺ៖ {v_corr})")

        # ៤. ស្វ័យសិក្សា (Self-Study)
        with w_tabs[3]:
            st.subheader(f"🧭 សកម្មភាពស្វ័យសិក្សា - {selected_week}")
            c.execute("SELECT id, title, content, video_url, pdf_name, pdf_data FROM lessons WHERE week = ? AND category = 'ស្វ័យសិក្សា' ORDER BY id DESC", (selected_week,))
            self_data = c.fetchall()
            if not self_data:
                st.info(f"មិនទាន់មានកិច្ចការស្វ័យសិក្សាសម្រាប់ {selected_week} នៅឡើយទេ។")
            else:
                for s_id_item, title, content, video_url, pdf_name, pdf_data in self_data:
                    with st.expander(f"📝 {title}", expanded=True):
                        st.markdown(content, unsafe_allow_html=True)
                        if pdf_data and pdf_name:
                            st.download_button(f"📥 ទាញយកសន្លឹកកិច្ចការស្វ័យសិក្សា៖ {pdf_name}", data=pdf_data, file_name=pdf_name, mime="application/pdf", key=f"self_pdf_{s_id_item}")
                        if video_url:
                            st.video(video_url)

        # ៥. វេទិកាពិភាក្សា (Discussion Forum)
        with w_tabs[4]:
            st.subheader(f"💬 វេទិកាពិភាក្សាប្រចាំ {selected_week}")
            st.caption("សិស្សអាចសួរសំណួរ ចែករំលែកចំណេះដឹង ឬពិភាក្សាអំពីលំហាត់ពិបាកៗនៅទីនេះ៖")
            
            with st.form(f"forum_form_{selected_week}"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    f_class = st.selectbox("ថ្នាក់របស់អ្នក", CLASSES)
                with col_f2:
                    f_name = st.text_input("ឈ្មោះរបស់អ្នក")
                f_msg = st.text_area("សរសេរមតិយោបល់ ឬសំណួរពិភាក្សា...")
                if st.form_submit_button("📤 បង្ហោះចូលវេទិកា"):
                    if f_name.strip() and f_msg.strip():
                        today = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute("INSERT INTO forum (week, class_name, author_name, role_tag, message, date) VALUES (?, ?, ?, ?, ?, ?)",
                                  (selected_week, f_class, f_name.strip(), "សិស្ស", f_msg.strip(), today))
                        conn.commit()
                        st.success("បានបង្ហោះមតិពិភាក្សារួចរាល់!")
                        st.rerun()
                    else:
                        st.error("សូមបញ្ចូលឈ្មោះ និងខ្លឹមសារពិភាក្សា!")

            st.divider()
            c.execute("SELECT class_name, author_name, role_tag, message, date FROM forum WHERE week = ? ORDER BY id DESC", (selected_week,))
            posts = c.fetchall()
            if not posts:
                st.info("មិនទាន់មានការពិភាក្សានៅក្នុងសប្តាហ៍នេះនៅឡើយទេ។ សូមចាប់ផ្តើមមុនគេ!")
            else:
                for p_class, p_author, p_role, p_msg, p_date in posts:
                    badge = "👨‍🏫 គ្រូបង្រៀន" if p_role == "គ្រូ" else f"👨‍🎓 {p_class}"
                    st.markdown(f"**{p_author}** `[{badge}]` • *{p_date}*")
                    st.info(p_msg)

        # ៦. ការវាយតម្លៃ (Assessment / Quiz)
        with w_tabs[5]:
            st.subheader(f"✍️ ការវាយតម្លៃសមត្ថភាព - {selected_week}")
            num_q = int(get_setting('num_questions', '5'))
            state_key = f"quiz_questions_{selected_week}"
            if state_key not in st.session_state:
                c.execute("SELECT id, question, opt_a, opt_b, opt_c, correct_opt FROM quizzes WHERE week = ? ORDER BY RANDOM() LIMIT ?", (selected_week, num_q))
                st.session_state[state_key] = c.fetchall()
            questions = st.session_state[state_key]
            
            if not questions:
                st.info(f"មិនទាន់មានសំណួរវាយតម្លៃសម្រាប់ {selected_week} នៅឡើយទេ។")
            else:
                with st.form(f"quiz_form_{selected_week}"):
                    q_class = st.selectbox("ជ្រើសរើសថ្នាក់របស់អ្នក", CLASSES)
                    q_sid = st.text_input("អត្តលេខសិស្ស")
                    q_sname = st.text_input("ឈ្មោះសិស្ស")
                    st.divider()
                    user_answers = {}
                    for idx, (q_id, q_text, a, b, c_opt, correct) in enumerate(questions, 1):
                        user_answers[q_id] = st.radio(f"សំណួរទី {idx}៖ {q_text}", [a, b, c_opt], key=f"q_{selected_week}_{q_id}")
                    if st.form_submit_button("បញ្ជូនចម្លើយ និងមើលពិន្ទុ"):
                        if q_sid and q_sname:
                            score = sum(1 for q_id, _, _, _, _, correct in questions if user_answers[q_id] == correct)
                            total = len(questions)
                            today = datetime.now().strftime("%Y-%m-%d %H:%M")
                            c.execute("INSERT INTO scores (class_name, student_id, student_name, week, score, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                      (q_class, q_sid.strip(), q_sname.strip(), selected_week, score, total, today))
                            conn.commit()
                            st.success(f"🎉 អបអរសាទរ {q_sname} ({q_class})! ពិន្ទុវាយតម្លៃប្រចាំ {selected_week} គឺ៖ {score} / {total}")
                            del st.session_state[state_key]
                        else:
                            st.error("សូមបញ្ចូលអត្តលេខ និងឈ្មោះមុននឹងបញ្ជូនចម្លើយ!")

    # ------------------------------------------
    # ខ. បុរេតេស្ត (Pre-Test)
    # ------------------------------------------
    elif main_nav == "📝 បុរេតេស្ត (Pre-Test)":
        st.subheader("📝 បុរេតេស្ត (តេស្តវាស់ស្ទង់ចំណេះដឹងមូលដ្ឋានមុនចូលរៀន)")
        c.execute("SELECT id, question, opt_a, opt_b, opt_c, correct_opt FROM quizzes WHERE is_pretest = 1")
        pre_questions = c.fetchall()
        if not pre_questions:
            st.info("លោកគ្រូមិនទាន់បានកំណត់សំណួរសម្រាប់បុរេតេស្តនៅឡើយទេ។")
        else:
            with st.form("pretest_form"):
                p_class = st.selectbox("ជ្រើសរើសថ្នាក់របស់អ្នក", CLASSES)
                p_sid = st.text_input("អត្តលេខសិស្ស")
                p_sname = st.text_input("ឈ្មោះសិស្ស")
                st.divider()
                user_answers = {}
                for idx, (q_id, q_text, a, b, c_opt, correct) in enumerate(pre_questions, 1):
                    user_answers[q_id] = st.radio(f"សំណួរទី {idx}៖ {q_text}", [a, b, c_opt], key=f"pre_{q_id}")
                if st.form_submit_button("បញ្ជូនចម្លើយបុរេតេស្ត"):
                    if p_sid and p_sname:
                        score = sum(1 for q_id, _, _, _, _, correct in pre_questions if user_answers[q_id] == correct)
                        total = len(pre_questions)
                        today = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute("INSERT INTO scores (class_name, student_id, student_name, week, score, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (p_class, p_sid.strip(), p_sname.strip(), "បុរេតេស្ត (Pre-Test)", score, total, today))
                        conn.commit()
                        st.success(f"🎉 បានបញ្ជូនរួចរាល់! ពិន្ទុបុរេតេស្តរបស់ {p_sname} គឺ៖ {score} / {total}")
                    else:
                        st.error("សូមបញ្ចូលអត្តលេខ និងឈ្មោះ!")

    # ------------------------------------------
    # គ. តេស្តបញ្ចប់វគ្គ (Final Test)
    # ------------------------------------------
    elif main_nav == "🎓 តេស្តបញ្ចប់វគ្គ (Final Test)":
        st.subheader("🎓 តេស្តបញ្ចប់វគ្គសិក្សា (សំណួរចម្រុះគ្រប់សប្តាហ៍)")
        num_final = int(get_setting('final_questions', '15'))
        if "final_questions_list" not in st.session_state:
            c.execute("SELECT id, question, opt_a, opt_b, opt_c, correct_opt FROM quizzes ORDER BY RANDOM() LIMIT ?", (num_final,))
            st.session_state["final_questions_list"] = c.fetchall()
        f_questions = st.session_state["final_questions_list"]

        if not f_questions:
            st.info("មិនទាន់មានសំណួរក្នុងឃ្លាំងនៅឡើយទេ។")
        else:
            with st.form("final_test_form"):
                f_class = st.selectbox("ជ្រើសរើសថ្នាក់របស់អ្នក", CLASSES)
                f_sid = st.text_input("អត្តលេខសិស្ស")
                f_sname = st.text_input("ឈ្មោះសិស្ស")
                st.divider()
                user_answers = {}
                for idx, (q_id, q_text, a, b, c_opt, correct) in enumerate(f_questions, 1):
                    user_answers[q_id] = st.radio(f"សំណួរទី {idx}៖ {q_text}", [a, b, c_opt], key=f"fin_{q_id}")
                if st.form_submit_button("បញ្ជូនចម្លើយតេស្តបញ្ចប់វគ្គ"):
                    if f_sid and f_sname:
                        score = sum(1 for q_id, _, _, _, _, correct in f_questions if user_answers[q_id] == correct)
                        total = len(f_questions)
                        today = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute("INSERT INTO scores (class_name, student_id, student_name, week, score, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (f_class, f_sid.strip(), f_sname.strip(), "តេស្តបញ្ចប់វគ្គ (Final)", score, total, today))
                        conn.commit()
                        st.success(f"🏆 អបអរសាទរ {f_sname}! អ្នកបានបញ្ចប់វគ្គសិក្សាដោយទទួលបានពិន្ទុ៖ {score} / {total}")
                        del st.session_state["final_questions_list"]
                    else:
                        st.error("សូមបញ្ចូលអត្តលេខ និងឈ្មោះ!")

    # ------------------------------------------
    # ឃ. បណ្ណាល័យឯកសារ (Library)
    # ------------------------------------------
    elif main_nav == "🏛️ បណ្ណាល័យឯកសារ (Library)":
        st.subheader("🏛️ បណ្ណាល័យឯកសារជំនួយការសិក្សា (E-Library)")
        c.execute("SELECT id, title, description, pdf_name, pdf_data, date FROM library ORDER BY id DESC")
        lib_books = c.fetchall()
        if not lib_books:
            st.info("មិនទាន់មានឯកសារក្នុងបណ្ណាល័យនៅឡើយទេ។")
        else:
            for b_id, b_title, b_desc, b_pdf_name, b_pdf_data, b_date in lib_books:
                with st.expander(f"📕 {b_title} (បង្ហោះថ្ងៃទី៖ {b_date})", expanded=True):
                    st.write(b_desc)
                    if b_pdf_data and b_pdf_name:
                        st.download_button(f"📥 ទាញយកសៀវភៅ/ឯកសារ៖ {b_pdf_name}", data=b_pdf_data, file_name=b_pdf_name, mime="application/pdf", key=f"lib_dl_{b_id}")
                        with st.expander("👁️ អានឯកសារផ្ទាល់លើអេក្រង់"):
                            base64_pdf = base64.b64encode(b_pdf_data).decode('utf-8')
                            st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>', unsafe_allow_html=True)

# ==========================================
# ២. ផ្នែកសម្រាប់គ្រូ (TEACHER ADMIN)
# ==========================================
elif role == "👨‍🏫 ផ្នែកសម្រាប់គ្រូ (Teacher Admin)":
    password = st.sidebar.text_input("បញ្ចូលលេខសម្ងាត់គ្រូ", type="password")
    
    # ប្តូរលេខសម្ងាត់ "23101990lkk" ទៅជាលេខសម្ងាត់ផ្ទាល់ខ្លួនរបស់លោកគ្រូ
    if password == "23101990lkk":
        t_tabs = st.tabs([
            "📊 របាយការណ៍ពិន្ទុ និងវត្តមាន",
            "➕ រៀបចំមេរៀន (PLP Style)",
            "💬 ឆ្លើយតបវេទិកាពិភាក្សា",
            "🎯 ការរំពឹងទុក & ជូនដំណឹង",
            "🏛️ បណ្ណាល័យ",
            "🏦 ឃ្លាំងសំណួរ & តេស្ត"
        ])
        
        # --- ផ្ទាំងទី ១៖ របាយការណ៍ពិន្ទុ និងវត្តមាន ---
        with t_tabs[0]:
            filter_class = st.selectbox("🏫 ជ្រើសរើសថ្នាក់ដើម្បីមើលរបាយការណ៍៖", ["ទាំងអស់"] + CLASSES)
            st.subheader("១. តារាងបូកសរុបពិន្ទុគ្រប់ការធ្វើតេស្ត")
            if filter_class == "ទាំងអស់":
                df_scores = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS ប្រភេទតេស្ត, score AS ពិន្ទុបាន, total AS ពិន្ទុពេញ, date AS កាលបរិច្ឆេទ FROM scores", conn)
            else:
                df_scores = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS ប្រភេទតេស្ត, score AS ពិន្ទុបាន, total AS ពិន្ទុពេញ, date AS កាលបរិច្ឆេទ FROM scores WHERE class_name = ?", conn, params=(filter_class,))
            
            if not df_scores.empty:
                pivot_scores = df_scores.pivot_table(index=['ថ្នាក់', 'អត្តលេខ', 'ឈ្មោះសិស្ស'], columns='ប្រភេទតេស្ត', values='ពិន្ទុបាន', aggfunc='max', fill_value=0).reset_index()
                score_cols = [col for col in pivot_scores.columns if col not in ['ថ្នាក់', 'អត្តលេខ', 'ឈ្មោះសិស្ស']]
                pivot_scores['ពិន្ទុសរុបរួម'] = pivot_scores[score_cols].sum(axis=1)
                st.dataframe(pivot_scores, use_container_width=True)
                st.download_button(f"📥 ទាញយកតារាងពិន្ទុ ({filter_class}) - Excel/CSV", pivot_scores.to_csv(index=False).encode('utf-8-sig'), f"scores_{filter_class}.csv", "text/csv")
            else:
                st.info("មិនទាន់មានទិន្នន័យពិន្ទុនៅឡើយទេ។")

            st.divider()
            st.subheader("២. តារាងវត្តមានសិស្ស")
            if filter_class == "ទាំងអស់":
                df_att = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS សប្តាហ៍, status AS ស្ថានភាព, date AS កាលបរិច្ឆេទ FROM attendance", conn)
            else:
                df_att = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS សប្តាហ៍, status AS ស្ថានភាព, date AS កាលបរិច្ឆេទ FROM attendance WHERE class_name = ?", conn, params=(filter_class,))
            st.dataframe(df_att, use_container_width=True)
            if not df_att.empty:
                st.download_button(f"📥 ទាញយកបញ្ជីវត្តមាន ({filter_class})", df_att.to_csv(index=False).encode('utf-8-sig'), f"attendance_{filter_class}.csv", "text/csv")

        # --- ផ្ទាំងទី ២៖ រៀបចំខ្លឹមសារមេរៀនតាមប្រភេទ (សេចក្តីផ្តើម, ខ្លឹមសារមេរៀន/វីដេអូភ្ជាប់សំណួរ, ស្វ័យសិក្សា) ---
        with t_tabs[1]:
            st.subheader("➕ បញ្ចូលខ្លឹមសារសិក្សាប្រចាំសប្តាហ៍")
            l_week = st.selectbox("១. ជ្រើសរើសសប្តាហ៍៖", WEEKS, key="adm_l_week")
            l_category = st.selectbox("២. ជ្រើសរើសផ្នែក (Menu) ដែលត្រូវដាក់បង្ហាញ៖", ["សេចក្តីផ្តើម", "ខ្លឹមសារមេរៀន", "ស្វ័យសិក្សា"])
            l_title = st.text_input("៣. ចំណងជើង៖")
            
            st.write("៤. សរសេរខ្លឹមសារលម្អិត (អាចដាក់អក្សរដិត ចំណុចត្រេ តម្រឹមឆ្វេង កណ្តាល ស្តាំ)៖")
            l_content_html = st_quill(value="", html=True, key="lesson_quill")
            
            l_pdf = st.file_uploader("៥. ទម្លាក់ឯកសារអាន PDF (បើមាន)៖", type=["pdf"])
            l_video = st.text_input("៦. តំណភ្ជាប់វីដេអូ YouTube (បើមាន)៖")
            
            # មុខងារបន្ថែម៖ វីដេអូភ្ជាប់ជាមួយសំណួរអន្តរកម្ម
            add_vq = st.checkbox("🎬 ភ្ជាប់សំណួរអន្តរកម្មនៅខាងក្រោមវីដេអូ/មេរៀននេះ (Interactive Video Question)")
            v_q, v_a, v_b, v_c, v_corr = None, None, None, None, None
            if add_vq:
                v_q = st.text_input("សំណួរបំផុសគំនិតសម្រាប់វីដេអូ៖")
                col_v1, col_v2, col_v3 = st.columns(3)
                with col_v1: v_a = st.text_input("ជម្រើស ក (វីដេអូ)")
                with col_v2: v_b = st.text_input("ជម្រើស ខ (វីដេអូ)")
                with col_v3: v_c = st.text_input("ជម្រើស គ (វីដេអូ)")
                v_corr_choice = st.selectbox("ចម្លើយត្រូវសម្រាប់វីដេអូ៖", ["ជម្រើស ក", "ជម្រើស ខ", "ជម្រើស គ"])
                if v_a and v_b and v_c:
                    v_corr = {"ជម្រើស ក": v_a, "ជម្រើស ខ": v_b, "ជម្រើស គ": v_c}[v_corr_choice]

            if st.button("💾 រក្សាទុក និងបង្ហោះមេរៀន"):
                if l_title:
                    pdf_name = l_pdf.name if l_pdf else None
                    pdf_bytes = l_pdf.read() if l_pdf else None
                    c.execute('''INSERT INTO lessons (week, category, title, content, video_url, pdf_name, pdf_data, v_question, v_opt_a, v_opt_b, v_opt_c, v_correct) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                              (l_week, l_category, l_title, l_content_html, l_video, pdf_name, pdf_bytes, v_q, v_a, v_b, v_c, v_corr))
                    conn.commit()
                    st.success(f"បានបង្ហោះ «{l_title}» ចូលក្នុងផ្នែក [{l_category}] នៃ {l_week} ដោយជោគជ័យ!")
                else:
                    st.error("សូមបញ្ចូលចំណងជើង!")

        # --- ផ្ទាំងទី ៣៖ គ្រប់គ្រង និងឆ្លើយតបវេទិកាពិភាក្សា ---
        with t_tabs[2]:
            st.subheader("💬 វេទិកាពិភាក្សា (ឆ្លើយតបសំណួរសិស្ស)")
            f_week_admin = st.selectbox("ជ្រើសរើសសប្តាហ៍ដើម្បីមើលការពិភាក្សា៖", WEEKS, key="adm_f_week")
            with st.form("admin_forum_reply"):
                reply_msg = st.text_area("សរសេរការឆ្លើយតប ឬការណែនាំរបស់គ្រូទៅកាន់សិស្ស...")
                if st.form_submit_button("📢 បង្ហោះការឆ្លើយតបរបស់គ្រូ"):
                    if reply_msg.strip():
                        today = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute("INSERT INTO forum (week, class_name, author_name, role_tag, message, date) VALUES (?, ?, ?, ?, ?, ?)",
                                  (f_week_admin, "គ្រប់ថ្នាក់", "លោកគ្រូ (Admin)", "គ្រូ", reply_msg.strip(), today))
                        conn.commit()
                        st.success("បានបង្ហោះការឆ្លើយតបរួចរាល់!")
                        st.rerun()

            c.execute("SELECT id, class_name, author_name, role_tag, message, date FROM forum WHERE week = ? ORDER BY id DESC", (f_week_admin,))
            for fid, fcls, fauth, frole, fmsg, fdate in c.fetchall():
                col1, col2 = st.columns([6, 1])
                col1.markdown(f"**{fauth}** ({fcls} - {frole}) • *{fdate}*: {fmsg}")
                if col2.button("លុប", key=f"del_f_{fid}"):
                    c.execute("DELETE FROM forum WHERE id = ?", (fid,))
                    conn.commit()
                    st.rerun()

        # --- ផ្ទាំងទី ៤៖ ការរំពឹងទុកពីវគ្គសិក្សា និងសេចក្តីជូនដំណឹង ---
        with t_tabs[3]:
            st.subheader("🎯 កែសម្រួល «ការរំពឹងទុកពីវគ្គសិក្សា» (ឧបករណ៍ដូច Word)")
            current_exp = get_setting('course_expectation', '')
            content_html = st_quill(value=current_exp, html=True, key="quill_editor")
            if st.button("💾 រក្សាទុកការរំពឹងទុកពីវគ្គសិក្សា"):
                c.execute("UPDATE settings SET value = ? WHERE key = 'course_expectation'", (content_html,))
                conn.commit()
                st.success("បានរក្សាទុកដោយជោគជ័យ!")

            st.divider()
            st.subheader("🔔 បង្ហោះសេចក្តីជូនដំណឹងទៅកាន់សិស្ស")
            with st.form("notif_form"):
                n_msg = st.text_area("សរសេរខ្លឹមសារជូនដំណឹង")
                if st.form_submit_button("📢 បង្ហោះសេចក្តីជូនដំណឹង"):
                    if n_msg.strip():
                        today = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute("INSERT INTO notifications (message, date) VALUES (?, ?)", (n_msg.strip(), today))
                        conn.commit()
                        st.success("បានបង្ហោះសេចក្តីជូនដំណឹងរួចរាល់!")

        # --- ផ្ទាំងទី ៥៖ បណ្ណាល័យឯកសារ ---
        with t_tabs[4]:
            st.subheader("🏛️ បញ្ចូលឯកសារ PDF ទៅក្នុងបណ្ណាល័យរួម")
            with st.form("add_lib_form"):
                b_title = st.text_input("ចំណងជើងសៀវភៅ ឬឯកសារ")
                b_desc = st.text_area("ការពិពណ៌នាសង្ខេប")
                b_pdf = st.file_uploader("📄 ជ្រើសរើសឯកសារ PDF", type=["pdf"])
                if st.form_submit_button("បញ្ចូលទៅក្នុងបណ្ណាល័យ"):
                    if b_title and b_pdf:
                        today = datetime.now().strftime("%Y-%m-%d")
                        c.execute("INSERT INTO library (title, description, pdf_name, pdf_data, date) VALUES (?, ?, ?, ?, ?)",
                                  (b_title, b_desc, b_pdf.name, b_pdf.read(), today))
                        conn.commit()
                        st.success("បានបញ្ចូលឯកសារទៅក្នុងបណ្ណាល័យរួចរាល់!")

        # --- ផ្ទាំងទី ៦៖ ឃ្លាំងសំណួរ បុរេតេស្ត និងតេស្តបញ្ចប់ ---
        with t_tabs[5]:
            st.subheader("📤 បញ្ចូលសំណួរច្រើនក្នុងពេលតែមួយ (Upload CSV/Excel)")
            sample_df = pd.DataFrame({
                "week": ["សប្តាហ៍ទី ១", "សប្តាហ៍ទី ២"],
                "question": ["តើ 2 + 3 ស្មើប៉ុន្មាន?", "តើរូបមន្តក្រឡាផ្ទៃការ៉េគឺជាអ្វី?"],
                "opt_a": ["4", "S = a × a"],
                "opt_b": ["5", "S = 4 × a"],
                "opt_c": ["6", "S = a + b"],
                "correct_opt": ["5", "S = a × a"]
            })
            st.download_button("📥 ទាញយកតារាងគំរូ (Template.csv)", sample_df.to_csv(index=False).encode('utf-8-sig'), "quiz_template.csv", "text/csv")

            uploaded_csv = st.file_uploader("ជ្រើសរើសឯកសារ CSV", type=["csv"])
            if uploaded_csv is not None:
                if st.button("🚀 បញ្ចូលសំណួរទាំងអស់ពីឯកសារនេះ"):
                    try:
                        df_up = pd.read_csv(uploaded_csv)
                        count = 0
                        for _, row in df_up.iterrows():
                            c.execute("INSERT INTO quizzes (week, question, opt_a, opt_b, opt_c, correct_opt) VALUES (?, ?, ?, ?, ?, ?)",
                                      (str(row['week']).strip(), str(row['question']).strip(), str(row['opt_a']).strip(), str(row['opt_b']).strip(), str(row['opt_c']).strip(), str(row['correct_opt']).strip()))
                            count += 1
                        conn.commit()
                        st.success(f"🎉 បានបញ្ចូលសំណួរចំនួន {count} ដោយជោគជ័យ!")
                    except Exception as e:
                        st.error(f"កំហុស៖ {e}")

            st.divider()
            st.subheader("📝 ជ្រើសរើសសំណួរដាក់ចូលក្នុង «បុរេតេស្ត (Pre-Test)»")
            df_all_q = pd.read_sql_query("SELECT id, week, question, correct_opt, is_pretest FROM quizzes", conn)
            if not df_all_q.empty:
                selected_pre_ids = []
                for _, row in df_all_q.iterrows():
                    if st.checkbox(f"[{row['week']}] {row['question']} (ត្រូវ៖ {row['correct_opt']})", value=bool(row['is_pretest'] == 1), key=f"chk_pre_{row['id']}"):
                        selected_pre_ids.append(row['id'])
                if st.button("💾 រក្សាទុកវិញ្ញាសាបុរេតេស្ត"):
                    c.execute("UPDATE quizzes SET is_pretest = 0")
                    for qid in selected_pre_ids:
                        c.execute("UPDATE quizzes SET is_pretest = 1 WHERE id = ?", (qid,))
                    conn.commit()
                    st.success("បានរក្សាទុកវិញ្ញាសាបុរេតេស្តរួចរាល់!")

            st.divider()
            st.subheader("⚙️ កំណត់ចំនួនសំណួរតេស្តប្រចាំសប្តាហ៍ និងតេស្តបញ្ចប់វគ្គ")
            col_a, col_b = st.columns(2)
            with col_a:
                w_num = st.number_input("ចំនួនសំណួរតេស្តប្រចាំសប្តាហ៍៖", min_value=1, max_value=50, value=int(get_setting('num_questions', '5')))
            with col_b:
                f_num = st.number_input("ចំនួនសំណួរតេស្តបញ្ចប់វគ្គ៖", min_value=1, max_value=100, value=int(get_setting('final_questions', '15')))
            if st.button("រក្សាទុកការកំណត់"):
                c.execute("UPDATE settings SET value = ? WHERE key = 'num_questions'", (str(w_num),))
                c.execute("UPDATE settings SET value = ? WHERE key = 'final_questions'", (str(f_num),))
                conn.commit()
                st.success("បានរក្សាទុកការកំណត់រួចរាល់!")
    else:
        st.warning("សូមបញ្ចូលលេខសម្ងាត់គ្រូនៅរបារខាងឆ្វេង ដើម្បីចូលគ្រប់គ្រងទិន្នន័យ។")
