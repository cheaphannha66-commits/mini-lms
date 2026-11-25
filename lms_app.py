import streamlit as st
import sqlite3
import pandas as pd
import base64
from datetime import datetime

# កំណត់រចនាសម្ព័ន្ធទំព័រ
st.set_page_config(page_title="ចំណេះដឹងគណិតវិទ្យា", page_icon="📐", layout="wide")

# បង្កើត និងភ្ជាប់ Database (SQLite)
conn = sqlite3.connect('school_lms.db', check_same_thread=False)
c = conn.cursor()

# បញ្ជីសប្តាហ៍ទាំង ៥ និងបញ្ជីថ្នាក់ (លោកគ្រូអាចបន្ថែម ឬកែឈ្មោះថ្នាក់នៅទីនេះ)
WEEKS = ["សប្តាហ៍ទី ១", "សប្តាហ៍ទី ២", "សប្តាហ៍ទី ៣", "សប្តាហ៍ទី ៤", "សប្តាហ៍ទី ៥"]
CLASSES = ["ថ្នាក់ ក", "ថ្នាក់ ខ", "ថ្នាក់ គ"]

# បង្កើតតារាងទិន្នន័យ (Tables) និងអាប់ដេតជួរឈរដោយមិនប៉ះពាល់ទិន្នន័យចាស់
def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, class_name TEXT, student_id TEXT, student_name TEXT, week TEXT, date TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lessons 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, week TEXT, title TEXT, content TEXT, video_url TEXT, pdf_name TEXT, pdf_data BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS quizzes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, week TEXT, question TEXT, opt_a TEXT, opt_b TEXT, opt_c TEXT, correct_opt TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, class_name TEXT, student_id TEXT, student_name TEXT, week TEXT, score INTEGER, total INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings 
                 (key TEXT PRIMARY KEY, value TEXT)''')

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
    if 'pdf_name' not in l_cols:
        c.execute("ALTER TABLE lessons ADD COLUMN pdf_name TEXT")
    if 'pdf_data' not in l_cols:
        c.execute("ALTER TABLE lessons ADD COLUMN pdf_data BLOB")

    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('num_questions', '5')")
    conn.commit()

init_db()

def get_num_questions():
    c.execute("SELECT value FROM settings WHERE key='num_questions'")
    res = c.fetchone()
    return int(res[0]) if res else 5

# រចនាម៉ូដអក្សរខ្មែរ (Battambang) និងលាក់របារ GitHub ខាងលើ
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Battambang:wght@400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Battambang', sans-serif; }
    [data-testid="stToolbar"] { visibility: hidden; display: none; }
    header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

st.title("📐 ចំណេះដឹងគណិតវិទ្យា (កម្មវិធីសិក្សា ៥ សប្តាហ៍)")

# ម៉ឺនុយជ្រើសរើសតួនាទី (សិស្ស ឬ គ្រូ)
role = st.sidebar.selectbox("ជ្រើសរើសតួនាទីប្រើប្រាស់៖", ["👨‍🎓 ផ្នែកសម្រាប់សិស្ស (Student)", "👨‍🏫 ផ្នែកសម្រាប់គ្រូ (Teacher Admin)"])

# ==========================================
# ១. ផ្នែកសម្រាប់សិស្ស (STUDENT PORTAL)
# ==========================================
if role == "👨‍🎓 ផ្នែកសម្រាប់សិស្ស (Student)":
    selected_week = st.selectbox("📅 ជ្រើសរើសសប្តាហ៍សិក្សា៖", WEEKS)
    st.divider()

    tab1, tab2, tab3 = st.tabs(["✅ ចុះវត្តមាន", "📚 មេរៀនស្វ័យសិក្សា", "📝 ធ្វើតេស្តសមត្ថភាព"])

    # --- ផ្ទាំងទី ១៖ សិស្សចុះវត្តមាន (បញ្ជាក់ថ្នាក់) ---
    with tab1:
        st.subheader(f"ចុះវត្តមានប្រចាំ {selected_week}")
        with st.form("attendance_form"):
            s_class = st.selectbox("ជ្រើសរើសថ្នាក់របស់អ្នក", CLASSES)
            s_id = st.text_input("អត្តលេខសិស្ស (ឧ. S001)")
            s_name = st.text_input("គោត្តនាម និងនាម")
            status = st.selectbox("ស្ថានភាព", ["វត្តមាន", "សុំច្បាប់"])
            submitted = st.form_submit_button("បញ្ជូនវត្តមាន")
            
            if submitted:
                if s_id and s_name:
                    today = datetime.now().strftime("%Y-%m-%d %H:%M")
                    c.execute("INSERT INTO attendance (class_name, student_id, student_name, week, date, status) VALUES (?, ?, ?, ?, ?, ?)",
                              (s_class, s_id.strip(), s_name.strip(), selected_week, today, status))
                    conn.commit()
                    st.success(f"ជោគជ័យ! បានកត់ត្រាវត្តមានសម្រាប់ {s_name} ({s_class} - {selected_week}) រួចរាល់។")
                else:
                    st.error("សូមបញ្ចូលអត្តលេខ និងឈ្មោះរបស់អ្នក!")

    # --- ផ្ទាំងទី ២៖ មេរៀនស្វ័យសិក្សាតាមសប្តាហ៍ ---
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
                        st.download_button(
                            label=f"📥 ទាញយកឯកសារ PDF៖ {pdf_name}",
                            data=pdf_data,
                            file_name=pdf_name,
                            mime="application/pdf",
                            key=f"dl_pdf_{l_id}"
                        )
                        with st.expander("👁️ ចុចទីនេះដើម្បីអានឯកសារ PDF ផ្ទាល់"):
                            base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                    if video_url:
                        st.video(video_url)

    # --- ផ្ទាំងទី ៣៖ ធ្វើតេស្ត (បញ្ជាក់ថ្នាក់) ---
    with tab3:
        st.subheader(f"តេស្តវាស់ស្ទង់សមត្ថភាព - {selected_week}")
        num_q = get_num_questions()
        
        state_key = f"quiz_questions_{selected_week}"
        if state_key not in st.session_state:
            c.execute("SELECT id, question, opt_a, opt_b, opt_c, correct_opt FROM quizzes WHERE week = ? ORDER BY RANDOM() LIMIT ?", (selected_week, num_q))
            st.session_state[state_key] = c.fetchall()
            
        questions = st.session_state[state_key]
        
        if not questions:
            st.info(f"មិនទាន់មានសំណួរតេស្តសម្រាប់ {selected_week} នៅឡើយទេ។")
        else:
            st.caption(f"ប្រព័ន្ធបានចាប់យកសំណួរចំនួន {len(questions)} ដោយចៃដន្យពីឃ្លាំងសំណួររបស់ {selected_week}។")
            with st.form(f"quiz_form_{selected_week}"):
                q_class = st.selectbox("ជ្រើសរើសថ្នាក់របស់អ្នក", CLASSES)
                q_sid = st.text_input("អត្តលេខសិស្ស")
                q_sname = st.text_input("ឈ្មោះសិស្ស")
                st.divider()
                
                user_answers = {}
                for idx, (q_id, q_text, a, b, c_opt, correct) in enumerate(questions, 1):
                    user_answers[q_id] = st.radio(f"សំណួរទី {idx}៖ {q_text}", [a, b, c_opt], key=f"q_{selected_week}_{q_id}")
                
                quiz_submit = st.form_submit_button("បញ្ជូនចម្លើយ និងមើលពិន្ទុ")
                
                if quiz_submit:
                    if q_sid and q_sname:
                        score = 0
                        total = len(questions)
                        for q_id, q_text, a, b, c_opt, correct in questions:
                            if user_answers[q_id] == correct:
                                score += 1
                        
                        today = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute("INSERT INTO scores (class_name, student_id, student_name, week, score, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (q_class, q_sid.strip(), q_sname.strip(), selected_week, score, total, today))
                        conn.commit()
                        st.success(f"🎉 អបអរសាទរ {q_sname} ({q_class})! ពិន្ទុសម្រាប់ {selected_week} របស់អ្នកគឺ៖ {score} / {total}")
                        del st.session_state[state_key]
                    else:
                        st.error("សូមបញ្ចូលអត្តលេខ និងឈ្មោះមុននឹងបញ្ជូនចម្លើយ!")

# ==========================================
# ២. ផ្នែកសម្រាប់គ្រូ (TEACHER ADMIN)
# ==========================================
elif role == "👨‍🏫 ផ្នែកសម្រាប់គ្រូ (Teacher Admin)":
    password = st.sidebar.text_input("បញ្ចូលលេខសម្ងាត់គ្រូ", type="password")
    
    # ប្តូរលេខសម្ងាត់ "23101990lkk" ទៅជាលេខសម្ងាត់ផ្ទាល់ខ្លួនរបស់លោកគ្រូ
    if password == "23101990lkk":
        t_tab1, t_tab2, t_tab3 = st.tabs(["📊 របាយការណ៍វត្តមាន និងពិន្ទុតាមថ្នាក់", "➕ បង្ហោះមេរៀនតាមសប្តាហ៍", "🏦 ឃ្លាំងសំណួរ (Question Bank)"])
        
        # --- ផ្ទាំងទី ១៖ បូកសរុបវត្តមាន និងពិន្ទុបែងចែកតាមថ្នាក់ ---
        with t_tab1:
            filter_class = st.selectbox("🏫 ជ្រើសរើសថ្នាក់ដើម្បីមើលរបាយការណ៍៖", ["ទាំងអស់"] + CLASSES)
            st.divider()

            st.subheader("១. តារាងពិន្ទុសិស្សតាមសប្តាហ៍ និងសរុបរួម")
            if filter_class == "ទាំងអស់":
                df_scores = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS សប្តាហ៍, score AS ពិន្ទុបាន, total AS ពិន្ទុពេញ, date AS កាលបរិច្ឆេទ FROM scores", conn)
            else:
                df_scores = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS សប្តាហ៍, score AS ពិន្ទុបាន, total AS ពិន្ទុពេញ, date AS កាលបរិច្ឆេទ FROM scores WHERE class_name = ?", conn, params=(filter_class,))
            
            if not df_scores.empty:
                st.write("**តារាងបូកសរុបពិន្ទុរាល់សប្តាហ៍ និងពិន្ទុសរុបរួមរបស់សិស្សម្នាក់ៗ៖**")
                # រៀបចំតារាងបង្ហាញពិន្ទុតាមសប្តាហ៍នីមួយៗ (Pivot Table)
                pivot_scores = df_scores.pivot_table(
                    index=['ថ្នាក់', 'អត្តលេខ', 'ឈ្មោះសិស្ស'], 
                    columns='សប្តាហ៍', 
                    values='ពិន្ទុបាន', 
                    aggfunc='max', 
                    fill_value=0
                ).reset_index()
                
                # បូកសរុបពិន្ទុគ្រប់សប្តាហ៍បញ្ចូលគ្នា
                week_cols = [col for col in pivot_scores.columns if col in WEEKS]
                pivot_scores['ពិន្ទុសរុបរួម'] = pivot_scores[week_cols].sum(axis=1)
                
                st.dataframe(pivot_scores, use_container_width=True)
                
                csv_summary = pivot_scores.to_csv(index=False).encode('utf-8-sig')
                st.download_button(f"📥 ទាញយកតារាងពិន្ទុសរុប ({filter_class}) - Excel/CSV", csv_summary, f"scores_{filter_class}.csv", "text/csv")
                
                with st.expander("មើលប្រវត្តិធ្វើតេស្តលម្អិតទាំងអស់"):
                    st.dataframe(df_scores, use_container_width=True)
            else:
                st.info(f"មិនទាន់មានទិន្នន័យពិន្ទុសម្រាប់ {filter_class} នៅឡើយទេ។")

            st.divider()
            st.subheader("២. តារាងវត្តមាន និងអវត្តមានសិស្ស")
            if filter_class == "ទាំងអស់":
                df_att = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS សប្តាហ៍, status AS ស្ថានភាព, date AS កាលបរិច្ឆេទ FROM attendance", conn)
            else:
                df_att = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS សប្តាហ៍, status AS ស្ថានភាព, date AS កាលបរិច្ឆេទ FROM attendance WHERE class_name = ?", conn, params=(filter_class,))
            
            st.dataframe(df_att, use_container_width=True)
            
            if not df_att.empty:
                csv_att = df_att.to_csv(index=False).encode('utf-8-sig')
                st.download_button(f"📥 ទាញយកបញ្ជីវត្តមាន ({filter_class}) - Excel/CSV", csv_att, f"attendance_{filter_class}.csv", "text/csv")

        # --- ផ្ទាំងទី ២៖ បង្ហោះមេរៀនតាមសប្តាហ៍ ---
        with t_tab2:
            st.subheader("បន្ថែមមេរៀនស្វ័យសិក្សាថ្មី")
            with st.form("add_lesson_form"):
                l_week = st.selectbox("ជ្រើសរើសសប្តាហ៍សម្រាប់មេរៀននេះ", WEEKS)
                l_title = st.text_input("ចំណងជើងមេរៀន")
                l_content = st.text_area("ខ្លឹមសារមេរៀន / សេចក្តីណែនាំ")
                l_pdf = st.file_uploader("📄 ទម្លាក់ឯកសារមេរៀន PDF នៅទីនេះ (បើមាន)", type=["pdf"])
                l_video = st.text_input("តំណភ្ជាប់វីដេអូ YouTube (បើមាន)")
                
                if st.form_submit_button("រក្សាទុកមេរៀន"):
                    if l_title and l_content:
                        pdf_name = l_pdf.name if l_pdf else None
                        pdf_bytes = l_pdf.read() if l_pdf else None
                        c.execute("INSERT INTO lessons (week, title, content, video_url, pdf_name, pdf_data) VALUES (?, ?, ?, ?, ?, ?)", 
                                  (l_week, l_title, l_content, l_video, pdf_name, pdf_bytes))
                        conn.commit()
                        st.success(f"បានបង្ហោះមេរៀនចូលក្នុង {l_week} ដោយជោគជ័យ!")
                    else:
                        st.error("សូមបញ្ចូលចំណងជើង និងខ្លឹមសារមេរៀន!")

        # --- ផ្ទាំងទី ៣៖ ឃ្លាំងសំណួរ (Question Bank) ---
        with t_tab3:
            st.subheader("⚙️ កំណត់ចំនួនសំណួរសម្រាប់សិស្សធ្វើតេស្តម្តងៗ")
            current_num = get_num_questions()
            new_num = st.number_input("ចំនួនសំណួរដែលត្រូវចាប់ដោយចៃដន្យ (Random) ក្នុង ១ តេស្ត៖", min_value=1, max_value=50, value=current_num)
            if st.button("រក្សាទុកការកំណត់"):
                c.execute("UPDATE settings SET value = ? WHERE key = 'num_questions'", (str(new_num),))
                conn.commit()
                st.success(f"បានកំណត់ឲ្យប្រព័ន្ធចាប់យក {new_num} សំណួរដោយចៃដន្យសម្រាប់តេស្តនីមួយៗ!")

            st.divider()
            st.subheader("➕ បញ្ចូលសំណួរថ្មីទៅក្នុងឃ្លាំងសំណួរ (Question Bank)")
            with st.form("add_quiz_form"):
                q_week = st.selectbox("ជ្រើសរើសសប្តាហ៍សម្រាប់សំណួរនេះ", WEEKS)
                q_text = st.text_input("សំណួរ")
                opt_a = st.text_input("ជម្រើស ក")
                opt_b = st.text_input("ជម្រើស ខ")
                opt_c = st.text_input("ជម្រើស គ")
                correct = st.selectbox("ចម្លើយដែលត្រឹមត្រូវ", ["ជម្រើស ក", "ជម្រើស ខ", "ជម្រើស គ"])
                if st.form_submit_button("បញ្ចូលទៅក្នុងឃ្លាំងសំណួរ"):
                    if q_text and opt_a and opt_b and opt_c:
                        ans_map = {"ជម្រើស ក": opt_a, "ជម្រើស ខ": opt_b, "ជម្រើស គ": opt_c}
                        c.execute("INSERT INTO quizzes (week, question, opt_a, opt_b, opt_c, correct_opt) VALUES (?, ?, ?, ?, ?, ?)",
                                  (q_week, q_text, opt_a, opt_b, opt_c, ans_map[correct]))
                        conn.commit()
                        st.success(f"បានបញ្ចូលសំណួរទៅក្នុងឃ្លាំងសំណួររបស់ {q_week} រួចរាល់!")
                    else:
                        st.error("សូមបំពេញសំណួរ និងជម្រើសទាំង ៣ ឲ្យបានគ្រប់គ្រាន់!")

            st.divider()
            st.subheader("📋 បញ្ជីសំណួរទាំងអស់ក្នុងឃ្លាំងសំណួរ")
            filter_week = st.selectbox("ត្រងមើលសំណួរតាមសប្តាហ៍៖", ["ទាំងអស់"] + WEEKS)
            if filter_week == "ទាំងអស់":
                df_q = pd.read_sql_query("SELECT id AS លេខកូដ, week AS សប្តាហ៍, question AS សំណួរ, correct_opt AS ចម្លើយត្រូវ FROM quizzes", conn)
            else:
                df_q = pd.read_sql_query("SELECT id AS លេខកូដ, week AS សប្តាហ៍, question AS សំណួរ, correct_opt AS ចម្លើយត្រូវ FROM quizzes WHERE week = ?", conn, params=(filter_week,))
            
            st.dataframe(df_q, use_container_width=True)
            
            if not df_q.empty:
                del_id = st.number_input("បញ្ចូល 'លេខកូដ' សំណួរដែលចង់លុបចេញពីឃ្លាំង៖", min_value=1, step=1)
                if st.button("🗑️ លុបសំណួរនេះ"):
                    c.execute("DELETE FROM quizzes WHERE id = ?", (del_id,))
                    conn.commit()
                    st.warning(f"បានលុបសំណួរលេខកូដ {del_id} រួចរាល់! សូម Refresh ទំព័រដើម្បីមើលបញ្ជីថ្មី។")
    else:
        st.warning("សូមបញ្ចូលលេខសម្ងាត់គ្រូនៅរបារខាងឆ្វេង ដើម្បីចូលគ្រប់គ្រងទិន្នន័យ។")
