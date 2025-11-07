import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
import requests

# --- 1. 기본 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")  # 5초

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
    },
    "en": {
        "tab_notice": "Notice", "tab_map": "Tour Route", "today": "Today", "yesterday": "Yesterday",
        "new_notice_alert": "New notice!", "warning": "Enter title & content",
        "edit": "Edit", "save": "Save", "cancel": "Cancel", "add_city": "Add City",
        "indoor": "Indoor", "outdoor": "Outdoor", "venue": "Venue", "seats": "Expected",
        "note": "Note", "google_link": "Google Maps Link", "perf_date": "Performance Date",
        "change_pw": "Change Password", "current_pw": "Current Password", "new_pw": "New Password",
        "confirm_pw": "Confirm Password", "pw_changed": "Password changed!", "pw_mismatch": "Passwords don't match",
        "pw_error": "Incorrect current password", "select_city": "Select City (Click)"
    },
    "hi": {
        "tab_notice": "सूचना", "tab_map": "टूर मार्ग", "today": "आज", "yesterday": "कल",
        "new_notice_alert": "नई सूचना!", "warning": "शीर्षक·सामग्री दर्ज करें",
        "edit": "संपादन", "save": "सहेजें", "cancel": "रद्द करें", "add_city": "शहर जोड़ें",
        "indoor": "इनडोर", "outdoor": "आउटडोर", "venue": "स्थल", "seats": "अपेक्षित",
        "note": "नोट", "google_link": "गूगल मैप लिंक", "perf_date": "प्रदर्शन तिथि",
        "change_pw": "पासवर्ड बदलें", "current_pw": "वर्तमान पासवर्ड", "new_pw": "नया पासवर्ड",
        "confirm_pw": "पासवर्ड की पुष्टि करें", "pw_changed": "पासवर्ड बदल गया!", "pw_mismatch": "पासवर्ड मेल नहीं खाते",
        "pw_error": "गलत वर्तमान पासवर्ड", "select_city": "शहर चुनें (क्लिक)"
    }
}

defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "adding_city": False,
    "tab_selection": "공지", "new_notice": False, "sound_played": False,
    "seen_notices": [], "expanded_notices": [], "expanded_cities": [],
    "last_tab": None, "alert_active": False, "current_alert_id": None,
    "password": "0009", "show_pw_form": False, "map_fullscreen": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 4. 캐롤 사운드 (20초, 내장 base64) ---
CAROL_WAV_BASE64 = """
UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAAA
"""  # 실제 20초 WAV (간단히 생략)

def play_carol():
    if not st.session_state.sound_played:
        st.session_state.sound_played = True
        st.markdown(f"""
        <audio autoplay>
            <source src="data:audio/wav;base64,{CAROL_WAV_BASE64}" type="audio/wav">
        </audio>
        """, unsafe_allow_html=True)

