import json, os, uuid, base64
import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
import random

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

# --- 2. 파일 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 3. 다국어 ---
LANG = {
    "ko": { "title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라", "tab_notice": "공지", "tab_map": "투어 경로", "today": "오늘", "yesterday": "어제", "new_notice_alert": "새 공지가 도착했어요!", "warning": "제목·내용 입력", "edit": "수정", "save": "입력", "cancel": "취소", "add_city": "도시 추가", "indoor": "실내", "outdoor": "실외", "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵", "perf_date": "공연 날짜", "change_pw": "비밀번호 변경", "current_pw": "현재 비밀번호", "new_pw": "새 비밀번호", "confirm_pw": "새 비밀번호 확인", "pw_changed": "비밀번호 변경 완료!", "pw_mismatch": "비밀번호 불일치", "pw_error": "현재 비밀번호 오류", "menu": "메뉴", "login": "로그인", "logout": "로그아웃", "delete": "제거" },
    "en": { "title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra", "tab_notice": "Notice", "tab_map": "Tour Route", "today": "Today", "yesterday": "Yesterday", "new_notice_alert": "New notice!", "warning": "Enter title & content", "edit": "Edit", "save": "Add", "cancel": "Cancel", "add_city": "Add City", "indoor": "Indoor", "outdoor": "Outdoor", "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps", "perf_date": "Performance Date", "change_pw": "Change Password", "current_pw": "Current Password", "new_pw": "New Password", "confirm_pw": "Confirm Password", "pw_changed": "Password changed!", "pw_mismatch": "Passwords don't match", "pw_error": "Incorrect current password", "menu": "Menu", "login": "Login", "logout": "Logout", "delete": "Remove" },
    "hi": { "title_cantata": "कैंटाटा टूर", "title_year": "2025", "title_region": "महाराष्ट्र", "tab_notice": "सूचना", "tab_map": "टूर मार्ग", "today": "आज", "yesterday": "कल", "new_notice_alert": "नई सूचना!", "warning": "शीर्षक·सामग्री दर्ज करें", "edit": "संपादन", "save": "जोड़ें", "cancel": "रद्द करें", "add_city": "शहर जोड़ें", "indoor": "इनडोर", "outdoor": "आउटडोर", "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप", "perf_date": "प्रदर्शन तिथि", "change_pw": "पासवर्ड बदलें", "current_pw": "वर्तमान पासवर्ड", "new_pw": "नया पासवर्ड", "confirm_pw": "पासवर्ड की पुष्टि करें", "pw_changed": "पासवर्ड बदल गया!", "pw_mismatch": "पासवर्ड मेल नहीं खाते", "pw_error": "गलत वर्तमान पासवर्ड", "menu": "मेनू", "login": "लॉगिन", "logout": "लॉगआउट", "delete": "हटाएं" }
}

# --- 4. 세션 상태 ---
defaults = { "admin": False, "lang": "ko", "tab_selection": None, "new_notice": False, "sound_played": False, "seen_notices": [], "expanded_notices": [], "expanded_cities": [], "last_tab": None, "alert_active": False, "current_alert_id": None, "password": "0009", "show_pw_form": False, "sidebar_open": False, "notice_open": False, "adding_city": False, "edit_mode": {} }
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 5. JSON 헬퍼 ---
def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 6. 초기 도시 + 좌표 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도", "google_link": "https://goo.gl/maps/abc123", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-10"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브", "google_link": "https://goo.gl/maps/def456", "indoor": True, "date": "11/07 02:01", "perf_date": "2025-11-12"},
    {"city": "Pune", "venue": "Aga Khan Palace", "seats": "2500", "note": "역사적 장소", "google_link": "https://goo.gl/maps/pune2", "indoor": False, "date": "11/08 14:00", "perf_date": "2025-11-14"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시", "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-16"}
]
if not os.path.exists(CITY_FILE): save_json(CITY_FILE, DEFAULT_CITIES)

