import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =============================================
# 세션 초기화
# =============================================
defaults = {
    "admin": False,
    "lang": "ko",
    "selected_city": None,
    "venue_input": "",
    "seat_count": 0,
    "venue_type": "실내",
    "note_input": "",
    "map_link": "",
    "mode": None,                     # add / edit
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================================
# 언어
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "caption": "마하라스트라 지역 투어 관리 시스템",
        "tab_notice": "공지 관리",
        "tab_map": "투어 경로",
        "add_city": "도시 추가",
        "city_list": "도시 목록",
        "venue": "공연장소",
        "seats": "예상 인원",
        "note": "특이사항",
        "google_link": "구글맵 링크",
        "indoor": "실내",
        "outdoor": "실외",
        "register": "등록",
        "edit": "수정",
        "delete": "삭제",
        "show_route": "경로 보기",
        "select_city": "도시 선택",
        "warning": "⚠️ 올바른 정보를 입력하세요.",
    },
}
_ = LANG[st.session_state.lang]

# =============================================
# 유틸
# =============================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_latlon_from_shortlink(short_url):
    try:
        r = requests.get(short_url, allow_redirects=True, timeout=5)
        final_url = r.url
        match = re.search(r'@([0-9\.\-]+),([0-9\.\-]+)', final_url)
        if match:
            return float(match.group(1)), float(match.group(2))
    except:
        pass
    return None, None

def make_navigation_link(lat, lon):
    ua = st.session_state.get("user_agent", "")
    if "Android" in ua:
        return f"google.navigation:q={lat},{lon}"
    elif "iPhone" in ua or "iPad" in ua:
        return f"comgooglemaps://?daddr={lat},{lon}&directionsmode=driving"
    else:
        return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

# =============================================
# 도시 관리 섹션
# =============================================
def render_city_section():
    st.subheader(_["show_route"])

    # ------------------------------------------------------------------
    # 1. 항상 최신 파일을 읽어옴
    # ------------------------------------------------------------------
    cities_data = load_json(CITY_FILE)
    city_names = [c["city"] for c in cities_data]

    # ------------------------------------------------------------------
    # 2. 관리자 UI
    # ------------------------------------------------------------------
    if st.session_state.admin:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown("#### 도시 목록")
        with col2:
            if st.button("➕ 도시 추가"):
                st.session_state.selected_city = None
                st.session_state.venue_input = ""
                st.session_state.seat_count = 0
                st.session_state.venue_type = _["indoor"]
                st.session_state.note_input = ""
                st.session_state.map_link = ""
                st.session_state.mode = "add"
                st.rerun()

        # ------------------------------------------------------------------
        # 3. 도시 선택 (key 로 강제 리프레시)
        # ------------------------------------------------------------------
        selected = st.selectbox(
            _["select_city"],
            ["(새 도시 추가)"] + city_names,
            key=f"city_select_{len(city_names)}"
        )

        # ------------------------------------------------------------------
        # 4. 선택에 따라 입력 폼 초기화
        # ------------------------------------------------------------------
        if selected == "(새 도시 추가)":
            city_name = st.text_input("도시 이름", key="new_city_name")
            st.session_state.mode = "add"
        else:
            city_name = selected
            st.session_state.selected_city = selected
            st.session_state.mode = "edit"

            city_info = next((c for c in cities_data if c["city"] == selected), None)
            if city_info:
                st.session_state.venue_input = city_info.get("venue", "")
                st.session_state.seat_count = city_info.get("seats", 0)
                st.session_state.venue_type = city_info.get("type", _["indoor"])
                st.session_state.note_input = city_info.get("note", "")
                st.session_state.map_link = city_info.get("nav_url", "")

        st.markdown("---")
        st.text_input(_["venue"], key="venue_input")
        st.number_input(_["seats"], min_value=0, step=10, key="seat_count")
        st.radio("공연형태", [_["indoor"], _["outdoor"]], horizontal=True, key="venue_type")
        st.text_input(_["google_link"], key="map_link")
        st.text_area(_["note"], key="note_input")

        # ------------------------------------------------------------------
        # 5. 등록 / 삭제 / 취소
        # ------------------------------------------------------------------
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(_["register"]):
                lat, lon = extract_latlon_from_shortlink(st.session_state.map_link)
                if not lat or not lon:
                    st.warning(_["warning"])
                else:
                    nav_url = make_navigation_link(lat, lon)
                    new_data = {
                        "city": city_name,
                        "venue": st.session_state.venue_input,
                        "seats": st.session_state.seat_count,
                        "type": st.session_state.venue_type,
                        "note": st.session_state.note_input,
                        "lat": lat,
                        "lon": lon,
                        "nav_url": nav_url,
                    }

                    if st.session_state.mode == "add":
                        cities_data.append(new_data)
                        st.success("도시가 추가되었습니다.")
                    else:
                        for i, c in enumerate(cities_data):
                            if c["city"] == city_name:
                                cities_data[i] = new_data
                                break
                        st.success("도시 정보가 수정되었습니다.")

                    save_json(CITY_FILE, cities_data)
                    st.session_state.selected_city = None
                    st.session_state.mode = None
                    st.rerun()

        with c2:
            if st.session_state.mode == "edit" and st.button(_["delete"]):
                cities_data = [c for c in cities_data if c["city"] != city_name]
                save_json(CITY_FILE, cities_data)
                st.success("도시가 삭제되었습니다.")
                st.session_state.selected_city = None
                st.session_state.mode = None
                st.rerun()

        with c3:
            if st.button("취소"):
                st.session_state.selected_city = None
                st.session_state.mode = None
                st.rerun()

    # ------------------------------------------------------------------
    # 6. 지도 표시 (항상 최신 데이터)
    # ------------------------------------------------------------------
    st.markdown("---")
    m = folium.Map(location=[19.0, 73.0], zoom_start=6)
    data = load_json(CITY_FILE)
    coords = []
    for c in data:
        popup_html = f"""
        <b>{c['city']}</b><br>
        장소: {c.get('venue','')}<br>
        인원: {c.get('seats','')}<br>
        형태: {c.get('type','')}<br>
        <a href='{c.get('nav_url','#')}' target='_blank'>길안내</a><br>
        특이사항: {c.get('note','')}
        """
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=popup_html,
            tooltip=c["city"],
            icon=folium.Icon(color="red", icon="music")
        ).add_to(m)
        coords.append((c["lat"], c["lon"]))

    if coords:
        AntPath(coords, color="#ff1744", weight=5, delay=800).add_to(m)

    st_folium(m, width=900, height=550)

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    st.markdown("### 관리자 모드")
    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if pw == "0000":
                st.session_state.admin = True
                st.success("로그인 완료")
                st.rerun()
            else:
                st.error("비밀번호 오류")
    else:
        st.success("관리자 로그인 중")
        if st.button("로그아웃"):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 메인 페이지
# =============================================
st.markdown(f"# {_['title']} ")
st.caption(_["caption"])

render_city_section()
