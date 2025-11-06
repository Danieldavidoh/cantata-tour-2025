import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, cos, sin, asin, sqrt

# ===========================
# 기본 설정
# ===========================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ===========================
# Haversine 거리 계산
# ===========================
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371
    return c * r

# ===========================
# 자동 새로고침 (일반 모드)
# ===========================
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh")

# ===========================
# 세션 기본값 초기화
# ===========================
defaults = {
    "admin": False,
    "lang": "ko",
    "edit_city": None,
    "expanded": {},
    "adding_cities": [],
    "pw": "0009",
    "seen_notices": []
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ===========================
# 다국어 설정
# ===========================
LANG = {
    "ko": { 
        "title_base": "칸타타 투어", "caption": "마하라스트라", 
        "tab_notice": "공지", "tab_map": "투어 경로", "map_title": "경로 보기",
        "add_city": "도시 추가", "password": "비밀번호", "login": "로그인",
        "logout": "로그아웃", "wrong_pw": "비밀번호가 틀렸습니다.",
        "select_city": "도시 선택", "venue": "공연장소", "seats": "예상 인원",
        "note": "특이사항", "google_link": "구글맵 링크",
        "indoor": "실내", "outdoor": "실외", "register": "등록", 
        "edit": "수정", "remove": "삭제", "date": "등록일", 
        "performance_date": "공연 날짜", "cancel": "취소", 
        "title_label": "제목", "content_label": "내용", 
        "upload_image": "이미지 업로드", "upload_file": "파일 업로드",
        "submit": "등록", "warning": "제목과 내용을 모두 입력해주세요.",
        "file_download": "파일 다운로드", "change_pw": "비밀번호 변경",
        "new_pw": "새 비밀번호", "confirm_pw": "비밀번호 확인",
        "pw_changed": "비밀번호가 변경되었습니다.", 
        "pw_mismatch": "비밀번호가 일치하지 않습니다."
    },
    "en": { 
        "title_base": "Cantata Tour", "caption": "Maharashtra", 
        "tab_notice": "Notice", "tab_map": "Tour Route", "map_title": "View Route",
        "add_city": "Add City", "password": "Password", "login": "Login",
        "logout": "Logout", "wrong_pw": "Wrong password.", 
        "select_city": "Select City", "venue": "Venue", "seats": "Expected Attendance",
        "note": "Notes", "google_link": "Google Maps Link", 
        "indoor": "Indoor", "outdoor": "Outdoor", "register": "Register", 
        "edit": "Edit", "remove": "Remove", "date": "Registered On", 
        "performance_date": "Performance Date", "cancel": "Cancel",
        "title_label": "Title", "content_label": "Content", 
        "upload_image": "Upload Image", "upload_file": "Upload File",
        "submit": "Submit", "warning": "Please enter both title and content.",
        "file_download": "Download File", "change_pw": "Change Password", 
        "new_pw": "New Password", "confirm_pw": "Confirm Password",
        "pw_changed": "Password changed.", "pw_mismatch": "Passwords do not match."
    }
}

# ===== 다국어 래퍼 클래스 (호출/색인 모두 지원)
class Trans:
    def __init__(self, lang_map):
        self.lang_map = lang_map
    def __call__(self, key):
        lang = st.session_state.get("lang", "ko")
        return self.lang_map.get(lang, {}).get(key, key)
    def __getitem__(self, key):
        return self.__call__(key)
_ = Trans(LANG)

# ===========================
# 크리스마스 테마
# ===========================
christmas_night = """
<style>
.stApp { background: linear-gradient(135deg,#0f0c29,#302b63,#24243e); color:#f0f0f0; font-family:'Segoe UI',sans-serif; overflow:hidden; }
.christmas-title { text-align:center; margin:20px 0; }
.cantata { font-size:3em; font-weight:bold; color:#e74c3c; text-shadow:0 0 10px #ff6b6b; }
.year { font-size:2.8em; font-weight:bold; color:#ecf0f1; text-shadow:0 0 8px #ffffff; }
.maha { font-size:1.8em; color:#3498db; font-style:italic; text-shadow:0 0 6px #74b9ff; }
</style>
"""
st.markdown(christmas_night, unsafe_allow_html=True)

# ===========================
# 제목
# ===========================
st.markdown(
    f'<div class="christmas-title">'
    f'<div class="cantata">{_("title_base")}</div>'
    f'<div class="year">2025</div>'
    f'<div class="maha">{_("caption")}</div>'
    f'</div>',
    unsafe_allow_html=True
)

# ===========================
# 유틸리티
# ===========================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_latlon_from_shortlink(short_url):
    try:
        r = requests.get(short_url, allow_redirects=True, timeout=5)
        match = re.search(r'@([0-9.\-]+),([0-9.\-]+)', r.url)
        if match:
            return float(match.group(1)), float(match.group(2))
    except:
        return None, None
    return None, None

# ===========================
# 공지사항 관리
# ===========================
def add_notice(title, content, image_file=None, upload_file=None):
    img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_file.name}") if image_file else None
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{upload_file.name}") if upload_file else None
    if image_file:
        with open(img_path, "wb") as f: f.write(image_file.read())
    if upload_file:
        with open(file_path, "wb") as f: f.write(upload_file.read())
    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
        "image": img_path,
        "file": file_path
    }
    data = load_json(NOTICE_FILE)
    data.insert(0, new_notice)
    save_json(NOTICE_FILE, data)
    st.session_state.expanded = {}
    st.session_state.seen_notices = []
    st.toast("공지가 등록되었습니다.")
    st.rerun()

