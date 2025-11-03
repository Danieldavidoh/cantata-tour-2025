import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from math import radians, sin, cos, sqrt, atan2

# --- language ---
LANG = {
    "ko": {"title": "칸타타 투어", "subtitle": "마하라스트라", "select_city": "도시 선택", "add_city": "추가",
           "register": "등록", "venue": "공연장", "seats": "좌석 수", "indoor": "실내", "outdoor": "실외",
           "google": "구글 지도 링크", "notes": "특이사항", "tour_map": "투어 지도", "tour_route": "경로",
           "password": "관리자 비밀번호", "login": "로그인", "logout": "로그아웃", "date": "공연 날짜",
           "total": "총 거리 및 소요시간"},
    "en": {"title": "Cantata Tour", "subtitle": "Maharashtra", "select_city": "Select City", "add_city": "Add",
           "register": "Register", "venue": "Venue", "seats": "Seats", "indoor": "Indoor", "outdoor": "Outdoor",
           "google": "Google Maps Link", "notes": "Notes", "tour_map": "Tour Map", "tour_route": "Route",
           "password": "Admin Password", "login": "Log in", "logout": "Log out", "date": "Date",
           "total": "Total Distance & Time"},
    "hi": {"title": "कांटाटा टूर", "subtitle": "महाराष्ट्र", "select_city": "शहर चुनें", "add_city": "जोड़ें",
           "register": "पंजीकरण करें", "venue": "स्थान", "seats": "सीटें", "indoor": "इनडोर", "outdoor": "आउटडोर",
           "google": "गूगल मानचित्र लिंक", "notes": "टिप्पणी", "tour_map": "टूर मानचित्र", "tour_route": "मार्ग",
           "password": "व्यवस्थापक पासवर्ड", "login": "लॉगिन", "logout": "लॉगआउट", "date": "दिनांक",
           "total": "कुल दूरी और समय"}
}

# --- cities and coordinates ---
cities = sorted([
    "Mumbai", "Pune", "Nagpur", "Nashik", "Thane", "Aurangabad", "Solapur", "Amravati", "Nanded", "Kolhapur",
    "Akola", "Latur", "Ahmadnagar", "Jalgaon", "Dhule", "Malegaon", "Bhusawal", "Bhiwandi", "Bhandara", "Beed"
])

coords = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79), "Thane": (19.22, 72.98),
    "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Amravati": (20.93, 77.75), "Nanded": (19.16, 77.31), "Kolhapur": (16.70, 74.24),
    "Akola": (20.70, 77.00), "Latur": (18.40, 76.18), "Ahmadnagar": (19.10, 74.75), "Jalgaon": (21.00, 75.57), "Dhule": (20.90, 74.77),
    "Malegaon": (20.55, 74.53), "Bhusawal": (21.05, 76.00), "Bhiwandi": (19.30, 73.06), "Bhandara": (21.17, 79.65), "Beed": (18.99, 75.76)
}

# --- utility: haversine distance (km) ---
def distance_km(p1, p2):
    R = 6371
    lat1, lon1 = radians(p1[0]), radians(p1[1])
    lat2, lon2 = radians(p2[0]), radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# --- Streamlit setup ---
st.set_page_config(page_title="Cantata Tour", layout="wide")

# --- state setup ---
if "lang" not in st.session_state:
    st.session_state.lang = "ko"
if "admin" not in st.session_state:
    st.session_state.admin = False
if "route" not in st.session_state:
    st.session_state.route = []
if "venue_data" not in st.session_state:
    st.session_state.venue_data = {}

# --- Sidebar ---
with st.sidebar:
    lang_selected = st.selectbox("Language / 언어 / भाषा", ["ko", "en", "hi"], index=0)
    st.session_state.lang = lang_selected
    _ = LANG[st.session_state.lang]

    st.markdown("---")
    st.write("🎅 **Admin Panel**")

    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0691":
                st.session_state.admin = True
                st.success("✅ 관리자 모드 활성화")
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.success("👋 손님 모드로 전환합니다.")
            st.rerun()

