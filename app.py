import json
import os
import uuid
import base64
import random
import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone

# 가짜 라이브러리 임포트 (st_autorefresh는 Streamlit 환경에서만 유효)
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = lambda **kwargs: None
    # st.warning("`streamlit_autorefresh` 라이브러리가 설치되지 않았습니다. 자동 새로고침이 작동하지 않을 수 있습니다.")

st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

# --- 자동 새로고침 ---
# 관리자가 아닐 경우 10초마다 새로고침 (요청 반영: 5초 -> 10초)
if not st.session_state.get("admin", False):
    st_autorefresh(interval=10000, key="auto_refresh_user")

# --- 파일 경로 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 다국어 설정 ---
LANG = {
    "ko": {
        "title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
        "tab_notice": "공지", "tab_map": "투어 경로", "indoor": "실내", "outdoor": "실외",
        "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵",
        "warning": "도시와 장소를 입력하세요", "delete": "제거", "menu": "메뉴", "login": "로그인", "logout": "로그아웃",
        "add_city": "추가", "register": "등록", "update": "수정", "remove": "제거",
        "date": "날짜", "city_name": "도시 이름", "search_placeholder": "도시/장소 검색...",
        
        # 추가 번역 (모든 UI 요소 포함)
        "general": "일반", "urgent": "긴급",
        "admin_login": "관리자 로그인",
        "update_content": "내용 수정",
        "existing_notices": "기존 공지사항",
        "no_notices": "공지사항이 없습니다.",
        "content": "내용",
        "no_content": "내용 없음",
        "no_title": "제목 없음",
        "tour_schedule_management": "투어 일정 관리",
        "set_data": "데이터 설정",
        "type": "유형",
        "city": "도시",
        "link": "링크",
        "past_route": "지난 경로",
        "single_location": "단일 위치",
        "legend": "범례",
        "no_schedule": "일정이 없습니다.",
        "city_coords_error": "좌표를 찾을 수 없습니다. city_dict에 추가해 주세요.",
        "logged_in_success": "관리자로 로그인했습니다.",
        "logged_out_success": "로그아웃했습니다.",
        "incorrect_password": "비밀번호가 틀렸습니다.",
        "fill_in_fields": "제목과 내용을 채워주세요.",
        "notice_reg_success": "공지사항이 성공적으로 등록되었습니다!",
        "notice_del_success": "공지사항이 삭제되었습니다.",
        "notice_upd_success": "공지사항이 수정되었습니다.",
        "schedule_reg_success": "일정이 등록되었습니다.",
        "schedule_del_success": "일정 항목이 제거되었습니다.",
        "schedule_upd_success": "일정이 성공적으로 수정되었습니다.",
        "venue_placeholder": "공연 장소를 입력하세요",
        "note_placeholder": "특이사항을 입력하세요",
        "google_link_placeholder": "구글맵 URL을 입력하세요",
        "seats_tooltip": "예상 관객 인원"
    },
    "en": {
        "title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
        "tab_notice": "Notice", "tab_map": "Tour Route", "indoor": "Indoor", "outdoor": "Outdoor",
        "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps",
        "warning": "Enter city and venue", "delete": "Remove", "menu": "Menu", "login": "Login", "logout": "Logout",
        "add_city": "Add", "register": "Register", "update": "Update", "remove": "Remove",
        "date": "Date", "city_name": "City Name", "search_placeholder": "Search City/Venue...",
        
        # Additional translations
        "general": "General", "urgent": "Urgent",
        "admin_login": "Admin Login",
        "update_content": "Update Content",
        "existing_notices": "Existing Notices",
        "no_notices": "No notices available.",
        "content": "Content",
        "no_content": "No Content",
        "no_title": "No Title",
        "tour_schedule_management": "Tour Schedule Management",
        "set_data": "Set Data",
        "type": "Type",
        "city": "City",
        "link": "Link",
        "past_route": "Past Route",
        "single_location": "Single Location",
        "legend": "Legend",
        "no_schedule": "No schedule available.",
        "city_coords_error": "Coordinates not found. Please add to city_dict.",
        "logged_in_success": "Logged in as Admin.",
        "logged_out_success": "Logged out.",
        "incorrect_password": "Incorrect password.",
        "fill_in_fields": "Please fill in the title and content.",
        "notice_reg_success": "Notice registered successfully!",
        "notice_del_success": "Notice deleted.",
        "notice_upd_success": "Notice updated.",
        "schedule_reg_success": "Schedule registered.",
        "schedule_del_success": "Schedule entry removed.",
        "schedule_upd_success": "Schedule updated successfully.",
        "venue_placeholder": "Enter venue name",
        "note_placeholder": "Enter notes/special remarks",
        "google_link_placeholder": "Enter Google Maps URL",
        "seats_tooltip": "Expected audience count"
    },
    "hi": {
        "title_cantata": "कैंटाटा टूर", "title_year": "२०२५", "title_region": "महाराष्ट्र",
        "tab_notice": "सूचना", "tab_map": "टूर रूट", "indoor": "इनडोर", "outdoor": "आउटडोर",
        "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप्स",
        "warning": "शहर और स्थल दर्ज करें", "delete": "हटाएं", "menu": "मेनू", "login": "लॉगिन", "logout": "लॉगआउट",
        "add_city": "जोड़ें", "register": "रजिस्टर", "update": "अपडेट", "remove": "हटाएं",
        "date": "तारीख", "city_name": "शहर का नाम", "search_placeholder": "शहर/स्थल खोजें...",
        
        # Additional translations
        "general": "सामान्य", "urgent": "तत्काल",
        "admin_login": "व्यवस्थापक लॉगिन",
        "update_content": "सामग्री अपडेट करें",
        "existing_notices": "मौजूदा सूचनाएं",
        "no_notices": "कोई सूचना उपलब्ध नहीं है।",
        "content": "सामग्री",
        "no_content": "कोई सामग्री नहीं",
        "no_title": "कोई शीर्षक नहीं",
        "tour_schedule_management": "टूर अनुसूची प्रबंधन",
        "set_data": "डेटा सेट करें",
        "type": "प्रकार",
        "city": "शहर",
        "link": "लिंक",
        "past_route": "पिछला मार्ग",
        "single_location": "एकल स्थान",
        "legend": "किंवदंती",
        "no_schedule": "कोई कार्यक्रम उपलब्ध नहीं है।",
        "city_coords_error": "निर्देशांक नहीं मिला। कृपया city_dict में जोड़ें।",
        "logged_in_success": "व्यवस्थापक के रूप में लॉग इन किया गया।",
        "logged_out_success": "लॉग आउट किया गया।",
        "incorrect_password": "गलत पासवर्ड।",
        "fill_in_fields": "कृपया शीर्षक और सामग्री भरें।",
        "notice_reg_success": "सूचना सफलतापूर्वक पंजीकृत हुई!",
        "notice_del_success": "सूचना हटा दी गई।",
        "notice_upd_success": "सूचना अपडेट की गई।",
        "schedule_reg_success": "कार्यक्रम पंजीकृत हुआ।",
        "schedule_del_success": "कार्यक्रम प्रविष्टि हटा दी गई।",
        "schedule_upd_success": "कार्यक्रम सफलतापूर्वक अपडेट किया गया।",
        "venue_placeholder": "स्थल का नाम दर्ज करें",
        "note_placeholder": "नोट्स/विशेष टिप्पणी दर्ज करें",
        "google_link_placeholder": "गूगल मैप्स URL दर्ज करें",
        "seats_tooltip": "अपेक्षित दर्शक संख्या"
    }
}

