import json, os, uuid, base64, random
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh

# ────────────────────────────── 1. 페이지 설정 ──────────────────────────────
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

# ────────────────────────────── 2. 파일 ──────────────────────────────
NOTICE_FILE = "notice.json"
CITY_FILE   = "cities.json"
UPLOAD_DIR  = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ────────────────────────────── 3. 다국어 ──────────────────────────────
LANG = {
    "ko": { "title_cantata":"칸타타 투어","title_year":"2025","title_region":"마하라스트라",
            "tab_notice":"공지","tab_map":"투어 경로","today":"오늘","yesterday":"어제",
            "new_notice_alert":"새 공지가 도착했어요!","warning":"제목·내용 입력",
            "edit":"수정","save":"입력","cancel":"취소","add_city":"도시 추가",
            "indoor":"실내","outdoor":"실외","venue":"공연 장소","seats":"예상 인원",
            "note":"특이사항","google_link":"구글맵","perf_date":"공연 날짜",
            "change_pw":"비밀번호 변경","current_pw":"현재 비밀번호","new_pw":"새 비밀번호",
            "confirm_pw":"새 비밀번호 확인","pw_changed":"비밀번호 변경 완료!","pw_mismatch":"비밀번호 불일치",
            "pw_error":"현재 비밀번호 오류","menu":"메뉴","login":"로그인","logout":"로그아웃","delete":"제거"},
    "en": { "title_cantata":"Cantata Tour","title_year":"2025","title_region":"Maharashtra",
            "tab_notice":"Notice","tab_map":"Tour Route", ... },   # (생략)
    "hi": { "title_cantata":"कैंटाटा टूर","title_year":"2025","title_region":"महाराष्ट्र", ... }   # (생략)
}
# ────────────────────────────── 4. 세션 상태 ──────────────────────────────
defaults = {"admin":False,"lang":"ko","notice_open":False,"map_open":False,"adding_city":False}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# ────────────────────────────── 5. JSON 헬퍼 ──────────────────────────────
def load_json(f): return json.load(open(f,"r",encoding="utf-8")) if os.path.exists(f) else []
def save_json(f,d): json.dump(d,open(f,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

# ────────────────────────────── 6. 초기 도시 ──────────────────────────────
DEFAULT_CITIES = [ ... ]   # 기존 코드 그대로
if not os.path.exists(CITY_FILE): save_json(CITY_FILE, DEFAULT_CITIES)
CITY_COORDS = {"Mumbai":(19.0760,72.8777),"Pune":(18.5204,73.8567),"Nagpur":(21.1458,79.0882)}

# ────────────────────────────── 7. CSS (핵심) ──────────────────────────────
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
    /* 배경 & 기본 */
    [data-testid="stAppViewContainer"]{
        background:url("background_christmas_dark.png") center/cover fixed;
        padding-top:0 !important; margin:0 !important;
    }
    /* 제목 (상단 1/3) */
    .fixed-title{
        position:fixed; top:20vh; left:0; width:100%; z-index:1000;
        text-align:center; padding:0; margin:0;
    }
    .main-title{
        font-size:2.8em !important; font-weight:bold;
        text-shadow:0 3px 8px rgba(0,0,0,0.6);
        margin:0 !important; line-height:1.2;
    }
    /* 버튼 바 (제목 바로 아래 고정) */
    .button-bar{
        position:fixed; top:32vh; left:0; width:100%; z-index:1000;
        display:flex; justify-content:center; gap:30px;
        padding:12px 0; background:transparent;
    }
    .tab-btn{
        background:rgba(255,255,255,0.94); color:#333;
        border:none; border-radius:50px; padding:14px 28px;
        font-weight:bold; font-size:1.1em; cursor:pointer;
        box-shadow:0 6px 20px rgba(0,0,0,0.2);
        display:flex; align-items:center; gap:8px;
        min-width:160px; justify-content:center;
    }
    .tab-btn:hover{ background:#f1c40f; color:#fff; }
    .tab-btn i{ font-size:1.3em; }

    /* 콘텐츠 영역 (버튼 클릭 전 숨김) */
    .content-area{ margin-top:48vh !important; visibility:hidden; opacity:0; transition:all .4s; }
    .content-area.show{ visibility:visible; opacity:1; }

    /* 눈송이 */
    .snowflake{position:fixed;top:-15px;color:#fff;font-size:1.1em;pointer-events:none;
               animation:fall linear infinite;opacity:.3;z-index:1;}
    @keyframes fall{0%{transform:translateY(0) rotate(0deg);}
                    100%{transform:translateY(120vh) rotate(360deg);}}

    /* 모바일 햄버거 */
    .hamburger{position:fixed;top:15px;left:15px;z-index:10000;
               background:rgba(0,0,0,.6);color:#fff;border:none;
               border-radius:50%;width:50px;height:50px;font-size:24px;
               cursor:pointer;box-shadow:0 0 10px rgba(0,0,0,.3);}
    .sidebar-mobile{position:fixed;top:0;left:-300px;width:280px;height:100vh;
                    background:rgba(30,30,30,.95);color:#fff;padding:20px;
                    transition:left .3s;z-index:9999;overflow-y:auto;}
    .sidebar-mobile.open{left:0;}
    .overlay{position:fixed;top:0;left:0;width:100vw;height:100vh;
             background:rgba(0,0,0,.5);z-index:9998;display:none;}
    .overlay.open{display:block;}
    @media(min-width:769px){
        .hamburger,.sidebar-mobile,.overlay{display:none !important;}
        section[data-testid="stSidebar"]{display:block !important;}
    }
    .stButton>button{border:none !important;-webkit-appearance:none !important;}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────── 눈송이 (26개) ──────────────────────────────
for i in range(26):
    left = random.randint(0,100)
    dur  = random.randint(10,20)
    size = random.uniform(.8,1.4)
    delay= random.uniform(0,10)
    st.markdown(
        f"<div class='snowflake' style='left:{left}vw;animation-duration:{dur}s;"
        f"font-size:{size}em;animation-delay:{delay}s;'>❄</div>",
        unsafe_allow_html=True)

# ────────────────────────────── 제목 ──────────────────────────────
st.markdown('<div class="fixed-title">', unsafe_allow_html=True)
title_html = f'<span style="color:red;">{_("title_cantata")}</span> ' \
             f'<span style="color:white;">{_("title_year")}</span> ' \
             f'<span style="color:green;font-size:67%;">{_("title_region")}</span>'
st.markdown(f'<h1 class="main-title">{title_html}</h1>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ────────────────────────────── 버튼 바 (고정) ──────────────────────────────
st.markdown('<div class="button-bar">', unsafe_allow_html=True)

col_btn1, col_btn2 = st.columns([1,1], gap="large")
with col_btn1:
    if st.button(
        f"**{_('tab_notice')}**   <i class='fa-solid fa-bullhorn'></i>",
        key="notice_toggle_btn", use_container_width=True,
        help="공지사항 보기"
    ):
        st.session_state.notice_open = True
        st.session_state.map_open    = False
        st.rerun()
with col_btn2:
    if st.button(
        f"**{_('tab_map')}**   <i class='fa-solid fa-route'></i>",
        key="map_toggle_btn", use_container_width=True,
        help="투어 경로 보기"
    ):
        st.session_state.map_open    = True
        st.session_state.notice_open = False
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ────────────────────────────── 콘텐츠 영역 (초기 숨김) ──────────────────────────────
content_class = "content-area"
if st.session_state.notice_open or st.session_state.map_open:
    content_class += " show"

st.markdown(f'<div class="{content_class}">', unsafe_allow_html=True)

# ────────────────────────────── ① 공지 ──────────────────────────────
if st.session_state.notice_open:
    # (기존 공지 코드 그대로 복사)
    # ... (admin 작성, 목록, 삭제 등)
    pass   # ← 여기엔 기존 공지 코드를 그대로 붙여넣으세요

# ────────────────────────────── ② 투어 경로 ──────────────────────────────
if st.session_state.map_open:
    # (기존 지도·도시 추가 코드 그대로 복사)
    # ... (admin 도시 추가, folium 지도 등)
    pass   # ← 여기엔 기존 map 코드를 그대로 붙여넣으세요

st.markdown('</div>', unsafe_allow_html=True)

# ────────────────────────────── 모바일 햄버거 메뉴 (그대로) ──────────────────────────────
st.markdown(f'''
<button class="hamburger" onclick="document.querySelector('.sidebar-mobile').classList.toggle('open');
                                 document.querySelector('.overlay').classList.toggle('open');">☰</button>
<div class="overlay" onclick="document.querySelector('.sidebar-mobile').classList.remove('open');
                           this.classList.remove('open');"></div>
<div class="sidebar-mobile">
    <h3 style="color:white;">{_("menu")}</h3>
    <select onchange="window.location.href='?lang='+this.value" style="width:100%;padding:8px;margin:10px 0;">
        <option value="ko" {'selected' if st.session_state.lang=="ko" else ''}>한국어</option>
        <option value="en" {'selected' if st.session_state.lang=="en" else ''}>English</option>
        <option value="hi" {'selected' if st.session_state.lang=="hi" else ''}>हिंदी</option>
    </select>
    {'''
        <input type="password" placeholder="비밀번호" id="mobile_pw" style="width:100%;padding:8px;margin:10px 0;">
        <button onclick="if(document.getElementById(\'mobile_pw\').value==\'0009\')
                         window.location.href=\'?admin=true\'; else alert(\'비밀번호 오류\');"
                style="width:100%;padding:10px;background:#e74c3c;color:white;border:none;border-radius:8px;">
            {_("login")}
        </button>
    ''' if not st.session_state.admin else f'''
        <button onclick="window.location.href=\'?admin=false\'"
                style="width:100%;padding:10px;background:#27ae60;color:white;border:none;
                       border-radius:8px;margin:10px 0;">{_("logout")}</button>
    ''' }
</div>
''', unsafe_allow_html=True)

# ────────────────────────────── 사이드바 (PC) ──────────────────────────────
with st.sidebar:
    lang_map = {"한국어":"ko","English":"en","हिंदी":"hi"}
    sel = st.selectbox("언어", list(lang_map.keys()),
                       index=list(lang_map.values()).index(st.session_state.lang))
    if lang_map[sel] != st.session_state.lang:
        st.session_state.lang = lang_map[sel]; st.rerun()

    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password", key="pw_input")
        if st.button("로그인", key="login_btn"):
            if pw == "0009":
                st.session_state.admin = True; st.rerun()
            else: st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃", key="logout_btn"):
            st.session_state.admin = False; st.rerun()
        # 비밀번호 변경 폼 등 (기존 코드 그대로)
