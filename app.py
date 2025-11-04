import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from math import radians, sin, cos, sqrt, atan2
import re
import json
import os
import base64

# =============================================
# Streamlit state 초기화 (최상단!)
# =============================================
st.set_page_config(page_title="Cantata Tour", layout="wide")

if "lang" not in st.session_state: st.session_state.lang = "ko"
if "admin" not in st.session_state: st.session_state.admin = False
if "route" not in st.session_state: st.session_state.route = []
if "venue_data" not in st.session_state: st.session_state.venue_data = {}
if "notice_data" not in st.session_state: st.session_state.notice_data = []
if "new_notice" not in st.session_state: st.session_state.new_notice = False
if "show_notice_list" not in st.session_state: st.session_state.show_notice_list = False
if "show_full_notice" not in st.session_state: st.session_state.show_full_notice = None
if "show_popup" not in st.session_state: st.session_state.show_popup = True
if "exp_state" not in st.session_state: st.session_state.exp_state = {}

# =============================================
# 데이터 저장
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

# 데이터 로드
st.session_state.venue_data = load_venue_data()
st.session_state.notice_data = load_notice_data()
st.session_state.new_notice = len(st.session_state.notice_data) > 0

# =============================================
# 언어팩
# =============================================
LANG = {
    "ko": {"title": "칸타타 투어", "select_city": "도시 선택", "add_city": "추가",
           "register": "등록", "venue": "공연장", "seats": "좌석 수", "indoor": "실내", "outdoor": "실외",
           "google": "구글 지도 링크", "notes": "특이사항", "tour_map": "투어 지도", "tour_route": "경로",
           "password": "관리자 비밀번호", "login": "로그인", "logout": "로그아웃", "date": "공연 날짜",
           "total": "총 거리 및 소요시간", "already_added": "이미 추가된 도시입니다.", "lang_name": "한국어",
           "notice_title": "공지 제목", "notice_content": "공지 내용", "notice_button": "공지", "new_notice": "새로운 공지",
           "notices": "이전 공지", "notice_save": "공지 추가", "upload_file": "사진/파일 업로드"},
    "en": {"title": "Cantata Tour", "select_city": "Select City", "add_city": "Add",
           "register": "Register", "venue": "Venue", "seats": "Seats", "indoor": "Indoor", "outdoor": "Outdoor",
           "google": "Google Maps Link", "notes": "Notes", "tour_map": "Tour Map", "tour_route": "Route",
           "password": "Admin Password", "login": "Log in", "logout": "Log out", "date": "Date",
           "total": "Total Distance & Time", "already_added": "City already added.", "lang_name": "English",
           "notice_title": "Notice Title", "notice_content": "Notice Content", "notice_button": "Notice", "new_notice": "New Notice",
           "notices": "Previous Notices", "notice_save": "Add Notice", "upload_file": "Upload File/Photo"},
    "hi": {"title": "कांटाटा टूर", "select_city": "शहर चुनें", "add_city": "जोड़ें",
           "register": "पंजीकरण करें", "venue": "स्थान", "seats": "सीटें", "indoor": "इनडोर", "outdoor": "आउटडोर",
           "google": "गूगल मानचित्र लिंक", "notes": "टिप्पणी", "tour_map": "टूर मानचित्र", "tour_route": "मार्ग",
           "password": "व्यवस्थापक पासवर्ड", "login": "लॉगिन", "logout": "लॉगआउट", "date": "दिनांक",
           "total": "कुल दूरी और समय", "already_added": "यह शहर पहले से जोड़ा गया है।", "lang_name": "हिन्दी",
           "notice_title": "सूचना शीर्षक", "notice_content": "सूचना सामग्री", "notice_button": "सूचना", "new_notice": "नई सूचना",
           "notices": "पिछली सूचनाएं", "notice_save": "सूचना जोड़ें", "upload_file": "फ़ाइल/तस्वीर अपलोड करें"}
}

