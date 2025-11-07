import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, sin, cos, sqrt, asin, atan2, degrees
import requests

# --- 1. 기본 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh_user")

# --- 2. 파일/디렉토리 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 3. 다국어 ---
LANG = {
    "ko": {
        "tab_notice": "공지", "tab_map": "투어 경로", "today": "오늘", "yesterday": "어제",
        "new_notice_alert": "따끈한 공지가 도착했어요!", "warning": "제목과 내용을 입력하세요."
    },
    "en": {
        "tab_notice": "Notice", "tab_map": "Tour Route", "today": "Today", "yesterday": "Yesterday",
        "new_notice_alert": "Hot new notice arrived!", "warning": "Please enter title and content."
    },
    "hi": {
        "tab_notice": "सूचना", "tab_map": "टूर मार्ग", "today": "आज", "yesterday": "कल",
        "new_notice_alert": "ताज़ा सूचना आई है!", "warning": "कृपया शीर्षक और सामग्री दर्ज करें।"
    }
}

# --- 4. 세션 초기화 ---
defaults = {
    "admin": False, "lang": "ko", "edit_city": None,
    "tab_selection": "공지", "new_notice": False, "sound_played": False,
    "seen_notices": [], "expanded_notices": [], "expanded_cities": [], "last_tab": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

_ = lambda key: LANG.get(st.session_state.lang, LANG["ko"]).get(key, key)

# --- 5. 크리스마스 캐롤 (Base64) ---
CHRISTMAS_CAROL_WAV = "UklGRu4FAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA..."

# --- 6. 🔥 지옥불 알림 + 최대 볼륨 사운드 ---
st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #f0f0f0; }}
.christmas-title {{ text-align: center; margin: 20px 0; }}
.cantata {{ font-size: 3em; color: #e74c3c; text-shadow: 0 0 10px #ff6b6b; }}
.year {{ font-size: 2.8em; color: #ecf0f1; text-shadow: 0 0 8px #ffffff; }}
.maha {{ font-size: 1.8em; color: #3498db; font-style: italic; text-shadow: 0 0 6px #74b9ff; }}

/* 🔥🔥🔥 지옥불 알림 🔥🔥🔥 */
.alert-slide {{
    position: fixed;
    top: 20px;
    right: 10%;
    transform: translateX(0);
    background: linear-gradient(45deg, #ff1a1a, #ff6b1a, #ffcc00, #ff1a1a);
    background-size: 400% 400%;
    color: white;
    padding: 16px 36px;
    border-radius: 60px;
    font-weight: 900;
    font-size: 1.3em;
    z-index: 99999;
    box-shadow: 
        0 0 20px rgba(255, 0, 0, 0.9),
        0 0 40px rgba(255, 100, 0, 0.7),
        0 0 80px rgba(255, 200, 0, 0.5),
        0 0 120px rgba(255, 255, 0, 0.3);
    animation: 
        slideRight 7s forwards,
        pulseBg 1.5s infinite,
        shake 0.5s infinite alternate,
        glow 2s infinite alternate;
    white-space: nowrap;
    border: 3px solid transparent;
    text-shadow: 
        0 0 10px #fff,
        0 0 20px #ff0,
        0 0 30px #f00;
    letter-spacing: 1px;
    font-family: 'Arial Black', sans-serif;
    transform-style: preserve-3d;
    perspective: 1000px;
    overflow: visible;
}}

.alert-slide::before {{
    content: '';
    position: absolute;
    top: -10px; left: -10px; right: -10px; bottom: -10px;
    background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><defs><radialGradient id="fire"><stop offset="0%" stop-color="%23ff0"/><stop offset="100%" stop-color="%23f00"/></radialGradient></defs><circle cx="50" cy="50" r="40" fill="url(%23fire)" opacity="0.6"><animate attributeName="r" values="30;50;30" dur="1s" repeatCount="indefinite"/></circle></svg>') repeat;
    background-size: 30px 30px;
    animation: fireParticles 2s infinite linear;
    z-index: -1;
    border-radius: 70px;
    opacity: 0.8;
}}

@keyframes slideRight {{
    0% {{ transform: translateX(200%) rotateY(90deg); opacity: 0; }}
    15% {{ transform: translateX(0) rotateY(0deg); opacity: 1; }}
    85% {{ transform: translateX(0) rotateY(0deg); opacity: 1; }}
    100% {{ transform: translateX(200%) rotateY(-90deg); opacity: 0; }}
}}

@keyframes pulseBg {{ 0%, 100% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} }}
@keyframes shake {{ 0% {{ transform: translateX(0) rotateY(0); }} 100% {{ transform: translateX(-3px) rotateY(-2deg); }} }}
@keyframes glow {{ 0% {{ box-shadow: 0 0 20px rgba(255,0,0,0.9), 0 0 40px rgba(255,100,0,0.7); }} 100% {{ box-shadow: 0 0 40px rgba(255,0,0,1), 0 0 80px rgba(255,100,0,0.9), 0 0 120px rgba(255,255,0,0.5); }} }}
@keyframes fireParticles {{ 0% {{ background-position: 0 0; }} 100% {{ background-position: 100px 100px; }} }}
@keyframes textFlicker {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.8; }} }}

.alert-slide span {{ animation: textFlicker 0.3s infinite; display: inline-block; }}

@media (max-width: 768px) {{
    .alert-slide {{ right: 5%; font-size: 1.1em; padding: 12px 24px; }}
}}
</style>

<script>
function playChristmasCarol() {{
    try {{
        const audio = new Audio('data:audio/wav;base64,{CHRISTMAS_CAROL_WAV}');
        audio.volume = 1.0;
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const source = ctx.createMediaElementSource(audio);
        const gainNode = ctx.createGain();
        gainNode.gain.value = 5.0;
        const compressor = ctx.createDynamicsCompressor();
        source.connect(gainNode).connect(compressor).connect(ctx.destination);
        if (navigator.vibrate) navigator.vibrate([200, 100, 200, 100, 500]);
        audio.play().catch(() => {{}});
    }} catch(e) {{
        const audio = new Audio('data:audio/wav;base64,{CHRISTMAS_CAROL_WAV}');
        audio.volume = 1.0;
        if (navigator.vibrate) navigator.vibrate(500);
        audio.play().catch(() => {{}});
    }}
}}
</script>
""", unsafe_allow_html=True)

st.markdown('<div class="christmas-title"><div class="cantata">칸타타 투어</div><div class="year">2025</div><div class="maha">마하라스트라</div></div>', unsafe_allow_html=True)

# --- 7. 사이드바 ---
with st.sidebar:
    lang_map = {"한국어": "ko", "English": "en", "हिंदी": "hi"}
    selected = st.selectbox("언어", list(lang_map.keys()), index=list(lang_map.values()).index(st.session_state.lang))
    if lang_map[selected] != st.session_state.lang:
        st.session_state.lang = lang_map[selected]
        st.session_state.tab_selection = _(f"tab_notice")
        st.rerun()

    st.markdown("---")
    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password", key="pw_input")
        if st.button("로그인", key="login_btn"):
            if pw == "0009":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃", key="logout_btn"):
            st.session_state.admin = False
            st.rerun()

# --- 8. JSON 헬퍼 ---
def load_json(f):
    if not os.path.exists(f): return []
    try: return json.load(open(f, "r", encoding="utf-8"))
    except: return []

def save_json(f, d):
    with open(f, "w", encoding="utf-8") as fp:
        json.dump(d, fp, ensure_ascii=False, indent=2)

# --- 9. 초기 도시 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도", "google_link": "https://goo.gl/maps/abc123", "indoor": False, "lat": 19.0760, "lon": 72.8777, "perf_date": None, "date": "11/07 02:01"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브", "google_link": "https://goo.gl/maps/def456", "indoor": True, "lat": 18.5204, "lon": 73.8567, "perf_date": None, "date": "11/07 02:01"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시", "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "lat": 21.1458, "lon": 79.0882, "perf_date": None, "date": "11/07 02:01"}
]
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

# --- 10. 실시간 거리 ---
def get_real_travel_time(lat1, lon1, lat2, lon2):
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")
        if api_key:
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {"origins": f"{lat1},{lon1}", "destinations": f"{lat2},{lon2}", "key": api_key, "mode": "driving"}
            res = requests.get(url, params=params, timeout=5).json()
            if res["rows"][0]["elements"][0]["status"] == "OK":
                dist = res["rows"][0]["elements"][0]["distance"]["value"] / 1000
                mins = res["rows"][0]["elements"][0]["duration"]["value"] // 60
                return dist, mins
    except: pass
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    dist = R * c
    mins = int(dist / 80 * 60)
    return dist, mins

# --- 11. 공지 기능 ---
def format_notice_date(d):
    try:
        nd = datetime.strptime(d.split()[0], "%m/%d").replace(year=date.today().year).date()
        return _("today") if nd == date.today() else _("yesterday") if nd == date.today() - timedelta(days=1) else d.split()[0]
    except: return d.split()[0] if ' ' in d else d

def add_notice(title, content, img=None, file=None):
    img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
    if img: open(img_path, "wb").write(img.read())
    if file: open(file_path, "wb").write(file.read())
    notice = {
        "id": str(uuid.uuid4()), "title": title, "content": content,
        "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
        "image": img_path, "file": file_path
    }
    data = load_json(NOTICE_FILE)
    data.insert(0, notice)
    save_json(NOTICE_FILE, data)
    st.session_state.seen_notices = []
    st.session_state.new_notice = True
    st.session_state.expanded_notices = []
    st.rerun()

def render_notices():
    data = load_json(NOTICE_FILE)
    has_new = False
    for i, n in enumerate(data):
        new = n["id"] not in st.session_state.seen_notices and not st.session_state.admin
        if new: has_new = True
        title = f"{format_notice_date(n['date'])} | {n['title']}" + (' <span class="new-badge">NEW</span>' if new else '')
        exp_key = f"notice_{n['id']}"
        expanded = exp_key in st.session_state.expanded_notices
        with st.expander(title, expanded=expanded):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], width="stretch")
            if n.get("file") and os.path.exists(n["file"]):
                b64 = base64.b64encode(open(n["file"], "rb").read()).decode()
                st.markdown(f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(n["file"])}">파일 다운로드</a>', unsafe_allow_html=True)
            if st.session_state.admin and st.button("삭제", key=f"del_n_{n['id']}"):
                data.pop(i)
                save_json(NOTICE_FILE, data)
                st.rerun()
            if new and not st.session_state.admin:
                st.session_state.seen_notices.append(n["id"])
            if expanded and exp_key not in st.session_state.expanded_notices:
                st.session_state.expanded_notices.append(exp_key)
            elif not expanded and exp_key in st.session_state.expanded_notices:
                st.session_state.expanded_notices.remove(exp_key)

    if has_new and not st.session_state.sound_played:
        st.markdown("<script>playChristmasCarol();</script>", unsafe_allow_html=True)
        st.session_state.sound_played = True
        st.markdown(f'<div class="alert-slide"><span>{_("new_notice_alert")}</span></div>', unsafe_allow_html=True)
    elif not has_new:
        st.session_state.sound_played = False

# --- 12. 지도 ---
def render_map():
    st.subheader("경로 보기")
    today = date.today()
    raw_cities = load_json(CITY_FILE)
    cities = sorted(
        [c | {"perf_date": c.get("perf_date") if c.get("perf_date") not in [None, "9999-12-31"] else "9999-12-31"} for c in raw_cities],
        key=lambda x: x["perf_date"] if x["perf_date"] != "9999-12-31" else "9999-12-31"
    )

    m = folium.Map(location=[18.5204, 73.8567], zoom_start=9, tiles="CartoDB positron")
    if not cities:
        folium.Marker([18.5204, 73.8567], popup="시작", icon=folium.Icon(color="green", icon="star", prefix="fa")).add_to(m)
    else:
        for i, c in enumerate(cities):
            is_past = c.get('perf_date') and c['perf_date'] != "9999-12-31" and datetime.strptime(c['perf_date'], "%Y-%m-%d").date() < today
            icon = folium.Icon(color="red", icon="music", prefix="fa", opacity=0.5 if is_past else 1.0)
            popup = f"<b>{c['city']}</b><br>{c.get('perf_date','미정')}<br>{c.get('venue','—')}"
            folium.Marker([c["lat"], c["lon"]], popup=folium.Popup(popup, max_width=280), tooltip=c["city"], icon=icon).add_to(m)

            if i < len(cities) - 1:
                next_c = cities[i+1]
                dist_km, mins = get_real_travel_time(c['lat'], c['lon'], next_c['lat'], next_c['lon'])
                time_str = f"{mins//60}h {mins%60}m" if mins else ""
                label_text = f"{dist_km:.0f}km {time_str}".strip()
                mid_lat, mid_lon = (c['lat'] + next_c['lat']) / 2, (c['lon'] + next_c['lon']) / 2
                bearing = degrees(atan2(next_c['lon'] - c['lon'], next_c['lat'] - c['lat']))
                folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=f'''
                    <div style="transform: translate(-50%,-50%) rotate({bearing}deg); opacity: {"0.5" if is_past else "1.0"}; color:#e74c3c; font-weight:bold; font-size:12px;">
                    {label_text}</div>''')).add_to(m)
                AntPath([(c['lat'], c['lon']), (next_c['lat'], next_c['lon'])],
                        color="#e74c3c", weight=6, opacity=0.5 if is_past else 1.0,
                        delay=800, dash_array=[20,30]).add_to(m)

            exp_key = f"city_{c['city']}"
            expanded = exp_key in st.session_state.expanded_cities
            with st.expander(f"{c['city']} | {c.get('perf_date','미정')}", expanded=expanded):
                info = {"등록일": "date", "공연 날짜": "perf_date", "장소": "venue", "예상 인원": "seats", "특이사항": "note"}
                for k, v in info.items():
                    st.write(f"{k}: {c.get(v, '—')}")
                if c.get("google_link"):
                    st.markdown(f"[구글맵 보기]({c['google_link']})")
                if st.session_state.admin and not st.session_state.edit_city:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("수정", key=f"edit_city_{i}"):
                            st.session_state.edit_city = c["city"]
                            st.rerun()
                    with c2:
                        if st.button("삭제", key=f"del_city_{i}"):
                            raw_cities = [x for x in raw_cities if x["city"] != c["city"]]
                            save_json(CITY_FILE, raw_cities)
                            st.rerun()
                if expanded and exp_key not in st.session_state.expanded_cities:
                    st.session_state.expanded_cities.append(exp_key)
                elif not expanded and exp_key in st.session_state.expanded_cities:
                    st.session_state.expanded_cities.remove(exp_key)

    st_folium(m, width=900, height=550, key="tour_map")

# --- 13. 탭 ---
tab_selection = st.radio(
    "탭 선택",
    [_(f"tab_notice"), _(f"tab_map")],
    index=0 if st.session_state.tab_selection == _(f"tab_notice") else 1,
    horizontal=True,
    key="main_tab"
)

if tab_selection != st.session_state.get("last_tab"):
    st.session_state.expanded_notices = []
    st.session_state.expanded_cities = []
    st.session_state.last_tab = tab_selection
    st.rerun()

if st.session_state.get("new_notice", False):
    st.session_state.tab_selection = _(f"tab_notice")
    st.session_state.new_notice = False
    st.rerun()

# --- 14. 렌더링 ---
if tab_selection == _(f"tab_notice"):
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            title = st.text_input("제목")
            content = st.text_area("내용")
            img = st.file_uploader("이미지", type=["png", "jpg"])
            file = st.file_uploader("파일")
            if st.form_submit_button("등록"):
                if title.strip() and content.strip():
                    add_notice(title, content, img, file)
                else:
                    st.warning(_("warning"))
    render_notices()
else:
    render_map()
