# app.py
import json, os, uuid, base64, random
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
    "ko": {"title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
           "tab_notice": "공지", "tab_map": "투어 경로", "indoor": "실내", "outdoor": "실외",
           "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵",
           "perf_date": "공연 날짜", "warning": "제목·내용 입력", "delete": "제거",
           "menu": "메뉴", "login": "로그인", "logout": "로그아웃"},
    "en": {"title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
           "tab_notice": "Notice", "tab_map": "Tour Route", "indoor": "Indoor", "outdoor": "Outdoor",
           "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps",
           "perf_date": "Performance Date", "warning": "Enter title & content", "delete": "Remove",
           "menu": "Menu", "login": "Login", "logout": "Logout"},
    "hi": {"title_cantata": "कैंटाटा टूर", "title_year": "2025", "title_region": "महाराष्ट्र",
           "tab_notice": "सूचना", "tab_map": "टूर मार्ग", "indoor": "इनडोर", "outdoor": "आउटडोर",
           "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप",
           "perf_date": "प्रदर्शन तिथि", "warning": "शीर्षक·सामग्री दर्ज करें", "delete": "हटाएं",
           "menu": "मेनू", "login": "लॉगिन", "logout": "लॉगआउट"}
}
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False, "adding_city": False}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- JSON 헬퍼 ---
def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 기본 도시 및 좌표 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도",
     "google_link": "https://goo.gl/maps/abc123", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-10"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브",
     "google_link": "https://goo.gl/maps/def456", "indoor": True, "date": "11/07 02:01", "perf_date": "2025-11-12"},
    {"city": "Pune", "venue": "Aga Khan Palace", "seats": "2500", "note": "역사적 장소",
     "google_link": "https://goo.gl/maps/pune2", "indoor": False, "date": "11/08 14:00", "perf_date": "2025-11-14"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시",
     "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-16"}
]
if not os.path.exists(CITY_FILE): save_json(CITY_FILE, DEFAULT_CITIES)
CITY_COORDS = {"Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567), "Nagpur": (21.1458, 79.0882)}

# --- CSS: 모든 요소를 한 화면에 상단 고정 배치 ---
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
[data-testid="stAppViewContainer"] {
    background: url("background_christmas_dark.png");
    background-size: cover; background-position: center;
    background-attachment: fixed; height: 100vh; overflow: hidden;
}
section.main { padding: 0 !important; margin: 0 !important; height: 100vh; overflow: hidden; }
.header-container { text-align: center; margin: 0; padding: 0; }
.christmas-decoration {
    display: flex; justify-content: center; gap: 12px; margin-bottom: 0;
}
.christmas-decoration i { color:#fff; text-shadow:0 0 10px rgba(255,255,255,0.6); animation: float 3s ease-in-out infinite; opacity:0.95; }
@keyframes float {0%,100%{transform:translateY(0);}50%{transform:translateY(-6px);} }
.main-title {
    font-size: 2.4em !important; font-weight: bold; text-align: center;
    text-shadow: 0 3px 8px rgba(0,0,0,0.6);
    margin: 0; padding: 0;
}
.button-row { display: flex; justify-content: center; gap: 10px; margin: 5px 0; }
.tab-btn {
    background: rgba(255,255,255,0.96); color: #c62828; border: none;
    border-radius: 20px; padding: 8px 15px; font-weight: bold; font-size: 1em;
    cursor: pointer; transition: all 0.3s ease;
}
.tab-btn:hover { background: #d32f2f; color: white; transform: translateY(-2px); }
.notice-container, .map-container {
    height: 65vh; overflow-y: auto; margin-top: 5px; padding: 10px;
    background: rgba(255,255,255,0.15); border-radius: 10px;
}
.snowflake {
    position:fixed; top:-15px; color:#fff; font-size:1em; pointer-events:none;
    animation:fall linear infinite; opacity:0.4; z-index:1;
}
@keyframes fall {0%{transform:translateY(0);}100%{transform:translateY(110vh);} }
</style>
""", unsafe_allow_html=True)

# --- 눈 효과 ---
for i in range(40):
    left = random.randint(0, 100)
    duration = random.randint(10, 20)
    size = random.uniform(0.7, 1.3)
    delay = random.uniform(0, 8)
    st.markdown(
        f"<div class='snowflake' style='left:{left}vw; animation-duration:{duration}s; font-size:{size}em; animation-delay:{delay}s;'>❄</div>",
        unsafe_allow_html=True
    )

# --- 헤더 ---
st.markdown('<div class="header-container">', unsafe_allow_html=True)
st.markdown('''
<div class="christmas-decoration">
    <i class="fas fa-gift"></i><i class="fas fa-candy-cane"></i><i class="fas fa-socks"></i>
    <i class="fas fa-sleigh"></i><i class="fas fa-deer"></i><i class="fas fa-tree"></i><i class="fas fa-bell"></i>
</div>
''', unsafe_allow_html=True)
st.markdown(
    f'<h1 class="main-title"><span style="color:red;">{_("title_cantata")}</span> '
    f'<span style="color:white;">{_("title_year")}</span> '
    f'<span style="color:green; font-size:65%;">{_("title_region")}</span></h1>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# --- 버튼 행 ---
st.markdown('<div class="button-row">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])
with col1:
    if st.button(_("tab_notice"), use_container_width=True):
        st.session_state.notice_open = True
        st.session_state.map_open = False
        st.rerun()
with col2:
    if st.button(_("tab_map"), use_container_width=True):
        st.session_state.map_open = True
        st.session_state.notice_open = False
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- 공지 영역 ---
if st.session_state.notice_open:
    st.markdown('<div class="notice-container">', unsafe_allow_html=True)
    data = load_json(NOTICE_FILE)
    if st.session_state.admin:
        with st.expander("공지 작성"):
            with st.form("notice_form", clear_on_submit=True):
                title = st.text_input("제목")
                content = st.text_area("내용")
                if st.form_submit_button("등록"):
                    if title.strip() and content.strip():
                        notice = {
                            "id": str(uuid.uuid4()), "title": title, "content": content,
                            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                        }
                        data.insert(0, notice)
                        save_json(NOTICE_FILE, data)
                        st.rerun()
                    else:
                        st.warning(_("warning"))
    for i, n in enumerate(data):
        with st.expander(f"{n['date']} | {n['title']}"):
            st.markdown(n["content"])
            if st.session_state.admin and st.button(_("delete"), key=f"del_{i}"):
                data.pop(i); save_json(NOTICE_FILE, data); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 지도 영역 ---
if st.session_state.map_open:
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    cities = load_json(CITY_FILE)
    m = folium.Map(location=[18.5204, 73.8567], zoom_start=7)
    for i, c in enumerate(cities):
        coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
        folium.Marker(coords, tooltip=c["city"]).add_to(m)
    st_folium(m, width=900, height=400)
    st.markdown('</div>', unsafe_allow_html=True)
