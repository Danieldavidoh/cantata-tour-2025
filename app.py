import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from math import radians, sin, cos, sqrt, atan2
import re
import json
import os

# =============================================
# 데이터 저장
# =============================================
VENUE_FILE = "venue_data.json"
NOTICE_FILE = "notice_data.json"

def load_venue_data():
    if os.path.exists(VENUE_FILE):
        with open(VENUE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_venue_data(data):
    with open(VENUE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_notice_data():
    if os.path.exists(NOTICE_FILE):
        with open(NOTICE_FILE, "r") as f:
            return json.load(f)
    return []

def save_notice_data(data):
    with open(NOTICE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =============================================
# 언어팩
# =============================================
LANG = {
    "ko": {"title": "칸타타 투어", "subtitle": "마하라스트라", "tour_map": "투어 지도", "notice_button": "공지", "new_notice": "새로운 공지", "notices": "이전 공지"},
    "en": {"title": "Cantata Tour", "subtitle": "Maharashtra", "tour_map": "Tour Map", "notice_button": "Notice", "new_notice": "New Notice", "notices": "Previous Notices"},
    "hi": {"title": "कांटाटा टूर", "subtitle": "महाराष्ट्र", "tour_map": "टूर मानचित्र", "notice_button": "सूचना", "new_notice": "नई सूचना", "notices": "पिछली सूचनाएं"}
}

# =============================================
# 150개 도시 + 좌표 (생략 – 위 코드와 동일)
# =============================================
# (coords 딕셔너리 동일 – 길이 문제로 생략, 이전 코드 그대로 사용)

# =============================================
# Streamlit state
# =============================================
st.set_page_config(page_title="Cantata Tour", layout="wide")

if "lang" not in st.session_state: st.session_state.lang = "ko"
if "admin" not in st.session_state: st.session_state.admin = False
if "route" not in st.session_state: st.session_state.route = []
st.session_state.venue_data = load_venue_data()
st.session_state.notice_data = load_notice_data()
if "new_notice" not in st.session_state: st.session_state.new_notice = len(st.session_state.notice_data) > 0
if "show_notice_list" not in st.session_state: st.session_state.show_notice_list = False
if "show_popup" not in st.session_state: st.session_state.show_popup = False

# =============================================
# Sidebar
# =============================================
with st.sidebar:
    lang_options = {"ko": "한국어", "en": "English", "hi": "हिन्दी"}
    lang_selected = st.selectbox("Language", options=list(lang_options.keys()), format_func=lambda x: lang_options[x])
    st.session_state.lang = lang_selected
    _ = LANG[st.session_state.lang]

    st.markdown("---")
    st.write("**Admin**")
    if not st.session_state.admin:
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw == "0691":
                st.session_state.admin = True
                st.rerun()
    else:
        if st.button("Logout"):
            st.session_state.admin = False
            st.rerun()

# =============================================
# Theme
# =============================================
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at 20% 20%, #0a0a0f 0%, #000000 100%); color: #ffffff; }
h1 { color: #ff3333 !important; text-align: center; font-weight: 900; font-size: 4.3em; text-shadow: 0 0 25px #b71c1c, 0 0 15px #00ff99; }
#notice-popup { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #228B22; padding: 20px; border-radius: 10px; box-shadow: 0 0 20px #ff3b3b; z-index: 9999; max-width: 80%; cursor: pointer; }
</style>
""", unsafe_allow_html=True)

# =============================================
# Title
# =============================================
st.markdown(f"<h1>{_['title']} 2025 🎄<br><small>{_['subtitle']}</small></h1>", unsafe_allow_html=True)

# =============================================
# 일반 모드: 제목 + 지도 + 오른쪽 공지 버튼
# =============================================
if not st.session_state.admin:
    map_col, notice_col = st.columns([4, 1])
    with map_col:
        st.subheader(_["tour_map"])
        try:
            GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        except:
            st.error("Google Maps API 키 없음")
            st.stop()

        m = folium.Map(location=(19.75, 75.71), zoom_start=6,
                       tiles=f"https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_API_KEY}",
                       attr="Google")

        points = [coords[c] for c in st.session_state.route if c in coords]
        if len(points) >= 2:
            AntPath(points, color="red", weight=4, delay=800).add_to(m)

        for c in st.session_state.route:
            if c in coords:
                data = st.session_state.venue_data.get(c, {})
                popup = f"<b>{c}</b><br>"
                if "date" in data:
                    popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data['type']}<br>"
                if "google" in data and data["google"]:
                    lat, lng = re.search(r'@(\d+\.\d+),(\d+\.\d+)', data["google"]) or (None, None)
                    nav_link = f"https://www.google.com/maps/dir/?api=1&destination={lat.group(1)},{lng.group(1)}" if lat and lng else data["google"]
                    popup += f"<a href='{nav_link}' target='_blank'>🚗 네비 시작</a>"
                folium.Marker(coords[c], popup=popup, icon=folium.Icon(color="red", icon="music", prefix="fa")).add_to(m)

        st_folium(m, width=900, height=650)

    with notice_col:
        st.write("")  # 공간
        button_label = f"{_['new_notice']} 📢" if st.session_state.new_notice else _["notice_button"]
        if st.button(button_label, key="notice_btn"):
            st.session_state.show_notice_list = True
            st.session_state.new_notice = False
            st.rerun()

    # 공지 리스트 (버튼 클릭 시)
    if st.session_state.show_notice_list:
        st.markdown("### 공지사항")
        for notice in st.session_state.notice_data:
            if st.button(notice["title"], key=f"notice_{notice['id']}"):
                st.markdown(f"""
                <div id="notice-popup" onclick="this.style.display='none';">
                    <h3>{notice['title']}</h3>
                    <p>{notice['content']}</p>
                </div>
                """, unsafe_allow_html=True)

    # 새 공지 알림음 + 팝업
    if st.session_state.new_notice and st.session_state.show_popup:
        st.markdown("""
        <audio autoplay>
            <source src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" type="audio/mpeg">
        </audio>
        <script>
            setTimeout(() => { document.querySelector('audio').pause(); }, 5000);
        </script>
        """, unsafe_allow_html=True)
        latest = st.session_state.notice_data[0]
        st.markdown(f"""
        <div id="notice-popup" onclick="this.style.display='none';">
            <h3>{latest['title']}</h3>
            <p>{latest['content']}</p>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.show_popup = False

    st.stop()

# =============================================
# 관리자 모드: 전체 UI (기존 코드 유지)
# =============================================
# (이전 코드의 관리자 부분 그대로 – 길이 문제로 생략, 이전 메시지 참조)
