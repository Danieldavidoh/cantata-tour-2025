import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
import math

# =============================================
# 1. 다국어 사전 (모든 공백 일반 스페이스)
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
    .reportview-container { 
        background: linear-gradient(to bottom, #0f0c29, #302b63, #24243e); 
        overflow: hidden;
    }
    .sidebar .sidebar-content { background: #228B22; color: white; }
    .Widget>label { color: #90EE90; font-weight: bold; }
    h1, h2, h3 { color: #90EE90; text-shadow: 1px 1px 3px #8B0000; text-align: center; }
    .stButton>button { 
        background: #228B22; color: white; border: 2px solid #8B0000; 
        border-radius: 12px; font-weight: bold; padding: 10px;
    }
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
        vertical=True
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
# 6. UI 시작
# =============================================
st.markdown(f"<h1>{_[ 'title' ]}</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 4])
with col1:
    if st.button(_["start_btn"], use_container_width=True):
        city = st.session_state.start_city
        if city not in st.session_state.route:
            st.session_state.route = [city]
            st.session_state.dates[city] = datetime.now().date()
            st.success(f"{_['start_city']}: {city}")
            st.rerun()
with col2:
    st.session_state.start_city = st.selectbox(_["start_city"], cities, index=cities.index(st.session_state.start_city) if st.session_state.start_city in cities else 0)

# =============================================
# 7. 경로 관리
# =============================================
if st.session_state.route:
    st.markdown("---")
    available = [c for c in cities if c not in st.session_state.route]
    if available:
        col_add, col_next = st.columns([1, 4])
        with col_add:
            if st.button(_["add_btn"], use_container_width=True):
                new_city = st.session_state.get('next_city_select', available[0])
                st.session_state.route.append(new_city)
                if len(st.session_state.route) > 1:
                    prev = st.session_state.route[-2]
                    lat1, lon1 = coords[prev]
                    lat2, lon2 = coords[new_city]
                    R = 6371
                    dlat = math.radians(lat2 - lat1)
                    dlon = math.radians(lon2 - lon1)
                    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    km = round(R * c)
                    hrs = round(km / 50, 1)
                    st.session_state.distances.setdefault(prev, {})[new_city] = (km, hrs)
                    st.session_state.distances.setdefault(new_city, {})[prev] = (km, hrs)
                    prev_date = st.session_state.dates.get(prev, datetime.now().date())
                    st.session_state.dates[new_city] = (datetime.combine(prev_date, datetime.min.time()) + timedelta(hours=hrs)).date()
                st.success(f"{new_city} 추가됨")
                st.rerun()
        with col_next:
            select_key = f"next_city_{'_'.join(st.session_state.route)}"
            st.session_state.next_city_select = st.selectbox(_["next_city"], available, key=select_key)

    st.markdown(_["current_route"])
    route_display = []
    for i, city in enumerate(st.session_state.route):
        route_display.append(city)
        if i < len(st.session_state.route) - 1:
            next_city = st.session_state.route[i+1]
            km, hrs = st.session_state.distances.get(city, {}).get(next_city, (0, 0))
            route_display.append(f"({km}km, {hrs}h)")
    st.write(" -> ".join(route_display))

    total_km = total_hrs = 0
    for i in range(len(st.session_state.route)-1):
        a, b = st.session_state.route[i], st.session_state.route[i+1]
        km, hrs = st.session_state.distances.get(a, {}).get(b, (100, 2.0))
        total_km += km
        total_hrs += hrs
    c1, c2 = st.columns(2)
    c1.metric(_["total_distance"], f"{total_km:,} km")
    c2.metric(_["total_time"], f"{total_hrs:.1f} h")

    # =============================================
    # 8. 공연장 관리
    # =============================================
    st.markdown("---")
    st.subheader(_["venues_dates"])

    for city in st.session_state.route:
        with st.expander(f"**{city}**", expanded=True):
            cur = st.session_state.dates.get(city, datetime.now().date())
            new = st.date_input(_["performance_date"], cur, key=f"date_{city}")
            if new != cur:
                st.session_state.dates[city] = new
                st.success("날짜 변경됨")
                st.rerun()

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

            if st.session_state.admin or st.session_state.guest_mode:
                st.markdown("---")
                io = st.session_state.get(f"io_{city}", _["outdoor"])
                if st.button(f"**{io}**", key=f"io_toggle_{city}"):
                    io = _["indoor"] if io == _["outdoor"] else _["outdoor"]
                    st.session_state[f"io_{city}"] = io
                    st.rerun()
                border_color = "#90EE90" if io == _["indoor"] else "#87CEEB"
                st.markdown(f"<div style='border:3px solid {border_color}; border-radius:12px; padding:8px; text-align:center; font-weight:bold; background:white;'>{io}</div>", unsafe_allow_html=True)

                with st.form(key=f"add_{city}"):
                    c1, c2 = st.columns([3, 1])
                    with c1: v = st.text_input(_["venue_name"], key=f"v_{city}")
                    with c2: s = st.number_input(_["seats"], 1, step=50, key=f"s_{city}")
                    l = st.text_input(_["google_link"], placeholder="https://...", key=f"l_{city}")
                    if st.form_submit_button(_["register"]) and v:
                        new_row = pd.DataFrame([{'Venue': v, 'Seats': s, 'IndoorOutdoor': io, 'Google Maps Link': l}])
                        target = st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
                        target[city] = pd.concat([target.get(city, pd.DataFrame()), new_row], ignore_index=True)
                        st.success("등록 완료")
                        st.rerun()

# =============================================
# 9. 지도 (루트 빨간색)
# =============================================
st.markdown("---")
st.subheader(_["tour_map"])
center = coords.get(st.session_state.route[0] if st.session_state.route else 'Mumbai', (19.75, 75.71))
m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")
if len(st.session_state.route) > 1:
    folium.PolyLine([coords[c] for c in st.session_state.route], color="red", weight=4).add_to(m)
for city in st.session_state.route:
    df = st.session_state.admin_venues.get(city, pd.DataFrame()) if st.session_state.admin else st.session_state.venues.get(city, pd.DataFrame())
    link = next((r['Google Maps Link'] for _, r in df.iterrows() if r['Google Maps Link'].startswith('http')), None)
    popup = f"<b style='color:#8B0000'>{city}</b><br>{st.session_state.dates.get(city, 'TBD').strftime(_['date_format'])}"
    if link:
        popup = f'<a href="{link}" target="_blank" style="color:#90EE90">{popup}<br><i>{_["open_maps"]}</i></a>'
    folium.CircleMarker(coords[city], radius=15, color="#90EE90", fill_color="#8B0000", popup=folium.Popup(popup, max_width=300)).add_to(m)
folium_static(m, width=700, height=500)
st.caption(_["caption"])