# =============================================
# 3개 도시 + 좌표
# =============================================
cities = ["Mumbai", "Pune", "Nagpur"]
coords = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882)
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
# Sidebar
# =============================================
with st.sidebar:
    lang_options = {"ko": "한국어", "en": "English", "hi": "हिन्दी"}
    lang_selected = st.selectbox("Language", options=list(lang_options.keys()), format_func=lambda x: lang_options[x])
    st.session_state.lang = lang_selected
    _ = LANG[st.session_state.lang]

    st.markdown("---")
    st.write("**Admin**")
    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0691":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.rerun()

# =============================================
# Theme + 모바일 반응형
# =============================================
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at 20% 20%, #0a0a0f 0%, #000000 100%); color: #ffffff; font-family: 'Noto Sans KR', sans-serif; }
h1 { color: #ff3333 !important; text-align: center; font-weight: 900; font-size: 4.3em; text-shadow: 0 0 25px #b71c1c, 0 0 15px #00ff99; margin-bottom: 0; }
h1 span.year { color: #ffffff; font-weight: 800; font-size: 0.8em; vertical-align: super; }
h1 span.subtitle { color: #cccccc; font-size: 0.45em; vertical-align: super; margin-left: 5px; }
#notice-button { 
    position: absolute; top: 10px; right: 10px; z-index: 1000; 
    background: linear-gradient(90deg, #ff3b3b, #228B22); color: white; 
    padding: 10px 15px; border-radius: 8px; font-weight: 700; cursor: pointer; 
    transition: 0.3s; box-shadow: 0 0 10px #ff4d4d;
}
#notice-button:hover { transform: scale(1.1); }
#notice-button.neon { animation: neon 1.5s infinite alternate; }
@keyframes neon { from { box-shadow: 0 0 5px #ff00ff; } to { box-shadow: 0 0 20px #ff00ff; } }
#notice-list { 
    position: fixed; top: 60px; right: 10px; z-index: 1000; 
    background: #0a0a0f; padding: 10px; border-radius: 8px; max-height: 70vh; overflow-y: auto; 
    box-shadow: 0 0 10px #ff4d4d;
}
#full-screen-notice { 
    position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
    background: rgba(0,0,0,0.95); z-index: 10000; display: flex; align-items: center; justify-content: center; 
}
#full-screen-notice-content { 
    background: #228B22; padding: 30px; border-radius: 15px; max-width: 90%; max-height: 90%; overflow-y: auto; 
}
.distance-label { background: rgba(255, 0, 0, 0.7); color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; white-space: nowrap; transform: rotate(-30deg); }
@media (max-width: 768px) {
    #notice-button { top: 5px; right: 5px; font-size: 0.8em; padding: 8px 12px; }
    #notice-list { top: 50px; right: 5px; max-height: 50vh; }
}
</style>
""", unsafe_allow_html=True)

# =============================================
# Title
# =============================================
st.markdown(
    f"<h1>{_['title']} <span class='year'>2025</span><span class='subtitle'>마하라스트라</span> 🎄</h1>",
    unsafe_allow_html=True
)

# =============================================
# 일반 모드
# =============================================
if not st.session_state.admin:
    # 공지 버튼
    neon_class = "neon" if st.session_state.new_notice else ""
    button_label = f"{_['new_notice']} 📢" if st.session_state.new_notice else _["notice_button"]
    st.markdown(f"""
    <div id="notice-button" class="{neon_class}" onclick="document.getElementById('notice_btn_hidden').click();">
        {button_label}
    </div>
    """, unsafe_allow_html=True)
    if st.button("", key="notice_btn_hidden"):
        st.session_state.show_notice_list = not st.session_state.show_notice_list
        if st.session_state.new_notice:
            st.session_state.new_notice = False
        st.rerun()

    # 지도
    st.subheader(_["tour_map"])
    try:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    except:
        st.error("Google Maps API 키 없음")
        st.stop()

    m = folium.Map(location=(19.75, 75.71), zoom_start=6,
                   tiles=f"https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_API_KEY}",
                   attr="Google")

    points = [coords[c] for c in st.session_state.route if c in coords]
    if len(points) >= 2:
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            dist = distance_km(p1, p2)
            time_hr = dist / 60.0
            mid_lat = (p1[0] + p2[0]) / 2
            mid_lng = (p1[1] + p2[1]) / 2
            folium.Marker(
                location=[mid_lat, mid_lng],
                icon=folium.DivIcon(html=f"""
                    <div class="distance-label">
                        {dist:.1f} km / {time_hr:.1f} h
                    </div>
                """)
            ).add_to(m)
        AntPath(points, color="red", weight=4, delay=800).add_to(m)

    for c in st.session_state.route:
        if c in coords:
            data = st.session_state.venue_data.get(c, {})
            popup = f"<b>{c}</b><br>"
            if "date" in data:
                popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data['type']}<br>"
            if "google" in data and data["google"]:
                lat, lng = re.search(r'@(\d+\.\d+),(\d+\.\d+)', data["google"]) or (None, None)
                nav_link = f"https://www.google.com/maps/dir/?api=1&destination={lat.group(1)},{lng.group(1)}" if lat and lng else data["google"]
                popup += f"<a href='{nav_link}' target='_blank'>네비 시작</a>"
            folium.Marker(coords[c], popup=popup,
                          icon=folium.Icon(color="red", icon="music", prefix="fa")).add_to(m)

    st_folium(m, width=900, height=650)

    # 공지 리스트
    if st.session_state.show_notice_list:
        st.markdown(f"""
        <div id="notice-list">
            <h4>{_['notices']}</h4>
        """, unsafe_allow_html=True)
        today_notices = [n for n in st.session_state.notice_data if datetime.strptime(n["timestamp"].split('.')[0], "%Y-%m-%d %H:%M:%S").date() == datetime.now().date()]
        for notice in today_notices:
            if st.button(notice["title"], key=f"notice_{notice['id']}"):
                st.session_state.show_full_notice = notice["id"]
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 전체 화면 공지 (전체 클릭 시 닫힘)
    if st.session_state.show_full_notice is not None:
        notice = next((n for n in st.session_state.notice_data if n["id"] == st.session_state.show_full_notice), None)
        if notice:
            content = notice["content"]
            if "file" in notice and notice["file"]:
                content += f"<br><img src='data:image/png;base64,{notice['file']}' style='max-width:100%;'>"
            st.markdown(f"""
            <div id="full-screen-notice" onclick="document.getElementById('close_full_notice_hidden').click();">
                <div id="full-screen-notice-content" onclick="event.stopPropagation();">
                    <h3>{notice['title']}</h3>
                    <div>{content}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("", key="close_full_notice_hidden"):
                st.session_state.show_full_notice = None
                st.rerun()

    # 새 공지 팝업
    if st.session_state.new_notice and st.session_state.show_popup:
        st.markdown("""
        <audio autoplay>
            <source src="https://www.soundjay.com/holiday/christmas-bells-1.mp3" type="audio/mpeg">
        </audio>
        <script>
            setTimeout(() => { document.querySelector('audio').pause(); }, 5000);
        </script>
        """, unsafe_allow_html=True)
        latest = st.session_state.notice_data[0]
        st.markdown(f"""
        <div id="full-screen-notice" onclick="document.getElementById('close_popup_hidden').click();">
            <div id="full-screen-notice-content" onclick="event.stopPropagation();">
                <h3>{latest['title']}</h3>
                <p>{latest['content']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("", key="close_popup_hidden"):
            st.session_state.show_popup = False
            st.rerun()

    st.stop()

# =============================================
# 관리자 모드 (이전 코드 유지)
# =============================================
# (이전 관리자 코드 그대로 – 생략)
