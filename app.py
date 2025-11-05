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
# 페이지 설정
# =============================================
st.set_page_config(
    page_title="Cantata Tour 2025",
    page_icon="🎄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================
# 세션 상태 안전 초기화
# =============================================
def _init_session_state():
    defaults = {
        "lang": "ko",
        "admin": False,
        "route": [],
        "venue_data": {},
        "notice_data": [],
        "show_popup": True,
        "notice_counter": 0,
        "expanded_notices": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_session_state()

# =============================================
# 파일 입출력 (안전하게)
# =============================================
VENUE_FILE = "venue_data.json"
NOTICE_FILE = "notice_data.json"

def load_json(file, default):
    try:
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"파일 로드 실패: {file} ({e})")
    return default

def save_json(file, data):
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"파일 저장 실패: {file} ({e})")

# load persisted data once
st.session_state.venue_data = load_json(VENUE_FILE, st.session_state.venue_data)
st.session_state.notice_data = load_json(NOTICE_FILE, st.session_state.notice_data)

# 기본 도시 자동 추가 (초기 실행시에만)
def ensure_default_cities():
    default_cities = {
        "Mumbai": {"venue": "NSCI Dome", "seats": 5000, "type": "실내", "google": ""},
        "Pune": {"venue": "Balewadi Stadium", "seats": 8000, "type": "실외", "google": ""},
        "Nagpur": {"venue": "VCA Stadium", "seats": 45000, "type": "실외", "google": ""},
    }
    changed = False
    for k, v in default_cities.items():
        if k not in st.session_state.venue_data:
            st.session_state.venue_data[k] = v
            changed = True
        if k not in st.session_state.route:
            st.session_state.route.append(k)
    if changed:
        save_json(VENUE_FILE, st.session_state.venue_data)

ensure_default_cities()

# =============================================
# 경고 사운드(브라우저 제한 주의)
# =============================================
ALERT_SOUND = """
<audio autoplay><source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmFgU7k9n1unEiBC13yO/eizEIHWq+8+OWT" type="audio/wav"></audio>
"""

# =============================================
# 알림 제어
# =============================================

def check_new_notices():
    current = len(st.session_state.notice_data)
    if current > st.session_state.notice_counter:
        st.session_state.notice_counter = current
        return True
    return False

def show_alert_popup():
    st.markdown(
        f"""
    <div style="position:fixed;top:20px;right:20px;z-index:9999;background:linear-gradient(135deg,#ff1744,#ff6b6b);color:white;padding:20px;border-radius:15px;box-shadow:0 0 30px rgba(255,23,68,0.8);font-weight:bold;font-size:1.2em;text-align:center;max-width:320px;border:3px solid #fff;animation:pulse 1.5s infinite,slideIn 0.5s;">
        새 공지 도착!
    </div>
    <style>
    @keyframes pulse {{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.05)}}}}
    @keyframes slideIn {{from{{transform:translateX(100%);opacity:0}}to{{transform:translateX(0);opacity:1}}}}
    </style>
    """
        + ALERT_SOUND,
        unsafe_allow_html=True,
    )

def notice_badge():
    count = len(st.session_state.notice_data)
    if count > 0:
        st.markdown(
            f"""
        <div style="position:fixed;top:15px;right:20px;z-index:9998;background:#ff1744;color:white;border-radius:50%;width:40px;height:40px;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:1.1em;box-shadow:0 0 15px #ff1744;animation:bounce 2s infinite;">
            {count}
        </div>
        <style>@keyframes bounce{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-10px)}}}}</style>
        """,
            unsafe_allow_html=True,
        )

# =============================================
# 다국어(간단)
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어",
        "password": "관리자 비밀번호",
        "login": "로그인",
        "logout": "로그아웃",
        "notice_title": "공지 제목",
        "notice_content": "공지 내용",
        "upload_file": "사진/파일 업로드",
        "city_input": "도시 입력",
        "venue_name": "공연장 이름",
        "seats_count": "좌석 수",
        "venue_type": "공연장 유형",
        "google_link": "구글 링크",
        "add_venue": "추가",
        "already_exists": "이미 존재하는 도시입니다.",
        "delete": "삭제",
        "today_notice": "오늘의 공지",
    }
}
_ = LANG.get(st.session_state.lang, LANG["ko"])

