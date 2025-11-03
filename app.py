import streamlit as st
import pandas as pd
from datetime import datetime, date
import folium
from streamlit_folium import st_folium  # ← import는 밑줄 (_) – 맞음!
import random
from geopy.distance import great_circle

# 1. 다국어 사전
LANG = {
    "en": {
        "title": "Cantata Tour 2025", "add_city": "Add City", "select_city": "Select City",
        "add_venue_btn": "Add Venue", "tour_route": "Tour Route", "remove": "Remove",
        "reset_btn": "Reset All", "performance_date": "Performance Date",
        "venue_name": "Venue Name", "seats": "Seats", "indoor_outdoor": "Indoor/Outdoor",
        "indoor": "Indoor", "outdoor": "Outdoor", "google_link": "Google Maps Link",
        "special_notes": "Special Notes", "register": "Register", "save": "Save",
        "tour_map": "Tour Map", "admin_mode": "Admin Mode", "guest_mode": "Guest Mode",
        "enter_password": "Enter password to access Admin Mode", "submit": "Submit",
        "drive_to": "Drive Here", "distance": "Distance (km)", "time": "Time (min)",
        "no_performance": "No Performance", "today_performance": "Today's Performance!",
        "past_performance": "Past Performance", "total_distance": "Total Distance",
        "total_time": "Total Time", "add_city_to_route": "Add City to Route",
        "city_placeholder": "Select City (Maharashtra)", "admin_input_mode": "Admin Input Mode",
        "guest_view_mode": "Guest View Mode", "confirm_delete": "Are you sure you want to delete?",
        "enter_venue_name": "Please enter a venue name", "date_changed": "Date changed",
        "venue_registered": "Venue registered successfully", "venue_deleted": "Venue deleted successfully",
        "date_format": "%Y-%m-%d", "venues": "Venues", "caption": "Red dotted line: Tour route | Red circle: Today | Gray: Past"
    },
    "ko": {
        "title": "칸타타 투어 2025", "add_city": "도시 추가", "select_city": "도시 선택",
        "add_venue_btn": "공연장 등록", "tour_route": "투어 경로", "remove": "삭제",
        "reset_btn": "전체 초기화", "performance_date": "공연 날짜",
        "venue_name": "공연장 이름", "seats": "좌석 수", "indoor_outdoor": "실내/실외",
        "indoor": "실내", "outdoor": "실외", "google_link": "구글 지도 링크",
        "special_notes": "특이사항", "register": "등록", "save": "저장",
        "tour_map": "투어 지도", "admin_mode": "관리자 모드", "guest_mode": "손님 모드",
        "enter_password": "관리자 모드 접근을 위한 비밀번호 입력", "submit": "제출",
        "drive_to": "길찾기", "distance": "거리 (km)", "time": "소요시간 (분)",
        "no_performance": "공연 없음", "today_performance": "오늘의 공연!",
        "past_performance": "지난 공연", "total_distance": "총 거리",
        "total_time": "총 소요시간", "add_city_to_route": "경로에 도시 추가",
        "city_placeholder": "도시 선택 (마하라스트라)", "admin_input_mode": "관리자 입력 모드",
        "guest_view_mode": "손님 보기 모드", "confirm_delete": "정말 삭제하시겠습니까?",
        "enter_venue_name": "공연장 이름을 입력하세요.", "date_changed": "날짜 변경됨",
        "venue_registered": "등록 완료", "venue_deleted": "삭제 완료",
        "date_format": "%Y년 %m월 %d일", "venues": "공연장", "caption": "빨간 점선: 투어 경로 | 빨간 원: 오늘 | 회색: 과거"
    },
    "hi": {
        "title": "कांताता टूर 2025", "add_city": "शहर जोड़ें", "select_city": "शहर चुनें",
        "add_venue_btn": "स्थल जोड़ें", "tour_route": "टूर मार्ग", "remove": "हटाएं",
        "reset_btn": "सब रीसेट करें", "performance_date": "प्रदर्शन तिथि",
        "venue_name": "स्थल का नाम", "seats": "सीटें", "indoor_outdoor": "इंडोर/आउटडोर",
        "indoor": "इंडोर", "outdoor": "आउटडोर", "google_link": "गूगल मैप्स लिंक",
        "special_notes": "विशेष टिप्पणियाँ", "register": "रजिस्टर", "save": "सहेजें",
        "tour_map": "टूर मैप", "admin_mode": "एडमिन मोड", "guest_mode": "गेस्ट मोड",
        "enter_password": "एडमिन मोड एक्सेस करने के लिए पासवर्ड दर्ज करें", "submit": "जमा करें",
        "drive_to": "यहाँ ड्राइव करें", "distance": "दूरी (किमी)", "time": "समय (मिनट)",
        "no_performance": "कोई प्रदर्शन नहीं", "today_performance": "आज का प्रदर्शन!",
        "past_performance": "पिछला प्रदर्शन", "total_distance": "कुल दूरी",
        "total_time": "कुल समय", "add_city_to_route": "मार्ग में शहर जोड़ें",
        "city_placeholder": "शहर चुनें (महाराष्ट्र)", "admin_input_mode": "एडमिन इनपुट मोड",
        "guest_view_mode": "गेस्ट व्यू मोड", "confirm_delete": "क्या आप वाकई हटाना चाहते हैं?",
        "enter_venue_name": "कृपया स्थल का नाम दर्ज करें", "date_changed": "तिथि बदली गई",
        "venue_registered": "पंजीकरण सफल", "venue_deleted": "स्थल हटा दिया गया",
        "date_format": "%d-%m-%Y", "venues": "स्थल", "caption": "लाल बिंदीदार रेखा: टूर मार्ग | लाल गोला: आज | ग्रे: अतीत"
    },
}

