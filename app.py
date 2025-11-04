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
# PWA & 실시간 푸시 알림 설정
# =============================================
st.set_page_config(
    page_title="Cantata Tour 2025",
    page_icon="🎄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# PWA Manifest & Service Worker 등록
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
    "show_full_notice": None, "show_popup": True, "notice_counter": 0, "push_enabled": False
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

# =============================================
# 콜백 함수들
# =============================================
def delete_notice(notice_id):
    st.session_state.notice_data = [x for x in st.session_state.notice_data if x["id"] != notice_id]
    save_json(NOTICE_FILE, st.session_state.notice_data)
    if st.session_state.show_full_notice == notice_id:
        st.session_state.show_full_notice = None
    st.success("삭제됨")
    st.rerun()

def open_notice(notice_id):
    st.session_state.show_full_notice = notice_id
    st.rerun()

# =============================================
# 실시간 알림 시스템
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
# 언어 설정
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어", "select_city": "도시 선택", "add_city": "추가", "register": "등록",
        "venue": "공연장", "seats": "좌석 수", "indoor": "실내", "outdoor": "실외", "google": "구글 지도 링크",
        "notes": "특이사항", "tour_map": "투어 지도", "tour_route": "경로", "password": "관리자 비밀번호",
        "login": "로그인", "logout": "로그아웃", "date": "공연 날짜", "notice_title": "공지 제목",
        "notice_content": "공지 내용", "upload_file": "사진/파일 업로드", "notice_status": "공지현황"
    },
    "en": {
        "title": "Cantata Tour", "select_city": "Select City", "add_city": "Add", "register": "Register",
        "venue": "Venue", "seats": "Seats", "indoor": "Indoor", "outdoor": "Outdoor", "google": "Google Maps Link",
        "notes": "Notes", "tour_map": "Tour Map", "tour_route": "Route", "password": "Admin Password",
        "login": "Login", "logout": "Logout", "date": "Performance Date", "notice_title": "Notice Title",
        "notice_content": "Notice Content", "upload_file": "Upload Photo/File", "notice_status": "Notice Board"
    },
    "hi": {
        "title": "कांताता टूर", "select_city": "शहर चुनें", "add_city": "जोड़ें", "register": "रजिस्टर",
        "venue": "स्थल", "seats": "सीटें", "indoor": "इनडोर", "outdoor": "आउटडोर", "google": "गूगल मैप लिंक",
        "notes": "नोट्स", "tour_map": "टूर मैप", "tour_route": "रूट", "password": "एडमिन पासवर्ड",
        "login": "लॉगिन", "logout": "लॉगआउट", "date": "प्रदर्शन तिथि", "notice_title": "सूचना शीर्षक",
        "notice_content": "सूचना सामग्री", "upload_file": "फोटो/फ़ाइल अपलोड करें", "notice_status": "सूचना बोर्ड"
    }
}

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    lang_selected = st.selectbox(
        "Language", 
        ["ko", "en", "hi"], 
        format_func=lambda x: {"ko":"한국어","en":"English","hi":"हिन्दी"}[x]
    )
    st.session_state.lang = lang_selected if lang_selected in LANG else "ko"
    _ = LANG[st.session_state.lang]

    st.markdown("---")
    st.write("**Admin**")
    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]) and pw == "0000":
            st.session_state.admin = True
            st.rerun()
        elif pw and pw != "0000":
            st.error("비밀번호 틀림")
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
h1 span.year { color: #fff; font-size: 0.8em; vertical-align: super; }
h1 span.subtitle { color: #ccc; font-size: 0.45em; vertical-align: super; margin-left: 5px; }

.map-header {
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    margin-bottom: 10px;
}
.map-title {
    font-size: 1.5em; 
    font-weight: bold; 
    color: #ff6b6b;
}

.refresh-btn {
    background: none; 
    border: none; 
    cursor: pointer; 
    padding: 8px; 
    border-radius: 50%; 
    transition: all 0.2s;
    display: flex; align-items: center; justify-content: center;
    width: 40px; height: 40px;
}
.refresh-btn:hover {
    background: rgba(0,200,83,0.2); 
    transform: scale(1.1);
}
.refresh-icon {
    width: 24px; height: 24px; 
    animation: rotate 2s linear infinite paused;
}
.refresh-btn:hover .refresh-icon {
    animation-play-state: running;
}
@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.notice-card { 
    background:#1a1a1a; border:2px solid #333; border-radius:12px; padding:15px; margin:10px 0; 
    display:flex; justify-content:space-between; align-items:center; 
    gap: 10px;
}
.notice-title { color:#ff6b6b; font-weight:bold; flex: 1; }
.notice-time { color:#888; font-size:0.8em; margin-top: 4px; }
.notice-buttons { display: flex; gap: 8px; align-items: center; }
.btn-view, .btn-del { 
    background: #ff6b6b; color:white; border:none; padding:8px 14px; border-radius:6px; 
    cursor:pointer; font-size:0.9em; transition: all 0.2s; white-space: nowrap;
}
.btn-del { background: #d32f2f !important; }
.btn-view:hover, .btn-del:hover { transform: scale(1.05); opacity: 0.9; }

@media (max-width: 768px) {
    .map-header { flex-direction: row; justify-content: space-between; padding: 0 10px; }
    .map-title { font-size: 1.3em; }
    .refresh-btn { width: 36px; height: 36px; }
    .notice-card { flex-direction: column; text-align: center; gap: 10px; }
    .notice-buttons { justify-content: center; width: 100%; }
    .btn-view, .btn-del { flex: 1; max-width: 120px; }
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"<h1>{_['title']} <span class='year'>2025</span><span class='subtitle'>마하라스트라</span> 🎄</h1>", unsafe_allow_html=True)

# 구글 새로고침 SVG
REFRESH_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#00c853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="23,4 23,10 17,10"></polyline>
  <path d="M20.49,15A17.28,17.28,0,0,0,15.36,3.29L16.51,4.44a9,9,0,1,1-2.9,16.28A9,9,0,0,1,2.52,9"></path>
</svg>
"""

# =============================================
# 실시간 알림 활성화
# =============================================
notice_badge()
if check_new_notices() and st.session_state.show_popup:
    show_alert_popup()
    st.session_state.show_popup = False

# =============================================
# 도시 & 거리 계산
# =============================================
cities = ["Mumbai", "Pune", "Nagpur"]
coords = {"Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567), "Nagpur": (21.1458, 79.0882)}

def distance_km(p1, p2):
    R = 6371
    lat1, lon1 = radians(p1[0]), radians(p1[1])
    lat2, lon2 = radians(p2[0]), radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# =============================================
# 공통 공지현황 UI (컬럼 0 금지)
# =============================================
def render_notice_list(is_admin=False):
    if st.session_state.notice_data:
        for n in st.session_state.notice_data:
            uid = f"{'admin' if is_admin else 'user'}_notice_{n['id']}_{uuid.uuid4().hex[:8]}"
            
            st.markdown(f"""
            <div class="notice-card">
                <div style="flex: 1;">
                    <div class="notice-title">📢 {n['title']}</div>
                    <div class="notice-time">{n['timestamp'][:16].replace('T',' ')}</div>
                </div>
                <div class="notice-buttons">
                    <button class="btn-view" onclick="document.getElementById('{uid}_view').click(); return false;">보기</button>
                    {'<button class="btn-del" onclick="document.getElementById(\'{uid}_del\').click(); return false;">삭제</button>' if is_admin else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if is_admin:
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(" ", key=f"{uid}_view"):
                        open_notice(n['id'])
                with col2:
                    if st.button(" ", key=f"{uid}_del"):
                        delete_notice(n['id'])
            else:
                col1, _ = st.columns([1, 10])
                with col1:
                    if st.button(" ", key=f"{uid}_view"):
                        open_notice(n['id'])
    else:
        st.write("공지가 없습니다.")

# =============================================
# 일반 사용자 모드
# =============================================
if not st.session_state.admin:
    st.markdown(f"""
    <div class="map-header">
        <div class="map-title">투어지도</div>
        <button class="refresh-btn" onclick="window.location.reload(); return false;" title="새로고침">
            <div class="refresh-icon">{REFRESH_SVG}</div>
        </button>
    </div>
    """, unsafe_allow_html=True)

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
            for i in range(len(points)-1):
                p1, p2 = points[i], points[i+1]
                dist = distance_km(p1, p2)
                time_hr = dist / 60.0
                mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
                folium.Marker(mid, icon=folium.DivIcon(html=f"<div style='color:white;font-size:10pt'>{dist:.1f}km / {time_hr:.1f}h</div>")).add_to(m)
            AntPath(points, color="red", weight=4, delay=800).add_to(m)

        for c in st.session_state.route:
            if c in coords:
                data = st.session_state.venue_data.get(c, {})
                popup = f"<b>{c}</b><br>"
                if "date" in data: popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data['type']}<br>"
                if "google" in data and data["google"]:
                    match = re.search(r'@(\d+\.\d+),(\d+\.\d+)', data["google"])
                    lat, lng = (match.group(1), match.group(2)) if match else (None, None)
                    nav = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}" if lat else data["google"]
                    popup += f"<a href='{nav}' target='_blank'>네비 시작</a>"
                folium.Marker(coords[c], popup=popup, icon=folium.Icon(color="red")).add_to(m)
        st_folium(m, width=900, height=600)

    st.markdown("---")
    with st.expander("공지현황", expanded=st.session_state.show_full_notice is not None):
        render_notice_list(is_admin=False)

    if st.session_state.show_full_notice:
        notice = next((x for x in st.session_state.notice_data if x["id"] == st.session_state.show_full_notice), None)
        if notice:
            st.markdown(f"""
            <div style="background:rgba(10,10,15,0.95);padding:25px;border-radius:15px;border:2px solid #ff1744;margin:20px 0;box-shadow:0 0 30px rgba(255,23,68,0.4);">
                <h3 style="color:#ff6b6b;margin-top:0;">📢 {notice['title']}</h3>
                <p style="white-space:pre-line;line-height:1.8;">{notice['content']}</p>
                <small style="color:#888;">{notice['timestamp'][:16].replace('T',' ')}</small>
            </div>
            """, unsafe_allow_html=True)
            if 'file' in notice:
                st.image(base64.b64decode(notice['file']), use_column_width=True)
            if st.button("닫기"):
                st.session_state.show_full_notice = None
                st.rerun()

    st.stop()

# =============================================
# 관리자 모드
# =============================================
st.markdown(f"""
<div class="map-header">
    <div class="map-title">투어지도</div>
    <button class="refresh-btn" onclick="window.location.reload(); return false;" title="새로고침">
        <div class="refresh-icon">{REFRESH_SVG}</div>
    </button>
</div>
""", unsafe_allow_html=True)

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
        for i in range(len(points)-1):
            p1, p2 = points[i], points[i+1]
            dist = distance_km(p1, p2)
            time_hr = dist / 60.0
            mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
            folium.Marker(mid, icon=folium.DivIcon(html=f"<div style='color:white;font-size:10pt'>{dist:.1f}km / {time_hr:.1f}h</div>")).add_to(m)
        AntPath(points, color="red", weight=4, delay=800).add_to(m)

    for c in st.session_state.route:
        if c in coords:
            data = st.session_state.venue_data.get(c, {})
            popup = f"<b>{c}</b><br>"
            if "date" in data: popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data['type']}<br>"
            if "google" in data and data["google"]:
                match = re.search(r'@(\d+\.\d+),(\d+\.\d+)', data["google"])
                lat, lng = (match.group(1), match.group(2)) if match else (None, None)
                nav = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}" if lat else data["google"]
                popup += f"<a href='{nav}' target='_blank'>네비 시작</a>"
            folium.Marker(coords[c], popup=popup, icon=folium.Icon(color="red")).add_to(m)
    st_folium(m, width=900, height=600)

st.subheader("공지사항 입력")
title = st.text_input(_["notice_title"])
content = st.text_area(_["notice_content"])
uploaded = st.file_uploader(_["upload_file"], type=["png", "jpg", "jpeg"])

if st.button("등록") and title:
    new_notice = {
        "id": len(st.session_state.notice_data) + 1,
        "title": title,
        "content": content,
        "timestamp": str(datetime.now())
    }
    if uploaded:
        new_notice["file"] = base64.b64encode(uploaded.read()).decode()
    st.session_state.notice_data.insert(0, new_notice)
    save_json(NOTICE_FILE, st.session_state.notice_data)
    st.session_state.show_popup = True
    st.success("공지 등록 완료")
    st.rerun()

st.markdown("---")
with st.expander("공지현황", expanded=st.session_state.show_full_notice is not None):
    render_notice_list(is_admin=True)

if st.session_state.show_full_notice:
    notice = next((x for x in st.session_state.notice_data if x["id"] == st.session_state.show_full_notice), None)
    if notice:
        st.markdown(f"""
        <div style="background:rgba(10,10,15,0.95);padding:25px;border-radius:15px;border:2px solid #ff1744;margin:20px 0;box-shadow:0 0 30px rgba(255,23,68,0.4);">
            <h3 style="color:#ff6b6b;margin-top:0;">📢 {notice['title']}</h3>
            <p style="white-space:pre-line;line-height:1.8;">{notice['content']}</p>
            <small style="color:#888;">{notice['timestamp'][:16].replace('T',' ')}</small>
        </div>
        """, unsafe_allow_html=True)
        if 'file' in notice:
            st.image(base64.b64decode(notice['file']), use_column_width=True)
        if st.button("닫기"):
            st.session_state.show_full_notice = None
            st.rerun()
