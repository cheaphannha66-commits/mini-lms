import streamlit as st
import sqlite3
import pandas as pd
import base64
import hashlib
from datetime import datetime
from streamlit_quill import st_quill

# កំណត់រចនាសម្ព័ន្ធទំព័រ
st.set_page_config(page_title="ចំណេះដឹងគណិតវិទ្យា - LMS", page_icon="📐", layout="wide")

# បង្កើត និងភ្ជាប់ Database (SQLite)
conn = sqlite3.connect('school_lms.db', check_same_thread=False)
c = conn.cursor()

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==========================================
# ការកំណត់គណនីគ្រូ
# ==========================================
TEACHER_EMAIL = "cheaphannha66@gmail.com"
TEACHER_PASS_HASH = hash_pass("23101990lkk")
TEACHER_NAME = "លោកគ្រូ ជា បញ្ញា"

WEEKS = ["សប្តាហ៍ទី ១", "សប្តាហ៍ទី ២", "សប្តាហ៍ទី ៣", "សប្តាហ៍ទី ៤", "សប្តាហ៍ទី ៥"]
CLASSES = ["ថ្នាក់ ក", "ថ្នាក់ ខ", "ថ្នាក់ គ"]

# បង្កើត និងអាប់ដេតតារាងទិន្នន័យ (ការពារទិន្នន័យចាស់ ១០០%)
def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, role TEXT, class_name TEXT, student_id TEXT, full_name TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, class_name TEXT, student_id TEXT, student_name TEXT, week TEXT, date TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lessons 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, week TEXT, category TEXT, title TEXT, content TEXT, video_url TEXT, pdf_name TEXT, pdf_data BLOB, v_question TEXT, v_opt_a TEXT, v_opt_b TEXT, v_opt_c TEXT, v_correct TEXT, ext_link TEXT, video_blob BLOB, video_filename TEXT)''')
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
    c.execute('''CREATE TABLE IF NOT EXISTS completions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, activity_key TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio_tasks 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, due_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio_submissions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER, class_name TEXT, student_id TEXT, student_name TEXT, file_name TEXT, file_data BLOB, note TEXT, score TEXT, date TEXT)''')

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
    new_l_cols = {
        'category': "TEXT DEFAULT 'ឯកសារអាន (File)'",
        'pdf_name': "TEXT",
        'pdf_data': "BLOB",
        'v_question': "TEXT",
        'v_opt_a': "TEXT",
        'v_opt_b': "TEXT",
        'v_opt_c': "TEXT",
        'v_correct': "TEXT",
        'ext_link': "TEXT",
        'video_blob': "BLOB",
        'video_filename': "TEXT"
    }
    for col_name, col_type in new_l_cols.items():
        if col_name not in l_cols:
            c.execute(f"ALTER TABLE lessons ADD COLUMN {col_name} {col_type}")

    c.execute("PRAGMA table_info(quizzes)")
    if 'is_pretest' not in [col[1] for col in c.fetchall()]:
        c.execute("ALTER TABLE quizzes ADD COLUMN is_pretest INTEGER DEFAULT 0")

    c.execute("SELECT COUNT(*) FROM portfolio_tasks")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO portfolio_tasks (title, description, due_date) VALUES (?, ?, ?)",
                  ("ផលបត្រទី ១៖ សំណើគម្រោង និងសន្លឹកកិច្ចការអនុវត្ត", "សូមសិស្សទម្លាក់ឯកសារផលបត្រ (PDF, Word ឬរូបភាព) ចូលទីនេះ។", "ចុងសប្តាហ៍ទី ៣"))
        c.execute("INSERT INTO portfolio_tasks (title, description, due_date) VALUES (?, ?, ?)",
                  ("ផលបត្របញ្ចប់វគ្គ៖ របាយការណ៍សំយោគ និងការឆ្លុះបញ្ចាំង", "សូមប្រគល់របាយការណ៍ផលបត្រចុងក្រោយរបស់អ្នកនៅទីនេះ។", "ចុងសប្តាហ៍ទី ៥"))

    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('num_questions', '5')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('final_questions', '15')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('course_expectation', '<p>សូមស្វាគមន៍មកកាន់វគ្គសិក្សា <b>ចំណេះដឹងគណិតវិទ្យា</b>!</p>')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card1_title', 'រយៈពេលសិក្សា')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card1_desc', '៥ សប្តាហ៍ (ស្វ័យសិក្សា និងអនុវត្ត)')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card2_title', 'ទម្រង់សិក្សា')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card2_desc', 'សិក្សាតាមអនឡាញ វីដេអូ និងវេទិកាពិភាក្សា')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card3_title', 'ការវាយតម្លៃ & ផលបត្រ')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card3_desc', 'បុរេតេស្ត តេស្តប្រចាំសប្តាហ៍ និងផលបត្រ')")
    conn.commit()

init_db()

def get_setting(key, default_val):
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = c.fetchone()
    return res[0] if res else default_val

# រចនាម៉ូដ CSS ផ្ទៃខាងក្រោយពណ៌ស និងរចនាបថ Moodle / PLP LMS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Battambang:wght@400;700&display=swap');
    html, body, [class*="css"], .stApp { 
        font-family: 'Battambang', sans-serif; 
        background-color: #ffffff !important;
        color: #1f2937;
    }
    [data-testid="stToolbar"] { visibility: hidden; display: none; }
    header { visibility: hidden; }
    
    .lms-header {
        background-color: #ffffff;
        text-align: center;
        padding: 10px 0 15px 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 15px;
    }
    .lms-main-title {
        font-size: 32px;
        font-weight: bold;
        color: #f59e0b;
        text-shadow: 1px 1px 0px #1e3a8a;
        margin: 0;
    }
    .login-card {
        border: 1px solid #dbeafe;
        border-top: 5px solid #2563eb;
        border-radius: 12px;
        padding: 25px;
        background-color: #f8fafc;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .welcome-banner {
        border: 1px solid #dbeafe;
        border-top: 4px solid #2563eb;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: #ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        margin-bottom: 20px;
    }
    .welcome-banner h3 { color: #1f2937; margin-bottom: 8px; font-weight: bold; }
    .welcome-banner p { color: #4b5563; font-size: 16px; margin: 0; }
    .welcome-banner span { color: #2563eb; font-weight: bold; }

    .info-card {
        border-radius: 10px; padding: 15px; display: flex; align-items: center; margin-bottom: 15px;
    }
    .card-green { background-color: #f0fdf4; border: 1px solid #bbf7d0; }
    .card-blue { background-color: #eff6ff; border: 1px solid #bfdbfe; }
    .card-pink { background-color: #fdf2f8; border: 1px solid #fbcfe8; }
    .card-icon {
        width: 44px; height: 44px; border-radius: 8px; display: flex; align-items: center; justify-content: center;
        font-size: 22px; margin-right: 12px; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .card-title { color: #1d4ed8; font-weight: bold; font-size: 15px; margin: 0; }
    .card-desc { color: #15803d; font-size: 13px; margin: 2px 0 0 0; }

    .activity-row {
        display: flex; align-items: center; border: 1px solid #e5e7eb; border-left: 4px solid #16a34a;
        border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; background-color: #ffffff;
    }
    .icon-box {
        width: 42px; height: 42px; border-radius: 8px; display: flex; align-items: center; justify-content: center;
        font-size: 20px; margin-right: 15px; flex-shrink: 0;
    }
    .icon-h5p { background-color: #f3f4f6; border: 1px solid #d1d5db; color: #111827; font-weight: bold; font-size: 14px; }
    .icon-video { background-color: #dc2626; color: white; }
    .icon-task { background-color: #ec4899; color: white; }
    .icon-pdf { background-color: #2563eb; color: white; }
    .icon-link { background-color: #0891b2; color: white; }
    .icon-page { background-color: #4f46e5; color: white; }
    .icon-att { background-color: #16a34a; color: white; }
    .icon-forum { background-color: #f59e0b; color: white; }
    .icon-quiz { background-color: #7c3aed; color: white; }
    
    .act-title { color: #1d4ed8; font-size: 16px; font-weight: bold; margin: 0; }
    .act-status-done { color: #15803d; font-size: 13px; font-weight: bold; margin-top: 3px; }
    .act-status-pending { color: #6b7280; font-size: 13px; margin-top: 3px; }
    </style>
""", unsafe_allow_html=True)

# ក្បាលខាងលើពណ៌ស
st.markdown('''
    <div class="lms-header">
        <p class="lms-main-title">📐 ចំណេះដឹងគណិតវិទ្យា 🎓</p>
    </div>
''', unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = {}

# ==============================================================================
# អនុគមន៍រួម៖ បង្ហាញបញ្ជី Learning Materials ក្នុងសប្តាហ៍នីមួយៗ (ប្រើបានទាំងសិស្ស និងគ្រូ)
# ==============================================================================
def render_week_materials(selected_week, is_teacher=False, stu_id="", completed_keys=set()):
    # ១. សេចក្តីផ្តើម / សេចក្តីណែនាំប្រចាំសប្តាហ៍
    c.execute("SELECT id, title, content, pdf_name, pdf_data FROM lessons WHERE week = ? AND category = 'សេចក្តីផ្តើម' ORDER BY id ASC", (selected_week,))
    for i_id, title, content, pdf_name, pdf_data in c.fetchall():
        col_i1, col_i2 = st.columns([8, 1]) if is_teacher else (st.container(), None)
        with col_i1:
            st.markdown(f'<div class="welcome-banner" style="text-align:left; padding:12px 18px;"><h4 style="color:#1d4ed8; margin:0;">📌 {title}</h4></div>', unsafe_allow_html=True)
            st.markdown(content, unsafe_allow_html=True)
            if pdf_data and pdf_name:
                st.download_button(f"📥 ទាញយកឯកសារណែនាំ៖ {pdf_name}", data=pdf_data, file_name=pdf_name, key=f"intro_dl_{i_id}_{is_teacher}")
        if is_teacher and col_i2:
            if col_i2.button("🗑️ លុប", key=f"del_intro_{i_id}"):
                c.execute("DELETE FROM lessons WHERE id = ?", (i_id,))
                conn.commit()
                st.rerun()

    # ២. បញ្ជី Learning Materials ទាំងអស់ក្នុងសប្តាហ៍នេះ (File, Video, Interactive H5P, Link, Page, Task)
    c.execute('''SELECT id, category, title, content, video_url, pdf_name, pdf_data, v_question, v_opt_a, v_opt_b, v_opt_c, v_correct, ext_link, video_blob, video_filename 
                 FROM lessons WHERE week = ? AND category != 'សេចក្តីផ្តើម' ORDER BY id ASC''', (selected_week,))
    materials = c.fetchall()

    if not materials:
        st.info(f"មិនទាន់មានសម្ភារៈសិក្សា (Learning Material) នៅក្នុង {selected_week} នៅឡើយទេ។")

    for act_id, cat, title, content, video_url, pdf_name, pdf_data, v_q, v_a, v_b, v_c, v_corr, ext_link, vid_blob, vid_fname in materials:
        act_key = f"lesson_{act_id}"
        is_done = act_key in completed_keys

        # កំណត់ Icon និងស្លាកសម្គាល់តាមប្រភេទ Material
        if cat == "ឯកសារអាន (File)":
            icon_cls, icon_char, action_label = "icon-pdf", "📄", "ឯកសារអាន (File)"
        elif cat == "វីដេអូបង្រៀន (Video)":
            icon_cls, icon_char, action_label = "icon-video", "🎬", "វីដេអូបង្រៀន (Video)"
        elif cat == "វីដេអូភ្ជាប់សំណួរ (H5P)":
            icon_cls, icon_char, action_label = "icon-h5p", "H5P", "មេរៀនអន្តរកម្មភ្ជាប់សំណួរ"
        elif cat == "តំណភ្ជាប់ខាងក្រៅ (Link)":
            icon_cls, icon_char, action_label = "icon-link", "🔗", "តំណភ្ជាប់សិក្សា (Link)"
        elif cat == "កិច្ចការ / ស្វ័យសិក្សា (Task)":
            icon_cls, icon_char, action_label = "icon-task", "📤", "កិច្ចការ / ស្វ័យសិក្សា"
        else:
            icon_cls, icon_char, action_label = "icon-page", "📝", "អត្ថបទមេរៀន (Page)"

        if is_teacher:
            status_html = f'<div class="act-status-pending">ប្រភេទ៖ {action_label}</div>'
        else:
            status_html = f'<div class="act-status-done">✓ រួចរាល់ ({action_label})</div>' if is_done else f'<div class="act-status-pending">○ {action_label}</div>'

        col_m1, col_m2 = st.columns([9, 1]) if is_teacher else (st.container(), None)
        with col_m1:
            st.markdown(f'''
                <div class="activity-row">
                    <div class="icon-box {icon_cls}">{icon_char}</div>
                    <div>
                        <p class="act-title">{title}</p>
                        {status_html}
                    </div>
                </div>
            ''', unsafe_allow_html=True)
        if is_teacher and col_m2:
            st.write("")
            if col_m2.button("🗑️ លុប", key=f"del_mat_{act_id}"):
                c.execute("DELETE FROM lessons WHERE id = ?", (act_id,))
                conn.commit()
                st.rerun()

        with st.expander(f"បើកមើល៖ {title}"):
            if content:
                st.markdown(content, unsafe_allow_html=True)
            
            # បង្ហាញឯកសារ File (PDF, Word, Excel, Slide...)
            if pdf_data and pdf_name:
                st.download_button(f"📥 ទាញយកឯកសារ៖ {pdf_name}", data=pdf_data, file_name=pdf_name, key=f"dl_m_{act_id}_{is_teacher}")
                if pdf_name.lower().endswith(".pdf"):
                    with st.expander("👁️ អានឯកសារ PDF ផ្ទាល់លើអេក្រង់"):
                        base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                        st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>', unsafe_allow_html=True)
            
            # បង្ហាញវីដេអូ YouTube ឬ វីដេអូ Upload MP4
            if video_url:
                st.video(video_url)
            if vid_blob:
                st.video(vid_blob)

            # បង្ហាញតំណភ្ជាប់ Link ខាងក្រៅ
            if ext_link:
                st.link_button("🌐 ចុចទីនេះដើម្បីបើកតំណភ្ជាប់សិក្សា", ext_link)

            # បង្ហាញសំណួរអន្តរកម្ម H5P
            if v_q and v_a and v_b and v_c:
                st.markdown("---")
                st.markdown(f"**🎬 សំណួរបំផុសគំនិត៖** {v_q}")
                ans_choice = st.radio("ជ្រើសរើសចម្លើយ៖", [v_a, v_b, v_c], key=f"vq_r_{act_id}_{is_teacher}")
                if st.button("ផ្ទៀងផ្ទាត់ចម្លើយ", key=f"vq_c_{act_id}_{is_teacher}"):
                    if ans_choice == v_corr:
                        st.success("🎉 ត្រឹមត្រូវ!")
                        if not is_teacher and stu_id and not is_done:
                            c.execute("INSERT INTO completions (student_id, activity_key, date) VALUES (?, ?, ?)", (stu_id, act_key, datetime.now().strftime("%Y-%m-%d %H:%M")))
                            conn.commit()
                            st.rerun()
                    else:
                        st.error(f"❌ មិនទាន់ត្រូវទេ! ចម្លើយត្រូវគឺ៖ {v_corr}")

            # ប៊ូតុងគូសចំណាំថារួចរាល់សម្រាប់សិស្ស
            if not is_teacher and not is_done:
                if st.button("✓ គូសចំណាំថារួចរាល់", key=f"dn_b_{act_id}"):
                    c.execute("INSERT INTO completions (student_id, activity_key, date) VALUES (?, ?, ?)", (stu_id, act_key, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    st.rerun()


# ==============================================================================
# ទំព័រទី ០៖ ផ្ទាំង SIGN IN / REGISTER ជាមួយ EMAIL
# ==============================================================================
if not st.session_state.logged_in:
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.subheader("🔐 ចូលប្រើប្រាស់ប្រព័ន្ធសិក្សាអនឡាញ (Sign In)")
        st.caption("សូមជ្រើសរើសតួនាទី និងបញ្ចូល Email របស់អ្នកដើម្បីចូលទៅកាន់ថ្នាក់រៀន")

        auth_mode = st.tabs(["🔑 ចូលប្រើប្រាស់ (Sign In)", "📝 ចុះឈ្មោះសិស្សថ្មី (Register)"])

        with auth_mode[0]:
            login_role = st.radio("ជ្រើសរើសតួនាទីរបស់អ្នក៖", ["👨‍🎓 សិស្ស (Student)", "👨‍🏫 គ្រូបង្រៀន (Teacher)"], horizontal=True)
            email_in = st.text_input("អ៊ីមែល (Email)៖", placeholder="example@gmail.com", key="log_email").strip().lower()
            pass_in = st.text_input("លេខសម្ងាត់ (Password)៖", type="password", key="log_pass")

            if st.button("🚀 ចូលប្រើប្រាស់ (Sign In)", use_container_width=True, type="primary"):
                if login_role == "👨‍🏫 គ្រូបង្រៀន (Teacher)":
                    if email_in == TEACHER_EMAIL.lower() and hash_pass(pass_in) == TEACHER_PASS_HASH:
                        st.session_state.logged_in = True
                        st.session_state.user_info = {"role": "teacher", "email": TEACHER_EMAIL, "full_name": TEACHER_NAME}
                        st.rerun()
                    else:
                        st.error("❌ Email ឬ លេខសម្ងាត់គ្រូមិនត្រឹមត្រូវទេ!")
                else:
                    c.execute("SELECT email, role, class_name, student_id, full_name FROM users WHERE email = ? AND password = ?", (email_in, hash_pass(pass_in)))
                    user_row = c.fetchone()
                    if user_row:
                        st.session_state.logged_in = True
                        st.session_state.user_info = {"role": "student", "email": user_row[0], "class_name": user_row[2], "student_id": user_row[3], "full_name": user_row[4]}
                        st.rerun()
                    else:
                        st.error("❌ Email ឬ លេខសម្ងាត់សិស្សមិនត្រឹមត្រូវ ឬមិនទាន់បានចុះឈ្មោះ!")

        with auth_mode[1]:
            st.info("សម្រាប់សិស្សដែលចូលប្រើលើកដំបូង សូមបំពេញព័ត៌មានខាងក្រោមដើម្បីបង្កើតគណនី៖")
            with st.form("register_form"):
                reg_email = st.text_input("អ៊ីមែល (Email)៖", placeholder="student@gmail.com").strip().lower()
                reg_pass = st.text_input("បង្កើតលេខសម្ងាត់ (Password)៖", type="password")
                reg_class = st.selectbox("ជ្រើសរើសថ្នាក់របស់អ្នក៖", CLASSES)
                reg_sid = st.text_input("អត្តលេខសិស្ស (ឧ. S001)៖").strip()
                reg_name = st.text_input("គោត្តនាម និងនាម៖").strip()
                
                if st.form_submit_button("✅ បង្កើតគណនី និងចូលរៀនភ្លាម"):
                    if reg_email and reg_pass and reg_sid and reg_name:
                        if "@" not in reg_email:
                            st.error("សូមបញ្ចូលទម្រង់ Email ឲ្យបានត្រឹមត្រូវ!")
                        else:
                            c.execute("SELECT email FROM users WHERE email = ?", (reg_email,))
                            if c.fetchone():
                                st.error("Email នេះត្រូវបានចុះឈ្មោះរួចហើយ!")
                            else:
                                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                                c.execute("INSERT INTO users (email, password, role, class_name, student_id, full_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                          (reg_email, hash_pass(reg_pass), "student", reg_class, reg_sid, reg_name, now_str))
                                conn.commit()
                                st.session_state.logged_in = True
                                st.session_state.user_info = {"role": "student", "email": reg_email, "class_name": reg_class, "student_id": reg_sid, "full_name": reg_name}
                                st.rerun()
                    else:
                        st.error("សូមបំពេញព័ត៌មានទាំងអស់ឲ្យបានគ្រប់គ្រាន់!")
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# បន្ទាប់ពី SIGN IN ជោគជ័យ
# ==============================================================================
else:
    user = st.session_state.user_info

    with st.sidebar:
        st.markdown("### 👤 ព័ត៌មានគណនី")
        if user["role"] == "teacher":
            st.success(f"**តួនាទី៖ គ្រូបង្រៀន**\n\nឈ្មោះ៖ {user['full_name']}\n\nEmail៖ {user['email']}")
        else:
            st.info(f"**តួនាទី៖ សិស្ស**\n\nឈ្មោះ៖ {user['full_name']}\n\nអត្តលេខ៖ {user['student_id']} ({user['class_name']})\n\nEmail៖ {user['email']}")
        if st.button("🚪 ចាកចេញ (Sign Out)", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = {}
            st.rerun()

    # ==========================================
    # ១. ផ្នែកសម្រាប់សិស្ស (STUDENT PORTAL)
    # ==========================================
    if user["role"] == "student":
        stu_class, stu_id, stu_name = user["class_name"], user["student_id"], user["full_name"]

        col_top1, col_top2 = st.columns([5, 1])
        with col_top1:
            st.markdown(f"👋 សូមស្វាគមន៍៖ **{stu_name}** | អត្តលេខ៖ **{stu_id}** | **{stu_class}**")
        with col_top2:
            if st.button("🚪 ចាកចេញ", key="top_logout_stu"):
                st.session_state.logged_in = False
                st.session_state.user_info = {}
                st.rerun()

        top_menu = st.radio("ម៉ឺនុយ៖", ["📘 វគ្គសិក្សា", "👥 អ្នកចូលរួម", "📊 ពិន្ទុរបស់ខ្ញុំ", "🏛️ បណ្ណាល័យ", "📝 បុរេតេស្ត & តេស្តបញ្ចប់"], horizontal=True, label_visibility="collapsed")
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

        c.execute("SELECT activity_key FROM completions WHERE student_id = ?", (stu_id,))
        completed_keys = {row[0] for row in c.fetchall()}

        if top_menu == "📘 វគ្គសិក្សា":
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 2, 2, 1])
            with col_btn2:
                with st.popover("ℹ️ សេចក្តីណែនាំពីវគ្គសិក្សា", use_container_width=True):
                    st.markdown(get_setting('course_expectation', ''), unsafe_allow_html=True)
            with col_btn3:
                with st.popover("📢 ដំណឹងថ្មីៗ", use_container_width=True):
                    c.execute("SELECT message, date FROM notifications ORDER BY id DESC LIMIT 5")
                    for msg, ndate in c.fetchall():
                        st.info(f"**[{ndate}]** {msg}")

            st.write("")
            with st.expander("⌄ ទូទៅ", expanded=True):
                st.markdown(f'<div class="welcome-banner"><h3>សូមជម្រាបសួរ {stu_name}!</h3><p>សូមស្វាគមន៍មកកាន់វគ្គសិក្សាស្តីពី <span>ចំណេះដឹងគណិតវិទ្យា</span> 🫶</p></div>', unsafe_allow_html=True)
                kc1, kc2, kc3 = st.columns(3)
                with kc1: st.markdown(f'<div class="info-card card-green"><div class="card-icon">⏱️</div><div><p class="card-title">{get_setting("card1_title", "រយៈពេលសិក្សា")}</p><p class="card-desc">{get_setting("card1_desc", "៥ សប្តាហ៍")}</p></div></div>', unsafe_allow_html=True)
                with kc2: st.markdown(f'<div class="info-card card-blue"><div class="card-icon">👥</div><div><p class="card-title">{get_setting("card2_title", "ទម្រង់សិក្សា")}</p><p class="card-desc">{get_setting("card2_desc", "ស្វ័យសិក្សា និងអនឡាញ")}</p></div></div>', unsafe_allow_html=True)
                with kc3: st.markdown(f'<div class="info-card card-pink"><div class="card-icon">💻</div><div><p class="card-title">{get_setting("card3_title", "ការវាយតម្លៃ & ផលបត្រ")}</p><p class="card-desc">{get_setting("card3_desc", "តេស្ត និងប្រគល់ផលបត្រ")}</p></div></div>', unsafe_allow_html=True)

            with st.expander("⌄ ផលបត្រ និងការប្រគល់កិច្ចការ (Portfolio) 🗂️", expanded=True):
                c.execute("SELECT id, title, description, due_date FROM portfolio_tasks ORDER BY id ASC")
                p_tasks = c.fetchall()
                c.execute("SELECT task_id FROM portfolio_submissions WHERE student_id = ?", (stu_id,))
                submitted_task_ids = {r[0] for r in c.fetchall()}

                for tid, t_title, t_desc, t_due in p_tasks:
                    is_sub = tid in submitted_task_ids
                    status_badge = '<div class="act-status-done">✓ មើល &nbsp;&nbsp; ✓ ប្រគល់កិច្ចការរួចរាល់</div>' if is_sub else f'<div class="act-status-pending">○ មើល &nbsp;&nbsp; ប្រគល់ផលបត្រ (កំណត់ត្រឹម៖ {t_due})</div>'
                    st.markdown(f'<div class="activity-row"><div class="icon-box icon-task">📤</div><div><p class="act-title">{t_title}</p>{status_badge}</div></div>', unsafe_allow_html=True)
                    with st.expander(f"ចុចទីនេះដើម្បីទម្លាក់ឯកសារផលបត្រ៖ {t_title}"):
                        st.write(t_desc)
                        up_file = st.file_uploader("📎 ជ្រើសរើសឯកសារផលបត្រ៖", type=["pdf", "docx", "doc", "xlsx", "png", "jpg", "jpeg"], key=f"pf_file_{tid}")
                        pf_note = st.text_input("កំណត់សម្គាល់បន្ថែម៖", key=f"pf_note_{tid}")
                        if st.button("📤 បញ្ជូនផលបត្រ", key=f"pf_btn_{tid}"):
                            if up_file:
                                c.execute('''INSERT INTO portfolio_submissions (task_id, class_name, student_id, student_name, file_name, file_data, note, score, date) 
                                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                          (tid, stu_class, stu_id, stu_name, up_file.name, up_file.read(), pf_note, "រង់ចាំពិនិត្យ", datetime.now().strftime("%Y-%m-%d %H:%M")))
                                conn.commit()
                                st.success("បានប្រគល់ផលបត្ររួចរាល់!")
                                st.rerun()

            with st.expander("⌄ មេរៀន និងសកម្មភាពសិក្សាប្រចាំសប្តាហ៍ (សប្តាហ៍ទី ១ - ៥) 📚", expanded=True):
                selected_week = st.selectbox("🔽 ជ្រើសរើសសប្តាហ៍សិក្សា៖", WEEKS)
                
                # ចុះវត្តមាន
                att_key = f"att_{selected_week}"
                att_done = att_key in completed_keys
                st.markdown(f'<div class="activity-row"><div class="icon-box icon-att">✅</div><div><p class="act-title">ចុះវត្តមានសិក្សាប្រចាំ {selected_week}</p>{"<div class=act-status-done>✓ រួចរាល់</div>" if att_done else "<div class=act-status-pending>○ មិនទាន់បានចុះវត្តមាន</div>"}</div></div>', unsafe_allow_html=True)
                with st.expander("ចុចដើម្បីចុះវត្តមាន"):
                    att_status = st.selectbox("ស្ថានភាព៖", ["វត្តមាន", "សុំច្បាប់"], key=f"att_s_{selected_week}")
                    if st.button("បញ្ជូនវត្តមាន", key=f"att_b_{selected_week}"):
                        today = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute("INSERT INTO attendance (class_name, student_id, student_name, week, date, status) VALUES (?, ?, ?, ?, ?, ?)", (stu_class, stu_id, stu_name, selected_week, today, att_status))
                        if not att_done:
                            c.execute("INSERT INTO completions (student_id, activity_key, date) VALUES (?, ?, ?)", (stu_id, att_key, today))
                        conn.commit()
                        st.rerun()

                # បង្ហាញបញ្ជី Learning Materials ទាំងអស់ក្នុងសប្តាហ៍នេះ
                render_week_materials(selected_week, is_teacher=False, stu_id=stu_id, completed_keys=completed_keys)

                # វេទិកាពិភាក្សា
                forum_key = f"forum_{selected_week}"
                forum_done = forum_key in completed_keys
                st.markdown(f'<div class="activity-row"><div class="icon-box icon-forum">💬</div><div><p class="act-title">វេទិកាពិភាក្សាប្រចាំ {selected_week}</p>{"<div class=act-status-done>✓ បំពេញសកម្មភាព</div>" if forum_done else "<div class=act-status-pending>○ ចូលរួមពិភាក្សា</div>"}</div></div>', unsafe_allow_html=True)
                with st.expander("បើកវេទិកាពិភាក្សា"):
                    f_msg = st.text_area("សរសេរមតិពិភាក្សា...", key=f"f_t_{selected_week}")
                    if st.button("📤 បង្ហោះ", key=f"f_b_{selected_week}"):
                        if f_msg.strip():
                            today = datetime.now().strftime("%Y-%m-%d %H:%M")
                            c.execute("INSERT INTO forum (week, class_name, author_name, role_tag, message, date) VALUES (?, ?, ?, ?, ?, ?)", (selected_week, stu_class, stu_name, "សិស្ស", f_msg.strip(), today))
                            if not forum_done:
                                c.execute("INSERT INTO completions (student_id, activity_key, date) VALUES (?, ?, ?)", (stu_id, forum_key, today))
                            conn.commit()
                            st.rerun()
                    c.execute("SELECT class_name, author_name, role_tag, message, date FROM forum WHERE week = ? ORDER BY id DESC", (selected_week,))
                    for p_cls, p_auth, p_role, p_msg, p_dt in c.fetchall():
                        badge = "👨‍🏫 គ្រូបង្រៀន" if p_role == "គ្រូ" else f"👨‍🎓 {p_cls}"
                        st.markdown(f"**{p_auth}** `[{badge}]` • *{p_dt}*")
                        st.info(p_msg)

                # តេស្តវាយតម្លៃប្រចាំសប្តាហ៍
                quiz_key = f"quiz_{selected_week}"
                quiz_done = quiz_key in completed_keys
                st.markdown(f'<div class="activity-row"><div class="icon-box icon-quiz">✍️</div><div><p class="act-title">ការវាយតម្លៃសមត្ថភាព - {selected_week}</p>{"<div class=act-status-done>✓ រួចរាល់</div>" if quiz_done else "<div class=act-status-pending>○ ធ្វើតេស្តវាយតម្លៃ</div>"}</div></div>', unsafe_allow_html=True)
                with st.expander("ចុចដើម្បីធ្វើតេស្តវាយតម្លៃ"):
                    num_q = int(get_setting('num_questions', '5'))
                    state_key = f"quiz_questions_{selected_week}"
                    if state_key not in st.session_state:
                        c.execute("SELECT id, question, opt_a, opt_b, opt_c, correct_opt FROM quizzes WHERE week = ? ORDER BY RANDOM() LIMIT ?", (selected_week, num_q))
                        st.session_state[state_key] = c.fetchall()
                    questions = st.session_state[state_key]
                    if not questions:
                        st.info("មិនទាន់មានសំណួរតេស្តទេ។")
                    else:
                        user_answers = {}
                        for idx, (q_id, q_text, a, b, c_opt, correct) in enumerate(questions, 1):
                            user_answers[q_id] = st.radio(f"សំណួរទី {idx}៖ {q_text}", [a, b, c_opt], key=f"q_{selected_week}_{q_id}")
                        if st.button("បញ្ជូនចម្លើយ", key=f"sub_q_{selected_week}"):
                            score = sum(1 for q_id, _, _, _, _, correct in questions if user_answers[q_id] == correct)
                            total = len(questions)
                            today = datetime.now().strftime("%Y-%m-%d %H:%M")
                            c.execute("INSERT INTO scores (class_name, student_id, student_name, week, score, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)", (stu_class, stu_id, stu_name, selected_week, score, total, today))
                            if not quiz_done:
                                c.execute("INSERT INTO completions (student_id, activity_key, date) VALUES (?, ?, ?)", (stu_id, quiz_key, today))
                            conn.commit()
                            st.success(f"🎉 ពិន្ទុរបស់អ្នកគឺ៖ {score} / {total}")
                            del st.session_state[state_key]
                            st.rerun()

        elif top_menu == "👥 អ្នកចូលរួម":
            st.subheader("👥 បញ្ជីឈ្មោះសិស្សដែលបានចុះឈ្មោះចូលរៀន")
            df_part = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, full_name AS ឈ្មោះសិស្ស, email AS អ៊ីមែល FROM users WHERE role = 'student' ORDER BY class_name, student_id", conn)
            st.dataframe(df_part, use_container_width=True)

        elif top_menu == "📊 ពិន្ទុរបស់ខ្ញុំ":
            st.subheader(f"📊 លទ្ធផលពិន្ទុរបស់ {stu_name} ({stu_id})")
            df_my_sc = pd.read_sql_query("SELECT week AS វិញ្ញាសា, score AS ពិន្ទុបាន, total AS ពិន្ទុពេញ, date AS កាលបរិច្ឆេទ FROM scores WHERE student_id = ?", conn, params=(stu_id,))
            st.dataframe(df_my_sc, use_container_width=True)
            df_my_pf = pd.read_sql_query("SELECT t.title AS ប្រធានបទផលបត្រ, s.file_name AS ឯកសារបានប្រគល់, s.score AS ពិន្ទុវាយតម្លៃ, s.date AS កាលបរិច្ឆេទ FROM portfolio_submissions s JOIN portfolio_tasks t ON s.task_id = t.id WHERE s.student_id = ?", conn, params=(stu_id,))
            st.dataframe(df_my_pf, use_container_width=True)

        elif top_menu == "🏛️ បណ្ណាល័យ":
            st.subheader("🏛️ បណ្ណាល័យឯកសារជំនួយការសិក្សា")
            c.execute("SELECT id, title, description, pdf_name, pdf_data, date FROM library ORDER BY id DESC")
            for b_id, b_title, b_desc, b_pdf_name, b_pdf_data, b_date in c.fetchall():
                st.markdown(f'<div class="activity-row"><div class="icon-box icon-pdf">📕</div><div><p class="act-title">{b_title}</p><div class="act-status-pending">បង្ហោះថ្ងៃទី៖ {b_date}</div></div></div>', unsafe_allow_html=True)
                with st.expander(f"អាន ឬទាញយក៖ {b_title}"):
                    st.write(b_desc)
                    if b_pdf_data and b_pdf_name:
                        st.download_button(f"📥 ទាញយក៖ {b_pdf_name}", data=b_pdf_data, file_name=b_pdf_name, key=f"lib_d_{b_id}")
                        base64_pdf = base64.b64encode(b_pdf_data).decode('utf-8')
                        st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>', unsafe_allow_html=True)

        elif top_menu == "📝 បុរេតេស្ត & តេស្តបញ្ចប់":
            t_type = st.radio("ជ្រើសរើសប្រភេទតេស្ត៖", ["📝 បុរេតេស្ត (Pre-Test)", "🎓 តេស្តបញ្ចប់វគ្គ (Final Test)"], horizontal=True)
            if t_type == "📝 បុរេតេស្ត (Pre-Test)":
                c.execute("SELECT id, question, opt_a, opt_b, opt_c, correct_opt FROM quizzes WHERE is_pretest = 1")
                pre_q = c.fetchall()
                if not pre_q: st.info("មិនទាន់មានសំណួរបុរេតេស្តនៅឡើយទេ។")
                else:
                    ans_p = {qid: st.radio(f"សំណួរទី {idx}៖ {qt}", [a, b, c_o], key=f"p_{qid}") for idx, (qid, qt, a, b, c_o, corr) in enumerate(pre_q, 1)}
                    if st.button("បញ្ជូនចម្លើយបុរេតេស្ត"):
                        sc = sum(1 for qid, _, _, _, _, corr in pre_q if ans_p[qid] == corr)
                        c.execute("INSERT INTO scores (class_name, student_id, student_name, week, score, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)", (stu_class, stu_id, stu_name, "បុរេតេស្ត (Pre-Test)", sc, len(pre_q), datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        st.success(f"🎉 ពិន្ទុបុរេតេស្តរបស់អ្នកគឺ៖ {sc} / {len(pre_q)}")
            else:
                num_f = int(get_setting('final_questions', '15'))
                if "fin_q_list" not in st.session_state:
                    c.execute("SELECT id, question, opt_a, opt_b, opt_c, correct_opt FROM quizzes ORDER BY RANDOM() LIMIT ?", (num_f,))
                    st.session_state["fin_q_list"] = c.fetchall()
                fin_q = st.session_state["fin_q_list"]
                if not fin_q: st.info("មិនទាន់មានសំណួរក្នុងឃ្លាំងទេ។")
                else:
                    ans_f = {qid: st.radio(f"សំណួរទី {idx}៖ {qt}", [a, b, c_o], key=f"f_{qid}") for idx, (qid, qt, a, b, c_o, corr) in enumerate(fin_q, 1)}
                    if st.button("បញ្ជូនចម្លើយតេស្តបញ្ចប់វគ្គ"):
                        sc = sum(1 for qid, _, _, _, _, corr in fin_q if ans_f[qid] == corr)
                        c.execute("INSERT INTO scores (class_name, student_id, student_name, week, score, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)", (stu_class, stu_id, stu_name, "តេស្តបញ្ចប់វគ្គ (Final)", sc, len(fin_q), datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        st.success(f"🏆 ពិន្ទុតេស្តបញ្ចប់វគ្គរបស់អ្នកគឺ៖ {sc} / {len(fin_q)}")
                        del st.session_state["fin_q_list"]

    # ==========================================
    # ២. ផ្នែកសម្រាប់គ្រូ (TEACHER ADMIN)
    # ==========================================
    elif user["role"] == "teacher":
        col_t1, col_t2 = st.columns([5, 1])
        with col_t1:
            st.markdown(f"👨‍🏫 គណនីគ្រប់គ្រង៖ **{user['full_name']}** (`{user['email']}`)")
        with col_t2:
            if st.button("🚪 ចាកចេញ", key="top_logout_tch"):
                st.session_state.logged_in = False
                st.session_state.user_info = {}
                st.rerun()

        t_tabs = st.tabs([
            "📚 រៀបចំមេរៀនតាមសប្តាហ៍ (Add Material)",
            "📊 របាយការណ៍ពិន្ទុ & វត្តមាន",
            "🗂️ ពិនិត្យផលបត្រសិស្ស",
            "💬 វេទិកាពិភាក្សា",
            "🏛️ បណ្ណាល័យ & ព័ត៌មានទូទៅ",
            "🏦 ឃ្លាំងសំណួរ & តេស្ត",
            "👥 គណនីសិស្ស"
        ])
        
        # --- ផ្ទាំងទី ១៖ ចូលទៅសប្តាហ៍នីមួយៗ ហើយចុចប៊ូតុង Add Learning Material ផ្ទាល់ដូច LMS ស្តង់ដារ ---
        with t_tabs[0]:
            adm_selected_week = st.selectbox("📅 ជ្រើសរើសសប្តាហ៍ដើម្បីរៀបចំ និងបន្ថែមសម្ភារៈសិក្សា៖", WEEKS, key="adm_week_view")
            
            col_hdr1, col_hdr2 = st.columns([3, 1])
            with col_hdr1:
                st.subheader(f"📖 សម្ភារៈសិក្សាក្នុង {adm_selected_week}")
            with col_hdr2:
                # ប៊ូតុង Add Learning Material នៅក្នុងសប្តាហ៍នោះផ្ទាល់!
                add_popover = st.popover("➕ Add Learning Material", use_container_width=True)
                with add_popover:
                    st.markdown(f"### ➕ បន្ថែមសម្ភារៈសិក្សាចូល {adm_selected_week}")
                    mat_type = st.selectbox("ជ្រើសរើសប្រភេទសម្ភារៈ (Material Type)៖", [
                        "ឯកសារអាន (File)",
                        "វីដេអូបង្រៀន (Video)",
                        "វីដេអូភ្ជាប់សំណួរ (H5P)",
                        "អត្ថបទមេរៀន (Page)",
                        "តំណភ្ជាប់ខាងក្រៅ (Link)",
                        "កិច្ចការ / ស្វ័យសិក្សា (Task)",
                        "សេចក្តីផ្តើម"
                    ])
                    mat_title = st.text_input("ចំណងជើងសម្ភារៈសិក្សា៖", placeholder="ឧ. មេរៀនទី ១៖ ឯកសារអាន ឬ វីដេអូបង្រៀន...")
                    
                    mat_file, mat_vid_url, mat_vid_file, mat_link = None, None, None, None
                    v_q, v_a, v_b, v_c, v_corr = None, None, None, None, None

                    # បង្ហាញប្រអប់បញ្ចូលតាមប្រភេទដែលគ្រូបានជ្រើសរើស
                    if mat_type in ["ឯកសារអាន (File)", "កិច្ចការ / ស្វ័យសិក្សា (Task)", "សេចក្តីផ្តើម"]:
                        mat_file = st.file_uploader("📎 ទម្លាក់ឯកសារ (PDF, Word, Excel, PowerPoint, រូបភាព)៖", type=["pdf", "docx", "doc", "xlsx", "pptx", "png", "jpg"])
                    
                    if mat_type in ["វីដេអូបង្រៀន (Video)", "វីដេអូភ្ជាប់សំណួរ (H5P)"]:
                        vid_source = st.radio("ប្រភពវីដេអូ៖", ["តំណភ្ជាប់ YouTube", "Upload ឯកសារវីដេអូ (MP4)"], horizontal=True)
                        if vid_source == "តំណភ្ជាប់ YouTube":
                            mat_vid_url = st.text_input("បិទភ្ជាប់ Link វីដេអូ YouTube៖", placeholder="https://www.youtube.com/watch?v=...")
                        else:
                            mat_vid_file = st.file_uploader("🎬 ជ្រើសរើសឯកសារវីដេអូ (MP4)៖", type=["mp4", "mov"])

                    if mat_type == "តំណភ្ជាប់ខាងក្រៅ (Link)":
                        mat_link = st.text_input("🔗 បិទភ្ជាប់ URL (ឧ. GeoGebra, Quizizz, Google Form)៖", placeholder="https://...")

                    if mat_type == "វីដេអូភ្ជាប់សំណួរ (H5P)":
                        st.markdown("**🎯 បង្កើតសំណួរភ្ជាប់ជាមួយវីដេអូ៖**")
                        v_q = st.text_input("សំណួរបំផុសគំនិត៖")
                        v_a = st.text_input("ជម្រើស ក")
                        v_b = st.text_input("ជម្រើស ខ")
                        v_c = st.text_input("ជម្រើស គ")
                        v_cc = st.selectbox("ចម្លើយដែលត្រឹមត្រូវ៖", ["ជម្រើស ក", "ជម្រើស ខ", "ជម្រើស គ"])
                        if v_a and v_b and v_c:
                            v_corr = {"ជម្រើស ក": v_a, "ជម្រើស ខ": v_b, "ជម្រើស គ": v_c}[v_cc]

                    mat_desc = st.text_area("សេចក្តីពណ៌នា ឬខ្លឹមសារមេរៀន (ស្រេចចិត្ត)៖")

                    if st.button("💾 រក្សាទុក និងបង្ហោះចូលសប្តាហ៍នេះ", type="primary", use_container_width=True):
                        if mat_title:
                            f_name = mat_file.name if mat_file else None
                            f_bytes = mat_file.read() if mat_file else None
                            vf_name = mat_vid_file.name if mat_vid_file else None
                            vf_bytes = mat_vid_file.read() if mat_vid_file else None
                            
                            c.execute('''INSERT INTO lessons (week, category, title, content, video_url, pdf_name, pdf_data, v_question, v_opt_a, v_opt_b, v_opt_c, v_correct, ext_link, video_blob, video_filename) 
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                                      (adm_selected_week, mat_type, mat_title, mat_desc, mat_vid_url, f_name, f_bytes, v_q, v_a, v_b, v_c, v_corr, mat_link, vf_bytes, vf_name))
                            conn.commit()
                            st.success(f"បានបន្ថែម «{mat_title}» ដោយជោគជ័យ!")
                            st.rerun()
                        else:
                            st.error("សូមបញ្ចូលចំណងជើង!")

            st.divider()
            # បង្ហាញសម្ភារៈសិក្សាទាំងអស់ដែលមានក្នុងសប្តាហ៍នេះ ឲ្យគ្រូពិនិត្យ និងអាចចុចលុបបានភ្លាមៗ
            render_week_materials(adm_selected_week, is_teacher=True)

        # --- ផ្ទាំងទី ២៖ របាយការណ៍ពិន្ទុ និងវត្តមាន ---
        with t_tabs[1]:
            filter_class = st.selectbox("🏫 ជ្រើសរើសថ្នាក់៖", ["ទាំងអស់"] + CLASSES)
            st.subheader("១. តារាងបូកសរុបពិន្ទុតេស្ត")
            if filter_class == "ទាំងអស់":
                df_scores = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS ប្រភេទតេស្ត, score AS ពិន្ទុបាន, total AS ពិន្ទុពេញ, date AS កាលបរិច្ឆេទ FROM scores", conn)
            else:
                df_scores = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS ប្រភេទតេស្ត, score AS ពិន្ទុបាន, total AS ពិន្ទុពេញ, date AS កាលបរិច្ឆេទ FROM scores WHERE class_name = ?", conn, params=(filter_class,))
            
            if not df_scores.empty:
                pivot_scores = df_scores.pivot_table(index=['ថ្នាក់', 'អត្តលេខ', 'ឈ្មោះសិស្ស'], columns='ប្រភេទតេស្ត', values='ពិន្ទុបាន', aggfunc='max', fill_value=0).reset_index()
                score_cols = [col for col in pivot_scores.columns if col not in ['ថ្នាក់', 'អត្តលេខ', 'ឈ្មោះសិស្ស']]
                pivot_scores['ពិន្ទុសរុបរួម'] = pivot_scores[score_cols].sum(axis=1)
                st.dataframe(pivot_scores, use_container_width=True)
                st.download_button(f"📥 ទាញយកតារាងពិន្ទុ ({filter_class})", pivot_scores.to_csv(index=False).encode('utf-8-sig'), f"scores_{filter_class}.csv", "text/csv")
            else:
                st.info("មិនទាន់មានទិន្នន័យពិន្ទុទេ។")

            st.divider()
            st.subheader("២. តារាងវត្តមានសិស្ស")
            if filter_class == "ទាំងអស់":
                df_att = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS សប្តាហ៍, status AS ស្ថានភាព, date AS កាលបរិច្ឆេទ FROM attendance", conn)
            else:
                df_att = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, student_name AS ឈ្មោះសិស្ស, week AS សប្តាហ៍, status AS ស្ថានភាព, date AS កាលបរិច្ឆេទ FROM attendance WHERE class_name = ?", conn, params=(filter_class,))
            st.dataframe(df_att, use_container_width=True)
            if not df_att.empty:
                st.download_button(f"📥 ទាញយកបញ្ជីវត្តមាន ({filter_class})", df_att.to_csv(index=False).encode('utf-8-sig'), f"attendance_{filter_class}.csv", "text/csv")

        # --- ផ្ទាំងទី ៣៖ គ្រប់គ្រង និងពិនិត្យផលបត្រសិស្ស ---
        with t_tabs[2]:
            st.subheader("🗂️ ១. បង្កើតប្រធានបទផលបត្រថ្មី")
            with st.form("new_pf_task"):
                pt_title = st.text_input("ចំណងជើងផលបត្រ")
                pt_desc = st.text_area("សេចក្តីណែនាំសម្រាប់សិស្ស")
                pt_due = st.text_input("កាលបរិច្ឆេទផុតកំណត់")
                if st.form_submit_button("➕ បង្កើតប្រអប់ទទួលផលបត្រ"):
                    if pt_title:
                        c.execute("INSERT INTO portfolio_tasks (title, description, due_date) VALUES (?, ?, ?)", (pt_title, pt_desc, pt_due))
                        conn.commit()
                        st.rerun()

            st.divider()
            st.subheader("📥 ២. ពិនិត្យ ទាញយក និងដាក់ពិន្ទុផលបត្រសិស្ស")
            c.execute('''SELECT s.id, t.title, s.class_name, s.student_id, s.student_name, s.file_name, s.file_data, s.note, s.score, s.date 
                         FROM portfolio_submissions s JOIN portfolio_tasks t ON s.task_id = t.id ORDER BY s.id DESC''')
            for sid_sub, t_name, s_cls, s_id_num, s_nm, f_nm, f_bytes, s_note, s_sc, s_dt in c.fetchall():
                with st.expander(f"📄 [{s_cls}] {s_nm} ({s_id_num}) - {t_name} | ពិន្ទុ៖ {s_sc}"):
                    st.write(f"**ឈ្មោះឯកសារ៖** {f_nm} | **ប្រគល់នៅ៖** {s_dt}")
                    st.download_button(f"📥 ទាញយកឯកសារ៖ {f_nm}", data=f_bytes, file_name=f_nm, key=f"adm_dl_pf_{sid_sub}")
                    col_g1, col_g2 = st.columns([2, 1])
                    with col_g1: new_grade = st.text_input("ដាក់ពិន្ទុ ឬមតិវាយតម្លៃ៖", value=s_sc, key=f"grd_in_{sid_sub}")
                    with col_g2:
                        st.write(""); st.write("")
                        if st.button("រក្សាទុកពិន្ទុ", key=f"grd_btn_{sid_sub}"):
                            c.execute("UPDATE portfolio_submissions SET score = ? WHERE id = ?", (new_grade, sid_sub))
                            conn.commit()
                            st.rerun()

        # --- ផ្ទាំងទី ៤៖ វេទិកាពិភាក្សា ---
        with t_tabs[3]:
            f_w_adm = st.selectbox("ជ្រើសរើសសប្តាហ៍៖", WEEKS, key="f_w_a")
            with st.form("adm_f_rep"):
                rep = st.text_area("ឆ្លើយតបសិស្ស...")
                if st.form_submit_button("📢 បង្ហោះ"):
                    if rep.strip():
                        c.execute("INSERT INTO forum (week, class_name, author_name, role_tag, message, date) VALUES (?, ?, ?, ?, ?, ?)",
                                  (f_w_adm, "គ្រប់ថ្នាក់", user['full_name'], "គ្រូ", rep.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        st.rerun()
            c.execute("SELECT id, class_name, author_name, role_tag, message, date FROM forum WHERE week = ? ORDER BY id DESC", (f_w_adm,))
            for fid, fcls, fauth, frole, fmsg, fdate in c.fetchall():
                col1, col2 = st.columns([6, 1])
                col1.markdown(f"**{fauth}** ({fcls} - {frole}) • *{fdate}*: {fmsg}")
                if col2.button("លុប", key=f"df_{fid}"):
                    c.execute("DELETE FROM forum WHERE id = ?", (fid,))
                    conn.commit()
                    st.rerun()

        # --- ផ្ទាំងទី ៥៖ បណ្ណាល័យ & ព័ត៌មានទូទៅ ---
        with t_tabs[4]:
            st.subheader("🏛️ បញ្ចូលឯកសារទៅក្នុងបណ្ណាល័យរួម")
            with st.form("lib_f"):
                bt = st.text_input("ចំណងជើងឯកសារ")
                bd = st.text_area("ការពិពណ៌នា")
                bp = st.file_uploader("ឯកសារ PDF", type=["pdf"])
                if st.form_submit_button("បញ្ចូលក្នុងបណ្ណាល័យ"):
                    if bt and bp:
                        c.execute("INSERT INTO library (title, description, pdf_name, pdf_data, date) VALUES (?, ?, ?, ?, ?)", (bt, bd, bp.name, bp.read(), datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        st.success("បានបញ្ចូលរួចរាល់!")

            st.divider()
            st.subheader("🎯 កែសម្រួល «សេចក្តីណែនាំពីវគ្គសិក្សា» (Word Editor) & ដំណឹង")
            exp_html = st_quill(value=get_setting('course_expectation', ''), html=True, key="exp_q")
            if st.button("💾 រក្សាទុកសេចក្តីណែនាំពីវគ្គសិក្សា"):
                c.execute("UPDATE settings SET value = ? WHERE key = 'course_expectation'", (exp_html,))
                conn.commit()
                st.success("បានរក្សាទុក!")

            with st.form("n_form"):
                n_msg = st.text_area("បង្ហោះសេចក្តីជូនដំណឹងថ្មី")
                if st.form_submit_button("📢 បង្ហោះដំណឹង"):
                    if n_msg.strip():
                        c.execute("INSERT INTO notifications (message, date) VALUES (?, ?)", (n_msg.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        st.success("បានបង្ហោះដំណឹង!")

        # --- ផ្ទាំងទី ៦៖ ឃ្លាំងសំណួរ & តេស្ត ---
        with t_tabs[5]:
            st.subheader("📤 Upload សំណួរច្រើន (CSV/Excel)")
            sample_df = pd.DataFrame({
                "week": ["សប្តាហ៍ទី ១", "សប្តាហ៍ទី ២"],
                "question": ["តើ 2 + 3 ស្មើប៉ុន្មាន?", "តើរូបមន្តក្រឡាផ្ទៃការ៉េគឺជាអ្វី?"],
                "opt_a": ["4", "S = a × a"],
                "opt_b": ["5", "S = 4 × a"],
                "opt_c": ["6", "S = a + b"],
                "correct_opt": ["5", "S = a × a"]
            })
            st.download_button("📥 ទាញយកតារាងគំរូ (Template.csv)", sample_df.to_csv(index=False).encode('utf-8-sig'), "quiz_template.csv", "text/csv")
            up_csv = st.file_uploader("ជ្រើសរើសឯកសារ CSV", type=["csv"])
            if up_csv and st.button("🚀 បញ្ចូលសំណួរទាំងអស់"):
                df_u = pd.read_csv(up_csv)
                for _, r in df_u.iterrows():
                    c.execute("INSERT INTO quizzes (week, question, opt_a, opt_b, opt_c, correct_opt) VALUES (?, ?, ?, ?, ?, ?)",
                              (str(r['week']).strip(), str(r['question']).strip(), str(r['opt_a']).strip(), str(r['opt_b']).strip(), str(r['opt_c']).strip(), str(r['correct_opt']).strip()))
                conn.commit()
                st.success("បានបញ្ចូលសំណួរដោយជោគជ័យ!")

            st.divider()
            st.subheader("📝 ជ្រើសរើសសំណួរសម្រាប់ «បុរេតេស្ត (Pre-Test)»")
            df_aq = pd.read_sql_query("SELECT id, week, question, correct_opt, is_pretest FROM quizzes", conn)
            if not df_aq.empty:
                sel_ids = [r['id'] for _, r in df_aq.iterrows() if st.checkbox(f"[{r['week']}] {r['question']}", value=bool(r['is_pretest'] == 1), key=f"cp_{r['id']}")]
                if st.button("💾 រក្សាទុកបុរេតេស្ត"):
                    c.execute("UPDATE quizzes SET is_pretest = 0")
                    for qid in sel_ids:
                        c.execute("UPDATE quizzes SET is_pretest = 1 WHERE id = ?", (qid,))
                    conn.commit()
                    st.success("បានរក្សាទុក!")

            st.divider()
            c1, c2 = st.columns(2)
            with c1: wn = st.number_input("ចំនួនសំណួរតេស្តប្រចាំសប្តាហ៍៖", 1, 50, int(get_setting('num_questions', '5')))
            with c2: fn = st.number_input("ចំនួនសំណួរតេស្តបញ្ចប់វគ្គ៖", 1, 100, int(get_setting('final_questions', '15')))
            if st.button("រក្សាទុកចំនួនសំណួរ"):
                c.execute("UPDATE settings SET value = ? WHERE key = 'num_questions'", (str(wn),))
                c.execute("UPDATE settings SET value = ? WHERE key = 'final_questions'", (str(fn),))
                conn.commit()
                st.success("បានរក្សាទុក!")

        # --- ផ្ទាំងទី ៧៖ គ្រប់គ្រងគណនីសិស្ស ---
        with t_tabs[6]:
            st.subheader("👥 បញ្ជីគណនីសិស្សដែលបានចុះឈ្មោះក្នុងប្រព័ន្ធ")
            df_users = pd.read_sql_query("SELECT class_name AS ថ្នាក់, student_id AS អត្តលេខ, full_name AS ឈ្មោះសិស្ស, email AS អ៊ីមែល, created_at AS ថ្ងៃចុះឈ្មោះ FROM users WHERE role = 'student'", conn)
            st.dataframe(df_users, use_container_width=True)
            if not df_users.empty:
                st.download_button("📥 ទាញយកបញ្ជីគណនីសិស្ស (CSV)", df_users.to_csv(index=False).encode('utf-8-sig'), "registered_students.csv", "text/csv")
