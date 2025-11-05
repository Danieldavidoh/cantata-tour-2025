# app.py
import streamlit as st
import json, os, uuid, base64, asyncio, threading, websockets
from datetime import datetime
from folium.plugins import AntPath
from streamlit_folium import st_folium
import folium

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
WS_URL = "ws://localhost:8765"  # WebSocket 서버 주소
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =============================================
# JSON 유틸
# =============================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_file_download_link(file_path, label):
    if not os.path.exists(file_path): return ""
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">{label}</a>'
    return href

# =============================================
# 다국어
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "caption": "마하라스트라 지역 투어 관리 시스템",
        "tab_notice": "공지 관리",
        "tab_map": "투어 경로",
        "title_label": "제목",
        "content_label": "내용",
        "upload_image": "이미지 업로드 (선택)",
        "upload_file": "파일 업로드 (선택)",
        "submit": "등록",
        "delete": "삭제",
        "warning": "제목과 내용을 모두 입력해주세요.",
        "notice_list": "공지 목록",
        "no_notice": "등록된 공지가 없습니다.",
        "map_title": "경로 보기",
        "admin_login": "관리자 로그인",
        "password": "비밀번호",
        "login": "로그인",
        "logout": "로그아웃",
        "wrong_pw": "비밀번호가 틀렸습니다.",
        "lang_select": "언어 선택",
        "file_download": "📎 파일 다운로드",
        "new_notice": "🔔 새 공지가 등록되었습니다!"
    }
}

_ = LANG["ko"]

# =============================================
# 세션 초기화
# =============================================
if "admin" not in st.session_state:
    st.session_state.admin = False
if "notice_data" not in st.session_state:
    st.session_state.notice_data = load_json(NOTICE_FILE)
if "new_notice_alert" not in st.session_state:
    st.session_state.new_notice_alert = False
if "ws_started" not in st.session_state:
    st.session_state.ws_started = False

# =============================================
# WebSocket Listener (실시간 수신)
# =============================================
async def listen_to_ws():
    try:
        async with websockets.connect(WS_URL) as ws:
            async for msg in ws:
                data = json.loads(msg)
                if data.get("type") == "notice_update":
                    st.session_state.new_notice_alert = True
                    st.session_state.notice_data = load_json(NOTICE_FILE)
                    st.experimental_rerun()
    except:
        pass

def start_ws_listener():
    asyncio.run(listen_to_ws())

if not st.session_state.ws_started:
    st.session_state.ws_started = True
    threading.Thread(target=start_ws_listener, daemon=True).start()

# =============================================
# 관리자 → WebSocket 서버에 알림 전송
# =============================================
async def send_ws_notice():
    try:
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({"type": "new_notice"}))
    except:
        pass

# =============================================
# 공지 추가 / 삭제
# =============================================
def add_notice(title, content, image_file=None, upload_file=None):
    img_path, file_path = None, None
    if image_file:
        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_file.name}")
        with open(img_path, "wb") as f: f.write(image_file.read())
    if upload_file:
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{upload_file.name}")
        with open(file_path, "wb") as f: f.write(upload_file.read())
    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "image": img_path,
        "file": file_path
    }
    notices = load_json(NOTICE_FILE)
    notices.insert(0, new_notice)
    save_json(NOTICE_FILE, notices)
    asyncio.run(send_ws_notice())
    st.success("📢 공지 등록 완료!")
    st.rerun()

def delete_notice(nid):
    notices = [n for n in load_json(NOTICE_FILE) if n["id"] != nid]
    save_json(NOTICE_FILE, notices)
    st.session_state.notice_data = notices
    asyncio.run(send_ws_notice())
    st.rerun()

# =============================================
# 공지 리스트 렌더링
# =============================================
def render_notice_list(admin=False):
    st.subheader(_["notice_list"])
    notices = st.session_state.notice_data
    if not notices:
        st.info(_["no_notice"]); return
    for idx, n in enumerate(notices):
        with st.expander(f"📅 {n.get('date')} | {n.get('title')}"):
            st.markdown(n.get("content", ""))
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                st.markdown(get_file_download_link(n["file"], _["file_download"]), unsafe_allow_html=True)
            if admin:
                if st.button(_["delete"], key=f"del_{n['id']}_{idx}"):
                    delete_notice(n["id"])

# =============================================
# 지도
# =============================================
def render_map():
    st.subheader(_["map_title"])
    cities = [
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Nashik", "lat": 19.9975, "lon": 73.7898},
    ]
    m = folium.Map(location=[19.0, 73.0], zoom_start=7)
    coords = [(c["lat"], c["lon"]) for c in cities]
    for c in cities:
        folium.Marker([c["lat"], c["lon"]], popup=c["name"], tooltip=c["name"], icon=folium.Icon(color="red", icon="music")).add_to(m)
    AntPath(coords, color="#ff1744", weight=5, delay=800).add_to(m)
    st_folium(m, width=900, height=550)

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    st.markdown("### 관리자 로그인")
    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0000":
                st.session_state.admin = True
                st.success("관리자 모드 ON")
                st.rerun()
            else:
                st.error(_["wrong_pw"])
    else:
        st.success("관리자 모드")
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 헤더 + 알림
# =============================================
st.markdown(f"# {_['title']} 🎵")
st.caption(_["caption"])

if st.session_state.new_notice_alert:
    st.toast(_["new_notice"], icon="📢")
    st.session_state.new_notice_alert = False

# =============================================
# 탭
# =============================================
tab1, tab2 = st.tabs([_["tab_notice"], _["tab_map"]])

with tab1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_["title_label"])
            c = st.text_area(_["content_label"])
            img = st.file_uploader(_["upload_image"], type=["png", "jpg", "jpeg"])
            f = st.file_uploader(_["upload_file"])
            if st.form_submit_button(_["submit"]):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_["warning"])
        render_notice_list(admin=True)
    else:
        render_notice_list(admin=False)

with tab2:
    render_map()
