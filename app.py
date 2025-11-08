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

# --- 4. 세션 상태 ---
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 5. JSON 헬퍼 ---
def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 6. 기본 도시 및 좌표 ---
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

# --- CSS ---
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
[data-testid="stAppViewContainer"] { background: url("background_christmas_dark.png"); background-size: cover; background-position: center; background-attachment: fixed; }
.header-container { text-align: center; margin: 0; padding: 0; }
.christmas-decoration { display: flex; justify-content: center; gap: 12px; margin-bottom: 0; }
.christmas-decoration i { color:#fff; text-shadow:0 0 10px rgba(255,255,255,0.6); animation: float 3s ease-in-out infinite; opacity:0.95; }
@keyframes float {0%,100%{transform:translateY(0);}50%{transform:translateY(-6px);}}
.main-title { font-size: 2.4em !important; font-weight: bold; text-align: center; text-shadow: 0 3px 8px rgba(0,0,0,0.6); margin: 0; padding: 0; }
.button-row { display: flex; justify-content: center; gap: 10px; margin: 8px 0; }
.tab-btn { background: rgba(255,255,255,0.96); color: #c62828; border: none; border-radius: 20px; padding: 8px 15px; font-weight: bold; font-size: 1em; cursor: pointer; transition: all 0.3s ease; }
.tab-btn:hover { background: #d32f2f; color: white; transform: translateY(-2px); }
.notice-container, .map-container {
    height: 62vh; overflow-y: auto; margin: 8px 0; padding: 15px;
    background: rgba(255,255,255,0.12); border-radius: 15px; backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.2);
}
.notice-container::-webkit-scrollbar, .map-container::-webkit-scrollbar { width: 8px; }
.notice-container::-webkit-scrollbar-thumb, .map-container::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.4); border-radius: 10px; }
.snowflake { position:fixed; top:-15px; color:#fff; font-size:1em; pointer-events:none; animation:fall linear infinite; opacity:0.4; z-index:1; }
@keyframes fall {0%{transform:translateY(0);}100%{transform:translateY(110vh);}}
</style>
""", unsafe_allow_html=True)

# --- 눈 효과 ---
for i in range(40):
    left = random.randint(0, 100)
    duration = random.randint(10, 20)
    size = random.uniform(0.7, 1.3)
    delay = random.uniform(0, 8)
    st.markdown(f"<div class='snowflake' style='left:{left}vw; animation-duration:{duration}s; font-size:{size}em; animation-delay:{delay}s;'>❄</div>", unsafe_allow_html=True)

# --- 헤더 ---
st.markdown('<div class="header-container">', unsafe_allow_html=True)
st.markdown('''
<div class="christmas-decoration">
    <i class="fas fa-gift"></i><i class="fas fa-candy-cane"></i><i class="fas fa-socks"></i>
    <i class="fas fa-sleigh"></i><i class="fas fa-deer"></i><i class="fas fa-tree"></i><i class="fas fa-bell"></i>
</div>
''', unsafe_allow_html=True)
st.markdown(f'<h1 class="main-title"><span style="color:red;">{_("title_cantata")}</span> <span style="color:white;">{_("title_year")}</span> <span style="color:green; font-size:65%;">{_("title_region")}</span></h1>', unsafe_allow_html=True)
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

# --- 초기 화면 ---
if not st.session_state.notice_open and not st.session_state.map_open:
    st.markdown("""
    <div style='text-align:center; margin-top:50px; padding:30px; background:rgba(255,255,255,0.1); border-radius:20px;'>
        <h2 style='color:#fff; margin:0;'>칸타타 투어 2025</h2>
        <p style='color:#eee; font-size:1.1em; margin:10px 0;'>
            위 버튼을 눌러 <b>공지사항</b> 또는 <b>투어 일정</b>을 확인하세요.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 공지 영역 (박스 안에 전부!) ---
if st.session_state.notice_open:
    st.markdown('<div class="notice-container">', unsafe_allow_html=True)
    
    if st.session_state.admin:
        st.markdown("### 공지 작성")
        with st.form("notice_form", clear_on_submit=True):
            title = st.text_input("제목", placeholder="공지 제목을 입력하세요")
            content = st.text_area("내용", placeholder="내용을 입력하세요", height=120)
            col1, col2 = st.columns([1, 4])
            with col1:
                submit = st.form_submit_button("등록")
            if submit:
                if title.strip() and content.strip():
                    notice = {
                        "id": str(uuid.uuid4()),
                        "title": title,
                        "content": content,
                        "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                    }
                    data = load_json(NOTICE_FILE)
                    data.insert(0, notice)
                    save_json(NOTICE_FILE, data)
                    st.success("공지가 등록되었습니다!")
                    st.rerun()
                else:
                    st.warning(_("warning"))

    st.markdown("### 공지사항")
    data = load_json(NOTICE_FILE)
    if not data:
        st.info("등록된 공지가 없습니다.")
    else:
        for i, n in enumerate(data):
            st.markdown(f"**{n['date']} | {n['title']}**")
            st.markdown(n["content"])
            if st.session_state.admin:
                if st.button("삭제", key=f"del_{n['id']}"):
                    data.pop(i)
                    save_json(NOTICE_FILE, data)
                    st.rerun()
            st.markdown("---")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 지도 영역 (박스 안에 전부!) ---
if st.session_state.map_open:
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st.markdown("### 투어 경로")
    cities = load_json(CITY_FILE)
    if not cities:
        st.warning("등록된 도시가 없습니다.")
    else:
        m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="OpenStreetMap")
        for i, c in enumerate(cities):
            coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
            lat, lon = coords
            is_future = c.get("perf_date", "9999-12-31") >= str(date.today())
            color = "red" if is_future else "gray"
            indoor_text = _("indoor") if c.get("indoor") else _("outdoor")
            popup_html = f"""
            <div style='font-size:13px; line-height:1.5;'>
                <b>{c['city']}</b><br>
                공연: {c.get('perf_date','미정')}<br>
                장소: {c.get('venue','—')}<br>
                인원: {c.get('seats','—')}<br>
                {indoor_text}<br>
                <a href='https://www.google.com/maps/dir/?api=1&destination={lat},{lon}' target='_blank'>
                    길찾기
                </a>
            </div>
            """
            folium.Marker(
                coords,
                popup=folium.Popup(popup_html, max_width=260),
                icon=folium.Icon(color=color, icon="music", prefix="fa")
            ).add_to(m)
            if i < len(cities) - 1:
                nxt = CITY_COORDS.get(cities[i+1]["city"], (18.5204, 73.8567))
                AntPath([coords, nxt], color="#e74c3c", weight=5, opacity=0.7).add_to(m)
        st_folium(m, width=850, height=380, key="tour_map")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 사이드바 (언어 + 관리자 로그인) ---
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
                st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃"):
            st.session_state.admin = False
            st.rerun()
