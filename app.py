import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from math import radians, sin, cos, sqrt, atan2

# =============================================
# 언어팩
# =============================================
LANG = {
    "ko": {"title": "칸타타 투어", "subtitle": "마하라스트라", "select_city": "도시 선택", "add_city": "추가",
           "register": "등록", "venue": "공연장", "seats": "좌석 수", "indoor": "실내", "outdoor": "실외",
           "google": "구글 지도 링크", "notes": "특이사항", "tour_map": "투어 지도", "tour_route": "경로",
           "password": "관리자 비밀번호", "login": "로그인", "logout": "로그아웃", "date": "공연 날짜",
           "total": "총 거리 및 소요시간", "already_added": "이미 추가된 도시입니다."},
    "en": {"title": "Cantata Tour", "subtitle": "Maharashtra", "select_city": "Select City", "add_city": "Add",
           "register": "Register", "venue": "Venue", "seats": "Seats", "indoor": "Indoor", "outdoor": "Outdoor",
           "google": "Google Maps Link", "notes": "Notes", "tour_map": "Tour Map", "tour_route": "Route",
           "password": "Admin Password", "login": "Log in", "logout": "Log out", "date": "Date",
           "total": "Total Distance & Time", "already_added": "City already added."},
    "hi": {"title": "कांटाटा टूर", "subtitle": "महाराष्ट्र", "select_city": "शहर चुनें", "add_city": "जोड़ें",
           "register": "पंजीकरण करें", "venue": "स्थान", "seats": "सीटें", "indoor": "इनडोर", "outdoor": "आउटडोर",
           "google": "गूगल मानचित्र लिंक", "notes": "टिप्पणी", "tour_map": "टूर मानचित्र", "tour_route": "मार्ग",
           "password": "व्यवस्थापक पासवर्ड", "login": "लॉगिन", "logout": "लॉगआउट", "date": "दिनांक",
           "total": "कुल दूरी और समय", "already_added": "यह शहर पहले से जोड़ा गया है।"}
}

# =============================================
# 실제 도시 목록 (정렬됨)
# =============================================
cities = sorted([
    "Mumbai","Pune","Nagpur","Nashik","Thane","Aurangabad","Solapur","Amravati","Nanded","Kolhapur",
    "Akola","Latur","Ahmadnagar","Jalgaon","Dhule","Malegaon","Bhusawal","Bhiwandi","Bhandara","Beed",
    "Ratnagiri","Wardha","Sangli","Satara","Yavatmal","Parbhani","Osmanabad","Palghar","Chandrapur","Raigad"
])

coords = {
    "Mumbai":(19.07,72.88),"Pune":(18.52,73.86),"Nagpur":(21.15,79.08),"Nashik":(20.00,73.79),"Thane":(19.22,72.98),
    "Aurangabad":(19.88,75.34),"Solapur":(17.67,75.91),"Amravati":(20.93,77.75),"Nanded":(19.16,77.31),"Kolhapur":(16.70,74.24),
    "Akola":(20.70,77.00),"Latur":(18.40,76.18),"Ahmadnagar":(19.10,74.75),"Jalgaon":(21.00,75.57),"Dhule":(20.90,74.77),
    "Malegaon":(20.55,74.53),"Bhusawal":(21.05,76.00),"Bhiwandi":(19.30,73.06),"Bhandara":(21.17,79.65),"Beed":(18.99,75.76),
    "Ratnagiri":(16.99,73.31),"Wardha":(20.74,78.60),"Sangli":(16.86,74.57),"Satara":(17.68,74.00),"Yavatmal":(20.39,78.13),
    "Parbhani":(19.26,76.77),"Osmanabad":(18.17,76.04),"Palghar":(19.70,72.77),"Chandrapur":(19.95,79.29),"Raigad":(18.51,73.19)
}

# =============================================
# 거리 계산
# =============================================
def distance_km(p1, p2):
    R = 6371
    lat1, lon1 = radians(p1[0]), radians(p1[1])
    lat2, lon2 = radians(p2[0]), radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# =============================================
# Streamlit state
# =============================================
st.set_page_config(page_title="Cantata Tour", layout="wide")

if "lang" not in st.session_state: st.session_state.lang = "ko"
if "admin" not in st.session_state: st.session_state.admin = False
if "route" not in st.session_state: st.session_state.route = []
if "venue_data" not in st.session_state: st.session_state.venue_data = {}

# =============================================
# Sidebar
# =============================================
with st.sidebar:
    lang_selected = st.selectbox("Language", ["ko","en","hi"], index=["ko","en","hi"].index(st.session_state.lang))
    st.session_state.lang = lang_selected
    _ = LANG[st.session_state.lang]

    st.markdown("---")
    st.write("**Admin**")

    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0691":
                st.session_state.admin = True
                st.success("관리자 모드 활성화")
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.rerun()

