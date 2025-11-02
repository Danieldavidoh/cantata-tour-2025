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
    },
}

# =============================================
# 2. 크리스마스 테마 CSS
# =============================================
st.markdown("""
<style>
    .reportview-container { background: linear-gradient(to bottom, #0f0c29, #302b63, #24243e); overflow: hidden; }
    .sidebar .sidebar-content { background: #228B22; color: white; }
    .Widget>label { color: #90EE90; font-weight: bold; }
    
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
    .stButton>button { background: #228B22; color: white; border: 2px solid #8B0000; border-radius: 12px; font-weight: bold; padding: 10px; }
    .stButton>button:hover { background: #8B0000; color: white; }
    .stTextInput>label, .stSelectbox>label, .stNumberInput>label { color: #90EE90; }
    .stMetric { background: rgba(34,139,34,0.3); border: 2px solid #90EE90; border-radius: 12px; padding: 10px; }
    .stExpander { background: rgba(139,0,0,0.4); border: 1px solid #90EE90; border-radius: 12px; }
    .stExpander>summary { color: #90EE90; font-weight: bold; }
    .stMarkdown { color: #90EE90; }

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
</style>
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
    lang = st.radio(
        label="Select",
        options=["en", "ko", "hi"],
        format_func=lambda x: {"en": "English", "ko": "한국어", "hi": "हिन्दी"}[x],
        horizontal=False
    )
    _ = LANG[lang]

    st.markdown("---")
    st.markdown("### Admin")
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
            st.session_state.show_pw = True
            st.rerun()
    else:
        if st.button(_["admin_mode"]):
            st.session_state.show_pw = True
        if st.session_state.show_pw:
            pw = st.text_input(_["enter_password"], type="password")
            if st.button(_["submit"]):
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
                del st.session_state[key]
            st.rerun()

# =============================================
# 4. 세션 초기화
# =============================================
if 'route' not in st.session_state:
    st.session_state.route = []
if 'dates' not in st.session_state:
    st.session_state.dates = {}
if 'distances' not in st.session_state:
    st.session_state.distances = {}
if 'venues' not in st.session_state:
    st.session_state.venues = {}
if
