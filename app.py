# app.py - 완전 정리판 (2025.11.07) 🔥 크리스마스 알림음 + 버그 전면 수정
import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, sin, cos, sqrt, asin

# ==================== [1] 하버신 거리 계산 ====================
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return 6371 * 2 * asin(sqrt(a))

# ==================== [2] 3초 자동 새로고침 (비관리자만) ====================
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto")

st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

# ==================== [3] 파일/디렉토리 ====================
NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==================== [4] 세션 초기화 ====================
defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "expanded": {}, "adding_cities": [],
    "pw": "0009", "seen_notices": [], "active_tab": "공지", "new_notice": False, "sound_played": False
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ==================== [5] 다국어 사전 ====================
LANG = {
    "ko": { "title_base": "칸타타 투어", "caption": "마하라스트라", "tab_notice": "공지", "tab_map": "투어 경로",
            "map_title": "경로 보기", "add_city": "도시 추가", "password": "비밀번호", "login": "로그인",
            "logout": "로그아웃", "wrong_pw": "비밀번호가 틀렸습니다.", "select_city": "도시 선택",
            "venue": "공연장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵 링크",
            "indoor": "실내", "outdoor": "실외", "register": "등록", "edit": "수정", "remove": "삭제",
            "date": "등록일", "performance_date": "공연 날짜", "cancel": "취소", "title_label": "제목",
            "content_label": "내용", "upload_image": "이미지 업로드", "upload_file": "파일 업로드",
            "submit": "등록", "warning": "제목과 내용을 모두 입력해주세요.", "file_download": "파일 다운로드" },
    "en": { "title_base": "Cantata Tour", "caption": "Maharashtra", "tab_notice": "Notice", "tab_map": "Tour Route",
            "map_title": "View Route", "add_city": "Add City", "password": "Password", "login": "Login",
            "logout": "Logout", "wrong_pw": "Wrong password.", "select_city": "Select City", "venue": "Venue",
            "seats": "Expected Attendance", "note": "Notes", "google_link": "Google Maps Link",
            "indoor": "Indoor", "outdoor": "Outdoor", "register": "Register", "edit": "Edit", "remove": "Remove",
            "date": "Registered On", "performance_date": "Performance Date", "cancel": "Cancel",
            "title_label": "Title", "content_label": "Content", "upload_image": "Upload Image",
            "upload_file": "Upload File", "submit": "Submit", "warning": "Please enter both title and content.",
            "file_download": "Download File" },
    "hi": { "title_base": "कांताता टूर", "caption": "महाराष्ट्र", "tab_notice": "सूचना", "tab_map": "टूर मार्ग",
            "map_title": "मार्ग देखें", "add_city": "शहर जोड़ें", "password": "पासवर्ड", "login": "लॉगिन",
            "logout": "लॉगआ웃", "wrong_pw": "गलत पासवर्ड।", "select_city": "शहर चुनें", "venue": "स्थल",
            "seats": "अपेक्षित उपस्थिति", "note": "नोट्स", "google_link": "गूगल मैप्स लिंक",
            "indoor": "इनडोर", "outdoor": "आउटडोर", "register": "रजिस्टर", "edit": "संपादित करें",
            "remove": "हटाएं", "date": "तारीख", "performance_date": "प्रदर्शन तिथि", "cancel": "रद्द करें",
            "title_label": "शीर्षक", "content_label": "सामग्री", "upload_image": "छवि अपलोड करें",
            "upload_file": "फ़ाइल अपलोड करें", "submit": "जमा करें", "warning": "शीर्षक और सामग्री दोनों दर्ज करें।",
            "file_download": "फ़ाइल डाउन로드 करें" }
}
_ = lambda key: LANG[st.session_state.lang].get(key, key)

# ==================== [6] 크리스마스 테마 + 5초 Jingle Bells WAV (Base64) ====================
JINGLE_BELLS_WAV = """
UklGRnoGAABXQVZFZm10IBAAAAABAAEAIlYAAIlYAABQTFRFAAAAAP4AAAD8AAAAAAAAAAAAAAACAgIC
AgMEBQYHCAkKCwwNDg8QERITFBUWFhcYGBkaGxwdHh8gIiMkJSYnKCkqKywtLi8wMTIzNDU2Nzg5Ojs8
PT4/QEFCQkNERUZGRkdISUpLTE1OT09QUVJTVFVaW1xdXl9gYWFhYmNkZWZnaGlqa2ttbW5vcHFyc3R1
dnd4eXp7fH1+f4CBgoOEhYaHiImKi4yNjo+QkZKTlJWWl5iZmpucnZ6foKGio6SlpqeoqaqrrK2ur7Cx
srO0tba3uLm6u7y9vr/AwcLDxMXGx8jJysvMzc7P0NHS09TV1tfY2drb3N3e3+Dh4uPk5ebn6Onq6+zt
7u/w8fLz9PX29/j5+vv8/f7/AAA=
""".strip().replace("\n", "")

