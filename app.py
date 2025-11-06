import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone
from streamlit_autorefresh import st_autorefresh

# 3초 새로고침 (일반 모드)
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh")

# 기본 설정
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 세션 초기화
defaults = {
    "admin": False,
    "lang": "ko",
    "edit_city": None,
    "expanded": {},
    "adding_cities": []
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 다국어 딕셔너리
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "caption": "마하라스트라 투어 관리 시스템",
        "tab_notice": "공지 관리",
        "tab_map": "투어 경로",
        "map_title": "경로 보기",
        "add_city": "도시 추가",  # ← 여기 변경!
        "password": "비밀번호",
        "login": "로그인",
        "logout": "로그아웃",
        "wrong_pw": "비밀번호가 틀렸습니다.",
        "select_city": "도시 선택",
        "venue": "공연장소",
        "seats": "예상 인원",
        "note": "특이사항",
        "google_link": "구글맵 링크",
        "indoor": "실내",
        "outdoor": "실외",
        "register": "등록",
        "edit": "수정",
        "remove": "삭제",
        "date": "등록일",
        "performance_date": "공연 날짜",
        "cancel": "취소",
        "title_label": "제목",
        "content_label": "내용",
        "upload_image": "이미지 업로드",
        "upload_file": "파일 업로드",
        "submit": "등록",
        "warning": "제목과 내용을 모두 입력해주세요.",
        "file_download": "파일 다운로드",
    },
    "en": {
        "title": "Cantata Tour 2025",
        "caption": "Maharashtra Tour Management System",
        "tab_notice": "Notice",
        "tab_map": "Tour Route",
        "map_title": "View Route",
        "add_city": "Add City",  # ← 영어
        "password": "Password",
        "login": "Login",
        "logout": "Logout",
        "wrong_pw": "Wrong password.",
        "select_city": "Select City",
        "venue": "Venue",
        "seats": "Expected Attendance",
        "note": "Notes",
        "google_link": "Google Maps Link",
        "indoor": "Indoor",
        "outdoor": "Outdoor",
        "register": "Register",
        "edit": "Edit",
        "remove": "Remove",
        "date": "Registered On",
        "performance_date": "Performance Date",
        "cancel": "Cancel",
        "title_label": "Title",
        "content_label": "Content",
        "upload_image": "Upload Image",
        "upload_file": "Upload File",
        "submit": "Submit",
        "warning": "Please enter both title and content.",
        "file_download": "Download File",
    },
    "hi": {
        "title": "कांताता टूर 2025",
        "caption": "महाराष्ट्र टूर प्रबंधन प्रणाली",
        "tab_notice": "सूचना",
        "tab_map": "टूर मार्ग",
        "map_title": "मार्ग देखें",
        "add_city": "शहर जोड़ें",  # ← 힌디어
        "password": "पासवर्ड",
        "login": "लॉगिन",
        "logout": "लॉगआउट",
        "wrong_pw": "गलत पासवर्ड।",
        "select_city": "शहर चुनें",
        "venue": "स्थल",
        "seats": "अपेक्षित उपस्थिति",
        "note": "नोट्स",
        "google_link": "गूगल मैप्स लिंक",
        "indoor": "इनडोर",
        "outdoor": "आउटडोर",
        "register": "रजिस्टर",
        "edit": "संपादित करें",
        "remove": "हटाएं",
        "date": "पंजीकरण तिथि",
        "performance_date": "प्रदर्शन तिथि",
        "cancel": "रद्द करें",
        "title_label": "शीर्षक",
        "content_label": "सामग्री",
        "upload_image": "छवि अपलोड करें",
        "upload_file": "फ़ाइल अपलोड करें",
        "submit": "जमा करें",
        "warning": "शीर्षक और सामग्री दोनों दर्ज करें।",
        "file_download": "फ़ाइल डाउनलोड करें",
    }
}

# 번역 함수
_ = lambda key: LANG[st.session_state.lang].get(key, key)

# 유틸 (생략 - 동일)
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_latlon_from_shortlink(short_url):
    try:
        r = requests.get(short_url, allow_redirects=True, timeout=5)
        final_url = r.url
        match = re.search(r'@([0-9\.\-]+),([0-9\.\-]+)', final_url)
        if match:
            return float(match.group(1)), float(match.group(2))
    except:
        pass
    return None, None

# 공지 기능 (생략 - 동일)
def add_notice(title, content, image_file=None, upload_file=None):
    # ... (동일)
    pass

def render_notice_list(show_delete=False):
    # ... (동일)
    pass

# 지도 + 도시 관리
def render_map():
    col_title, col_btn = st.columns([6, 1])
    with col_title:
        st.subheader(_("map_title"))
    with col_btn:
        if st.session_state.admin:
            if st.button(_("add_city"), key="btn_add_city"):  # ← "도시 추가" 표시
                st.session_state.adding_cities.append(None)
                st.rerun()

    cities_data = load_json(CITY_FILE)
    cities_data = sorted(cities_data, key=lambda x: x.get("perf_date", "9999-12-31"))

    if not os.path.exists(CITY_LIST_FILE):
        default_cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"]
        save_json(CITY_LIST_FILE, default_cities)
    cities_list = load_json(CITY_LIST_FILE)
    existing = {c["city"] for c in cities_data}
    available = [c for c in cities_list if c not in existing]

    # --- 동적 추가 폼 ---
    for i in range(len(st.session_state.adding_cities)):
        with st.container():
            col_sel, col_del = st.columns([8, 1])
            with col_sel:
                options = [None] + available
                current = st.session_state.adding_cities[i]
                idx = options.index(current) if current in options else 0
                city_name = st.selectbox(
                    _("select_city"),
                    options,
                    index=idx,
                    key=f"add_select_{i}"
                )
                st.session_state.adding_cities[i] = city_name
            with col_del:
                if st.button("×", key=f"remove_add_{i}"):
                    st.session_state.adding_cities.pop(i)
                    st.rerun()

            if city_name:
                venue = st.text_input(_("venue"), key=f"add_venue_{i}")
                seats = st.number_input(_("seats"), min_value=0, step=50, key=f"add_seats_{i}")
                perf_date = st.date_input(_("performance_date"), key=f"add_perf_date_{i}")
                venue_type = st.radio("공연형태", [_("indoor"), _("outdoor")], horizontal=True, key=f"add_type_{i}")
                map_link = st.text_input(_("google_link"), key=f"add_link_{i}")
                note = st.text_area(_("note"), key=f"add_note_{i}")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button(_("register"), key=f"reg_{i}"):
                        # ... (동일)
                        pass
                with c2:
                    if st.button(_("cancel"), key=f"cancel_{i}"):
                        st.session_state.adding_cities.pop(i)
                        st.rerun()

            st.markdown("---")

    # --- 기존 도시 목록 + 수정 모드 + 지도 ---
    # ... (이전 코드와 동일, 생략)

# 사이드바 + 메인 (동일)
# ... (생략)

with tab2:
    render_map()
