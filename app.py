import json
import os
import uuid
import base64
import random
import streamlit as st
from datetime import datetime, date
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
        "date": "등록일", "city_name": "도시 이름", "search_placeholder": "도시/장소 검색..."
    },
    "en": {
        "title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
        "tab_notice": "Notice", "tab_map": "Tour Route", "indoor": "Indoor", "outdoor": "Outdoor",
        "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps",
        "warning": "Enter city and venue", "delete": "Remove", "menu": "Menu", "login": "Login", "logout": "Logout",
        "add_city": "Add", "register": "Register", "update": "Update", "remove": "Remove",
        "date": "Date", "city_name": "City Name", "search_placeholder": "Search City/Venue..."
    },
    "hi": {
        "title_cantata": "कैंटाटा टूर", "title_year": "२०२५", "title_region": "महाराष्ट्र",
        "tab_notice": "सूचना", "tab_map": "टूर रूट", "indoor": "इनडोर", "outdoor": "आउटडोर",
        "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप्स",
        "warning": "शहर और स्थल दर्ज करें", "delete": "हटाएं", "menu": "मेनू", "login": "लॉगिन", "logout": "लॉगआउट",
        "add_city": "जोड़ें", "register": "रजिस्टर", "update": "अपडेट", "remove": "हटाएं",
        "date": "तारीख", "city_name": "शहर का नाम", "search_placeholder": "शहर/स्थल खोजें..."
    }
}

# --- 세션 초기화 ---
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False, "logged_in_user": None, "show_login_form": False}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
    elif k == "lang" and not isinstance(st.session_state[k], str):
        st.session_state[k] = "ko"

# --- 번역 함수 ---
def _(key):
    lang = st.session_state.lang if isinstance(st.session_state.lang, str) else "ko"
    return LANG.get(lang, LANG["ko"]).get(key, key)

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
ADMIN_PASS = "0009" # 요청 반영: 비밀번호를 '0009'로 변경
# 실제로는 보안 강화를 해야 합니다.

