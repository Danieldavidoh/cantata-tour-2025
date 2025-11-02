import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
import math
# =============================================
# 1. 다국어 사전
# =============================================
LANG = {
    "en": {
        "title": "Cantata Tour 2025",
        "start_city": "Starting City",
        "start_btn": "Start",
        "reset_btn": "Reset All",
        "next_city": "Next City",
        "add_btn": "Add",
        "current_route": "### Current Route",
        "total_distance": "Total Distance",
        "total_time": "Total Time",
        "venues_dates": "Venues & Dates",
        "performance_date": "Performance Date",
        "venue_name": "Venue Name",
        "seats": "Seats",
        "indoor_outdoor": "Indoor/Outdoor",
        "indoor": "Indoor",
        "outdoor": "Outdoor",
        "google_link": "Google Maps Link",
        "register": "Register",
        "add_venue": "Add Venue",
        "edit": "Edit",
        "open_maps": "Open in Google Maps",
        "save": "Save",
        "delete": "Delete",
        "tour_map": "Tour Map",
        "caption": "Mobile: Add to Home Screen -> Use like an app!",
        "date_format": "%b %d, %Y",
        "admin_mode": "Admin Mode",
        "guest_mode": "Guest Mode",
        "enter_password": "Enter password to access Admin Mode",
        "submit": "Submit",
        "drive_to": "Drive Here",
        "edit_venue": "Edit",
        "delete_venue": "Delete",
        "confirm_delete": "Are you sure you want to delete?",
        "close": "Close",
    },
    "ko": {
        "title": "칸타타 투어 2025",
        "start_city": "출발 도시",
        "start_btn": "시작",
        "reset_btn": "전체 초기화",
        "next_city": "다음 도시",
        "add_btn": "추가",
        "current_route": "### 현재 경로",
        "total_distance": "총 거리",
        "total_time": "총 소요시간",
        "venues_dates": "공연장 & 날짜",
        "performance_date": "공연 날짜",
        "venue_name": "공연장 이름",
        "seats": "좌석 수",
        "indoor_outdoor": "실내/실외",
        "indoor": "실내",
        "outdoor": "실외",
        "google_link": "구글 지도 링크",
        "register": "등록",
        "add_venue": "공연장 추가",
        "edit": "편집",
        "open_maps": "구글 지도 열기",
        "save": "저장",
        "delete": "삭제",
        "tour_map": "투어 지도",
        "caption": "모바일: 홈 화면에 추가 -> 앱처럼 사용!",
        "date_format": "%Y년 %m월 %d일",
        "admin_mode": "관리자 모드",
        "guest_mode": "손님 모드",
        "enter_password": "관리자 모드 접근을 위한 비밀번호 입력",
        "submit": "제출",
        "drive_to": "길찾기",
        "edit_venue": "편집",
        "delete_venue": "삭제",
        "confirm_delete": "정말 삭제하시겠습니까?",
        "close": "닫기",
    },
    "hi": {
        "title": "कांताता टूर 2025",
        "start_city": "प्रारंभिक शहर",
        "start_btn": "शुरू करें",
        "reset_btn": "सब रीसेट करें",
        "next_city": "अगला शहर",
        "add_btn": "जोड़ें",
        "current_route": "### वर्तमान मार्ग",
        "total_distance": "कुल दूरी",
        "total_time": "कुल समय",
        "venues_dates": "स्थल और तिथियाँ",
        "performance_date": "प्रदर्शन तिथि",
        "venue_name": "स्थल का नाम",
        "seats": "सीटें",
        "indoor_outdoor": "इंडोर/आउटडोर",
        "indoor": "इंडोर",
        "outdoor": "आउटडोर",
        "google_link": "गूगल मैप्स लिंक",
        "register": "रजिस्टर",
        "add_venue": "स्थल जोड़ें",
        "edit": "संपादित करें",
        "open_maps": "गूगल मैप्स में खोलें",
        "save": "सहेजें",
        "delete": "हटाएँ",
        "tour_map": "टूर मैप",
        "caption": "मोबाइल: होम स्क्रीन पर जोड़ें -> ऐप की तरह उपयोग करें!",
        "date_format": "%d %b %Y",
        "admin_mode": "एडमिन मोड",
        "guest_mode": "गेस्ट मोड",
        "enter_password": "एडमिन मोड एक्सेस करने के लिए पासवर्ड दर्ज करें",
        "submit": "जमा करें",
        "drive_to": "यहाँ ड्राइव करें",
        "edit_venue": "संपादित करें",
        "delete_venue": "हटाएँ",
        "confirm_delete": "क्या आप वाकई हटाना चाहते हैं?",
        "close": "बंद करें",
    },
}
# =============================================
# 2. 크리스마스 테마 CSS + 장식 (전체 UI에 고르게 배치)
# =============================================
st.markdown("""
<style>
    /* 배경 설정 */
    .reportview-container {
        background: linear-gradient(to bottom, #0f0c29, #302b63, #24243e);
        overflow: hidden;
        position: relative;
    }
    .sidebar .sidebar-content { background: #228B22; color: white; }
    .Widget>label { color: #90EE90; font-weight: bold; }
 
    /* 제목 스타일 및 모바일 반응형 처리 */
    .christmas-title {
        font-size: 3.5em !important;
        font-weight: bold;
        text-align: center;
        text-shadow: 0 0 5px #FFF, 0 0 10px #FFF, 0 0 15px #FFF, 0 0 20px #8B0000, 0 0 35px #8B0000;
        letter-spacing: 2px;
        position: relative;
        margin: 20px 0;
    }
    .christmas-title .main { color: #FF0000 !important; }
    .christmas-title .year { color: white !important; text-shadow: 0 0 5px #FFF, 0 0 10px #FFF, 0 0 15px #FFF, 0 0 20px #00BFFF; }
 
    /* 모바일에서 한국어 제목 줄바꿈을 위한 클래스 */
    .mobile-break { display: none; }
    @media (max-width: 600px) {
        .christmas-title { font-size: 2.5em !important; }
        .mobile-break { display: block; height: 0; content: ""; } /* 강제 줄바꿈 */
    }
    .christmas-title::before {
        content: "❄️ ❄️ ❄️";
        position: absolute;
        top: -20px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 0.6em;
        color: white;
        animation: snow-fall 3s infinite ease-in-out;
    }
    @keyframes snow-fall { 0%, 100% { transform: translateX(-50%) translateY(0); } 50% { transform: translateX(-50%) translateY(10px); } }
 
    h1, h2, h3 { color: #90EE90; text-shadow: 1px 1px 3px #8B0000; text-align: center; }
    .stButton>button {
        background: #228B22;
        color: white;
        border: 2px solid #8B0000;
        border-radius: 12px;
        font-weight: bold;
        padding: 10px;
        transition: all 0.2s;
    }
    .stButton>button:hover { background: #8B0000; color: white; }
    .stTextInput>label, .stSelectbox>label, .stNumberInput>label, .stDateInput>label { color: #90EE90; }
    .stMetric { background: rgba(34,139,34,0.3); border: 2px solid #90EE90; border-radius: 12px; padding: 10px; }
    .stExpander { background: rgba(139,0,0,0.4); border: 1px solid #90EE90; border-radius: 12px; }
    .stExpander>summary { color: #90EE90; font-weight: bold; }
    .stMarkdown { color: #90EE90; }
    /* 실내/실외 버튼 스타일 */
    /* 실내 버튼 (파란색 계열) */
    .stButton>button[key*='io_toggle_'] {
        border: 2px solid #90EE90;
        background: #3CB371; /* Outdoor default */
    }
    /* 이 CSS는 버튼이 클릭될 때 Streamlit 내부적으로 세션 상태를 기반으로 인라인 스타일링을 통해 변경됩니다. */
    /* 크리스마스 장식 - 전체 UI에 고르게 배치 */
    .christmas-decoration {
        position: absolute;
        font-size: 2.5em;
        pointer-events: none;
        animation: float 6s infinite ease-in-out;
        z-index: 10;
    }
    .gift { color: #FFD700; top: 8%; left: 5%; animation-delay: 0s; }
    .candy-cane { color: #FF0000; top: 8%; right: 5%; animation-delay: 1s; transform: rotate(15deg); }
    .stocking { color: #8B0000; top: 25%; left: 3%; animation-delay: 2s; }
    .bell { color: #FFD700; top: 25%; right: 3%; animation-delay: 3s; }
    .wreath { color: #228B22; top: 45%; left: 2%; animation-delay: 4s; }
    .santa-hat { color: #FF0000; top: 45%; right: 2%; animation-delay: 5s; }
    .tree { color: #228B22; bottom: 20%; left: 10%; animation-delay: 0.5s; }
    .snowman { color: white; bottom: 20%; right: 10%; animation-delay: 2.5s; }
    .candle { color: #FFA500; top: 65%; left: 8%; animation-delay: 1.5s; }
    .star { color: #FFD700; top: 65%; right: 8%; animation-delay: 3.5s; }
    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(5deg); }
    }
    .snowflake {
        position: absolute;
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2em;
        pointer-events: none;
        animation: fall linear infinite;
        opacity: 0.9;
    }
    @keyframes fall {
        0% { transform: translateY(-100vh) rotate(0deg); opacity: 0.9; }
        100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
    }
 
    /* 지도 최대 크기 설정 */
    .st-emotion-cache-16ffz9n { /* Streamlit main content container selector */
        max-width: 100% !important;
        padding: 1rem 1rem !important; /* 모바일에서 맵 크기 확보를 위해 패딩 줄임 */
    }
    /* Date input 직접 입력 방지 (타이핑 불가) */
    .stDateInput > div > div > input {
        pointer-events: none !important;
        background-color: transparent !important;
    }
    .stDateInput > div > div > input::placeholder {
        color: #90EE90 !important;
    }
    /* Admin/Guest 모달-like 오버레이 클릭으로 닫기 */
    .stSidebar {
        position: relative;
    }
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 9999;
        display: none;
    }
    .modal-content {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #228B22;
        padding: 20px;
        border-radius: 10px;
        color: white;
        z-index: 10000;
    }
    .modal-overlay.active {
        display: block;
    }
    /* 빈 공간 클릭으로 닫기 - 사이드바 외부 클릭 감지 (JS 필요하지만 Streamlit 한계로 토글 버튼 강조) */
</style>
""", unsafe_allow_html=True)
# 크리스마스 장식 추가 (전체 UI에 고르게 배치)
st.markdown("""
<div class="christmas-decoration gift">🎁</div>
<div class="christmas-decoration candy-cane">🍭</div>
<div class="christmas-decoration stocking">🧦</div>
<div class="christmas-decoration bell">🔔</div>
<div class="christmas-decoration wreath">🌿</div>
<div class="christmas-decoration santa-hat">🎅</div>
<div class="christmas-decoration tree">🎄</div>
<div class="christmas-decoration snowman">⛄</div>
<div class="christmas-decoration candle">🕯️</div>
<div class="christmas-decoration star">⭐</div>
""", unsafe_allow_html=True)
# 눈송이 생성
import random
snowflakes = ""
for i in range(80):
    left = random.randint(0, 100)
    size = random.choice(["0.8em", "1em", "1.2em", "1.4em"])
    duration = random.uniform(8, 20)
    delay = random.uniform(0, 5)
    snowflakes += f'<div class="snowflake" style="left:{left}%;font-size:{size};animation-duration:{duration}s;animation-delay:{delay}s;">❄️</div>'