# =============================================
# 사이드바: 로그인 + 언어
# =============================================
with st.sidebar:
    lang_selected = st.selectbox(
        "Language",
        ["ko", "en", "hi"],
        format_func=lambda x: {"ko": "한국어", "en": "English", "hi": "हिन्दी"}[x],
        index=["ko", "en", "hi"].index(st.session_state.lang if st.session_state.lang in ("ko","en","hi") else "ko"),
    )
    st.session_state.lang = lang_selected if lang_selected in LANG else "ko"
    _ = LANG.get(st.session_state.lang, LANG["ko"])

    st.markdown("---")
    st.write("**Admin**")
    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]) and pw == "0000":
            st.session_state.admin = True
            st.experimental_rerun()
        elif pw and pw != "0000":
            st.error("비밀번호 틀림")
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.experimental_rerun()

# =============================================
# SVG 아이콘 및 스타일
# =============================================
REFRESH_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M23 4v6h-6"></path>
  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
</svg>
"""

st.markdown(
    """
<style>
.stApp { background: radial-gradient(circle at 20% 20%, #0a0a0f 0%, #000000 100%); color: #fff; }
h1 { color: #ff3333 !important; text-align: center; font-weight: 900; font-size: 4em;
     text-shadow: 0 0 25px #b71c1c, 0 0 15px #00ff99; }
.notice-input-title, .city-input-title, .today-notice-title {
    color: white !important; 
    font-weight: bold; 
    font-size: 1.3em; 
    margin-bottom: 15px;
}
.refresh-btn { background: none; border: 2px solid #00c853; border-radius: 50%; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s; }
.notice-item { background:#1a1a1a; border:2px solid #333; border-radius:12px; padding:12px; margin:8px 0; }
.notice-content { color: #ddd; margin-top: 12px; white-space: pre-line; }
.city-input-form { background: #1a1a1a; border: 2px solid #333; border-radius: 12px; padding: 20px; margin: 20px 0; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(f"<h1>{_['title']} <span class='year'>2025</span><span class='subtitle'>마하라스트라</span> 🎄</h1>", unsafe_allow_html=True)

# =============================================
# 알림 표시
# =============================================
notice_badge()
if check_new_notices() and st.session_state.show_popup:
    try:
        show_alert_popup()
    except Exception:
        # 브라우저 보안 때문에 실패할 수 있음 — 무시
        pass
    st.session_state.show_popup = False

# =============================================
# 좌표 및 거리 함수
# =============================================
coords = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882),
}

def distance_km(p1, p2):
    R = 6371
    lat1, lon1 = radians(p1[0]), radians(p1[1])
    lat2, lon2 = radians(p2[0]), radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    # haversine -> 2*R*asin(sqrt(a)) is numerically stable; use atan2 for safety
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# =============================================
# 공지 삭제
# =============================================

def delete_notice(notice_id):
    st.session_state.notice_data = [n for n in st.session_state.notice_data if n["id"] != notice_id]
    save_json(NOTICE_FILE, st.session_state.notice_data)
    if notice_id in st.session_state.expanded_notices:
        del st.session_state.expanded_notices[notice_id]
    st.success("공지 삭제됨")
    st.experimental_rerun()

# =============================================
# 공지 렌더링 (deterministic keys)
# =============================================

def render_notice_list(show_delete=False):
    if not st.session_state.notice_data:
        st.write("등록된 공지가 없습니다.")
        return

    for n in st.session_state.notice_data:
        notice_id = n["id"]
        is_expanded = st.session_state.expanded_notices.get(str(notice_id), False)
        toggle_key = f"toggle_{notice_id}"

        with st.container():
            if show_delete:
                col1, col2 = st.columns([6, 1])
                with col1:
                    if st.button(f"📢 {n['title']}", key=toggle_key, use_container_width=True):
                        st.session_state.expanded_notices[str(notice_id)] = not is_expanded
                        st.experimental_rerun()
                    st.caption(f"{n.get('timestamp','')[:16].replace('T',' ')}")
                with col2:
                    del_key = f"del_{notice_id}"
                    if st.button("삭제", key=del_key):
                        delete_notice(notice_id)
            else:
                if st.button(f"📢 {n['title']}", key=toggle_key, use_container_width=True):
                    st.session_state.expanded_notices[str(notice_id)] = not is_expanded
                    st.experimental_rerun()
                st.caption(f"{n.get('timestamp','')[:16].replace('T',' ')}")

            if st.session_state.expanded_notices.get(str(notice_id), False):
                st.markdown(f"<div class='notice-content'>{n.get('content','')}</div>", unsafe_allow_html=True)
                if n.get("file"):
                    try:
                        img_bytes = base64.b64decode(n.get("file"))
                        st.image(img_bytes, use_column_width=True)
                    except Exception:
                        st.warning("이미지를 표시할 수 없습니다.")

# =============================================
# 투어 지도 렌더
# =============================================

def render_tour_map():
    st.markdown(
        """
    <div class="map-header">
        <div class="map-title">투어지도</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.expander("투어지도", expanded=False):
        GOOGLE_API_KEY = None
        try:
            GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
        except Exception:
            GOOGLE_API_KEY = None

        # Google key가 없으면 OpenStreetMap tiles로 폴백
        if GOOGLE_API_KEY:
            tiles = f"https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_API_KEY}"
            attr = "Google"
        else:
            tiles = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attr = "OpenStreetMap"

        m = folium.Map(location=(19.75, 75.71), zoom_start=6, tiles=tiles, attr=attr)

        points = [coords[c] for c in st.session_state.route if c in coords]
        if len(points) >= 2:
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]
                dist = distance_km(p1, p2)
                time_hr = dist / 60.0
                mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                folium.Marker(mid, icon=folium.DivIcon(html=f"<div style='color:white;font-size:10pt'>{dist:.1f}km / {time_hr:.1f}h</div>"),).add_to(m)
            AntPath(points, weight=4, delay=800).add_to(m)

        for c in st.session_state.route:
            if c in coords:
                data = st.session_state.venue_data.get(c, {})
                popup = f"<b>{c}</b><br>"
                if "date" in data:
                    popup += f"{data['date']}<br>{data.get('venue','')}<br>Seats: {data.get('seats','')}<br>{data.get('type','')}<br>"
                if data.get("google"):
                    match = re.search(r'@([\d\.]+),([\d\.]+)', data["google"])
                    if match:
                        lat, lng = match.group(1), match.group(2)
                        nav = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
                    else:
                        nav = data["google"]
                    popup += f"<a href='{nav}' target='_blank'>네비 시작</a>"
                folium.Marker(coords[c], popup=popup, icon=folium.Icon(color="red")).add_to(m)

        st_folium(m, width=900, height=600)

# =============================================
# 일반 사용자 화면
# =============================================
if not st.session_state.admin:
    st.markdown(
        f"""
    <div class="today-notice-header">
        <button class="refresh-btn" onclick="window.location.reload(); return false;" title="새로고침">
            <div class="refresh-icon">{REFRESH_SVG}</div>
        </button>
        <div class='today-notice-title'>{_['today_notice']}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    render_notice_list(show_delete=False)
    st.markdown("---")
    render_tour_map()
    st.stop()

# =============================================
# 관리자: 공지 등록 폼
# =============================================
st.markdown(
    f"""
<div class="notice-input-header">
    <div class="notice-input-title">공지사항 입력</div>
    <div>
        <button class="refresh-btn" onclick="window.location.reload(); return false;" title="새로고침">
            <div class="refresh-icon">{REFRESH_SVG}</div>
        </button>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.form("notice_form"):
    title = st.text_input(_["notice_title"])
    content = st.text_area(_["notice_content"])
    uploaded = st.file_uploader(_["upload_file"], type=["png", "jpg", "jpeg"])
    submitted = st.form_submit_button("등록")

if submitted and title:
    new_notice = {
        "id": uuid.uuid4().hex,
        "title": title,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    }
    if uploaded is not None:
        try:
            new_notice["file"] = base64.b64encode(uploaded.read()).decode()
        except Exception:
            st.warning("업로드된 파일을 읽는 중 문제가 발생했습니다.")
    st.session_state.notice_data.insert(0, new_notice)
    save_json(NOTICE_FILE, st.session_state.notice_data)
    st.session_state.show_popup = True
    st.success("공지 등록 완료")
    st.experimental_rerun()

# 공지 목록 (관리자용 삭제 버튼 포함)
render_notice_list(show_delete=True)

# 구분선
st.markdown("<div style='height: 2px; background: linear-gradient(90deg, transparent, #ff6b6b, transparent); margin: 30px 0;'></div>", unsafe_allow_html=True)

# 도시 추가 폼
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
        if not new_city:
            st.error("도시 이름을 입력하세요.")
        elif new_city in st.session_state.venue_data:
            st.error(_["already_exists"])
        else:
            st.session_state.venue_data[new_city] = {
                "venue": venue_name,
                "seats": seats,
                "type": venue_type,
                "google": google_link,
            }
            save_json(VENUE_FILE, st.session_state.venue_data)
            if new_city not in st.session_state.route:
                st.session_state.route.append(new_city)
            st.success(f"{new_city} 추가됨!")
            st.experimental_rerun()

# 투어 지도 (관리자도 볼 수 있게)
st.markdown("---")
render_tour_map()
