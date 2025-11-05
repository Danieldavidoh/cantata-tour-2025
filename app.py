import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
import time

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =============================================
# 세션 초기화
# =============================================
if "admin" not in st.session_state:
    st.session_state.admin = False
if "lang" not in st.session_state:
    st.session_state.lang = "ko"
if "last_notice_count" not in st.session_state:
    st.session_state.last_notice_count = 0
if "route" not in st.session_state:
    st.session_state.route = []
if "venues" not in st.session_state:
    st.session_state.venues = {}

# =============================================
# 다국어 (한국어, 영어, 힌디어)
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "caption": "마하라스트라 지역 투어 관리 시스템",
        "tab_notice": "공지 관리",
        "tab_map": "투어 경로",
        "add_notice": "새 공지 추가",
        "title_label": "제목",
        "content_label": "내용",
        "upload_image": "이미지 업로드 (선택)",
        "upload_file": "파일 업로드 (선택)",
        "submit": "등록",
        "warning": "제목과 내용을 모두 입력해주세요.",
        "notice_list": "공지 목록",
        "no_notice": "등록된 공지가 없습니다.",
        "delete": "삭제",
        "map_title": "경로 보기",
        "admin_login": "관리자 로그인",
        "password": "비밀번호",
        "login": "로그인",
        "logout": "로그아웃",
        "wrong_pw": "비밀번호가 틀렸습니다.",
        "lang_select": "언어 선택",
        "file_download": "파일 다운로드",
        "add_city": "도시 추가",
        "select_city": "도시 선택",
        "add_city_btn": "추가",
        "tour_route": "투어 경로",
        "venue_name": "공연장 이름",
        "seats": "좌석 수",
        "google_link": "구글 지도 링크",
        "special_notes": "특이사항",
        "register": "등록",
        "navigate": "길찾기",
        "enter_venue_name": "공연장 이름을 입력하세요.",
        "venue_registered": "등록 완료",
        "indoor": "실내",
        "outdoor": "실외"
    },
    "en": {
        "title": "Cantata Tour 2025",
        "caption": "Maharashtra Region Tour Management System",
        "tab_notice": "Notice Management",
        "tab_map": "Tour Route",
        "add_notice": "Add Notice",
        "title_label": "Title",
        "content_label": "Content",
        "upload_image": "Upload Image (Optional)",
        "upload_file": "Upload File (Optional)",
        "submit": "Submit",
        "warning": "Please fill in both title and content.",
        "notice_list": "Notice List",
        "no_notice": "No notices registered.",
        "delete": "Delete",
        "map_title": "View Route",
        "admin_login": "Admin Login",
        "password": "Password",
        "login": "Login",
        "logout": "Logout",
        "wrong_pw": "Incorrect password.",
        "lang_select": "Language Selection",
        "file_download": "File Download",
        "add_city": "Add City",
        "select_city": "Select City",
        "add_city_btn": "Add",
        "tour_route": "Tour Route",
        "venue_name": "Venue Name",
        "seats": "Seat Count",
        "google_link": "Google Maps Link",
        "special_notes": "Special Notes",
        "register": "Register",
        "navigate": "Navigate",
        "enter_venue_name": "Please enter venue name.",
        "venue_registered": "Registration complete",
        "indoor": "Indoor",
        "outdoor": "Outdoor"
    },
    "hi": {
        "title": "कांताता टूर 2025",
        "caption": "महाराष्ट्र क्षेत्र यात्रा प्रबंधन प्रणाली",
        "tab_notice": "सूचना प्रबंधन",
        "tab_map": "टूर मार्ग",
        "add_notice": "नई सूचना जोड़ें",
        "title_label": "शीर्षक",
        "content_label": "सामग्री",
        "upload_image": "छवि अपलोड करें (वैकल्पिक)",
        "upload_file": "फ़ाइल अपलोड करें (वैकल्पिक)",
        "submit": "जमा करें",
        "warning": "कृपया शीर्षक और सामग्री दोनों भरें।",
        "notice_list": "सूचना सूची",
        "no_notice": "कोई सूचना पंजीकृत नहीं।",
        "delete": "हटाएं",
        "map_title": "मार्ग देखें",
        "admin_login": "एडमिन लॉगिन",
        "password": "पासवर्ड",
        "login": "लॉगिन",
        "logout": "लॉगआउट",
        "wrong_pw": "गलत पासवर्ड।",
        "lang_select": "भाषा चयन",
        "file_download": "फ़ाइल डाउनलोड",
        "add_city": "शहर जोड़ें",
        "select_city": "शहर चुनें",
        "add_city_btn": "जोड़ें",
        "tour_route": "टूर मार्ग",
        "venue_name": "स्थल का नाम",
        "seats": "सीटों की संख्या",
        "google_link": "गूगल मैप्स लिंक",
        "special_notes": "विशेष टिप्पणियाँ",
        "register": "पंजीकृत करें",
        "navigate": "नेविगेट करें",
        "enter_venue_name": "कृपया स्थल का नाम दर्ज करें।",
        "venue_registered": "पंजीकरण पूर्ण",
        "indoor": "इनडोर",
        "outdoor": "आउटडोर"
    }
}

