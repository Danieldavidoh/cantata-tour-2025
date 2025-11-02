import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import math
import random
import urllib.parse # For URL handling if needed

# Top으로 이동
# =============================================
# 1. 다국어 사전 (추가 키들: 하드코딩 메시지 다국어화)
# =============================================
LANG = {
    "en": {
        "title": "Cantata Tour 2025",
        "add_city": "Add City",
        "select_city": "Select City",
        "add_city_btn": "Add City",
        "tour_route": "Tour Route",
        "remove": "Remove",
        "reset_btn": "Reset All",
        "venues_dates": "Tour Route",
        "performance_date": "Performance Date",
        "venue_name": "Venue Name",
        "seats": "Seats",
        "indoor_outdoor": "Indoor/Outdoor",
        "indoor": "Indoor",
        "outdoor": "Outdoor",
        "google_link": "Google Maps Link",
        "special_notes": "Special Notes",
        "register": "Register",
        "add_venue": "Add Venue",
        "edit": "Edit",
        "open_maps": "Open in Google Maps",
        "navigate": "Navigate",
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
        # 추가 키들
        "date_changed": "Date changed",
        "venue_registered": "Venue registered successfully",
        "venue_deleted": "Venue deleted successfully",
        "venue_updated": "Venue updated successfully",
        "enter_venue_name": "Please enter a venue name",
        "edit_venue_label": "Venue Name",
        "edit_seats_label": "Seats",
        "edit_type_label": "Type",
        "edit_google_label": "Google Maps Link",
        "edit_notes_label": "Special Notes",
        "venue_count": "venues", # 1 venue, 2 venues
    },
    "ko": {
        "title": "칸타타 투어 2025",
        "add_city": "도시 추가",
        "select_city": "도시 선택",
        "add_city_btn": "도시 추가",
        "tour_route": "투어 경로",
        "remove": "삭제",
        "reset_btn": "전체 초기화",
        "venues_dates": "투어 경로",
        "performance_date": "공연 날짜",
        "venue_name": "공연장 이름",
        "seats": "좌석 수",
        "indoor_outdoor": "실내/실외",
        "indoor": "실내",
        "outdoor": "실외",
        "google_link": "구글 지도 링크",
        "special_notes": "특이사항",
        "register": "등록",
        "add_venue": "공연장 추가",
        "edit": "편집",
        "open_maps": "구글 지도 열기",
        "navigate": "길찾기",
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
        # 추가 키들
        "date_changed": "날짜 변경됨",
        "venue_registered": "등록 완료",
        "venue_deleted": "삭제 완료",
        "venue_updated": "수정 완료",
        "enter_venue_name": "공연장 이름을 입력하세요.",
        "edit_venue_label": "공연장 이름",
        "edit_seats_label": "좌석 수",
        "edit_type_label": "유형",
        "edit_google_label": "구글 지도 링크",
        "edit_notes_label": "특이사항",
        "venue_count": "개 공연장",
    },
    "hi": {
        "title": "कांताता टूर 2025",
        "add_city": "शहर जोड़ें",
        "select_city": "शहर चुनें",
        "add_city_btn": "शहर जोड़ें",
        "tour_route": "टूर मार्ग",
        "remove": "हटाएं",
        "reset_btn": "सब रीसेट करें",
        "venues_dates": "टूर मार्ग",
        "performance_date": "प्रदर्शन तिथि",
        "venue_name": "स्थल का नाम",
        "seats": "सीटें",
        "indoor_outdoor": "इंडोर/आउटडोर",
        "indoor": "इंडोर",
        "outdoor": "आउटडोर",
        "google_link": "गूगल मैप्स लिंक",
        "special_notes": "विशेष टिप्पणियाँ",
        "register": "रजिस्टर",
        "add_venue": "स्थल जोड़ें",
        "edit": "संपादित करें",
        "open_maps": "गूगल मैप्स में खोलें",
        "navigate": "नेविगेट करें",
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
        # 추가 키들
        "date_changed": "तिथि बदली गई",
        "venue_registered": "पंजीकरण सफल",
        "venue_deleted": "स्थल हटा दिया गया",
        "venue_updated": "स्थल अपडेट किया गया",
        "enter_venue_name": "कृपया स्थल का नाम दर्ज करें",
        "edit_venue_label": "स्थल का नाम",
        "edit_seats_label": "सीटें",
        "edit_type_label": "प्रकार",
        "edit_google_label": "गूगल मैप्स लिंक",
        "edit_notes_label": "विशेष टिप्पणियाँ",
        "venue_count": "स्थल",
    },
}