def render_notice_list(show_delete=False):
    data = load_json(NOTICE_FILE)
    has_new = False
    expanded_any = False

    for idx, n in enumerate(data):
        nid = n["id"]
        is_new = nid not in st.session_state.seen_notices
        title_display = f"{n['date']} | {n['title']}"
        if is_new and not st.session_state.admin:
            title_display += ' <span class="new-badge">NEW</span>'

        key = f"notice_{idx}"
        expanded = st.session_state.expanded.get(key, False)
        with st.expander(title_display, expanded=expanded):
            expanded_any = True
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                href = f'<a href="data:file/octet-stream;base64,{base64.b64encode(open(n["file"],"rb").read()).decode()}" download="{os.path.basename(n["file"])}">🎁 {_("file_download")}</a>'
                st.markdown(href, unsafe_allow_html=True)
            if show_delete and st.button(_("remove"), key=f"del_{idx}"):
                data.pop(idx)
                save_json(NOTICE_FILE, data)
                st.toast("공지가 삭제되었습니다.")
                st.rerun()
            if is_new and expanded:
                st.session_state.seen_notices.append(nid)

        st.session_state.expanded[key] = expanded

    if expanded_any:
        st.markdown('<div style="text-align:right;"><button onclick="window.scrollTo(0,0)" class="close-all">닫기</button></div>', unsafe_allow_html=True)
        st.markdown("""
        <style>
        .close-all {
            background:#e74c3c; color:white; border:none;
            border-radius:10px; padding:6px 12px; font-weight:bold;
            cursor:pointer; margin-top:8px;
        }
        .close-all:hover { background:#c0392b; }
        </style>
        """, unsafe_allow_html=True)

# ===========================
# 지도 / 도시 관리
# ===========================
def render_map():
    st.subheader(f"🎅 {_('map_title')}")
    cities_data = load_json(CITY_FILE)
    m = folium.Map(location=[19.0, 73.0], zoom_start=6)
    coords = []

    for c in cities_data:
        popup_html = f"""
        <div style="width:220px;">
        <b>{c['city']}</b><br>
        날짜: {c.get('perf_date','')}<br>
        장소: {c.get('venue','')}<br>
        인원: {c.get('seats','')}<br>
        형태: {c.get('type','')}<br>
        <a href="{c.get('map_link','#')}" target="_blank">길안내</a><br>
        특이사항: {c.get('note','')}
        </div>
        """
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=popup_html,
            tooltip=c["city"],
            icon=folium.Icon(color="red", icon="music")
        ).add_to(m)
        coords.append((c["lat"], c["lon"]))

    if coords:
        AntPath(coords, color="#e74c3c", weight=5, delay=800).add_to(m)

    st_folium(m, width=900, height=550)

# ===========================
# 탭 구성
# ===========================
tab1, tab2 = st.tabs([f"🎁 {_('tab_notice')}", f"🗺️ {_('tab_map')}"])
with tab1:
    render_notice_list(show_delete=st.session_state.admin)
with tab2:
    render_map()

# ===========================
# 조용한 눈 내리는 효과
# ===========================
silent_snow = """
<style>
.silent-snowflake {
    position: fixed;
    top: -10px;
    color: rgba(255,255,255,0.7);
    font-size: 1em;
    pointer-events: none;
    z-index: 0;
    user-select: none;
    animation: fall_slow linear forwards;
}
@keyframes fall_slow {
    0% { transform: translateY(0px) translateX(0px); opacity: 0.9; }
    100% { transform: translateY(100vh) translateX(30px); opacity: 0.1; }
}
</style>
<script>
function createSilentSnowflake() {
    const snow = document.createElement('div');
    snow.classList.add('silent-snowflake');
    snow.textContent = ['❅','❆','✻','✼'][Math.floor(Math.random()*4)];
    snow.style.left = Math.random() * 100 + 'vw';
    snow.style.fontSize = (Math.random() * 1.2 + 0.8) + 'em';
    snow.style.animationDuration = (Math.random() * 10 + 20) + 's';
    document.body.appendChild(snow);
    setTimeout(() => snow.remove(), 20000);
}
setInterval(createSilentSnowflake, 700);
</script>
"""
st.markdown(silent_snow, unsafe_allow_html=True)
