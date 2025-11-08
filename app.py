import json, os, uuid, base64, random
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

LANG = {
    "ko": {"title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
           "tab_notice": "공지", "tab_map": "투어 경로", "indoor": "실내", "outdoor": "실외",
           "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵", "perf_date": "공연 날짜",
           "warning": "제목·내용 입력", "delete": "제거", "menu": "메뉴", "login": "로그인", "logout": "로그아웃",
           "add_city": "공연 추가", "city": "도시", "city_search": "도시 검색"},
    # ... (en, hi 동일)
}

defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 전체 도시 & 좌표 ---
CITY_COORDS = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
    "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Amravati": (20.93, 77.75),
    "Nanded": (19.16, 77.31), "Kolhapur": (16.70, 74.24), "Akola": (20.70, 77.00), "Latur": (18.40, 76.18),
    "Ahmadnagar": (19.10, 74.75), "Jalgaon": (21.00, 75.57), "Dhule": (20.90, 74.77), "Ichalkaranji": (16.69, 74.47),
    "Malegaon": (20.55, 74.53), "Bhusawal": (21.05, 76.00), "Bhiwandi": (19.30, 73.06), "Bhandara": (21.17, 79.65),
    "Beed": (18.99, 75.76), "Buldana": (20.54, 76.18), "Chandrapur": (19.95, 79.30), "Dharashiv": (18.40, 76.57),
    "Gondia": (21.46, 80.19), "Hingoli": (19.72, 77.15), "Jalna": (19.85, 75.89), "Mira-Bhayandar": (19.28, 72.87),
    "Nandurbar": (21.37, 74.22), "Osmanabad": (18.18, 76.07), "Palghar": (19.70, 72.77), "Parbhani": (19.27, 76.77),
    "Ratnagiri": (16.99, 73.31), "Sangli": (16.85, 74.57), "Satara": (17.68, 74.02), "Sindhudurg": (16.24, 73.42),
    "Wardha": (20.75, 78.60), "Washim": (20.11, 77.13), "Yavatmal": (20.39, 78.12), "Kalyan-Dombivli": (19.24, 73.13),
    "Ulhasnagar": (19.22, 73.16), "Vasai-Virar": (19.37, 72.81), "Sangli-Miraj-Kupwad": (16.85, 74.57), "Nanded-Waghala": (19.16, 77.31),
    "Bandra (Mumbai)": (19.06, 72.84), "Colaba (Mumbai)": (18.92, 72.82), "Andheri (Mumbai)": (19.12, 72.84),
    "Navi Mumbai": (19.03, 73.00), "Pimpri-Chinchwad (Pune)": (18.62, 73.80), "Kothrud (Pune)": (18.50, 73.81), "Hadapsar (Pune)": (18.51, 73.94),
    "Pune Cantonment": (18.50, 73.89), "Nashik Road": (20.00, 73.79), "Deolali (Nashik)": (19.94, 73.82), "Satpur (Nashik)": (20.01, 73.79),
    "Aurangabad City": (19.88, 75.34), "Jalgaon City": (21.00, 75.57), "Nagpur City": (21.15, 79.08), "Sitabuldi (Nagpur)": (21.14, 79.08),
    "Jaripatka (Nagpur)": (21.12, 79.07), "Solapur City": (17.67, 75.91), "Pandharpur (Solapur)": (17.66, 75.32), "Amravati City": (20.93, 77.75),
    "Badnera (Amravati)": (20.84, 77.73), "Akola City": (20.70, 77.00), "Washim City": (20.11, 77.13), "Yavatmal City": (20.39, 78.12),
    "Wardha City": (20.75, 78.60), "Chandrapur City": (19.95, 79.30), "Gadchiroli": (20.09, 80.11), "Gondia City": (21.46, 80.19),
    "Bhandara City": (21.17, 79.65), "Gadhinglaj (Kolhapur)": (16.22, 74.35), "Kagal (Kolhapur)": (16.58, 74.31)
}

# --- 기본 공연 목록 (상세 + 나머지 빈 공연) ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도", "google_link": "https://goo.gl/maps/abc123", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-10", "lat": 19.07, "lon": 72.88},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브", "google_link": "https://goo.gl/maps/def456", "indoor": True, "date": "11/07 02:01", "perf_date": "2025-11-12", "lat": 18.52, "lon": 73.86},
    {"city": "Pune", "venue": "Aga Khan Palace", "seats": "2500", "note": "역사적 장소", "google_link": "https://goo.gl/maps/pune2", "indoor": False, "date": "11/08 14:00", "perf_date": "2025-11-14", "lat": 18.52, "lon": 73.86},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시", "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-16", "lat": 21.15, "lon": 79.08}
]

existing_cities = {c["city"] for c in DEFAULT_CITIES}
for city in sorted(CITY_COORDS.keys()):
    if city not in existing_cities:
        lat, lon = CITY_COORDS[city]
        DEFAULT_CITIES.append({
            "city": city, "venue": "", "seats": "", "note": "", "google_link": "",
            "indoor": False, "date": "", "perf_date": "", "lat": lat, "lon": lon
        })

if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

# --- (CSS, 눈송이, 헤더, 버튼 등 생략, 이전과 동일) ---

if st.session_state.map_open:
    cities = load_json(CITY_FILE)
    city_names = sorted({c['city'] for c in cities})

    if st.session_state.admin:
        st.header(_("add_city"))
        with st.form("city_form", clear_on_submit=True):
            search_term = st.text_input(_("city_search"), "")
            filtered_cities = [c for c in city_names if search_term.lower() in c.lower()] if search_term else city_names
            selected_city = st.selectbox(_("city"), options=[""] + sorted(filtered_cities))

            perf_date = st.date_input(_("perf_date"), value=None)
            venue = st.text_input(_("venue"))
            note = st.text_input(_("note"))
            google_link = st.text_input(_("google_link"))

            col_indoor, col_seats = st.columns([1, 2])
            with col_indoor:
                indoor = st.radio("장소 유형", [_("indoor"), _("outdoor")], horizontal=True) == _("indoor")
            with col_seats:
                seats = st.number_input(_("seats"), min_value=0, value=500, step=50)

            if st.form_submit_button("추가"):
                if selected_city and venue:
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
                    st.success("공연 추가 완료!")
                    st.rerun()
                else:
                    st.warning("도시와 공연 장소를 입력하세요.")

    # --- 지도 및 목록 (이전과 동일, lat/lon fallback 포함) ---
    m = folium.Map(location=[18.52, 73.86], zoom_start=7, tiles="OpenStreetMap")
    for i, c in enumerate(cities):
        lat = c.get("lat") or CITY_COORDS.get(c["city"], (18.52, 73.86))[0]
        lon = c.get("lon") or CITY_COORDS.get(c["city"], (18.52, 73.86))[1]
        coords = (lat, lon)
        # ... (마커, AntPath 동일) ...
    st_folium(m, width=900, height=550, key="tour_map")

    if st.session_state.admin:
        st.subheader("공연 목록 관리")
        for i, c in enumerate(cities):
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(f"{c['city']} - {c['venue'] or '—'} ({c.get('perf_date', '미정')})")
            with cols[1]:
                if st.button(_("delete"), key=f"del_{i}"):
                    cities.pop(i)
                    save_json(CITY_FILE, cities)
                    st.rerun()

# --- (나머지 공지, 사이드바 등 동일) ---