# --- 세션 초기화 ---
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False, "logged_in_user": None, "show_login_form": False, "play_sound": False}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
    elif k == "lang" and not isinstance(st.session_state[k], str):
        st.session_state[k] = "ko"

# --- 번역 함수 ---
def _(key):
    lang = st.session_state.lang if isinstance(st.session_state.lang, str) else "ko"
    return LANG.get(lang, LANG["ko"]).get(key, key)

# --- 알림음 함수 ---
def play_alert_sound():
    st.session_state.play_sound = True

# --- JSON 헬퍼 ---
def load_json(f):
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            # st.error(f"Error reading {f}: Invalid JSON format. Initializing empty list.")
            return []
    return []

def save_json(f, d):
    try:
        with open(f, "w", encoding="utf-8") as file:
            json.dump(d, file, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error saving {f}: {e}")

# --- 도시 목록 및 좌표 정의 (원래 코드에서 가져옴) ---
city_dict = {
    "Ahmadnagar": {"lat": 19.095193, "lon": 74.749596}, "Akola": {"lat": 20.702269, "lon": 77.004699},
    "Ambernath": {"lat": 19.186354, "lon": 73.191948}, "Amravati": {"lat": 20.93743, "lon": 77.779271},
    "Aurangabad": {"lat": 19.876165, "lon": 75.343314}, "Badlapur": {"lat": 19.1088, "lon": 73.1311},
    "Bhandara": {"lat": 21.180052, "lon": 79.564987}, "Bhiwandi": {"lat": 19.300282, "lon": 73.069645},
    "Bhusawal": {"lat": 21.02606, "lon": 75.830095}, "Chandrapur": {"lat": 19.957275, "lon": 79.296875},
    "Chiplun": {"lat": 17.5322, "lon": 73.516}, "Dhule": {"lat": 20.904964, "lon": 74.774651},
    "Dombivli": {"lat": 19.2183, "lon": 73.0865}, "Gondia": {"lat": 21.4598, "lon": 80.195},
    "Hingoli": {"lat": 19.7146, "lon": 77.1424}, "Ichalkaranji": {"lat": 16.6956, "lon": 74.4561},
    "Jalgaon": {"lat": 21.007542, "lon": 75.562554}, "Jalna": {"lat": 19.833333, "lon": 75.883333},
    "Kalyan": {"lat": 19.240283, "lon": 73.13073}, "Karad": {"lat": 17.284, "lon": 74.1779},
    "Karanja": {"lat": 20.7083, "lon": 76.93}, "Karanja Lad": {"lat": 20.3969, "lon": 76.8908},
    "Karjat": {"lat": 18.9121, "lon": 73.3259}, "Kavathe Mahankal": {"lat": 17.218, "lon": 74.416},
    "Khamgaon": {"lat": 20.691, "lon": 76.6886}, "Khopoli": {"lat": 18.6958, "lon": 73.3207},
    "Kolad": {"lat": 18.5132, "lon": 73.2166}, "Kolhapur": {"lat": 16.691031, "lon": 74.229523},
    "Kopargaon": {"lat": 19.883333, "lon": 74.483333}, "Koparkhairane": {"lat": 19.0873, "lon": 72.9856},
    "Kothrud": {"lat": 18.507399, "lon": 73.807648}, "Kudal": {"lat": 16.033333, "lon": 73.683333},
    "Kurla": {"lat": 19.0667, "lon": 72.8833}, "Latur": {"lat": 18.406526, "lon": 76.560229},
    "Lonavala": {"lat": 18.75, "lon": 73.4}, "Mahad": {"lat": 18.086, "lon": 73.3006},
    "Malegaon": {"lat": 20.555256, "lon": 74.525539}, "Malkapur": {"lat": 20.4536, "lon": 76.3886},
    "Manmad": {"lat": 20.3333, "lon": 74.4333}, "Mira-Bhayandar": {"lat": 19.271112, "lon": 72.854094},
    "Mumbai": {"lat": 19.07609, "lon": 72.877426}, "Nagpur": {"lat": 21.1458, "lon": 79.088154},
    "Nanded": {"lat": 19.148733, "lon": 77.321011}, "Nandurbar": {"lat": 21.317, "lon": 74.02},
    "Nashik": {"lat": 20.011645, "lon": 73.790332}, "Niphad": {"lat": 20.074, "lon": 73.834},
    "Osmanabad": {"lat": 18.169111, "lon": 76.035309}, "Palghar": {"lat": 19.691644, "lon": 72.768478},
    "Panaji": {"lat": 15.4909, "lon": 73.8278}, "Panvel": {"lat": 18.989746, "lon": 73.117069},
    "Parbhani": {"lat": 19.270335, "lon": 76.773347}, "Peth": {"lat": 18.125, "lon": 74.514},
    "Phaltan": {"lat": 17.9977, "lon": 74.4066}, "Pune": {"lat": 18.52043, "lon": 73.856743},
    "Raigad": {"lat": 18.515048, "lon": 73.179436}, "Ramtek": {"lat": 21.3142, "lon": 79.2676},
    "Ratnagiri": {"lat": 16.990174, "lon": 73.311902}, "Sangli": {"lat": 16.855005, "lon": 74.56427},
    "Sangole": {"lat": 17.126, "lon": 75.0331}, "Saswad": {"lat": 18.3461, "lon": 74.0335},
    "Satara": {"lat": 17.688481, "lon": 73.993631}, "Sawantwadi": {"lat": 15.8964, "lon": 73.7626},
    "Shahada": {"lat": 21.1167, "lon": 74.5667}, "Shirdi": {"lat": 19.7667, "lon": 74.4771},
    "Shirpur": {"lat": 21.1286, "lon": 74.4172}, "Shirur": {"lat": 18.7939, "lon": 74.0305},
    "Shrirampur": {"lat": 19.6214, "lon": 73.8653}, "Sinnar": {"lat": 19.8531, "lon": 73.9976},
    "Solan": {"lat": 30.9083, "lon": 77.0989}, "Solapur": {"lat": 17.659921, "lon": 75.906393},
    "Talegaon": {"lat": 18.7519, "lon": 73.487}, "Thane": {"lat": 19.218331, "lon": 72.978088},
    "Achalpur": {"lat": 20.1833, "lon": 77.6833}, "Akot": {"lat": 21.1, "lon": 77.1167},
    "Ambajogai": {"lat": 18.9667, "lon": 76.6833}, "Amalner": {"lat": 21.0333, "lon": 75.3333},
    "Anjangaon Surji": {"lat": 21.1167, "lon": 77.8667}, "Arvi": {"lat": 20.45, "lon": 78.15},
    "Ashti": {"lat": 18.0, "lon": 76.25}, "Atpadi": {"lat": 17.1667, "lon": 74.4167},
    "Baramati": {"lat": 18.15, "lon": 74.6}, "Barshi": {"lat": 18.11, "lon": 76.06},
    "Basmat": {"lat": 18.7, "lon": 77.856}, "Bhokar": {"lat": 19.5167, "lon": 77.3833},
    "Biloli": {"lat": 19.5333, "lon": 77.2167}, "Chikhli": {"lat": 20.9, "lon": 76.0167},
    "Daund": {"lat": 18.4667, "lon": 74.65}, "Deola": {"lat": 20.5667, "lon": 74.05},
    "Dhanora": {"lat": 20.7167, "lon": 79.0167}, "Dharni": {"lat": 21.25, "lon": 78.2667},
    "Dharur": {"lat": 18.0833, "lon": 76.7}, "Digras": {"lat": 19.45, "lon": 77.55},
    "Dindori": {"lat": 21.0, "lon": 79.0}, "Erandol": {"lat": 21.0167, "lon": 75.2167},
    "Faizpur": {"lat": 21.1167, "lon": 75.7167}, "Gadhinglaj": {"lat": 16.2333, "lon": 74.1333},
    "Guhagar": {"lat": 16.4, "lon": 73.4}, "Hinganghat": {"lat": 20.0167, "lon": 78.7667},
    "Igatpuri": {"lat": 19.6961, "lon": 73.5212}, "Junnar": {"lat": 19.2667, "lon": 73.8833},
    "Kankavli": {"lat": 16.3833, "lon": 73.5167}, "Koregaon": {"lat": 17.2333, "lon": 74.1167},
    "Kupwad": {"lat": 16.7667, "lon": 74.4667}, "Lonar": {"lat": 19.9833, "lon": 76.5167},
    "Mangaon": {"lat": 18.1869, "lon": 73.2555}, "Mangalwedha": {"lat": 16.6667, "lon": 75.1333},
    "Morshi": {"lat": 20.0556, "lon": 77.7647}, "Pandharpur": {"lat": 17.6658, "lon": 75.3203},
    "Parli": {"lat": 18.8778, "lon": 76.65}, "Rahuri": {"lat": 19.2833, "lon": 74.5833},
    "Raver": {"lat": 20.5876, "lon": 75.9002}, "Sangamner": {"lat": 19.3167, "lon": 74.5333},
    "Savner": {"lat": 21.0833, "lon": 79.1333}, "Sillod": {"lat": 20.0667, "lon": 75.1833},
    "Tumsar": {"lat": 20.4623, "lon": 79.5429}, "Udgir": {"lat": 18.4167, "lon": 77.1239},
    "Ulhasnagar": {"lat": 19.218451, "lon": 73.16024}, "Vasai-Virar": {"lat": 19.391003, "lon": 72.839729},
    "Wadgaon Road": {"lat": 18.52, "lon": 73.85}, "Wadwani": {"lat": 18.9, "lon": 76.69},
    "Wai": {"lat": 17.9524, "lon": 73.8775}, "Wani": {"lat": 19.0, "lon": 78.002},
    "Wardha": {"lat": 20.745445, "lon": 78.602452}, "Wardha Road": {"lat": 20.75, "lon": 78.6},
    "Yavatmal": {"lat": 20.389917, "lon": 78.130051}
}

major_cities_available = [c for c in ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik", "Kalyan", "Vasai-Virar", "Aurangabad", "Solapur", "Mira-Bhayandar", "Bhiwandi", "Amravati", "Nanded", "Kolhapur", "Ulhasnagar", "Sangli", "Malegaon", "Jalgaon", "Akola", "Latur", "Dhule", "Ahmadnagar", "Chandrapur", "Parbhani", "Ichalkaranji", "Jalna", "Ambernath", "Bhusawal", "Panvel", "Dombivli"] if c in city_dict]
remaining_cities = sorted([c for c in city_dict if c not in major_cities_available])
city_options = ["공연없음"] + major_cities_available + remaining_cities


# --- 데이터 로드 (공지사항 및 투어 일정) ---
tour_notices = load_json(NOTICE_FILE)
tour_schedule = load_json(CITY_FILE) 

# 만약 city_dict에 있는 도시 정보가 없다면 초기화
if not tour_schedule:
    # 초기 도시 데이터를 지도 경로를 위해 포맷팅하여 저장
    initial_schedule = []
    for city, coords in city_dict.items():
        initial_schedule.append({
            "id": str(uuid.uuid4()),
            "city": city,
            "venue": "TBD",
            "lat": coords["lat"],
            "lon": coords["lon"],
            "date": "",
            "type": "outdoor",
            "seats": "0",
            "note": "Initial Data",
            "google_link": "",
            "reg_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    save_json(CITY_FILE, initial_schedule)
    tour_schedule = initial_schedule


# --- 관리자 및 UI 설정 ---
ADMIN_PASS = "0009" # 비밀번호: '0009'

# 요청 반영: 제목 스타일 (아이콘 제거, 기본 스타일 유지)
title_html = f"""
    <div class="header-container">
        <h1 class="main-title">
            <span style="color: #FF4B4B;">{_('title_cantata')}</span> 
            <span style="color: white;">{_('title_year')}</span>
            <span style="color: #008000; font-size: 0.66em;">{_('title_region')}</span>
        </h1>
    </div>
"""
st.markdown(title_html, unsafe_allow_html=True)

# 언어 선택 버튼 (상단 고정)
col_lang, col_auth = st.columns([1, 3])
with col_lang:
    # 요청 반영: 언어 선택 옵션을 해당 언어명으로 표시
    LANG_OPTIONS = {"ko": "한국어", "en": "English", "hi": "हिन्दी"}
    lang_keys = list(LANG_OPTIONS.keys())
    lang_display_names = list(LANG_OPTIONS.values())
    
    current_lang_index = lang_keys.index(st.session_state.lang)

    selected_lang_display = st.selectbox(
        _("menu"), 
        options=lang_display_names, 
        index=current_lang_index,
        key="lang_select"
    )
    
    # 표시된 이름으로 다시 키를 찾음
    selected_lang_key = lang_keys[lang_display_names.index(selected_lang_display)]
    
    if selected_lang_key != st.session_state.lang:
        st.session_state.lang = selected_lang_key
        st.rerun()

# --- 로그인 / 로그아웃 로직 ---
with col_auth:
    if st.session_state.admin:
        if st.button(_("logout"), key="logout_btn"):
            st.session_state.admin = False
            st.session_state.logged_in_user = None
            st.session_state.show_login_form = False # 로그아웃 시 폼 숨김
            st.success(_("logged_out_success"))
            play_alert_sound()
            st.rerun()
    else:
        # 로그인 버튼 클릭 시 폼 표시 상태 변경
        if st.button(_("login"), key="login_btn"):
            st.session_state.show_login_form = not st.session_state.show_login_form
        
        # 폼 표시 상태가 True일 때만 폼을 렌더링
        if st.session_state.show_login_form:
            with st.form("login_form_permanent", clear_on_submit=False):
                st.write(_("admin_login"))
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(_("login"))
                
                if submitted:
                    if password == ADMIN_PASS:
                        st.session_state.admin = True
                        st.session_state.logged_in_user = "Admin"
                        st.session_state.show_login_form = False # 성공하면 폼 숨김
                        st.success(_("logged_in_success"))
                        play_alert_sound()
                        st.rerun()
                    else:
                        st.error(_("incorrect_password"))
                        # 실패해도 폼을 유지하기 위해 show_login_form=True 유지


# --- 탭 구성 ---
tab1, tab2 = st.tabs([_("tab_notice"), _("tab_map")])

# =============================================================================
# 탭 1: 공지사항 (Notice)
# =============================================================================
with tab1:
    st.subheader(f"🔔 {_('tab_notice')}")

    if st.session_state.admin:
        # --- 관리자: 공지사항 등록/수정 폼 ---
        with st.expander(_("register"), expanded=True):
            with st.form("notice_form", clear_on_submit=True):
                notice_title = st.text_input(_("title_cantata"))
                notice_content = st.text_area(_("note"))
                
                # 내부적으로는 항상 English key를 사용하고, 사용자에게는 번역된 값을 보여줍니다.
                type_options = {"General": _("general"), "Urgent": _("urgent")}
                selected_display_type = st.radio(_("type"), list(type_options.values()))
                
                # Display value를 이용해 내부 key를 찾습니다.
                notice_type = list(type_options.keys())[list(type_options.values()).index(selected_display_type)]
                
                submitted = st.form_submit_button(_("register"))
                if submitted and notice_title and notice_content:
                    new_notice = {
                        "id": str(uuid.uuid4()),
                        "title": notice_title,
                        "content": notice_content,
                        "type": notice_type, # English key로 저장
                        "date": datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S") # IST 기준 시간
                    }
                    tour_notices.insert(0, new_notice) # 최신순으로 맨 앞에 추가
                    save_json(NOTICE_FILE, tour_notices)
                    st.success(_("notice_reg_success"))
                    play_alert_sound()
                    st.rerun()
                elif submitted:
                    st.warning(_("fill_in_fields"))
        
        # --- 관리자: 공지사항 목록 및 수정/삭제 ---
        st.subheader(_("existing_notices"))
        
        # 안정성 강화: 유효한 형식의 공지사항만 필터링하고 날짜순으로 정렬
        valid_notices = [n for n in tour_notices if isinstance(n, dict) and n.get('id') and n.get('title')]
        notices_to_display = sorted(valid_notices, key=lambda x: x.get('date', '9999-12-31'), reverse=True)
        
        # 번역을 위해 type_options을 다시 정의
        type_options_rev = {"General": _("general"), "Urgent": _("urgent")}
        
        for notice in notices_to_display:
            notice_id = notice['id'] # 이제 'id'는 반드시 존재
            # 저장된 English key를 이용해 번역된 텍스트를 가져옵니다.
            notice_type_key = notice.get('type', 'General')
            translated_type = type_options_rev.get(notice_type_key, _("general"))
            notice_title = notice['title'] # 이제 'title'은 반드시 존재
            
            with st.expander(f"[{translated_type}] {notice_title} ({notice.get('date', 'N/A')[:10]})", expanded=False):
                col_del, col_title = st.columns([1, 4])
                with col_del:
                    if st.button(_("remove"), key=f"del_n_{notice_id}", help=_("remove")):
                        tour_notices[:] = [n for n in tour_notices if n.get('id') != notice_id]
                        save_json(NOTICE_FILE, tour_notices)
                        st.success(_("notice_del_success"))
                        play_alert_sound()
                        st.rerun()
                
                with col_title:
                    st.markdown(f"**{_('content')}:** {notice.get('content', _('no_content'))}")
                
                # 간단한 업데이트 로직 추가
                with st.form(f"update_notice_{notice_id}", clear_on_submit=True):
                    # 현재 타입을 찾아서 초기값으로 설정
                    current_type_index = list(type_options_rev.keys()).index(notice_type_key)
                    updated_display_type = st.radio(_("type"), list(type_options_rev.values()), index=current_type_index, key=f"update_type_{notice_id}")
                    updated_type_key = list(type_options_rev.keys())[list(type_options_rev.values()).index(updated_display_type)]
                    
                    updated_content = st.text_area(_("update_content"), value=notice.get('content', ''))
                    
                    if st.form_submit_button(_("update")):
                        for n in tour_notices:
                            if n.get('id') == notice_id:
                                n['content'] = updated_content
                                n['type'] = updated_type_key # English key로 저장
                                save_json(NOTICE_FILE, tour_notices)
                                st.success(_("notice_upd_success"))
                                play_alert_sound()
                                st.rerun()
        
    else:
        # --- 사용자: 공지사항 보기 (안정성 강화) ---
        valid_notices = [n for n in tour_notices if isinstance(n, dict) and n.get('title')]
        if not valid_notices:
            st.info(_("no_notices"))
        else:
            notices_to_display = sorted(valid_notices, key=lambda x: x.get('date', '9999-12-31'), reverse=True)
            type_options_rev = {"General": _("general"), "Urgent": _("urgent")}
            
            for notice in notices_to_display:
                notice_type_key = notice.get('type', 'General')
                translated_type = type_options_rev.get(notice_type_key, _("general"))
                
                notice_title = notice.get('title', _("no_title"))
                notice_content = notice.get('content', _("no_content"))
                
                st.markdown(f"**[{translated_type}] {notice_title}** - *{notice.get('date', 'N/A')[:16]}*")
                st.info(notice_content)
                st.markdown("---")


# =============================================================================
# 탭 2: 투어 경로 (Map)
# =============================================================================
with tab2:
    st.subheader(f"🗺️ {_('tab_map')}")
    
    # --- 관리자: 투어 일정 관리 ---
    if st.session_state.admin:
        st.markdown(f"**{_('register')} {_('tab_map')} {_('set_data')}**")
        
        with st.expander(_("add_city"), expanded=True):
            with st.form("schedule_form", clear_on_submit=True):
                col_c, col_d, col_v = st.columns(3)
                
                city_name_input = col_c.selectbox(_('city_name'), options=city_options, index=city_options.index("공연없음") if "공연없음" in city_options else 0)
                schedule_date = col_d.date_input(_("date"))
                venue_name = col_v.text_input(_("venue"), placeholder=_("venue_placeholder"))
                
                col_l, col_s, col_n = st.columns(3)
                type_options_map = {_("indoor"): "indoor", _("outdoor"): "outdoor"} # Display -> Internal Key
                selected_display_type = col_l.radio(_("type"), list(type_options_map.keys()))
                type_sel = type_options_map[selected_display_type] # Internal key
                
                # 요청 반영: 예상인원 기본값을 100에서 500으로 변경
                expected_seats = col_s.number_input(_("seats"), min_value=0, value=500, help=_("seats_tooltip"))
                google_link = col_n.text_input(_("google_link"), placeholder=_("google_link_placeholder"))
                
                note = st.text_area(_("note"), placeholder=_("note_placeholder"))
                
                submitted = st.form_submit_button(_("register"))
                
                if submitted:
                    if city_name_input == "공연없음" or not venue_name or not schedule_date:
                        st.error(_("warning"))
                    elif city_name_input not in city_dict:
                        st.error(f"Coordinates for '{city_name_input}' not found in city_dict. {_('city_coords_error')}")
                    else:
                        city_coords = city_dict[city_name_input]
                        new_schedule_entry = {
                            "id": str(uuid.uuid4()),
                            "city": city_name_input,
                            "venue": venue_name,
                            "lat": city_coords["lat"],
                            "lon": city_coords["lon"],
                            "date": schedule_date.strftime("%Y-%m-%d"),
                            "type": type_sel, # Internal key로 저장
                            "seats": str(expected_seats),
                            "note": note,
                            "google_link": google_link,
                            "reg_date": datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
                        }
                        tour_schedule.append(new_schedule_entry)
                        save_json(CITY_FILE, tour_schedule)
                        st.success(f"{_('schedule_reg_success')} ({city_name_input})")
                        play_alert_sound()
                        st.rerun()
                        
        
        # --- 관리자: 일정 보기 및 수정/삭제 (안정성 강화) ---
        
        # 안정성 강화: 유효한 형식의 일정만 필터링
        valid_schedule = [
            item 
            for item in tour_schedule 
            if isinstance(item, dict) and item.get('id') and item.get('city') and item.get('venue')
        ]
        
        if valid_schedule:
            st.subheader(_("tour_schedule_management"))
            
            # id를 기준으로 딕셔너리로 변환
            schedule_dict = {item['id']: item for item in valid_schedule}
            
            # 날짜를 기준으로 정렬
            sorted_schedule_items = sorted(schedule_dict.items(), key=lambda x: x[1].get('date', '9999-12-31'))
            
            type_options_map_rev = {"indoor": _("indoor"), "outdoor": _("outdoor")} # Internal Key -> Display

            for item_id, item in sorted_schedule_items:
                # 내부 키를 이용하여 번역된 타입 텍스트를 가져옴
                translated_type = type_options_map_rev.get(item.get('type', 'outdoor'), _("outdoor"))
                
                with st.expander(f"[{item.get('date', 'N/A')}] {item['city']} - {item['venue']} ({translated_type})", expanded=False):
                    col_u, col_d = st.columns([1, 5])
                    
                    with col_u:
                        # 수정 버튼 클릭 시 편집 모드로 전환
                        if st.button(_("update"), key=f"upd_s_{item_id}"):
                            st.session_state[f"edit_mode_{item_id}"] = True
                            st.rerun()
                        if st.button(_("remove"), key=f"del_s_{item_id}"):
                            # tour_schedule 리스트를 직접 수정
                            tour_schedule[:] = [s for s in tour_schedule if s.get('id') != item_id]
                            save_json(CITY_FILE, tour_schedule)
                            st.success(f"{item['city']} {_('schedule_del_success')}")
                            play_alert_sound()
                            st.rerun()

                    if st.session_state.get(f"edit_mode_{item_id}"):
                        with st.form(f"edit_form_{item_id}"):
                            col_uc, col_ud, col_uv = st.columns(3)
                            
                            updated_city = col_uc.selectbox(_("city"), city_options, index=city_options.index(item.get('city', "공연없음")))
                            
                            # 날짜 형식 처리 개선
                            try:
                                initial_date = datetime.strptime(item.get('date', '2025-01-01'), "%Y-%m-%d").date()
                            except ValueError:
                                initial_date = date.today()
                                
                            updated_date = col_ud.date_input(_("date"), value=initial_date)
                            updated_venue = col_uv.text_input(_("venue"), value=item.get('venue'))
                            
                            col_ul, col_us, col_ug = st.columns(3)
                            
                            # 현재 타입에 맞는 인덱스를 찾아서 초기값으로 설정
                            current_map_type = item.get('type', 'outdoor')
                            current_map_index = 0 if current_map_type == "indoor" else 1
                            
                            map_type_list = list(type_options_map_rev.values())
                            updated_display_type = col_ul.radio(_("type"), map_type_list, index=current_map_index, key=f"update_map_type_{item_id}")
                            # Display value를 이용해 내부 key를 찾습니다.
                            updated_type = "indoor" if updated_display_type == _("indoor") else "outdoor"
                            
                            seats_value = item.get('seats', '0')
                            updated_seats = col_us.number_input(_("seats"), min_value=0, value=int(seats_value) if str(seats_value).isdigit() else 0)
                            updated_google = col_ug.text_input(_("google_link"), value=item.get('google_link', ''))

                            updated_note = st.text_area(_("note"), value=item.get('note'))
                            
                            if st.form_submit_button(_("update")):
                                for idx, s in enumerate(tour_schedule):
                                    if s.get('id') == item_id:
                                        coords = city_dict.get(updated_city, {'lat': s.get('lat', 0), 'lon': s.get('lon', 0)})
                                        tour_schedule[idx] = {
                                            "id": item_id,
                                            "city": updated_city,
                                            "venue": updated_venue,
                                            "lat": coords["lat"],
                                            "lon": coords["lon"],
                                            "date": updated_date.strftime("%Y-%m-%d"),
                                            "type": updated_type, # Internal key로 저장
                                            "seats": str(updated_seats),
                                            "note": updated_note,
                                            "google_link": updated_google,
                                            "reg_date": s.get('reg_date', datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S"))
                                        }
                                        save_json(CITY_FILE, tour_schedule)
                                        st.session_state[f"edit_mode_{item_id}"] = False
                                        st.success(_("schedule_upd_success"))
                                        play_alert_sound()
                                        st.rerun()
                        
                    if not st.session_state.get(f"edit_mode_{item_id}"):
                        st.markdown(f"**{_('date')}:** {item.get('date', 'N/A')} ({item.get('reg_date', '')})")
                        st.markdown(f"**{_('venue')}:** {item.get('venue', 'N/A')}")
                        st.markdown(f"**{_('seats')}:** {item.get('seats', 'N/A')}")
                        st.markdown(f"**{_('type')}:** {translated_type}")
                        if item.get('google_link'):
                            google_link_url = item['google_link']
                            st.markdown(f"**{_('google_link')}:** [{_('google_link')}]({google_link_url})")
                        st.markdown(f"**{_('note')}:** {item.get('note', 'N/A')}")
        else:
            st.info(_("no_schedule"))

    # --- 지도 표시 (사용자 & 관리자 공통) ---
    
    # 1. 경로 데이터 준비 (날짜순 정렬 및 안정성 강화)
    current_date = date.today() # 현재 날짜
    schedule_for_map = sorted([
        s for s in tour_schedule 
        if s.get('date') and s.get('lat') is not None and s.get('lon') is not None and s.get('id')
    ], key=lambda x: x['date'])
    
    # 2. 지도 중심 설정 (일단 Pune로 설정)
    start_coords = [18.52043, 73.856743] # Pune
    if schedule_for_map:
        # 첫 번째 공연 도시로 중심 이동
        start_coords = [schedule_for_map[0]['lat'], schedule_for_map[0]['lon']]

    m = folium.Map(location=start_coords, zoom_start=8)

    # 3. 마커 및 경로 그리기
    locations = []
    
    for item in schedule_for_map:
        lat = item['lat']
        lon = item['lon']
        date_str = item['date']
        
        try:
            event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            # 날짜 형식 오류 시, 미래로 간주하여 표시
            event_date = current_date + timedelta(days=365)
        
        is_past = event_date < current_date
        
        # 마커 색상 설정 (내부 키 사용)
        color = 'blue' if item.get('type') == 'indoor' else 'red'
        
        # 지난 도시 30% 투명도, 미래 도시 100% 투명도
        opacity_val = 0.3 if is_past else 1.0
        
        # 팝업 내용 (번역 적용)
        popup_html = f"""
        <b>{_('city')}:</b> {item.get('city', 'N/A')}<br>
        <b>{_('date')}:</b> {date_str}<br>
        <b>{_('venue')}:</b> {item.get('venue', 'N/A')}<br>
        <b>{_('seats')}:</b> {item.get('seats', 'N/A')}<br>
        """
        
        if item.get('google_link'):
            google_link_url = item['google_link'] 
            popup_html += f'<a href="{google_link_url}" target="_blank">{_("google_link")}</a>'
        
        # DivIcon을 사용하여 2/3 크기 (scale 0.666) 및 투명도 적용
        city_initial = item.get('city', 'A')[0]
        marker_icon_html = f"""
            <div style="
                transform: scale(0.666); 
                opacity: {opacity_val};
                text-align: center;
                white-space: nowrap;
            ">
                <i class="fa fa-map-marker fa-3x" style="color: {color};"></i>
                <div style="font-size: 10px; color: black; font-weight: bold; position: absolute; top: 12px; left: 13px;">{city_initial}</div>
            </div>
        """
            
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{item.get('city', 'N/A')} - {date_str}",
            icon=folium.DivIcon(
                icon_size=(30, 45),
                icon_anchor=(15, 45),
                html=marker_icon_html
            )
        ).add_to(m)
        
        locations.append([lat, lon])

    # 4. AntPath (경로 애니메이션) - 과거/미래 분리 및 스타일 적용
    
    if len(locations) > 1:
        # 현재/미래 공연이 시작되는 인덱스를 찾습니다.
        current_index = -1
        for i, item in enumerate(schedule_for_map):
            try:
                event_date = datetime.strptime(item['date'], "%Y-%m-%d").date()
                if event_date >= current_date:
                    current_index = i
                    break
            except ValueError:
                # 날짜 형식 오류 시, 이 항목은 건너뜀
                continue
        
        if current_index == -1: # 모든 일정이 과거 또는 날짜 오류
            past_segments = locations
            future_segments = []
        elif current_index == 0: # 모든 일정이 미래/현재 시작
            past_segments = []
            future_segments = locations
        else: 
            # 과거 세그먼트: 시작 ~ 현재/다음 도시 (PolyLine 사용)
            past_segments = locations[:current_index + 1]
            # 미래 세그먼트: 현재/다음 도시 ~ 끝 (AntPath 사용)
            future_segments = locations[current_index:]

        # 지난 도시/라인 30% 투명도의 빨간색 선
        if len(past_segments) > 1:
            folium.PolyLine(
                locations=past_segments,
                color="#FF4B4B", # Streamlit Red
                weight=5,
                opacity=0.3,
                tooltip=_("past_route")
            ).add_to(m)
            
        # 도시간 연결선 80% 투명도의 빨간색 AntPath
        if len(future_segments) > 1:
            AntPath(
                future_segments, 
                use="regular", 
                dash_array='5, 5', 
                color='#FF4B4B', # Streamlit Red
                weight=5, 
                opacity=0.8,
                options={"delay": 1000, "dash_factor": 0.1, "color": "#FF4B4B"}
            ).add_to(m)
            
    elif locations:
        # 도시가 하나만 있는 경우, 해당 위치에 원을 그려 표시
        try:
            single_item_date = datetime.strptime(schedule_for_map[0]['date'], "%Y-%m-%d").date()
            single_is_past = single_item_date < current_date
        except ValueError:
            single_is_past = False # 날짜 오류 시 미래로 간주
            
        folium.Circle(
            location=locations[0],
            radius=1000, # 1km
            color='#FF4B4B',
            fill=True,
            fill_color='#FF4B4B',
            fill_opacity=0.3 if single_is_past else 0.8,
            tooltip=_("single_location")
        ).add_to(m)

    # 지도 표시
    st_folium(m, width=1000, height=600)
    
    # 범례 표시
    st.info(f"{_('legend')}: 🔴 {_('outdoor')} | 🔵 {_('indoor')}")

# --- 알림음 재생 스크립트 (요청 반영) ---
if st.session_state.play_sound:
    # 플래그를 즉시 재설정
    st.session_state.play_sound = False
    
    # 짧은 알림음 파일을 HTML 오디오 태그로 삽입하여 자동 재생
    st.markdown("""
        <audio autoplay>
            <source src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
    """, unsafe_allow_html=True)


# --- CSS 적용 (최하단에 위치시켜야 함) ---
# NameError를 유발하던 CSS 블록의 문법 오류를 수정했습니다.
st.markdown(f"""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
/* 기본 배경/글꼴 색상 설정 (CSS 제거 요청에 따라 중립적인 색상으로 설정) */

/* 제목 컨테이너 기본 스타일 */
.header-container {{ 
    text-align: center; 
    margin: 0 !important; 
    padding-top: 20px;
    position: relative;
}}
.main-title {{
    font-size: 3em;
    margin-bottom: 0.5em;
    text-shadow: 2px 2px 4px #000000;
}}

[data-testid="stAppViewContainer"] {{ 
    /* 배경 이미지를 제거하고 다크 배경색 적용 */
    background-color: #1E1E1E;
    color: #FFFFFF;
    background-attachment: fixed; 
}}

/* Streamlit 기본 텍스트 색상 오버라이드 */
.stText {{
    color: #FFFFFF;
}}

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] button {{
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 8px 8px 0 0;
}}
.stTabs [data-baseweb="tab-list"] button [data-testid="stText"] {{
    font-weight: bold;
    color: #FFFFFF;
    text-shadow: 1px 1px 2px #000;
}}

/* 사이드바 배경 */
section[data-testid="stSidebar"] {{
    background-color: #333333;
}}

/* 입력 필드 배경 */
div[data-testid="stTextInput"] > div > div > input,
div[data-testid="stNumberInput"] > div > div > input,
div[data-testid="stTextArea"] > div > textarea,
div[data-testid="stForm"] {{
    background-color: #444444;
    color: #FFFFFF;
    border: 1px solid #777777;
}}

/* Expander 배경 */
[data-testid$="stExpander"] {{
    background-color: #2E2E2E;
    border-radius: 8px;
    border: 1px solid #555555;
}}

/* 버튼 스타일 */
.stButton > button {{
    background-color: #4CAF50; /* Green */
    color: white;
    border: 1px solid #388E3C;
    font-weight: bold;
}}
.stButton > button:hover {{
    background-color: #388E3C;
    border-color: #4CAF50;
}}

/* Selectbox와 Date Input의 배경 */
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stDateInput"] > div > div {{
    background-color: #444444;
    color: #FFFFFF;
}}

/* st.info/st.warning 등의 텍스트 색상 */
div[data-testid="stAlert"] {{
    color: #FFFFFF !important;
}}

</style>
""", unsafe_allow_html=True)