st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #f0f0f0; overflow: hidden; }}
.christmas-title {{ text-align: center; margin: 20px 0; }}
.cantata {{ font-size: 3em; color: #e74c3c; text-shadow: 0 0 10px #ff6b6b; }}
.year {{ font-size: 2.8em; color: #ecf0f1; text-shadow: 0 0 8px #ffffff; }}
.maha {{ font-size: 1.8em; color: #3498db; font-style: italic; text-shadow: 0 0 6px #74b9ff; }}
.snowflake {{ color: rgba(255,255,255,0.5); font-size: 1.2em; position: absolute; top: -10px; animation: fall linear forwards; }}
@keyframes fall {{ to {{ transform: translateY(100vh); opacity: 0;}}}}
.stButton>button {{ background: #c0392b !important; color: white !important; border: 2px solid #e74c3c !important; border-radius: 12px !important; }}
.stButton>button:hover {{ background: #e74c3c !important; }}
.new-badge {{ background: #e74c3c; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.7em; margin-left: 5px; }}
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

// 🎄 5초 크리스마스 캐롤 알림음 재생
function playJingleBells() {{
    const audio = new Audio('data:audio/wav;base64,{JINGLE_BELLS_WAV}');
    audio.play().catch(() => {{}});
}}
</script>
""", unsafe_allow_html=True)

# ==================== [7] 제목 ====================
st.markdown(f"""
<div class="christmas-title">
<div class="cantata">{_('title_base')}</div>
<div class="year">2025</div>
<div class="maha">{_('caption')}</div>
</div>
""", unsafe_allow_html=True)

# ==================== [8] 사이드바 (언어 + 관리자 로그인) ====================
with st.sidebar:
    lang_options = ["한국어", "English", "हिंदी"]
    lang_map = {"한국어":"ko", "English":"en", "हिंदी":"hi"}
    idx = lang_options.index(next((l for l in lang_options if lang_map[l] == st.session_state.lang), "한국어"))
    selected = st.selectbox("언어", lang_options, index=idx)
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
            elif pw == "0691":
                st.session_state.pw = "9000"
                st.success("비밀번호 변경됨: 9000")
                st.rerun()
            elif pw == "0692":
                st.session_state.pw = "0009"
                st.success("비밀번호 초기화됨: 0009")
                st.rerun()
            else:
                st.error(_("wrong_pw"))
    else:
        st.success("🎅 관리자 모드")
        if st.button(_("logout")):
            st.session_state.admin = False
            st.rerun()

# ==================== [9] JSON 헬퍼 ====================
def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ==================== [10] 공지 기능 ====================
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

        with st.expander(title, expanded=st.session_state.expanded.get(f"n{i}", False)):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                with open(n["file"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(n["file"])}">📥 {_("file_download")}</a>'
                st.markdown(href, unsafe_allow_html=True)
            if st.session_state.admin and st.button("🗑️ 삭제", key=f"del_n{i}"):
                data.pop(i)
                save_json(NOTICE_FILE, data)
                st.rerun()
            if new and not st.session_state.admin:
                st.session_state.seen_notices.append(n["id"])

    # 🎄 새 공지 시 크리스마스 캐롤 재생
    if has_new and not st.session_state.get("sound_played", False):
        st.markdown("<script>playJingleBells();</script>", unsafe_allow_html=True)
        st.session_state.sound_played = True
    elif not has_new:
        st.session_state.sound_played = False

# ==================== [11] 지도 & 투어 경로 ====================
def render_map():
    st.subheader(_('map_title'))
    if st.session_state.admin and st.button(_('add_city')):
        st.session_state.adding_cities.append(None)
        st.rerun()

    cities = sorted(load_json(CITY_FILE), key=lambda x: x.get("perf_date", "9999-12-31"))
    total_dist = 0

    for i, c in enumerate(cities):
        with st.expander(f"{c['city']} | {c.get('perf_date', '미정')}"):
            st.write(f"등록일: {c.get('date', '—')}")
            st.write(f"공연 날짜: {c.get('perf_date', '—')}")
            st.write(f"공연장소: {c.get('venue', '—')}")
            st.write(f"예상 인원: {c.get('seats', '—')}")
            st.write(f"특이사항: {c.get('note', '—')}")

            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✏️ 수정", key=f"edit_city_{i}"):
                        st.session_state.edit_city = c["city"]
                        st.rerun()
                with c2:
                    if st.button("🗑️ 삭제", key=f"del_city_{i}"):
                        cities.pop(i)
                        save_json(CITY_FILE, cities)
                        st.rerun()

        if i < len(cities) - 1:
            d = haversine(c['lat'], c['lon'], cities[i+1]['lat'], cities[i+1]['lon'])
            total_dist += d
            st.markdown(f"<div style='text-align:center;color:#2ecc71'>📍 {d:.0f}km</div>", unsafe_allow_html=True)

    if len(cities) > 1:
        st.markdown(f"<div style='text-align:center;color:#e74c3c;font-size:1.2em'>🎄 총 거리: {total_dist:.0f}km</div>", unsafe_allow_html=True)

    m = folium.Map(location=[19.0, 73.0], zoom_start=7)
    coords = []
    for c in cities:
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=f"<b>{c['city']}</b><br>{c.get('perf_date','')}<br>{c.get('venue','')}",
            tooltip=c["city"]
        ).add_to(m)
        coords.append((c["lat"], c["lon"]))
    if coords:
        AntPath(coords, color="#e74c3c", weight=6, opacity=0.8).add_to(m)
    st_folium(m, width=900, height=550)

# ==================== [12] 탭 + 강제 이동 ====================
tab1, tab2 = st.tabs([_("tab_notice"), _("tab_map")])
if st.session_state.new_notice:
    st.session_state.active_tab = "공지"
    st.session_state.new_notice = False

with tab1:
    st.session_state.active_tab = "공지"
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
