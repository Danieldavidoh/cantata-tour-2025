import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, cos, sin, asin, sqrt

# -------------------------------
# 기본 설정 및 새로고침
# -------------------------------
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh")

st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------------------------------
# 세션 초기화
# -------------------------------
defaults = {
    "admin": False, "lang": "ko", "edit_city": None,
    "expanded": {}, "adding_cities": [], "pw": "0009",
    "seen_notices": [], "active_tab": "notice"
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------------------
# 다국어
# -------------------------------
LANG = {
    "ko": {"title_base": "칸타타 투어", "caption": "마하라스트라", "tab_notice": "공지", "tab_map": "투어 경로",
           "map_title": "경로 보기", "add_city": "도시 추가", "password": "비밀번호", "login": "로그인",
           "logout": "로그아웃", "wrong_pw": "비밀번호가 틀렸습니다.", "select_city": "도시 선택",
           "venue": "공연장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵 링크",
           "indoor": "실내", "outdoor": "실외", "register": "등록", "edit": "수정", "remove": "삭제",
           "date": "등록일", "performance_date": "공연 날짜", "cancel": "취소", "title_label": "제목",
           "content_label": "내용", "upload_image": "이미지 업로드", "upload_file": "파일 업로드",
           "submit": "등록", "warning": "제목과 내용을 모두 입력해주세요.", "file_download": "파일 다운로드",
           "change_pw": "비밀번호 변경", "new_pw": "새 비밀번호", "confirm_pw": "비밀번호 확인",
           "pw_changed": "비밀번호가 변경되었습니다.", "pw_mismatch": "비밀번호가 일치하지 않습니다."}
}
_ = lambda k: LANG[st.session_state.lang].get(k, k)

# -------------------------------
# 배경 + 눈 효과 (z-index 수정)
# -------------------------------
christmas_night = """
<style>
.stApp { 
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  color: #f0f0f0; font-family: 'Segoe UI', sans-serif; overflow: hidden;
}
.christmas-title { text-align: center; margin: 20px 0; position: relative; z-index: 10; }
.cantata { font-size: 3em; font-weight: bold; color: #e74c3c; text-shadow: 0 0 10px #ff6b6b; }
.year { font-size: 2.8em; font-weight: bold; color: #ecf0f1; text-shadow: 0 0 8px #ffffff; }
.maha { font-size: 1.8em; color: #3498db; font-style: italic; text-shadow: 0 0 6px #74b9ff; }

.floating-icons { position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none; z-index: -1; opacity: 0.5; }
.icon { position: absolute; font-size: 2em; animation: float 6s infinite ease-in-out, spin 8s infinite linear; }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-20px)} }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

.snowflake { color: rgba(255, 255, 255, 0.6); font-size: 1.2em;
  position: fixed; top: -10px; animation: fall linear forwards;
  user-select: none; pointer-events: none; z-index: -1; }
@keyframes fall { to { transform: translateY(100vh); opacity: 0; } }
</style>

<div class="floating-icons">
  <div class="icon" style="top:10%; left:10%;">🎄</div>
  <div class="icon" style="top:15%; left:80%;">🎁</div>
  <div class="icon" style="top:70%; left:15%;">🍭</div>
  <div class="icon" style="top:60%; left:75%;">🧦</div>
  <div class="icon" style="top:30%; left:60%;">🦌</div>
  <div class="icon" style="top:40%; left:20%;">🎅</div>
</div>

<script>
function createSnowflake() {
  const snow = document.createElement('div');
  snow.classList.add('snowflake');
  snow.innerText = ['❅','❆','✻','✼'][Math.floor(Math.random()*4)];
  snow.style.left = Math.random()*100+'vw';
  snow.style.animationDuration = (Math.random()*10+8)+'s';
  snow.style.opacity = Math.random()*0.5+0.3;
  snow.style.fontSize = (Math.random()*1.2+0.8)+'em';
  document.body.appendChild(snow);
  setTimeout(()=>snow.remove(),18000);
}
setInterval(createSnowflake, 400);
</script>
"""
st.markdown(christmas_night, unsafe_allow_html=True)

# -------------------------------
# 제목
# -------------------------------
st.markdown(
    f"""<div class='christmas-title'>
         <div class='cantata'>{_('title_base')}</div>
         <div class='year'>2025</div>
         <div class='maha'>{_('caption')}</div>
       </div>""",
    unsafe_allow_html=True
)

# -------------------------------
# 사이드바 (언어/관리자)
# -------------------------------
with st.sidebar:
    st.markdown("### 🌐 언어 선택")
    lang = st.radio("", ["한국어"], index=0)
    st.session_state.lang = "ko"

    st.markdown("---")
    if not st.session_state.admin:
        st.markdown("### 🎅 관리자 로그인")
        pw = st.text_input(_("password"), type="password")
        if st.button(_("login")):
            if pw == st.session_state.pw:
                st.session_state.admin = True
                st.rerun()
            else:
                st.error(_("wrong_pw"))
    else:
        st.success("🎄 관리자 모드")
        if st.button(_("logout")):
            st.session_state.admin = False
            st.rerun()

# -------------------------------
# JSON 유틸
# -------------------------------
def load_json(f):
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as x: return json.load(x)
    return []
def save_json(f, d):
    with open(f, "w", encoding="utf-8") as x: json.dump(d, x, ensure_ascii=False, indent=2)

# -------------------------------
# 공지 탭
# -------------------------------
def render_notice():
    st.subheader(f"🎁 {_('tab_notice')}")
    data = load_json(NOTICE_FILE)
    for n in data:
        with st.expander(f"{n['date']} | {n['title']}"):
            st.write(n["content"])

# -------------------------------
# 지도 탭
# -------------------------------
def render_map():
    st.subheader(f"🗺️ {_('tab_map')}")
    m = folium.Map(location=[19.0, 73.0], zoom_start=6)
    st_folium(m, width=900, height=550)

# -------------------------------
# 탭 이동 시 상태 초기화
# -------------------------------
tab1, tab2 = st.tabs([f"🎁 {_('tab_notice')}", f"🗺️ {_('tab_map')}"])
with tab1:
    if st.session_state.active_tab != "notice":
        st.session_state.expanded = {}
        st.session_state.adding_cities = []
        st.session_state.active_tab = "notice"
    render_notice()

with tab2:
    if st.session_state.active_tab != "map":
        st.session_state.expanded = {}
        st.session_state.adding_cities = []
        st.session_state.active_tab = "map"
    render_map()