st.markdown(snowflakes, unsafe_allow_html=True)
# =============================================
# 3. 페이지 설정 + 사이드바
# =============================================
st.set_page_config(page_title="Cantata Tour 2025", layout="wide", initial_sidebar_state="collapsed")
with st.sidebar:
    st.markdown("### Language")
 
    # 세션 상태에서 언어 불러오기 또는 기본값 설정
    if 'lang' not in st.session_state:
        st.session_state.lang = "ko"
     
    lang = st.radio(
        label="Select",
        options=["en", "ko", "hi"],
        format_func=lambda x: {"en": "English", "ko": "한국어", "hi": "हिन्दी"}[x],
        horizontal=False,
        key="language_select"
    )
    _ = LANG[lang]
 
    # 언어 변경 시 세션 상태 업데이트 및 새로고침
    if lang != st.session_state.lang:
        st.session_state.lang = lang
        st.rerun()
    # 빈 공간 클릭으로 닫기 - 사이드바 확장 상태에서 외부 클릭 시 reruns (Streamlit 한계로 토글 버튼으로 대체, 추가 close 버튼)
    if st.button(_["close"], key="close_sidebar"):
        st.session_state.show_pw = False
        st.rerun()
    st.markdown("---")
    st.markdown("### Admin")
 
    # 세션 상태 초기화
    if 'admin' not in st.session_state:
        st.session_state.admin = False
    if 'show_pw' not in st.session_state:
        st.session_state.show_pw = False
    if 'guest_mode' not in st.session_state:
        st.session_state.guest_mode = False
    if st.session_state.admin:
        st.success("Admin Mode Active")
        if st.button(_["guest_mode"]):
            st.session_state.guest_mode = True
            st.session_state.admin = False
            st.session_state.show_pw = False # Admin -> Guest 시 비밀번호 입력창 닫음
            st.rerun()
    else:
        # 비밀번호 입력 폼을 토글 버튼 아래에 배치
        if st.button(_["admin_mode"]):
            st.session_state.show_pw = not st.session_state.show_pw # 토글 기능
         
        if st.session_state.show_pw:
            with st.form("admin_login_form"):
                pw = st.text_input(_["enter_password"], type="password", key="admin_pw_input")
                col_pw, col_close = st.columns([3,1])
                with col_pw:
                    pass
                with col_close:
                    if st.button(_["close"], key="close_pw"):
                        st.session_state.show_pw = False
                        st.rerun()
                if st.form_submit_button(_["submit"]):
                    if pw == "0691":
                        st.session_state.admin = True
                        st.session_state.show_pw = False
                        st.session_state.guest_mode = False
                        st.success("Activated!")
                        st.rerun()
                    else:
                        st.error("Incorrect")
    if st.session_state.admin:
        st.markdown("---")
        if st.button(_["reset_btn"]):
            for key in list(st.session_state.keys()):
                if key not in ['lang']: # 언어 설정은 유지
                    del st.session_state[key]
            st.rerun()
         
