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
        "note": "특이사항", "google_link": "구글맵 링크", "perf_date": "공연 날짜",
        "change_pw": "비밀번호 변경", "current_pw": "현재 비밀번호", "new_pw": "새 비밀번호",
        "confirm_pw": "새 비밀번호 확인", "pw_changed": "비밀번호 변경 완료!", "pw_mismatch": "비밀번호 불일치",
        "pw_error": "현재 비밀번호 오류", "select_city": "도시 선택 (클릭)"
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

# --- 4. 캐롤 사운드 (옵션) ---
def play_carol():
    if not st.session_state.sound_played:
        st.session_state.sound_played = True
        st.markdown("""
        <audio autoplay loop>
            <source src="data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAAA" type="audio/wav">
        </audio>
        """, unsafe_allow_html=True)

# --- 5. UI (화면 가림 완전 해결) ---
st.markdown("""
<style>
    /* Streamlit 기본 컨테이너 강제 오버플로우 허용 */
    .main > div {
        overflow: visible !important;
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
        z-index: 10;
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
        z-index: 10;
        position: relative;
    }

    /* 공지 */
    .streamlit-expanderHeader {
        background: #006400 !important;
        color: #FFFFFF !important;
        border: 2px solid #FFD700;
        border-radius: 12px;
        padding: 14px 18px;
        font-size: 1.05em;
        position: relative;
        z-index: 5;
    }
    .streamlit-expander {
        background: rgba(0, 100, 0, 0.7) !important;
        border: 2px solid #FFD700;
        border-radius: 12px;
        margin-bottom: 14px;
        position: relative;
        z-index: 5;
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
        z-index: 5;
    }

    /* 사이드바 */
    .css-1d391kg {
        background: #000000 !important;
        border-right: 3px solid #FFD700 !important;
        z-index: 10;
    }

    /* 크리스마스 요소 (내용 위) */
    .christmas-element {
        position: fixed !important;
        z-index: 1 !important;
        pointer-events: none !important;
        user-select: none !important;
    }

    /* 별 (배경) */
    .star {
        position: fixed !important;
        background: #ffffff;
        border-radius: 50%;
        animation: twinkle 3s infinite;
        pointer-events: none !important;
        z-index: 0 !important;
    }
    @keyframes twinkle { 0%,100% { opacity: 0.5; } 50% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# --- 6. 크리스마스 요소 & 별 (스크롤 방지 + 화면 가림 해결) ---
st.markdown("""
<script>
    // DOM 로드 후 실행
    window.addEventListener('load', () => {
        const body = document.body;

        // 별 생성
        function createStar() {
            const star = document.createElement('div');
            star.className = 'star';
            star.style.width = Math.random() * 3 + 'px';
            star.style.height = star.style.width;
            star.style.left = Math.random() * 100 + 'vw';
            star.style.top = Math.random() * 100 + 'vh';
            star.style.animationDelay = Math.random() * 3 + 's';
            body.appendChild(star);
            setTimeout(() => star.remove(), 10000);
        }

        // 크리스마스 요소
        const elements = [
            {html: '🎄', style: 'bottom:10%;left:5%;font-size:4em;animation:float 6s infinite;'},
            {html: '🎁', style: 'bottom:15%;right:8%;font-size:2.5em;animation:sway 4s infinite;'},
            {html: '🔔', style: 'top:15%;left:10%;font-size:2em;animation:ring 3s infinite;'},
            {html: '🧦', style: 'top:20%;right:12%;font-size:2.5em;animation:hop 3.5s infinite;'},
            {html: '🍭', style: 'bottom:18%;left:12%;font-size:2em;animation:hop 4s infinite;'},
            {html: '🦌', style: 'top:25%;left:50%;font-size:2.5em;animation:hop 3s infinite;'},
            {html: '🎅🛷', style: 'top:8%;font-size:2em;animation:slide 25s linear infinite;'}
        ];
        elements.forEach(e => {
            const el = document.createElement('div');
            el.className = 'christmas-element';
            el.innerHTML = e.html;
            el.style.cssText = e.style;
            body.appendChild(el);
        });

        // 애니메이션 정의
        const style = document.createElement('style');
        style.innerHTML = `
            @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-15px); } }
            @keyframes sway { 0%,100% { transform: rotate(-5deg); } 50% { transform: rotate(5deg); } }
            @keyframes ring { 0%,100% { transform: rotate(-15deg); } 50% { transform: rotate(15deg); } }
            @keyframes hop { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
            @keyframes slide { 0% { transform: translateX(-100vw); } 100% { transform: translateX(100vw); } }
        `;
        document.head.appendChild(style);

        // 주기적 별 생성
        for(let i=0; i<150; i++) createStar();
        setInterval(() => { for(let i=0; i<5; i++) createStar(); }, 1000);
    });
</script>
""", unsafe_allow_html=True)

# --- 7. 제목 ---
st.markdown("""
<div class="main-title">
    <span class="cantata">칸타타 투어</span> <span class="year">2025</span>
    <div class="maharashtra">마하라스트라</div>
</div>
""", unsafe_allow_html=True)

# --- 8. 나머지 코드 (기존과 동일) ---
# (공지, 지도, 탭 등은 이전 버전 그대로)

# --- 9. 초기 도시 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도",
     "google_link": "https://goo.gl/maps/abc123", "indoor": False, "date": "11/07 02:01"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브",
     "google_link": "https://goo.gl/maps/def456", "indoor": True, "date": "11/07 02:01"},
    {"city": "Pune", "venue": "Aga Khan Palace", "seats": "2500", "note": "역사적 장소",
     "google_link": "https://goo.gl/maps/pune2", "indoor": False, "date": "11/08 14:00"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시",
     "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "date": "11/07 02:01"}
]
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

CITY_COORDS = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882)
}

# --- 10. 공지 기능 ---
def add_notice(title, content, img=None, file=None):
    # ... (기존 코드 그대로)
    pass

# --- 11. render_notices, render_map 등 ---
# (기존 코드 복사)

# --- 12. 탭 ---
col1, col2 = st.columns(2)
with col1:
    if st.button(_(f"tab_notice"), use_container_width=True):
        st.session_state.tab_selection = _(f"tab_notice")
        st.rerun()
with col2:
    if st.button(_(f"tab_map"), use_container_width=True):
        st.session_state.tab_selection = _(f"tab_map")
        st.rerun()

# --- 13. 렌더링 ---
if st.session_state.tab_selection == _(f"tab_notice"):
    # ... 공지 렌더링
else:
    # ... 지도 렌더링
