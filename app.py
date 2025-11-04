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
if "show_notice_status" not in st.session_state:
    st.session_state.show_notice_status = False

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
           "notice_save": "공지 추가", "upload_file": "사진/파일 업로드", "notice_status": "공지현황"},
    # (en, hi 생략 – 필요 시 추가)
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
# Theme
# =============================================
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at 20% 20%, #0a0a0f 0%, #000000 100%); color: #ffffff; }
h1 { color: #ff3333 !important; text-align: center; font-weight: 900; font-size: 4.3em; text-shadow: 0 0 25px #b71c1c, 0 0 15px #00ff99; }
h1 span.year { color: #ffffff; font-weight: 800; font-size: 0.8em; vertical-align: super; }
h1 span.subtitle { color: #cccccc; font-size: 0.45em; vertical-align: super; margin-left: 5px; }
#notice-button { position: absolute; top: 10px; right: 10px; z-index: 1000; background: linear-gradient(90deg, #ff3b3b, #228B22); color: white; padding: 10px 15px; border-radius: 8px; font-weight: 700; cursor: pointer; }
#notice-button.neon { animation: neon 1.5s infinite alternate; }
@keyframes neon { from { box-shadow: 0 0 5px #ff00ff; } to { box-shadow: 0 0 20px #ff00ff; } }
#notice-list { position: fixed; top: 60px; right: 10px; z-index: 1000; background: #0a0a0f; padding: 10px; border-radius: 8px; max-height: 70vh; overflow-y: auto; box-shadow: 0 0 10px #ff4d4d; }
#full-screen-notice { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 10000; display: flex; align-items: center; justify-content: center; }
#full-screen-notice-content { background: #228B22; padding: 30px; border-radius: 15px; max-width: 90%; max-height: 90%; overflow-y: auto; }
#close-button { position: absolute; top: calc(100% - 60px); right: 20px; background: #ff3b3b; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 20px; cursor: pointer; z-index: 10002; box-shadow: 0 0 10px rgba(255, 59, 59, 0.8); }
#close-button:hover { background: #cc0000; transform: scale(1.1); }
.distance-label { background: rgba(255, 0, 0, 0.7); color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; white-space: nowrap; transform: rotate(-30deg); }
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
    # (일반 모드 코드 생략 – 이전 유지)

    st.stop()

# =============================================
# 관리자 모드
# =============================================
if st.session_state.admin:
    # 공지 입력 (오른쪽 등록 버튼)
    st.markdown("---")
    st.subheader("공지사항 입력")
    
    col_input, col_button = st.columns([4, 1])
    with col_input:
        notice_title = st.text_input(_["notice_title"], key="notice_title_input")
        notice_content = st.text_area(_["notice_content"], key="notice_content_input")
        uploaded_file = st.file_uploader(_["upload_file"], type=["png", "jpg", "jpeg", "pdf", "txt"], key="notice_file_input")
    
    with col_button:
        st.write("")  # 공간
        st.write("")  # 공간
        if st.button("등록", key="register_notice_btn"):
            if notice_title and notice_content:
                file_b64 = None
                if uploaded_file:
                    file_b64 = base64.b64encode(uploaded_file.read()).decode()
                new_notice = {
                    "id": len(st.session_state.notice_data) + 1,
                    "title": notice_title,
                    "content": notice_content,
                    "file": file_b64,
                    "timestamp": str(datetime.now())
                }
                st.session_state.notice_data.insert(0, new_notice)
                save_notice_data(st.session_state.notice_data)
                st.success("공지 등록 완료")
                st.session_state.new_notice = True
                # 입력창 리셋
                st.rerun()
            else:
                st.error("제목과 내용을 입력하세요.")

    # 공지현황 버튼
    if st.button(_["notice_status"], key="show_notice_status"):
        st.session_state.show_notice_status = not st.session_state.show_notice_status
        st.rerun()

    left, right = st.columns([1, 2])

    with left:
        # (도시 입력 코드 생략 – 이전 유지)

    with right:
        st.subheader(_["tour_map"])
        # (지도 코드 생략 – 이전 유지)

        # 공지현황 창
        if st.session_state.show_notice_status:
            st.markdown("---")
            st.subheader("공지 현황")
            if st.session_state.notice_data:
                for notice in st.session_state.notice_data:
                    col1, col2 = st.columns([9, 1])
                    with col1:
                        st.write(f"**{notice['title']}**")
                    with col2:
                        if st.button("X", key=f"delete_notice_{notice['id']}"):
                            st.session_state.notice_data = [n for n in st.session_state.notice_data if n["id"] != notice["id"]]
                            save_notice_data(st.session_state.notice_data)
                            st.success("공지 삭제 완료")
                            st.rerun()
            else:
                st.write("공지가 없습니다.")
