import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from math import radians, sin, cos, sqrt, atan2
import json
import os
import uuid

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
NOTICE_FILE = "notice.json"

# =============================================
# 유틸 함수
# =============================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =============================================
# 다국어 지원
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
        "lang_select": "언어 선택"
    },
    "en": {
        "title": "Cantata Tour 2025",
        "caption": "Maharashtra Tour Management",
        "tab_notice": "Notice Board",
        "tab_map": "Tour Route",
        "add_notice": "Add Notice",
        "title_label": "Title",
        "content_label": "Content",
        "submit": "Submit",
        "warning": "Please fill in both title and content.",
        "notice_list": "Notice List",
        "no_notice": "No notices yet.",
        "delete": "Delete",
        "map_title": "View Route",
        "admin_login": "Admin Login",
        "password": "Password",
        "login": "Login",
        "logout": "Logout",
        "wrong_pw": "Wrong password.",
        "lang_select": "Language"
    },
    "hi": {
        "title": "कांताता टूर 2025",
        "caption": "महाराष्ट्र टूर मैनेजमेंट",
        "tab_notice": "सूचना बोर्ड",
        "tab_map": "टूर रूट",
        "add_notice": "नई सूचना जोड़ें",
        "title_label": "शीर्षक",
        "content_label": "सामग्री",
        "submit": "जमा करें",
        "warning": "कृपया शीर्षक और सामग्री भरें।",
        "notice_list": "सूचना सूची",
        "no_notice": "कोई सूचना नहीं है।",
        "delete": "हटाएं",
        "map_title": "रूट देखें",
        "admin_login": "एडमिन लॉगिन",
        "password": "पासवर्ड",
        "login": "लॉगिन",
        "logout": "लॉगआउट",
        "wrong_pw": "गलत पासवर्ड।",
        "lang_select": "भाषा चुनें"
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

_ = LANG[st.session_state.lang]

# =============================================
# 공지 관리 함수
# =============================================
def add_notice(title, content):
    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    st.session_state.notice_data.insert(0, new_notice)
    save_json(NOTICE_FILE, st.session_state.notice_data)
    st.rerun()

def delete_notice(notice_id):
    st.session_state.notice_data = [n for n in st.session_state.notice_data if n["id"] != notice_id]
    save_json(NOTICE_FILE, st.session_state.notice_data)
    st.rerun()

def render_notice_list(show_delete=False):
    st.subheader(_["notice_list"])

    if not st.session_state.notice_data:
        st.info(_["no_notice"])
        return

    for idx, n in enumerate(st.session_state.notice_data):
        with st.expander(f"📅 {n.get('date','?')} | {n.get('title','(제목 없음)')}"):
            st.markdown(n.get('content', ''))
            if show_delete:
                if st.button(_["delete"], key=f"del_{n['id']}_{idx}"):
                    delete_notice(n["id"])

# =============================================
# 지도 렌더링
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
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=c["name"],
            tooltip=c["name"],
            icon=folium.Icon(color="red", icon="music")
        ).add_to(m)

    AntPath(coords, color="#ff1744", weight=5, delay=800).add_to(m)
    st_folium(m, width=900, height=550)

# =============================================
# 사이드바: 언어 + 관리자 로그인
# =============================================
with st.sidebar:
    # 언어 선택
    new_lang = st.selectbox(
        _["lang_select"],
        ["ko", "en", "hi"],
        format_func=lambda x: {"ko": "한국어", "en": "English", "hi": "हिन्दी"}[x],
        index=["ko", "en", "hi"].index(st.session_state.lang)
    )
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")

    # 관리자 로그인
    if not st.session_state.admin:
        st.markdown(f"### 🔐 {_['admin_login']}")
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0000":
                st.session_state.admin = True
                st.success("✅ 관리자 모드 ON")
                st.rerun()
            else:
                st.error(_["wrong_pw"])
    else:
        st.success("✅ 관리자 모드")
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 메인
# =============================================
st.markdown(f"# {_['title']} 🎄")
st.caption(_['caption'])

tab1, tab2 = st.tabs([_['tab_notice'], _['tab_map']])

with tab1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_["title_label"])
            c = st.text_area(_["content_label"])
            if st.form_submit_button(_["submit"]):
                if t.strip() and c.strip():
                    add_notice(t, c)
                else:
                    st.warning(_["warning"])
        render_notice_list(show_delete=True)
    else:
        render_notice_list(show_delete=False)

with tab2:
    render_map()