# =============================================
# 4. 세션 초기화
# =============================================
if 'tour_stops' not in st.session_state:
    default_stop = {
        'city': 'Mumbai',
        'date': datetime.now().date(),
        'venue': '',
        'seats': 100,
        'io': _["outdoor"],
        'link': '',
        'registered': False
    }
    st.session_state.tour_stops = [default_stop]
if 'show_city' not in st.session_state:
    st.session_state.show_city = {}
# =============================================
# 5. 도시 목록 및 좌표
# =============================================
cities = sorted([
    'Mumbai', 'Pune', 'Nagpur', 'Nashik', 'Thane', 'Aurangabad', 'Solapur', 'Amravati', 'Nanded', 'Kolhapur',
    'Akola', 'Latur', 'Ahmadnagar', 'Jalgaon', 'Dhule', 'Ichalkaranji', 'Malegaon', 'Bhusawal', 'Bhiwandi', 'Bhandara',
    'Beed', 'Buldana', 'Chandrapur', 'Dharashiv', 'Gondia', 'Hingoli', 'Jalna', 'Mira-Bhayandar', 'Nandurbar', 'Osmanabad',
    'Palghar', 'Parbhani', 'Ratnagiri', 'Sangli', 'Satara', 'Sindhudurg', 'Wardha', 'Washim', 'Yavatmal', 'Kalyan-Dombivli',
    'Ulhasnagar', 'Vasai-Virar', 'Sangli-Miraj-Kupwad', 'Nanded-Waghala', 'Bandra (Mumbai)', 'Colaba (Mumbai)', 'Andheri (Mumbai)',
    'Boric Nagar (Mumbai)', 'Navi Mumbai', 'Mumbai Suburban', 'Pimpri-Chinchwad (Pune)', 'Koregaon Park (Pune)', 'Kothrud (Pune)',
    'Hadapsar (Pune)', 'Pune Cantonment', 'Nashik Road', 'Deolali (Nashik)', 'Satpur (Nashik)', 'Aurangabad City', 'Jalgaon City',
    'Bhopalwadi (Aurangabad)', 'Nagpur City', 'Sitabuldi (Nagpur)', 'Jaripatka (Nagpur)', 'Solapur City', 'Hotgi (Solapur)',
    'Pandharpur (Solapur)', 'Amravati City', 'Badnera (Amravati)', 'Paratwada (Amravati)', 'Akola City', 'Murtizapur (Akola)',
    'Washim City', 'Mangrulpir (Washim)', 'Yavatmal City', 'Pusad (Yavatmal)', 'Darwha (Yavatmal)', 'Wardha City',
    'Sindi (Wardha)', 'Hinganghat (Wardha)', 'Chandrapur City', 'Brahmapuri (Chandrapur)', 'Mul (Chandrapur)', 'Gadchiroli',
    'Aheri (Gadchiroli)', 'Dhanora (Gadchiroli)', 'Gondia City', 'Tiroda (Gondia)', 'Arjuni Morgaon (Gondia)',
    'Bhandara City', 'Pauni (Bhandara)', 'Tumsar (Bhandara)', 'Nagbhid (Chandrapur)', 'Gadhinglaj (Kolhapur)',
    'Kagal (Kolhapur)', 'Ajra (Kolhapur)', 'Shiroli (Kolhapur)'
])
coords = {
    'Mumbai': (19.07, 72.88), 'Pune': (18.52, 73.86), 'Nagpur': (21.15, 79.08), 'Nashik': (20.00, 73.79),
    'Thane': (19.22, 72.98), 'Aurangabad': (19.88, 75.34), 'Solapur': (17.67, 75.91), 'Amravati': (20.93, 77.75),
    'Nanded': (19.16, 77.31), 'Kolhapur': (16.70, 74.24), 'Akola': (20.70, 77.00), 'Latur': (18.40, 76.57),
    'Ahmadnagar': (19.10, 74.75), 'Jalgaon': (21.00, 75.57), 'Dhule': (20.90, 74.77), 'Ichalkaranji': (16.69, 74.47),
    'Malegaon': (20.55, 74.53), 'Bhusawal': (21.05, 76.00), 'Bhiwandi': (19.30, 73.06), 'Bhandara': (21.17, 79.65),
    'Beed': (18.99, 75.76), 'Buldana': (20.54, 76.18), 'Chandrapur': (19.95, 79.30), 'Dharashiv': (18.40, 76.57),
    'Gondia': (21.46, 80.19), 'Hingoli': (19.72, 77.15), 'Jalna': (19.85, 75.89), 'Mira-Bhayandar': (19.28, 72.87),
    'Nandurbar': (21.37, 74.22), 'Osmanabad': (18.18, 76.07), 'Palghar': (19.70, 72.77), 'Parbhani': (19.27, 76.77),
    'Ratnagiri': (16.99, 73.31), 'Sangli': (16.85, 74.57), 'Satara': (17.68, 74.02), 'Sindhudurg': (16.24, 73.42),
    'Wardha': (20.75, 78.60), 'Washim': (20.11, 77.13), 'Yavatmal': (20.39, 78.12), 'Kalyan-Dombivli': (19.24, 73.13),
    'Ulhasnagar': (19.22, 73.16), 'Vasai-Virar': (19.37, 72.81), 'Sangli-Miraj-Kupwad': (16.85, 74.57), 'Nanded-Waghala': (19.16, 77.31),
    'Bandra (Mumbai)': (19.06, 72.84), 'Colaba (Mumbai)': (18.92, 72.82), 'Andheri (Mumbai)': (19.12, 72.84), 'Boric Nagar (Mumbai)': (19.07, 72.88),
    'Navi Mumbai': (19.03, 73.00), 'Mumbai Suburban': (19.07, 72.88), 'Pimpri-Chinchwad (Pune)': (18.62, 73.80), 'Koregaon Park (Pune)': (18.54, 73.90),
    'Kothrud (Pune)': (18.50, 73.81), 'Hadapsar (Pune)': (18.51, 73.94), 'Pune Cantonment': (18.50, 73.89), 'Nashik Road': (20.00, 73.79),
    'Deolali (Nashik)': (19.94, 73.82), 'Satpur (Nashik)': (20.01, 73.79), 'Aurangabad City': (19.88, 75.34), 'Jalgaon City': (21.00, 75.57),
    'Bhopalwadi (Aurangabad)': (19.88, 75.34), 'Nagpur City': (21.15, 79.08), 'Sitabuldi (Nagpur)': (21.14, 79.08), 'Jaripatka (Nagpur)': (21.12, 79.07),
    'Solapur City': (17.67, 75.91), 'Hotgi (Solapur)': (17.57, 75.95), 'Pandharpur (Solapur)': (17.66, 75.32), 'Amravati City': (20.93, 77.75),
    'Badnera (Amravati)': (20.84, 77.73), 'Paratwada (Amravati)': (21.06, 77.21), 'Akola City': (20.70, 77.00), 'Murtizapur (Akola)': (20.73, 77.37),
    'Washim City': (20.11, 77.13), 'Mangrulpir (Washim)': (20.31, 77.05), 'Yavatmal City': (20.39, 78.12), 'Pusad (Yavatmal)': (19.91, 77.57),
    'Darwha (Yavatmal)': (20.31, 77.78), 'Wardha City': (20.75, 78.60), 'Sindi (Wardha)': (20.82, 78.09), 'Hinganghat (Wardha)': (20.58, 78.58),
    'Chandrapur City': (19.95, 79.30), 'Brahmapuri (Chandrapur)': (20.61, 79.89), 'Mul (Chandrapur)': (19.95, 79.06), 'Gadchiroli': (20.09, 80.11),
    'Aheri (Gadchiroli)': (19.37, 80.18), 'Dhanora (Gadchiroli)': (19.95, 80.15), 'Gondia City': (21.46, 80.19), 'Tiroda (Gondia)': (21.28, 79.68),
    'Arjuni Morgaon (Gondia)': (21.29, 80.20), 'Bhandara City': (21.17, 79.65), 'Pauni (Bhandara)': (21.07, 79.81), 'Tumsar (Bhandara)': (21.37, 79.75),
    'Nagbhid (Chandrapur)': (20.29, 79.36), 'Gadhinglaj (Kolhapur)': (16.23, 74.34), 'Kagal (Kolhapur)': (16.57, 74.31), 'Ajra (Kolhapur)': (16.67, 74.22),
    'Shiroli (Kolhapur)': (16.70, 74.24)
}
# =============================================
# 6. 제목 (모바일 반응형 적용)
# =============================================
title_text = _['title']
if lang == 'ko':
    # 한국어: "칸타타"와 "투어 2025"를 분리하고, CSS를 사용하여 모바일에서 줄바꿈
    parts = title_text.split()
    main_part = parts[0] # 칸타타
    rest_part = " ".join(parts[1:]) # 투어 2025
    title_html = f'<span class="main">{main_part}</span><span class="mobile-break"></span> <span class="year">{rest_part}</span>'
