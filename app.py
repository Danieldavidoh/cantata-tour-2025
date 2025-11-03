import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from math import radians, sin, cos, sqrt, atan2
import random  # 눈 효과용

# =============================================
# 언어팩
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어", "subtitle": "마하라스트라", "select_city": "도시 선택", "add_city": "추가",
        "register": "등록", "venue": "공연장", "seats": "좌석 수", "indoor": "실내", "outdoor": "실외",
        "google": "구글 지도 링크", "notes": "특이사항", "tour_map": "투어 지도", "tour_route": "경로",
        "password": "관리자 비밀번호", "login": "로그인", "logout": "로그아웃", "date": "공연 날짜",
        "total": "총 거리 및 총 소요시간", "already_added": "이미 추가된 도시입니다."
    },
    "hi": {
        "title": "कांटाटा टूर", "subtitle": "महाराष्ट्र", "select_city": "शहर चुनें", "add_city": "जोड़ें",
        "register": "पंजीकरण करें", "venue": "स्थान", "seats": "सीटें", "indoor": "इनडोर", "outdoor": "आउटडोर",
        "google": "गूगल मानचित्र लिंक", "notes": "टिप्पणी", "tour_map": "टूर मानचित्र", "tour_route": "मार्ग",
        "password": "व्यवस्थापक पासवर्ड", "login": "लॉगिन", "logout": "लॉगआउट", "date": "दिनांक",
        "total": "कुल दूरी और समय", "already_added": "यह शहर पहले से जोड़ा गया है।"
    },
}

# =============================================
# 도시 리스트 및 좌표
# =============================================
cities = sorted([
    "Mumbai", "Pune", "Nagpur", "Nashik", "Thane", "Aurangabad", "Solapur",
    "Amravati", "Nanded", "Kolhapur", "Akola", "Latur", "Ahmadnagar", "Jalgaon",
    "Dhule", "Malegaon", "Bhusawal", "Bhiwandi", "Bhandara", "Beed"
])

coords = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08),
    "Nashik": (20.00, 73.79), "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34),
    "Solapur": (17.67, 75.91), "Amravati": (20.93, 77.75), "Nanded": (19.16, 77.31),
    "Kolhapur": (16.70, 74.24), "Akola": (20.70, 77.00), "Latur": (18.40, 76.18),
    "Ahmadnagar": (19.10, 74.75), "Jalgaon": (21.00, 75.57), "Dhule": (20.90, 74.77),
    "Malegaon": (20.55, 74.53), "Bhusawal": (21.05, 76.00), "Bhiwandi": (19.30, 73.06),
    "Bhandara": (21.17, 79.65), "Beed": (18.99, 75.76)
}

# =============================================
# 거리 계산 함수
# =============================================
def distance_km(p1, p2):
    R = 6371
    lat1, lon1 = radians(p1[0]), radians(p1[1])
    lat2, lon2 = radians(p2[0]), radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="Cantata Tour", layout="wide")

# 세션 상태 초기화
for key, default in [("lang", "ko"), ("admin", False), ("route", []), ("venue_data", {})]:
    st.session_state.setdefault(key, default)

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    st.session_state.lang = st.selectbox("Language", ["ko", "hi"], index=["ko", "hi"].index(st.session_state.lang))
    _ = LANG[st.session_state.lang]

    st.markdown("---")
    st.write("**Admin Panel**")

    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0691":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("Wrong password")
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 테마 CSS + 눈 효과 (CSS 먼저!)
# =============================================
st.markdown("""
<style>
.stApp {
  background: radial-gradient(circle at 20% 20%, #0b0b10 0%, #000000 100%);
  color: #ffffff;
  font-family: 'Noto Sans KR', sans-serif;
  overflow: hidden;
  position: relative;
}

/* 제목: 한 줄 강제 + 크기 조절 */
h1 {
  color: #ff3b3b !important;
  text-align: center;
  font-weight: 900;
  font-size: 3.0em !important;
  white-space: nowrap;
  text-shadow: 0 0 25px #b71c1c;
  margin: 10px 0 !important;
}
h1 span.year {color: #ffffff; font-size: 0.85em; vertical-align: super;}
h2.subtitle {text-align: center; color: #d0d0d0; font-size: 1.2em; margin-top: -10px;}

/* 눈 효과 */
.snowflake {
  position: fixed;
  color: #ffffff;
  font-size: 1.6em;
  pointer-events: none;
  animation: fall linear infinite;
  z-index: 9999;
  opacity: 0.9;
}
@keyframes fall {
  0% {transform: translateY(-10vh) rotate(0deg); opacity: 1;}
  100% {transform: translateY(110vh) rotate(360deg); opacity: 0;}
}

/* Expander */
.streamlit-expanderHeader {
  background-color: rgba(0, 80, 40, 0.7) !important;
  color: #fff !important;
}
</style>
""", unsafe_allow_html=True)

