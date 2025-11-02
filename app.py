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
if 'admin_venues' not in st.session_state:
    st.session_state.admin_venues = {}
if 'start_city' not in st.session_state:
    st.session_state.start_city = 'Mumbai'

# =============================================
# 5. 도시 목록 및 좌표
# =============================================
cities = sorted([...])  # (기존 코드 그대로)
coords = { ... }  # (기존 코드 그대로)

# =============================================
# 6. 제목
# =============================================
title_parts = _['title'].rsplit(' ', 1)
main_title = title_parts[0]
year = title_parts[1] if len(title_parts) > 1 else ""
st.markdown(f'<h1 class="christmas-title"><span class="main">{main_title}</span> <span class="year">{year}</span></h1>', unsafe_allow_html=True)

# =============================================
# 7. UI 시작 ~ 경로 관리 (기존 코드)
# =============================================
# (생략 - 기존 코드 그대로)

# =============================================
# 9. 공연장 & 날짜 (새로운 폼 추가)
# =============================================
st.markdown("---")
st.subheader(_["venues_dates"])

for city in st.session_state.route:
    with st.expander(f"**{city}**", expanded=False):
        # 공연 날짜
        cur = st.session_state.dates.get(city, datetime.now().date())
        new = st.date_input(_["performance_date"], cur, key=f"date_{city}")
        if new != cur:
            st.session_state.dates[city] = new
            st.success("날짜 변경됨")
            st.rerun()

        # 공연장 등록 폼 (항상 보임)
        if st.session_state.admin or st.session_state.guest_mode:
            st.markdown("---")
            col1, col2, col3, col4 = st.columns([3, 1, 3, 1])

            with col1:
                venue_name = st.text_input(_["venue_name"], key=f"v_{city}")
            with col2:
                seats = st.number_input(_["seats"], 1, step=50, key=f"s_{city}")
            with col3:
                google_link = st.text_input(_["google_link"], placeholder="https://...", key=f"l_{city}")
            with col4:
                # 실내/실외 토글 버튼 (기본: 실외)
                io_key = f"io_{city}"
                if io_key not in st.session_state:
                    st.session_state[io_key] = _["outdoor"]
                if st.button(f"**{st.session_state[io_key]}**", key=f"io_toggle_{city}"):
                    st.session_state[io_key] = _["indoor"] if st.session_state[io_key] == _["outdoor"] else _["outdoor"]
                    st.rerun()

            # 등록 버튼 (왼쪽 끝)
            if st.button(f"**{_[\"register\"]}**", key=f"register_{city}", use_container_width=True):
                if venue_name:
                    new_row = pd.DataFrame([{
                        'Venue': venue_name,
                        'Seats': seats,
                        'IndoorOutdoor': st.session_state[io_key],
                        'Google Maps Link': google_link
                    }])
                    target = st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
                    target[city] = pd.concat([target.get(city, pd.DataFrame()), new_row], ignore_index=True)
                    st.success("등록 완료")
                    st.rerun()
                else:
                    st.error("공연장 이름을 입력하세요.")

        # 공연장 목록
        df = st.session_state.admin_venues.get(city, pd.DataFrame()) if st.session_state.admin else st.session_state.venues.get(city, pd.DataFrame(columns=['Venue', 'Seats', 'IndoorOutdoor', 'Google Maps Link']))
        if not df.empty:
            for idx, row in df.iterrows():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**{row['Venue']}**")
                    st.caption(f"{row['Seats']} {_['seats']}")
                with col2:
                    color = "🟢" if row['IndoorOutdoor'] == _["indoor"] else "🔵"
                    st.write(f"{color} {row['IndoorOutdoor']}")
                with col3:
                    if row['Google Maps Link'].startswith("http"):
                        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={row['Google Maps Link']}&travelmode=driving"
                        st.markdown(f"[{_['drive_to']}]({maps_url})", unsafe_allow_html=True)
                with col4:
                    if st.session_state.admin or st.session_state.guest_mode:
                        if st.button(_["edit_venue"], key=f"edit_{city}_{idx}"):
                            st.session_state[f"edit_{city}_{idx}"] = True
                        if st.button(_["delete_venue"], key=f"del_{city}_{idx}"):
                            if st.checkbox(_["confirm_delete"], key=f"confirm_{city}_{idx}"):
                                target = st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
                                target[city] = target[city].drop(idx).reset_index(drop=True)
                                st.success("삭제 완료")
                                st.rerun()

                # 편집 폼
                if st.session_state.get(f"edit_{city}_{idx}", False):
                    with st.form(key=f"edit_form_{city}_{idx}"):
                        ev = st.text_input("Venue", row['Venue'], key=f"ev_{city}_{idx}")
                        es = st.number_input("Seats", 1, value=row['Seats'], key=f"es_{city}_{idx}")
                        eio = st.selectbox("Type", [_[ "indoor" ], _["outdoor"]], index=0 if row['IndoorOutdoor'] == _["indoor"] else 1, key=f"eio_{city}_{idx}")
                        el = st.text_input("Google Link", row['Google Maps Link'], key=f"el_{city}_{idx}")
                        if st.form_submit_button("Save"):
                            target = st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
                            target[city].loc[idx] = [ev, es, eio, el]
                            del st.session_state[f"edit_{city}_{idx}"]
                            st.success("수정 완료")
                            st.rerun()

# =============================================
# 10. 지도 (빨간색 점선 + 화살표)
# =============================================
# (기존 코드 그대로)