else:
    # 기타 언어: 기존 로직 사용
    title_parts = title_text.rsplit(' ', 1)
    main_title = title_parts[0]
    year = title_parts[1] if len(title_parts) > 1 else ""
    title_html = f'<span class="main">{main_title}</span> <span class="year">{year}</span>'
st.markdown(f'<h1 class="christmas-title">{title_html}</h1>', unsafe_allow_html=True)
# =============================================
# 7. Haversine 거리 계산 함수
# =============================================
def haversine(c1, c2):
    if c1 not in coords or c2 not in coords:
        return 0, 0.0
    lat1, lon1 = coords[c1]
    lat2, lon2 = coords[c2]
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    km = round(R * c)
    hrs = round(km / 50, 1)  # Avg speed 50km/h
    return km, hrs
# =============================================
# 8. 공연장 & 날짜 (최상단 배치)
# =============================================
st.markdown("---")
st.subheader(_["venues_dates"])
is_mode = st.session_state.admin or st.session_state.guest_mode
if is_mode:
    _, col_add = st.columns([4, 1])
    with col_add:
        if st.button(_["add_btn"], use_container_width=True):
            default_stop = {
                'city': 'Mumbai',
                'date': datetime.now().date(),
                'venue': '',
                'seats': 100,
                'io': _["outdoor"],
                'link': '',
                'registered': False
            }
            st.session_state.tour_stops.append(default_stop)
            st.rerun()
