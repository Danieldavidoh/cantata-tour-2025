# app.py
import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json
import os
import uuid
import base64
import pytz

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =============================================
# 세션 초기화
# =============================================
if "admin" not in st.session_state:
    st.session_state.admin = False
if "lang" not in st.session_state:
    st.session_state.lang = "ko"
if "last_notice_count" not in st.session_state:
    st.session_state.last_notice_count = 0

# =============================================
# 다국어
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "caption": "마하라스트라 지역 투어 관리 시스템",
        "tab_notice": "공지 관리",
        "tab_map": "투어 경로",
        "add_notice": "새 공지 추가",
        "title_label": "제목",
        "content_label": "내용",
        "upload_image": "이미지 업로드 (선택)",
        "upload_file": "파일 업로드 (선택)",
        "submit": "등록",
        "warning": "제목과 내용을 모두 입력해주세요.",
        "notice_list": "공지 목록",
        "no_notice": "등록된 공지가 없습니다.",
        "delete": "삭제",
        "map_title": "경로 보기",
        "admin_login": "관리자 로그인",
        "password": "비밀번호",
        "login": "로그인",
        "logout": "로그아웃",
        "wrong_pw": "비밀번호가 틀렸습니다.",
        "lang_select": "언어 선택",
        "file_download": "파일 다운로드",
        "add_city": "도시 추가",
        "city_name": "도시 이름",
        "latitude": "위도",
        "longitude": "경도",
        "city_added": "도시가 추가되었습니다."
    },
}

_ = LANG[st.session_state.lang]

# =============================================
# JSON 유틸
# =============================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_file_download_link(file_path, label):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">{label}</a>'

# =============================================
# 공지 추가/삭제
# =============================================
def add_notice(title, content, image_file=None, upload_file=None):
    img_path, file_path = None, None

    if image_file:
        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_file.name}")
        with open(img_path, "wb") as f:
            f.write(image_file.read())

    if upload_file:
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{upload_file.name}")
        with open(file_path, "wb") as f:
            f.write(upload_file.read())

    # 뭄바이 기준 시각으로 저장 (년도 제외)
    india = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india)
    formatted_time = now.strftime("%m/%d %H:%M")

    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": formatted_time,
        "image": img_path,
        "file": file_path
    }

    data = load_json(NOTICE_FILE)
    data.insert(0, new_notice)
    save_json(NOTICE_FILE, data)

    st.toast("공지가 등록되었습니다.")
    st.rerun()

def delete_notice(notice_id):
    data = load_json(NOTICE_FILE)
    for n in data:
        if n["id"] == notice_id:
            if n.get("image") and os.path.exists(n["image"]):
                os.remove(n["image"])
            if n.get("file") and os.path.exists(n["file"]):
                os.remove(n["file"])
    data = [n for n in data if n["id"] != notice_id]
    save_json(NOTICE_FILE, data)
    st.toast("공지가 삭제되었습니다.")
    st.rerun()

# =============================================
# 공지 리스트
# =============================================
def render_notice_list(show_delete=False):
    data = load_json(NOTICE_FILE)
    if not data:
        st.info(_["no_notice"])
        return
    for idx, n in enumerate(data):
        with st.expander(f"{n['date']} | {n['title']}"):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                st.markdown(get_file_download_link(n["file"], _["file_download"]), unsafe_allow_html=True)
            if show_delete:
                if st.button(_["delete"], key=f"del_{n['id']}_{idx}"):
                    delete_notice(n["id"])

# =============================================
# 지도 + 도시 추가 기능 복구
# =============================================
def render_map():
    st.subheader(_["map_title"])
    cities = load_json(CITY_FILE)

    # 기본 도시
    if not cities:
        cities = [
            {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
            {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
            {"name": "Nashik", "lat": 19.9975, "lon": 73.7898},
        ]
        save_json(CITY_FILE, cities)

    m = folium.Map(location=[19.0, 73.0], zoom_start=7)
    coords = [(c["lat"], c["lon"]) for c in cities]
    for c in cities:
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=c["name"],
            tooltip=c["name"],
            icon=folium.Icon(color="red", icon="music")
        ).add_to(m)

    if len(coords) > 1:
        AntPath(coords, color="#ff1744", weight=5, delay=800).add_to(m)

    st_folium(m, width=900, height=550)

    # 관리자 모드에서 도시 추가 (복구!)
    if st.session_state.admin:
        st.markdown("### " + _("add_city"))
        with st.form("add_city_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(_("city_name"))
            with col2:
                lat = st.number_input(_("latitude"), step=0.0001, format="%.6f")
            lon = st.number_input(_("longitude"), step=0.0001, format="%.6f")
            submitted = st.form_submit_button("추가")
            if submitted and name.strip():
                cities.append({"name": name, "lat": lat, "lon": lon})
                save_json(CITY_FILE, cities)
                st.toast(_("city_added"))
                st.rerun()

# =============================================
# 자동 새로고침 (3초마다) + 알림
# =============================================
if not st.session_state.admin:
    count = len(load_json(NOTICE_FILE))
    if st.session_state.last_notice_count == 0:
        st.session_state.last_notice_count = count

    # 3초마다 자동 갱신
    st_autorefresh(interval=3 * 1000, key="auto_refresh")

    new_count = len(load_json(NOTICE_FILE))
    if new_count > st.session_state.last_notice_count:
        st.toast("새 공지가 등록되었습니다!")
        st.audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg", format="audio/ogg")
        st.session_state.last_notice_count = new_count

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    st.markdown("### " + _("lang_select"))
    new_lang = st.selectbox("", ["ko"], index=0)
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")

    if not st.session_state.admin:
        st.markdown("### " + _("admin_login"))
        pw = st.text_input(_("password"), type="password")
        if st.button(_("login")):
            if pw == "0000":
                st.session_state.admin = True
                st.success("관리자 모드 ON")
                st.rerun()
            else:
                st.error(_("wrong_pw"))
    else:
        st.success("관리자 모드")
        if st.button(_("logout")):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 메인
# =============================================
st.markdown(f"# {_['title']} ")
st.caption(_["caption"])

tab1, tab2 = st.tabs([_["tab_notice"], _["tab_map"]])

with tab1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_("title_label"))
            c = st.text_area(_("content_label"))
            img = st.file_uploader(_("upload_image"), type=["png", "jpg", "jpeg"])
            f = st.file_uploader(_("upload_file"))
            if st.form_submit_button(_("submit")):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_("warning"))
        render_notice_list(show_delete=True)
    else:
        render_notice_list(show_delete=False)
        if st.button("새로고침"):
            st.rerun()

with tab2:
    render_map()