_ = LANG[st.session_state.lang]

# =============================================
# JSON 유틸
# =============================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_file_download_link(file_path, label):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">{label}</a>'

# =============================================
# 공지 추가/삭제
# =============================================
def add_notice(title, content, image_file=None, upload_file=None):
    img_path, file_path = None, None
    if image_file:
        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_file.name}")
        with open(img_path, "wb") as f:
            f.write(image_file.read())
    if upload_file:
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{upload_file.name}")
        with open(file_path, "wb") as f:
            f.write(upload_file.read())
    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now().strftime("%m/%d %H:%M"),
        "image": img_path,
        "file": file_path
    }
    data = load_json(NOTICE_FILE)
    data.insert(0, new_notice)
    save_json(NOTICE_FILE, data)
    st.toast("공지가 등록되었습니다.")
    st.rerun()

def delete_notice(notice_id):
    data = load_json(NOTICE_FILE)
    for n in data:
        if n["id"] == notice_id:
            if n.get("image") and os.path.exists(n["image"]):
                os.remove(n["image"])
            if n.get("file") and os.path.exists(n["file"]):
                os.remove(n["file"])
    data = [n for n in data if n["id"] != notice_id]
    save_json(NOTICE_FILE, data)
    st.toast("공지가 삭제되었습니다.")
    st.rerun()

# =============================================
# 공지 리스트
# =============================================
def render_notice_list(show_delete=False):
    data = load_json(NOTICE_FILE)
    if not data:
        st.info(_["no_notice"])
        return
    for idx, n in enumerate(data):
        with st.expander(f"{n['date']} | {n['title']}"):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                st.markdown(get_file_download_link(n["file"], _["file_download"]), unsafe_allow_html=True)
            if show_delete:
                if st.button(_["delete"], key=f"del_{n['id']}_{idx}"):
                    delete_notice(n["id"])

# =============================================
# 도시 리스트 (150개 도시, 알파벳 순)
# =============================================
CITIES = sorted([
    "Mumbai", "Pune", "Nagpur", "Nashik", "Thane", "Aurangabad", "Solapur", "Kolhapur",
    "Amravati", "Jalgaon", "Akola", "Latur", "Ahmednagar", "Dhule", "Chandrapur", "Parbhani",
    "Jalna", "Bhusawal", "Satara", "Beed", "Yavatmal", "Gondia", "Wardha", "Nandurbar", "Osmanabad",
    "Hingoli", "Buldhana", "Washim", "Gadchiroli", "Sangli", "Ratnagiri", "Sindhudurg", "Nanded",
    "Palghar", "Raigad", "Baramati", "Karad", "Pandharpur", "Malegaon", "Ichalkaranji", "Bhiwandi",
    "Ambarnath", "Ulhasnagar", "Panvel", "Kalyan", "Vasai", "Virar", "Mira-Bhayandar", "Khopoli",
    "Alibag", "Boisar", "Dombivli", "Badlapur", "Talegaon", "Chiplun", "Mahad", "Roha", "Pen",
    "Murbad", "Khed", "Satana", "Sinnar", "Shirdi", "Sangamner", "Manmad", "Shahada", "Bodwad",
    "Raver", "Malkapur", "Nandura", "Shegaon", "Daryapur", "Mangrulpir", "Pusad", "Umarkhed",
    "Wani", "Ballarpur", "Bhandara", "Tumsar", "Deoli", "Selu", "Pathri", "Gangakhed", "Ambajogai",
    "Majalgaon", "Parli", "Nilanga", "Ausa", "Udgir", "Loha", "Hadgaon", "Kinwat", "Pusad", "Mehkar",
    "Chikhli", "Deulgaon Raja", "Lonar", "Risod", "Malegaon Camp", "Ozar", "Lasalgaon", "Yeola",
    "Trimbak", "Surgana", "Dahanu", "Jawhar", "Talasari", "Vikramgad", "Mokhada", "Khalapur",
    "Mhasla", "Shrivardhan", "Dapoli", "Guhagar", "Lanja", "Rajapur", "Deogad", "Kankavli",
    "Kudal", "Sawantwadi", "Dodamarg", "Vita", "Khanapur", "Islampur", "Tasgaon", "Miraj", "Uran",
    "Murbad", "Karjat", "Ambegaon", "Junnar", "Rajgurunagar", "Daund", "Indapur", "Karmala", "Barshi",
    "Madha", "Mohol", "Malshiras", "Akkalkot", "Phaltan", "Patan", "Khatav", "Koregaon", "Man", "Wai"
])