for i in range(len(st.session_state.tour_stops)):
    stop = st.session_state.tour_stops[i]
    st.markdown("---")
    st.markdown(f"### Stop {i+1}")
    # 도시 선택 (상단 왼쪽)
    current_city = stop['city']
    if is_mode:
        if st.button(current_city, key=f"city_btn_{i}"):
            st.session_state.setdefault('show_city', {})
            st.session_state.show_city[i] = True
            st.rerun()
        if st.session_state.get('show_city', {}).get(i, False):
            used_others = {st.session_state.tour_stops[j]['city'] for j in range(len(st.session_state.tour_stops)) if j != i}
            available = [c for c in cities if c not in used_others]
            idx = available.index(current_city)
            sel_city = st.selectbox("", options=available, index=idx, key=f"sel_city_{i}")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if st.button("Confirm", key=f"conf_city_{i}"):
                    stop['city'] = sel_city
                    st.session_state.show_city[i] = False
                    st.rerun()
            with col_c2:
                if st.button("Cancel", key=f"can_city_{i}"):
                    st.session_state.show_city[i] = False
                    st.rerun()
    else:
        st.markdown(f"**City:** {current_city}")
    # 공연 날짜 (왼쪽, 달력 선택)
    new_date = st.date_input(_["performance_date"], value=stop['date'], key=f"date_{i}", help="Click calendar to select date only")
    if new_date != stop['date']:
        stop['date'] = new_date
        st.rerun()
    if is_mode:
        registered = stop.get('registered', False)
        if registered:
            # 등록된 상태: 표시 모드
            col_vn, col_io = st.columns([3, 1])
            with col_vn:
                st.write(f"**{_['venue_name']}** {stop['venue']}")
                st.caption(f"{stop['seats']} {_['seats']}")
            with col_io:
                color = "🔵" if stop['io'] == _["indoor"] else "🟢"
                st.write(f"{color} {stop['io']}")
            col_gl, col_car = st.columns([3, 1])
            with col_gl:
                st.write(f"{_['google_link']}: {stop['link']}")
            with col_car:
                if stop['link'].startswith("http"):
                    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={stop['link']}&travelmode=driving"
                    st.markdown(f"""
                        <a href="{maps_url}" target="_blank" style="font-size: 24px; text-decoration: none; color: #FFD700; display: block; text-align: center;" title="{_['drive_to']}">
                            🚗
                        </a>
                    """, unsafe_allow_html=True)
            col_e, col_d = st.columns([1, 1])
            with col_e:
                if st.button(_["edit"], key=f"edit_{i}"):
                    stop['registered'] = False
                    st.rerun()
            with col_d:
                if st.button(_["delete"], key=f"del_{i}"):
                    del st.session_state.tour_stops[i]
                    if 'show_city' in st.session_state and i in st.session_state.show_city:
                        del st.session_state.show_city[i]
                    st.rerun()
        else:
            # 입력 모드
            col_vn, col_s = st.columns([3, 1])
            with col_vn:
                new_venue = st.text_input(_["venue_name"], value=stop['venue'], key=f"v_{i}")
                if new_venue != stop['venue']:
                    stop['venue'] = new_venue
                    st.rerun()
            with col_s:
                new_seats = st.number_input(_["seats"], min_value=1, step=50, value=stop['seats'], key=f"s_{i}")
                if new_seats != stop['seats']:
                    stop['seats'] = new_seats
                    st.rerun()
            # 실내/실외 토글
            st.markdown(_["indoor_outdoor"])
            is_indoor = stop['io'] == _["indoor"]
            button_text = _["indoor"] if is_indoor else _["outdoor"]
            button_style = 'background: #1E90FF; border: 2px solid #00BFFF; color: white;' if is_indoor else 'background: #3CB371; border: 2px solid #90EE90; color: white;'
            st.markdown(f"""
                <style>
                    .stButton > button[key='io_{i}'] {{
                        {button_style}
                        border-radius: 12px;
                        font-weight: bold;
                    }}
                </style>
            """, unsafe_allow_html=True)
            if st.button(button_text, key=f"io_{i}", use_container_width=True):
                stop['io'] = _["indoor"] if not is_indoor else _["outdoor"]
                st.rerun()
            col_gl, col_car_dummy = st.columns([3, 1])
            with col_gl:
                new_link = st.text_input(_["google_link"], value=stop['link'], placeholder="https://...", key=f"l_{i}")
                if new_link != stop['link']:
                    stop['link'] = new_link
                    st.rerun()
            with col_car_dummy:
                st.write("")
            if st.button(_["register"], use_container_width=True):
                if stop['venue']:
                    stop['registered'] = True
                    st.success("등록 완료")
                    st.rerun()
                else:
                    st.error("공연장 이름을 입력하세요.")
    else:
        # 비 모드: 등록된 경우만 표시
        if stop.get('registered', False):
            col_vn, col_io = st.columns([3, 1])
            with col_vn:
                st.write(f"**Venue:** {stop['venue']}")
                st.caption(f"{stop['seats']} seats")
            with col_io:
                color = "🔵" if stop['io'] == _["indoor"] else "🟢"
                st.write(f"{color} {stop['io']}")
            col_gl, col_car = st.columns([3, 1])
            with col_gl:
                st.write(f"Google Link: {stop['link']}")
            with col_car:
                if stop['link'].startswith("http"):
                    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={stop['link']}&travelmode=driving"
                    st.markdown(f"""
                        <a href="{maps_url}" target="_blank" style="font-size: 24px; text-decoration: none; color: #FFD700; display: block; text-align: center;" title="{_['drive_to']}">
                            🚗
                        </a>
                    """, unsafe_allow_html=True)
        else:
            st.info("Venue not registered.")
