1.9s
cd /mount/src/cantata-tour-2025 && 
cat > app.py << 'EOF'
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
        "title": "🎼 Cantata Tour <span style='font-size:1.1rem; color:#888;'>(Maharashtra)</span>",
        "start_city": "Starting City",
        "start_btn": "🚀 Start",
        "reset_btn": "🔄 Reset All",
        "next_city": "Next City",
        "add_btn": "➕ Add",
        "current_route": "### Current Route",
        "total_distance": "Total Distance",
        "total_time": "Total Time",
        "venues_dates": "Venues & Dates",
        "performance_date": "Performance Date",
        "venue_name": "Venue Name",
        "seats": "Seats",
        "indoor_outdoor": "Indoor/Outdoor",
        "indoor": "Indoor", # 언어 중립적인 키로 사용
        "outdoor": "Outdoor", # 언어 중립적인 키로 사용
        "google_link": "Google Maps Link",
        "register": "Register",
        "add_venue": "Add Venue",
        "edit": "Edit",
        "open_maps": "Open in Google Maps",
        "save": "Save",
        "delete": "Delete",
        "tour_map": "Tour Map",
        "caption": "Mobile: ⋮ → 'Add to Home Screen' → Use like an app!",
        "date_format": "%b %d, %Y",
        "admin_mode": "Admin Mode",
        "enter_password": "Enter password to access Admin Mode",
        "submit": "Submit",
        "io_indoor_display": "Indoor", # 화면 표시에 사용
        "io_outdoor_display": "Outdoor", # 화면 표시에 사용
    },
    "ko": {
        "title": "🎼 칸타타 투어 <span style='font-size:1.1rem; color:#888;'>(마하라슈트라)</span>",
        "start_city": "출발 도시",
        "start_btn": "🚀 시작",
        "reset_btn": "🔄 전체 초기화",
        "next_city": "다음 도시",
        "add_btn": "➕ 추가",
        "current_route": "### 현재 경로",
        "total_distance": "총 거리",
        "total_time": "총 소요시간",
        "venues_dates": "공연장 & 날짜",
        "performance_date": "공연 날짜",
        "venue_name": "공연장 이름",
        "seats": "좌석 수",
        "indoor_outdoor": "실내/실외",
        "indoor": "Indoor", # 언어 중립적인 키로 사용
        "outdoor": "Outdoor", # 언어 중립적인 키로 사용
        "google_link": "구글 지도 링크",
        "register": "등록",
        "add_venue": "공연장 추가",
        "edit": "편집",
        "open_maps": "구글 지도 열기",
        "save": "저장",
        "delete": "삭제",
        "tour_map": "투어 지도",
        "caption": "모바일: ⋮ → '홈 화면에 추가' → 앱처럼 사용!",
        "date_format": "%Y년 %m월 %d일",
        "admin_mode": "관리자 모드",
        "enter_password": "관리자 모드 접근을 위한 비밀번호 입력",
        "submit": "제출",
        "io_indoor_display": "실내", # 화면 표시에 사용
        "io_outdoor_display": "실외", # 화면 표시에 사용
    },
    "hi": {
        "title": "🎼 कांताता टूर <span style='font-size:1.1rem; color:#888;'>(महाराष्ट्र)</span>",
        "start_city": "प्रारंभिक शहर",
        "start_btn": "🚀 शुरू करें",
        "reset_btn": "🔄 सब रीसेट करें",
        "next_city": "अगला शहर",
        "add_btn": "➕ जोड़ें",
        "current_route": "### वर्तमान मार्ग",
        "total_distance": "कुल दूरी",
        "total_time": "कुल समय",
        "venues_dates": "स्थल और तिथियाँ",
        "performance_date": "प्रदर्शन तिथि",
        "venue_name": "स्थल का नाम",
        "seats": "सीटें",
        "indoor_outdoor": "इंडोर/आउटडोर",
        "indoor": "Indoor", # 언어 중립적인 키로 사용
        "outdoor": "Outdoor", # 언어 중립적인 키로 사용
        "google_link": "गूगल मैप्स लिंक",
        "register": "रजिस्टर",
        "add_venue": "स्थल जोड़ें",
        "edit": "संपादित करें",
        "open_maps": "गूगल मैप्स में खोलें",
        "save": "सहेजें",
        "delete": "हटाएँ",
        "tour_map": "टूर मैप",
        "caption": "मोबाइल: ⋮ → 'होम स्क्रीन पर जोड़ें' → ऐप की तरह उपयोग करें!",
        "date_format": "%d %b %Y",
        "admin_mode": "एडमिन मोड",
        "enter_password": "एडमिन मोड एक्सेस करने के लिए पासवर्ड दर्ज करें",
        "submit": "जमा करें",
        "io_indoor_display": "इंडोर", # 화면 표시에 사용
        "io_outdoor_display": "आउटडोर", # 화면 표시에 사용
    },
}

