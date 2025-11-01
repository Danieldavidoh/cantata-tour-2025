cd ~/cantata-tour && 
cat > app.py << 'EOF'
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
import math
import locale
import sys
 
# =============================================
# 1. 다국어 사전 (영어 / 한국어 / 힌디어)
# =============================================
LANG = {
    "en": {
        "title": "🎼 Cantata Tour <span style='font-size:1.1rem; color:#888; font-weight:normal;'>(Maharashtra)</span>",
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
        "google_link": "Google Maps Link",
        "register": "Register",
        "open_maps": "Open in Google Maps",
        "save": "Save",
        "delete": "Delete",
        "tour_map": "Tour Map",
        "caption": "Mobile: ⋮ → 'Add to Home Screen' → Use like an app!",
        "date_format": "%b %d, %Y",   # Jan 01, 2025
    },
    "ko": {
        "title": "🎼 칸타타 투어 <span style='font-size:1.1rem; color:#888; font-weight:normal;'>(마하라슈트라)</span>",
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
        "google_link": "구글 지도 링크",
        "register": "등록",
        "open_maps": "구글 지도 열기",
        "save": "저장",
        "delete": "삭제",
        "tour_map": "투어 지도",
        "caption": "모바일: ⋮ → '홈 화면에 추가' → 앱처럼 사용!",
        "date_format": "%Y년 %m월 %d일",   # 2025년 01월 01일
    },
    "hi": {
        "title": "🎼 कांताता टूर <span style='font-size:1.1rem; color:#888; font-weight:normal;'>(महाराष्ट्र)</span>",
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
        "google_link": "गूगल मैप्स लिंक",
        "register": "रजिस्टर",
        "open_maps": "गूगल मैप्स में खोलें",
        "save": "सहेजें",
        "delete": "हटाएँ",
        "tour_map": "टूर मैप",
        "caption": "मोबाइल: ⋮ → 'होम स्क्रीन पर जोड़ें' → ऐप की तरह उपयोग करें!",
        "date_format": "%d %b %Y",   # 01 जनवरी 2025
    },
}
 
# =============================================
# 2. 언어 선택 (사이드바)
# =============================================
st.set_page_config(page_title="Cantata Tour", layout="wide", initial_sidebar_state="collapsed")
 
with st.sidebar:
    st.markdown("### 🌐 Language")
    lang = st.radio(
        "Select language",
        options=["en", "ko", "hi"],
        format_func=lambda x: {"en": "English", "ko": "한국어", "hi": "हिन्दी"}[x],
        index=0,
        horizontal=True,
    )
# 현재 선택된 언어 텍스트
_ = LANG[lang]
 
# =============================================
# 3. 도시 & 좌표 (변경 없음)
# =============================================
cities = [
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
]
cities = sorted(cities)
 
