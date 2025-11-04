# app.py
import streamlit as st
import requests
import threading
import time
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from math import radians, sin, cos, sqrt, atan2
import re
import json
import os
import base64
import uuid

# =============================================
# 백엔드 서버 주소 (같은 머신에서 실행)
# =============================================
BACKEND_URL = "http://localhost:5000"

# =============================================
# PWA & 실시간 새로고침 설정
# =============================================
st.set_page_config(
    page_title="Cantata Tour 2025",
    page_icon="🎄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# PWA + 실시간 새로고침 스크립트
st.markdown(f"""
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#ff1744">
<script>
let ws;
function connectWebSocket() {{
    ws = new WebSocket("ws://localhost:5000/ws");
    ws.onmessage = function(event) {{
        if (event.data === "refresh") {{
            window.location.reload();
        }}
    }};
    ws.onclose = function() {{
        setTimeout(connectWebSocket, 3000);
    }};
}}
window.addEventListener('load', connectWebSocket);
</script>
""", unsafe_allow_html=True)

# =============================================
# 세션 상태 초기화
# =============================================
defaults = {
    "lang": "ko", "admin": False, "route": [], "venue_data": {}, "notice_data": [],
    "expanded_notice": None, "show_popup": True, "notice_counter": 0
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================================
# 데이터 로드/저장
# =============================================
VENUE_FILE = "venue_data.json"
NOTICE_FILE = "notice_data.json"

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

st.session_state.venue_data = load_json(VENUE_FILE, {})
st.session_state.notice_data = load_json(NOTICE_FILE, [])

# 기본 도시 자동 추가
default_cities = {
    "Mumbai": {"venue": "NSCI Dome", "seats": 5000, "type": "실내", "google": ""},
    "Pune": {"venue": "Balewadi Stadium", "seats": 8000, "type": "실외", "google": ""},
    "Nagpur": {"venue": "VCA Stadium", "seats": 45000, "type": "실외", "google": ""}
}
if not st.session_state.venue_data:
    st.session_state.venue_data = default_cities.copy()
    save_json(VENUE_FILE, st.session_state.venue_data)
for city in default_cities:
    if city not in st.session_state.route:
        st.session_state.route.append(city)

# =============================================
# 관리자 새로고침 → 모든 사용자 새로고침
# =============================================
def trigger_refresh():
    try:
        requests.post(f"{BACKEND_URL}/trigger_refresh")
    except:
        pass  # 백엔드 없으면 무시

# =============================================
# 언어 설정
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어", "password": "관리자 비밀번호", "login": "로그인", "logout": "로그아웃",
        "notice_title": "공지 제목", "notice_content": "공지 내용", "upload_file": "사진/파일 업로드"
    }
}
_ = LANG[st.session_state.lang] if st.session_state.lang in LANG else LANG["ko"]

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    lang_selected = st.selectbox("Language", ["ko", "en", "hi"], format_func=lambda x: {"ko":"한국어","en":"English","hi":"हिन्दी"}[x])
    st.session_state.lang = lang_selected if lang_selected in LANG else "ko"
    _ = LANG.get(st.session_state.lang, LANG["ko"])

    st.markdown("---")
    st.write("**Admin**")
    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]) and pw == "0000":
            st.session_state.admin = True
            st.rerun()
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 스타일
# =============================================
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at 20% 20%, #0a0a0f 0%, #000000 100%); color: #fff; }
h1 { color: #ff3333 !important; text-align: center; font-weight: 900; font-size: 4em;
     text-shadow: 0 0 25px #b71c1c, 0 0 15px #00ff99; }
.refresh-btn {
    background: #00c853; color: white; border: none; padding: 10px 20px; border-radius: 50px;
    font-weight: bold; cursor: pointer; box-shadow: 0 0 15px rgba(0,200,83,0.6);
}
.refresh-btn:hover { background: #00b140; transform: scale(1.05); }
</style>
""", unsafe_allow_html=True)

st.markdown(f"<h1>{_['title']} <span class='year'>2025</span><span class='subtitle'>마하라스트라</span> 🎄</h1>", unsafe_allow_html=True)

# =============================================
# 관리자 모드
# =============================================
if st.session_state.admin:
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("전체 새로고침", key="admin_refresh"):
            trigger_refresh()
            st.success("모든 사용자 새로고침 명령 전송!")
            st.rerun()

# =============================================
# 나머지 UI (이전과 동일, 생략)
# =============================================
# (투어지도, 공지현황 등 이전 코드 그대로 복사)

# ... (이전 코드의 나머지 부분 그대로)