# =============================================
# 좌표 데이터
# =============================================
COORDS = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
    "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Kolhapur": (16.70, 74.24),
    "Amravati": (20.93, 77.75), "Jalgaon": (21.00, 75.57), "Akola": (20.70, 77.00), "Latur": (18.40, 76.57),
    "Ahmednagar": (19.10, 74.75), "Dhule": (20.90, 74.77), "Chandrapur": (19.95, 79.30), "Parbhani": (19.27, 76.77),
    "Jalna": (19.85, 75.89), "Bhusawal": (21.05, 76.00), "Satara": (17.68, 74.02), "Beed": (18.99, 75.76),
    "Yavatmal": (20.39, 78.12), "Gondia": (21.46, 80.19), "Wardha": (20.75, 78.60), "Nandurbar": (21.37, 74.22),
    "Osmanabad": (18.18, 76.07), "Hingoli": (19.72, 77.15), "Buldhana": (20.54, 76.18), "Washim": (20.11, 77.13),
    "Gadchiroli": (20.09, 80.11), "Sangli": (16.85, 74.57), "Ratnagiri": (16.99, 73.31), "Sindhudurg": (16.24, 73.42),
    "Nanded": (19.16, 77.31), "Palghar": (19.70, 72.77), "Raigad": (18.74, 73.30), "Baramati": (18.23, 74.58),
    "Karad": (17.29, 74.18), "Pandharpur": (17.66, 75.32), "Malegaon": (20.55, 74.53), "Ichalkaranji": (16.69, 74.47),
    "Bhiwandi": (19.30, 73.06), "Ambarnath": (19.06, 73.15), "Ulhasnagar": (19.22, 73.16), "Panvel": (18.99, 73.11),
    "Kalyan": (19.24, 73.13), "Vasai": (19.37, 72.81), "Virar": (19.46, 72.81), "Mira-Bhayandar": (19.28, 72.87),
    "Khopoli": (18.79, 73.35), "Alibag": (18.64, 72.87), "Boisar": (19.80, 72.75), "Dombivli": (19.21, 73.09),
    "Badlapur": (19.15, 73.12), "Talegaon": (18.93, 73.69), "Chiplun": (17.53, 73.18), "Mahad": (17.55, 73.42),
    "Roha": (18.44, 73.12), "Pen": (18.75, 73.10), "Murbad": (19.28, 73.39), "Khed": (18.89, 73.85),
        "Satana": (20.67, 74.20), "Sinnar": (20.00, 74.22), "Shirdi": (19.77, 74.62), "Sangamner": (19.57, 74.22),
        "Manmad": (20.21, 74.13), "Shahada": (21.54, 74.47), "Bodwad": (21.03, 76.15), "Raver": (21.24, 75.78),
        "Malkapur": (20.89, 76.22), "Nandura": (20.83, 76.46), "Shegaon": (20.79, 76.69), "Daryapur": (21.23, 77.33),
        "Mangrulpir": (20.31, 77.05), "Pusad": (19.91, 77.57), "Umarkhed": (19.73, 77.69), "Wani": (20.05, 78.95),
        "Ballarpur": (19.84, 79.18), "Bhandara": (21.17, 79.65), "Tumsar": (21.37, 79.75), "Deoli": (20.40, 78.10),
        "Selu": (19.95, 76.45), "Pathri": (19.22, 76.49), "Gangakhed": (18.97, 76.76), "Ambajogai": (18.74, 76.38),
        "Majalgaon": (18.75, 76.21), "Parli": (18.86, 76.52), "Nilanga": (18.13, 77.12), "Ausa": (18.65, 76.39),
        "Udgir": (18.73, 77.12), "Loha": (19.10, 77.81), "Hadgaon": (19.49, 77.36), "Kinwat": (19.62, 78.18),
        "Pusad": (19.91, 77.57), "Mehkar": (20.15, 76.57), "Chikhli": (20.35, 76.25), "Deulgaon Raja": (20.02, 76.53),
        "Lonar": (20.14, 76.53), "Risod": (20.00, 76.78), "Malegaon Camp": (20.55, 74.53), "Ozar": (20.09, 73.91),
        "Lasalgaon": (20.14, 74.23), "Yeola": (20.14, 74.43), "Trimbak": (19.93, 73.53), "Surgana": (20.56, 73.55),
        "Dahanu": (20.03, 72.71), "Jawhar": (19.90, 73.10), "Talasari": (20.13, 72.93), "Vikramgad": (19.83, 73.06),
        "Mokhada": (20.03, 73.30), "Khalapur": (18.79, 73.28), "Mhasla": (18.45, 73.00), "Shrivardhan": (18.05, 73.01),
        "Dapoli": (17.44, 73.13), "Guhagar": (17.31, 73.12), "Lanja": (17.31, 73.31), "Rajapur": (16.95, 73.36),
        "Deogad": (16.66, 73.40), "Kankavli": (16.26, 73.71), "Kudal": (16.02, 73.74), "Sawantwadi": (15.90, 73.81),
        "Dodamarg": (15.74, 74.09), "Vita": (17.25, 74.53), "Khanapur": (16.64, 74.51), "Islampur": (16.70, 74.29),
        "Tasgaon": (16.68, 74.56), "Miraj": (16.82, 74.62), "Uran": (18.81, 72.91), "Murbad": (19.28, 73.39),
        "Karjat": (19.12, 73.33), "Ambegaon": (18.79, 73.80), "Junnar": (19.20, 73.87), "Rajgurunagar": (18.87, 73.87),
        "Daund": (18.47, 74.24), "Indapur": (18.11, 74.03), "Karmala": (17.93, 74.95), "Barshi": (17.23, 75.69),
        "Madha": (17.57, 75.41), "Mohol": (17.58, 75.42), "Malshiras": (17.26, 75.04), "Akkalkot": (17.23, 76.20),
        "Phaltan": (17.98, 74.43), "Patan": (17.31, 74.13), "Khatav": (17.23, 74.44), "Koregaon": (17.68, 74.06),
        "Man": (17.24, 74.29), "Wai": (17.95, 73.89)
    ]

