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

# --- 1. 기본 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh_user")

# --- 2. 파일 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 3. 다국어 ---
LANG = {
    "ko": {"tab_notice": "공지", "tab_map": "투어 경로", "today": "오늘", "yesterday": "어제",
           "new_notice_alert": "새 공지가 도착했어요!", "warning": "제목·내용 입력", "edit": "수정", "save": "저장"},
    "en": {"tab_notice": "Notice", "tab_map": "Tour Route", "today": "Today", "yesterday": "Yesterday",
           "new_notice_alert": "New notice!", "warning": "Enter title & content", "edit": "Edit", "save": "Save"},
    "hi": {"tab_notice": "सूचना", "tab_map": "टूर मार्ग", "today": "आज", "yesterday": "कल",
           "new_notice_alert": "नई सूचना!", "warning": "शीर्षक·सामग्री दर्ज करें", "edit": "संपादन", "save": "सहेजें"}
}

defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "editing_city": False,
    "tab_selection": "공지", "new_notice": False, "sound_played": False,
    "seen_notices": [], "expanded_notices": [], "expanded_cities": [],
    "last_tab": None, "alert_active": False, "current_alert_id": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 4. 크리스마스 캐롤 사운드 ---
def play_carol():
    if os.path.exists("carol.wav") and not st.session_state.sound_played:
        st.session_state.sound_played = True
        st.audio("carol.wav", autoplay=True)

# 페이지 로드 시 사운드 재생 (한 번만)
play_carol()

