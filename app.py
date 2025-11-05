# app.py
import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid
from math import radians, sin, cos, sqrt, atan2

# -------------------------------------------------
# 기본 페이지 설정
# -------------------------------------------------
st.set_page_config(page_title="Cantata Tour 2025", page_icon="🎄", layout="wide")

# -------------------------------------------------
# 세션 초기화
# -------------------------------------------------
def init_state():
    defaults = {
        "admin": False,
        "notice_data": [],
        "venue_data": {},
        "route": [],
        "expanded_notices": {}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

NOTICE_FILE = "notice_data.json"
VENUE_FILE = "venue_data.json"

# -------------------------------------------------
# JSON 파일 입출력
# -------------------------------------------------
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

st.session_state.notice_data = load_json(NOTICE_FILE, [])
st.session_state.venue_data = load_json(VENUE_FILE, {})

# -------------------------------------------------
# 거리 계산 함수
# -------------------------------------------------
def calc_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# -------------------------------------------------
# 공지 추가 / 삭제 함수
# -------------------------------------------------
def add_notice(title, content):
    if not title or not content:
        st.warning("제목과 내용을 입력하세요.")
        return
    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    st.session_state.notice_data.append(new_notice)
    save_json(NOTICE_FILE, st.session_state.notice_data)
    st.success("공지 추가됨 ✅")
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

def delete_notice(notice_id):
    st.session_state.notice_data = [n for n in st.session_state.notice_data if n.get("id") != notice_id]
    save_json(NOTICE_FILE, st.session_state.notice_data)
    st.success("공지 삭제됨 🗑️")
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# -------------------------------------------------
# 공지 리스트 렌더링
# -------------------------------------------------
def render_notice_list(show_delete=False):
    st.subheader("📢 공지 목록")
    if not st.session_state.notice_data:
        st.info("등록된 공지가 없습니다.")
        return

    for n in st.session_state.notice_data:
        title = n.get("title", "제목 없음")
        content = n.get("content", "")
        date = n.get("date", "날짜 없음")
        nid = n.get("id", str(uuid.uuid4()))

        with st.expander(f"📅 {date} | {title}"):
            st.write(content)
            if show_delete:
                if st.button("🗑️ 삭제", key=f"del_{nid}"):
                    delete_notice(nid)

# -------------------------------------------------
# 공연장 관리 함수
# -------------------------------------------------
def add_venue(city, venue, lat, lon):
    if not city or not venue:
        st.warning("도시와 공연장 이름을 입력하세요.")
        return
    st.session_state.venue_data[city] = {"venue": venue, "lat": lat, "lon": lon}
    save_json(VENUE_FILE, st.session_state.venue_data)
    st.success(f"{city} 공연장 추가됨 🎶")

def render_venue_map():
    if not st.session_state.venue_data:
        st.info("등록된 공연장이 없습니다.")
        return

    # 첫 번째 도시 기준으로 지도 중심 설정
    first_city = list(st.session_state.venue_data.values())[0]
    m = folium.Map(location=[first_city["lat"], first_city["lon"]], zoom_start=6)

    coords = []
    for city, info in st.session_state.venue_data.items():
        folium.Marker(
            location=[info["lat"], info["lon"]],
            tooltip=f"{city} - {info['venue']}",
            icon=folium.Icon(color="red", icon="music")
        ).add_to(m)
        coords.append([info["lat"], info["lon"]])

    if len(coords) > 1:
        AntPath(coords, color="blue", weight=3).add_to(m)

    st_data = st_folium(m, width=700, height=450)

# -------------------------------------------------
# 메인 페이지
# -------------------------------------------------
def main():
    st.title("🎄 Cantata Tour 2025")
    st.caption("마하라스트라 투어 일정 관리 대시보드")

    # 관리자 로그인
    if not st.session_state.admin:
        pw = st.text_input("관리자 비밀번호", type="password")
        if st.button("로그인"):
            if pw == "0000":
                st.session_state.admin = True
                try:
                    st.rerun()
                except AttributeError:
                    st.experimental_rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
        return

    # 로그아웃 버튼
    if st.button("로그아웃"):
        st.session_state.admin = False
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

    # 공지 추가 섹션
    st.markdown("### 📢 공지 추가")
    title = st.text_input("공지 제목")
    content = st.text_area("공지 내용")
    if st.button("공지 추가"):
        add_notice(title, content)

    # 공지 리스트
    render_notice_list(show_delete=True)

    st.markdown("---")

    # 공연장 관리 섹션
    st.markdown("### 🏟️ 공연장 추가")
    city = st.text_input("도시 이름")
    venue = st.text_input("공연장 이름")
    lat = st.number_input("위도", format="%.6f")
    lon = st.number_input("경도", format="%.6f")
    if st.button("공연장 추가"):
        add_venue(city, venue, lat, lon)

    st.markdown("### 🗺️ 공연장 지도")
    render_venue_map()

# -------------------------------------------------
# 실행
# -------------------------------------------------
if __name__ == "__main__":
    main()