# =============================================
# 공지 추가/삭제
# =============================================
def add_notice(title, content, image_file=None, upload_file=None):
    img_path, file_path = None, None
    if image_file:
        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_file.name}")
        with open(img_path, "wb") as f:
            f.write(image_file.read())
    if upload_file:
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{upload_file.name}")
        with open(file_path, "wb") as f:
            f.write(upload_file.read())
    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now().strftime("%m/%d %H:%M"),
        "image": img_path,
        "file": file_path
    }
    data = load_json(NOTICE_FILE)
    data.insert(0, new_notice)
    save_json(NOTICE_FILE, data)
    st.toast("공지가 등록되었습니다.")
    st.rerun()

def delete_notice(notice_id):
    data = load_json(NOTICE_FILE)
    for n in data:
        if n["id"] == notice_id:
            if n.get("image") and os.path.exists(n["image"]):
                os.remove(n["image"])
            if n.get("file") and os.path.exists(n["file"]):
                os.remove(n["file"])
    data = [n for n in data if n["id"] != notice_id]
    save_json(NOTICE_FILE, data)
    st.toast("공지가 삭제되었습니다.")
    st.rerun()

# =============================================
# 공지 리스트
# =============================================
def render_notice_list(show_delete=False):
    data = load_json(NOTICE_FILE)
    if not data:
        st.info(_["no_notice"])
        return
    for idx, n in enumerate(data):
        with st.expander(f"{n['date']} | {n['title']}"):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                st.markdown(get_file_download_link(n["file"], _["file_download"]), unsafe_allow_html=True)
            if show_delete:
                if st.button(_["delete"], key=f"del_{n['id']}_{idx}"):
                    delete_notice(n["id"])

# =============================================
# 자동 새로고침 (10초마다)
# =============================================
def auto_refresh():
    if not st.session_state.admin:
        count = len(load_json(NOTICE_FILE))
        if st.session_state.last_notice_count == 0:
            st.session_state.last_notice_count = count
        time.sleep(10)
        new_count = len(load_json(NOTICE_FILE))
        if new_count > st.session_state.last_notice_count:
            st.toast("새 공지가 등록되었습니다!")
            st.session_state.last_notice_count = new_count
        st.rerun()

