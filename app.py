import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, cos, sin, asin, sqrt

# 거리 계산 함수
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))

# 새로고침
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh")

# 기본 설정
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 세션 초기값
defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "expanded": {},
    "adding_cities": [], "pw": "0009", "seen_notices": [],
    "active_tab": "notice"
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# 언어
LANG = {
    "ko": {"title_base": "칸타타 투어", "caption": "마하라스트라",
           "tab_notice": "공지", "tab_map": "투어 경로",
           "map_title": "경로 보기", "add_city": "도시 추가",
           "password": "비밀번호", "login": "로그인",
           "logout": "로그아웃", "wrong_pw": "비밀번호가 틀렸습니다.",
           "title_label": "제목", "content_label": "내용",
           "upload_image": "이미지 업로드", "upload_file": "파일 업로드",
           "submit": "등록", "warning": "제목과 내용을 모두 입력해주세요.",
           "file_download": "파일 다운로드"}
}
_ = lambda k: LANG[st.session_state.lang].get(k, k)

# === 크리스마스 테마 + 눈 효과 ===
st.markdown("""
<style>
.stApp {
  background: radial-gradient(circle at top, #2c3e50 0%, #1c1c2b 100%);
  color: #f8f8f8;
  font-family: 'Segoe UI', sans-serif;
  position: relative;
  overflow: hidden;
}
h1, h2, h3, h4, h5, h6, p, div, span, label {
  color: #f0f0f0 !important;
}
.stButton > button {
  background-color: #e74c3c !important;
  color: white !important;
  border: none !important;
  border-radius: 10px;
  padding: 0.4em 1em;
  transition: 0.2s;
}
.stButton > button:hover {
  background-color: #ff6b6b !important;
}
.snowflake {
  position: fixed;
  top: -10px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 1em;
  pointer-events: none;
  animation: fall linear forwards;
  z-index: 9999;
}
@keyframes fall {
  to { transform: translateY(110vh); opacity: 0; }
}
</style>
<script>
function createSnowflake(){
  const s=document.createElement('div');
  s.classList.add('snowflake');
  s.innerText=['❅','❆','✻','✼'][Math.floor(Math.random()*4)];
  s.style.left=Math.random()*100+'vw';
  s.style.fontSize=(Math.random()*1.5+0.5)+'em';
  s.style.animationDuration=(Math.random()*10+8)+'s';
  s.style.opacity=Math.random()*0.8+0.2;
  document.body.appendChild(s);
  setTimeout(()=>s.remove(),15000);
}
setInterval(createSnowflake,200);

function playNotification(){
  const a=new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU'+Array(100).fill('A').join(''));
  a.play().catch(()=>{});
}
</script>
""", unsafe_allow_html=True)

# === 상단 헤더: 제목 + 언어선택 + 관리자 버튼 ===
colA, colB, colC = st.columns([2, 1, 1])
with colA:
    st.markdown(f"<h2 style='margin-top:0;'>🎄 {_('title_base')} 2025 🎶</h2>", unsafe_allow_html=True)
with colB:
    lang_sel = st.selectbox("Language", ["ko"], index=["ko"].index(st.session_state.lang))
    st.session_state.lang = lang_sel
with colC:
    if st.session_state.admin:
        if st.button(_("logout")):
            st.session_state.admin = False
            st.toast("관리자 모드 해제됨")
            st.rerun()
    else:
        pw = st.text_input(_("password"), type="password")
        if st.button(_("login")):
            if pw == st.session_state.pw:
                st.session_state.admin = True
                st.toast("관리자 모드 진입")
                st.rerun()
            else:
                st.warning(_("wrong_pw"))

# === 유틸 ===
def load_json(f): return json.load(open(f,encoding="utf-8")) if os.path.exists(f) else []
def save_json(f,d): json.dump(d,open(f,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

# === 공지 ===
def add_notice(title, content, image=None, file=None):
    img=file_path=None
    if image:
        img=os.path.join(UPLOAD_DIR,f"{uuid.uuid4()}_{image.name}")
        open(img,"wb").write(image.read())
    if file:
        file_path=os.path.join(UPLOAD_DIR,f"{uuid.uuid4()}_{file.name}")
        open(file_path,"wb").write(file.read())
    new={"id":str(uuid.uuid4()),"title":title,"content":content,
         "date":datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
         "image":img,"file":file_path}
    data=load_json(NOTICE_FILE); data.insert(0,new); save_json(NOTICE_FILE,data)
    st.session_state.expanded={}
    st.session_state.active_tab="notice"
    st.toast("새 공지 등록 완료!")
    st.rerun()

def render_notice_list():
    data=load_json(NOTICE_FILE)
    for i,n in enumerate(data):
        with st.expander(f"{n['date']} | {n['title']}"):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                href=f'<a href="data:file/octet-stream;base64,{base64.b64encode(open(n["file"],"rb").read()).decode()}" download="{os.path.basename(n["file"])}">{_("file_download")}</a>'
                st.markdown(href, unsafe_allow_html=True)

# === 지도 ===
def render_map():
    st.subheader(_("map_title"))
    st.write("여기에 지도 표시 (기존 기능 유지)")
    # 기존 folium 지도 로직 넣으면 됩니다.

# === 탭 ===
tabs = [ _("tab_notice"), _("tab_map") ]
selected_tab = st.tabs(tabs)

with selected_tab[0]:
    if st.session_state.active_tab != "notice":
        st.session_state.expanded = {}
        st.session_state.active_tab = "notice"
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_("title_label"))
            c = st.text_area(_("content_label"))
            img = st.file_uploader(_("upload_image"), type=["png","jpg","jpeg"])
            f = st.file_uploader(_("upload_file"))
            if st.form_submit_button(_("submit")):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_("warning"))
    render_notice_list()

with selected_tab[1]:
    if st.session_state.active_tab != "map":
        st.session_state.expanded = {}
        st.session_state.active_tab = "map"
    render_map()
