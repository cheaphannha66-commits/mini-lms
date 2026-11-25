import streamlit as st
import sqlite3
import pandas as pd
import base64
from datetime import datetime
from streamlit_quill import st_quill

# កំណត់រចនាសម្ព័ន្ធទំព័រ
st.set_page_config(page_title="ចំណេះដឹងគណិតវិទ្យា", page_icon="📐", layout="wide")

# បង្កើត និងភ្ជាប់ Database (SQLite)
conn = sqlite3.connect('school_lms.db', check_same_thread=False)
c = conn.cursor()

# បញ្ជីសប្តាហ៍ទាំង ៥ និងបញ្ជីថ្នាក់
WEEKS = ["សប្តាហ៍ទី ១", "សប្តាហ៍ទី ២", "សប្តាហ៍ទី ៣", "សប្តាហ៍ទី ៤", "សប្តាហ៍ទី ៥"]
CLASSES = ["ថ្នាក់ ក", "ថ្នាក់ ខ", "ថ្នាក់ គ"]

# បង្កើត និងអាប់ដេតតារាងទិន្នន័យ (រក្សាទុកទិន្នន័យចាស់ ១០០%)
def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, class_name TEXT, student_id TEXT, student_name TEXT, week TEXT, date TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lessons 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, week TEXT, title TEXT, content TEXT, video_url TEXT, pdf_name TEXT, pdf_data BLOB)''')
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

    # អាប់ដេតជួរឈរសម្រាប់តារាងចាស់ៗ
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
    if 'pdf_name' not in l_cols:
        c.execute("ALTER TABLE lessons ADD COLUMN pdf_name TEXT")
    if 'pdf_data' not in l_cols:
        c.execute("ALTER TABLE lessons ADD COLUMN pdf_data BLOB")

    c.execute("PRAGMA table_info(quizzes)")
    q_cols = [col[1] for col in c.fetchall()]
    if 'is_pretest' not in q_cols:
        c.execute("ALTER TABLE quizzes ADD COLUMN is_pretest INTEGER DEFAULT 0")

    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('num_questions', '5')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('final_questions', '15')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('course_expectation', '<p>សូមស្វាគមន៍មកកាន់វគ្គសិក្សា <b>ចំណេះដឹងគណិតវិទ្យា</b>!</p>')")
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

st.title("📐 ចំណេះដឹងគណិតវិទ្យា")

# ម៉ឺនុយជ្រើសរើសតួនាទី (សិស្ស ឬ គ្រូ)
role = st.sidebar.selectbox("ជ្រើសរើសតួនាទីប្រើប្រាស់៖", ["👨‍🎓 ផ្នែកសម្រាប់សិស្ស (Student)", "👨‍🏫 ផ្នែកសម្រាប់គ្រូ (Teacher Admin)"])

# ==========================================
# ១. ផ្នែកសម្រាប់សិស្ស (STUDENT PORTAL)
# ==========================================
if role == "👨‍🎓 ផ្នែកសម្រាប់សិស្ស (Student)":
    # បង្ហាញសេចក្តីជូនដំណឹង (Notification) នៅផ្នែកខាងលើបង្អស់
    c.execute("SELECT message, date FROM notifications ORDER BY id DESC LIMIT 3")
    notifs = c.fetchall()
    if notifs:
        for msg, n_date in notifs:
            st.info(f"🔔 **សេចក្តីជូនដំណឹង ({n_date})៖** {msg}")

    # បង្ហាញការរំពឹងទុកពីវគ្គសិក្សា
    with st.expander("🎯 ការរំពឹងទុក និងគោលបំណងនៃវគ្គសិក្សា (សូមអានមុនចាប់ផ្តើម)", expanded=False):
        expectation_html = get_setting('course_expectation', '')
        st.markdown(expectation_html, unsafe_allow_html=True)

    # ម៉ឺនុយមេសម្រាប់សិស្ស
    main_nav = st.radio(
        "ជ្រើសរើសផ្នែកសិក្សា៖",
        ["📅 មេរៀន និងតេស្តប្រចាំសប្តាហ៍", "📝 បុរេតេស្ត (Pre-Test)", "🎓 តេស្តបញ្ចប់វគ្គ (Final Test)", "🏛️ បណ្ណាល័យឯកសារ (Library)"],
        horizontal=True
    )
    st.divider()

    # ------------------------------------------
    # ក. មេរៀន និងតេស្តប្រចាំសប្តាហ៍ (១ ដល់ ៥)
    # ------------------------------------------
    if main_nav == "📅 មេរៀន និងតេស្តប្រចាំសប្តាហ៍":
        selected_week = st.selectbox("ជ្រើសរើសសប្តាហ៍សិក្សា៖", WEEKS)
        tab1, tab2, tab3 = st.tabs(["✅ ចុះវត្តមាន", "📚 មេរៀនស្វ័យសិក្សា", "✍️ ធ្វើតេស្តប្រចាំសប្តាហ៍"])

        with tab1:
            st.subheader(f"ចុះវត្តមានប្រចាំ {selected_week}")
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

        with tab2:
            st.subheader(f"មេរៀនស្វ័យសិក្សា - {selected_week}")
            c.execute("SELECT id, title, content, video_url, pdf_name, pdf_data FROM lessons WHERE week = ? ORDER BY id DESC", (selected_week,))
            lessons_data = c.fetchall()
            if not lessons_data:
                st.info(f"មិនទាន់មានមេរៀនសម្រាប់ {selected_week} នៅឡើយទេ។")
            else:
                for l_id, title, content, video_url, pdf_name, pdf_data in lessons_data:
                    with st.expander(f"📖 {title}", expanded=True):
                        st.write(content)
                        if pdf_data and pdf_name:
                            st.download_button(f"📥 ទាញយកឯកសារ PDF៖ {pdf_name}", data=pdf_data, file_name=pdf_name, mime="application/pdf", key=f"dl_pdf_{l_id}")
                            with st.expander("👁️ ចុចទីនេះដើម្បីអានឯកសារ PDF ផ្ទាល់"):
                                base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                                st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>', unsafe_allow_html=True)
                        if video_url:
                            st.video(video_url)

        with tab3:
            st.subheader(f"តេស្តវាស់ស្ទង់សមត្ថភាព - {selected_week}")
            num_q = int(get_setting('num_questions', '5'))
            state_key = f"quiz_questions_{selected_week}"
            if state_key not in st.session_state:
                c.execute("SELECT id, question, opt_a, opt_b, opt_c, correct_opt FROM quizzes WHERE week = ? ORDER BY RANDOM() LIMIT ?", (selected_week, num_q))
                st.session_state[state_key] = c.fetchall()
            questions = st.session_state[state_key]
            
            if not questions:
                st.info(f"មិនទាន់មានសំណួរតេស្តសម្រាប់ {selected_week} នៅឡើយទេ។")
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
                            st.success(f"🎉 អបអរសាទរ {q_sname} ({q_class})! ពិន្ទុសម្រាប់ {selected_week} របស់អ្នកគឺ៖ {score} / {total}")
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
            st.caption(f"តេស្តបញ្ចប់វគ្គនេះមានសំណួរចម្រុះចំនួន {len(f_questions)} សំណួរ ដែលចាប់យកពីគ្រប់សប្តាហ៍។")
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
            "🎯 ការរំពឹងទុក និងជូនដំណឹង",
            "➕ បង្ហោះមេរៀន",
            "🏛️ បណ្ណាល័យ (Library)",
            "🏦 ឃ្លាំងសំណួរ (Upload/បញ្ចូល)",
            "⚙️ រៀបចំបុរេតេស្ត & តេស្តបញ្ចប់"
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
                
                csv_summary = pivot_scores.to_csv(index=False).encode('utf-8-sig')
                st.download_button(f"📥 ទាញយកតារាងពិន្ទុ ({filter_class}) - Excel/CSV", csv_summary, f"scores_{filter_class}.csv", "text/csv")
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

        # --- ផ្ទាំងទី ២៖ ការរំពឹងទុកពីវគ្គសិក្សា (Word Editor) និងសេចក្តីជូនដំណឹង ---
        with t_tabs[1]:
            st.subheader("🎯 កែសម្រួល «ការរំពឹងទុកពីវគ្គសិក្សា» (ឧបករណ៍ដូច Word)")
            st.caption("លោកគ្រូអាចប្រើប៊ូតុងខាងក្រោមដើម្បីដាក់អក្សរដិត ទំហំអក្សរ ចំណុចត្រេ ឬតម្រឹមឆ្វេង កណ្តាល ស្តាំ៖")
            current_exp = get_setting('course_expectation', '')
            content_html = st_quill(value=current_exp, html=True, key="quill_editor")
            if st.button("💾 រក្សាទុកការរំពឹងទុកពីវគ្គសិក្សា"):
                c.execute("UPDATE settings SET value = ? WHERE key = 'course_expectation'", (content_html,))
                conn.commit()
                st.success("បានរក្សាទុកខ្លឹមសារការរំពឹងទុកពីវគ្គសិក្សាដោយជោគជ័យ!")

            st.divider()
            st.subheader("🔔 បង្ហោះសេចក្តីជូនដំណឹងទៅកាន់សិស្ស (Notification)")
            with st.form("notif_form"):
                n_msg = st.text_area("សរសេរខ្លឹមសារជូនដំណឹង (ឧ. សូមសិស្សទាំងអស់ធ្វើតេស្តសប្តាហ៍ទី ២ ឲ្យបានមុនថ្ងៃសៅរ៍)")
                if st.form_submit_button("📢 បង្ហោះសេចក្តីជូនដំណឹង"):
                    if n_msg.strip():
                        today = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute("INSERT INTO notifications (message, date) VALUES (?, ?)", (n_msg.strip(), today))
                        conn.commit()
                        st.success("បានបង្ហោះសេចក្តីជូនដំណឹងទៅកាន់អេក្រង់សិស្សរួចរាល់!")

            c.execute("SELECT id, message, date FROM notifications ORDER BY id DESC")
            all_notifs = c.fetchall()
            if all_notifs:
                st.write("**ប្រវត្តិសេចក្តីជូនដំណឹង៖**")
                for nid, nmsg, ndate in all_notifs:
                    col1, col2 = st.columns([5, 1])
                    col1.write(f"- [{ndate}] {nmsg}")
                    if col2.button("លុប", key=f"del_n_{nid}"):
                        c.execute("DELETE FROM notifications WHERE id = ?", (nid,))
                        conn.commit()
                        st.rerun()

        # --- ផ្ទាំងទី ៣៖ បង្ហោះមេរៀនតាមសប្តាហ៍ ---
        with t_tabs[2]:
            st.subheader("➕ បន្ថែមមេរៀនស្វ័យសិក្សាប្រចាំសប្តាហ៍")
            with st.form("add_lesson_form"):
                l_week = st.selectbox("ជ្រើសរើសសប្តាហ៍", WEEKS)
                l_title = st.text_input("ចំណងជើងមេរៀន")
                l_content = st.text_area("ខ្លឹមសារមេរៀន / សេចក្តីណែនាំ")
                l_pdf = st.file_uploader("📄 ទម្លាក់ឯកសារមេរៀន PDF (បើមាន)", type=["pdf"])
                l_video = st.text_input("តំណភ្ជាប់វីដេអូ YouTube (បើមាន)")
                if st.form_submit_button("រក្សាទុកមេរៀន"):
                    if l_title and l_content:
                        pdf_name = l_pdf.name if l_pdf else None
                        pdf_bytes = l_pdf.read() if l_pdf else None
                        c.execute("INSERT INTO lessons (week, title, content, video_url, pdf_name, pdf_data) VALUES (?, ?, ?, ?, ?, ?)", 
                                  (l_week, l_title, l_content, l_video, pdf_name, pdf_bytes))
                        conn.commit()
                        st.success(f"បានបង្ហោះមេរៀនចូលក្នុង {l_week} ដោយជោគជ័យ!")

        # --- ផ្ទាំងទី ៤៖ បណ្ណាល័យឯកសារ (Library) ---
        with t_tabs[3]:
            st.subheader("🏛️ បញ្ចូលឯកសារ PDF ទៅក្នុងបណ្ណាល័យរួម")
            with st.form("add_lib_form"):
                b_title = st.text_input("ចំណងជើងសៀវភៅ ឬឯកសារ")
                b_desc = st.text_area("ការពិពណ៌នាសង្ខេបអំពីឯកសារ")
                b_pdf = st.file_uploader("📄 ជ្រើសរើសឯកសារ PDF", type=["pdf"])
                if st.form_submit_button("បញ្ចូលទៅក្នុងបណ្ណាល័យ"):
                    if b_title and b_pdf:
                        today = datetime.now().strftime("%Y-%m-%d")
                        c.execute("INSERT INTO library (title, description, pdf_name, pdf_data, date) VALUES (?, ?, ?, ?, ?)",
                                  (b_title, b_desc, b_pdf.name, b_pdf.read(), today))
                        conn.commit()
                        st.success("បានបញ្ចូលឯកសារទៅក្នុងបណ្ណាល័យដោយជោគជ័យ!")
                    else:
                        st.error("សូមបញ្ចូលចំណងជើង និងជ្រើសរើសឯកសារ PDF!")

        # --- ផ្ទាំងទី ៥៖ ឃ្លាំងសំណួរ (Bulk Upload CSV ឬ បញ្ចូលម្តងមួយ) ---
        with t_tabs[4]:
            st.subheader("📤 បញ្ចូលសំណួរច្រើនក្នុងពេលតែមួយ (Upload CSV/Excel)")
            st.info("លោកគ្រូអាចទាញយកតារាងគំរូខាងក្រោម វាយសំណួរច្រើនក្នុង Excel រួចរក្សាទុកជា CSV (UTF-8) ហើយ Upload ចូលតែម្តង!")
            
            # បង្កើតឯកសារគំរូសម្រាប់ឲ្យគ្រូ Download
            sample_df = pd.DataFrame({
                "week": ["សប្តាហ៍ទី ១", "សប្តាហ៍ទី ២"],
                "question": ["តើ 2 + 3 ស្មើប៉ុន្មាន?", "តើរូបមន្តក្រឡាផ្ទៃការ៉េគឺជាអ្វី?"],
                "opt_a": ["4", "S = a × a"],
                "opt_b": ["5", "S = 4 × a"],
                "opt_c": ["6", "S = a + b"],
                "correct_opt": ["5", "S = a × a"]
            })
            st.download_button("📥 ទាញយកតារាងគំរូ (Template.csv)", sample_df.to_csv(index=False).encode('utf-8-sig'), "quiz_template.csv", "text/csv")

            uploaded_csv = st.file_uploader("ជ្រើសរើសឯកសារ CSV ដែលមានសំណួររបស់លោកគ្រូ", type=["csv"])
            if uploaded_csv is not None:
                if st.button("🚀 បញ្ចូលសំណួរទាំងអស់ពីឯកសារនេះទៅក្នុងឃ្លាំង"):
                    try:
                        df_up = pd.read_csv(uploaded_csv)
                        count = 0
                        for _, row in df_up.iterrows():
                            c.execute("INSERT INTO quizzes (week, question, opt_a, opt_b, opt_c, correct_opt) VALUES (?, ?, ?, ?, ?, ?)",
                                      (str(row['week']).strip(), str(row['question']).strip(), str(row['opt_a']).strip(), str(row['opt_b']).strip(), str(row['opt_c']).strip(), str(row['correct_opt']).strip()))
                            count += 1
                        conn.commit()
                        st.success(f"🎉 ជោគជ័យ! បានបញ្ចូលសំណួរចំនួន {count} ទៅក្នុងឃ្លាំងសំណួររួចរាល់!")
                    except Exception as e:
                        st.error(f"មានបញ្ហាក្នុងការអានឯកសារ៖ {e} (សូមប្រាកដថាឈ្មោះជួរឈរដូចក្នុងតារាងគំរូ)")

            st.divider()
            with st.expander("➕ ឬបញ្ចូលសំណួរម្តងមួយដោយផ្ទាល់"):
                with st.form("add_quiz_form"):
                    q_week = st.selectbox("ជ្រើសរើសសប្តាហ៍", WEEKS)
                    q_text = st.text_input("សំណួរ")
                    opt_a = st.text_input("ជម្រើស ក")
                    opt_b = st.text_input("ជម្រើស ខ")
                    opt_c = st.text_input("ជម្រើស គ")
                    correct = st.selectbox("ចម្លើយដែលត្រឹមត្រូវ", ["ជម្រើស ក", "ជម្រើស ខ", "ជម្រើស គ"])
                    if st.form_submit_button("បញ្ចូលសំណួរ"):
                        if q_text and opt_a and opt_b and opt_c:
                            ans_map = {"ជម្រើស ក": opt_a, "ជម្រើស ខ": opt_b, "ជម្រើស គ": opt_c}
                            c.execute("INSERT INTO quizzes (week, question, opt_a, opt_b, opt_c, correct_opt) VALUES (?, ?, ?, ?, ?, ?)",
                                      (q_week, q_text, opt_a, opt_b, opt_c, ans_map[correct]))
                            conn.commit()
                            st.success("បានបញ្ចូលសំណួររួចរាល់!")

        # --- ផ្ទាំងទី ៦៖ រៀបចំបុរេតេស្ត (Pre-Test) និងតេស្តបញ្ចប់វគ្គ ---
        with t_tabs[5]:
            st.subheader("📝 ជ្រើសរើសសំណួរពីគ្រប់សប្តាហ៍ដាក់ចូលក្នុង «បុរេតេស្ត (Pre-Test)»")
            df_all_q = pd.read_sql_query("SELECT id, week, question, correct_opt, is_pretest FROM quizzes", conn)
            
            if not df_all_q.empty:
                st.caption("ធីក (✓) ក្នុងប្រអប់ខាងមុខសំណួរណាដែលលោកគ្រូចង់ដាក់ក្នុងបុរេតេស្ត រួចចុចប៊ូតុងរក្សាទុក៖")
                selected_pre_ids = []
                for _, row in df_all_q.iterrows():
                    is_checked = bool(row['is_pretest'] == 1)
                    if st.checkbox(f"[{row['week']}] {row['question']} (ចម្លើយ៖ {row['correct_opt']})", value=is_checked, key=f"chk_pre_{row['id']}"):
                        selected_pre_ids.append(row['id'])
                
                if st.button("💾 រក្សាទុកវិញ្ញាសាបុរេតេស្ត"):
                    c.execute("UPDATE quizzes SET is_pretest = 0")
                    for qid in selected_pre_ids:
                        c.execute("UPDATE quizzes SET is_pretest = 1 WHERE id = ?", (qid,))
                    conn.commit()
                    st.success(f"បានកំណត់សំណួរចំនួន {len(selected_pre_ids)} សម្រាប់បុរេតេស្តដោយជោគជ័យ!")
            else:
                st.info("មិនទាន់មានសំណួរក្នុងឃ្លាំងនៅឡើយទេ។")

            st.divider()
            st.subheader("🎓 កំណត់ចំនួនសំណួរសម្រាប់ «តេស្តបញ្ចប់វគ្គ (Final Test)» និង «តេស្តប្រចាំសប្តាហ៍»")
            col_a, col_b = st.columns(2)
            with col_a:
                w_num = st.number_input("ចំនួនសំណួរតេស្តប្រចាំសប្តាហ៍៖", min_value=1, max_value=50, value=int(get_setting('num_questions', '5')))
            with col_b:
                f_num = st.number_input("ចំនួនសំណួរតេស្តបញ្ចប់វគ្គ (ចាប់ចម្រុះគ្រប់សប្តាហ៍)៖", min_value=1, max_value=100, value=int(get_setting('final_questions', '15')))
            
            if st.button("រក្សាទុកចំនួនសំណួរ"):
                c.execute("UPDATE settings SET value = ? WHERE key = 'num_questions'", (str(w_num),))
                c.execute("UPDATE settings SET value = ? WHERE key = 'final_questions'", (str(f_num),))
                conn.commit()
                st.success("បានរក្សាទុកការកំណត់រួចរាល់!")
    else:
        st.warning("សូមបញ្ចូលលេខសម្ងាត់គ្រូនៅរបារខាងឆ្វេង ដើម្បីចូលគ្រប់គ្រងទិន្នន័យ។")
