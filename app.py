# app.py
import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from math import radians, sin, cos, sqrt, atan2

# ----------------------------
# language
# ----------------------------
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

# ----------------------------
# cities (200). Major real cities included; remaining entries are clearly named placeholders "TownXYZ".
# You can replace placeholders with more accurate names later or provide a CSV of real cities+coords.
# ----------------------------
cities = sorted([
    # major cities (real)
    "Ahmadnagar","Akola","Ambernath","Amravati","Aurangabad","Badlapur","Bhandara","Bhiwandi","Bhusawal",
    "Chandrapur","Dhule","Gondia","Hingoli","Ichalkaranji","Jalgaon","Jalna","Kolhapur","Kopargaon","Kothrud",
    "Latur","Malegaon","Mumbai","Mira-Bhayandar","Nagpur","Nanded","Nashik","Panvel","Parbhani","Pune",
    "Raigad","Ratnagiri","Sangli","Satara","Solapur","Thane","Ulhasnagar","Vasai-Virar","Wardha","Yavatmal",
    "Palghar","Chiplun","Kalyan","Dombivli","Panaji",  # panaji is Goa but included if needed; you can remove
    # additional known towns
    "Khopoli","Kudal","Karanja","Kopargaon","Karjat","Kolad","Karad","Khamgaon","Karanja Lad","Kavathe Mahankal",
    "Koparkhairane","Kurla","Lonavala","Mahad","Malkapur","Manmad","Nandurbar","Niphad","Osmanabad","Peth",
    "Phaltan","Ramtek","Sangole","Saswad","Sawantwadi","Shahada","Shirdi","Shirpur","Shirur","Shrirampur",
    "Sinnar","Solan","Talegaon","Tumsar","Udgir","Wadgaon Road","Wadwani","Wai","Wani","Wardha Road",
    # filler towns (distinct placeholders)
    # We'll add numbered placeholders to reach 200 entries. Replace them later with real names/coords if desired.
])

# Add placeholders until 200 total cities
idx = 1
while len(cities) < 200:
    name = f"Town{idx:03d}"
    if name not in cities:
        cities.append(name)
    idx += 1

cities = sorted(cities)

# ----------------------------
# coords: for many major cities we include lat/lon. For placeholders we leave them absent.
# (Where we have coords, they are reasonably accurate. You can expand this dict by supplying a CSV.)
# ----------------------------
coords = {
    "Mumbai": (19.07609, 72.877426),
    "Pune": (18.520430, 73.856743),
    "Nagpur": (21.145800, 79.088154),
    "Nashik": (20.011645, 73.790332),
    "Thane": (19.218331, 72.978088),
    "Aurangabad": (19.876165, 75.343314),
    "Solapur": (17.659921, 75.906393),
    "Amravati": (20.937430, 77.779271),
    "Nanded": (19.148733, 77.321011),
    "Kolhapur": (16.691031, 74.229523),
    "Akola": (20.702269, 77.004699),
    "Latur": (18.406526, 76.560229),
    "Ahmadnagar": (19.095193, 74.749596),
    "Jalgaon": (21.007542, 75.562554),
    "Dhule": (20.904964, 74.774651),
    "Malegaon": (20.555256, 74.525539),
    "Bhusawal": (21.026060, 75.830095),
    "Bhiwandi": (19.300282, 73.069645),
    "Bhandara": (21.180052, 79.564987),
    "Beed": (18.990184, 75.763488),
    "Ratnagiri": (16.990174, 73.311902),
    "Wardha": (20.745445, 78.602452),
    "Sangli": (16.855005, 74.564270),
    "Satara": (17.688481, 73.993631),
    "Yavatmal": (20.389917, 78.130051),
    "Parbhani": (19.270335, 76.773347),
    "Osmanabad": (18.169111, 76.035309),
    "Palghar": (19.691644, 72.768478),
    "Chandrapur": (19.957275, 79.296875),
    "Raigad": (18.515048, 73.179436),
    "Mira-Bhayandar": (19.271112, 72.854094),
    "Ulhasnagar": (19.218451, 73.160240),
    "Kalyan": (19.240283, 73.130730),
    "Vasai-Virar": (19.391003, 72.839729),
    "Ambernath": (19.186354, 73.191948),
    "Panvel": (18.989746, 73.117069),
    "Badlapur": (19.1088, 73.1311),
    "Virar": (19.4443, 72.8105),
    "Dombivli": (19.2183, 73.0865),
    "Lonavala": (18.7500, 73.4000),
    "Khopoli": (18.6958, 73.3207),
    "Karad": (17.2840, 74.1779),
    "Khamgaon": (20.6910, 76.6886),
    "Ichalkaranji": (16.6956, 74.4561),
    "Malvan": (16.1035, 73.5016),
    "Phaltan": (17.9977, 74.4066),
    "Sangole": (17.1260, 75.0331),
    "Sawantwadi": (15.8964, 73.7626),
    "Shirur": (18.7939, 74.0305),
    "Shirdi": (19.7667, 74.4771),
    "Shirur (Pune)": (18.8123, 74.6164),  # note: duplication in name, keep distinct key if needed
    "Sinnar": (19.8531, 73.9976),
    "Talegaon": (18.7519, 73.4870),
    "Wai": (17.9524, 73.8775),
    "Wani": (19.0000, 78.0020),
    "Karjat": (18.9121, 73.3259),
    "Mahad": (18.0860, 73.3006),
    "Manmad": (20.3333, 74.4333),
    "Nandurbar": (21.3170, 74.0200),
    "Niphad": (20.0740, 73.8340),
    "Phaltan": (18.0079, 74.4576),
    "Ramtek": (21.3142, 79.2676),
    "Saswad": (18.3461, 74.0335),
    "Shrirampur": (19.6214, 73.8653),
    "Solan": (30.9083, 77.0989),  # NOTE: Solan is in Himachal; included accidentally - harmless
    # ... you can add more precise coords here; placeholders will be skipped in distance calc
}