# =============================================
# 2. 페이지 설정 (맨 위로 이동!)
# =============================================
st.set_page_config(page_title="Cantata Tour 2025", layout="wide", initial_sidebar_state="collapsed")

# =============================================
# 3. 크리스마스 테마 CSS + 장식 (전체 UI에 고르게 배치)
# =============================================
st.markdown("""
<style>
    .reportview-container {
        background: linear-gradient(to bottom, #0f0c29, #302b63, #24243e);
        overflow: hidden;
        position: relative;
    }
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
    .stExpander>summary { color: #90EE90; font-weight: bold; font-size: 1.5em !important; } /* expander 헤더 글씨 크기 증가 */
    .stExpander>div>div>label { font-size: 1.2em !important; } /* 내부 레이블 크기 증가 */
    .stMarkdown { color: #90EE90; }
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
    .city-link { color: #90EE90; text-decoration: underline; cursor: pointer; font-size: 1.3em !important; }
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
snowflakes = ""
for i in range(80):
    left = random.randint(0, 100)
    size = random.choice(["0.8em", "1em", "1.2em", "1.4em"])
    duration = random.uniform(8, 20)
    delay = random.uniform(0, 5)
    snowflakes += f'<div class="snowflake" style="left:{left}%;font-size:{size};animation-duration:{duration}s;animation-delay:{delay}s;">❄️</div>'
st.markdown(snowflakes, unsafe_allow_html=True)

# =============================================
# 4. 사이드바
# =============================================
with st.sidebar:
    st.markdown("### Language")
    lang = st.radio(
        label="Select",
        options=["en", "ko", "hi"],
        format_func=lambda x: {"en": "English", "ko": "한국어", "hi": "हिन्दी"}[x]
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
            # 특정 키만 삭제 (안전하게)
            for key in ['route', 'dates', 'venues', 'admin_venues']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# =============================================
# 5. 세션 초기화 (venues/admin_venues에 columns 있는 빈 DF로)
# =============================================
if 'route' not in st.session_state:
    st.session_state.route = []
if 'dates' not in st.session_state:
    st.session_state.dates = {}
# 'venues'와 'admin_venues'를 빈 DF를 담을 딕셔너리로 초기화
df_cols = ['Venue', 'Seats', 'IndoorOutdoor', 'Google Maps Link', 'Special Notes']
if 'venues' not in st.session_state:
    st.session_state.venues = {}
if 'admin_venues' not in st.session_state:
    st.session_state.admin_venues = {}
if 'active_expander' not in st.session_state:
    st.session_state.active_expander = None

# =============================================
# 6. 도시 목록 및 좌표
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
# 7. 제목 (원본 스타일: 한국어일 때 메인/연도 분리 + 모바일 줄바꿈)
# =============================================
title_text = _['title']
if lang == 'ko':
    # 한국어: "칸타타"와 "투어 2025"를 분리하고, CSS를 사용하여 모바일에서 줄바꿈
    parts = title_text.split()
    main_part = parts[0] if parts else title_text
    rest_part = " ".join(parts[1:]) if len(parts) > 1 else ""
    # mobile-break 클래스를 통해 작은 화면에서 줄바꿈 허용
    title_html = f'<span class="main">{main_part}</span><span class="mobile-break"></span> <span class="year">{rest_part}</span>'
else:
    # 기타 언어: 기존 로직 사용 (마지막 단어를 연도로 간주)
    title_parts = title_text.rsplit(' ', 1)
    main_title = title_parts[0]
    year = title_parts[1] if len(title_parts) > 1 else ""
    title_html = f'<span class="main">{main_title}</span> <span class="year">{year}</span>'

st.markdown(f'<h1 class="christmas-title">{title_html}</h1>', unsafe_allow_html=True)

# =============================================
# 8. 도시 추가 및 투어 경로 (왼쪽 컬럼)
# =============================================
left_col, right_col = st.columns([1, 3])
with left_col:
    available = [c for c in cities if c not in st.session_state.route]
    if available:
        select_col, btn_col = st.columns([2, 1])
        with select_col:
            next_city = st.selectbox(_["select_city"], available, key="next_city_select")
        with btn_col:
            if st.button(_["add_city_btn"], key="add_city_btn"):
                st.session_state.route.append(next_city)
                # 날짜 초기화 (오늘 날짜)
                st.session_state.dates[next_city] = datetime.now().date()
                st.rerun()

    st.markdown("---")
    if st.session_state.route:
        st.subheader(_["venues_dates"])

        for city in st.session_state.route:
            target = st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
            
            # 해당 도시에 등록된 DataFrame이 있고 비어있지 않은지 확인
            current_df = target.get(city, pd.DataFrame(columns=df_cols))
            has_venues = not current_df.empty
            
            date_obj = st.session_state.dates.get(city, datetime.now().date())
            date_str = date_obj.strftime(_['date_format'])
            
            # 닫힌 Expander 라벨 구성
            icon_part = ''
            venue_summary = ''
            if has_venues:
                # 첫 번째 venue의 구글 맵 링크를 가져옴
                first_link = current_df.iloc[0]['Google Maps Link']
                venue_summary = f"({len(current_df)} {_['venue_count']})"
                if first_link and first_link.startswith('http'):
                    # 길찾기 URL 생성 (자동차 아이콘)
                    nav_url = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(first_link)}&travelmode=driving"
                    # 닫힌 박스 오른쪽에 표시될 아이콘. Markdown link로 처리
                    icon_part = f' [🚗]({nav_url})'

            expander_label = f"**{city}** - {date_str} {venue_summary} {icon_part}"
            
            # Expander 시작
            with st.expander(expander_label, expanded=False):
                
                # 1. 공연 날짜 입력 (상시 노출)
                st.markdown("#### " + _["performance_date"])
                col_date, _ = st.columns([1, 4])
                with col_date:
                    new_date = st.date_input(_["performance_date"], date_obj, key=f"date_{city}", label_visibility="collapsed")
                if new_date != date_obj:
                    st.session_state.dates[city] = new_date
                    st.success(_["date_changed"])
                    st.rerun()

                st.markdown("---")

                # 2. 공연장 등록/관리 (Admin/Guest 모드일 때만)
                if st.session_state.admin or st.session_state.guest_mode:
                    
                    # --- A. 새 공연장 등록 폼 ---
                    with st.expander(_["add_venue"], expanded=(not has_venues)): # 첫 등록 시 자동 펼침
                        with st.form(key=f"add_venue_form_{city}"):
                            
                            # 공연장 이름 / 좌석 수
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                venue_name = st.text_input(_["venue_name"], key=f"v_add_{city}")
                            with col2:
                                # 좌석 수: 1 이상의 정수
                                seats = st.number_input(_["seats"], 1, value=1000, step=50, key=f"s_add_{city}")

                            # 구글 지도 링크 / 실내외 토글
                            col3, col4 = st.columns([3, 1])
                            with col3:
                                google_link = st.text_input(_["google_link"], placeholder="https://www.google.com/maps/place/...", key=f"l_add_{city}")
                            with col4:
                                io_key = f"io_add_{city}"
                                if io_key not in st.session_state:
                                    st.session_state[io_key] = _["outdoor"]
                                # 실내/실외 토글 버튼
                                if st.button(_["indoor_outdoor"], key=f"io_toggle_add_{city}"):
                                    st.session_state[io_key] = _["indoor"] if st.session_state[io_key] == _["outdoor"] else _["outdoor"]
                                    st.rerun()
                                st.markdown(f"**{st.session_state[io_key]}**")
                            
                            # 특이사항
                            special_notes = st.text_area(_["special_notes"], key=f"sn_add_{city}")
                            
                            # 등록 버튼
                            if st.form_submit_button(_['register']):
                                if venue_name:
                                    new_row = pd.DataFrame([{
                                        'Venue': venue_name,
                                        'Seats': seats,
                                        'IndoorOutdoor': st.session_state[io_key],
                                        'Google Maps Link': google_link,
                                        'Special Notes': special_notes
                                    }])
                                    
                                    # DataFrame이 없으면 새로 만들고, 있으면 추가
                                    if city not in target or target[city].empty:
                                        target[city] = new_row
                                    else:
                                        target[city] = pd.concat([target[city], new_row], ignore_index=True)
                                    
                                    st.success(_["venue_registered"])
                                    st.rerun()
                                else:
                                    st.error(_["enter_venue_name"])
                    
                    # --- B. 기존 공연장 목록 및 편집/삭제 ---
                    if has_venues:
                        st.markdown("#### Registered Venues")
                        
                        for idx, row in current_df.iterrows():
                            st.markdown("---")
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.write(f"**{row['Venue']}**")
                                st.caption(f"{row['Seats']} {_['seats']} | Notes: {row.get('Special Notes','')}")
                            with col2:
                                color = "🟢" if row['IndoorOutdoor'] == _["indoor"] else "🔵"
                                st.write(f"{color} {row['IndoorOutdoor']}")
                            with col3:
                                # 편집/삭제 버튼은 콤팩트하게 배치
                                edit_col, del_col = st.columns(2)
                                with edit_col:
                                    if st.button("✏️", help=_["edit_venue"], key=f"edit_btn_{city}_{idx}"):
                                        st.session_state[f"edit_mode_{city}_{idx}"] = True
                                with del_col:
                                    if st.button("🗑️", help=_["delete_venue"], key=f"del_btn_{city}_{idx}"):
                                        # 삭제 확인
                                        if st.session_state.get(f"confirm_del_{city}_{idx}", False) or st.checkbox(_["confirm_delete"], key=f"confirm_del_{city}_{idx}"):
                                            target[city] = target[city].drop(idx).reset_index(drop=True)
                                            if target[city].empty:
                                                del target[city] # 빈 경우 딕셔너리 키 삭제
                                            st.success(_["venue_deleted"])
                                            st.rerun()

                            # 편집 폼 (버튼 클릭 시 활성화)
                            if st.session_state.get(f"edit_mode_{city}_{idx}", False):
                                with st.form(key=f"edit_form_{city}_{idx}"):
                                    st.markdown("##### " + _["edit_venue"])
                                    ev = st.text_input(_["edit_venue_label"], row['Venue'], key=f"ev_{city}_{idx}")
                                    es = st.number_input(_["edit_seats_label"], 1, value=row['Seats'], step=50, key=f"es_{city}_{idx}")
                                    eio = st.selectbox(_["edit_type_label"], [_["indoor"], _["outdoor"]], index=0 if row['IndoorOutdoor'] == _["indoor"] else 1, key=f"eio_{city}_{idx}")
                                    el = st.text_input(_["edit_google_label"], row['Google Maps Link'], key=f"el_{city}_{idx}")
                                    esn = st.text_area(_["edit_notes_label"], row.get('Special Notes',''), key=f"esn_{city}_{idx}")
                                    
                                    if st.form_submit_button(_["save"]):
                                        target[city].loc[idx] = [ev, es, eio, el, esn]
                                        del st.session_state[f"edit_mode_{city}_{idx}"]
                                        st.success(_["venue_updated"])
                                        st.rerun()


# =============================================
# 9. 지도 (점선 + 목적지 앞 화살표, TBD strftime 에러 수정)
# =============================================
with right_col: # 오른쪽에 나머지 UI 배치
    st.markdown("---")
    st.subheader(_["tour_map"])
    center = coords.get(st.session_state.route[0] if st.session_state.route else 'Mumbai', (19.75, 75.71))
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")
    
    # 경로 선 및 화살표 추가
    if len(st.session_state.route) > 1:
        points = [coords[c] for c in st.session_state.route]
        folium.PolyLine(points, color="red", weight=4, dash_array="10, 10").add_to(m)
        for i in range(len(points) - 1):
            start = points[i]
            end = points[i + 1]
            arrow_lat = end[0] - (end[0] - start[0]) * 0.05
            arrow_lon = end[1] - (end[1] - start[1]) * 0.05
            folium.RegularPolygonMarker(
                location=[arrow_lat, arrow_lon],
                fill_color='red',
                number_of_sides=3,
                rotation=math.degrees(math.atan2(end[1] - start[1], end[0] - start[0])) - 90,
                radius=10
            ).add_to(m)
    
    # 마커 추가
    for city in st.session_state.route:
        target = st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
        df = target.get(city, pd.DataFrame(columns=df_cols))
        
        link = next((r['Google Maps Link'] for _, r in df.iterrows() if r['Google Maps Link'].startswith('http')), None)
        date_obj = st.session_state.dates.get(city)
        date_str = date_obj.strftime(_['date_format']) if date_obj else 'TBD' 
        
        popup = f"<b style='color:#8B0000'>{city}</b><br>{date_str}"
        
        if link:
            # 팝업에 길찾기 링크 추가
            nav_url = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(link)}&travelmode=driving"
            popup = f'<a href="{nav_url}" target="_blank" style="color:#90EE90; text-decoration: none;">{popup}<br><i>🚗 {_["navigate"]}</i></a>'
        
        folium.CircleMarker(coords[city], radius=15, color="#90EE90", fill_color="#8B0000", popup=folium.Popup(popup, max_width=300)).add_to(m)
    
    st_folium(m, width=700, height=500)
    st.caption(_["caption"])
