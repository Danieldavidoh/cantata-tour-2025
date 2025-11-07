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

# --- 4. 캐롤 사운드 ---
def play_carol():
    if not st.session_state.sound_played:
        st.session_state.sound_played = True
        st.markdown("""
        <audio autoplay loop>
            <source src="data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAAA" type="audio/wav">
        </audio>
        """, unsafe_allow_html=True)

# --- 5. UI (화면 가림 해결) ---
st.markdown("""
<style>
    .main > div { overflow: visible !important; }
    .stApp { overflow: visible !important; background: #000000; color: #ffffff; font-family: 'Playfair Display', serif; }
    .main-title { text-align: center; margin: 20px 0 40px; line-height: 1.2; z-index: 10; }
    .main-title .cantata { color: #DC143C; font-size: 2.8em; font-weight: 700; text-shadow: 0 0 15px #FFD700; }
    .main-title .year { color: #FFFFFF; font-size: 2.8em; font-weight: 700; text-shadow: 0 0 15px #FFFFFF; }
    .main-title .maharashtra { color: #D3D3D3; font-size: 1.8em; font-style: italic; display: block; margin-top: -10px; }
    .stButton > button { background: #8B0000 !important; color: #FFFFFF !important; border: 2px solid #FFD700 !important; border-radius: 14px !important; padding: 14px 30px !important; font-weight: 600; font-size: 1.1em; box-shadow: 0 4px 20px rgba(255, 215, 0, 0.3); z-index: 10; }
    .stButton > button:hover { background: #B22222 !important; transform: translateY(-3px); box-shadow: 0 8px 30px rgba(255, 215, 0, 0.5); }
    .streamlit-expanderHeader { background: #006400 !important; color: #FFFFFF !important; border: 2px solid #FFD700; border-radius: 12px; padding: 14px 18px; font-size: 1.05em; z-index: 5; }
    .streamlit-expander { background: rgba(0, 100, 0, 0.7) !important; border: 2px solid #FFD700; border-radius: 12px; margin-bottom: 14px; z-index: 5; }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        background: #FFFFFF !important; color: #000000 !important; border: 2px solid #DC143C !important; border-radius: 10px; z-index: 5;
    }
    .css-1d391kg { background: #000000 !important; border-right: 3px solid #FFD700 !important; z-index: 10; }
    .christmas-element { position: fixed !important; z-index: 1 !important; pointer-events: none !important; }
    .star { position: fixed !important; background: #ffffff; border-radius: 50%; animation: twinkle 3s infinite; pointer-events: none !important; z-index: 0 !important; }
    @keyframes twinkle { 0%,100% { opacity: 0.5; } 50% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# --- 6. 크리스마스 요소 & 별 ---
st.markdown("""
<script>
    window.addEventListener('load', () => {
        const body = document.body;
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
        const style = document.createElement('style');
        style.innerHTML = `
            @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-15px); } }
            @keyframes sway { 0%,100% { transform: rotate(-5deg); } 50% { transform: rotate(5deg); } }
            @keyframes ring { 0%,100% { transform: rotate(-15deg); } 50% { transform: rotate(15deg); } }
            @keyframes hop { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
            @keyframes slide { 0% { transform: translateX(-100vw); } 100% { transform: translateX(100vw); } }
        `;
        document.head.appendChild(style);
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

# --- 8. 사이드바 ---
with st.sidebar:
    lang_map = {"한국어": "ko"}
    sel = st.selectbox("언어", list(lang_map.keys()), index=0)
    if lang_map[sel] != st.session_state.lang:
        st.session_state.lang = lang_map[sel]
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

# --- 9. JSON 헬퍼 ---
def load_json(f):
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

def save_json(f, d):
    with open(f, "w", encoding="utf-8") as file:
        json.dump(d, file, ensure_ascii=False, indent=2)

# --- 10. 초기 도시 ---
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
        """, unsafe_allow_html=True)

# --- 12. 지도 ---
def render_map():
    m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="CartoDB positron")
    raw_cities = load_json(CITY_FILE)
    cities = sorted(raw_cities, key=lambda x: x.get("perf_date", "9999-12-31"))
    for i, c in enumerate(cities):
        coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
        indoor_text = _(f"indoor") if c.get("indoor") else _(f"outdoor")
        perf_date_formatted = format_date_with_weekday(c.get("perf_date"))
        google_nav = f"https://www.google.com/maps/dir/?api=1&destination={coords[0]},{coords[1]}&travelmode=driving"
        popup_html = f"""
        <div style="font-size: 14px; line-height: 1.6; color: #000000;">
            <b>{c['city']}</b><br>
            <b>날짜:</b> <strong>{perf_date_formatted}</strong><br>
            <b>장소:</b> <strong>{c.get('venue','—')}</strong><br>
            <b>예상 인원:</b> <strong>{c.get('seats','—')}</strong><br>
            <b>장소:</b> <strong>{indoor_text}</strong>
        </div>
        """
        folium.Marker(coords, popup=folium.Popup(popup_html, max_width=320), icon=folium.Icon(color="red" if c.get('perf_date') else "gray", icon="music", prefix="fa")).add_to(m)
    st_folium(m, width=900, height=550, key="tour_map")

def format_date_with_weekday(perf_date):
    if perf_date and perf_date != "9999-12-31":
        dt = datetime.strptime(perf_date, "%Y-%m-%d")
        weekday = dt.strftime("%A")
        weekdays = {"Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일", "Thursday": "목요일", "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"}
        return f"{perf_date} ({weekdays.get(weekday, weekday)})"
    return "미정"

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