# =============================================

# 2. 페이지 설정 + 사이드바

# =============================================

st.set_page_config(page_title="Cantata Tour", layout="wide", initial_sidebar_state="collapsed")
with st.sidebar:
    st.markdown("### 🌐 Language")
    lang = st.radio("Select", ["en", "ko", "hi"], format_func=lambda x: {"en": "English", "ko": "한국어", "hi": "हिन्दी"}[x], horizontal=True)
    _ = LANG[lang]
    st.markdown("---")
    st.markdown("### 🔒 Admin")
    if 'admin' not in st.session_state:
        st.session_state.admin = False
    if 'show_pw' not in st.session_state:
        st.session_state.show_pw = False
    if st.session_state.admin:
        st.success("Admin Mode Active")
    else:
        if st.button(*["admin_mode"]):
            st.session_state.show_pw = True
        if st.session_state.show_pw:
            pw = st.text_input(*["enter_password"], type="password")
            if st.button(*["submit"]):
                if pw == "0691":
                    st.session_state.admin = True
                    st.session_state.show_pw = False
                    st.success("Activated!")
                    st.rerun()
                else:
                    st.error("Incorrect")
    st.markdown("---")
    if st.button(*["reset_btn"]):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# =============================================

# 3. 세션 초기화

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
if 'edit_modes' not in st.session_state:
    st.session_state.edit_modes = {}
if 'add_modes' not in st.session_state:
    st.session_state.add_modes = {}
if 'next_city_select' not in st.session_state:
    st.session_state.next_city_select = None

# 도시 목록 및 좌표

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

# 5. UI 시작

# =============================================