# =============================================
# 9. 현재 경로 및 총 거리/시간
# =============================================
st.markdown("---")
st.markdown(_["current_route"])
route = [s['city'] for s in st.session_state.tour_stops]
if route:
    display_parts = []
    for j in range(len(route)):
        display_parts.append(route[j])
        if j < len(route) - 1:
            km, hrs = haversine(route[j], route[j + 1])
            display_parts.append(f"({km}km, {hrs}h)")
    st.write(" -> ".join(display_parts))
    total_km = total_hrs = 0
    for j in range(len(route) - 1):
        km, hrs = haversine(route[j], route[j + 1])
        total_km += km
        total_hrs += hrs
    c1, c2 = st.columns(2)
    c1.metric(_["total_distance"], f"{total_km:,} km")
    c2.metric(_["total_time"], f"{total_hrs:.1f} h")
# =============================================
# 10. 지도 (점선 + 목적지 앞 화살표) - 최대 크기 적용
# =============================================
st.markdown("---")
st.subheader(_["tour_map"])
if route:
    center = coords.get(route[0], (19.07, 72.88))
else:
    center = (19.07, 72.88)
 
m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron", width="100%", height="100vh")
if len(route) > 1:
    points = [coords[c] for c in route]
    # 점선으로 경로 표시
    folium.PolyLine(points, color="#8B0000", weight=4, dash_array="10, 10").add_to(m)
 
    # 경로를 따라 화살표 추가
    for j in range(len(points) - 1):
        start = points[j]
        end = points[j + 1]
     
        # 선의 90% 지점에 화살표 위치 계산
        arrow_lat = start[0] + (end[0] - start[0]) * 0.90
        arrow_lon = start[1] + (end[1] - start[1]) * 0.90
     
        # 각도 계산 (y, x) -> atan2(lon_diff, lat_diff)
        angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
     
        folium.RegularPolygonMarker(
            location=[arrow_lat, arrow_lon],
            fill_color='#8B0000', # 짙은 빨간색
            color='#8B0000',
            number_of_sides=3,
            # 화살표가 진행 방향을 향하도록 각도 조정 (-90은 Folium의 기본 방향을 맞추기 위함)
            rotation=angle - 90,
            radius=8
        ).add_to(m)
# 마커 추가
for idx, city in enumerate(route):
    stop = next((s for s in st.session_state.tour_stops if s['city'] == city), None)
    if stop:
        link = stop.get('link', '')
        date_str = stop['date'].strftime(_['date_format'])
        popup = f"<b style='color:#8B0000'>{city}</b><br>{date_str}"
        if link:
            # 길찾기 링크로 변경 (현재 위치 -> 목적지)
            maps_url = f"https://www.google.com/maps/dir/?api=1&destination={link}&travelmode=driving"
            popup = f'{popup}<br><a href="{maps_url}" target="_blank" style="color:#90EE90; text-decoration: none;">🚗 {_["drive_to"]}</a>'
 
    # 시작 도시 마커는 다르게 표시
    marker_color = "#8B0000" if idx == 0 else "#228B22"
 
    folium.CircleMarker(
        coords[city],
        radius=12,
        color=marker_color,
        fill=True,
        fill_color=marker_color,
        fill_opacity=0.8,
        popup=folium.Popup(popup, max_width=300)
    ).add_to(m)
# 지도를 가능한 최대 크기로 표시 (width=None이 컨테이너 전체 너비를 사용)
folium_static(m, height=600, width=1200)
st.caption(_["caption"])
