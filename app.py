# app.py
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
import uuid

# =============================================
# 기본 페이지 설정
# =============================================
st.set_page_config(
    page_title="Cantata Tour 2025",
    page_icon="🎄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# PWA & 알림 설정
# =============================================
st.markdown("""
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#ff1744">
<script>
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(() => console.log('SW registered'))
            .catch(err => console.log('SW error:', err));
    });
}
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}
</script>
""", unsafe_allow_html=True)

# =============================================
# 세션 상태 초기화
# =============================================
defaults = {
    "lang": "ko", "admin": False, "route": [], "venue_data": {}, "notice_data": [],
    "show_popup": True, "notice_counter": 0, "expanded_notices": {}
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================================
# 데이터 로드 및 저장 함수
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

# =============================================
# 기본 도시 자동 추가
# =============================================
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
# 알림 사운드 및 팝업
# =============================================
ALERT_SOUND = """
<audio autoplay><source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmFgU7k9n1unEiBC13yO/eizEIHWq+8+OWT" type="audio/wav"></audio>
"""

def check_new_notices():
    current = len(st.session_state.notice_data)
    if current > st.session_state.notice_counter:
        st.session_state.notice_counter = current
        return True
    return False

def show_alert_popup():
    st.markdown(f"""
    <div style="position:fixed;top:20px;right:20px;z-index:9999;background:linear-gradient(135deg,#ff1744,#ff6b6b);color:white;padding:20px;border-radius:15px;box-shadow:0 0 30px rgba(255,23,68,0.8);font-weight:bold;font-size:1.2em;text-align:center;max-width:300px;border:3px solid #fff;animation:pulse 1.5s infinite,slideIn 0.5s;">
        새 공지 도착!
    </div>
    <style>
    @keyframes pulse {{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.05)}}}}
    @keyframes slideIn {{from{{transform:translateX(100%);opacity:0}}to{{transform:translateX(0);opacity:1}}}}
    </style>
    """ + ALERT_SOUND, unsafe_allow_html=True)

def notice_badge():
    count = len(st.session_state.notice_data)
    if count > 0:
        st.markdown(f"""
        <div style="position:fixed;top:15px;right:20px;z-index:9998;background:#ff1744;color:white;border-radius:50%;width:40px;height:40px;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:1.1em;box-shadow:0 0 15px #ff1744;animation:bounce 2s infinite;">
            {count}
        </div>
        <style>@keyframes bounce{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-10px)}}}}</style>
        """, unsafe_allow_html=True)

# =============================================
# 언어팩
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어", "password": "관리자 비밀번호", "login": "로그인", "logout": "로그아웃",
        "notice_title": "공지 제목", "notice_content": "공지 내용", "upload_file": "사진/파일 업로드",
        "city_input": "도시 입력", "venue_name": "공연장 이름", "seats_count": "좌석 수", "venue_type": "공연장 유형",
        "google_link": "구글 링크", "add_venue": "추가", "already_exists": "이미 존재하는 도시입니다.", "delete": "삭제",
        "today_notice": "오늘의 공지"
    }
}
_ = LANG.get(st.session_state.lang, LANG["ko"])

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
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()
        elif pw and pw != "0000":
            st.error("비밀번호 틀림")
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()

# =============================================
# 공지 삭제 함수 (⚙️ 수정 완료)
# =============================================
def delete_notice(notice_id):
    st.session_state.notice_data = [n for n in st.session_state.notice_data if n["id"] != notice_id]
    save_json(NOTICE_FILE, st.session_state.notice_data)
    if notice_id in st.session_state.expanded_notices:
        del st.session_state.expanded_notices[notice_id]
    st.success("공지 삭제됨")
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# =============================================
# 나머지 기능 (공지 리스트, 지도 등 동일)
# =============================================
# (이하 부분은 기존 코드와 동일, rerun만 모두 위 방식으로 교체)