st.markdown(f"<h1 style='margin:0; padding:0; font-size:2.2rem;'>{*['title']}</h1>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 4])
with col1:
    if st.button(*["start_btn"], use_container_width=True):
        city = st.session_state.start_city
        if city not in st.session_state.route:
            st.session_state.route = [city]
            st.session_state.dates[city] = datetime.now().date()
            st.success(f"{*['start_city']}: {city}")
            st.rerun()
with col2:
    st.session_state.start_city = st.selectbox(*["start_city"], cities, index=cities.index(st.session_state.start_city) if st.session_state.start_city in cities else 0)

# =============================================

# 6. 경로 관리

# =============================================

if st.session_state.route:
    st.markdown("---")
    available = [c for c in cities if c not in st.session_state.route]
    if available:
        col_add, col_next = st.columns([1, 4])
        with col_add:
            if st.button(*["add_btn"], use_container_width=True):
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
                    # 최소 하루가 지나도록 조정
                    st.session_state.dates[new_city] = (datetime.combine(prev_date, datetime.min.time()) + timedelta(hours=hrs, days=1)).date()
                st.success(f"{new_city} {*['add_btn'].replace('➕ ', '')}")
                st.rerun()
        with col_next:
            st.selectbox(*["next_city"], available, key='next_city_select')
    st.markdown(*["current_route"])
    st.write(" → ".join(st.session_state.route))
    total_km = total_hrs = 0
    for i in range(len(st.session_state.route)-1):
        a, b = st.session_state.route[i], st.session_state.route[i+1]
        km, hrs = st.session_state.distances.get(a, {}).get(b, (100, 2.0))
        total_km += km
        total_hrs += hrs
    c1, c2 = st.columns(2)
    c1.metric(*["total_distance"], f"{total_km:,} km")
    c2.metric(*["total_time"], f"{total_hrs:.1f} h")
    # =============================================
    # 7. 공연장 관리
    # =============================================
    st.markdown("---")
    st.subheader(*["venues_dates"])
   
    # 헬퍼 함수: 언어 중립적인 키를 현재 언어의 표시 문자열로 변환
    def get_io_display(io_key, *):
        if io_key == 'Indoor':
            return *['io_indoor_display']
        elif io_key == 'Outdoor':
            return *['io_outdoor_display']
        return io_key
    for city in st.session_state.route:
        with st.expander(city, expanded=False):
            cur = st.session_state.dates.get(city, datetime.now().date())
            new = st.date_input(*["performance_date"], cur, key=f"date*{city}")
            if new != cur:
                st.session_state.dates[city] = new
                st.success(f"{*['performance_date']} {*['save']}")
                st.rerun()
            df = st.session_state.admin_venues.get(city, pd.DataFrame()) if st.session_state.admin else st.session_state.venues.get(city, pd.DataFrame(columns=['Venue', 'Seats', 'IndoorOutdoor', 'Google Maps Link']))
            if not df.empty:
                for idx, row in df.iterrows():
                    # 저장된 언어 중립 키(Indoor/Outdoor)를 현재 언어로 표시
                    io_display = get_io_display(row['IndoorOutdoor'], *)
                    st.write(f"**{row['Venue']}** ({row['Seats']} {*['seats']}, {io_display})")
                    if row['Google Maps Link'].startswith("http"):
                        st.markdown(f"[{*['open_maps']}]({row['Google Maps Link']})")
            if st.session_state.admin or city not in st.session_state.admin_venues:
                with st.form(key=f"add*{city}"):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1: v = st.text_input(*["venue_name"], key=f"v*{city}")
                    with c2: s = st.number_input(*["seats"], 1, step=50, key=f"s*{city}")
                    with c3:
                        # 세션 상태에 언어 중립적인 키(Indoor/Outdoor)를 저장
                        io_key = st.session_state.get(f"io_{city}", 'Outdoor')
                        if st.button(*["indoor_outdoor"], key=f"io_btn*{city}", use_container_width=True):
                            io_key = 'Indoor' if io_key == 'Outdoor' else 'Outdoor'
                            st.session_state[f"io_{city}"] = io_key
                        st.markdown(f"**{get_io_display(io_key, _)}**") # 현재 언어로 표시
                    l = st.text_input(*["google_link"], key=f"l*{city}")
                    if st.form_submit_button(*["register"]) and v:
                        new_row = pd.DataFrame([{'Venue': v, 'Seats': s, 'IndoorOutdoor': io_key, 'Google Maps Link': l}])
                        target = st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
                        target[city] = pd.concat([target.get(city, pd.DataFrame()), new_row], ignore_index=True)
                        st.success(f"{*['register']} {_['save']}")
                        st.rerun()

# =============================================

# 8. 지도

# =============================================

st.markdown("---")
st.subheader(*["tour_map"])
if st.session_state.route:
    center = coords.get(st.session_state.route[0], (19.75, 75.71))
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")
    if len(st.session_state.route) > 1:
        folium.PolyLine([coords[c] for c in st.session_state.route], color="red", weight=4).add_to(m)
    for city in st.session_state.route:
        df = st.session_state.admin_venues.get(city, pd.DataFrame()) if st.session_state.admin else st.session_state.venues.get(city, pd.DataFrame())
        link = next((r['Google Maps Link'] for *, r in df.iterrows() if r['Google Maps Link'].startswith('http')), None)
        popup = f"<b>{city}</b>
{st.session_state.dates.get(city, 'TBD').strftime(*['date_format'])}"
        if link:
            popup = f'<a href="{link}" target="_blank">{popup}
<i>{*["open_maps"]}</i></a>'
        folium.CircleMarker(coords[city], radius=12, color="#2E8B57", fill_color="#90EE90", popup=folium.Popup(popup, max_width=300)).add_to(m)
    folium_static(m, width=700, height=500)
st.caption(_["caption"])
EOF
git add app.py
git commit -m "Final attempt to remove shell commands and resolve SyntaxError"
git push
