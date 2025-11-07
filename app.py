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

# --- 4. 화면 가림 완전 해결 + 구글맵 타일 ---
st.markdown("""
<style>
    /* Streamlit 전체 강제 오버플로우 허용 */
    html, body, [data-testid="stAppViewContainer"], .main > div, .block-container {
        overflow: visible !important;
        position: relative !important;
    }
    .stApp {
        overflow: visible !important;
        background: #000000;
        color: #ffffff;
        font-family: 'Playfair Display', serif;
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

    /* 구글맵 타일용 */
    .folium-map {
        width: 100% !important;
        height: 600px !important;
        z-index: 10 !important;
    }

    /* 눈 결정체 (내용 아래) */
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

<script>
    document.addEventListener('DOMContentLoaded', () => {
        const container = document.body;
        function createSnow() {
            const snow = document.createElement('div');
            snow.className = 'snowflake';
            snow.innerHTML = ['❄', '❅', '❆'][Math.floor(Math.random() * 3)];
            snow.style.left = Math.random() * 100 + 'vw';
            snow.style.animationDuration = Math.random() * 8 + 7 + 's';
            snow.style.opacity = Math.random() * 0.3 + 0.3;
            snow.style.fontSize = Math.random() * 12 + 12 + 'px';
            container.appendChild(snow);
            setTimeout(() => snow.remove(), 15000);
        }
        setInterval(createSnow, 300);
    });
</script>
""", unsafe_allow_html=True)

# --- 5. 제목 ---
st.markdown("""
<div class="main-title">
    <span class="cantata">칸타타 투어</span> <span class="year">2025</span>
    <div class="maharashtra">마하라스트라</div>
</div>
""", unsafe_allow_html=True)

# --- 6. 사이드바 ---
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

# --- 7. JSON 헬퍼 ---
def load_json(f):
    return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []

def save_json(f, d):
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 8. 전체 도시 & 좌표 (70개) ---
coords = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
    "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Amravati": (20.93, 77.75),
    "Nanded": (19.16, 77.31), "Kolhapur": (16.70, 74.24), "Akola": (20.70, 77.00), "Latur": (18.40, 76.18),
    "Ahmadnagar": (19.10, 74.75), "Jalgaon": (21.00, 75.57), "Dhule": (20.90, 74.77), "Ichalkaranji": (16.69, 74.47),
    "Malegaon": (20.55, 74.53), "Bhusawal": (21.05, 76.00), "Bhiwandi": (19.30, 73.06), "Bhandara": (21.17, 79.65),
    "Beed": (18.99, 75.76), "Buldana": (20.54, 76.18), "Chandrapur": (19.95, 79.30), "Dharashiv": (18.40, 76.57),
    "Gondia": (21.46, 80.19), "Hingoli": (19.72, 77.15), "Jalna": (19.85, 75.89), "Mira-Bhayandar": (19.28, 72.87),
    "Nandurbar": (21.37, 74.22), "Osmanabad": (18.18, 76.07), "Palghar": (19.70, 72.77), "Parbhani": (19.27, 76.77),
    "Ratnagiri": (16.99, 73.31), "Sangli": (16.85, 74.57), "Satara": (17.68, 74.02), "Sindhudurg": (16.24, 73.42),
    "Wardha": (20.75, 78.60), "Washim": (20.11, 77.13), "Yavatmal": (20.39, 78.12), "Kalyan-Dombivli": (19.24, 73.13),
    "Ulhasnagar": (19.22, 73.16), "Vasai-Virar": (19.37, 72.81), "Sangli-Miraj-Kupwad": (16.85, 74.57), "Nanded-Waghala": (19.16, 77.31),
    "Bandra (Mumbai)": (19.06, 72.84), "Colaba (Mumbai)": (18.92, 72.82), "Andheri (Mumbai)": (19.12, 72.84),
    "Navi Mumbai": (19.03, 73.00), "Pimpri-Chinchwad (Pune)": (18.62, 73.80), "Kothrud (Pune)": (18.50, 73.81), "Hadapsar (Pune)": (18.51, 73.94),
    "Pune Cantonment": (18.50, 73.89), "Nashik Road": (20.00, 73.79), "Deolali (Nashik)": (19.94, 73.82), "Satpur (Nashik)": (20.01, 73.79),
    "Aurangabad City": (19.88, 75.34), "Jalgaon City": (21.00, 75.57), "Nagpur City": (21.15, 79.08), "Sitabuldi (Nagpur)": (21.14, 79.08),
    "Jaripatka (Nagpur)": (21.12, 79.07), "Solapur City": (17.67, 75.91), "Pandharpur (Solapur)": (17.66, 75.32), "Amravati City": (20.93, 77.75),
    "Badnera (Amravati)": (20.84, 77.73), "Akola City": (20.70, 77.00), "Washim City": (20.11, 77.13), "Yavatmal City": (20.39, 78.12),
    "Wardha City": (20.75, 78.60), "Chandrapur City": (19.95, 79.30), "Gadchiroli": (20.09, 80.11), "Gondia City": (21.46, 80.19),
    "Bhandara City": (21.17, 79.65), "Gadhinglaj (Kolhapur)": (16.23, 74.34), "Kagal (Kolhapur)": (16.57, 74.31)
}

# --- 9. 초기 도시 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "indoor": False},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "indoor": True},
    {"city": "Pune", "venue": "Aga Khan Palace", "seats": "2500", "indoor": False},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "indoor": False}
]
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

# --- 10. 공지 & 지도 (구글맵 타일 사용) ---
def render_notices():
    st.write("공지 내용이 여기에 표시됩니다.")

def render_map():
    st.subheader("경로 보기")
    raw_cities = load_json(CITY_FILE)
    cities = sorted(raw_cities, key=lambda x: x.get("perf_date", "9999-12-31"))

    # 구글맵 타일 사용
    m = folium.Map(
        location=[18.5204, 73.8567],
        zoom_start=7,
        tiles="https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Maps"
    )
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        overlay=True,
        control=True
    ).add_to(m)

    for i, c in enumerate(cities):
        city_name = c["city"]
        coords_tuple = coords.get(city_name, (18.5204, 73.8567))
        indoor_text = "실내" if c.get("indoor") else "실외"
        perf_date_formatted = c.get("perf_date", "미정")

        popup_html = f"""
        <div style="font-size: 14px; line-height: 1.6; color: #000000;">
            <b>{city_name}</b><br>
            <b>날짜:</b> <strong>{perf_date_formatted}</strong><br>
            <b>장소:</b> <strong>{c.get('venue','—')}</strong><br>
            <b>예상 인원:</b> <strong>{c.get('seats','—')}</strong><br>
            <b>장소:</b> <strong>{indoor_text}</strong>
        </div>
        """
        folium.Marker(
            coords_tuple,
            popup=folium.Popup(popup_html, max_width=320),
            icon=folium.Icon(color="red", icon="music", prefix="fa")
        ).add_to(m)

        if i < len(cities) - 1:
            next_city = cities[i + 1]["city"]
            next_coords = coords.get(next_city, (18.5204, 73.8567))
            AntPath([coords_tuple, next_coords], color="#FFD700", weight=5, opacity=0.8).add_to(m)

    st_folium(m, width=900, height=600, key="google_map")

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