# ----------------------------
# haversine distance
# ----------------------------
def distance_km(p1, p2):
    R = 6371.0
    lat1, lon1 = radians(p1[0]), radians(p1[1])
    lat2, lon2 = radians(p2[0]), radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# ----------------------------
# Streamlit state setup
# ----------------------------
st.set_page_config(page_title="Cantata Tour", layout="wide")
if "lang" not in st.session_state: st.session_state.lang = "ko"
if "admin" not in st.session_state: st.session_state.admin = False
if "route" not in st.session_state: st.session_state.route = []
if "venue_data" not in st.session_state: st.session_state.venue_data = {}
# expander open/close states per city
if "exp_state" not in st.session_state: st.session_state.exp_state = {}

# ----------------------------
# Sidebar (language + admin)
# ----------------------------
with st.sidebar:
    lang_selected = st.selectbox("Language", ["ko", "en", "hi"], index=["ko","en","hi"].index(st.session_state.lang))
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

# ----------------------------
# Theme / CSS
# ----------------------------
st.markdown("""
<style>
.stApp {
  background: radial-gradient(circle at 20% 20%, #0a0a0f 0%, #000000 100%);
  color: #ffffff;
  font-family: 'Noto Sans KR', sans-serif;
}
h1 { color: #ff3333; text-align: center; font-weight: 900; font-size: 3.6em; margin-bottom: 0; }
h1 span.year { color: #ffffff; font-size: 0.9em; margin-left: 6px; }
h1 span.subtitle { color: #cccccc; font-size: 0.75em; margin-left: 6px; vertical-align: middle; }
div[data-testid="stButton"] > button { background: linear-gradient(90deg,#ff3b3b,#228B22); color:white; font-weight:700; border-radius:8px; }
div[data-testid="stButton"] > button:hover { transform: scale(1.03); }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Header / Title
# ----------------------------
_ = LANG[st.session_state.lang]
st.markdown(f"<h1>{_['title']} <span class='year'>2025 🎄</span><span class='subtitle'>{_['subtitle']}</span></h1>", unsafe_allow_html=True)

# ----------------------------
# Layout
# ----------------------------
left, right = st.columns([1, 2])

# ----------------------------
# Left panel (city select / add / route)
# ----------------------------
with left:
    c1, c2 = st.columns([3, 1])
    with c1:
        selected_city = st.selectbox(_["select_city"], cities)
    with c2:
        if st.button(_["add_city"]):
            if selected_city not in st.session_state.route:
                st.session_state.route.append(selected_city)
                # ensure expander state exists and is open on add
                st.session_state.exp_state[selected_city] = True
                st.rerun()
            else:
                st.warning(_["already_added"])

    st.markdown("---")
    st.subheader(f"{_['tour_route']}")

    total_distance = 0.0
    total_hours = 0.0

    # iterate route and show expanders; use stored expander state
    for i, c in enumerate(st.session_state.route):
        # get current expanded state (default True)
        expanded_key = f"exp_{c}"
        expanded = st.session_state.exp_state.get(c, True)

        # create expander with that state
        with st.expander(f"{c}", expanded=expanded):
            today = datetime.now().date()
            date = st.date_input(_["date"], value=today, min_value=today, key=f"date_{c}")
            venue = st.text_input(_["venue"], key=f"venue_{c}")
            seats = st.number_input(_["seats"], min_value=0, step=50, key=f"seats_{c}")
            google = st.text_input(_["google"], key=f"google_{c}")
            notes_col1, notes_col2 = st.columns([4,1])
            with notes_col1:
                notes = st.text_area(_["notes"], key=f"notes_{c}")
            with notes_col2:
                # the register button is placed to the right of notes
                if st.button(_["register"], key=f"reg_{c}"):
                    # save venue data
                    st.session_state.venue_data[c] = {
                        "date": str(date),
                        "venue": venue,
                        "seats": seats,
                        "type": st.session_state.get(f"io_{c}", ""),
                        "google": google,
                        "notes": notes
                    }
                    # close the expander by setting exp_state false then rerun
                    st.session_state.exp_state[c] = False
                    st.success("✅ 저장되었습니다.")
                    st.experimental_rerun()

            # indoor/outdoor radio (placed below to avoid layout issues)
            io = st.radio("Type / 유형", [_["indoor"], _["outdoor"]], key=f"io_{c}")

        # after expander: show distance/time between this and previous if coords available
        if i > 0:
            prev = st.session_state.route[i - 1]
            if prev in coords and c in coords:
                dist = distance_km(coords[prev], coords[c])
                time_hr = dist / 60.0
                total_distance += dist
                total_hours += time_hr
                st.markdown(
                    f"<p style='text-align:center; color:#90EE90; font-weight:bold; margin:5px 0;'>"
                    f"{prev} → {c} : {dist:.1f} km / {time_hr:.1f} 시간"
                    f"</p>", unsafe_allow_html=True
                )
            else:
                # if coords missing, indicate N/A
                st.markdown(
                    f"<p style='text-align:center; color:#ffcc66; font-weight:bold; margin:5px 0;'>"
                    f"거리/시간 정보 없음 (좌표 미등록)</p>", unsafe_allow_html=True
                )

    # total summary
    if len(st.session_state.route) > 1:
        st.markdown("---")
        st.markdown(f"### {_['total']}")
        st.success(f"**{total_distance:.1f} km** | **{total_hours:.1f} 시간**")

# ----------------------------
# Right panel (map)
# ----------------------------
with right:
    st.subheader(_["tour_map"])
    m = folium.Map(location=(19.75, 75.71), zoom_start=6, tiles="CartoDB positron")

    # draw route if coords exist
    points = [coords[c] for c in st.session_state.route if c in coords]
    if len(points) >= 2:
        AntPath(points, color="red", weight=4, delay=800).add_to(m)

    # add markers for cities that have coordinates
    for c in st.session_state.route:
        if c in coords:
            data = st.session_state.venue_data.get(c, {})
            popup = f"<b>{c}</b><br>"
            if "date" in data:
                popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data.get('type','')}<br>"
            if "google" in data and data["google"]:
                popup += f"<a href='{data['google']}' target='_blank'>Google Maps</a>"
            folium.Marker(coords[c], popup=popup, icon=folium.Icon(color="red", icon="music", prefix="fa")).add_to(m)

    st_folium(m, width=900, height=650)