# =============================================
# 눈 폭설 생성 (200개! CSS 로드 후 실행)
# =============================================
snowflakes = "".join(
    f'<div class="snowflake" style="left:{random.randint(0,100)}%; top:-10%; animation-duration:{random.uniform(8,20)}s; animation-delay:{random.uniform(0,5)}s;">❄️</div>'
    for _ in range(200)
)
st.markdown(snowflakes, unsafe_allow_html=True)

# =============================================
# 제목 (한 줄!)
# =============================================
st.markdown(f"<h1>🎄 {_['title']} <span class='year'>2025</span></h1>", unsafe_allow_html=True)
st.markdown(f"<h2 class='subtitle'>{_['subtitle']}</h2>", unsafe_allow_html=True)

# =============================================
# 본문
# =============================================
left, right = st.columns([1, 2])

with left:
    st.subheader(f"{_['tour_route']}")

    c1, c2 = st.columns([3, 1])
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

    total_distance = 0.0
    total_hours = 0.0

    for i, c in enumerate(st.session_state.route):
        with st.expander(f"{c}"):
            today = datetime.now().date()
            date = st.date_input(_["date"], value=today, min_value=today, key=f"date_{c}_{i}")
            venue = st.text_input(_["venue"], key=f"venue_{c}_{i}")
            seats = st.number_input(_["seats"], min_value=0, step=50, key=f"seats_{c}_{i}")
            google = st.text_input(_["google"], key=f"google_{c}_{i}")
            notes = st.text_area(_["notes"], key=f"notes_{c}_{i}")
            io = st.radio("Type", [_["indoor"], _["outdoor"]], key=f"io_{c}_{i}")

            if st.session_state.admin:
                if st.button(_["register"], key=f"reg_{c}_{i}"):
                    st.session_state.venue_data[c] = {
                        "date": str(date), "venue": venue, "seats": seats,
                        "type": io, "google": google, "notes": notes
                    }
                    st.success("저장 완료")
                    st.rerun()

        if i > 0:
            prev = st.session_state.route[i - 1]
            if prev in coords and c in coords:
                dist = distance_km(coords[prev], coords[c])
                time_hr = dist / 60.0
                total_distance += dist
                total_hours += time_hr
                st.markdown(f"**{prev} → {c}**: {dist:.1f} km / {time_hr:.1f} 시간")

    if len(st.session_state.route) > 1:
        st.markdown("---")
        st.markdown(f"### {_['total']}")
        st.success(f"총 거리: {total_distance:.1f} km | 총 소요시간: {total_hours:.1f} 시간")

with right:
    st.subheader(f"{_['tour_map']}")
    # 지도 밝게! (OpenStreetMap 기본 타일)
    m = folium.Map(location=(19.75, 75.71), zoom_start=7, tiles="OpenStreetMap")

    points = [coords[c] for c in st.session_state.route if c in coords]
    if len(points) >= 2:
        AntPath(points, color="red", weight=4, delay=800).add_to(m)

    for c in st.session_state.route:
        if c in coords:
            data = st.session_state.venue_data.get(c, {})
            popup = f"<b>{c}</b><br>"
            if data:
                popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data['type']}<br>"
                if data.get("google"):
                    popup += f"<a href='{data['google']}' target='_blank'>Google Maps</a>"
            folium.Marker(
                coords[c], popup=popup,
                icon=folium.Icon(color="red", icon="music", prefix="fa")
            ).add_to(m)

    st_folium(m, width=900, height=650)
