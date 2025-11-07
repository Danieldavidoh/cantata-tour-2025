import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from pytz import timezone
from streamlit_autorefresh import st_autorefresh

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
LANG = {
    "ko": {
        "tab_notice": "공지", "tab_map": "투어 경로", "today": "오늘", "yesterday": "어제",
        "new_notice_alert": "새 공지가 도착했어요!", "warning": "제목·내용 입력",
        "edit": "수정", "save": "저장", "cancel": "취소", "add_city": "도시 추가",
        "indoor": "실내", "outdoor": "실외", "venue": "장소", "seats": "예상 인원",
        "note": "특이사항", "google_link": "구글맵 링크", "perf_date": "공연 날짜"
    }
}

defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "adding_city": False,
    "tab_selection": "공지", "new_notice": False, "sound_played": False,
    "seen_notices": [], "expanded_notices": [], "expanded_cities": [],
    "last_tab": None, "alert_active": False, "current_alert_id": None,
    "password": "0009", "show_pw_form": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 4. UI + 투명 눈 결정체 (화면 가림 완전 해결) ---
st.markdown("""
<style>
    /* Streamlit 전체 컨테이너 강제 오버플로우 허용 */
    .main > div {
        overflow: visible !important;
    }
    .stApp {
        overflow: visible !important;
        background: #000000;
        color: #ffffff;
        font-family: 'Playfair Display', serif;
        position: relative;
    }

    /* 제목 */
    .main-title {
        text-align: center;
        margin: 20px 0 40px;
        line-height: 1.2;
        position: relative;
        z-index: 20;
    }
    .main-title .cantata { color: #DC143C; font-size: 2.8em; font-weight: 700; text-shadow: 0 0 15px #FFD700; }
    .main-title .year { color: #FFFFFF; font-size: 2.8em; font-weight: 700; text-shadow: 0 0 15px #FFFFFF; }
    .main-title .maharashtra { color: #D3D3D3; font-size: 1.8em; font-style: italic; display: block; margin-top: -10px; }

    /* 탭 버튼 */
    .stButton > button {
        background: #8B0000 !important;
        color: #FFFFFF !important;
        border: 2px solid #FFD700 !important;
        border-radius: 14px !important;
        padding: 14px 30px !important;
        font-weight: 600;
        font-size: 1.1em;
        box-shadow: 0 4px 20px rgba(255, 215, 0, 0.3);
        z-index: 20;
        position: relative;
    }
    .stButton > button:hover {
        background: #B22222 !important;
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(255, 215, 0, 0.5);
    }

    /* 공지 */
    .streamlit-expanderHeader {
        background: #006400 !important;
        color: #FFFFFF !important;
        border: 2px solid #FFD700;
        border-radius: 12px;
        padding: 14px 18px;
        font-size: 1.05em;
        z-index: 15;
        position: relative;
    }
    .streamlit-expander {
        background: rgba(0, 100, 0, 0.7) !important;
        border: 2px solid #FFD700;
        border-radius: 12px;
        margin-bottom: 14px;
        z-index: 15;
        position: relative;
    }

    /* 입력 폼 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        background: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #DC143C !important;
        border-radius: 10px;
        z-index: 15;
        position: relative;
    }

    /* 사이드바 */
    .css-1d391kg {
        background: #000000 !important;
        border-right: 3px solid #FFD700 !important;
        z-index: 20;
    }

    /* 투명한 눈 결정체 (내용 아래) */
    .snowflake {
        position: fixed !important;
        color: rgba(255, 255, 255, 0.5) !important;
        font-size: 1.5em;
        pointer-events: none !important;
        user-select: none !important;
        z-index: -1 !important;
        animation: fall linear forwards;
    }
    @keyframes fall {
        to { transform: translateY(120vh) rotate(720deg); opacity: 0; }
    }
</style>
""", unsafe_allow_html=True)

# --- 5. 투명한 눈 결정체 스크립트 (DOM 로드 후 실행) ---
st.markdown("""
<script>
    document.addEventListener('DOMContentLoaded', () => {
        const body = document.body;
        function createSnow() {
            const snow = document.createElement('div');
            snow.className = 'snowflake';
            snow.innerHTML = ['❄', '❅', '❆'][Math.floor(Math.random() * 3)];
            snow.style.left = Math.random() * 100 + 'vw';
            snow.style.animationDuration = Math.random() * 8 + 7 + 's';
            snow.style.opacity = Math.random() * 0.3 + 0.3;
            snow.style.fontSize = Math.random() * 12 + 12 + 'px';
            body.appendChild(snow);
            setTimeout(() => snow.remove(), 15000);
        }
        setInterval(createSnow, 300);
    });
</script>
""", unsafe_allow_html=True)

# --- 6. 제목 ---
st.markdown("""
<div class="main-title">
    <span class="cantata">칸타타 투어</span> <span class="year">2025</span>
    <div class="maharashtra">마하라스트라</div>
</div>
""", unsafe_allow_html=True)

# --- 7. 사이드바 ---
with st.sidebar:
    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if pw == st.session_state.password:
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃"):
            st.session_state.admin = False
            st.rerun()

# --- 8. JSON 헬퍼 ---
def load_json(f):
    return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []

def save_json(f, d):
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 9. 초기 도시 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "indoor": False},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "indoor": True},
    {"city": "Pune", "venue": "Aga Khan Palace", "seats": "2500", "indoor": False},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "indoor": False}
]
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

CITY_COORDS = {"Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567), "Nagpur": (21.1458, 79.0882)}

# --- 10. 공지 & 지도 ---
def render_notices():
    st.write("공지 내용이 여기에 표시됩니다.")

def render_map():
    st.subheader("경로 보기")
    m = folium.Map(location=[18.5204, 73.8567], zoom_start=7)
    raw_cities = load_json(CITY_FILE)
    for c in raw_cities:
        coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
        folium.Marker(coords, popup=c["city"]).add_to(m)
    st_folium(m, width=900, height=550)

# --- 11. 탭 ---
col1, col2 = st.columns(2)
with col1:
    if st.button("공지", use_container_width=True):
        st.session_state.tab_selection = "공지"
        st.rerun()
with col2:
    if st.button("투어 경로", use_container_width=True):
        st.session_state.tab_selection = "투어 경로"
        st.rerun()

# --- 12. 렌더링 ---
if st.session_state.tab_selection == "공지":
    render_notices()
else:
    render_map()
