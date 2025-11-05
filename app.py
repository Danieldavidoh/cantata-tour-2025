# app.py
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
# 거리 계산 함수
# =============================================
def calc_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # 지구 반경 (km)
    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# =============================================
# 공지 관리
# =============================================
def add_notice(title, content):
    if "notice_data" not in st.session_state:
        st.session_state.notice_data = []
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
    if "notice_data" in st.session_state:
        st.session_state.notice_data = [n for n in st.session_state.notice_data if n["id"] != notice_id]
        save_json(NOTICE_FILE, st.session_state.notice_data)
        st.rerun()

def render_notice_list(show_delete=False):
    st.subheader("공지 목록")

    if "notice_data" not in st.session_state or not st.session_state.notice_data:
        st.info("등록된 공지가 없습니다.")
        return

    for idx, n in enumerate(st.session_state.notice_data):
        # KeyError 방지
        title = n.get("title", "제목 없음")
        content = n.get("content", "")
        date = n.get("date", "날짜 없음")
        nid = n.get("id") or str(uuid.uuid4())

        # DuplicateElementKey 방지
        with st.expander(f"{date} | {title}", expanded=False):
            st.markdown(content)
            if show_delete:
                if st.button("삭제", key=f"del_{nid}_{idx}"):
                    delete_notice(nid)

# =============================================
# 지도 렌더링
# =============================================
def render_map():
    st.subheader("경로 보기")

    cities = [
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Nashik", "lat": 19.9975, "lon": 73.7898},
    ]

    m = folium.Map(location=[19.0, 73.0], zoom_start=7)

    coords = []
    for c in cities:
        coords.append((c["lat"], c["lon"]))
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=c["name"],
            tooltip=c["name"],
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    AntPath(coords, color="red", weight=3, delay=600).add_to(m)
    st_folium(m, width=800, height=500)

# =============================================
# 세션 상태 초기화
# =============================================
if "admin" not in st.session_state:
    st.session_state.admin = False
if "lang" not in st.session_state:
    st.session_state.lang = "ko"
if "notice_data" not in st.session_state:
    st.session_state.notice_data = load_json(NOTICE_FILE)

# 누락된 ID 자동 보정
changed = False
for n in st.session_state.notice_data:
    if "id" not in n:
        n["id"] = str(uuid.uuid4())
        changed = True
if changed:
    save_json(NOTICE_FILE, st.session_state.notice_data)

# =============================================
# 언어 설정 (항상 정의)
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
        "caption": "Maharashtra Tour Management System",
        "tab_notice": "Notice Board",
        "tab_map": "Tour Route",
        "add_notice": "Add New Notice",
        "title_label": "Title",
        "content_label": "Content",
        "submit": "Submit",
        "warning": "Please fill in both title and content.",
        "notice_list": "Notice List",
        "no_notice": "No notices registered.",
        "delete": "Delete",
        "map_title": "View Route",
        "admin_login": "Admin Login",
        "password": "Password",
        "login": "Login",
        "logout": "Logout",
        "wrong_pw": "Wrong password.",
        "lang_select": "Select Language"
    },
    "hi": {
        "title": "कांताता टूर 2025",
        "caption": "महाराष्ट्र क्षेत्र टूर प्रबंधन प्रणाली",
        "tab_notice": "सूचना बोर्ड",
        "tab_map": "टूर मार्ग",
        "add_notice": "नई सूचना जोड़ें",
        "title_label": "शीर्षक",
        "content_label": "सामग्री",
        "submit": "जमा करें",
        "warning": "कृपया शीर्षक और सामग्री दोनों भरें।",
        "notice_list": "सूचना सूची",
        "no_notice": "कोई सूचना पंजीकृत नहीं।",
        "delete": "हटाएं",
        "map_title": "मार्ग देखें",
        "admin_login": "प्रशासक लॉगिन",
        "password": "पासवर्ड",
        "login": "लॉगिन",
        "logout": "लॉगआउट",
        "wrong_pw": "गलत पासवर्ड।",
        "lang_select": "भाषा चुनें"
    }
}
_ = LANG.get(st.session_state.lang, LANG["ko"])  # 안전하게 ko 기본값

# =============================================
# 사이드바: 관리자 로그인 + 언어 선택
# =============================================
with st.sidebar:
    st.markdown("### " + _("lang_select"))
    lang_choice = st.selectbox(
        "Language",
        options=["ko", "en", "hi"],
        format_func=lambda x: {"ko": "한국어", "en": "English", "hi": "हिन्दी"}[x],
        index=["ko", "en", "hi"].index(st.session_state.lang)
    )
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()

    st.markdown("---")
    st.markdown("### " + _("admin_login"))
    if not st.session_state.admin:
        pw = st.text_input(_("password"), type="password", key="admin_pw")
        if st.button(_("login")):
            if pw == "0000":  # 비밀번호: 0000
                st.session_state.admin = True
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error(_("wrong_pw"))
    else:
        st.success("관리자 모드")
        if st.button(_("logout")):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 메인 UI
# =============================================
st.title(_("title"))
st.caption(_("caption"))

# 탭 구성
tab_notice, tab_map = st.tabs([_("tab_notice"), _("tab_map")])

# =============================================
# 탭 1: 공지 관리
# =============================================
with tab_notice:
    if st.session_state.admin:
        st.subheader(_("add_notice"))
        with st.form("add_notice_form", clear_on_submit=True):
            title = st.text_input(_("title_label"))
            content = st.text_area(_("content_label"))
            submitted = st.form_submit_button(_("submit"))
            if submitted:
                if title.strip() and content.strip():
                    add_notice(title, content)
                    st.success("공지가 등록되었습니다.")
                else:
                    st.warning(_("warning"))

        render_notice_list(show_delete=True)
    else:
        render_notice_list(show_delete=False)

# =============================================
# 탭 2: 투어 경로
# =============================================
with tab_map:
    render_map()