if not st.session_state.admin:
    auto_refresh()

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    st.markdown("### 언어 선택")
    lang_options = ["ko", "en", "hi"]
    lang_labels = ["한국어", "English", "हिन्दी"]
    current_idx = lang_options.index(st.session_state.lang)
    new_lang = st.selectbox(
        "언어 선택",
        lang_options,
        format_func=lambda x: lang_labels[lang_options.index(x)],
        index=current_idx
    )
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")
    if not st.session_state.admin:
        st.markdown("### 관리자 로그인")
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if pw == "0000":
                st.session_state.admin = True
                st.success("관리자 모드 ON")
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃"):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 메인
# =============================================
st.markdown(f"# {_['title']} 🎄")
st.caption(_["caption"])

tab1, tab2 = st.tabs([_["tab_notice"], _["tab_map"]])

# =============================================
# 공지 탭
# =============================================
with tab1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_["title_label"])
            c = st.text_area(_["content_label"])
            img = st.file_uploader(_["upload_image"], type=["png", "jpg", "jpeg"])
            f = st.file_uploader(_["upload_file"])
            if st.form_submit_button(_["submit"]):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_["warning"])
        render_notice_list(show_delete=True)
    else:
        render_notice_list(show_delete=False)
        if st.button("새로고침"):
            st.rerun()

# =============================================
# 투어 경로 탭
# =============================================
with tab2:
    # 관리자 전용 도시 추가
    if st.session_state.admin:
        with st.expander("도시 추가", expanded=False):
            st.markdown("#### 공연 도시 입력")
            selected_city = st.selectbox("도시 선택", CITIES, index=0)
            col1, col2 = st.columns([3, 1])
            with col1:
                venue_input = st.text_input(_["venue_name"])
            with col2:
                seat_count = st.number_input(_["seats"], value=0, step=50, min_value=0)
            google_link = st.text_input(_["google_link"])
            notes = st.text_area(_["special_notes"])
            indoor_outdoor = st.radio("형태", [_["indoor"], _["outdoor"]], horizontal=True)
            if st.button(_["register"], key="register_city_main"):
                if selected_city == "공연없음":
                    st.warning("도시를 선택해주세요.")
                elif not venue_input:
                    st.error(_["enter_venue_name"])
                else:
                    if selected_city not in st.session_state.route:
                        st.session_state.route.append(selected_city)
                    if selected_city not in st.session_state.venues:
                        st.session_state.venues[selected_city] = []
                    st.session_state.venues[selected_city].append({
                        "Venue": venue_input,
                        "Seats": seat_count,
                        "Google Maps Link": google_link,
                        "Special Notes": notes,
                        "IndoorOutdoor": indoor_outdoor
                    })
                    st.success(_["venue_registered"])
                    st.rerun()

    # 투어 경로 표시
    st.subheader(_["tour_route"])
    for city in st.session_state.route:
        venues = st.session_state.venues.get(city, [])
        car_icon = ""
        if venues:
            link = venues[0]["Google Maps Link"]
            if link and link.startswith("http"):
                car_icon = f'<span style="float:right">[자동차]({link})</span>'
        with st.expander(f"**{city}**{car_icon}", expanded=False):
            if venues:
                for v in venues:
                    st.write(f"**{v['Venue']}**")
                    st.caption(f"{v['Seats']} {_['seats']} | {v.get('Special Notes','')} | {v['IndoorOutdoor']}")
                    if v["Google Maps Link"].startswith("http"):
                        st.markdown(f'<div style="text-align:right">[자동차]({v["Google Maps Link"]})</div>', unsafe_allow_html=True)

    # 지도 (이전 단계 기준)
    st.subheader("Tour Map")
    if st.session_state.route:
        center = (19.75, 75.71)
        m = folium.Map(location=center, zoom_start=7, tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google")
        points = []
        for city in st.session_state.route:
            lat, lon = coords.get(city, center)
            points.append((lat, lon))
            venues = st.session_state.venues.get(city, [])
            popup_lines = []
            for v in venues:
                line = f"<b>{v['Venue']}</b><br>{v['Seats']}석 | {v['IndoorOutdoor']}"
                if v.get('Special Notes'):
                    line += f"<br>{v['Special Notes']}"
                if v["Google Maps Link"].startswith("http"):
                    line += f"<br><a href='{v['Google Maps Link']}' target='_blank'>자동차 구글맵</a>"
                popup_lines.append(line + "<hr>")
            popup_html = "<br>".join(popup_lines)
            folium.CircleMarker(
                location=[lat, lon],
                radius=12,
                color="#90EE90",
                fill_color="#8B0000",
                popup=folium.Popup(popup_html, max_width=450),
                tooltip=None
            ).add_to(m)
        if len(points) > 1:
            folium.PolyLine(points, color="red", weight=4).add_to(m)
        st_folium(m, width=700, height=500)
    else:
        st.info("등록된 도시가 없습니다.")