# --- 5. 알림 CSS + JS ---
st.markdown("""
<style>
    .alert-box {
        position: fixed; top: 20px; right: 20px; z-index: 9999;
        background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 16px 20px;
        border-radius: 12px; box-shadow: 0 8px 20px rgba(231, 76, 60, 0.4);
        font-weight: bold; font-size: 16px; display: flex; align-items: center; gap: 12px;
        animation: slideIn 0.6s ease-out, pulse 1.5s infinite;
    }
    @keyframes slideIn { from { transform: translateX(120%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
    .alert-close { cursor: pointer; font-size: 24px; font-weight: bold; }
    .city-form { background: #f8f9fa; padding: 20px; border-radius: 12px; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# --- 6. 사이드바 ---
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
            if pw == "0009":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃", key="logout"):
            st.session_state.admin = False
            st.rerun()

# --- 7. JSON 헬퍼 ---
def load_json(f):
    return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []

def save_json(f, d):
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 8. 초기 도시 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도",
     "google_link": "https://goo.gl/maps/abc123", "indoor": False, "lat": 19.0760, "lon": 72.8777,
     "perf_date": None, "date": "11/07 02:01"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브",
     "google_link": "https://goo.gl/maps/def456", "indoor": True, "lat": 18.5204, "lon": 73.8567,
     "perf_date": None, "date": "11/07 02:01"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시",
     "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "lat": 21.1458, "lon": 79.0882,
     "perf_date": None, "date": "11/07 02:01"}
]
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

# --- 9. 거리 계산 ---
def get_real_travel_time(lat1, lon1, lat2, lon2):
    try:
        key = st.secrets.get("GOOGLE_API_KEY", "")
        if key:
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            p = {"origins": f"{lat1},{lon1}", "destinations": f"{lat2},{lon2}",
                 "key": key, "mode": "driving"}
            r = requests.get(url, params=p, timeout=5).json()
            if r["rows"][0]["elements"][0]["status"] == "OK":
                d = r["rows"][0]["elements"][0]["distance"]["value"] / 1000
                m = r["rows"][0]["elements"][0]["duration"]["value"] // 60
                return d, m
    except Exception as e:
        st.warning(f"거리 API 오류: {e}")
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    return R * 2 * asin(sqrt(a)), int(R * 2 * asin(sqrt(a)) / 80 * 60)

# --- 10. 공지 기능 ---
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
    if not st.session_state.admin:
        st.session_state.seen_notices = []
        st.session_state.new_notice = True
        st.session_state.alert_active = True
        st.session_state.current_alert_id = notice["id"]
        st.session_state.sound_played = False  # 새 공지 → 사운드 재생
        play_carol()
        st.rerun()

def format_notice_date(d):
    try:
        dt = datetime.strptime(d, "%m/%d %H:%M")
        today = date.today()
        if dt.date() == today:
            return _(f"today")
        elif dt.date() == today - timedelta(days=1):
            return _(f"yesterday")
        return d
    except:
        return d

def render_notices():
    data = load_json(NOTICE_FILE)
    for i, n in enumerate(data):
        badge = ' NEW' if (not st.session_state.admin and n["id"] not in st.session_state.seen_notices) else ''
        title = f"{format_notice_date(n['date'])} | {n['title']}{badge}"
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

            if not st.session_state.admin and n["id"] not in st.session_state.seen_notices:
                st.session_state.seen_notices.append(n["id"])

            if expanded and exp_key not in st.session_state.expanded_notices:
                st.session_state.expanded_notices.append(exp_key)
            elif not expanded and exp_key in st.session_state.expanded_notices:
                st.session_state.expanded_notices.remove(exp_key)

            if (not st.session_state.admin and expanded and
                n["id"] == st.session_state.current_alert_id):
                st.session_state.alert_active = False
                st.rerun()

    if not st.session_state.admin and st.session_state.alert_active and st.session_state.current_alert_id:
        st.markdown(f"""
        <div class="alert-box" id="alert">
            <span>{_("new_notice_alert")}</span>
            <span class="alert-close" onclick="document.getElementById('alert').remove()">×</span>
        </div>
        """, unsafe_allow_html=True)

# --- 11. 지도 + 도시 수정 폼 ---
def render_map():
    st.subheader("경로 보기")
    today = date.today()
    raw_cities = load_json(CITY_FILE)
    cities = sorted([
        c | {"perf_date": c.get("perf_date") if c.get("perf_date") not in [None, "9999-12-31"] else "9999-12-31"}
        for c in raw_cities
    ], key=lambda x: x["perf_date"] if x["perf_date"] != "9999-12-31" else "9999-12-31")

    # --- 도시 수정 폼 ---
    if st.session_state.admin and st.session_state.edit_city:
        city_to_edit = next((c for c in raw_cities if c["city"] == st.session_state.edit_city), None)
        if city_to_edit:
            st.markdown("### 도시 정보 수정")
            with st.form("edit_city_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    city = st.text_input("도시명", value=city_to_edit["city"])
                    venue = st.text_input("장소", value=city_to_edit["venue"])
                    seats = st.text_input("예상 인원", value=city_to_edit["seats"])
                    indoor = st.checkbox("실내", value=city_to_edit.get("indoor", False))
                with col2:
                    note = st.text_area("특이사항", value=city_to_edit.get("note", ""))
                    google_link = st.text_input("구글맵 링크", value=city_to_edit.get("google_link", ""))
                    perf_date = st.date_input("공연 날짜", value=(
                        datetime.strptime(city_to_edit["perf_date"], "%Y-%m-%d").date()
                        if city_to_edit["perf_date"] and city_to_edit["perf_date"] != "9999-12-31"
                        else None
                    ))

                lat = st.number_input("위도", value=city_to_edit["lat"], format="%.6f")
                lon = st.number_input("경도", value=city_to_edit["lon"], format="%.6f")

                if st.form_submit_button("저장"):
                    updated = {
                        "city": city, "venue": venue, "seats": seats, "note": note,
                        "google_link": google_link, "indoor": indoor,
                        "lat": lat, "lon": lon,
                        "perf_date": perf_date.strftime("%Y-%m-%d") if perf_date else None,
                        "date": city_to_edit["date"]
                    }
                    raw_cities = [updated if c["city"] == st.session_state.edit_city else c for c in raw_cities]
                    save_json(CITY_FILE, raw_cities)
                    st.session_state.edit_city = None
                    st.success("수정 완료!")
                    st.rerun()

            if st.button("취소"):
                st.session_state.edit_city = None
                st.rerun()

    # --- 지도 렌더링 ---
    m = folium.Map(location=[18.5204, 73.8567], zoom_start=9, tiles="CartoDB positron")

    for i, c in enumerate(cities):
        is_past = (c.get('perf_date') and c['perf_date'] != "9999-12-31" and
                   datetime.strptime(c['perf_date'], "%Y-%m-%d").date() < today)
        opacity = 0.3 if is_past else 1.0

        popup_html = f"<b>{c['city']}</b><br>{c.get('perf_date','미정')}<br>{c.get('venue','—')}"
        folium.Marker(
            [c["lat"], c["lon"]], popup=folium.Popup(popup_html, max_width=280),
            tooltip=c["city"], icon=folium.Icon(color="red" if not is_past else "gray", icon="music", prefix="fa")
        ).add_to(m)

        if i < len(cities) - 1:
            nxt = cities[i + 1]
            dist, mins = get_real_travel_time(c['lat'], c['lon'], nxt['lat'], nxt['lon'])
            label = f"{dist:.0f}km → {mins//60}h {mins%60}m"
            mid_lat = (c['lat'] + nxt['lat']) / 2
            mid_lon = (c['lon'] + nxt['lon']) / 2
            bearing = degrees(atan2(nxt['lon'] - c['lon'], nxt['lat'] - c['lat']))
            bearing = (bearing + 360) % 360
            if 90 < bearing < 270:
                bearing = (bearing + 180) % 360

            path_op = 0.3 if is_past else 1.0
            folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=f"""
                <div style="font-size:10pt; background:white; padding:2px 6px; border-radius:4px; border:1px solid #ccc;">
                    {label}
                </div>
            """)).add_to(m)

            AntPath([(c['lat'], c['lon']), (nxt['lat'], nxt['lon'])],
                    color="#e74c3c", weight=6, opacity=path_op, delay=800, dash_array=[20, 30]).add_to(m)

        # 도시 정보 + 수정/삭제
        exp_key = f"city_{c['city']}"
        expanded = exp_key in st.session_state.expanded_cities
        with st.expander(f"{c['city']} | {c.get('perf_date','미정')}", expanded=expanded):
            for k, v in {"등록일": "date", "공연 날짜": "perf_date", "장소": "venue",
                         "예상 인원": "seats", "특이사항": "note"}.items():
                st.write(f"**{k}**: {c.get(v, '—')}")
            if c.get("google_link"):
                st.markdown(f"[구글맵 보기]({c['google_link']})")

            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(_(f"edit"), key=f"edit_{c['city']}_{i}"):
                        st.session_state.edit_city = c["city"]
                        st.rerun()
                with c2:
                    if st.button("삭제", key=f"del_{c['city']}_{i}"):
                        raw_cities = [x for x in raw_cities if x["city"] != c["city"]]
                        save_json(CITY_FILE, raw_cities)
                        st.rerun()

            if expanded and exp_key not in st.session_state.expanded_cities:
                st.session_state.expanded_cities.append(exp_key)
            elif not expanded and exp_key in st.session_state.expanded_cities:
                st.session_state.expanded_cities.remove(exp_key)

    st_folium(m, width=900, height=550, key="tour_map")

# --- 12. 탭 ---
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

# --- 13. 렌더링 ---
st.markdown('# 칸타타 투어 2025 마하라스트라', unsafe_allow_html=True)

if tab_selection == _(f"tab_notice"):
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            title = st.text_input("제목")
            content = st.text_area("내용")
            img = st.file_uploader("이미지", type=["png", "jpg", "jpeg"])
            file = st.file_uploader("첨부 파일", type=["pdf", "txt", "docx"])
            if st.form_submit_button("등록"):
                if title.strip() and content.strip():
                    add_notice(title, content, img, file)
                else:
                    st.warning(_("warning"))
    render_notices()
else:
    render_map()
