# app.py - 칸타타 투어 2025 (최종 완전판 + 마하라슈트라 주요 도시 3개 기본 로드) 🎄
# 주요 도시: Mumbai, Pune, Nagpur 자동 추가 / 도시 추가 시 selectbox로 선택 + 세부 입력

import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, sin, cos, sqrt, asin

# --- 1. 하버신 거리 계산 ---
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return 6371 * 2 * asin(sqrt(a))

# --- 2. 자동 리프레시 (사용자 전용) ---
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh_user")

st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

# --- 3. 파일/디렉토리 ---
NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 4. 세션 상태 초기화 ---
defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "expanded": {}, "adding_cities": [],
    "pw": "0009", "seen_notices": [], "active_tab": "공지", "new_notice": False, "sound_played": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 5. 다국어 사전 ---
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
            "logout": "लॉगआउट", "wrong_pw": "गलत पासवर्ड।", "select_city": "शहर चुनें", "venue": "स्थल",
            "seats": "अपेक्षित उपस्थिति", "note": "नोट्स", "google_link": "गूगल मैप्स लिंक",
            "indoor": "इनडोर", "outdoor": "आउटडोर", "register": "रजिस्टर", "edit": "संपादित करें",
            "remove": "हटाएं", "date": "तारीख", "performance_date": "प्रदर्शन तिथि", "cancel": "रद्द करें",
            "title_label": "शीर्षक", "content_label": "सामग्री", "upload_image": "छवि अपलोड करें",
            "upload_file": "फ़ाइल अपलोड करें", "submit": "जमा करें", "warning": "शीर्षक और सामग्री दोनों दर्ज करें।",
            "file_download": "फ़ाइल डाउन로드 करें" }
}

# --- 6. 번역 함수 ---
_ = lambda key: LANG[st.session_state.lang].get(key, key)

# --- 7. 크리스마스 테마 + 캐롤 알람음 ---
MERRY_CHRISTMAS_WAV = "UklGRu4FAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA..."  # 실제 base64로 교체

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

# --- 8. 메인 타이틀 ---
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

# --- 11. 초기 도시 데이터 (마하라슈트라 주요 3개: Mumbai, Pune, Nagpur) ---
DEFAULT_CITIES = [
    {
        "city": "Mumbai",
        "venue": "Gateway of India",
        "seats": "5000",
        "note": "인도 영화 수도",
        "google_link": "https://goo.gl/maps/abc123",
        "indoor": False,
        "lat": 19.0760,
        "lon": 72.8777,
        "perf_date": None,
        "date": "11/07 02:01"
    },
    {
        "city": "Pune",
        "venue": "Shaniwar Wada",
        "seats": "3000",
        "note": "IT 허브",
        "google_link": "https://goo.gl/maps/def456",
        "indoor": True,
        "lat": 18.5204,
        "lon": 73.8567,
        "perf_date": None,
        "date": "11/07 02:01"
    },
    {
        "city": "Nagpur",
        "venue": "Deekshabhoomi",
        "seats": "2000",
        "note": "오렌지 도시",
        "google_link": "https://goo.gl/maps/ghi789",
        "indoor": False,
        "lat": 21.1458,
        "lon": 79.0882,
        "perf_date": None,
        "date": "11/07 02:01"
    }
]

# 초기 데이터 저장 (한 번만)
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

# --- 12. 공지 기능 ---
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

        with st.expander(title, expanded=False):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]): 
                st.image(n["image"], use_container_width=True)
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

