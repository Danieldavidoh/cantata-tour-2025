# app.py
import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from math import radians, sin, cos, sqrt, atan2
import re
import json
import os
import base64
import uuid

# =============================================
# PWA & 실시간 푸시 알림 설정
# =============================================
st.set_page_config(
    page_title="Cantata Tour 2025",
    page_icon="🎄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# PWA Manifest & Service Worker 등록
st.markdown("""
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#ff1744">
<script>
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(() => console.log('SW registered'))
            .catch(err => console.log('SW error:', err));
    });
}
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}
</script>
""", unsafe_allow_html=True)

# =============================================
# 세션 상태 초기화
# =============================================
defaults = {
    "lang": "ko", "admin": False, "route": [], "venue_data": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================================
# 데이터 로드/저장
# =============================================
VENUE_FILE = "venue_data.json"

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

st.session_state.venue_data = load_json(VENUE_FILE, {})

# 기본 도시 자동 추가
default_cities = {
    "Mumbai": {"venue": "NSCI Dome", "seats": 5000, "type": "실내", "google": ""},
    "Pune": {"venue": "Balewadi Stadium", "seats": 8000, "type": "실외", "google": ""},
    "Nagpur": {"venue": "VCA Stadium", "seats": 45000, "type": "실외", "google": ""}
}
if not st.session_state.venue_data:
    st.session_state.venue_data = default_cities.copy()
    save_json(VENUE_FILE, st.session_state.venue_data)
for city in default_cities:
    if city not in st.session_state.route:
        st.session_state.route.append(city)

# =============================================
# 언어 설정
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어", "password": "관리자 비밀번호", "login": "로그인", "logout": "로그아웃",
        "city_input": "도시 입력", "venue_name": "공연장 이름", "seats_count": "좌석 수", "venue_type": "공연장 유형",
        "google_link": "구글 링크", "add_venue": "추가", "already_exists": "이미 존재하는 도시입니다."
    }
}
_ = LANG.get(st.session_state.lang, LANG["ko"])

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    lang_selected = st.selectbox("Language", ["ko", "en", "hi"], format_func=lambda x: {"ko":"한국어","en":"English","hi":"हिन्दी"}[x])
    st.session_state.lang = lang_selected if lang_selected in LANG else "ko"
    _ = LANG.get(st.session_state.lang, LANG["ko"])

    st.markdown("---")
    st.write("**Admin**")
    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]) and pw == "0000":
            st.session_state.admin = True
            st.rerun()
        elif pw and pw != "0000":
            st.error("비밀번호 틀림")
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 서클 화살표 SVG
# =============================================
REFRESH_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M23 4v6h-6"></path>
  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
</svg>
"""

# =============================================
# 스타일
# =============================================
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at 20% 20%, #0a0a0f 0%, #000000 100%); color: #fff; }
h1 { color: #ff3333 !important; text-align: center; font-weight: 900; font-size: 4em;
     text-shadow: 0 0 25px #b71c1c, 0 0 15px #00ff99; }
h1 span.year { color: #fff; font-size: 0.8em; vertical-align: super; }
h1 span.subtitle { color: #ccc; font-size: 0.45em; vertical-align: super; margin-left: 5px; }

/* 제목: 흰색 + 1.3em 통일 */
.city-input-title {
    color: white !important; 
    font-weight: bold; 
    font-size: 1.3em; 
    margin-bottom: 15px;
}

/* 새로고침 버튼 */
.refresh-btn {
    background: none; 
    border: 2px solid #00c853; 
    border-radius: 50%; 
    width: 44px; height: 44px; 
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; 
    transition: all 0.3s;
}
.refresh-btn:hover {
    background: rgba(0,200,83,0.1); 
    border-color: #00b140;
    transform: scale(1.15);
}
.refresh-icon {
    width: 24px; height: 24px; 
    animation: rotate 1.5s linear infinite paused;
    stroke: #00c853;
}
.refresh-btn:hover .refresh-icon {
    animation-play-state: running;
}
@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.city-input-form {
    background: #1a1a1a; border: 2px solid #333; border-radius: 12px; padding: 20px; margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"<h1>{_['title']} <span class='year'>2025</span><span class='subtitle'>마하라스트라</span> 🎄</h1>", unsafe_allow_html=True)

# =============================================
# 도시 & 거리 계산
# =============================================
coords = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882)
}

def distance_km(p1, p2):
    R = 6371
    lat1, lon1 = radians(p1[0]), radians(p1[1])
    lat2, lon2 = radians(p2[0]), radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# =============================================
# 투어지도 UI
# =============================================
def render_tour_map():
    st.markdown(f"""
    <div class="map-header">
        <div class="map-title">투어지도</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("투어지도", expanded=False):
        try:
            GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        except:
            st.error("Google Maps API 키 없음")
            return

        m = folium.Map(location=(19.75, 75.71), zoom_start=6,
                       tiles=f"https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_API_KEY}",
                       attr="Google")
        points = [coords[c] for c in st.session_state.route if c in coords]
        if len(points) >= 2:
            for i in range(len(points)-1):
                p1, p2 = points[i], points[i+1]
                dist = distance_km(p1, p2)
                time_hr = dist / 60.0
                mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
                folium.Marker(mid, icon=folium.DivIcon(html=f"<div style='color:white;font-size:10pt'>{dist:.1f}km / {time_hr:.1f}h</div>")).add_to(m)
            AntPath(points, color="red", weight=4, delay=800).add_to(m)

        for c in st.session_state.route:
            if c in coords:
                data = st.session_state.venue_data.get(c, {})
                popup = f"<b>{c}</b><br>"
                if "date" in data: popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data['type']}<br>"
                if "google" in data and data["google"]:
                    match = re.search(r'@(\d+\.\d+),(\d+\.\d+)', data["google"])
                    lat, lng = (match.group(1), match.group(2)) if match else (None, None)
                    nav = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}" if lat else data["google"]
                    popup += f"<a href='{nav}' target='_blank'>네비 시작</a>"
                folium.Marker(coords[c], popup=popup, icon=folium.Icon(color="red")).add_to(m)
        st_folium(m, width=900, height=600)

# =============================================
# 일반 사용자 UI
# =============================================
if not st.session_state.admin:
    render_tour_map()
    st.stop()

# =============================================
# 관리자 모드
# =============================================

# 도시 입력
st.markdown(f"<div class='city-input-title'>{_['city_input']}</div>", unsafe_allow_html=True)
with st.form("city_form", clear_on_submit=True):
    col1, col2 = st.columns([1, 1])
    with col1:
        new_city = st.text_input("도시 이름", placeholder="예: Delhi")
    with col2:
        venue_name = st.text_input(_["venue_name"], placeholder="공연장 이름")

    col3, col4 = st.columns([1, 1])
    with col3:
        seats = st.number_input(_["seats_count"], min_value=1, step=1)
    with col4:
        venue_type = st.selectbox(_["venue_type"], ["실내", "실외"])

    google_link = st.text_input(_["google_link"], placeholder="구글 링크 (선택)")

    if st.form_submit_button(_["add_venue"]):
        if new_city in st.session_state.venue_data:
            st.error(_["already_exists"])
        else:
            st.session_state.venue_data[new_city] = {
                "venue": venue_name,
                "seats": seats,
                "type": venue_type,
                "google": google_link
            }
            save_json(VENUE_FILE, st.session_state.venue_data)
            if new_city not in st.session_state.route:
                st.session_state.route.append(new_city)
            st.success(f"{new_city} 추가됨!")
            st.rerun()

# 투어지도
st.markdown("---")
render_tour_map()
