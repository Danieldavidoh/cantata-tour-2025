import json, os, uuid, base64, random
import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh

# --- 기본 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

LANG = {
    "ko": {"title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
           "tab_notice": "공지", "tab_map": "투어 경로", "indoor": "실내", "outdoor": "실외",
           "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵",
           "warning": "도시와 장소를 입력하세요", "delete": "제거", "menu": "메뉴", "login": "로그인", "logout": "로그아웃"},
}

defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 파일 유틸 ---
def load_json(f):
    try:
        if os.path.exists(f):
            return json.load(open(f, "r", encoding="utf-8"))
    except Exception:
        pass
    return []

def save_json(f, d):
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 기본 도시 데이터 ---
CITY_OPTIONS = ["Mumbai", "Pune", "Nagpur"]
CITY_COORDS = {
    "Mumbai": (19.07609, 72.877426),
    "Pune": (18.52043, 73.856743),
    "Nagpur": (21.1458, 79.088154),
}
DEFAULT_CITIES = [
    {"city": city, "venue": "공연 없음", "seats": "", "note": "", "google_link": "",
     "indoor": False, "date": "", "perf_date": "공연 없음",
     "lat": CITY_COORDS[city][0], "lon": CITY_COORDS[city][1]}
    for city in CITY_OPTIONS
]

# --- 도시 데이터 로드 (문제 자동 복구) ---
def load_cities():
    cities = load_json(CITY_FILE)
    if not isinstance(cities, list) or not cities:
        save_json(CITY_FILE, DEFAULT_CITIES)
        return DEFAULT_CITIES
    fixed = []
    for c in cities:
        if not isinstance(c, dict) or "city" not in c:
            continue
        city = c.get("city")
        if not city or city not in CITY_COORDS:
            continue
        fixed.append({
            "city": city,
            "venue": c.get("venue", "공연 없음"),
            "seats": c.get("seats", ""),
            "note": c.get("note", ""),
            "google_link": c.get("google_link", ""),
            "indoor": c.get("indoor", False),
            "date": c.get("date", ""),
            "perf_date": c.get("perf_date", "공연 없음"),
            "lat": c.get("lat", CITY_COORDS[city][0]),
            "lon": c.get("lon", CITY_COORDS[city][1])
        })
    if not fixed:
        fixed = DEFAULT_CITIES
    save_json(CITY_FILE, fixed)
    return fixed

# --- CSS & 눈 효과 ---
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: url("background_christmas_dark.png"); background-size: cover; }
.main-title { font-size: 2.8em; text-align: center; font-weight: bold; text-shadow: 0 3px 8px rgba(0,0,0,0.6); }
.button-row { display: flex; justify-content: center; gap: 20px; margin-top: 0 !important; }
.tab-btn { background: rgba(255,255,255,0.95); color: #c62828; border-radius: 20px; padding: 10px 20px; font-weight: bold; cursor: pointer; }
</style>
""", unsafe_allow_html=True)
for i in range(40):
    st.markdown(f"<div style='position:fixed; top:-10px; left:{random.randint(0,100)}vw; color:white; opacity:0.4; animation:fall {random.randint(10,18)}s linear infinite;'>❄</div>", unsafe_allow_html=True)

# --- 헤더 ---
st.markdown(f"<h1 class='main-title'>{_('title_cantata')} {_('title_year')} {_('title_region')}</h1>", unsafe_allow_html=True)

# --- 탭 버튼 ---
st.markdown('<div class="button-row">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    if st.button(_("tab_notice")):
        st.session_state.notice_open = not st.session_state.notice_open
        st.session_state.map_open = False
        st.rerun()
with c2:
    if st.button(_("tab_map")):
        st.session_state.map_open = not st.session_state.map_open
        st.session_state.notice_open = False
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- 공지 탭 ---
if st.session_state.notice_open:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            title = st.text_input("제목")
            content = st.text_area("내용")
            if st.form_submit_button("등록"):
                if title.strip() and content.strip():
                    notices = load_json(NOTICE_FILE)
                    notices.insert(0, {
                        "id": str(uuid.uuid4()),
                        "title": title,
                        "content": content,
                        "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                    })
                    save_json(NOTICE_FILE, notices)
                    st.success("등록 완료")
                    st.rerun()
    for n in load_json(NOTICE_FILE):
        with st.expander(f"{n['date']} | {n['title']}"):
            st.markdown(n["content"])

# --- 지도 탭 ---
if st.session_state.map_open:
    cities = load_cities()
    m = folium.Map(location=[18.52, 73.85], zoom_start=7)
    for i, c in enumerate(cities):
        color = "gray" if c.get("perf_date") and c["perf_date"] != "공연 없음" else "red"
        folium.Marker(
            (c["lat"], c["lon"]),
            popup=f"<b>{c['city']}</b><br>{_('venue')}: {c['venue']}<br>{_('seats')}: {c['seats'] or '—'}<br>{_('note')}: {c['note'] or '—'}",
            icon=folium.Icon(color=color, icon="music", prefix="fa")
        ).add_to(m)
        if i < len(cities) - 1:
            nxt = cities[i + 1]
            AntPath([(c["lat"], c["lon"]), (nxt["lat"], nxt["lon"])], color="#e74c3c", weight=5).add_to(m)
    st_folium(m, width=900, height=550)

# --- 사이드바 ---
with st.sidebar:
    if not st.session_state.admin:
        pw = st.text_input("관리자 비밀번호", type="password")
        if st.button("로그인"):
            if pw == "0009":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃"):
            st.session_state.admin = False
            st.rerun()
