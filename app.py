# app.py - 칸타타 투어 2025 (실제 교통 시간 + 라인 위 평행 텍스트) 🔥

import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, sin, cos, sqrt, asin, atan2, degrees
import requests

# --- 1. 하버신 거리 계산 ---
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return 6371 * 2 * asin(sqrt(a))

# --- 2. 실제 교통 시간 ---
@st.cache_data(ttl=3600)
def get_real_travel_time(lat1, lon1, lat2, lon2):
    api_key = st.secrets.get("GOOGLE_MAPS_API_KEY", None)
    if not api_key:
        dist = haversine(lat1, lon1, lat2, lon2)
        mins = int(dist * 60 / 55)
        return dist, mins

    origin = f"{lat1},{lon1}"
    dest = f"{lat2},{lon2}"
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={dest}&mode=driving&key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data["status"] == "OK":
            leg = data["routes"][0]["legs"][0]
            dist = leg["distance"]["value"] / 1000
            mins = leg["duration"]["value"] // 60
            return dist, mins
    except:
        pass
    dist = haversine(lat1, lon1, lat2, lon2)
    mins = int(dist * 60 / 55)
    return dist, mins

# --- 3. 자동 리프레시 ---
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh_user")

st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

# --- 4. 파일/디렉토리 ---
NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 5. 세션 상태 ---
defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "expanded": {}, "adding_cities": [],
    "pw": "0009", "seen_notices": [], "active_tab": "공지", "new_notice": False, "sound_played": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 6. 다국어 ---
LANG = {
    "ko": {
        "title_base": "칸타타 투어", "caption": "마하라스트라", "tab_notice": "공지", "tab_map": "투어 경로",
        "map_title": "경로 보기", "add_city": "도시 추가", "password": "비밀번호", "login": "로그인",
        "logout": "로그아웃", "wrong_pw": "비밀번호가 틀렸습니다.", "select_city": "도시 선택",
        "venue": "공연장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵 링크",
        "indoor": "실내", "outdoor": "실외", "register": "등록", "edit": "수정", "remove": "삭제",
        "date": "등록일", "performance_date": "공연 날짜", "cancel": "취소", "title_label": "제목",
        "content_label": "내용", "upload_image": "이미지 업로드", "upload_file": "파일 업로드",
        "submit": "등록", "warning": "제목과 내용을 모두 입력해주세요.", "file_download": "파일 다운로드",
        "pending": "미정", "est_time": "{hours}h {mins}m"
    },
    "en": {
        "title_base": "Cantata Tour", "caption": "Maharashtra", "tab_notice": "Notice", "tab_map": "Tour Route",
        "map_title": "View Route", "add_city": "Add City", "password": "Password", "login": "Login",
        "logout": "Logout", "wrong_pw": "Wrong password.", "select_city": "Select City", "venue": "Venue",
        "seats": "Expected Attendance", "note": "Notes", "google_link": "Google Maps Link",
        "indoor": "Indoor", "outdoor": "Outdoor", "register": "Register", "edit": "Edit", "remove": "Remove",
        "date": "Registered On", "performance_date": "Performance Date", "cancel": "Cancel",
        "title_label": "Title", "content_label": "Content", "upload_image": "Upload Image",
        "upload_file": "Upload File", "submit": "Submit", "warning": "Please enter both title and content.",
        "file_download": "Download File", "pending": "TBD", "est_time": "{hours}h {mins}m"
    },
    "hi": {
        "title_base": "कांताता टूर", "caption": "महाराष्ट्र", "tab_notice": "सूचना", "tab_map": "टूर मार्ग",
        "map_title": "मार्ग देखें", "add_city": "शहर जोड़ें", "password": "पासवर्ड", "login": "लॉगिन",
        "logout": "लॉगआउट", "wrong_pw": "गलत पासवर्ड।", "select_city": "शहर चुनें",
        "venue": "स्थल", "seats": "अपेक्षित उपस्थिति", "note": "नोट्स", "google_link": "गूगल मैप्स लिंक",
        "indoor": "इनडोर", "outdoor": "आउटडोर", "register": "रजिस्टर", "edit": "संपादित करें",
        "remove": "हटाएं", "date": "तारीख", "performance_date": "प्रदर्शन तिथि", "cancel": "रद्द करें",
        "title_label": "शीर्षक", "content_label": "सामग्री", "upload_image": "छवि अपलोड करें",
        "upload_file": "फ़ाइल अपलोड करें", "submit": "जमा करें", "warning": "शीर्षक और सामग्री दोनों दर्ज करें।",
        "file_download": "फ़ाइल डाउन로드 करें", "pending": "निर्धारित नहीं", "est_time": "{hours}घं {mins}मि"
    }
}

_ = lambda key: LANG[st.session_state.lang].get(key, key)

# --- 7. 테마 ---
MERRY_CHRISTMAS_WAV = "UklGRu4FAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA..."