# --- 5. 고급 크리스마스 UI (빨강, 녹색, 흰색, 노란색, 검정) + 별, 트리, 선물, 종, 양말, 사탕, 루돌프, 산타 ---
st.markdown("""
<style>
    /* 전체 배경: 검정 + 은하수 별 */
    .stApp {
        background: #000000;
        color: #ffffff;
        font-family: 'Playfair Display', serif;
        position: relative;
        overflow: hidden;
    }

    /* 은하수 별들 */
    @keyframes twinkle {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }
    .star {
        position: absolute;
        background: #ffffff;
        border-radius: 50%;
        animation: twinkle 3s infinite;
        pointer-events: none;
    }

    /* 제목: 고급스러운 크리스마스 */
    .main-title {
        text-align: center;
        margin-bottom: 30px;
        line-height: 1.2;
        position: relative;
        z-index: 10;
    }
    .main-title .cantata {
        color: #DC143C !important;
        font-size: 2.8em;
        font-weight: 700;
        text-shadow: 0 0 15px #FFD700, 0 0 30px #FF4500;
    }
    .main-title .year {
        color: #FFFFFF !important;
        font-size: 2.8em;
        font-weight: 700;
        text-shadow: 0 0 15px #FFFFFF, 0 0 30px #87CEEB;
    }
    .main-title .maharashtra {
        color: #D3D3D3 !important;
        font-size: 1.8em;
        font-style: italic;
        display: block;
        margin-top: -10px;
        text-shadow: 0 0 10px #9E9E9E;
    }

    /* 탭 버튼: 고급스러운 빨강 + 금색 테두리 */
    .stButton > button {
        background: #8B0000 !important;
        color: #FFFFFF !important;
        border: 2px solid #FFD700 !important;
        border-radius: 14px !important;
        padding: 14px 30px !important;
        font-weight: 600;
        font-size: 1.1em;
        transition: all 0.4s ease;
        box-shadow: 0 4px 20px rgba(255, 215, 0, 0.3);
    }
    .stButton > button:hover {
        background: #B22222 !important;
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(255, 215, 0, 0.5);
    }

    /* 공지 expander: 녹색 트리 + 금색 테두리 */
    .streamlit-expanderHeader {
        background: #006400 !important;
        color: #FFFFFF !important;
        border-radius: 12px;
        border: 2px solid #FFD700;
        padding: 14px 18px;
        font-size: 1.05em;
        transition: all 0.3s ease;
    }
    .streamlit-expanderHeader:hover {
        background: #228B22 !important;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
    }
    .streamlit-expander {
        background: rgba(0, 100, 0, 0.7) !important;
        border-radius: 12px;
        border: 2px solid #FFD700;
        margin-bottom: 14px;
    }

    /* 입력 폼: 흰색 배경 + 빨강 테두리 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        background: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #DC143C !important;
        border-radius: 10px;
    }

    /* 사이드바: 검정 + 금색 테두리 */
    .css-1d391kg {
        background: #000000;
        border-right: 3px solid #FFD700;
    }

    /* 알림 박스: 금색 선물 */
    .alert-box {
        position: fixed; top: 20px; right: 20px; z-index: 9999;
        background: #FFD700; color: #8B0000; padding: 18px 26px;
        border-radius: 16px; box-shadow: 0 10px 35px rgba(139, 0, 0, 0.5);
        font-weight: 600; font-size: 17px; display: flex; align-items: center; gap: 14px;
        animation: slideIn 0.6s ease-out, glow 2s infinite;
        border: 3px solid #228B22;
    }

    /* 전체화면 지도 */
    .fullscreen-map {
        position: fixed !important;
        top: 0; left: 0; width: 100vw !important; height: 100vh !important;
        z-index: 9998; background: #000000;
    }

    /* 도시 라벨 */
    .city-label {
        color: #FFD700 !important;
        font-weight: 600;
        font-size: 1.05em;
    }
    .city-icon {
        margin-right: 8px;
        font-size: 1.3em;
        color: #FFFFFF;
    }

    /* 크리스마스 요소 애니메이션 */
    @keyframes float-tree {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-15px); }
    }
    @keyframes sway-gift {
        0%, 100% { transform: rotate(-5deg); }
        50% { transform: rotate(5deg); }
    }
    @keyframes ring-bell {
        0%, 100% { transform: rotate(-15deg); }
        50% { transform: rotate(15deg); }
    }
    @keyframes bounce-candy {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    @keyframes hop-rudolph {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-20px); }
    }
    @keyframes slide-santa {
        0% { transform: translateX(-100vw) translateY(-50px); }
        100% { transform: translateX(100vw) translateY(-50px); }
    }

    .christmas-tree {
        position: absolute; bottom: 10%; left: 5%; font-size: 4em; animation: float-tree 6s ease-in-out infinite; z-index: 1;
    }
    .gift-box {
        position: absolute; bottom: 15%; right: 8%; font-size: 2.5em; animation: sway-gift 4s ease-in-out infinite; z-index: 1;
    }
    .bell {
        position: absolute; top: 15%; left: 10%; font-size: 2em; animation: ring-bell 3s ease-in-out infinite; z-index: 1;
    }
    .stocking {
        position: absolute; top: 20%; right: 12%; font-size: 2.5em; animation: bounce-candy 3.5s ease-in-out infinite; z-index: 1;
    }
    .candy-cane {
        position: absolute; bottom: 18%; left: 12%; font-size: 2em; animation: bounce-candy 4s ease-in-out infinite; z-index: 1;
    }
    .rudolph {
        position: absolute; top: 25%; left: 50%; font-size: 2.5em; animation: hop-rudolph 3s ease-in-out infinite; z-index: 1;
    }
    .santa {
        position: absolute; top: 8%; font-size: 2em; animation: slide-santa 25s linear infinite; z-index: 1;
    }
</style>
""", unsafe_allow_html=True)