# =============================================
# Theme
# =============================================
st.markdown("""
<style>
.stApp {
  background: radial-gradient(circle at 20% 20%, #0a0a0f 0%, #000000 100%);
  color: #ffffff;
  font-family: 'Noto Sans KR', sans-serif;
}

/* 제목: 칸타타 투어 빨간색 + 마하라스트라 작은 글씨 */
h1 {
  color: #ff3333 !important;
  text-align: center;
  font-weight: 900;
  font-size: 4.3em;
  text-shadow: 0 0 25px #b71c1c, 0 0 15px #00ff99;
  margin-bottom: 0;
}
h1 span.year {color: #ffffff; font-weight: 800; font-size: 0.8em; vertical-align: super;}
h1 span.subtitle {color: #cccccc; font-size: 0.45em; vertical-align: super; margin-left: 5px;}
h2 {text-align: center; color: #cccccc; margin-top: 0;}

/* 버튼 */
div[data-testid="stButton"] > button {
  background: linear-gradient(90deg, #ff3b3b, #228B22);
  border: none;
  color: white;
  font-weight: 700;
  border-radius: 8px;
  transition: 0.3s;
}
div[data-testid="stButton"] > button:hover {
  transform: scale(1.05);
  box-shadow: 0 0 15px #ff4d4d;
}
</style>
""", unsafe_allow_html=True)

# =============================================
# Title (마하라스트라 작은 글씨로 2025와 트리 사이)
# =============================================
st.markdown(
    f"<h1>{_['title']} <span class='year'>2025</span><span class='subtitle'>{_['subtitle']}</span> 🎄</h1>",
    unsafe_allow_html=True
)

# =============================================
# Layout
# =============================================
left, right = st.columns([1,2])

# =============================================
# Left panel
# =============================================
with left:
    c1, c2 = st.columns([3,1])
    with c1:
        selected_city = st.selectbox(_["select_city"], cities)
    with c2:
        if st.button(_["add_city"]):
            if selected_city not in st.session_state.route:
                st.session_state.route.append(selected_city)
                st.rerun()
            else:
                st.warning(_["already_added"])

    st.markdown("---")
    st.subheader(f"{_['tour_route']}")

    total_distance = 0.0
    total_hours = 0.0

    # 도시 박스 + 거리/시간 (도시명 없이)
    for i, c in enumerate(st.session_state.route):
        with st.expander(f"{c}"):
            today = datetime.now().date()
            date = st.date_input(_["date"], value=today, min_value=today, key=f"date_{c}")
            venue = st.text_input(_["venue"], key=f"venue_{c}")
            seats = st.number_input(_["seats"], min_value=0, step=50, key=f"seats_{c}")
            google = st.text_input(_["google"], key=f"google_{c}")
            notes = st.text_area(_["notes"], key=f"notes_{c}")
            io = st.radio("Type", [_["indoor"], _["outdoor"]], key=f"io_{c}")

            if st.session_state.admin:
                if st.button(_["register"], key=f"reg_{c}"):
                    st.session_state.venue_data[c] = {
                        "date": str(date), "venue": venue, "seats": seats,
                        "type": io, "google": google, "notes": notes
                    }
                    st.success("저장되었습니다.")
                    st.rerun()

        # 첫 번째와 두 번째 사이에도 거리/시간 표시
        if i > 0:
            prev = st.session_state.route[i - 1]
            if prev in coords and c in coords:
                dist = distance_km(coords[prev], coords[c])
                time_hr = dist / 60.0
                total_distance += dist
                total_hours += time_hr
                st.markdown(
                    f"<p style='text-align:center; color:#90EE90; font-weight:bold; margin:5px 0;'>"
                    f"{dist:.1f} km / {time_hr:.1f} 시간"
                    f"</p>",
                    unsafe_allow_html=True
                )

    if len(st.session_state.route) > 1:
        st.markdown("---")
        st.markdown(f"### {_['total']}")
        st.success(f"총 거리: **{total_distance:.1f} km** | 총 소요시간: **{total_hours:.1f} 시간**")

# =============================================
# Right panel
# =============================================
with right:
    st.subheader(_["tour_map"])
    m = folium.Map(location=(19.75,75.71), zoom_start=6, tiles="CartoDB positron")

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
                popup += f"<a href='{data['google']}' target='_blank'>Google Maps</a>"
            folium.Marker(coords[c], popup=popup,
                          icon=folium.Icon(color="red", icon="music", prefix="fa")).add_to(m)

    st_folium(m, width=900, height=650)
