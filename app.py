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

# --- 7. CSS: 크리스마스 애니메이션 폭발 ---
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
    [data-testid="stAppViewContainer"]::before {
        content: ''; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0;
        background: linear-gradient(135deg, rgba(0,0,50,0.8), rgba(0,0,20,0.9));
        animation: snowbg 20s linear infinite;
    }
    @keyframes snowbg { 0% { background-position: 0 0; } 100% { background-position: 100% 100%; } }

    /* 크리스마스 아이콘: 반짝임 + 회전 */
    .christmas-decoration {
        position: fixed; top: 2vh; left: 0; width: 100%; z-index: 1001;
        display: flex; justify-content: center; gap: 12px; flex-wrap: nowrap; pointer-events: none;
    }
    .christmas-decoration i {
        color: #fff; text-shadow: 0 0 15px #fff, 0 0 30px #ff0, 0 0 45px #f00;
        animation: float 3s ease-in-out infinite, sparkle 2s infinite alternate;
        opacity: 0.95;
    }
    @keyframes sparkle {
        0%, 100% { text-shadow: 0 0 15px #fff, 0 0 30px #ff0, 0 0 45px #f00; }
        50% { text-shadow: 0 0 20px #fff, 0 0 40px #ff0, 0 0 60px #f00, 0 0 80px #f00; }
    }

    /* 제목: 빛나는 효과 */
    .main-title {
        font-size: 2.8em !important; font-weight: bold; text-align: center;
        margin: 12vh 0 10px 0 !important; line-height: 1.2; z-index: 1000;
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { text-shadow: 0 0 10px #fff, 0 0 20px #fff, 0 0 30px #c62828; }
        to { text-shadow: 0 0 20px #fff, 0 0 30px #fff, 0 0 40px #c62828, 0 0 50px #c62828; }
    }

    /* 버튼: 호버 시 눈송이 폭발 */
    .tab-btn {
        position: relative; overflow: hidden;
        background: rgba(255,255,255,0.96); color: #c62828; border: none;
        border-radius: 20px; padding: 10px 20px; font-weight: bold;
        font-size: 1.1em; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: all 0.3s ease; flex: 1; max-width: 200px;
    }
    .tab-btn:hover { background: #d32f2f; color: white; transform: translateY(-2px); }
    .tab-btn::after {
        content: '❄❄❄'; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) scale(0);
        font-size: 1.5em; opacity: 0; transition: all 0.3s ease;
    }
    .tab-btn:hover::after { transform: translate(-50%, -50%) scale(3); opacity: 1; }

    /* 눈송이: 100개 + 부드러운 낙하 */
    .snowflake {
        position: fixed; top: -20px; color: #fff; font-size: 1.2em; pointer-events: none;
        animation: fall linear infinite; opacity: 0.7; z-index: 1; text-shadow: 0 0 5px #fff;
    }
    @keyframes fall { 0% { transform: translateY(0) rotate(0deg); opacity: 0.7; } 100% { transform: translateY(120vh) rotate(360deg); opacity: 0; } }

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

# --- 크리스마스 아이콘 (반짝임) ---
st.markdown('''
<div class="christmas-decoration">
    <i class="fas fa-gift"></i>
    <i class="fas fa-candy-cane"></i>
    <i class="fas fa-socks"></i>
    <i class="fas fa-sleigh"></i>
    <i class="fas fa-deer"></i>
    <i class="fas fa-tree"></i>
    <i class="fas fa-bell"></i>
</div>
''', unsafe_allow_html=True)

# --- 눈송이 100개 (부드러운 낙하) ---
for i in range(100):
    left = random.randint(0, 100)
    duration = random.randint(8, 25)
    size = random.uniform(0.6, 1.6)
    delay = random.uniform(0, 15)
    st.markdown(f"<div class='snowflake' style='left:{left}vw; animation-duration:{duration}s; font-size:{size}em; animation-delay:{delay}s;'>❄</div>", unsafe_allow_html=True)

# --- 제목 (빛나는 효과) ---
title_html = f'<h1 class="main-title"><span style="color:red;">{_("title_cantata")}</span> <span style="color:white;">{_("title_year")}</span> <span style="color:green; font-size:67%;">{_("title_region")}</span></h1>'
st.markdown(title_html, unsafe_allow_html=True)

# --- 버튼 라인 (눈송이 폭발) ---
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

# --- 공지/지도 (기존 코드 유지) ---
# ... (생략, 이전 코드 그대로)

# --- 모바일 햄버거 + 사이드바 ---
# ... (생략, 이전 코드 그대로)
