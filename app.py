import json, os, uuid, base64, random
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
import pandas as pd

st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
CSV_FILE = "마하라스트라 도시목록.csv"
os.makedirs(UPLOAD_DIR, exist_ok=True)

LANG = {
    "ko": {"title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
           "tab_notice": "공지", "tab_map": "투어 경로", "indoor": "실내", "outdoor": "실외",
           "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵", "perf_date": "공연 날짜",
           "warning": "제목·내용 입력", "delete": "제거", "menu": "메뉴", "login": "로그인", "logout": "로그아웃",
           "add_city": "도시 추가", "city": "도시", "import_cities": "CSV 도시 일괄 추가", "import_success": "도시 일괄 추가 완료!"},
    "en": {"title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
           "tab_notice": "Notice", "tab_map": "Tour Route", "indoor": "Indoor", "outdoor": "Outdoor",
           "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps", "perf_date": "Performance Date",
           "warning": "Enter title & content", "delete": "Remove", "menu": "Menu", "login": "Login", "logout": "Logout",
           "add_city": "Add City", "city": "City", "import_cities": "Import All Cities from CSV", "import_success": "Cities imported successfully!"},
    "hi": {"title_cantata": "कैंटाटा टूर", "title_year": "2025", "title_region": "महाराष्ट्र",
           "tab_notice": "सूचना", "tab_map": "टूर मार्ग", "indoor": "इनडोर", "outdoor": "आउटडोर",
           "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप", "perf_date": "प्रदर्शन तिथि",
           "warning": "शीर्षक·सामग्री दर्ज करें", "delete": "हटाएं", "menu": "मेनू", "login": "लॉगिन", "logout": "लॉगआउट",
           "add_city": "शहर जोड़ें", "city": "शहर", "import_cities": "CSV से सभी शहर आयात करें", "import_success": "शहर सफलतापूर्वक आयात किए गए!"}
}

defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 도시 좌표 ---
CITY_COORDS = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08),
    "Nashik": (20.00, 73.79), "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34),
    "Solapur": (17.67, 75.91), "Kolhapur": (16.70, 74.24), "Amravati": (20.93, 77.75)
}

# --- 기본 도시 목록 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도", "google_link": "https://goo.gl/maps/abc123", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-10", "lat": CITY_COORDS["Mumbai"][0], "lon": CITY_COORDS["Mumbai"][1]},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브", "google_link": "https://goo.gl/maps/def456", "indoor": True, "date": "11/07 02:01", "perf_date": "2025-11-12", "lat": CITY_COORDS["Pune"][0], "lon": CITY_COORDS["Pune"][1]},
]

if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

# --- CSV 도시 일괄 추가 ---
def import_cities_from_csv():
    if not os.path.exists(CSV_FILE): return st.error(f"{CSV_FILE} 파일이 없습니다.")
    df = pd.read_csv(CSV_FILE)
    new_cities = df.dropna(subset=['city'])['city'].astype(str).str.strip().unique().tolist()
    current_cities = load_json(CITY_FILE)
    current_names = {c['city'] for c in current_cities}
    added = 0
    for city_name in new_cities:
        if city_name not in current_names:
            lat, lon = CITY_COORDS.get(city_name, (18.52, 73.86))
            current_cities.append({
                "city": city_name, "venue": "", "seats": "", "note": "", "google_link": "",
                "indoor": False, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
                "perf_date": "", "lat": lat, "lon": lon
            })
            current_names.add(city_name)
            added += 1
    save_json(CITY_FILE, current_cities)
    st.success(f"{added}개 도시가 추가되었습니다!")

# --- 헤더 및 스타일 ---
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
    [data-testid="stAppViewContainer"] { background: url("background_christmas_dark.png"); background-size: cover; background-position: center; background-attachment: fixed; padding-top: 0 !important; margin: 0 !important; }
    .main-title { font-size: 2.8em; font-weight: bold; text-align: center; color:white; text-shadow: 0 3px 8px rgba(0,0,0,0.6); }
