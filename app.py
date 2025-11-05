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

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =============================================
# 유틸 함수
# =============================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for n in data:
                    n.setdefault("id", str(uuid.uuid4()))
                    n.setdefault("title", "(제목 없음)")
                    n.setdefault("content", "")
                    n.setdefault("date", datetime.now().strftime("%Y-%m-%d %H:%M"))
                return data
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
    href = f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">{label}</a>'
    return href

# =============================================
# 다국어 사전 (힌디어 포함)
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
        "delete_confirm": "정말 이 공지를 삭제하시겠습니까?",
        "confirm_yes": "예, 삭제합니다",
        "confirm_no": "취소",
        "map_title": "경로 보기",
        "admin_login": "관리자 로그인",
        "password": "비밀번호",
        "login": "로그인",
        "logout": "로그아웃",
        "wrong_pw": "비밀번호가 틀렸습니다.",
        "lang_select": "언어 선택",
        "file_download": "파일 다운로드",
        "new_notice_alert": "새 공지가 도착했습니다!"
    },
    "en": {
        "title": "Cantata Tour 2025",
        "caption": "Maharashtra Tour Management System",
        "tab_notice": "Notice Board",
        "tab_map": "Tour Route",
        "add_notice": "Add New Notice",
        "title_label": "Title",
        "content_label": "Content",
        "upload_image": "Upload Image (optional)",
        "upload_file": "Upload File (optional)",
        "submit": "Submit",
        "warning": "Please enter both title and content.",
        "notice_list": "Notice List",
        "no_notice": "No notices available.",
        "delete": "Delete",
        "delete_confirm": "Are you sure you want to delete this notice?",
        "confirm_yes": "Yes, delete",
        "confirm_no": "Cancel",
        "map_title": "View Route",
        "admin_login": "Admin Login",
        "password": "Password",
        "login": "Login",
        "logout": "Logout",
        "wrong_pw": "Incorrect password.",
        "lang_select": "Language",
        "file_download": "Download File",
        "new_notice_alert": "New notice posted!"
    },
    "hi": {
        "title": "कांताता टूर 2025",
        "caption": "महाराष्ट्र टूर मैनेजमेंट सिस्टम",
        "tab_notice": "सूचना बोर्ड",
        "tab_map": "टूर रूट",
        "add_notice": "नई सूचना जोड़ें",
        "title_label": "शीर्षक",
        "content_label": "सामग्री",
        "upload_image": "छवि अपलोड करें (वैकल्पिक)",
        "upload_file": "फ़ाइल अपलोड करें (वैकल्पिक)",
        "submit": "जमा करें",
        "warning": "कृपया शीर्षक और सामग्री दोनों भरें।",
        "notice_list": "सूचना सूची",
        "no_notice": "कोई सूचना उपलब्ध नहीं।",
        "delete": "हटाएं",
        "delete_confirm": "क्या आप वाकई इस सूचना को हटाना चाहते हैं?",
        "confirm_yes": "हाँ, हटाएं",
        "confirm_no": "रद्द करें",
        "map_title": "रूट देखें",
        "admin_login": "एडमिन लॉगिन",
        "password": "पासवर्ड",
        "login": "लॉगिन",
        "logout": "लॉगआउट",
        "wrong_pw": "गलत पासवर्ड।",
        "lang_select": "भाषा",
        "file_download": "फ़ाइल डाउनलोड करें",
        "new_notice_alert": "नई सूचना पोस्ट की गई!"
    }
}

# =============================================
# 세션 초기화
# =============================================
if "admin" not in st.session_state:
    st.session_state.admin = False
if "lang" not in st.session_state:
    st.session_state.lang = "ko"
if "notice_data" not in st.session_state:
    st.session_state.notice_data = load_json(NOTICE_FILE)
if "delete_target" not in st.session_state:
    st.session_state.delete_target = None
if "last_notice_count" not in st.session_state:
    st.session_state.last_notice_count = len(st.session_state.notice_data)
if "last_check_time" not in st.session_state:
    st.session_state.last_check_time = datetime.now()

# =============================================
# 번역 함수 정의
# =============================================
def _(key):
    return LANG[st.session_state.lang].get(key, key)