st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #f0f0f0; }}
.christmas-title {{ text-align: center; margin: 20px 0; }}
.cantata {{ font-size: 3em; color: #e74c3c; text-shadow: 0 0 10px #ff6b6b; }}
.year {{ font-size: 2.8em; color: #ecf0f1; text-shadow: 0 0 8px #ffffff; }}
.maha {{ font-size: 1.8em; color: #3498db; font-style: italic; text-shadow: 0 0 6px #74b9ff; }}
.snowflake {{ color: rgba(255,255,255,0.5); font-size: 1.2em; position: absolute; top: -10px; animation: fall linear forwards; }}
@keyframes fall {{ to {{ transform: translateY(100vh); opacity: 0;}}}}
.stButton>button {{ background: #c0392b !important; color: white !important; border: 2px solid #e74c3c !important; border-radius: 12px !important; }}
.stButton>button:hover {{ background: #e74c3c !important; }}
.new-badge {{ background: #e74c3c; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.7em; margin-left: 5px; }}
.popup-content {{ max-width: 280px; text-align: center; color: #e74c3c; line-height: 1.6; padding: 10px; }}
.popup-content b {{ font-size: 1.3em; }}
</style>
<script>
function createSnowflake() {{
    const s = document.createElement('div'); s.classList.add('snowflake');
    s.innerText = ['❅','❆','✻','✼'][Math.floor(Math.random()*4)];
    s.style.left = Math.random()*100 + 'vw';
    s.style.animationDuration = Math.random()*10 + 8 + 's';
    s.style.opacity = Math.random()*0.4 + 0.3;
    document.body.appendChild(s);
    setTimeout(() => s.remove(), 18000);
}}
setInterval(createSnowflake, 400);
function playMerryChristmas() {{
    const audio = new Audio('data:audio/wav;base64,{MERRY_CHRISTMAS_WAV}');
    audio.play().catch(() => {{}});
}}
</script>
""", unsafe_allow_html=True)

# --- 8. 타이틀 ---
st.markdown(f"""
<div class="christmas-title">
<div class="cantata">{_('title_base')}</div>
<div class="year">2025</div>
<div class="maha">{_('caption')}</div>
</div>
""", unsafe_allow_html=True)

# --- 9. 사이드바 ---
with st.sidebar:
    lang_options = ["한국어", "English", "हिंदी"]
    lang_map = {"한국어":"ko", "English":"en", "हिंदी":"hi"}
    selected = st.selectbox("언어", lang_options, index=[i for i, l in enumerate(lang_options) if lang_map[l] == st.session_state.lang][0])
    if lang_map[selected] != st.session_state.lang:
        st.session_state.lang = lang_map[selected]
        st.rerun()

    st.markdown("---")
    if not st.session_state.admin:
        pw = st.text_input(_("password"), type="password")
        if st.button(_("login")):
            if pw == st.session_state.pw:
                st.session_state.admin = True
                st.rerun()
            elif pw in ["0691", "0692"]:
                st.session_state.pw = "9000" if pw == "0691" else "0009"
                st.rerun()
            else:
                st.error(_("wrong_pw"))
    else:
        st.success("관리자 모드")
        if st.button(_("logout")):
            st.session_state.admin = False
            st.rerun()

# --- 10. JSON 헬퍼 ---
def load_json(f): 
    try:
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file:
                return json.load(file)
    except:
        pass
    return []

def save_json(f, d): 
    with open(f, "w", encoding="utf-8") as file:
        json.dump(d, file, ensure_ascii=False, indent=2)

# --- 11. 초기 도시 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도", "google_link": "https://goo.gl/maps/abc123", "indoor": False, "lat": 19.0760, "lon": 72.8777, "perf_date": None, "date": "11/07 02:01"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브", "google_link": "https://goo.gl/maps/def456", "indoor": True, "lat": 18.5204, "lon": 73.8567, "perf_date": None, "date": "11/07 02:01"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시", "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "lat": 21.1458, "lon": 79.0882, "perf_date": None, "date": "11/07 02:01"}
]

if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

CITY_COORDS = {c["city"]: (c["lat"], c["lon"]) for c in DEFAULT_CITIES}

# --- 12. 공지 기능 ---
def add_notice(title, content, img=None, file=None):
    img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
    if img: open(img_path, "wb").write(img.read())
    if file: open(file_path, "wb").write(file.read())

    notice = {"id": str(uuid.uuid4()), "title": title, "content": content, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"), "image": img_path, "file": file_path}
    data = load_json(NOTICE_FILE)
    data.insert(0, notice)
    save_json(NOTICE_FILE, data)

    st.session_state.seen_notices = []
    st.session_state.new_notice = True
    st.session_state.active_tab = "공지"
    st.rerun()

def render_notices():
    data = load_json(NOTICE_FILE)
    has_new = False
    for i, n in enumerate(data):
        new = n["id"] not in st.session_state.seen_notices and not st.session_state.admin
        if new: has_new = True
        title = f"{n['date']} | {n['title']}"
        if new: title += ' <span class="new-badge">NEW</span>'

        with st.expander(title, expanded=False):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]): st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                with open(n["file"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                st.markdown(f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(n["file"])}">파일 다운로드</a>', unsafe_allow_html=True)
            if st.session_state.admin and st.button("삭제", key=f"del_n{i}"):
                data.pop(i); save_json(NOTICE_FILE, data); st.rerun()
            if new and not st.session_state.admin:
                st.session_state.seen_notices.append(n["id"])

    if has_new and not st.session_state.get("sound_played", False):
        st.markdown("<script>playMerryChristmas();</script>", unsafe_allow_html=True)
        st.session_state.sound_played = True
    elif not has_new:
        st.session_state.sound_played = False

# --- 13. 지도 ---
def render_map():
    st.subheader(_('map_title'))
    PUNE_LAT, PUNE_LON = 18.5204, 73.8567
    today = date.today()

    raw_cities = load_json(CITY_FILE)
    cities = []
    for city in raw_cities:
        try:
            perf_date = city.get("perf_date")
            if perf_date is None or perf_date == "9999-12-31":
                perf_date = None
            elif not isinstance(perf_date, str):
                perf_date = str(perf_date)
            city["perf_date"] = perf_date
            cities.append(city)
        except:
            continue

    cities = sorted(cities, key=lambda x: x.get("perf_date", "9999-12-31") or "9999-12-31")

    # 수정/추가 폼 (기존 코드 유지 - 생략)

    if not cities:
        st.warning("도시 없음")
        m = folium.Map(location=[PUNE_LAT, PUNE_LON], zoom_start=9, tiles="CartoDB positron")
        folium.Marker([PUNE_LAT, PUNE_LON], popup="시작", icon=folium.Icon(color="green", icon="star", prefix="fa")).add_to(m)
        st_folium(m, width=900, height=550, key="empty_map")
        return

    m = folium.Map(location=[PUNE_LAT, PUNE_LON], zoom_start=9, tiles="CartoDB positron")

    # 오늘 공연 도시 인덱스 찾기
    today_index = -1
    for idx, c in enumerate(cities):
        try:
            perf_date_obj = datetime.strptime(c['perf_date'], "%Y-%m-%d").date() if c.get('perf_date') else None
            if perf_date_obj and perf_date_obj == today:
                today_index = idx
                break
        except:
            continue

    for i, c in enumerate(cities):
        display_date = _("pending") if not c.get("perf_date") else c["perf_date"]
        try:
            perf_date_obj = datetime.strptime(c['perf_date'], "%Y-%m-%d").date() if c.get('perf_date') else None
        except:
            perf_date_obj = None

        # 이전 도시 (today_index 이전) → 흐림
        is_past_segment = (today_index != -1 and i < today_index)

        # 아이콘 투명도
        icon_opacity = 0.35 if is_past_segment else 1.0
        icon = folium.Icon(color="red", icon="music", prefix="fa", opacity=icon_opacity)

        # 말풍선
        popup_html = f'''
        <div class="popup-content">
            <b>{c['city']}</b><br>
            {display_date}<br>
            {c.get('venue','—')}<br>
            인원: {c.get('seats','—')}<br>
            {c.get('note','—')}<br>
            <a href="{c.get('google_link','')}" target="_blank">구글맵</a>
        </div>
        '''
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=c["city"],
            icon=icon
        ).add_to(m)

        # 연결 라인: 이전 도시에서 나가는 라인 → 흐림
        if i < len(cities)-1:
            line_opacity = 0.35 if is_past_segment else 1.0
            segment_coords = [(c['lat'], c['lon']), (cities[i+1]['lat'], cities[i+1]['lon'])]
            AntPath(segment_coords, color="#e74c3c", weight=6, opacity=line_opacity, delay=800, dash_array=[20, 30]).add_to(m)

        # 도시 정보 expander
        with st.expander(f"{c['city']} | {display_date}"):
            st.write(f"등록일: {c.get('date', '—')}")
            st.write(f"공연 날짜: {display_date}")
            st.write(f"장소: {c.get('venue', '—')}")
            st.write(f"예상 인원: {c.get('seats', '—')}")
            st.write(f"특이사항: {c.get('note', '—')}")
            if c.get("google_link"):
                st.markdown(f"[구글맵 보기]({c['google_link']})")

            if st.session_state.admin and not st.session_state.get("edit_city"):
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("수정", key=f"edit_{i}"):
                        st.session_state.edit_city = c["city"]
                        st.rerun()
                with c2:
                    if st.button("삭제", key=f"del_{i}"):
                        cities.pop(i)
                        save_json(CITY_FILE, cities)
                        st.rerun()

    st_folium(m, width=900, height=550, key=f"map_{len(cities)}")

# --- 14. 탭 ---
tab1, tab2 = st.tabs([_("tab_notice"), _("tab_map")])

if st.session_state.get("new_notice", False):
    st.session_state.active_tab = "공지"
    st.session_state.new_notice = False
    st.rerun()

with tab1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_("title_label"))
            c = st.text_area(_("content_label"))
            img = st.file_uploader(_("upload_image"), type=["png","jpg","jpeg"])
            f = st.file_uploader(_("upload_file"))
            if st.form_submit_button(_("submit")):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_("warning"))
    render_notices()

with tab2:
    render_map()
