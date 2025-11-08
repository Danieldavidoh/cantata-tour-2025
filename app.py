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
    "ko": { "title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
            "tab_notice": "공지", "tab_map": "투어 경로", "indoor": "실내", "outdoor": "실외",
            "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵", "perf_date": "공연 날짜",
            "warning": "제목·내용 입력", "delete": "제거", "menu": "메뉴", "login": "로그인", "logout": "로그아웃", "close": "닫기" },
    "en": { "title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
            "tab_notice": "Notice", "tab_map": "Tour Route", "indoor": "Indoor", "outdoor": "Outdoor",
            "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps", "perf_date": "Performance Date",
            "warning": "Enter title & content", "delete": "Remove", "menu": "Menu", "login": "Login", "logout": "Logout", "close": "Close" },
    "hi": { "title_cantata": "कैंटाटा टूर", "title_year": "2025", "title_region": "महाराष्ट्र",
            "tab_notice": "सूचना", "tab_map": "टूर मार्ग", "indoor": "इनडोर", "outdoor": "आउटडोर",
            "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप", "perf_date": "प्रदर्शन तिथि",
            "warning": "शीर्षक·सामग्री दर्ज करें", "delete": "हटाएं", "menu": "मेनू", "login": "लॉगिन", "logout": "लॉगआउट", "close": "बंद करें" }
}

# --- 4. 세션 상태 ---
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False}
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