# --- 13. 투어 경로 (기본 도시 3개 로드 + selectbox 입력) ---
def render_map():
    st.subheader(_('map_title'))

    # --- Pune 중심 좌표 ---
    PUNE_LAT, PUNE_LON = 18.5204, 73.8567
    today = date.today()

    # --- 안전한 데이터 로드 및 정렬 ---
    raw_cities = load_json(CITY_FILE)
    cities = []
    for city in raw_cities:
        try:
            perf_date = city.get("perf_date")
            if perf_date is None:
                perf_date = "9999-12-31"
            elif not isinstance(perf_date, str):
                perf_date = str(perf_date)
            city["perf_date"] = perf_date
            cities.append(city)
        except:
            continue

    cities = sorted(cities, key=lambda x: x.get("perf_date", "9999-12-31"))

    # --- 관리자: 도시 추가 폼 (selectbox + 세부 입력) ---
    if st.session_state.admin:
        with st.expander("도시 추가", expanded=True):
            with st.form("add_city_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    # 주요 도시 selectbox
                    major_cities = ["Mumbai", "Pune", "Nagpur"]
                    selected_city = st.selectbox(_("select_city"), options=major_cities, placeholder="도시 선택")
                    venue = st.text_input(_("venue"), placeholder="예: Gateway of India")
                    perf_date_input = st.date_input(_("performance_date"), value=None)
                with col2:
                    # 예상인원 ±50 단위
                    seats = st.number_input(_("seats"), min_value=0, step=50, value=500)
                    note = st.text_area(_("note"), height=80)
                    gmap = st.text_input(_("google_link"))

                lat_lon_cols = st.columns(2)
                with lat_lon_cols[0]:
                    lat = st.number_input("위도 (Lat)", format="%.6f", value=PUNE_LAT)
                with lat_lon_cols[1]:
                    lon = st.number_input("경도 (Lon)", format="%.6f", value=PUNE_LON)
                indoor = st.checkbox(_("indoor"), value=True)

                if st.form_submit_button(_("register"), use_container_width=True):
                    if not selected_city or not venue.strip():
                        st.error("도시 선택과 장소는 필수입니다!")
                    else:
                        new_city = {
                            "city": selected_city,
                            "venue": venue.strip(),
                            "seats": str(seats),
                            "note": note.strip(),
                            "google_link": gmap.strip(),
                            "indoor": indoor,
                            "lat": float(lat),
                            "lon": float(lon),
                            "perf_date": str(perf_date_input) if perf_date_input else None,
                            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                        }
                        data = load_json(CITY_FILE)
                        data.append(new_city)
                        save_json(CITY_FILE, data)
                        st.success(f"{selected_city} 등록 완료!")
                        st.rerun()

    # --- 도시 없음 처리 ---
    if not cities:
        st.warning("아직 등록된 도시가 없습니다.")
        if not st.session_state.admin:
            st.info("관리자 로그인 후 도시를 추가해주세요!")
        m = folium.Map(location=[PUNE_LAT, PUNE_LON], zoom_start=9, tiles="CartoDB positron")
        folium.Marker([PUNE_LAT, PUNE_LON], popup="<b>칸타타 투어 2025</b><br>시작을 기다립니다!", 
                      tooltip="Pune", icon=folium.Icon(color="green", icon="star", prefix="fa")).add_to(m)
        st_folium(m, width=900, height=550, key="empty_map")
        return

    # --- 도시 있음: 목록 + 거리 + 지도 ---
    total_dist = 0
    coords = []
    m = folium.Map(location=[PUNE_LAT, PUNE_LON], zoom_start=9, tiles="CartoDB positron")

    for i, c in enumerate(cities):
        try:
            perf_date_obj = datetime.strptime(c['perf_date'], "%Y-%m-%d").date() if c['perf_date'] != "9999-12-31" else None
        except:
            perf_date_obj = None

        # --- 마커 상태 결정 (구글 스타일) ---
        if perf_date_obj and perf_date_obj < today:
            # 과거: 흐리게
            opacity = 0.4
            color = "gray"
            icon = "circle"
        elif perf_date_obj and perf_date_obj == today:
            # 오늘: 검은 원
            opacity = 1.0
            color = "black"
            icon = "circle"
        else:
            # 미래: 선명
            opacity = 1.0
            color = "red" if c.get("indoor") else "blue"
            icon = "tree-christmas"

        # --- 마커 추가 ---
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=f"<b style='color:#e74c3c'>{c['city']}</b><br>{c.get('perf_date','—')}<br>{c.get('venue','—')}",
            tooltip=c["city"],
            icon=folium.Icon(color=color, icon=icon, prefix="fa", icon_color="white")
        ).add_to(m)

        # --- 목록 ---
        with st.expander(f"{c['city']} | {c.get('perf_date', '미정')}"):
            st.write(f"등록일: {c.get('date', '—')}")
            st.write(f"공연 날짜: {c.get('perf_date', '—')}")
            st.write(f"장소: {c.get('venue', '—')}")
            st.write(f"예상 인원: {c.get('seats', '—')}")
            st.write(f"특이사항: {c.get('note', '—')}")
            if c.get("google_link"):
                st.markdown(f"[구글맵 보기]({c['google_link']})")

            if st.session_state.admin:
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

        # --- 거리 계산 ---
        if i < len(cities)-1:
            try:
                d = haversine(c['lat'], c['lon'], cities[i+1]['lat'], cities[i+1]['lon'])
                total_dist += d
                st.markdown(f"<div style='text-align:center;color:#2ecc71;font-weight:bold'>→ {d:.0f}km</div>", unsafe_allow_html=True)
            except:
                st.markdown("<div style='text-align:center;color:#e74c3c'>거리 계산 불가</div>", unsafe_allow_html=True)
        coords.append((c['lat'], c['lon']))

    # --- 경로선 ---
    if len(coords) > 1:
        AntPath(coords, color="#e74c3c", weight=6, opacity=0.9, delay=800).add_to(m)

    # --- 총 거리 ---
    if len(cities) > 1:
        st.markdown(f"<div style='text-align:center;color:#e74c3c;font-size:1.3em;margin:15px 0'>총 거리: {total_dist:.0f}km</div>", unsafe_allow_html=True)

    # --- 지도 렌더링 (항상 Pune 중심) ---
    st_folium(m, width=900, height=550, key=f"map_{len(cities)}", returned_objects=[])

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
