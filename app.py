import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, cos, sin, asin, sqrt

# 거리 계산 함수 (Haversine)
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))  # km

# 새로고침 (일반 사용자용)
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh")

# 기본 설정
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
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

# 언어 설정
LANG = {
    "ko": {
        "title_base": "칸타타 투어", "caption": "마하라스트라",
        "tab_notice": "공지", "tab_map": "투어 경로", "map_title": "경로 보기",
        "add_city": "도시 추가", "password": "비밀번호", "login": "로그인",
        "logout": "로그아웃", "wrong_pw": "비밀번호가 틀렸습니다.",
        "select_city": "도시 선택", "venue": "공연장소", "seats": "예상 인원",
        "note": "특이사항", "google_link": "구글맵 링크",
        "indoor": "실내", "outdoor": "실외", "register": "등록",
        "edit": "수정", "remove": "삭제", "date": "등록일",
        "performance_date": "공연 날짜", "cancel": "취소",
        "title_label": "제목", "content_label": "내용",
        "upload_image": "이미지 업로드", "upload_file": "파일 업로드",
        "submit": "등록", "warning": "제목과 내용을 모두 입력해주세요.",
        "file_download": "파일 다운로드"
    }
}
_ = lambda k: LANG[st.session_state.lang].get(k, k)

# === 크리스마스 밤 테마 + 전체화면 눈 효과 + 알림음 ===
st.markdown("""
<style>
.stApp {
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  color: #f0f0f0;
  font-family: 'Segoe UI', sans-serif;
  overflow: hidden;
  position: relative;
}
.christmas-title {
  text-align: center;
  margin: 20px 0;
}
.cantata {
  font-size: 3em;
  font-weight: bold;
  color: #e74c3c;
  text-shadow: 0 0 10px #ff6b6b;
}
.year {
  font-size: 2.8em;
  font-weight: bold;
  color: #ecf0f1;
  text-shadow: 0 0 8px #fff;
}
.maha {
  font-size: 1.8em;
  color: #3498db;
  font-style: italic;
  text-shadow: 0 0 6px #74b9ff;
}

/* 눈 효과 */
.snowflake {
  position: fixed;
  top: -10px;
  color: rgba(255, 255, 255, 0.8);
  user-select: none;
  pointer-events: none;
  font-size: 1.2em;
  z-index: 9999;
  animation: fall linear forwards;
}
@keyframes fall {
  to {
    transform: translateY(110vh);
    opacity: 0;
  }
}
</style>

<script>
function createSnowflake(){
  const s=document.createElement('div');
  s.classList.add('snowflake');
  s.innerText=['❅','❆','✻','✼'][Math.floor(Math.random()*4)];
  s.style.left=Math.random()*100+'vw';
  s.style.fontSize=(Math.random()*1.5+0.5)+'em';
  s.style.animationDuration=(Math.random()*8+6)+'s';
  s.style.opacity=Math.random()*0.6+0.3;
  document.body.appendChild(s);
  setTimeout(()=>s.remove(),14000);
}
setInterval(createSnowflake,200);

function playNotification(){
  const a=new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU'+Array(100).fill('A').join(''));
  a.play().catch(()=>{});
}
</script>
""", unsafe_allow_html=True)

# 타이틀
st.markdown(f"""
<div class="christmas-title">
  <div class="cantata">{_('title_base')}</div>
  <div class="year">2025</div>
  <div class="maha">{_('caption')}</div>
</div>
""", unsafe_allow_html=True)

# === 유틸 ===
def load_json(f): return json.load(open(f,encoding="utf-8")) if os.path.exists(f) else []
def save_json(f,d): json.dump(d,open(f,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

# === 공지 기능 ===
def add_notice(title, content, image=None, file=None):
    img=file_path=None
    if image: img=os.path.join(UPLOAD_DIR,f"{uuid.uuid4()}_{image.name}"); open(img,"wb").write(image.read())
    if file: file_path=os.path.join(UPLOAD_DIR,f"{uuid.uuid4()}_{file.name}"); open(file_path,"wb").write(file.read())
    new={"id":str(uuid.uuid4()),"title":title,"content":content,
         "date":datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
         "image":img,"file":file_path}
    data=load_json(NOTICE_FILE); data.insert(0,new); save_json(NOTICE_FILE,data)
    st.session_state.expanded={}; st.session_state.seen_notices=[]
    st.toast("새 공지가 등록되었습니다!")
    st.session_state.active_tab="notice"
    st.rerun()

def render_notice_list(show_delete=False):
    data=load_json(NOTICE_FILE)
    has_new=False
    for i,n in enumerate(data):
        nid=n["id"]
        is_new=nid not in st.session_state.seen_notices
        if is_new and not st.session_state.admin:
            has_new=True
        title=f"{n['date']} | {n['title']}"
        with st.expander(title):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"],use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                href=f'<a href="data:file/octet-stream;base64,{base64.b64encode(open(n["file"],"rb").read()).decode()}" download="{os.path.basename(n["file"])}">{_("file_download")}</a>'
                st.markdown(href,unsafe_allow_html=True)
            if show_delete and st.button(_("remove"),key=f"del_{i}"):
                data.pop(i); save_json(NOTICE_FILE,data); st.toast("삭제 완료"); st.rerun()
            if is_new:
                st.session_state.seen_notices.append(nid)
    if has_new and not st.session_state.get("sound_played",False):
        st.markdown('<script>playNotification();</script>',unsafe_allow_html=True)
        st.session_state.sound_played=True
        st.session_state.active_tab="notice"
        st.rerun()
    elif not has_new:
        st.session_state.sound_played=False

# === 지도 ===
def render_map():
    col1,col2=st.columns([5,2])
    with col1: st.subheader(_( "map_title" ))
    with col2:
        if st.session_state.admin and st.button(_( "add_city" ),use_container_width=True):
            st.session_state.adding_cities.append(None)
            st.rerun()
    st.markdown("여기에 지도 및 도시 관리 로직 (이전 코드 그대로 유지)")
    # (실제 지도 로직 생략 — 기존 코드 그대로 두세요.)

# === 탭 ===
tabs=[_( "tab_notice" ),_( "tab_map" )]
tab=st.session_state.active_tab
idx=0 if tab=="notice" else 1
selected=st.tabs([tabs[0],tabs[1]])

# 공지 탭
with selected[0]:
    if st.session_state.active_tab != "notice":
        st.session_state.active_tab = "notice"
        st.session_state.expanded = {}
    if st.session_state.admin:
        with st.form("notice_form",clear_on_submit=True):
            t=st.text_input(_( "title_label" ))
            c=st.text_area(_( "content_label" ))
            img=st.file_uploader(_( "upload_image" ),type=["png","jpg","jpeg"])
            f=st.file_uploader(_( "upload_file" ))
            if st.form_submit_button(_( "submit" )):
                if t.strip() and c.strip():
                    add_notice(t,c,img,f)
                else:
                    st.warning(_( "warning" ))
        render_notice_list(show_delete=True)
    else:
        render_notice_list(show_delete=False)

# 지도 탭
with selected[1]:
    if st.session_state.active_tab != "map":
        st.session_state.active_tab = "map"
        st.session_state.expanded = {}
    render_map()
