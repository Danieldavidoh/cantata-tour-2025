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

if "lang" not in st.session_state:
    st.session_state.lang = "ko"
if "admin" not in st.session_state:
    st.session_state.admin = False
if "route" not in st.session_state:
    st.session_state.route = []
if "venue_data" not in st.session_state:
    st.session_state.venue_data = {}
if "notice_data" not in st.session_state:
    st.session_state.notice_data = []
if "new_notice" not in st.session_state:
    st.session_state.new_notice = False
if "show_notice_list" not in st.session_state:
    st.session_state.show_notice_list = False
if "show_full_notice" not in st.session_state:
    st.session_state.show_full_notice = None
if "show_popup" not in st.session_state:
    st.session_state.show_popup = True
if "exp_state" not in st.session_state:
    st.session_state.exp_state = {}

# =============================================
# 데이터 저장 (실시간 반영)
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
    "ko": {
        "title": "칸타타 투어", "select_city": "도시 선택", "add_city": "추가",
        "register": "등록", "venue": "공연장", "seats": "좌석 수", "indoor": "실내", "outdoor": "실외",
        "google": "구글 지도 링크", "notes": "특이사항", "tour_map": "투어 지도", "tour_route": "경로",
        "password": "관리자 비밀번호", "login": "로그인", "logout": "로그아웃", "date": "공연 날짜",
        "total": "총 거리 및 소요시간", "already_added": "이미 추가된 도시입니다.",
        "notice_title": "공지 제목", "notice_content": "공지 내용", "notice_button": "공지", "new_notice": "새로운 공지",
        "upload_file": "사진/파일 업로드", "notice_status": "공지현황"
    },
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
# Theme (기본 위치)
# =============================================
st.markdown("""
<style>
.stApp { 
    background: radial-gradient(circle at 20% 20%, #0a0a0f 0%, #000000 100%); 
    color: #ffffff; 
    margin-top: 0;
}
h1 { 
    color: #ff3333 !important; 
    text-align: center; 
    font-weight: 900; 
    font-size: 4.3em; 
    text-shadow: 0 0 25px #b71c1c, 0 0 15px #00ff99; 
}
h1 span.year { color: #ffffff; font-weight: 800; font-size: 0.8em; vertical-align: super; }
h1 span.subtitle { color: #cccccc; font-size: 0.45em; vertical-align: super; margin-left: 5px; }
</style>
""", unsafe_allow_html=True)

# =============================================
# Title
# =============================================
st.markdown(f"<h1>{_['title']} <span class='year'>2025</span><span class='subtitle'>마하라스트라</span> 🎄</h1>", unsafe_allow_html=True)

# =============================================
# 일반 모드
# =============================================
if not st.session_state.admin:
    # 투어지도
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
                    match = re.search(r'@(\d+\.\d+),(\d+\.\d+)', data["google"])
                    lat, lng = (match.group(1), match.group(2)) if match else (None, None)
                    nav_link = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}" if lat and lng else data["google"]
                    popup += f"<a href='{nav_link}' target='_blank'>네비 시작</a>"
                folium.Marker(coords[c], popup=popup,
                              icon=folium.Icon(color="red", icon="music", prefix="fa")).add_to(m)

        st_folium(m, width=900, height=650)

    # 투어지도 아래 공지현황 버튼 (말풍선)
    st.markdown("---")
    notice_expander = st.expander("공지현황", expanded=False)
    with notice_expander:
        if st.session_state.notice_data:
            for notice in st.session_state.notice_data:
                st.markdown(f"""
                <div class="speech-bubble">
                    <button class="notice-title-btn" onclick="document.getElementById('open_notice_{notice['id']}').click();">{notice['title']}</button>
                </div>
                """, unsafe_allow_html=True)
                if st.button("", key=f"open_notice_{notice['id']}"):
                    st.session_state.show_full_notice = notice["id"]
                    st.rerun()
        else:
            st.write("공지가 없습니다.")

    # 새 공지 슬라이드 알림 + 캐롤
    if st.session_state.new_notice and st.session_state.show_popup:
        st.markdown("""
        <div class="slide-alert">
            <span>따끈한 공지가 도착했어요!</span>
            <span>따끈한 공지가 도착했어요!</span>
            <span>따끈한 공지가 도착했어요!</span>
        </div>
        <audio autoplay>
            <source src="https://www.soundjay.com/misc/sounds/bell-ringing-04.mp3" type="audio/mpeg">
        </audio>
        <script>
            setTimeout(() => { 
                document.querySelector('audio').pause(); 
                document.querySelector('.slide-alert').style.display = 'none';
            }, 6000);
        </script>
        <style>
        .slide-alert {
            position: fixed;
            top: 50px;
            right: 0;
            background: linear-gradient(90deg, #ff3b3b, #228B22);
            color: white;
            padding: 10px 20px;
            font-weight: bold;
            white-space: nowrap;
            overflow: hidden;
            z-index: 10002;
            animation: slide 10s linear infinite;
        }
        @keyframes slide {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }
        </style>
        """, unsafe_allow_html=True)
        st.session_state.show_popup = False

    # 공지현황 클릭 시 슬라이드 사라짐
    if notice_expander:
        st.markdown("<script>document.querySelector('.slide-alert')?.remove();</script>", unsafe_allow_html=True)

    # 전체 화면 공지 (새 나가기 버튼)
    if st.session_state.show_full_notice is not None:
        notice = next((n for n in st.session_state.notice_data if n["id"] == st.session_state.show_full_notice), None)
        if notice:
            content = notice["content"]
            if "file" in notice and notice["file"]:
                content += f"<br><img src='data:image/png;base64,{notice['file']}' style='max-width:100%;'>"

            close_clicked = st.button("", key="close_full_notice_hidden")
            if close_clicked:
                st.session_state.show_full_notice = None
                st.rerun()

            st.markdown(f"""
            <div id="full-screen-notice">
                <button id="new-exit-button" onclick="document.getElementById('close_full_notice_hidden').click();">나가기</button>
                <div id="full-screen-notice-content">
                    <h3>{notice['title']}</h3>
                    <div>{content}</div>
                </div>
            </div>
            <style>
            #full-screen-notice {
                position: fixed;
                top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.95);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            #full-screen-notice-content {
                background: #228B22;
                padding: 30px;
                border-radius: 15px;
                max-width: 90%;
                max-height: 90%;
                overflow-y: auto;
                position: relative;
            }
            #new-exit-button {
                position: absolute;
                top: 10px;
                right: 10px;
                background: #ff3b3b;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 0 10px rgba(255, 59, 59, 0.8);
            }
            #new-exit-button:hover {
                background: #cc0000;
                transform: scale(1.05);
            }
            .speech-bubble {
                background: #fff;
                border-radius: 15px;
                padding: 10px 15px;
                margin: 10px 0;
                position: relative;
                max-width: 80%;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            .speech-bubble:after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 50%;
                width: 0;
                height: 0;
                border: 10px solid transparent;
                border-top-color: #fff;
                border-bottom: 0;
                margin-left: -10px;
                margin-bottom: -10px;
            }
            .notice-title-btn {
                background: none;
                border: none;
                font-weight: bold;
                color: #228B22;
                cursor: pointer;
                text-align: left;
                width: 100%;
            }
            </style>
            """, unsafe_allow_html=True)

    st.stop()

# =============================================
# 관리자 모드 (생략 – 이전 유지)
# =============================================
