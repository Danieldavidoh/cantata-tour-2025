import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
import random

# --- 1. 기본 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

# --- 2. 파일 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 3. 다국어 ---
LANG = { ... }  # (기존 LANG 생략 - 그대로 유지)

defaults = { ... }  # (기존 defaults 생략 - 그대로 유지)
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 4. 캐롤 사운드 ---
def play_carol():
    if os.path.exists("carol.wav"):
        st.session_state.sound_played = True
        st.markdown(f"<audio autoplay><source src='carol.wav' type='audio/wav'></audio>", unsafe_allow_html=True)

# --- 5. CSS + 배경 + 눈 효과 (투명도 50%) ---
st.markdown("""
<style>
    /* 크리스마스 배경 */
    [data-testid="stAppViewContainer"] {
        background: url("background_christmas_dark.png");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* 눈송이 - 투명도 50% 고정 */
    .snowflake {
        position: fixed;
        top: -15px;
        color: white;
        font-size: 1.3em;
        pointer-events: none;
        animation: fall linear infinite;
        opacity: 0.5 !important;  /* 50% 투명 */
        text-shadow: 0 0 6px rgba(255,255,255,0.8);
        z-index: 1;
    }
    @keyframes fall {
        0%   { transform: translateY(0) rotate(0deg); }
        100% { transform: translateY(120vh) rotate(360deg); }
    }

    /* 기존 스타일 유지 */
    .alert-box { ... }
    .city-label { ... }
    .fullscreen-map { ... }
</style>
""", unsafe_allow_html=True)

# --- 눈송이 생성 (투명도 50% 고정) ---
for i in range(80):  # 성능 고려해 120 → 80개로 감소
    left = random.randint(0, 100)
    duration = random.randint(8, 16)
    size = random.uniform(0.9, 1.8)
    delay = random.uniform(0, 5)
    st.markdown(
        f"<div class='snowflake' style='left:{left}vw; animation-duration:{duration}s; font-size:{size}em; animation-delay:{delay}s;'>❄</div>",
        unsafe_allow_html=True
    )

# --- 전체화면 지도 클릭 ---
st.markdown("""
<script>
    let mapClicked = false;
    document.addEventListener('click', function(e) {
        if (e.target.closest('.folium-map')) {
            if (!mapClicked) {
                const map = e.target.closest('.folium-map');
                map.classList.add('fullscreen-map');
                mapClicked = true;
            } else {
                const map = document.querySelector('.fullscreen-map');
                if (map) map.classList.remove('fullscreen-map');
                mapClicked = false;
            }
        }
    });
</script>
""", unsafe_allow_html=True)

# --- 6. 제목 ---
st.markdown('# 칸타타 투어 2025 마하라스트라')

# --- 7. 사이드바 --- (기존 그대로)
with st.sidebar:
    # ... (기존 코드 유지)
    pass

# --- 8~10. JSON, 도시 초기화, 좌표 --- (기존 그대로)
# (DEFAULT_CITIES, CITY_COORDS 등 생략 - 동일)

# --- 11~12. 공지 및 지도 함수 ---
# (render_notices, format_date_with_weekday 등 생략 - 동일)

def render_map():
    st.subheader("경로 보기")
    today = date.today()
    raw_cities = load_json(CITY_FILE)
    cities = sorted(raw_cities, key=lambda x: x.get("perf_date", "9999-12-31"))

    # --- 지도: 일반 도로 지도 (Google Maps 스타일) ---
    m = folium.Map(
        location=[18.5204, 73.8567],
        zoom_start=7,
        tiles="OpenStreetMap"  # 일반 도로 지도 (위성 아님)
    )

    for i, c in enumerate(cities):
        is_past = (c.get('perf_date') and c['perf_date'] != "9999-12-31" and
                   datetime.strptime(c['perf_date'], "%Y-%m-%d").date() < today)
        color = "red" if not is_past else "gray"

        coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
        indoor_text = _(f"indoor") if c.get("indoor") else _(f"outdoor")
        perf_date_formatted = format_date_with_weekday(c.get("perf_date"))
        lat, lon = coords
        google_nav = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"

        popup_html = f"""
        <div style="font-size: 14px; line-height: 1.6; font-family: sans-serif;">
            <b style="color:#d35400;">{c['city']}</b><br>
            날짜: <b>{perf_date_formatted}</b><br>
            장소: {c.get('venue','—')}<br>
            인원: {c.get('seats','—')}<br>
            유형: {indoor_text}
        </div>
        """
        folium.Marker(
            coords,
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=color, icon="music", prefix="fa")
        ).add_to(m)

        if i < len(cities) - 1:
            nxt = cities[i + 1]
            nxt_coords = CITY_COORDS.get(nxt["city"], (18.5204, 73.8567))
            opacity = 0.3 if is_past else 1.0
            AntPath([coords, nxt_coords],
                    color="#e74c3c", weight=6, opacity=opacity, delay=800, dash_array=[20, 30]).add_to(m)

        # --- 도시 정보 Expander ---
        exp_key = f"city_{c['city']}"
        expanded = exp_key in st.session_state.expanded_cities
        with st.expander(f"{c['city']} | {format_date_with_weekday(c.get('perf_date'))}", expanded=expanded):
            indoor_icon = "실내" if c.get("indoor") else "야외"
            st.markdown(f"""
            <div><span style="font-weight:bold;color:#e74c3c;">장소:</span> {c.get('venue','—')}</div>
            <div><span style="font-weight:bold;color:#e74c3c;">인원:</span> {c.get('seats','—')}</div>
            <div><span style="font-weight:bold;color:#e74c3c;">유형:</span> {indoor_text}</div>
            <div><span style="font-weight:bold;color:#e74c3c;">특이사항:</span> {c.get('note','—')}</div>
            """, unsafe_allow_html=True)
            if c.get("google_link") or True:
                st.markdown(f"[길 안내 (Google Maps)]({google_nav})", unsafe_allow_html=True)

            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("수정", key=f"edit_{c['city']}"):
                        st.session_state.edit_city = c["city"]
                        st.rerun()
                with c2:
                    if st.button("삭제", key=f"del_{c['city']}"):
                        raw_cities = [x for x in raw_cities if x["city"] != c["city"]]
                        save_json(CITY_FILE, raw_cities)
                        st.rerun()

    st_folium(m, width=900, height=550, key="tour_map")

# --- 13. 탭 ---
col1, col2 = st.columns(2)
with col1:
    if st.button(_(f"tab_notice"), use_container_width=True):
        st.session_state.tab_selection = _(f"tab_notice")
        st.rerun()
with col2:
    if st.button(_(f"tab_map"), use_container_width=True):
        st.session_state.tab_selection = _(f"tab_map")
        st.rerun()

# --- 탭 전환 초기화 ---
if st.session_state.tab_selection != st.session_state.get("last_tab"):
    st.session_state.expanded_notices = []
    st.session_state.expanded_cities = []
    st.session_state.last_tab = st.session_state.tab_selection
    st.rerun()

if st.session_state.get("new_notice", False):
    st.session_state.tab_selection = _(f"tab_notice")
    st.session_state.new_notice = False
    st.rerun()

# --- 14. 렌더링 ---
if st.session_state.tab_selection == _(f"tab_notice"):
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            title = st.text_input("제목")
            content = st.text_area("내용")
            img = st.file_uploader("이미지", type=["png", "jpg", "jpeg"])
            file = st.file_uploader("첨부 파일")
            if st.form_submit_button("등록"):
                if title.strip() and content.strip():
                    add_notice(title, content, img, file)
                else:
                    st.warning(_("warning"))
    render_notices()
else:
    render_map()