# --- 7. CSS: 한 화면 완전 밀착 + 고정 ---
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
        overflow: hidden !important; height: 100vh !important; margin: 0 !important; padding: 0 !important;
    }
    [data-testid="stAppViewContainer"] {
        background: url("background_christmas_dark.png") center/cover fixed;
    }

    /* 전체 컨테이너 */
    .main-container {
        display: flex; flex-direction: column; height: 100vh; padding: 0; margin: 0;
    }

    /* 헤더: 아이콘 + 제목 + 버튼 (완전 밀착) */
    .header {
        flex: 0 0 auto; text-align: center; padding: 10px 0 0 0; margin: 0;
    }
    .christmas-decoration {
        display: flex; justify-content: center; gap: 10px; margin: 0 !important; padding: 0 !important;
    }
    .christmas-decoration i {
        color: #fff; text-shadow: 0 0 10px rgba(255,255,255,0.7); animation: float 3s ease-in-out infinite; font-size: 2em;
    }
    .christmas-decoration i:nth-child(1) {animation-delay:0s;}
    .christmas-decoration i:nth-child(2) {animation-delay:.3s;}
    .christmas-decoration i:nth-child(3) {animation-delay:.6s;}
    .christmas-decoration i:nth-child(4) {animation-delay:.9s;}
    .christmas-decoration i:nth-child(5) {animation-delay:1.2s;}
    .christmas-decoration i:nth-child(6) {animation-delay:1.5s;}
    .christmas-decoration i:nth-child(7) {animation-delay:1.8s;}
    @keyframes float {0%,100%{transform:translateY(0) rotate(0deg);}50%{transform:translateY(-6px) rotate(3deg);}}

    .main-title {
        font-size: 2.6em !important; font-weight: bold; margin: 0 !important; padding: 0 !important; line-height: 1;
        text-shadow: 0 3px 8px rgba(0,0,0,0.6);
    }

    .button-row {
        display: flex; justify-content: center; gap: 15px; margin: 5px 0 0 0 !important; padding: 0;
    }
    .tab-btn {
        background: rgba(255,255,255,0.95); color: #c62828; border: none; border-radius: 20px;
        padding: 8px 16px; font-weight: bold; font-size: 1em; cursor: pointer;
        box-shadow: 0 3px 10px rgba(0,0,0,0.2); transition: all 0.3s; flex: 1; max-width: 160px;
    }
    .tab-btn:hover { background: #d32f2f; color: white; transform: translateY(-2px); }

    /* 눈송이 */
    .snowflake {position:fixed;top:-15px;color:#fff;font-size:1em;pointer-events:none;animation:fall linear infinite;opacity:0.4;z-index:1;}
    @keyframes fall {0%{transform:translateY(0) rotate(0deg);}100%{transform:translateY(120vh) rotate(360deg);}}

    /* 공지/지도 오버레이 */
    .overlay-content {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.9);
        z-index: 999; padding: 20px; overflow-y: auto; display: none;
    }
    .overlay-content.open { display: block; }
    .close-overlay {
        position: fixed; top: 15px; right: 15px; background: #e74c3c; color: white; border: none;
        padding: 10px 15px; border-radius: 50%; font-weight: bold; cursor: pointer; z-index: 1000;
    }

    /* 모바일 햄버거 */
    .hamburger {position:fixed;top:15px;left:15px;z-index:10000;background:rgba(0,0,0,.6);color:#fff;border:none;border-radius:50%;width:50px;height:50px;font-size:24px;cursor:pointer;box-shadow:0 0 10px rgba(0,0,0,.3);}
    .sidebar-mobile {position:fixed;top:0;left:-300px;width:280px;height:100vh;background:rgba(30,30,30,.95);color:#fff;padding:20px;transition:left .3s;z-index:9999;overflow-y:auto;}
    .sidebar-mobile.open {left:0;}
    .overlay {position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,.5);z-index:9998;display:none;}
    .overlay.open {display:block;}
    @media(min-width:769px){.hamburger,.sidebar-mobile,.overlay{display:none!important;}section[data-testid="stSidebar"]{display:block!important;}}
    .stButton>button{border:none!important;-webkit-appearance:none!important;}
</style>
""", unsafe_allow_html=True)

# --- 눈송이 60개 ---
for i in range(60):
    left = random.randint(0, 100)
    duration = random.randint(8, 18)
    size = random.uniform(0.7, 1.3)
    delay = random.uniform(0, 10)
    st.markdown(f"<div class='snowflake' style='left:{left}vw; animation-duration:{duration}s; font-size:{size}em; animation-delay:{delay}s;'>❄</div>", unsafe_allow_html=True)

# --- 메인 컨테이너 ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# --- 헤더: 아이콘 + 제목 + 버튼 (완전 밀착) ---
st.markdown('<div class="header">', unsafe_allow_html=True)

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

title_html = f'<h1 class="main-title"><span style="color:red;">{_("title_cantata")}</span> <span style="color:white;">{_("title_year")}</span> <span style="color:green; font-size:70%;">{_("title_region")}</span></h1>'
st.markdown(title_html, unsafe_allow_html=True)

st.markdown('<div class="button-row">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])
with col1:
    if st.button(_("tab_notice"), key="btn_notice"):
        st.session_state.notice_open = True
        st.session_state.map_open = False
        st.rerun()
with col2:
    if st.button(_("tab_map"), key="btn_map"):
        st.session_state.map_open = True
        st.session_state.notice_open = False
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # .header 종료

# --- 공지 오버레이 ---
if st.session_state.notice_open:
    st.markdown(f'''
    <div class="overlay-content open">
        <button class="close-overlay" onclick="window.location.href='?notice_open=False'">✕</button>
    ''', unsafe_allow_html=True)
    
    if st.session_state.admin:
        with st.expander("공지 작성"):
            with st.form("notice_form", clear_on_submit=True):
                title = st.text_input("제목")
                content = st.text_area("내용")
                img = st.file_uploader("이미지", type=["png","jpg","jpeg"])
                file = st.file_uploader("첨부 파일")
                if st.form_submit_button("등록"):
                    if title and content:
                        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
                        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
                        if img: open(img_path, "wb").write(img.getbuffer())
                        if file: open(file_path, "wb").write(file.getbuffer())
                        notice = {"id": str(uuid.uuid4()), "title": title, "content": content, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"), "image": img_path, "file": file_path}
                        data = load_json(NOTICE_FILE)
                        data.insert(0, notice)
                        save_json(NOTICE_FILE, data)
                        st.success("등록 완료!")
                        st.rerun()
                    else:
                        st.warning(_("warning"))

    data = load_json(NOTICE_FILE)
    for i, n in enumerate(data):
        with st.expander(f"{n['date']} | {n['title']}"):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]): st.image(n["image"])
            if n.get("file") and os.path.exists(n["file"]):
                b64 = base64.b64encode(open(n["file"], "rb").read()).decode()
                st.markdown(f'<a href="data:file/txt;base64,{b64}" download="{os.path.basename(n["file"])}">다운로드</a>', unsafe_allow_html=True)
            if st.session_state.admin and st.button(_("delete"), key=f"del_{n['id']}"):
                data.pop(i); save_json(NOTICE_FILE, data); st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 지도 오버레이 ---
if st.session_state.map_open:
    st.markdown(f'''
    <div class="overlay-content open">
        <button class="close-overlay" onclick="window.location.href='?map_open=False'">✕</button>
    ''', unsafe_allow_html=True)
    
    cities = load_json(CITY_FILE)
    m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="OpenStreetMap")
    for i, c in enumerate(cities):
        coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
        lat, lon = coords
        is_future = c.get("perf_date", "9999-12-31") >= str(date.today())
        color = "red" if is_future else "gray"
        indoor_text = _("indoor") if c.get("indoor") else _("outdoor")
        popup_html = f"<b>{c['city']}</b><br>{_('perf_date')}: {c.get('perf_date','미정')}<br>{_('venue')}: {c.get('venue','—')}<br>{_('seats')}: {c.get('seats','—')}<br>{indoor_text}<br><a href='https://www.google.com/maps/dir/?api=1&destination={lat},{lon}' target='_blank'>{_('google_link')}</a>"
        folium.Marker(coords, popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=color, icon="music", prefix="fa")).add_to(m)
        if i < len(cities) - 1:
            nxt = CITY_COORDS.get(cities[i+1]["city"], (18.5204, 73.8567))
            AntPath([coords, nxt], color="#e74c3c", weight=6, opacity=0.3 if not is_future else 1.0).add_to(m)
    st_folium(m, width=700, height=500, key="map_full")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # .main-container 종료

# --- 모바일 햄버거 ---
st.markdown(f'''
<button class="hamburger" onclick="document.querySelector('.sidebar-mobile').classList.toggle('open'); document.querySelector('.overlay').classList.toggle('open');">☰</button>
<div class="overlay" onclick="document.querySelector('.sidebar-mobile').classList.remove('open'); this.classList.remove('open');"></div>
<div class="sidebar-mobile">
    <h3 style="color:white;">{_("menu")}</h3>
    <select onchange="window.location.href='?lang='+this.value" style="width:100%;padding:8px;margin:10px 0;">
        <option value="ko" {'selected' if st.session_state.lang=="ko" else ''}>한국어</option>
        <option value="en" {'selected' if st.session_state.lang=="en" else ''}>English</option>
        <option value="hi" {'selected' if st.session_state.lang=="hi" else ''}>हिंदी</option>
    </select>
    {'''
        <input type="password" placeholder="비밀번호" id="pw" style="width:100%;padding:8px;margin:10px 0;">
        <button onclick="if(document.getElementById(\'pw\').value==\'0009\') window.location.href=\'?admin=true\'; else alert(\'오류\');" style="width:100%;padding:10px;background:#e74c3c;color:white;border:none;border-radius:8px;">{_("login")}</button>
    ''' if not st.session_state.admin else f'''
        <button onclick="window.location.href=\'?admin=false\'" style="width:100%;padding:10px;background:#27ae60;color:white;border:none;border-radius:8px;margin:10px 0;">{_("logout")}</button>
    ''' }
</div>
''', unsafe_allow_html=True)

# --- 사이드바 ---
with st.sidebar:
    lang_map = {"한국어": "ko", "English": "en", "हिंदी": "hi"}
    sel = st.selectbox("언어", list(lang_map.keys()), index=list(lang_map.values()).index(st.session_state.lang))
    if lang_map[sel] != st.session_state.lang:
        st.session_state.lang = lang_map[sel]
        st.rerun()
    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if pw == "0009":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("오류")
    else:
        st.success("관리자")
        if st.button("로그아웃"):
            st.session_state.admin = False
            st.rerun()