# 2. 페이지 설정 + 크리스마스 테마 CSS
st.set_page_config(page_title="Cantata Tour 2025", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .reportview-container {background:linear-gradient(to bottom,#0f0c29,#302b63,#24243e); color:#90EE90;}
    .stApp {background:transparent;}
    .stSidebar {background:#1e4d2b; color:white;}
    .Widget>label {color:#90EE90; font-weight:bold;}
    .stButton>button {background:#8B0000; color:white; border:2px solid #FFD700; border-radius:12px; font-weight:bold;}
    .stButton>button:hover {background:#FF0000;}
    .christmas-title {font-size:3.5em!important; font-weight:bold; text-align:center; text-shadow:0 0 5px #FFF,0 0 10px #FFF,0 0 15px #FFF,0 0 20px #8B0000;}
    .christmas-title .main {color:#FF0000!important;}
    .christmas-title .year {color:white!important; text-shadow:0 0 5px #FFF,0 0 10px #FFD700;}
    .stExpander {background:rgba(255,255,255,0.1); border:1px solid #90EE90; border-radius:12px;}
    .stExpander>summary {color:#FFD700; font-weight:bold; font-size:1.5em!important;}
    .route-item {background:rgba(255,255,255,0.05); border:1px solid #3CB371; padding:8px; border-radius:8px; margin-bottom:5px; color:#90EE90;}
    .route-item:hover {background:rgba(255,255,255,0.1);}
    .past-perf {background-color: rgba(0, 0, 0, 0.5) !important; color: #808080 !important;}
    .christmas-decoration {position:fixed; font-size:2.5em; pointer-events:none; animation:float 6s infinite ease-in-out; z-index:10;}
    .snowflake {position:fixed; color:rgba(255,255,255,0.9); font-size:1.2em; pointer-events:none; animation:fall linear infinite; opacity:0.9; z-index:10;}
    @keyframes float {0%,100%{transform:translateY(0) rotate(0deg);}50%{transform:translateY(-20px) rotate(5deg);}}
    @keyframes fall {0%{transform:translateY(-10vh) rotate(0deg); opacity:0.9;}100%{transform:translateY(100vh) rotate(360deg); opacity:0;}}
</style>
""", unsafe_allow_html=True)

# 크리스마스 장식 + 눈 효과
deco = """<div class="christmas-decoration" style="top:10%;left:1%;">🎁</div><div class="christmas-decoration" style="top:5%;right:1%;">🍭</div>"""
st.markdown(deco, unsafe_allow_html=True)
snow = "".join(f'<div class="snowflake" style="left:{random.randint(0,100)}%; animation-duration:{random.uniform(8,20):.1f}s; animation-delay:{random.uniform(0,5):.1f}s;">❄️</div>' for _ in range(80))
st.markdown(snow, unsafe_allow_html=True)

# 3. 세션 상태 초기화
for k, v in {"lang": "ko", "admin": False, "show_pw": False, "guest_mode": True, "route": [], "dates": {}, "venues": {}, "admin_venues": {}}.items():
    st.session_state.setdefault(k, v)

# 4. 도시 좌표 (완전 포함)
coords = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
    "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Amravati": (20.93, 77.75),
    "Nanded": (19.16, 77.31), "Kolhapur": (16.70, 74.24), "Akola": (20.70, 77.00), "Latur": (18.40, 76.18),
    "Ahmadnagar": (19.10, 74.75), "Jalgaon": (21.00, 75.57), "Dhule": (20.90, 74.77), "Ichalkaranji": (16.69, 74.47),
    "Malegaon": (20.55, 74.53), "Bhusawal": (21.05, 76.00), "Bhiwandi": (19.30, 73.06), "Bhandara": (21.17, 79.65),
    "Beed": (18.99, 75.76), "Buldana": (20.54, 76.18), "Chandrapur": (19.95, 79.30), "Dharashiv": (18.40, 76.57),
    "Gondia": (21.46, 80.19), "Hingoli": (19.72, 77.15), "Jalna": (19.85, 75.89), "Mira-Bhayandar": (19.28, 72.87),
    "Nandurbar": (21.37, 74.22), "Osmanabad": (18.18, 76.07), "Palghar": (19.70, 72.77), "Parbhani": (19.27, 76.77),
    "Ratnagiri": (16.99, 73.31), "Sangli": (16.85, 74.57), "Satara": (17.68, 74.02), "Sindhudurg": (16.24, 73.42),
    "Wardha": (20.75, 78.60), "Washim": (20.11, 77.13), "Yavatmal": (20.39, 78.12), "Kalyan-Dombivli": (19.24, 73.13),
    "Ulhasnagar": (19.22, 73.16), "Vasai-Virar": (19.37, 72.81), "Sangli-Miraj-Kupwad": (16.85, 74.57), "Nanded-Waghala": (19.16, 77.31),
    "Bandra (Mumbai)": (19.06, 72.84), "Colaba (Mumbai)": (18.92, 72.82), "Andheri (Mumbai)": (19.12, 72.84),
    "Navi Mumbai": (19.03, 73.00), "Pimpri-Chinchwad (Pune)": (18.62, 73.80), "Kothrud (Pune)": (18.50, 73.81), "Hadapsar (Pune)": (18.51, 73.94),
    "Pune Cantonment": (18.50, 73.89), "Nashik Road": (20.00, 73.79), "Deolali (Nashik)": (19.94, 73.82), "Satpur (Nashik)": (20.01, 73.79),
    "Aurangabad City": (19.88, 75.34), "Jalgaon City": (21.00, 75.57), "Nagpur City": (21.15, 79.08), "Sitabuldi (Nagpur)": (21.14, 79.08),
    "Jaripatka (Nagpur)": (21.12, 79.07), "Solapur City": (17.67, 75.91), "Pandharpur (Solapur)": (17.66, 75.32), "Amravati City": (20.93, 77.75),
    "Badnera (Amravati)": (20.84, 77.73), "Akola City": (20.70, 77.00), "Washim City": (20.11, 77.13), "Yavatmal City": (20.39, 78.12),
    "Wardha City": (20.75, 78.60), "Chandrapur City": (19.95, 79.30), "Gadchiroli": (20.09, 80.11), "Gondia City": (21.46, 80.19),
    "Bhandara City": (21.17, 79.65), "Gadhinglaj (Kolhapur)": (16.23, 74.34), "Kagal (Kolhapur)": (16.57, 74.31)
}
ALL_CITIES = sorted(coords.keys())

# 5. 헬퍼 함수
def target_df(): return st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
def date_str(city):
    d = st.session_state.dates.get(city)
    return d.strftime(LANG[st.session_state.lang]["date_format"]) if d and isinstance(d, date) else LANG[st.session_state.lang]["no_performance"]
def nav_url(link): return f"https://www.google.com/maps/dir/?api=1&destination={link.split('@')[-1].split('/')[0]}" if link and link.startswith("http") else "#"
def calculate_distance_time(c1, c2):
    if c1 in coords and c2 in coords:
        dist = great_circle(coords[c1], coords[c2]).kilometers
        time_min = round(dist / 60 * 60)
        return f"{dist:.1f} km", f"{time_min} min"
    return "?? km", "?? min"

# 6. 사이드바
with st.sidebar:
    st.session_state.lang = st.radio("Language", ["ko","en","hi"], format_func=lambda x: {"ko":"한국어","en":"English","hi":"हिन्दी"}[x], index=["ko","en","hi"].index(st.session_state.lang))
    _ = LANG[st.session_state.lang]

    if st.session_state.admin:
        st.success(_["admin_input_mode"])
        if st.button(_["guest_mode"]): st.session_state.admin = False; st.session_state.guest_mode = True; st.rerun()
        if st.button(_["reset_btn"]): [st.session_state[k].clear() for k in ["route","dates","venues","admin_venues"]]; st.rerun()
    else:
        if st.button(_["admin_mode"]): st.session_state.show_pw = True; st.rerun()
        if st.session_state.show_pw:
            pw = st.text_input(_["enter_password"], type="password")
            if st.button(_["submit"]):
                if pw == "0691": st.session_state.admin = True; st.session_state.show_pw = False; st.rerun()
                else: st.error("Wrong password")
        if not st.session_state.guest_mode: st.session_state.guest_mode = True

# 7. 제목
title_parts = _["title"].rsplit(" ", 1)
st.markdown(f'<h1 class="christmas-title"><span class="main">{title_parts[0]}</span> <span class="year">{title_parts[1]}</span></h1>', unsafe_allow_html=True)

# 8. 지도 테스트 (정상 동작 확인)
center = coords.get("Mumbai", (19.07, 72.88))
m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")
folium.CircleMarker(location=coords["Mumbai"], radius=15, color="red", fill=True, popup="Mumbai").add_to(m)
folium.CircleMarker(location=coords["Pune"], radius=15, color="green", fill=True, popup="Pune").add_to(m)
st_folium(m, width=700, height=500)

st.success("앱 정상 실행! `streamlit-folium` 설치 완료. 지도 동작 중.")