# =============================================
# 공지 관리
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

    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "image": img_path,
        "file": file_path
    }

    st.session_state.notice_data.insert(0, new_notice)
    save_json(NOTICE_FILE, st.session_state.notice_data)
    st.session_state.last_notice_count = len(st.session_state.notice_data)
    st.rerun()

def delete_notice(notice_id):
    st.session_state.notice_data = [n for n in st.session_state.notice_data if n.get("id") != notice_id]
    save_json(NOTICE_FILE, st.session_state.notice_data)
    st.session_state.delete_target = None
    st.rerun()

def render_notice_list():
    st.subheader(_("notice_list"))

    if not st.session_state.notice_data:
        st.info(_("no_notice"))
        return

    for idx, n in enumerate(st.session_state.notice_data):
        title = n.get("title", "(제목 없음)")
        date = n.get("date", "?")
        content = n.get("content", "")
        nid = n.get("id", str(uuid.uuid4()))

        with st.expander(f"{date} | {title}"):
            st.markdown(content)

            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)

            if n.get("file") and os.path.exists(n["file"]):
                st.markdown(get_file_download_link(n["file"], _("file_download")), unsafe_allow_html=True)

            if st.session_state.admin:
                if st.button(f"{_('delete')}", key=f"del_{nid}_{idx}"):
                    st.session_state.delete_target = nid

    if st.session_state.delete_target:
        st.warning(_("delete_confirm"))
        col1, col2 = st.columns(2)
        with col1:
            if st.button(_("confirm_yes"), key="yes_delete"):
                delete_notice(st.session_state.delete_target)
        with col2:
            if st.button(_("confirm_no"), key="cancel_delete"):
                st.session_state.delete_target = None
                st.rerun()

# =============================================
# 지도 (모바일 최적화)
# =============================================
def render_map():
    st.subheader(_("map_title"))
    cities = [
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Nashik", "lat": 19.9975, "lon": 73.7898},
    ]
    m = folium.Map(location=[19.0, 73.0], zoom_start=7)
    coords = [(c["lat"], c["lon"]) for c in cities]
    for c in cities:
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=c["name"],
            tooltip=c["name"],
            icon=folium.Icon(color="red", icon="music")
        ).add_to(m)
    AntPath(coords, color="#ff1744", weight=5, delay=800).add_to(m)

    # 모바일에서 좌우 100% 너비
    if st.session_state.admin:
        st_folium(m, width=900, height=550)
    else:
        st_folium(m, use_container_width=True, height=550)

# =============================================
# 사이드바 (힌디어 포함, "국내어" → "한국어")
# =============================================
with st.sidebar:
    st.markdown(f"### {_( 'lang_select')}")
    lang_choice = st.selectbox(
        "",
        ["ko", "en", "hi"],
        format_func=lambda x: {"ko": "한국어", "en": "English", "hi": "हिन्दी"}[x],
        index=["ko", "en", "hi"].index(st.session_state.lang)
    )
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()

    st.markdown("---")
    st.markdown(f"### {_( 'admin_login')}")
    if not st.session_state.admin:
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
# 자동 갱신 + 즉시 푸시 알림
# =============================================
current_time = datetime.now()

# 5분마다 자동 갱신 (일반 사용자만)
if not st.session_state.admin:
    if (current_time - st.session_state.last_check_time).total_seconds() > 300:
        latest_data = load_json(NOTICE_FILE)
        if len(latest_data) > st.session_state.last_notice_count:
            st.session_state.notice_data = latest_data
            st.session_state.last_notice_count = len(latest_data)
            st.rerun()
        st.session_state.last_check_time = current_time

# 관리자가 등록하면 즉시 알림 (일반 사용자에게)
if len(st.session_state.notice_data) > st.session_state.last_notice_count and not st.session_state.admin:
    st.toast(_("new_notice_alert"), icon="")
    st.session_state.last_notice_count = len(st.session_state.notice_data)

# =============================================
# 메인 헤더
# =============================================
st.markdown(f"# {_('title')}")
st.caption(_("caption"))

tab1, tab2 = st.tabs([_('tab_notice'), _['tab_map']])

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
                    st.success("공지 등록 완료!")
                else:
                    st.warning(_("warning"))
    render_notice_list()

with tab2:
    render_map()