# --- Custom CSS (크리스마스 테마 + 눈 내리는 효과) ---
st.markdown("""
<style>
body {
  background-color: #ffffff;
  color: #003300;
  font-family: 'Noto Sans KR', sans-serif;
  background-image: url('https://i.imgur.com/mC4n1Np.png'); /* subtle snowflake texture */
  background-size: cover;
}

/* 눈 내리는 효과 */
@keyframes snow {
  0% {background-position: 0px 0px;}
  100% {background-position: 0px 1000px;}
}
.stApp {
  background: linear-gradient(rgba(255,255,255,0.95), rgba(255,255,255,0.95)),
              url('https://i.imgur.com/OlbBRqH.png');
  background-repeat: repeat;
  animation: snow 20s linear infinite;
}

/* 제목 */
h1, h2 {
  text-align: center;
  color: #b30000;
  text-shadow: 2px 2px 4px #fff;
}

/* 버튼 */
button {
  background-color: #d32f2f !important;
  color: white !important;
  border-radius: 10px !important;
}

/* Expander */
.streamlit-expanderHeader {
  background-color: #c8e6c9 !important;
  color: #2e7d32 !important;
}

/* 크리스마스 장식 (이모지로 간단히) */
h1::before {
  content: "🎁🎄🔔 ";
}
h1::after {
  content: " 🎅❄️🍬";
}
</style>
""", unsafe_allow_html=True)

# --- Title section ---
_ = LANG[st.session_state.lang]
st.markdown(
    f"<h1>{_['title']}</h1>"
    f"<h2>2025 &nbsp; <span style='font-size:0.8em; color:green;'>{_['subtitle']}</span></h2>",
    unsafe_allow_html=True
)

left, right = st.columns([1, 2])

# --- Left panel ---
with left:
    st.subheader(f"🎁 {_['tour_route']}")

    c1, c2 = st.columns([3, 1])
    with c1:
        selected_city = st.selectbox(_["select_city"], cities)
    with c2:
        if st.button(_["add_city"]):
            st.session_state.route.append(selected_city)
            if selected_city not in st.session_state.venue_data:
                st.session_state.venue_data[selected_city] = {}
            st.rerun()

    st.markdown("---")

    total_distance = 0.0
    total_hours = 0.0

    for i, c in enumerate(st.session_state.route):
        with st.expander(f"🎄 {c}"):
            date = st.date_input(_["date"], value=datetime.now().date(), key=f"date_{c}")
            venue = st.text_input(_["venue"], key=f"venue_{c}")
            seats = st.number_input(_["seats"], min_value=0, step=50, key=f"seats_{c}")
            google = st.text_input(_["google"], key=f"google_{c}")
            notes = st.text_area(_["notes"], key=f"notes_{c}")
            indoor_outdoor = st.radio("Type / 유형", [_["indoor"], _["outdoor"]], key=f"io_{c}")

            if st.session_state.admin:
                if st.button(_["register"], key=f"reg_{c}"):
                    st.session_state.venue_data[c] = {
                        "date": str(date),
                        "venue": venue,
                        "seats": seats,
                        "type": indoor_outdoor,
                        "google": google,
                        "notes": notes
                    }
                    st.success("✅ 저장되었습니다.")
                    st.rerun()
            else:
                st.info("관리자 모드에서만 저장 가능합니다.")

        if i > 0:
            prev = st.session_state.route[i - 1]
            if prev in coords and c in coords:
                dist = distance_km(coords[prev], coords[c])
                time_hr = dist / 60.0
                total_distance += dist
                total_hours += time_hr
                st.markdown(f"➡️ **{prev} → {c}** : 약 {dist:.1f} km / {time_hr:.1f} 시간")

    if len(st.session_state.route) > 1:
        st.markdown("---")
        st.markdown(f"### 🎅 {_['total']}")
        st.success(f"🎁 총 거리: **{total_distance:.1f} km**  🎄 총 소요시간: **{total_hours:.1f} 시간**")

# --- Right panel: MAP ---
with right:
    st.subheader(f"🗺️ {_['tour_map']}")

    m = folium.Map(location=(19.75, 75.71), zoom_start=7, tiles="CartoDB positron")

    points = [coords[c] for c in st.session_state.route if c in coords]
    if len(points) >= 2:
        AntPath(points, color="red", weight=4, delay=800).add_to(m)

    for c in st.session_state.route:
        if c in coords:
            data = st.session_state.venue_data.get(c, {})
            popup = f"<b>{c}</b><br>"
            if "date" in data:
                popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data['type']}<br>"
            if "google" in data and data["google"]:
                popup += f"<a href='{data['google']}' target='_blank'>📍 Google Maps</a>"
            folium.Marker(coords[c], popup=popup,
                          icon=folium.Icon(color="red", icon="gift", prefix="fa")).add_to(m)

    st_folium(m, width=900, height=650)