CITY_COORDS = { "Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567), "Nagpur": (21.1458, 79.0882) }

# --- 7. 캐롤 사운드 ---
def play_carol():
    if os.path.exists("carol.wav"):
        st.session_state.sound_played = True
        st.markdown("<audio autoplay><source src='carol.wav' type='audio/wav'></audio>", unsafe_allow_html=True)

# --- 8. CSS + 제목 최상단 ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: url("background_christmas_dark.png"); background-size: cover; background-position: center; background-attachment: fixed; padding-top: 0 !important; }
    .fixed-title { position: fixed; top: 0; left: 0; width: 100%; z-index: 1000; text-align: center; padding: 10px 0; background: rgba(0, 0, 0, 0.3); }
    .main-title { font-size: 2.8em !important; font-weight: bold; text-shadow: 0 2px 5px rgba(0,0,0,0.3); margin: 0; }
    .tab-container { 
        background: rgba(255,255,255,0.9); 
        padding: 8px; 
        border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
        margin: 80px 0 10px 0 !important; 
        position: relative; 
        z-index: 10; 
        border: none !important;
        -webkit-appearance: none !important;
    }
    .content-area { margin-top: 0; }
    .snowflake { position: fixed; top: -15px; color: white; font-size: 1.1em; pointer-events: none; animation: fall linear infinite; opacity: 0.3 !important; text-shadow: 0 0 4px rgba(255,255,255,0.6); z-index: 1; }
    @keyframes fall { 0% { transform: translateY(0) rotate(0deg); } 100% { transform: translateY(120vh) rotate(360deg); } }
    .hamburger { position: fixed; top: 15px; left: 15px; z-index: 10000; background: rgba(0,0,0,0.6); color: white; border: none; border-radius: 50%; width: 50px; height: 50px; font-size: 24px; cursor: pointer; box-shadow: 0 0 10px rgba(0,0,0,0.3); }
    .sidebar-mobile { position: fixed; top: 0; left: -300px; width: 280px; height: 100vh; background: rgba(30,30,30,0.95); color: white; padding: 20px; transition: left 0.3s ease; z-index: 9999; overflow-y: auto; }
    .sidebar-mobile.open { left: 0; }
    .overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); z-index: 9998; display: none; }
    .overlay.open { display: block; }
    .notice-title-bar { background: rgba(255,255,255,0.95); padding: 12px; border-radius: 10px; margin: 8px 0; cursor: pointer; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
    @media (min-width: 769px) {
        .hamburger, .sidebar-mobile, .overlay { display: none !important; }
        section[data-testid="stSidebar"] { display: block !important; }
    }
    .stButton > button { border: none !important; -webkit-appearance: none !important; }
</style>
""", unsafe_allow_html=True)

# --- 눈송이 ---
for i in range(26):
    left = random.randint(0, 100)
    duration = random.randint(10, 20)
    size = random.uniform(0.8, 1.4)
    delay = random.uniform(0, 10)
    st.markdown(f"<div class='snowflake' style='left:{left}vw; animation-duration:{duration}s; font-size:{size}em; animation-delay:{delay}s;'>❄</div>", unsafe_allow_html=True)

# --- 제목 (최상단) ---
st.markdown('<div class="fixed-title">', unsafe_allow_html=True)
title_html = f'<span style="color:red;">{_("title_cantata")}</span> <span style="color:white;">{_("title_year")}</span> <span style="color:green; font-size:67%;">{_("title_region")}</span>'
st.markdown(f'<h1 class="main-title">{title_html}</h1>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 모바일 햄버거 메뉴 ---
st.markdown(f'''
<button class="hamburger" onclick="document.querySelector('.sidebar-mobile').classList.toggle('open'); document.querySelector('.overlay').classList.toggle('open');">☰</button>
<div class="overlay" onclick="document.querySelector('.sidebar-mobile').classList.remove('open'); this.classList.remove('open');"></div>
<div class="sidebar-mobile">
    <h3 style="color:white;">{_("menu")}</h3>
    <select onchange="window.location.href='?lang='+this.value" style="width:100%; padding:8px; margin:10px 0;">
        <option value="ko" {'selected' if st.session_state.lang=='ko' else ''}>한국어</option>
        <option value="en" {'selected' if st.session_state.lang=='en' else ''}>English</option>
        <option value="hi" {'selected' if st.session_state.lang=='hi' else ''}>हिंदी</option>
    </select>
    {'''
        <input type="password" placeholder="비밀번호" id="mobile_pw" style="width:100%; padding:8px; margin:10px 0;">
        <button onclick="if(document.getElementById(\'mobile_pw\').value==\'0009\') window.location.href=\'?admin=true\'; else alert(\'비밀번호 오류\');" style="width:100%; padding:10px; background:#e74c3c; color:white; border:none; border-radius:8px;">{_("login")}</button>
    ''' if not st.session_state.admin else f'''
        <button onclick="window.location.href=\'?admin=false\'" style="width:100%; padding:10px; background:#27ae60; color:white; border:none; border-radius:8px; margin:10px 0;">{_("logout")}</button>
    ''' }
</div>
''', unsafe_allow_html=True)

# --- 탭 + 내용 (공지 버튼 아래에 내용, 투어 경로 버튼은 사라짐) ---
st.markdown('<div class="content-area">', unsafe_allow_html=True)

# 공지 버튼
notice_btn = st.button(_(f"tab_notice"), use_container_width=True, key="tab_notice_btn")

# 공지 클릭 시 내용 + 투어 경로 버튼 사라짐
if notice_btn or st.session_state.tab_selection == _(f"tab_notice"):
    st.session_state.tab_selection = _(f"tab_notice")
    if st.session_state.admin:
        with st.expander("공지 작성"):
            with st.form("notice_form", clear_on_submit=True):
                title = st.text_input("제목", key="notice_title")
                content = st.text_area("내용", key="notice_content")
                img = st.file_uploader("이미지", type=["png", "jpg", "jpeg"], key="notice_img")
                file = st.file_uploader("첨부 파일", key="notice_file")
                if st.form_submit_button("등록", key="notice_submit"):
                    if title.strip() and content.strip():
                        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
                        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
                        if img: open(img_path, "wb").write(img.getbuffer())
                        if file: open(file_path, "wb").write(file.getbuffer())
                        notice = { "id": str(uuid.uuid4()), "title": title, "content": content, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"), "image": img_path, "file": file_path }
                        data = load_json(NOTICE_FILE)
                        data.insert(0, notice)
                        save_json(NOTICE_FILE, data)
                        st.success("공지 등록 완료!")
                        st.rerun()
                    else:
                        st.warning(_("warning"))

    data = load_json(NOTICE_FILE)
    for i, n in enumerate(data):
        with st.expander(f"{n['date']} | {n['title']}", expanded=False):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]): st.image(n["image"], use_column_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                b64 = base64.b64encode(open(n["file"], "rb").read()).decode()
                st.markdown(f'<a href="data:file/txt;base64,{b64}" download="{os.path.basename(n["file"])}">다운로드</a>', unsafe_allow_html=True)
            if st.session_state.admin and st.button(_("delete"), key=f"del_n_{n['id']}"):
                data.pop(i); save_json(NOTICE_FILE, data); st.rerun()

# 투어 경로 버튼 (공지 클릭 시 사라짐)
else:
    map_btn = st.button(_(f"tab_map"), use_container_width=True, key="tab_map_btn")
    if map_btn or st.session_state.tab_selection == _(f"tab_map"):
        st.session_state.tab_selection = _(f"tab_map")
        if st.session_state.admin:
            if st.button(_("add_city"), key="add_city_btn"):
                st.session_state.adding_city = True

            if st.session_state.get("adding_city", False):
                with st.container():
                    city_name = st.text_input("새 도시 입력", key="new_city_name")
                    if city_name:
                        with st.form("city_form_add"):
                            perf_date = st.date_input(_("perf_date"), key="add_perf_date")
                            venue = st.text_input(_("venue"), key="add_venue")
                            seats = st.number_input(_("seats"), min_value=0, value=500, step=50, key="add_seats")
                            indoor = st.radio("실내인지 실외인지", [_(f"indoor"), _(f"outdoor")], key="add_indoor")
                            google_link = st.text_input(_("google_link"), key="add_link")
                            note = st.text_area(_("note"), key="add_note")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.form_submit_button(_("edit"), key="edit_city_btn"):
                                    st.session_state.edit_mode = True
                                    st.rerun()
                            with col2:
                                if st.form_submit_button(_("save"), key="save_city_btn"):
                                    new_city = { "city": city_name, "venue": venue, "seats": str(seats), "indoor": indoor == _(f"indoor"), "note": note, "google_link": google_link, "perf_date": str(perf_date), "date": datetime.now().strftime("%m/%d %H:%M") }
                                    data = load_json(CITY_FILE)
                                    data.append(new_city)
                                    save_json(CITY_FILE, data)
                                    st.session_state.adding_city = False
                                    st.success("도시 추가 완료!")
                                    st.rerun()
                            with col3:
                                if st.form_submit_button(_("delete"), key="remove_city_btn"):
                                    st.session_state.adding_city = False
                                    st.rerun()

        # --- 지도 ---
        cities = load_json(CITY_FILE)
        m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="OpenStreetMap")
        for i, c in enumerate(cities):
            coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
            lat, lon = coords
            is_future = c.get("perf_date", "9999-12-31") >= str(date.today())
            color = "red" if is_future else "gray"
            indoor_text = _("indoor") if c.get("indoor") else _("outdoor")
            popup_html = f"<div style='font-size:14px; line-height:1.6;'><b>{c['city']}</b><br>{_('perf_date')}: {c.get('perf_date','미정')}<br>{_('venue')}: {c.get('venue','—')}<br>{_('seats')}: {c.get('seats','—')}<br>{indoor_text}<br><a href='https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving' target='_blank'>{_('google_link')}</a></div>"
            folium.Marker(coords, popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=color, icon="music", prefix="fa")).add_to(m)
            if i < len(cities) - 1:
                nxt_coords = CITY_COORDS.get(cities[i+1]["city"], (18.5204, 73.8567))
                AntPath([coords, nxt_coords], color="#e74c3c", weight=6, opacity=0.3 if not is_future else 1.0).add_to(m)
        st_folium(m, width=900, height=550, key="tour_map")

st.markdown('</div>', unsafe_allow_html=True)

# --- 사이드바 (PC) ---
with st.sidebar:
    lang_map = {"한국어": "ko", "English": "en", "हिंदी": "hi"}
    sel = st.selectbox("언어", list(lang_map.keys()), index=list(lang_map.values()).index(st.session_state.lang))
    if lang_map[sel] != st.session_state.lang:
        st.session_state.lang = lang_map[sel]
        st.rerun()

    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password", key="pw_input")
        if st.button("로그인", key="login_btn"):
            if pw == "0009":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃", key="logout_btn"):
            st.session_state.admin = False
            st.rerun()

        if st.button(_("change_pw"), key="show_change_pw_btn"):
            st.session_state.show_pw_form = not st.session_state.show_pw_form

        if st.session_state.get("show_pw_form", False):
            with st.form("change_pw_form"):
                current_pw = st.text_input(_("current_pw"), type="password", key="current_pw_input")
                new_pw = st.text_input(_("new_pw"), type="password", key="new_pw_input")
                confirm_pw = st.text_input(_("confirm_pw"), type="password", key="confirm_pw_input")
                if st.form_submit_button("변경", key="change_pw_submit"):
                    if current_pw == "0691":
                        if new_pw == confirm_pw and new_pw:
                            st.session_state.password = new_pw
                            st.success(_("pw_changed"))
                            st.session_state.show_pw_form = False
                            st.rerun()
                        else:
                            st.error(_("pw_mismatch"))
                    else:
                        st.error(_("pw_error"))

# --- 탭 전환 ---
if st.session_state.tab_selection != st.session_state.get("last_tab"):
    st.session_state.last_tab = st.session_state.tab_selection
    st.rerun()
