import json
import os
import uuid
import base64
import random
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

# --- 2. 파일 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 3. 다국어 ---
LANG = {
    "ko": { "title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
            "tab_notice": "공지", "tab_map": "투어 경로", "add_city": "도시 추가", "indoor": "실내", "outdoor": "실외",
            "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵", "perf_date": "공연 날짜",
            "warning": "제목·내용 입력", "edit": "수정", "save": "입력", "cancel": "취소", "delete": "제거" },
    "en": { "title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
            "tab_notice": "Notice", "tab_map": "Tour Route", "add_city": "Add City", "indoor": "Indoor", "outdoor": "Outdoor",
            "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps", "perf_date": "Performance Date",
            "warning": "Enter title & content", "edit": "Edit", "save": "Add", "cancel": "Cancel", "delete": "Remove" },
    "hi": { "title_cantata": "कैंटाटा टूर", "title_year": "2025", "title_region": "महाराष्ट्र",
            "tab_notice": "सूचना", "tab_map": "टूर मार्ग", "add_city": "शहर जोड़ें", "indoor": "इनडोर", "outdoor": "आउटडोर",
            "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप", "perf_date": "प्रदर्शन तिथि",
            "warning": "शीर्षक·सामग्री दर्ज करें", "edit": "संपादन", "save": "जोड़ें", "cancel": "रद्द करें", "delete": "हटाएं" }
}

