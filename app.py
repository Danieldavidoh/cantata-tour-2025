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
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

def delete_notice(notice_id):
    if "notice_data" in st.session_state:
        st.session_state.notice_data = [n for n in st.session_state.notice_data if n["id"] != notice_id]
        save_json(NOTICE_FILE, st.session_state.notice_data)
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

def render_notice_list(show_delete=False):
    st.subheader("📢 공지 목록")

    if "notice_data" not in st.session_state or not st.session_state.notice_data:
        st.info("등록된 공지가 없습니다.")
        return

    for idx, n in enumerate(st.session_state.notice_data):
        # ✅ KeyError 방지
        title = n.get("title", "제목 없음")
        content = n.get("content", "")
        date = n.get("date", "날짜 없음")
        nid = n.get("id") or str(uuid.uuid4())

        # ✅ DuplicateElementKey 방지: idx와 uuid를 함께 사용
        with st.expander(f"📅 {date} | {title}", expanded=False):
            st.markdown(content)
            if show_delete:
                if st.button("🗑️ 삭제", key=f"del_{nid}_{idx}"):
                    delete_notice(nid)

# =============================================
# 지도 렌더링
# =============================================
def render_map():
    st.subheader("🗺️ 경로 보기")

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
# 메인
# =============================================
def main():
    st.title("🎵 칸타타 투어 2025")
    st.caption("마하라스트라 지역 투어 관리 시스템")

    # 세션 초기화
    if "notice_data" not in st.session_state:
        st.session_state.notice_data = load_json(NOTICE_FILE)

    # ✅ 누락된 ID 자동 보정
    changed = False
    for n in st.session_state.notice_data:
        if "id" not in n:
            n["id"] = str(uuid.uuid4())
            changed = True
    if changed:
        save_json(NOTICE_FILE, st.session_state.notice_data)

    tabs = st.tabs(["📰 공지 관리", "🗺️ 투어 경로"])

    with tabs[0]:
        st.subheader("📝 새 공지 추가")
        with st.form("add_notice_form", clear_on_submit=True):
            title = st.text_input("제목")
            content = st.text_area("내용")
            submitted = st.form_submit_button("등록")
            if submitted:
                if title.strip() and content.strip():
                    add_notice(title, content)
                else:
                    st.warning("제목과 내용을 모두 입력해주세요.")

        render_notice_list(show_delete=True)

    with tabs[1]:
        render_map()

# =============================================
# 실행
# =============================================
if __name__ == "__main__":
    main()
