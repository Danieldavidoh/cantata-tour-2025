import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, cos, sin, asin, sqrt

# Haversine 거리 계산
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371  # km
    return c * r

# 3초 새로고침
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh")

# 기본 설정
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 세션 초기화
defaults = {
    "admin": False,
    "lang": "ko",
    "edit_city": None,
    "expanded": {},
    "adding_cities": [],
    "pw": "0009",
    "seen_notices": []
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 다국어
LANG = {
    "ko": { 
        "title_base": "칸타타 투어", 
        "caption": "마하라스트라", 
        "tab_notice": "공지", 
        "tab_map": "투어 경로", 
        "map_title": "경로 보기", 
        "add_city": "도시 추가", 
        "password": "비밀번호", 
        "login": "로그인", 
        "logout": "로그아웃", 
        "wrong_pw": "비밀번호가 틀렸습니다.", 
        "select_city": "도시 선택", 
        "venue": "공연장소", 
        "seats": "예상 인원", 
        "note": "특이사항", 
        "google_link": "구글맵 링크", 
        "indoor": "실내", 
        "outdoor": "실외", 
        "register": "등록", 
        "edit": "수정", 
        "remove": "삭제", 
        "date": "등록일", 
        "performance_date": "공연 날짜", 
        "cancel": "취소", 
        "title_label": "제목", 
        "content_label": "내용", 
        "upload_image": "이미지 업로드", 
        "upload_file": "파일 업로드", 
        "submit": "등록", 
        "warning": "제목과 내용을 모두 입력해주세요.", 
        "file_download": "파일 다운로드", 
        "change_pw": "비밀번호 변경", 
        "new_pw": "새 비밀번호", 
        "confirm_pw": "비밀번호 확인", 
        "pw_changed": "비밀번호가 변경되었습니다.", 
        "pw_mismatch": "비밀번호가 일치하지 않습니다.",
        "close_all": "모두 접기"
    },
    # (영어, 힌디어 생략 - 동일)
}
_ = lambda key: LANG[st.session_state.lang].get(key, key)

# === 크리스마스 테마 + 눈 + 알림음 ===
christmas_night = """
<style>
.stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #f0f0f0; font-family: 'Segoe UI', sans-serif; overflow: hidden; }
.christmas-title { text-align: center; margin: 20px 0; }
.cantata { font-size: 3em; font-weight: bold; color: #e74c3c; text-shadow: 0 0 10px #ff6b6b; }
.year { font-size: 2.8em; font-weight: bold; color: #ecf0f1; text-shadow: 0 0 8px #ffffff; }
.maha { font-size: 1.8em; color: #3498db; font-style: italic; text-shadow: 0 0 6px #74b9ff; }
.floating-icons { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1; }
.icon { position: absolute; font-size: 2em; animation: float 6s infinite ease-in-out, spin 8s infinite linear; opacity: 0.8; }
@keyframes float { 0%, 100% { transform: translateY(0) translateX(0); } 50% { transform: translateY(-20px) translateX(10px); } }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.snowflake { color: rgba(255, 255, 255, 0.5); font-size: 1.2em; position: absolute; top: -10px; animation: fall linear forwards; user-select: none; pointer-events: none; }
@keyframes fall { to { transform: translateY(100vh); opacity: 0; } }
.stButton>button { background: #c0392b !important; color: white !important; border: 2px solid #e74c3c !important; border-radius: 12px !important; font-weight: bold; }
.stButton>button:hover { background: #e74c3c !important; }
.remove-btn button { color: #000 !important; font-weight: bold; }
.new-badge { background: #e74c3c; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.7em; margin-left: 5px; }
/* 말풍선 한 줄 고정 */
.leaflet-popup-content { max-width: 300px !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.leaflet-popup-content b { display: block; white-space: normal; }
</style>

<div class="floating-icons">
    <div class="icon" style="top:10%; left:10%; animation-delay:0s;">Christmas tree</div>
    <div class="icon" style="top:15%; left:80%; animation-delay:1s;">Present</div>
    <div class="icon" style="top:70%; left:15%; animation-delay:2s;">Candy cane</div>
    <div class="icon" style="top:60%; left:75%; animation-delay:3s;">Stocking</div>
    <div class="icon" style="top:30%; left:60%; animation-delay:4s;">Reindeer</div>
    <div class="icon" style="top:40%; left:20%; animation-delay:5s;">Santa</div>
</div>

<script>
function createSnowflake() {
    const snow = document.createElement('div');
    snow.classList.add('snowflake');
    snow.innerText = ['Snowflake 1', 'Snowflake 2', 'Star 1', 'Star 2'][Math.floor(Math.random() * 4)];
    snow.style.left = Math.random() * 100 + 'vw';
    snow.style.animationDuration = Math.random() * 10 + 8 + 's';
    snow.style.opacity = Math.random() * 0.4 + 0.3;
    snow.style.fontSize = Math.random() * 1.2 + 0.8 + 'em';
    document.body.appendChild(snow);
    setTimeout(() => snow.remove(), 18000);
}
setInterval(createSnowflake, 400);

function playNotification() {
    const audio = new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU'+Array(100).fill('A').join(''));
    audio.play().catch(() => {});
}
</script>
"""
st.markdown(christmas_night, unsafe_allow_html=True)

# === 제목 ===
title_base = _( "title_base" )
caption = _( "caption" )
st.markdown(
    f'<div class="christmas-title">'
    f'<div class="cantata">{title_base}</div>'
    f'<div class="year">2025</div>'
    f'<div class="maha">{caption}</div>'
    f'</div>',
    unsafe_allow_html=True
)

# === 비밀번호 + 관리자 변경 ===
with st.sidebar:
    # (기존 코드 유지 - 생략)
    pass

# === 공지 기능 + 닫기 버튼 (오른쪽 아래) ===
def render_notice_list(show_delete=False):
    data = load_json(NOTICE_FILE)
    has_new = False
    any_expanded = False

    for idx, n in enumerate(data):
        notice_id = n["id"]
        is_new = notice_id not in st.session_state.seen_notices
        if is_new and not st.session_state.admin:
            has_new = True

        key = f"notice_{idx}"
        expanded = st.session_state.expanded.get(key, False)
        if expanded:
            any_expanded = True

        title_display = f"{n['date']} | {n['title']}"
        if is_new and not st.session_state.admin:
            title_display += ' <span class="new-badge">NEW</span>'

        with st.expander(title_display, expanded=expanded):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                href = f'<a href="data:file/octet-stream;base64,{base64.b64encode(open(n["file"], "rb").read()).decode()}" download="{os.path.basename(n["file"])}">Present {_("file_download")}</a>'
                st.markdown(href, unsafe_allow_html=True)
            if show_delete and st.button(_("remove"), key=f"del_{idx}"):
                data.pop(idx)
                save_json(NOTICE_FILE, data)
                st.session_state.expanded = {}
                st.toast("공지가 삭제되었습니다.")
                st.rerun()

            # 읽음 처리
            if not st.session_state.admin and is_new and expanded:
                if notice_id not in st.session_state.seen_notices:
                    st.session_state.seen_notices.append(notice_id)

            # 닫기 버튼 (오른쪽 아래)
            if expanded:
                col1, col2 = st.columns([6, 1])
                with col2:
                    if st.button("Close", key=f"close_{idx}"):
                        st.session_state.expanded[key] = False
                        st.rerun()

        if st.session_state.expanded.get(key, False) != expanded:
            st.session_state.expanded[key] = expanded

    # 알림음
    if has_new and not st.session_state.get("sound_played", False):
        st.markdown('<script>playNotification();</script>', unsafe_allow_html=True)
        st.session_state.sound_played = True
    elif not has_new:
        st.session_state.sound_played = False

    # 전체 접기 버튼 (펼쳐진 게 있을 때만)
    if any_expanded and not st.session_state.admin:
        if st.button(f"Close All {_('close_all')}"):
            st.session_state.expanded = {}
            st.rerun()

# === 투어 경로 탭: 지도 먼저 + 말풍선 한 줄 ===
def render_map():
    st.subheader(f"Map {_('map_title')}")

    cities_data = load_json(CITY_FILE)
    cities_data = sorted(cities_data, key=lambda x: x.get("perf_date", "9999-12-31"))

    # --- 지도 먼저 ---
    m = folium.Map(location=[19.0, 73.0], zoom_start=6)
    coords = []
    today = datetime.now().date()

    for c in cities_data:
        perf_date_str = c.get('perf_date')
        perf_date = datetime.strptime(perf_date_str, "%Y-%m-%d").date() if perf_date_str else None

        # 한 줄 고정 (특이사항 제외)
        popup_lines = [
            f"<b>{c['city']}</b>",
            f"날짜: {c.get('perf_date','')}",
            f"장소: {c.get('venue','')}",
            f"인원: {c.get('seats','')}",
            f"형태: {c.get('type','')}",
            f"<a href='{c.get('map_link','#')}' target='_blank'>길안내</a>"
        ]
        popup_html = "<br>".join(popup_lines) + f"<br><small>{c.get('note','')}</small>"

        icon = folium.Icon(color="red", icon="music")
        opacity = 1.0 if not perf_date or perf_date >= today else 0.4
        extra_classes = "today-marker" if perf_date == today else ""

        folium.Marker(
            [c["lat"], c["lon"]], popup=folium.Popup(popup_html, max_width=300),
            tooltip=c["city"], icon=icon, opacity=opacity, extra_classes=extra_classes
        ).add_to(m)
        coords.append((c["lat"], c["lon"]))

    if coords:
        AntPath(coords, color="#e74c3c", weight=5, delay=800).add_to(m)

    st_folium(m, width=900, height=550)

    # --- 도시 목록 (지도 아래) ---
    st.markdown("---")
    total_dist = 0
    total_time = 0
    average_speed = 65

    for idx, city in enumerate(cities_data):
        key = f"city_expander_{idx}"
        expanded = st.session_state.expanded.get(key, False)
        with st.expander(f"Present {city['city']} | {city.get('perf_date', '')}", expanded=expanded):
            st.write(f"**Date {_('date')}:** {city.get('date', '')}")
            st.write(f"**Performance {_('performance_date')}:** {city.get('perf_date', '')}")
            st.write(f"**Venue {_('venue')}:** {city.get('venue', '')}")
            st.write(f"**Attendance {_('seats')}:** {city.get('seats', '')}")
            st.write(f"**Note {_('note')}:** {city.get('note', '')}")

            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"Edit {_('edit')}", key=f"edit_{idx}_{city['city']}", use_container_width=True):
                        st.session_state.edit_city = city["city"]
                        st.rerun()
                with c2:
                    if st.button(f"Delete {_('remove')}", key=f"remove_{idx}_{city['city']}", use_container_width=True):
                        cities_data.pop(idx)
                        save_json(CITY_FILE, cities_data)
                        st.session_state.expanded = {}
                        st.toast("도시 삭제됨")
                        st.rerun()

        if st.session_state.expanded.get(key, False) != expanded:
            st.session_state.expanded[key] = expanded

        if idx < len(cities_data) - 1:
            next_city = cities_data[idx + 1]
            dist = haversine(city['lat'], city['lon'], next_city['lat'], next_city['lon'])
            time_h = dist / average_speed
            dist_text = f"**{dist:.0f}km / {time_h:.1f}h**"
            st.markdown(
                f'<div style="text-align:center; margin:15px 0; font-weight:bold; color:#2ecc71;">{dist_text}</div>',
                unsafe_allow_html=True
            )
            total_dist += dist
            total_time += time_h

    if len(cities_data) > 1:
        total_text = f"**총 거리 (첫 도시 기준): {total_dist:.0f}km / {total_time:.1f}h**"
        st.markdown(
            f'<div style="text-align:center; margin:20px 0; font-size:1.2em; font-weight:bold; color:#e74c3c;">{total_text}</div>',
            unsafe_allow_html=True
        )

# === 탭 ===
tab1, tab2 = st.tabs([f"Present {_('tab_notice')}", f"Map {_('tab_map')}"])

with tab1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_("title_label"))
            c = st.text_area(_("content_label"))
            img = st.file_uploader(_("upload_image"), type=["png", "jpg", "jpeg"])
            f = st.file_uploader(_("upload_file"))
            if st.form_submit_button(_("submit")):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_("warning"))
        render_notice_list(show_delete=True)
    else:
        render_notice_list(show_delete=False)

with tab2:
    render_map()