# --- 4. 세션 상태 ---
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False, "adding_city": False}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 5. JSON 헬퍼 ---
def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 6. 초기 도시 + 좌표 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도", "google_link": "https://goo.gl/maps/abc123", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-10"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브", "google_link": "https://goo.gl/maps/def456", "indoor": True, "date": "11/07 02:01", "perf_date": "2025-11-12"},
    {"city": "Pune", "venue": "Aga Khan Palace", "seats": "2500", "note": "역사적 장소", "google_link": "https://goo.gl/maps/pune2", "indoor": False, "date": "11/08 14:00", "perf_date": "2025-11-14"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시", "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-16"}
]
if not os.path.exists(CITY_FILE): save_json(CITY_FILE, DEFAULT_CITIES)
CITY_COORDS = { "Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567), "Nagpur": (21.1458, 79.0882) }

# --- 7. CSS: 전체화면 지도 + 닫기 버튼 ---
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
    [data-testid="stAppViewContainer"] { 
        background: url("background_christmas_dark.png"); background-size: cover; background-position: center; background-attachment: fixed; 
        padding-top: 0 !important; margin: 0 !important; overflow: hidden;
    }

    /* 초기 화면 위로 올림 */
    .initial-screen {
        position: relative; margin-top: -30vh; z-index: 100; text-align: center;
    }

    /* 크리스마스 아이콘 */
    .christmas-decoration {
        display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; pointer-events: none;
        margin: 0 0 10px 0;
    }
    .christmas-decoration i {
        color: #fff; text-shadow: 0 0 10px rgba(255,255,255,0.6);
        animation: float 3s ease-in-out infinite, sparkle 2s infinite alternate;
        opacity: 0.95;
    }
    @keyframes sparkle { 0% { text-shadow: 0 0 5px #fff; } 100% { text-shadow: 0 0 15px #fff, 0 0 30px #f00; } }

    /* 제목 */
    .main-title {
        font-size: 2.8em !important; font-weight: bold; text-align: center;
        text-shadow: 0 3px 8px rgba(0,0,0,0.6); margin: 0 !important; line-height: 1.2;
    }

    /* 버튼 라인 */
    .button-row {
        display: flex; justify-content: center; gap: 20px; margin: 10px 0 20px 0; padding: 0 15px;
    }
    .tab-btn {
        background: rgba(255,255,255,0.96); color: #c62828; border: none;
        border-radius: 20px; padding: 10px 20px; font-weight: bold;
        font-size: 1.1em; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: all 0.3s ease; flex: 1; max-width: 200px;
    }
    .tab-btn:hover { background: #d32f2f; color: white; transform: translateY(-2px); }

    /* 전체화면 지도 */
    .fullscreen-map {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 1000;
        background: transparent; display: none; flex-direction: column;
    }
    .fullscreen-map.show { display: flex; }

    /* 지도 닫기 버튼 (왼쪽 아래, 투명 아이콘) */
    .map-close-btn {
        position: fixed; bottom: 20px; left: 20px; z-index: 1001;
        background: rgba(0,0,0,0.5); color: white; border: none;
        border-radius: 50%; width: 50px; height: 50px; font-size: 1.5em;
        cursor: pointer; opacity: 0.7; transition: opacity 0.3s;
        display: flex; align-items: center; justify-content: center;
    }
    .map-close-btn:hover { opacity: 1; }

    /* 눈송이 */
    .snowflake { position:fixed; top:-15px; color:#fff; font-size:1.1em; pointer-events:none; animation:fall linear infinite; opacity:0.3; z-index:1; }
    @keyframes fall { 0% { transform:translateY(0) rotate(0deg); } 100% { transform:translateY(120vh) rotate(360deg); } }

    /* 모바일 햄버거 */
    .hamburger { position:fixed; top:15px; left:15px; z-index:10000; background:rgba(0,0,0,.6); color:#fff; border:none; border-radius:50%; width:50px; height:50px; font-size:24px; cursor:pointer; box-shadow:0 0 10px rgba(0,0,0,.3); }
    .sidebar-mobile { position:fixed; top:0; left:-300px; width:280px; height:100vh; background:rgba(30,30,30,.95); color:#fff; padding:20px; transition:left .3s; z-index:9999; overflow-y:auto; }
    .sidebar-mobile.open { left:0; }
    .overlay { position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,.5); z-index:9998; display:none; }
    .overlay.open { display:block; }
    @media(min-width:769px) { .hamburger, .sidebar-mobile, .overlay { display:none !important; } section[data-testid="stSidebar"] { display:block !important; } }
    .stButton>button { border:none !important; -webkit-appearance:none !important; }
</style>
""", unsafe_allow_html=True)

# --- 크리스마스 아이콘 (랜덤 크기 + 애니메이션) ---
icons = ["fa-gift", "fa-candy-cane", "fa-socks", "fa-sleigh", "fa-deer", "fa-tree", "fa-bell"]
icon_html = ""
for icon in icons:
    size = random.uniform(1.8, 2.5)
    delay = random.uniform(0, 2)
    icon_html += f'<i class="fas {icon}" style="font-size:{size}em; animation-delay:{delay}s;"></i> '
st.markdown(f'<div class="christmas-decoration">{icon_html}</div>', unsafe_allow_html=True)

# --- 눈송이 ---
for i in range(52):
    left = random.randint(0, 100)
    duration = random.randint(10, 20)
    size = random.uniform(0.8, 1.4)
    delay = random.uniform(0, 10)
    st.markdown(f"<div class='snowflake' style='left:{left}vw; animation-duration:{duration}s; font-size:{size}em; animation-delay:{delay}s;'>❄</div>", unsafe_allow_html=True)

# --- 제목 (두 배 위로) ---
st.markdown('<div class="initial-screen">', unsafe_allow_html=True)
title_html = f'<h1 class="main-title"><span style="color:red;">{_("title_cantata")}</span> <span style="color:white;">{_("title_year")}</span> <span style="color:green; font-size:67%;">{_("title_region")}</span></h1>'
st.markdown(title_html, unsafe_allow_html=True)

# --- 버튼 라인 ---
st.markdown('<div class="button-row">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])
with col1:
    if st.button(_("tab_notice"), key="btn_notice", use_container_width=True):
        st.session_state.notice_open = not st.session_state.notice_open
        st.session_state.map_open = False
        st.rerun()
with col2:
    if not st.session_state.notice_open:
        if st.button(_("tab_map"), key="btn_map", use_container_width=True):
            st.session_state.map_open = not st.session_state.map_open
            st.session_state.notice_open = False
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 전체화면 지도 (투어 경로 클릭 시) ---
map_class = "fullscreen-map"
if st.session_state.map_open:
    map_class += " show"
st.markdown(f'<div class="{map_class}">', unsafe_allow_html=True)
if st.session_state.map_open:
    # 상단 버튼 제거
    # 지도 닫기 버튼 (왼쪽 아래)
    st.markdown(f'''
    <button class="map-close-btn" onclick="window.location.href='?map_open=False'">✕</button>
    ''', unsafe_allow_html=True)
    cities = load_json(CITY_FILE)
    m = folium.Map(location=[18.5204, 73.8567], zoom_start=10, tiles="OpenStreetMap")  # Pune 중심
    for i, c in enumerate(cities):
        coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
        lat, lon = coords
        is_future = c.get("perf_date", "9999-12-31") >= str(date.today())
        color = "red" if is_future else "gray"
        indoor_text = _("indoor") if c.get("indoor") else _("outdoor")
        popup_html = f"<div style='font-size:14px; line-height:1.6;'><b>{c['city']}</b><br>{_('perf_date')}: {c.get('perf_date','미정')}<br>{_('venue')}: {c.get('venue','—')}<br>{_('seats')}: {c.get('seats','—')}<br>{indoor_text}<br><a href='https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving' target='_blank'>{_('google_link')}</a></div>"
        folium.Marker(coords, popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=color, icon="music", prefix="fa")).add_to(m)
        if i < len(cities) - 1:
            nxt_coords = CITY_COORDS.get(cities[i+1]["city"], (18.5204, 73.8567))
            AntPath([coords, nxt_coords], color="#e74c3c", weight=6, opacity=0.3 if not is_future else 1.0).add_to(m)
    st_folium(m, width='100%', height='100%', key="tour_map_full")
st.markdown('</div>', unsafe_allow_html=True)

# --- 공지/기타 (기존 코드 유지) ---
# ... (생략, 이전 코드 그대로)