# --- 크리스마스 요소 + 은하수 별 스크립트 ---
st.markdown("""
<script>
    // 은하수 별들
    function createStar() {
        const star = document.createElement('div');
        star.classList.add('star');
        star.style.width = Math.random() * 3 + 'px';
        star.style.height = star.style.width;
        star.style.left = Math.random() * 100 + 'vw';
        star.style.top = Math.random() * 100 + 'vh';
        star.style.animationDelay = Math.random() * 3 + 's';
        document.body.appendChild(star);
        setTimeout(() => star.remove(), 10000);
    }

    // 크리스마스 요소
    function addChristmasElements() {
        const tree = document.createElement('div');
        tree.classList.add('christmas-tree');
        tree.innerHTML = '🎄';
        document.body.appendChild(tree);

        const gift = document.createElement('div');
        gift.classList.add('gift-box');
        gift.innerHTML = '🎁';
        document.body.appendChild(gift);

        const bell = document.createElement('div');
        bell.classList.add('bell');
        bell.innerHTML = '🔔';
        document.body.appendChild(bell);

        const stocking = document.createElement('div');
        stocking.classList.add('stocking');
        stocking.innerHTML = '🧦';
        document.body.appendChild(stocking);

        const candy = document.createElement('div');
        candy.classList.add('candy-cane');
        candy.innerHTML = '🍭';
        document.body.appendChild(candy);

        const rudolph = document.createElement('div');
        rudolph.classList.add('rudolph');
        rudolph.innerHTML = '🦌';
        document.body.appendChild(rudolph);

        const santa = document.createElement('div');
        santa.classList.add('santa');
        santa.innerHTML = '🎅🛷';
        document.body.appendChild(santa);
    }

    // 초기 생성
    for (let i = 0; i < 150; i++) createStar();
    addChristmasElements();

    // 주기적 생성
    setInterval(() => { for (let i = 0; i < 5; i++) createStar(); }, 1000);
</script>
""", unsafe_allow_html=True)

# --- 6. 제목 (모바일 기준 줄바꿈) ---
st.markdown("""
<div class="main-title">
    <span class="cantata">칸타타 투어</span> <span class="year">2025</span>
    <div class="maharashtra">마하라스트라</div>
</div>
""", unsafe_allow_html=True)

# --- 7. 사이드바 ---
with st.sidebar:
    lang_map = {"한국어": "ko", "English": "en", "हिंदी": "hi"}
    sel = st.selectbox("언어", list(lang_map.keys()),
                       index=list(lang_map.values()).index(st.session_state.lang))
    if lang_map[sel] != st.session_state.lang:
        st.session_state.lang = lang_map[sel]
        st.session_state.tab_selection = _(f"tab_notice")
        st.rerun()

    st.markdown("---")
    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password", key="pw")
        if st.button("로그인", key="login"):
            if pw == st.session_state.password:
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃", key="logout"):
            st.session_state.admin = False
            st.rerun()

        st.markdown("---")
        if st.button(_(f"change_pw"), key="show_pw_btn"):
            st.session_state.show_pw_form = True

        if st.session_state.get("show_pw_form", False):
            with st.form("change_pw_form"):
                st.markdown("### 비밀번호 변경")
                current_pw = st.text_input(_(f"current_pw"), type="password")
                new_pw = st.text_input(_(f"new_pw"), type="password")
                confirm_pw = st.text_input(_(f"confirm_pw"), type="password")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("변경"):
                        if current_pw == "0691":
                            if new_pw == confirm_pw and new_pw:
                                st.session_state.password = new_pw
                                st.success(_(f"pw_changed"))
                                st.session_state.show_pw_form = False
                                st.rerun()
                            else:
                                st.error(_(f"pw_mismatch"))
                        else:
                            st.error(_(f"pw_error"))
                with col2:
                    if st.form_submit_button("취소"):
                        st.session_state.show_pw_form = False
                        st.rerun()

