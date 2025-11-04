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
import uuid  # 🔥 중복 키 방지용 추가

# =============================================
# 초기 설정
# =============================================
st.set_page_config(page_title="Cantata Tour", layout="wide")

# =============================================
# 세션 상태 초기화
# =============================================
for key, value in {
    "lang": "ko",
    "admin": False,
    "route": [],
    "venue_data": {},
    "notice_data": [],
    "new_notice": False,
    "show_notice_list": False,
    "show_full_notice": None,
    "show_popup": True,
    "exp_state": {},
    "notice_counter": 0,
    "rerun_counter": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =============================================
# 데이터 파일 설정
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

st.session_state.venue_data = load_venue_data()
st.session_state.notice_data = load_notice_data()
st.session_state.new_notice = len(st.session_state.notice_data) > 0

# =============================================
# 언어 설정
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어", "select_city": "도시 선택", "add_city": "추가",
        "register": "등록", "venue": "공연장", "seats": "좌석 수", "indoor": "실내", "outdoor": "실외",
        "google": "구글 지도 링크", "notes": "특이사항", "tour_map": "투어 지도", "tour_route": "경로",
        "password": "관리자 비밀번호", "login": "로그인", "logout": "로그아웃", "date": "공연 날짜",
        "total": "총 거리 및 소요시간", "already_added": "이미 추가된 도시입니다.",
        "notice_title": "공지 제목", "notice_content": "공지 내용", "notice_button": "공지",
        "new_notice": "새로운 공지", "upload_file": "사진/파일 업로드", "notice_status": "공지현황"
    },
}

# =============================================
# 도시 정보
# =============================================
cities = ["Mumbai", "Pune", "Nagpur"]
coords = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882)
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
            if pw == "0000":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 화면 스타일
# =============================================
st.markdown("""
<style>
.stApp { 
    background: radial-gradient(circle at 20% 20%, #0a0a0f 0%, #000000 100%); 
    color: #ffffff; 
}
h1 { 
    color: #ff3333 !important; 
    text-align: center; 
    font-weight: 900; 
    font-size: 4em; 
    text-shadow: 0 0 25px #b71c1c, 0 0 15px #00ff99; 
}
h1 span.year { color: #ffffff; font-weight: 800; font-size: 0.8em; vertical-align: super; }
h1 span.subtitle { color: #cccccc; font-size: 0.45em; vertical-align: super; margin-left: 5px; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"<h1>{_['title']} <span class='year'>2025</span><span class='subtitle'>마하라스트라</span> 🎄</h1>", unsafe_allow_html=True)

# =============================================
# 일반 사용자 모드
# =============================================
if not st.session_state.admin:
    with st.expander("투어지도", expanded=False):
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
                mid_lat, mid_lng = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
                folium.Marker(
                    location=[mid_lat, mid_lng],
                    icon=folium.DivIcon(html=f"<div style='color:white;font-size:10pt'>{dist:.1f} km / {time_hr:.1f} h</div>")
                ).add_to(m)
            AntPath(points, color="red", weight=4, delay=800).add_to(m)

        for c in st.session_state.route:
            if c in coords:
                data = st.session_state.venue_data.get(c, {})
                popup = f"<b>{c}</b><br>"
                if "date" in data:
                    popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data['type']}<br>"
                if "google" in data and data["google"]:
                    match = re.search(r'@(\d+\.\d+),(\d+\.\d+)', data["google"])
                    lat, lng = (match.group(1), match.group(2)) if match else (None, None)
                    nav_link = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}" if lat and lng else data["google"]
                    popup += f"<a href='{nav_link}' target='_blank'>네비 시작</a>"
                folium.Marker(coords[c], popup=popup, icon=folium.Icon(color="red")).add_to(m)

        st_folium(m, width=900, height=600)

    st.markdown("---")
    with st.expander("공지현황", expanded=False):
        if st.session_state.notice_data:
            for notice in st.session_state.notice_data:
                unique_key = f"open_notice_{notice['id']}_{uuid.uuid4().hex}"
                st.button(notice["title"], key=unique_key)
        else:
            st.write("공지가 없습니다.")

    st.stop()

# =============================================
# 관리자 모드
# =============================================
if st.session_state.admin:
    st.subheader("공지사항 입력")
    title = st.text_input(_["notice_title"])
    content = st.text_area(_["notice_content"])
    uploaded = st.file_uploader(_["upload_file"], type=["png", "jpg", "jpeg"])
    if st.button("등록"):
        new_notice = {
            "id": len(st.session_state.notice_data) + 1,
            "title": title,
            "content": content,
            "timestamp": str(datetime.now())
        }
        if uploaded:
            new_notice["file"] = base64.b64encode(uploaded.read()).decode()
        st.session_state.notice_data.insert(0, new_notice)
        save_notice_data(st.session_state.notice_data)
        st.success("공지 등록 완료")
        st.rerun()

    st.markdown("---")
    with st.expander("공지현황", expanded=False):
        if st.session_state.notice_data:
            for n in st.session_state.notice_data:
                uid = f"{n['id']}_{uuid.uuid4().hex}"
                col1, col2 = st.columns([9, 1])
                with col1:
                    st.write(f"📢 {n['title']}")
                with col2:
                    if st.button("삭제", key=uid):
                        st.session_state.notice_data = [x for x in st.session_state.notice_data if x["id"] != n["id"]]
                        save_notice_data(st.session_state.notice_data)
                        st.success("삭제됨")
                        st.rerun()
        else:
            st.write("공지가 없습니다.")
