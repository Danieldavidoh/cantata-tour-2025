# app.py
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =============================================
# 세션 초기화
# =============================================
defaults = {
    "admin": False,
    "lang": "ko",
    "venue_input": "",
    "seat_count": 0,
    "venue_type": "실내",
    "note_input": "",
    "map_link": "",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =============================================
# 현재시간 (뭄바이 기준)
# =============================================
india_time = datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
st.markdown(f"<p style='text-align:right;color:gray;font-size:0.9rem;'>🕓 {india_time} (Mumbai)</p>", unsafe_allow_html=True)

# =============================================
# 다국어
# =============================================
LANG = {
    "ko": {"title": "칸타타 투어 2025", "tab_notice": "공지", "tab_map": "투어 경로", "add_city": "도시 추가",
           "select_city": "도시 선택", "venue": "공연장소", "seats": "좌석수", "note": "특이사항", "google_link": "구글맵 링크",
           "indoor": "실내", "outdoor": "실외", "register": "등록", "edit": "수정", "delete": "삭제", "city": "도시", "date": "공연일"},
    "en": {"title": "Cantata Tour 2025", "tab_notice": "Notices", "tab_map": "Tour Route", "add_city": "Add City",
           "select_city": "Select City", "venue": "Venue", "seats": "Seats", "note": "Notes", "google_link": "Google Maps Link",
           "indoor": "Indoor", "outdoor": "Outdoor", "register": "Register", "edit": "Edit", "delete": "Delete", "city": "City", "date": "Date"},
    "hi": {"title": "कांताता टूर 2025", "tab_notice": "सूचनाएँ", "tab_map": "टूर मार्ग", "add_city": "शहर जोड़ें",
           "select_city": "शहर चुनें", "venue": "स्थल", "seats": "सीटें", "note": "टिप्पणियाँ", "google_link": "गूगल मैप लिंक",
           "indoor": "इनडोर", "outdoor": "आउटडोर", "register": "पंजीकृत करें", "edit": "संपादित करें", "delete": "हटाएं", "city": "शहर", "date": "दिनांक"},
}
_ = LANG[st.session_state.lang]

# =============================================
# 유틸
# =============================================
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
        final_url = r.url
        match = re.search(r'@([0-9\.\-]+),([0-9\.\-]+)', final_url)
        if match:
            return float(match.group(1)), float(match.group(2))
    except:
        pass
    return None, None

def make_navigation_link(lat, lon):
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

# =============================================
# 지도 + 도시 관리
# =============================================
def render_map():
    st.subheader(_["tab_map"])
    data = load_json(CITY_FILE)

    # === 관리자용 도시 관리 UI ===
    if st.session_state.admin:
        with st.expander("➕ 도시 관리", expanded=False):
            if not os.path.exists(CITY_LIST_FILE):
                default_cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad",
                                  "Kolhapur", "Solapur", "Thane", "Ratnagiri", "Sangli"]
                save_json(CITY_LIST_FILE, default_cities)
            cities_list = load_json(CITY_LIST_FILE)

            city = st.selectbox(_["select_city"], cities_list)
            event_date = st.date_input(_["date"], value=date.today())
            venue = st.text_input(_["venue"])
            seats = st.number_input(_["seats"], min_value=0, step=50)
            vtype = st.radio("공연형태", [_["indoor"], _["outdoor"]], horizontal=True)
            link = st.text_input(_["google_link"])
            note = st.text_area(_["note"])

            if st.button(_["register"]):
                lat, lon = extract_latlon_from_shortlink(link)
                if not lat or not lon:
                    st.warning("⚠️ 구글맵 링크가 올바르지 않습니다.")
                    return
                new_entry = {
                    "city": city,
                    "date": str(event_date),
                    "venue": venue,
                    "seats": seats,
                    "type": vtype,
                    "note": note,
                    "lat": lat,
                    "lon": lon,
                    "nav_url": make_navigation_link(lat, lon)
                }
                data.append(new_entry)
                save_json(CITY_FILE, data)
                st.toast("✅ 도시가 추가되었습니다.")
                st.rerun()

            # 수정 및 삭제
            if data:
                target = st.selectbox("수정/삭제할 도시 선택", [d["city"] for d in data])
                target_data = next((d for d in data if d["city"] == target), None)
                if target_data and st.button(_["delete"], key="del_city"):
                    data.remove(target_data)
                    save_json(CITY_FILE, data)
                    st.toast("🗑️ 도시가 삭제되었습니다.")
                    st.rerun()

    # === 지도 표시 ===
    m = folium.Map(location=[19.0, 73.0], zoom_start=6, tiles="CartoDB positron")
    coords = []

    for c in data:
        if not all(k in c for k in ["city", "lat", "lon"]):
            continue

        popup_html = f"""
        <div style="
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            text-align: center;
            white-space: nowrap;
            padding: 8px 16px;
            min-width: 320px;
            max-width: 420px;
            line-height: 1.5;
        ">
            <b>{c['city']}</b> | {c.get('venue','-')} | {c.get('seats',0)}석 | {c.get('type','')}
        </div>
        """

        folium.Marker(
            [c["lat"], c["lon"]],
            popup=folium.Popup(popup_html, max_width=450),
            tooltip=c["city"],
            icon=folium.Icon(color="red", icon="music", prefix="fa")
        ).add_to(m)
        coords.append((c["lat"], c["lon"]))

    if len(coords) > 1:
        AntPath(coords, color="#ff1744", weight=5, opacity=0.8, delay=800, dash_array=[20, 30]).add_to(m)

    st_folium(m, width=950, height=600, key="map_view")

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    st.markdown("### 언어 선택")
    lang_options = {"한국어": "ko", "English": "en", "हिन्दी": "hi"}
    display_options = list(lang_options.keys())
    current_idx = display_options.index(
        next((k for k, v in lang_options.items() if v == st.session_state.lang), "한국어")
    )
    selected_display = st.selectbox("Language", display_options, index=current_idx)
    new_lang = lang_options[selected_display]
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")
    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if pw == "0000":
                st.session_state.admin = True
                st.success("✅ 관리자 모드 ON")
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
    else:
        st.success("✅ 관리자 모드 활성화 중")
        if st.button("로그아웃"):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 메인
# =============================================
st.title(_["title"])
tab1, tab2 = st.tabs([_["tab_notice"], _["tab_map"]])
with tab2:
    render_map()