</style>
""", unsafe_allow_html=True)

st.markdown(f"<h1 class='main-title'>{_('title_cantata')} {_('title_year')} {_('title_region')}</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button(_("tab_notice"), key="btn_notice", use_container_width=True):
        st.session_state.notice_open = not st.session_state.notice_open
        st.session_state.map_open = False
        st.rerun()
with col2:
    if st.button(_("tab_map"), key="btn_map", use_container_width=True):
        st.session_state.map_open = not st.session_state.map_open
        st.session_state.notice_open = False
        st.rerun()

# --- 공지 ---
if st.session_state.notice_open:
    if st.session_state.admin:
        with st.expander("공지 작성"):
            with st.form("notice_form", clear_on_submit=True):
                title = st.text_input("제목")
                content = st.text_area("내용")
                if st.form_submit_button("등록"):
                    if title.strip() and content.strip():
                        notice = {"id": str(uuid.uuid4()), "title": title, "content": content,
                                  "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")}
                        data = load_json(NOTICE_FILE)
                        data.insert(0, notice)
                        save_json(NOTICE_FILE, data)
                        st.success("공지 등록 완료!")
                        st.rerun()
                    else:
                        st.warning(_("warning"))
    data = load_json(NOTICE_FILE)
    for i, n in enumerate(data):
        with st.expander(f"{n['date']} | {n['title']}", expanded=False):
            st.markdown(n["content"])
            if st.session_state.admin and st.button(_("delete"), key=f"del_n_{n['id']}"):
                data.pop(i); save_json(NOTICE_FILE, data); st.rerun()

# --- 지도 및 도시 관리 ---
if st.session_state.map_open:
    if st.session_state.admin and os.path.exists(CSV_FILE):
        if st.button(_("import_cities"), key="import_csv_cities"):
            import_cities_from_csv()
            st.rerun()

    cities = load_json(CITY_FILE)
    city_names = sorted({c['city'] for c in cities})

    if st.session_state.admin:
        st.header(_("add_city"))
        with st.form("city_form", clear_on_submit=True):
            # 기본값을 '공연 없음'으로 설정
            selected_city = st.selectbox(
                _("city"),
                options=["공연 없음"] + city_names,
                index=0,
                key="selected_city"
            )
            perf_date = st.date_input(_("perf_date"), value=None)
            venue = st.text_input(_("venue"))
            note = st.text_input(_("note"))
            google_link = st.text_input(_("google_link"))
            col_indoor, col_seats = st.columns([1, 2])
            with col_indoor:
                indoor_option = st.radio("장소 유형", [(_("indoor"), True), (_("outdoor"), False)],
                                         format_func=lambda x: x[0], horizontal=True)
                indoor = indoor_option[1]
            with col_seats:
                seats = st.number_input(_("seats"), min_value=0, max_value=10000, value=500, step=50, format="%d")

            if st.form_submit_button("추가"):
                if selected_city != "공연 없음" and venue:
                    lat, lon = CITY_COORDS.get(selected_city, (18.52, 73.86))
                    new_city = {
                        "city": selected_city, "venue": venue, "seats": str(seats), "note": note,
                        "google_link": google_link, "indoor": indoor,
                        "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
                        "perf_date": str(perf_date) if perf_date else "",
                        "lat": lat, "lon": lon
                    }
                    cities.append(new_city)
                    save_json(CITY_FILE, cities)
                    st.success("도시 추가 완료!")
                    st.session_state["selected_city"] = "공연 없음"
                    st.rerun()
                else:
                    st.warning("도시와 공연 장소를 입력하세요.")

    # 지도 표시
    m = folium.Map(location=[18.52, 73.86], zoom_start=7, tiles="OpenStreetMap")
    for i, c in enumerate(cities):
        lat, lon = c.get("lat", 18.52), c.get("lon", 73.86)
        popup_html = f"<div><b>{c['city']}</b><br>{_('venue')}: {c.get('venue','—')}<br>{_('perf_date')}: {c.get('perf_date','미정')}</div>"
        folium.Marker([lat, lon], popup=popup_html,
                      icon=folium.Icon(color="red", icon="music", prefix="fa")).add_to(m)
    st_folium(m, width=900, height=550, key="tour_map")

    if st.session_state.admin:
        st.subheader("도시 목록 관리")
        for i, c in enumerate(cities):
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(f"{c['city']} - {c['venue']} ({c.get('perf_date', '미정')})")
            with cols[1]:
                if st.button(_("delete"), key=f"del_c_{i}"):
                    cities.pop(i)
                    save_json(CITY_FILE, cities)
                    st.rerun()

# --- 사이드바 ---
with st.sidebar:
    lang_map = {"한국어": "ko", "English": "en", "हिंदी": "hi"}
    sel = st.selectbox("언어", list(lang_map.keys()), index=list(lang_map.values()).index(st.session_state.lang))
    if lang_map[sel] != st.session_state.lang:
        st.session_state.lang = lang_map[sel]
        st.rerun()
    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password", key="pw_input")
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