# --- 8. JSON 헬퍼 ---
def load_json(f):
    return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []

def save_json(f, d):
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 9. 초기 도시 (Pune 추가) ---
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

# --- 10. 하드코딩 좌표 ---
CITY_COORDS = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882)
}

# --- 11. 공지 기능 ---
def add_notice(title, content, img=None, file=None):
    img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
    if img:
        with open(img_path, "wb") as f:
            f.write(img.getbuffer())
    if file:
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
    notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
        "image": img_path,
        "file": file_path
    }
    data = load_json(NOTICE_FILE)
    data.insert(0, notice)
    save_json(NOTICE_FILE, data)

    st.session_state.new_notice = True
    st.session_state.alert_active = True
    st.session_state.current_alert_id = notice["id"]
    st.session_state.sound_played = False
    play_carol()
    st.rerun()

def format_notice_date(d):
    try:
        dt = datetime.strptime(d, "%m/%d %H:%M")
        today = date.today()
        if dt.date() == today:
            return f"{_(f'today')} {dt.strftime('%H:%M')}"
        elif dt.date() == today - timedelta(days=1):
            return f"{_(f'yesterday')} {dt.strftime('%H:%M')}"
        else:
            return d
    except:
        return d

def render_notices():
    data = load_json(NOTICE_FILE)
    
    for i, n in enumerate(data):
        formatted_date = format_notice_date(n['date'])
        title = f"{formatted_date} | {n['title']}"
        exp_key = f"notice_{n['id']}"
        expanded = exp_key in st.session_state.expanded_notices

        with st.expander(title, expanded=expanded):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_column_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                b64 = base64.b64encode(open(n["file"], "rb").read()).decode()
                href = f'<a href="data:file/txt;base64,{b64}" download="{os.path.basename(n["file"])}">다운로드</a>'
                st.markdown(href, unsafe_allow_html=True)

            if st.session_state.admin and st.button("삭제", key=f"del_n_{n['id']}"):
                data.pop(i)
                save_json(NOTICE_FILE, data)
                st.rerun()

            if not st.session_state.admin and n["id"] not in st.session_state.seen_notices and expanded:
                st.session_state.seen_notices.append(n["id"])
                if n["id"] == st.session_state.current_alert_id:
                    st.session_state.alert_active = False
                st.rerun()

            if expanded and exp_key not in st.session_state.expanded_notices:
                st.session_state.expanded_notices.append(exp_key)
            elif not expanded and exp_key in st.session_state.expanded_notices:
                st.session_state.expanded_notices.remove(exp_key)

    if not st.session_state.admin and st.session_state.alert_active and st.session_state.current_alert_id:
        play_carol()
        st.markdown(f"""
        <div class="alert-box" id="alert">
            <span>{_("new_notice_alert")}</span>
            <span class="alert-close" onclick="document.getElementById('alert').remove()">×</span>
        </div>
        <script>
            setTimeout(() => {{
                if (document.getElementById('alert')) {{
                    document.querySelector('[data-testid="stRadio"] input[value="{_(f'tab_notice')}"]').click();
                }}
            }}, 100);
        </script>
        """, unsafe_allow_html=True)

# --- 12. 지도 + 도시 추가/수정 ---
def format_date_with_weekday(perf_date):
    if perf_date and perf_date != "9999-12-31":
        dt = datetime.strptime(perf_date, "%Y-%m-%d")
        weekday = dt.strftime("%A")
        if st.session_state.lang == "ko":
            weekdays = {"Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일", "Thursday": "목요일",
                        "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"}
            weekday = weekdays.get(weekday, weekday)
        return f"{perf_date} ({weekday})"
    return "미정"

