# app.py
import json, os, uuid, base64, random
import streamlit as st  # <--- 반드시 최상단!
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
LANG = { ... }  # 생략 (기존 그대로)

# --- 4. 세션 상태 ---
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False, "adding_city": False}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 5. JSON 헬퍼 ---
def load_json(f): 
    return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): 
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)  # <--- 오타 수정!

# --- 6. 초기 도시 + 좌표 (반드시 여기서 정의!) ---
DEFAULT_CITIES = [ ... ]  # 기존 그대로
if not os.path.exists(CITY_FILE): 
    save_json(CITY_FILE, DEFAULT_CITIES)

# <--- 이 줄 반드시 추가! ---
CITY_COORDS = { 
    "Mumbai": (19.0760, 72.8777), 
    "Pune": (18.5204, 73.8567), 
    "Nagpur": (21.1458, 79.0882) 
}
# --- 여기까지 ---

# --- CSS 및 헤더 (기존 그대로) ---
st.markdown(""" ... """, unsafe_allow_html=True)

# --- 눈송이, 아이콘, 제목, 버튼 (기존 그대로) ---
# ... (생략)

# --- 버튼 라인 ---
st.markdown('<div class="button-row">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])
with col1:
    if st.button(_("tab_notice"), key="btn_notice", use_container_width=True):
        st.session_state.notice_open = not st.session_state.notice_open
        st.session_state.map_open = False
        st.rerun()
with col2:
    if st.button(_("tab_map"), key="btn_map", use_container_width=True):
        st.session_state.map_open = not st.session_state.map_open
        st.session_state.notice_open = False
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- 메인 컨텐츠 시작 ---
st.markdown("<div class='main-content'>", unsafe_allow_html=True)

# --- 공지 섹션 ---
if st.session_state.notice_open:
    st.markdown("## 공지사항")
    # ... (기존 공지 코드)

# --- 지도 섹션 ---
if st.session_state.map_open:
    st.markdown("## 투어 경로")
    cities = load_json(CITY_FILE)
    if not cities:
        st.warning("등록된 도시가 없습니다.")
    else:
        m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="OpenStreetMap")
        for i, c in enumerate(cities):
            coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))  # <--- 이제 정의됨!
            lat, lon = coords
            is_future = c.get("perf_date", "9999-12-31") >= str(date.today())
            color = "red" if is_future else "gray"
            indoor_text = _("indoor") if c.get("indoor") else _("outdoor")
            popup_html = f"""
            <div style='font-size:14px; line-height:1.6;'>
                <b>{c['city']}</b><br>
                {_('perf_date')}: {c.get('perf_date','미정')}<br>
                {_('venue')}: {c.get('venue','—')}<br>
                {_('seats')}: {c.get('seats','—')}<br>
                {indoor_text}<br>
                <a href='https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving' target='_blank'>
                    {_('google_link')}
                </a>
            </div>
            """
            folium.Marker(
                coords,
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=color, icon="music", prefix="fa")
            ).add_to(m)

            if i < len(cities) - 1:
                nxt_coords = CITY_COORDS.get(cities[i+1]["city"], (18.5204, 73.8567))
                AntPath([coords, nxt_coords], color="#e74c3c", weight=6, opacity=1.0 if is_future else 0.3).add_to(m)

        st_folium(m, width=900, height=550, key="tour_map")

# --- 초기 화면: 아무것도 안 보일 때 ---
if not st.session_state.notice_open and not st.session_state.map_open:
    st.markdown("""
    <div style='text-align:center; margin-top:40px; padding:30px; background:rgba(255,255,255,0.1); border-radius:20px;'>
        <h2 style='color:#fff;'>🎄 칸타타 투어 2025 🎄</h2>
        <p style='color:#ddd; font-size:1.2em;'>위 버튼을 눌러 <b>공지</b> 또는 <b>지도</b>를 확인하세요.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --- 사이드바 및 모바일 메뉴 (기존 그대로) ---
# ...