# 요청 반영: 제목 스타일 및 애니메이션을 위한 HTML 마크다운 처리
icons_html = """
    <i class="fas fa-gift christmas-icon icon-gift"></i>
    <i class="fas fa-candy-cane christmas-icon icon-cane"></i>
    <i class="fas fa-socks christmas-icon icon-sock"></i>
    <i class="fas fa-tree christmas-icon icon-tree"></i>
    <i class="fas fa-deer christmas-icon icon-deer"></i>
"""
title_html = f"""
    <div class="header-container">
        <div class="christmas-decoration">{icons_html}</div>
        <h1 class="main-title">
            <span style="color: red;">{_('title_cantata')}</span> 
            <span style="color: white;">{_('title_year')}</span>
            <span style="color: green; font-size: 0.66em;">{_('title_region')}</span>
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
        "Language", 
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
            st.success("Logged out.")
            st.rerun()
    else:
        # 로그인 버튼 클릭 시 폼 표시 상태 변경
        if st.button(_("login"), key="login_btn"):
            st.session_state.show_login_form = not st.session_state.show_login_form
        
        # 폼 표시 상태가 True일 때만 폼을 렌더링
        if st.session_state.show_login_form:
            with st.form("login_form_permanent", clear_on_submit=False):
                st.write("Admin Login")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(_("login"))
                
                if submitted:
                    if password == ADMIN_PASS:
                        st.session_state.admin = True
                        st.session_state.logged_in_user = "Admin"
                        st.session_state.show_login_form = False # 성공하면 폼 숨김
                        st.success("Logged in as Admin.")
                        st.rerun()
                    else:
                        st.error("Incorrect password.")
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
                notice_type = st.radio("Type", ["General", "Urgent"])
                
                submitted = st.form_submit_button(_("register"))
                if submitted and notice_title and notice_content:
                    new_notice = {
                        "id": str(uuid.uuid4()),
                        "title": notice_title,
                        "content": notice_content,
                        "type": notice_type,
                        "date": datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S") # IST 기준 시간
                    }
                    tour_notices.insert(0, new_notice) # 최신순으로 맨 앞에 추가
                    save_json(NOTICE_FILE, tour_notices)
                    st.success("Notice registered successfully!")
                    st.rerun()
                elif submitted:
                    st.warning("Please fill in the title and content.")
        
        # --- 관리자: 공지사항 목록 및 수정/삭제 ---
        st.subheader("Existing Notices")
        
        # 안정성 강화: 유효한 형식의 공지사항만 필터링하고 날짜순으로 정렬
        valid_notices = [n for n in tour_notices if isinstance(n, dict) and n.get('id') and n.get('title')]
        notices_to_display = sorted(valid_notices, key=lambda x: x.get('date', '9999-12-31'), reverse=True)
        
        for notice in notices_to_display:
            notice_id = notice['id'] # 이제 'id'는 반드시 존재
            notice_type = notice.get('type', 'General')
            notice_title = notice['title'] # 이제 'title'은 반드시 존재
            
            with st.expander(f"[{notice_type}] {notice_title} ({notice.get('date', 'N/A')[:10]})", expanded=False):
                col_del, col_title = st.columns([1, 4])
                with col_del:
                    if st.button(_("remove"), key=f"del_n_{notice_id}", help="Delete Notice"):
                        tour_notices[:] = [n for n in tour_notices if n.get('id') != notice_id]
                        save_json(NOTICE_FILE, tour_notices)
                        st.success("Notice deleted.")
                        st.rerun()
                
                with col_title:
                    st.markdown(f"**Content:** {notice.get('content', 'No Content')}")
                
                # 간단한 업데이트 로직 추가
                with st.form(f"update_notice_{notice_id}", clear_on_submit=True):
                    updated_content = st.text_area("Update Content", value=notice.get('content', ''))
                    if st.form_submit_button(_("update")):
                        for n in tour_notices:
                            if n.get('id') == notice_id:
                                n['content'] = updated_content
                                n['type'] = notice_type
                                save_json(NOTICE_FILE, tour_notices)
                                st.success("Notice updated.")
                                st.rerun()
                        
    else:
        # --- 사용자: 공지사항 보기 (안정성 강화) ---
        valid_notices = [n for n in tour_notices if isinstance(n, dict) and n.get('title')]
        if not valid_notices:
            st.info("No notices available.")
        else:
            notices_to_display = sorted(valid_notices, key=lambda x: x.get('date', '9999-12-31'), reverse=True)
            for notice in notices_to_display:
                notice_type = notice.get('type', 'General')
                notice_title = notice.get('title', 'No Title')
                notice_content = notice.get('content', 'No content available.')
                
                st.markdown(f"**[{notice_type}] {notice_title}** - *{notice.get('date', 'N/A')[:16]}*")
                st.info(notice_content)
                st.markdown("---")


# =============================================================================
# 탭 2: 투어 경로 (Map)
# =============================================================================
with tab2:
    st.subheader(f"🗺️ {_('tab_map')}")
    
    # --- 관리자: 투어 일정 관리 ---
    if st.session_state.admin:
        st.markdown(f"**{_('register')} {_('tab_map')} Data**")
        
        with st.expander(_("add_city"), expanded=True):
            with st.form("schedule_form", clear_on_submit=True):
                col_c, col_d, col_v = st.columns(3)
                
                city_name_input = col_c.selectbox(_('city_name'), options=city_options, index=city_options.index("공연없음") if "공연없음" in city_options else 0)
                schedule_date = col_d.date_input("Date")
                venue_name = col_v.text_input(_("venue"))
                
                col_l, col_s, col_n = st.columns(3)
                type_sel = col_l.radio("Type", [_("indoor"), _("outdoor")])
                expected_seats = col_s.number_input(_("seats"), min_value=0, value=100)
                google_link = col_n.text_input(_("google_link"))
                
                note = st.text_area(_("note"))
                
                submitted = st.form_submit_button(_("register"))
                
                if submitted:
                    if city_name_input == "공연없음" or not venue_name or not schedule_date:
                        st.error(_("warning"))
                    elif city_name_input not in city_dict:
                        st.error(f"Coordinates for '{city_name_input}' not found in city_dict. Please add it to the city_dict.")
                    else:
                        city_coords = city_dict[city_name_input]
                        new_schedule_entry = {
                            "id": str(uuid.uuid4()),
                            "city": city_name_input,
                            "venue": venue_name,
                            "lat": city_coords["lat"],
                            "lon": city_coords["lon"],
                            "date": schedule_date.strftime("%Y-%m-%d"),
                            "type": type_sel,
                            "seats": str(expected_seats),
                            "note": note,
                            "google_link": google_link,
                            "reg_date": datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
                        }
                        tour_schedule.append(new_schedule_entry)
                        save_json(CITY_FILE, tour_schedule)
                        st.success(f"Schedule for {city_name_input} registered.")
                        st.rerun()
                        
        
        # --- 관리자: 일정 보기 및 수정/삭제 (안정성 강화) ---
        
        # 안정성 강화: 유효한 형식의 일정만 필터링
        valid_schedule = [
            item 
            for item in tour_schedule 
            if isinstance(item, dict) and item.get('id') and item.get('city') and item.get('venue')
        ]
        
        if valid_schedule:
            st.subheader("Tour Schedule Management")
            
            # id를 기준으로 딕셔너리로 변환
            schedule_dict = {item['id']: item for item in valid_schedule}
            
            # 날짜를 기준으로 정렬
            sorted_schedule_items = sorted(schedule_dict.items(), key=lambda x: x[1].get('date', '9999-12-31'))

            for item_id, item in sorted_schedule_items:
                with st.expander(f"[{item.get('date', 'N/A')}] {item['city']} - {item['venue']}", expanded=False):
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
                            st.success(f"Schedule entry for {item['city']} removed.")
                            st.rerun()

                    if st.session_state.get(f"edit_mode_{item_id}"):
                        with st.form(f"edit_form_{item_id}"):
                            col_uc, col_ud, col_uv = st.columns(3)
                            
                            updated_city = col_uc.selectbox("City", city_options, index=city_options.index(item.get('city', "공연없음")))
                            
                            # 날짜 형식 처리 개선
                            try:
                                initial_date = datetime.strptime(item.get('date', '2025-01-01'), "%Y-%m-%d").date()
                            except ValueError:
                                initial_date = date.today()
                                
                            updated_date = col_ud.date_input("Date", value=initial_date)
                            updated_venue = col_uv.text_input("Venue", value=item.get('venue'))
                            
                            col_ul, col_us, col_ug = st.columns(3)
                            updated_type = col_ul.radio("Type", [_("indoor"), _("outdoor")], index=[_("indoor"), _("outdoor")].index(item.get('type', 'outdoor')))
                            seats_value = item.get('seats', '0')
                            updated_seats = col_us.number_input("Seats", min_value=0, value=int(seats_value) if str(seats_value).isdigit() else 0)
                            updated_google = col_ug.text_input("Google Link", value=item.get('google_link', ''))

                            updated_note = st.text_area("Note", value=item.get('note'))
                            
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
                                            "type": updated_type,
                                            "seats": str(updated_seats),
                                            "note": updated_note,
                                            "google_link": updated_google,
                                            "reg_date": s.get('reg_date', datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S"))
                                        }
                                        save_json(CITY_FILE, tour_schedule)
                                        st.session_state[f"edit_mode_{item_id}"] = False
                                        st.success("Schedule updated successfully.")
                                        st.rerun()
                        
                    if not st.session_state.get(f"edit_mode_{item_id}"):
                        st.markdown(f"**{_('date')}:** {item.get('date', 'N/A')} ({item.get('reg_date', '')})")
                        st.markdown(f"**{_('venue')}:** {item.get('venue', 'N/A')}")
                        st.markdown(f"**{_('seats')}:** {item.get('seats', 'N/A')}")
                        st.markdown(f"**Type:** {item.get('type', 'N/A')}")
                        if item.get('google_link'):
                            google_link_url = item['google_link']
                            st.markdown(f"**{_('google_link')}:** [{_('google_link')}]({google_link_url})")
                        st.markdown(f"**{_('note')}:** {item.get('note', 'N/A')}")


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
        
        # 마커 색상 설정
        color = 'blue' if item.get('type') == 'indoor' else 'red'
        
        # 요청 반영: 지난 도시 30% 투명도, 미래 도시 100% 투명도
        opacity_val = 0.3 if is_past else 1.0
        
        # 팝업 내용
        popup_html = f"""
        <b>City:</b> {item.get('city', 'N/A')}<br>
        <b>Date:</b> {date_str}<br>
        <b>Venue:</b> {item.get('venue', 'N/A')}<br>
        <b>Seats:</b> {item.get('seats', 'N/A')}<br>
        """
        
        if item.get('google_link'):
            google_link_url = item['google_link'] 
            popup_html += f'<a href="{google_link_url}" target="_blank">{_("google_link")}</a>'
        
        # 요청 반영: DivIcon을 사용하여 2/3 크기 (scale 0.666) 및 투명도 적용
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

        # 요청 반영: 지난 도시/라인 30% 투명도의 빨간색 선
        if len(past_segments) > 1:
            folium.PolyLine(
                locations=past_segments,
                color="#FF4B4B", # Streamlit Red
                weight=5,
                opacity=0.3,
                tooltip="Past Route"
            ).add_to(m)
            
        # 요청 반영: 도시간 연결선 80% 투명도의 빨간색 AntPath
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
            tooltip="Single Location"
        ).add_to(m)

    # 지도 표시
    st_folium(m, width=1000, height=600)
    
    # 범례 표시
    st.info(f"Legend: 🔴 {_('outdoor')} | 🔵 {_('indoor')}")

# --- CSS 적용 (최하단에 위치시켜야 함) ---
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
/* 요청 반영: 투명한 눈 입자 애니메이션 */
@keyframes snowfall {
    0% { background-position: 0% 0%, 50% 50%, 100% 100%; }
    100% { background-position: 500px 1000px, 0px 500px, -500px 500px; }
}

[data-testid="stAppViewContainer"] { 
    background: url("background_christmas_dark.png"); 
    background-size: cover; 
    background-attachment: fixed; 
    padding-top: 0 !important; 
    position: relative;
}

[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 99999; /* Ensure snow is on top of content */
    pointer-events: none; /* Allows clicks through the snow */
    /* Three layers of snow with different sizes/speeds for depth and transparency */
    background-image:
        radial-gradient(4px 4px at 20px 20px, rgba(255, 255, 255, 0.6), transparent),
        radial-gradient(3px 3px at 70px 70px, rgba(255, 255, 255, 0.8), transparent),
        radial-gradient(2px 2px at 120px 120px, rgba(255, 255, 255, 0.4), transparent);
    background-size: 500px 500px, 200px 200px, 300px 300px;
    animation: snowfall 50s linear infinite; /* 느린 연속적인 움직임 */
}

/* 요청 반영: 제목 아이콘 애니메이션 */
@keyframes float {
    0% { transform: translate(0, 0) rotate(0deg); opacity: 0.8; }
    50% { transform: translate(10px, -10px) rotate(5deg); opacity: 1; }
    100% { transform: translate(0, 0) rotate(0deg); opacity: 0.8; }
}

/* 헤더 스타일 및 애니메이션 컨테이너 */
.header-container { 
    text-align: center; 
    margin: 0 !important; 
    padding-top: 20px;
    position: relative; /* Ensure the decoration is positioned correctly */
}
.main-title {
    font-size: 3em;
    margin-bottom: 0.5em;
    text-shadow: 2px 2px 4px #000000;
}
.christmas-decoration {
    position: absolute;
    top: -50px; /* 제목 위로 이동 */
    height: 60px; /* 아이콘 움직일 공간 */
    width: 100%;
    overflow: visible; /* 아이콘이 컨테이너를 벗어나 움직일 수 있도록 */
    pointer-events: none;
}

.christmas-icon {
    position: absolute;
    animation: float 10s ease-in-out infinite alternate;
    z-index: 10;
}

/* 개별 아이콘 스타일 (랜덤 크기, 위치, 속도) */
.icon-gift { left: 10%; top: 5px; font-size: 25px; color: #00ff00; animation-duration: 12s; } /* Green */
.icon-cane { left: 30%; top: 15px; font-size: 35px; color: white; animation-duration: 9s; }
.icon-sock { right: 40%; top: 10px; font-size: 20px; color: #ff4b4b; animation-duration: 15s; } /* Red */
.icon-tree { right: 15%; top: 0px; font-size: 40px; color: #00ff00; animation-duration: 11s; } /* Green */
.icon-deer { left: 50%; top: 20px; font-size: 30px; color: #8B4513; animation-duration: 13s; } /* Brown */

/* 탭 스타일 개선 (크리스마스 테마색) */
.stTabs [data-baseweb="tab-list"] button {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 8px 8px 0 0;
}
.stTabs [data-baseweb="tab-list"] button [data-testid="stText"] {
    font-weight: bold;
    color: #ff4b4b; /* Red accent */
    text-shadow: 1px 1px 2px #000;
}
.stTabs [aria-selected="true"] {
    background-color: rgba(255, 255, 255, 0.2) !important;
}

/* 배경 이미지 적용 시 사이드바 배경이 흰색이 되는 것을 방지 */
section[data-testid="stSidebar"] {
    background-color: rgba(0, 0, 0, 0.8);
    border-right: 2px solid #ff4b4b; /* Christmas color border */
}

/* 일반 텍스트 입력 필드 배경 */
div[data-testid="stTextInput"] > div > div > input,
div[data-testid="stNumberInput"] > div > div > input,
div[data-testid="stTextArea"] > div > textarea,
div[data-testid="stForm"] {
    background-color: rgba(255, 255, 255, 0.9);
    color: black;
}

/* Expander 배경을 투명하게 만들어 배경 이미지 보이게 하기 */
[data-testid$="stExpander"] {
    background-color: rgba(10, 10, 10, 0.85);
    border-radius: 8px;
    border: 1px solid #00ff00; /* Green accent border */
}

/* 버튼 스타일 (로그인/로그아웃/등록 등) */
.stButton > button {
    background-color: #ff4b4b; /* Red button */
    color: white;
    border: 1px solid #cc0000;
    font-weight: bold;
}
.stButton > button:hover {
    background-color: #cc0000;
    border-color: #ff4b4b;
}

/* Selectbox와 Date Input의 흰색 배경 투명도 조정 */
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stDateInput"] > div > div {
    background-color: rgba(255, 255, 255, 0.9);
}

</style>
""", unsafe_allow_html=True)