coords = {  # (위도, 경도) – 기존 그대로
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
# 4. 세션 초기화
# =============================================
def init_session():
    defaults = {
        'route': [],
        'dates': {},
        'distances': {},
        'venues': {city: pd.DataFrame(columns=['Venue', 'Seats', 'Google Maps Link']) for city in cities},
        'start_city': 'Mumbai'
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
 
init_session()
 
# =============================================
# 5. UI – 한 줄 타이틀 (모바일 최적)
# =============================================
st.markdown(
    f"<h1 style='margin:0; padding:0; font-size:2.2rem;'>{_[ 'title' ]}</h1>",
    unsafe_allow_html=True
)
 
# 출발 도시 선택
start_city = st.selectbox(*["start_city"], cities,
                          index=cities.index(st.session_state.start_city) if st.session_state.start_city in cities else 0)
 
col_start, col_reset = st.columns([1, 4])
with col_start:
    if st.button(*["start_btn"], use_container_width=True):
        if start_city not in st.session_state.route:
            st.session_state.route = [start_city]
            st.session_state.dates[start_city] = datetime.now().date()
            st.success(f"{*['start_city']} {start_city}에서 투어가 시작되었습니다!")
            st.rerun()
 
with col_reset:
    if st.button(*["reset_btn"], use_container_width=True):
        init_session()
        st.rerun()
 
# =============================================
# 6. 경로 관리
# =============================================
if st.session_state.route:
    st.markdown("---")
 
    available = [c for c in cities if c not in st.session_state.route]
    if available:
        new_city = st.selectbox(*["next_city"], available, key="next_city")
        col_add, _ = st.columns([1, 3])
        with col_add:
            if st.button(*["add_btn"], use_container_width=True):
                st.session_state.route.append(new_city)
 
                if len(st.session_state.route) > 1:
                    prev = st.session_state.route[-2]
                    lat1, lon1 = coords[prev]
                    lat2, lon2 = coords[new_city]
                    R = 6371
                    dlat = math.radians(lat2 - lat1)
                    dlon = math.radians(lon2 - lon1)
                    a = (math.sin(dlat/2)**2 +
                         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                         math.sin(dlon/2)**2)
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    km = round(R * c)
                    hrs = round(km / 50, 1)
 
                    st.session_state.distances.setdefault(prev, {})[new_city] = (km, hrs)
                    st.session_state.distances.setdefault(new_city, {})[prev] = (km, hrs)
 
                    prev_date = st.session_state.dates.get(prev, datetime.now().date())
                    travel_dt = datetime.combine(prev_date, datetime.min.time()) + timedelta(hours=hrs)
                    st.session_state.dates[new_city] = travel_dt.date()
 
                st.success(f"{new_city} 추가! ({km}km, {hrs}h)")
                st.rerun()
 
    # 현재 경로 표시
    st.markdown(*["current_route"])
    st.write(" → ".join(st.session_state.route))
 
    total_km = total_hrs = 0
    for i in range(len(st.session_state.route)-1):
        a, b = st.session_state.route[i], st.session_state.route[i+1]
        km, hrs = st.session_state.distances.get(a, {}).get(b, (100, 2.0))
        total_km += km
        total_hrs += hrs
 
    col_k, col_t = st.columns(2)
    with col_k: st.metric(*["total_distance"], f"{total_km:,} km")
    with col_t: st.metric(*["total_time"], f"{total_hrs:.1f} h")
 
    # =============================================
    # 7. 공연장 + 날짜 + 구글맵 미리보기
    # =============================================
    st.markdown("---")
    st.subheader(*["venues_dates"])
 
    for i, city in enumerate(st.session_state.route):
        with st.expander(f"{city}", expanded=False):
            # 날짜 입력 (언어별 포맷)
            cur_date = st.session_state.dates.get(city, datetime.now().date())
            new_date = st.date_input(
                *["performance_date"],
                value=cur_date,
                key=f"date*{city}"
            )
            if new_date != cur_date:
                st.session_state.dates[city] = new_date
                st.success(f"{city} 날짜 → {new_date.strftime(*['date_format'])}")
                st.rerun()
 
            df = st.session_state.venues[city]
            if not df.empty:
                st.dataframe(df[['Venue', 'Seats']], use_container_width=True, hide_index=True)
 
            # 공연장 등록 폼
            with st.form(key=f"add*{city}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    venue = st.text_input(*["venue_name"], key=f"v*{city}")
                with col2:
                    seats = st.number_input(*["seats"], min_value=1, step=50, key=f"s*{city}")
                link = st.text_input(*["google_link"], placeholder="https://maps.google.com/...", key=f"l*{city}")
                submitted = st.form_submit_button(*["register"])
 
            if link and link.startswith("http"):
                st.markdown(f"{_['open_maps']}", unsafe_allow_html=True)
 
            if submitted and venue:
                new_row = pd.DataFrame([{'Venue': venue, 'Seats': seats, 'Google Maps Link': link}])
                st.session_state.venues[city] = pd.concat([df, new_row], ignore_index=True)
                st.success("등록 완료!")
                st.rerun()
 
            # 기존 공연장 편집/삭제
            for idx, row in df.iterrows():
                with st.expander(f"{row['Venue']} ({row['Seats']} {*['seats']})", expanded=False):
                    col_e1, col_e2 = st.columns([2, 1])
                    with col_e1:
                        new_venue = st.text_input(*["venue_name"], value=row['Venue'], key=f"ev*{city}*{idx}")
                    with col_e2:
                        new_seats = st.number_input(*["seats"], value=int(row['Seats']), min_value=1, key=f"es_{city}*{idx}")
                    new_link = st.text_input(*["google_link"], value=row['Google Maps Link'], key=f"el_{city}*{idx}")
 
                    col_save, col_del = st.columns(2)
                    with col_save:
                        if st.button(*["save"], key=f"save_{city}*{idx}"):
                            st.session_state.venues[city].loc[idx] = [new_venue, new_seats, new_link]
                            st.success("수정 완료")
                            st.rerun()
                    with col_del:
                        if st.button(*["delete"], key=f"del_{city}*{idx}"):
                            st.session_state.venues[city] = df.drop(idx).reset_index(drop=True)
                            st.success("삭제 완료")
                            st.rerun()
 
                    if row['Google Maps Link'] and row['Google Maps Link'].startswith("http"):
                        st.markdown(f"[{*['open_maps']}]({row['Google Maps Link']})", unsafe_allow_html=True)
 
        # 다음 도시까지 거리/시간 표시
        if i < len(st.session_state.route) - 1:
            next_c = st.session_state.route[i+1]
            km, hrs = st.session_state.distances.get(city, {}).get(next_c, (100, 2.0))
            st.markdown(
                f"<div style='text-align:center; margin:4px 0; color:#666;'>↓ {km}km | {hrs}h ↓</div>",
                unsafe_allow_html=True
            )
 
    # =============================================
    # 8. 투어 지도 (클릭 → 구글맵)
    # =============================================
    st.markdown("---")
    st.subheader(*["tour_map"])
 
    center = coords.get(st.session_state.route[0] if st.session_state.route else 'Mumbai', (19.75, 75.71))
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")
 
    route_coords = [coords.get(c, center) for c in st.session_state.route]
    if len(route_coords) > 1:
        folium.PolyLine(route_coords, color="red", weight=4, opacity=0.8, dash_array="5,10").add_to(m)
 
    for city in st.session_state.route:
        df = st.session_state.venues.get(city, pd.DataFrame())
        links = [r['Google Maps Link'] for *, r in df.iterrows() if r['Google Maps Link'] and r['Google Maps Link'].startswith('http')]
 
        if links:
            map_link = links[0]
            popup_html = f"""
            <a href="{map_link}" target="_blank" style="text-decoration:none; color:inherit; cursor:pointer; display:block;">
                <div style="font-size:14px; min-width:180px; text-align:center; padding:8px;">
                    <b style="font-size:16px;">{city}</b>

                    {*['performance_date']}: {st.session_state.dates.get(city, 'TBD').strftime(*['date_format'])}

                    <i style="color:#1a73e8;">{*['open_maps']}</i>
                </div>
            </a>
            """
        else:
            popup_html = f"""
            <div style="font-size:14px; min-width:180px; text-align:center; padding:8px;">
                <b style="font-size:16px;">{city}</b>

                {*['performance_date']}: {st.session_state.dates.get(city, 'TBD').strftime(*['date_format'])}
            </div>
            """
 
        popup = folium.Popup(popup_html, max_width=300)
        folium.CircleMarker(
            location=coords.get(city, center),
            radius=12,
            color="#2E8B57",
            fill=True,
            fill_color="#90EE90",
            popup=popup
        ).add_to(m)
 
    folium_static(m, width=700, height=500)
 
st.caption(*["caption"])
EOF