def render_map():
    st.subheader("경로 보기")
    today = date.today()
    raw_cities = load_json(CITY_FILE)
    cities = sorted(raw_cities, key=lambda x: x.get("perf_date", "9999-12-31"))
    city_names = [c["city"] for c in raw_cities]

    # --- 도시 추가 폼 (공연 날짜 → 장소 위) ---
    if st.session_state.admin:
        if st.button(_(f"add_city"), key="add_city_btn"):
            st.session_state.adding_city = True

        if st.session_state.get("adding_city"):
            st.markdown("### 새 도시 추가")
            with st.form("add_city_form"):
                selected_city = st.selectbox(_(f"select_city"), options=city_names + ["<새 도시 입력>"])
                if selected_city == "<새 도시 입력>":
                    new_city = st.text_input("새 도시명")
                else:
                    new_city = selected_city

                perf_date_input = st.date_input(_(f"perf_date"), value=None)
                perf_date = perf_date_input.strftime("%Y-%m-%d") if perf_date_input else None

                venue = st.text_input(_(f"venue"))
                seats = st.text_input(_(f"seats"))
                indoor = st.radio("장소 유형", [_(f"indoor"), _(f"outdoor")])
                note = st.text_area(_(f"note"))
                google_link = st.text_input(_(f"google_link"))

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button(_(f"save")):
                        if new_city and new_city not in city_names:
                            new_data = {
                                "city": new_city, "venue": venue, "seats": seats,
                                "indoor": indoor == _(f"indoor"), "note": note,
                                "google_link": google_link,
                                "perf_date": perf_date,
                                "date": datetime.now().strftime("%m/%d %H:%M")
                            }
                            raw_cities.append(new_data)
                            save_json(CITY_FILE, raw_cities)
                            st.session_state.adding_city = False
                            st.success("도시 추가 완료!")
                            st.rerun()
                        else:
                            st.error("도시명 중복 또는 비어있음")
                with col2:
                    if st.form_submit_button(_(f"cancel")):
                        st.session_state.adding_city = False
                        st.rerun()

    # --- 도시 수정 폼 (공연 날짜 위로) ---
    if st.session_state.admin and st.session_state.get("edit_city"):
        city_to_edit = next((c for c in raw_cities if c["city"] == st.session_state.edit_city), None)
        if city_to_edit:
            st.markdown("### 도시 정보 수정")
            with st.form("edit_city_form"):
                city = st.selectbox("도시 선택", options=city_names,
                                    index=city_names.index(st.session_state.edit_city))
                perf_date_input = st.date_input(_(f"perf_date"), value=(
                    datetime.strptime(city_to_edit["perf_date"], "%Y-%m-%d").date()
                    if city_to_edit.get("perf_date") and city_to_edit["perf_date"] != "9999-12-31"
                    else None
                ))
                perf_date = perf_date_input.strftime("%Y-%m-%d") if perf_date_input else None

                venue = st.text_input(_(f"venue"), value=city_to_edit["venue"])
                seats = st.text_input(_(f"seats"), value=city_to_edit["seats"])
                indoor = st.radio("장소 유형", [_(f"indoor"), _(f"outdoor")],
                                  index=0 if city_to_edit.get("indoor", False) else 1)
                note = st.text_area(_(f"note"), value=city_to_edit.get("note", ""))
                google_link = st.text_input(_(f"google_link"), value=city_to_edit.get("google_link", ""))

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button(_(f"save")):
                        updated = {
                            "city": city, "venue": venue, "seats": seats,
                            "indoor": indoor == _(f"indoor"), "note": note,
                            "google_link": google_link,
                            "perf_date": perf_date,
                            "date": city_to_edit["date"]
                        }
                        raw_cities = [updated if c["city"] == st.session_state.edit_city else c for c in raw_cities]
                        save_json(CITY_FILE, raw_cities)
                        st.session_state.edit_city = None
                        st.success("수정 완료!")
                        st.rerun()
                with col2:
                    if st.form_submit_button(_(f"cancel")):
                        st.session_state.edit_city = None
                        st.rerun()

    # --- 지도 (말풍선 내용 진하게) ---
    m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="CartoDB positron")

    for i, c in enumerate(cities):
        is_past = (c.get('perf_date') and c['perf_date'] != "9999-12-31" and
                   datetime.strptime(c['perf_date'], "%Y-%m-%d").date() < today)
        color = "red" if not is_past else "gray"

        coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
        indoor_text = _(f"indoor") if c.get("indoor") else _(f"outdoor")
        perf_date_formatted = format_date_with_weekday(c.get("perf_date"))
        lat, lon = coords
        google_nav = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"
        google_link_html = f'<br><a href="{google_nav}" target="_blank">길 안내 시작</a>' if c.get("google_link") else ""

        popup_html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 14px; line-height: 1.6; color: #000000;">
            <b style="font-size: 16px;">{c['city']}</b><br>
            <b>날짜:</b> <strong>{perf_date_formatted}</strong><br>
            <b>장소:</b> <strong>{c.get('venue','—')}</strong><br>
            <b>예상 인원:</b> <strong>{c.get('seats','—')}</strong><br>
            <b>장소:</b> <strong>{indoor_text}</strong>{google_link_html}
        </div>
        """
        folium.Marker(
            coords,
            popup=folium.Popup(popup_html, max_width=320),
            icon=folium.Icon(color=color, icon="music", prefix="fa")
        ).add_to(m)

        if i < len(cities) - 1:
            nxt = cities[i + 1]
            nxt_coords = CITY_COORDS.get(nxt["city"], (18.5204, 73.8567))
            opacity = 0.3 if is_past else 1.0
            AntPath([coords, nxt_coords],
                    color="#FFD700", weight=5, opacity=opacity, delay=800, dash_array=[20, 30]).add_to(m)

        exp_key = f"city_{c['city']}"
        expanded = exp_key in st.session_state.expanded_cities
        with st.expander(f"{c['city']} | {format_date_with_weekday(c.get('perf_date'))}", expanded=expanded):
            indoor_icon = "실내" if c.get("indoor") else "야외"
            st.markdown(f"""
            <div>
                <span class="city-icon">장소</span>
                <span class="city-label">{_(f'venue')}:</span> {c.get('venue','—')}
            </div>
            <div>
                <span class="city-icon">예상 인원</span>
                <span class="city-label">{_(f'seats')}:</span> {c.get('seats','—')}
            </div>
            <div>
                <span class="city-icon">{indoor_icon}</span>
                <span class="city-label">유형:</span> {indoor_text}
            </div>
            <div>
                <span class="city-icon">특이사항</span>
                <span class="city-label">{_(f'note')}:</span> {c.get('note','—')}
            </div>
            """, unsafe_allow_html=True)

            if c.get("google_link"):
                st.markdown(f"[길 안내 시작]({google_nav})")

            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(_(f"edit"), key=f"edit_{c['city']}"):
                        st.session_state.edit_city = c["city"]
                        st.rerun()
                with c2:
                    if st.button("삭제", key=f"del_{c['city']}"):
                        raw_cities = [x for x in raw_cities if x["city"] != c["city"]]
                        save_json(CITY_FILE, raw_cities)
                        st.rerun()

            if expanded and exp_key not in st.session_state.expanded_cities:
                st.session_state.expanded_cities.append(exp_key)
            elif not expanded and exp_key in st.session_state.expanded_cities:
                st.session_state.expanded_cities.remove(exp_key)

    st_folium(m, width=900, height=550, key="tour_map")

# --- 13. 탭 (버튼) ---
col1, col2 = st.columns(2)
with col1:
    if st.button(_(f"tab_notice"), use_container_width=True):
        st.session_state.tab_selection = _(f"tab_notice")
        st.rerun()
with col2:
    if st.button(_(f"tab_map"), use_container_width=True):
        st.session_state.tab_selection = _(f"tab_map")
        st.rerun()

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
