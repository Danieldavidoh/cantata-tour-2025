import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from math import radians, sin, cos, sqrt, atan2
import re  # Google Maps 위경도 추출
import json
import os

# =============================================
# 데이터 저장 (공유 json 파일)
# =============================================
VENUE_FILE = "venue_data.json"
NOTICE_FILE = "notice_data.json"

def load_venue_data():
    if os.path.exists(VENUE_FILE):
        with open(VENUE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_venue_data(data):
    with open(VENUE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_notice_data():
    if os.path.exists(NOTICE_FILE):
        with open(NOTICE_FILE, "r") as f:
            return json.load(f)
    return []

def save_notice_data(data):
    with open(NOTICE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =============================================
# 언어팩
# =============================================
LANG = {
    "ko": {"title": "칸타타 투어", "subtitle": "마하라스트라", "select_city": "도시 선택", "add_city": "추가",
           "register": "등록", "venue": "공연장", "seats": "좌석 수", "indoor": "실내", "outdoor": "실외",
           "google": "구글 지도 링크", "notes": "특이사항", "tour_map": "투어 지도", "tour_route": "경로",
           "password": "관리자 비밀번호", "login": "로그인", "logout": "로그아웃", "date": "공연 날짜",
           "total": "총 거리 및 소요시간", "already_added": "이미 추가된 도시입니다.", "lang_name": "한국어",
           "notice_title": "공지 제목", "notice_content": "공지 내용", "notice_button": "공지", "new_notice": "새로운 공지",
           "notices": "이전 공지"},
    "en": {"title": "Cantata Tour", "subtitle": "Maharashtra", "select_city": "Select City", "add_city": "Add",
           "register": "Register", "venue": "Venue", "seats": "Seats", "indoor": "Indoor", "outdoor": "Outdoor",
           "google": "Google Maps Link", "notes": "Notes", "tour_map": "Tour Map", "tour_route": "Route",
           "password": "Admin Password", "login": "Log in", "logout": "Log out", "date": "Date",
           "total": "Total Distance & Time", "already_added": "City already added.", "lang_name": "English",
           "notice_title": "Notice Title", "notice_content": "Notice Content", "notice_button": "Notice", "new_notice": "New Notice",
           "notices": "Previous Notices"},
    "hi": {"title": "कांटाटा टूर", "subtitle": "महाराष्ट्र", "select_city": "शहर चुनें", "add_city": "जोड़ें",
           "register": "पंजीकरण करें", "venue": "स्थान", "seats": "सीटें", "indoor": "इनडोर", "outdoor": "आउटडोर",
           "google": "गूगल मानचित्र लिंक", "notes": "टिप्पणी", "tour_map": "टूर मानचित्र", "tour_route": "मार्ग",
           "password": "व्यवस्थापक पासवर्ड", "login": "लॉगिन", "logout": "लॉग아우ट", "date": "दिनांक",
           "total": "कुल दूरी और समय", "already_added": "यह शहर पहले से जोड़ा गया है।", "lang_name": "हिन्दी",
           "notice_title": "सूचना शीर्षक", "notice_content": "सूचना सामग्री", "notice_button": "सूचना", "new_notice": "नई सूचना",
           "notices": "पिछली सूचनाएं"}
}

# =============================================
# 마하라슈트라 주요 150개 도시 (인구 순, 웹 검색 기반)
# =============================================
cities = sorted([
    "Mumbai", "Pune", "Nagpur", "Nashik", "Thane", "Aurangabad", "Solapur", "Amravati", "Nanded", "Kolhapur",
    "Akola", "Latur", "Ahmadnagar", "Jalgaon", "Dhule", "Malegaon", "Bhusawal", "Bhiwandi", "Bhandara", "Beed",
    "Ratnagiri", "Wardha", "Sangli", "Satara", "Yavatmal", "Parbhani", "Osmanabad", "Palghar", "Chandrapur", "Raigad",
    "Mira-Bhayandar", "Ulhasnagar", "Kalyan", "Vasai-Virar", "Ambernath", "Panvel", "Badlapur", "Virar", "Dombivli", "Bhivandi",
    "Ichalkaranji", "Khamgaon", "Phaltan", "Sangole", "Sawantwadi", "Shirur", "Shirdi", "Sinnar", "Talegaon", "Wai",
    "Wani", "Karjat", "Mahad", "Manmad", "Nandurbar", "Niphad", "Ramtek", "Saswad", "Shrirampur", "Lonavala",
    "Khopoli", "Karad", "Kopargaon", "Malvan", "Satara Road", "Kudal", "Karanja", "Kolad", "Kavathe Mahankal", "Koparkhairane",
    "Kurla", "Malkapur", "Peth", "Shahada", "Shirpur", "Solankur", "Sonegaon", "Tumsar", "Udgir", "Wadgaon Road",
    "Wadwani", "Chiplun", "Kothrud", "Gondia", "Hingoli", "Jalna", "Bhiwandi Nizampur", "Alibag", "Amalner", "Arvi",
    "Baramati", "Barsi", "Basmath", "Bhor", "Chakan", "Chalisgaon", "Chinchwad", "Dahanu", "Dapoli", "Daund",
    "Deolali", "Dehu", "Digras", "Erandol", "Gadhinglaj", "Gangakhed", "Gevrai", "Hinganghat", "Junnar", "Kagal",
    "Kandhar", "Kankavli", "Karanja Lad", "Khed", "Kinwat", "Koregaon", "Kurkumbh", "Lanja", "Loha", "Mahabaleshwar",
    "Mahagaon", "Majalgaon", "Mangalvedhe", "Mangaon", "Mhaswad", "Mokhada", "Morgaon", "Morshi", "Murbad", "Murtijapur",
    "Nandgaon", "Navi Mumbai", "Nilanga", "Ozar", "Pachora", "Paithan", "Pandharpur", "Paranda", "Parli", "Parner",
    "Partur", "Pathardi", "Patoda", "Pauni", "Pen", "Pimpalgaon Baswant", "Pimpri", "Pusad", "Rahuri", "Rajapur",
    "Rajgurunagar", "Raver", "Risod", "Roha", "Sangamner", "Saoner", "Sashti", "Savitri", "Selu", "Shevgaon",
    "Shrigonda", "Sillod", "Soygaon", "Talode", "Tasgaon", "Tirora", "Trimbak", "Tuljapur", "Umarga", "Umarkhed",
    "Uran", "Vaijapur", "Vani", "Vita", "Wada", "Warora", "Warud", "Washim", "Yaval", "Yeola"
])

coords = {
    "Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567), "Nagpur": (21.1458, 79.0882), "Nashik": (19.9975, 73.7898),
    "Thane": (19.2183, 72.9781), "Aurangabad": (19.8762, 75.3433), "Solapur": (17.6599, 75.9064), "Amravati": (20.9374, 77.7796),
    "Nanded": (19.1383, 77.3210), "Kolhapur": (16.7050, 74.2433), "Akola": (20.7096, 76.9981), "Latur": (18.4088, 76.5604),
    "Ahmadnagar": (19.0946, 74.7384), "Jalgaon": (21.0075, 75.5626), "Dhule": (20.9042, 74.7749), "Malegaon": (20.5540, 74.5255),
    "Bhusawal": (21.0455, 75.7877), "Bhiwandi": (19.2813, 73.0483), "Bhandara": (21.1700, 79.6500), "Beed": (18.9890, 75.7603),
    "Ratnagiri": (16.9944, 73.3002), "Wardha": (20.7453, 78.6022), "Sangli": (16.8544, 74.5642), "Satara": (17.6805, 74.0183),
    "Yavatmal": (20.3888, 78.1204), "Parbhani": (19.2686, 76.7708), "Osmanabad": (18.1816, 76.0389), "Palghar": (19.6969, 72.7699),
    "Chandrapur": (19.9615, 79.2961), "Raigad": (18.5167, 73.2000), "Mira-Bhayandar": (19.2813, 72.8561), "Ulhasnagar": (19.2215, 73.1645),
    "Kalyan": (19.2437, 73.1355), "Vasai-Virar": (19.4259, 72.8225), "Ambernath": (19.2098, 73.1867), "Panvel": (18.9894, 73.1175),
    "Badlapur": (19.1653, 73.2676), "Virar": (19.4559, 72.8114), "Dombivli": (19.2167, 73.0833), "Bhivandi": (19.3000, 73.0667),
    "Ichalkaranji": (16.7000, 74.4667), "Khamgaon": (20.7167, 76.5667), "Phaltan": (17.9833, 74.4333), "Sangole": (17.4333, 75.2000),
    "Sawantwadi": (15.9000, 73.8167), "Shirur": (18.8333, 74.3833), "Shirdi": (19.7667, 74.4833), "Sinnar": (19.8500, 74.0000),
    "Talegaon": (18.7333, 73.6667), "Wai": (17.9500, 73.9000), "Wani": (20.0667, 78.9500), "Karjat": (18.9167, 73.3333),
    "Mahad": (18.0833, 73.4167), "Manmad": (20.2500, 74.4500), "Nandurbar": (21.3667, 74.2500), "Niphad": (20.0833, 74.1167),
    "Ramtek": (21.4000, 79.3333), "Saswad": (18.3500, 74.0333), "Shrirampur": (19.6167, 74.6667), "Lonavala": (18.7500, 73.4167),
    "Khopoli": (18.7833, 73.3333), "Karad": (17.2833, 74.2000), "Kopargaon": (19.8833, 74.4833), "Malvan": (16.0667, 73.4667),
    "Satara Road": (17.6833, 74.0167), "Kudal": (16.0167, 73.6833), "Karanja": (20.4833, 77.4833), "Kolad": (18.4000, 73.2333),
    "Kavathe Mahankal": (17.0167, 74.8667), "Koparkhairane": (19.1167, 73.0000), "Kurla": (19.0833, 72.8833), "Malkapur": (20.8833, 76.2000),
    "Peth": (18.5500, 73.8333), "Shahada": (21.5500, 74.4667), "Shirpur": (21.3500, 74.8833), "Solankur": (16.7500, 74.4833),
    "Sonegaon": (21.1167, 79.0833), "Tumsar": (21.3833, 79.7333), "Udgir": (18.4000, 77.1167), "Wadgaon Road": (16.9000, 74.2833),
    "Wadwani": (18.9833, 76.0500), "Chiplun": (17.5333, 73.5167), "Kothrud": (18.5000, 73.8000), "Gondia": (21.4500, 80.2000),
    "Hingoli": (19.7167, 77.1500), "Jalna": (19.8333, 75.8833), "Bhiwandi Nizampur": (19.3000, 73.0667), "Alibag": (18.6411, 72.8722),
    "Amalner": (21.0500, 75.0667), "Arvi": (20.9833, 78.2333), "Baramati": (18.1500, 74.5833), "Barsi": (18.2333, 75.7000),
    "Basmath": (19.3167, 77.1667), "Bhor": (18.1667, 73.8500), "Chakan": (18.7667, 73.8500), "Chalisgaon": (20.4667, 75.0167),
    "Chinchwad": (18.6167, 73.8000), "Dahanu": (19.9667, 72.7333), "Dapoli": (17.7667, 73.2000), "Daund": (18.4667, 74.6000),
    "Deolali": (19.9500, 73.8333), "Dehu": (18.7167, 73.7667), "Digras": (20.1167, 77.7167), "Erandol": (20.9167, 75.3333),
    "Gadhinglaj": (16.2333, 74.3500), "Gangakhed": (18.9667, 76.7500), "Gevrai": (19.2667, 75.7500), "Hinganghat": (20.5500, 78.8333),
    "Junnar": (19.2000, 73.8833), "Kagal": (16.5833, 74.3167), "Kandhar": (18.9000, 77.2000), "Kankavli": (16.2667, 73.7000),
    "Karanja Lad": (20.4833, 77.4833), "Khed": (17.7167, 73.3833), "Kinwat": (19.6167, 78.2000), "Koregaon": (17.7000, 74.1667),
    "Kurkumbh": (18.3833, 74.5833), "Lanja": (16.8667, 73.5500), "Loha": (18.9667, 77.1333), "Mahabaleshwar": (17.9167, 73.6667),
    "Mahagaon": (16.8667, 77.7333), "Majalgaon": (19.1500, 76.2333), "Mangalvedhe": (17.5167, 75.4667), "Mangaon": (18.2333, 73.2833),
    "Mhaswad": (17.6333, 74.7833), "Mokhada": (19.9333, 73.3667), "Morgaon": (18.2667, 74.3167), "Morshi": (21.3333, 78.0167),
    "Murbad": (19.2500, 73.4000), "Murtijapur": (20.7333, 77.3667), "Nandgaon": (20.3167, 74.6500), "Navi Mumbai": (19.0330, 73.0297),
    "Nilanga": (18.1167, 76.7500), "Ozar": (20.1000, 73.9167), "Pachora": (20.6667, 75.3500), "Paithan": (19.4833, 75.3833),
    "Pandharpur": (17.6833, 75.3333), "Paranda": (18.2667, 75.4333), "Parli": (18.8500, 76.5333), "Parner": (19.0000, 74.4333),
    "Partur": (19.6000, 76.2167), "Pathardi": (19.1667, 75.1833), "Patoda": (18.8000, 75.5000), "Pauni": (20.7833, 79.6333),
    "Pen": (18.7333, 73.0833), "Pimpalgaon Baswant": (20.1667, 73.9833), "Pimpri": (18.6167, 73.8000), "Pusad": (19.9000, 77.5833),
    "Rahuri": (19.3833, 74.6500), "Rajapur": (16.6667, 73.5167), "Rajgurunagar": (18.8667, 73.9000), "Raver": (21.2500, 76.0333),
    "Risod": (19.9667, 76.7833), "Roha": (18.4333, 73.1167), "Sangamner": (19.5667, 74.2167), "Saoner": (21.3833, 78.9167),
    "Sashti": (19.7667, 79.2833), "Savitri": (17.9167, 73.4833), "Selu": (19.4500, 76.4500), "Shevgaon": (19.3500, 75.2333),
    "Shrigonda": (18.6167, 74.7000), "Sillod": (20.3000, 75.6500), "Soygaon": (20.6000, 75.6167), "Talode": (21.5667, 74.4667),
    "Tasgaon": (17.0333, 74.6000), "Tirora": (21.4000, 79.9333), "Trimbak": (19.9333, 73.5333), "Tuljapur": (18.0000, 76.0833),
    "Umarga": (17.8333, 76.6167), "Umarkhed": (19.6000, 77.6833), "Uran": (18.8833, 72.9500), "Vaijapur": (19.9167, 74.7333),
    "Vani": (20.2667, 74.1333), "Vita": (17.2667, 74.5333), "Wada": (19.6500, 73.1333), "Warora": (20.2333, 79.0000),
    "Warud": (21.4667, 78.2667), "Washim": (20.1167, 77.1333), "Yaval": (21.4000, 75.7000), "Yeola": (20.0333, 74.4833)
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
st.session_state.venue_data = load_venue_data()  # 공유
st.session_state.notice_data = load_notice_data()  # 공유
if "new_notice" not in st.session_state: st.session_state.new_notice = False  # 새 공지 플래그
if "viewed_notice" not in st.session_state: st.session_state.viewed_notice = set()  # 본 공지 ID

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

/* 제목: 칸타타 투어 빨간색 */
h1 {
  color: #ff3333 !important;
  text-align: center;
  font-weight: 900
font-size: 4.3em;
  text-shadow: 0 0 25px #b71c1c, 0 0 15px #00ff99;
  margin-bottom: 0;
}
h1 span.year {color: #ffffff; font-weight: 800;}
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
# Title
# =============================================
st.markdown(
    f"<h1>{_['title']} <span class='year'>2025 🎄</span></h1>"
    f"<h2>{_['subtitle']}</h2>",
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
                    save_venue_data(st.session_state.venue_data)
                    st.success("저장되었습니다.")
                    st.rerun()

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
        st.success(f"**{total_distance:.1f} km** | **{total_hours:.1f} 시간**")

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
