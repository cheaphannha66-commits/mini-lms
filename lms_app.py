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

# បង្កើតតារាងទិន្នន័យ (Tables) និងអាប់ដេតជួរឈរ PDF ដោយមិនប៉ះពាល់ទិន្នន័យចាស់
def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, student_name TEXT, date TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lessons 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, video_url TEXT, pdf_name TEXT, pdf_data BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS quizzes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT, opt_a TEXT, opt_b TEXT, opt_c TEXT, correct_opt TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, student_name TEXT, score INTEGER, total INTEGER, date TEXT)''')
    
    # ពិនិត្យ និងបន្ថែមជួរឈរ PDF សម្រាប់តារាងមេរៀនចាស់ (ការពារកុំឲ្យបាត់ទិន្នន័យចាស់)
    c.execute("PRAGMA table_info(lessons)")
    columns = [col[1] for col in c.fetchall()]
    if 'pdf_name' not in columns:
        c.execute("ALTER TABLE lessons ADD COLUMN pdf_name TEXT")
    if 'pdf_data' not in columns:
        c.execute("ALTER TABLE lessons ADD COLUMN pdf_data BLOB")
    conn.commit()

init_db()

# បញ្ចូលទិន្នន័យគំរូបឋម (ប្រសិនបើមិនទាន់មាន)
c.execute("SELECT COUNT(*) FROM lessons")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO lessons (title, content, video_url) VALUES (?, ?, ?)",
              ("មេរៀនទី ១៖ ការរកក្រឡាផ្ទៃត្រីកោណ", 
               "ក្រឡាផ្ទៃត្រីកោណស្មើនឹងពាក់កណ្តាលនៃផលគុណបាត និងកម្ពស់ (S = (b × h) / 2)។ សូមទស្សនាវីដេអូខាងក្រោម រួចចូលទៅធ្វើតេស្ត។",
               "https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
    c.execute("INSERT INTO quizzes (question, opt_a, opt_b, opt_c, correct_opt) VALUES (?, ?, ?, ?, ?)",
              ("១. តើរូបមន្តក្រឡាផ្ទៃត្រីកោណគឺជាអ្វី?", "S = b × h", "S = (b × h) / 2", "S = 2 × (b + h)", "S = (b × h) / 2"))
    c.execute("INSERT INTO quizzes (question, opt_a, opt_b, opt_c, correct_opt) VALUES (?, ?, ?, ?, ?)",
              ("២. បើត្រីកោណមានបាត 6cm និងកម្ពស់ 4cm តើក្រឡាផ្ទៃស្មើប៉ុន្មាន?", "12 cm²", "24 cm²", "10 cm²", "12 cm²"))
    conn.commit()

# រចនាម៉ូដអក្សរខ្មែរ (Battambang)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Battambang:wght@400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Battambang', sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.title("📐 ចំណេះដឹងគណិតវិទ្យា")

# ម៉ឺនុយជ្រើសរើសតួនាទី (សិស្ស ឬ គ្រូ)
role = st.sidebar.selectbox("ជ្រើសរើសតួនាទីប្រើប្រាស់៖", ["👨‍🎓 ផ្នែកសម្រាប់សិស្ស (Student)", "👨‍🏫 ផ្នែកសម្រាប់គ្រូ (Teacher Admin)"])

# ==========================================
# ១. ផ្នែកសម្រាប់សិស្ស (STUDENT PORTAL)
# ==========================================
if role == "👨‍🎓 ផ្នែកសម្រាប់សិស្ស (Student)":
    tab1, tab2, tab3 = st.tabs(["✅ ចុះវត្តមាន", "📚 មេរៀនស្វ័យសិក្សា", "📝 ធ្វើតេស្តសមត្ថភាព"])

    # --- ផ្ទាំងទី ១៖ សិស្សចុះវត្តមាន ---
    with tab1:
        st.subheader("ចុះវត្តមានចូលរៀនប្រចាំថ្ងៃ")
        with st.form("attendance_form"):
            s_id = st.text_input("អត្តលេខសិស្ស (ឧ. S001)")
            s_name = st.text_input("គោត្តនាម និងនាម")
            status = st.selectbox("ស្ថានភាព", ["វត្តមាន", "សុំច្បាប់"])
            submitted = st.form_submit_button("បញ្ជូនវត្តមាន")
            
            if submitted:
                if s_id and s_name:
                    today = datetime.now().strftime("%Y-%m-%d %H:%M")
                    c.execute("INSERT INTO attendance (student_id, student_name, date, status) VALUES (?, ?, ?, ?)",
                              (s_id.strip(), s_name.strip(), today, status))
                    conn.commit()
                    st.success(f"ជោគជ័យ! បានកត់ត្រាវត្តមានសម្រាប់ {s_name} រួចរាល់។")
                else:
                    st.error("សូមបញ្ចូលអត្តលេខ និងឈ្មោះរបស់អ្នក!")

    # --- ផ្ទាំងទី ២៖ មេរៀនស្វ័យសិក្សា (មានវីដេអូ និង PDF) ---
    with tab2:
        st.subheader("បញ្ជីមេរៀនស្វ័យសិក្សា")
        c.execute("SELECT id, title, content, video_url, pdf_name, pdf_data FROM lessons ORDER BY id DESC")
        lessons_data = c.fetchall()
        
        for l_id, title, content, video_url, pdf_name, pdf_data in lessons_data:
            with st.expander(f"📖 {title}", expanded=True):
                st.write(content)
                
                # បង្ហាញប៊ូតុងទាញយក និងអានឯកសារ PDF (ប្រសិនបើមាន)
                if pdf_data and pdf_name:
                    st.download_button(
                        label=f"📥 ទាញយកឯកសារ PDF៖ {pdf_name}",
                        data=pdf_data,
                        file_name=pdf_name,
                        mime="application/pdf",
                        key=f"dl_pdf_{l_id}"
                    )
                    # បង្ហាញផ្ទាំងអាន PDF ផ្ទាល់លើអេក្រង់ (សម្រាប់កុំព្យូទ័រ/Tablet)
                    with st.expander("👁️ ចុចទីនេះដើម្បីអានឯកសារ PDF ផ្ទាល់"):
                        base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)

                # បង្ហាញវីដេអូ YouTube (ប្រសិនបើមាន)
                if video_url:
                    st.video(video_url)

    # --- ផ្ទាំងទី ៣៖ ធ្វើតេស្ត ---
    with tab3:
        st.subheader("កម្រងសំណួរតេស្ត")
        c.execute("SELECT id, question, opt_a, opt_b, opt_c, correct_opt FROM quizzes")
        questions = c.fetchall()
        
        if not questions:
            st.info("មិនទាន់មានសំណួរតេស្តនៅឡើយទេ។")
        else:
            with st.form("quiz_form"):
                q_sid = st.text_input("អត្តលេខសិស្ស")
                q_sname = st.text_input("ឈ្មោះសិស្ស")
                st.divider()
                
                user_answers = {}
                for q_id, q_text, a, b, c_opt, correct in questions:
                    user_answers[q_id] = st.radio(q_text, [a, b, c_opt], key=f"q_{q_id}")
                
                quiz_submit = st.form_submit_button("បញ្ជូនចម្លើយ និងមើលពិន្ទុ")
                
                if quiz_submit:
                    if q_sid and q_sname:
                        score = 0
                        total = len(questions)
                        for q_id, q_text, a, b, c_opt, correct in questions:
                            if user_answers[q_id] == correct:
                                score += 1
                        
                        today = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute("INSERT INTO scores (student_id, student_name, score, total, date) VALUES (?, ?, ?, ?, ?)",
                                  (q_sid.strip(), q_sname.strip(), score, total, today))
                        conn.commit()
                        st.success(f"🎉 អបអរសាទរ {q_sname}! អ្នកទទួលបានពិន្ទុ៖ {score} / {total}")
                    else:
                        st.error("សូមបញ្ចូលអត្តលេខ និងឈ្មោះមុននឹងបញ្ជូនចម្លើយ!")

# ==========================================
# ២. ផ្នែកសម្រាប់គ្រូ (TEACHER ADMIN)
# ==========================================
elif role == "👨‍🏫 ផ្នែកសម្រាប់គ្រូ (Teacher Admin)":
    password = st.sidebar.text_input("បញ្ចូលលេខសម្ងាត់គ្រូ", type="password")
    
    # លោកគ្រូអាចប្តូរលេខសម្ងាត់ "23101990lkk" ខាងក្រោមនេះទៅជាលេខសម្ងាត់ផ្ទាល់ខ្លួនបាន
    if password == "23101990lkk":
        t_tab1, t_tab2, t_tab3 = st.tabs(["📊 របាយការណ៍វត្តមាន និងពិន្ទុ", "➕ បង្ហោះមេរៀនថ្មី (PDF/វីដេអូ)", "❓ បង្កើតសំណួរតេស្ត"])
        
        # --- ផ្ទាំងទី ១៖ បូកសរុបវត្តមាន និងពិន្ទុ ---
        with t_tab1:
            st.subheader("១. តារាងបូកសរុបពិន្ទុតេស្តសិស្ស")
            df_scores = pd.read_sql_query("SELECT student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, score AS ពិន្ទុបាន, total AS ពិន្ទុពេញ, date AS កាលបរិច្ឆេទ FROM scores", conn)
            st.dataframe(df_scores, use_container_width=True)
            
            if not df_scores.empty:
                summary_scores = df_scores.groupby(['អត្តលេខ', 'ឈ្មោះសិស្ស'])[['ពិន្ទុបាន', 'ពិន្ទុពេញ']].sum().reset_index()
                st.write("**សរុបពិន្ទុរួមរបស់សិស្សម្នាក់ៗ៖**")
                st.dataframe(summary_scores, use_container_width=True)
                
                csv_scores = summary_scores.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 ទាញយកតារាងពិន្ទុ (Excel/CSV)", csv_scores, "student_scores.csv", "text/csv")

            st.divider()
            st.subheader("២. តារាងវត្តមានសិស្ស")
            df_att = pd.read_sql_query("SELECT student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, status AS ស្ថានភាព, date AS កាលបរិច្ឆេទ FROM attendance", conn)
            st.dataframe(df_att, use_container_width=True)
            
            if not df_att.empty:
                csv_att = df_att.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 ទាញយកបញ្ជីវត្តមាន (Excel/CSV)", csv_att, "student_attendance.csv", "text/csv")

        # --- ផ្ទាំងទី ២៖ បង្ហោះមេរៀន (មានកន្លែងទម្លាក់ឯកសារ PDF) ---
        with t_tab2:
            st.subheader("បន្ថែមមេរៀនស្វ័យសិក្សាថ្មី")
            with st.form("add_lesson_form"):
                l_title = st.text_input("ចំណងជើងមេរៀន")
                l_content = st.text_area("ខ្លឹមសារមេរៀន / សេចក្តីណែនាំ")
                l_pdf = st.file_uploader("📄 ទម្លាក់ឯកសារមេរៀន PDF នៅទីនេះ (បើមាន)", type=["pdf"])
                l_video = st.text_input("តំណភ្ជាប់វីដេអូ YouTube (បើមាន)")
                
                if st.form_submit_button("រក្សាទុកមេរៀន"):
                    if l_title and l_content:
                        pdf_name = l_pdf.name if l_pdf else None
                        pdf_bytes = l_pdf.read() if l_pdf else None
                        
                        c.execute("INSERT INTO lessons (title, content, video_url, pdf_name, pdf_data) VALUES (?, ?, ?, ?, ?)", 
                                  (l_title, l_content, l_video, pdf_name, pdf_bytes))
                        conn.commit()
                        st.success("បានបង្ហោះមេរៀនថ្មី ព្រមទាំងឯកសារ PDF ដោយជោគជ័យ!")
                    else:
                        st.error("សូមបញ្ចូលចំណងជើង និងខ្លឹមសារមេរៀន!")

        # --- ផ្ទាំងទី ៣៖ បង្កើតសំណួរតេស្ត ---
        with t_tab3:
            st.subheader("បន្ថែមសំណួរតេស្តថ្មី")
            with st.form("add_quiz_form"):
                q_text = st.text_input("សំណួរ")
                opt_a = st.text_input("ជម្រើស ក")
                opt_b = st.text_input("ជម្រើស ខ")
                opt_c = st.text_input("ជម្រើស គ")
                correct = st.selectbox("ចម្លើយដែលត្រឹមត្រូវ", ["ជម្រើស ក", "ជម្រើស ខ", "ជម្រើស គ"])
                if st.form_submit_button("រក្សាទុកសំណួរ"):
                    if q_text and opt_a and opt_b and opt_c:
                        ans_map = {"ជម្រើស ក": opt_a, "ជម្រើស ខ": opt_b, "ជម្រើស គ": opt_c}
                        c.execute("INSERT INTO quizzes (question, opt_a, opt_b, opt_c, correct_opt) VALUES (?, ?, ?, ?, ?)",
                                  (q_text, opt_a, opt_b, opt_c, ans_map[correct]))
                        conn.commit()
                        st.success("បានបន្ថែមសំណួរតេស្តរួចរាល់!")
    else:
        st.warning("សូមបញ្ចូលលេខសម្ងាត់គ្រូនៅរបារខាងឆ្វេង ដើម្បីចូលគ្រប់គ្រងទិន្នន័យ។")
