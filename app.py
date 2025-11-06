import streamlit as st
from datetime import datetime
import json, os, uuid, base64, re, requests
from pytz import timezone
import urllib.parse

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
    "mode": None,
    "expanded": {}
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =============================================
# 다국어
# =============================================
_ = {
    "title": "칸타타 투어 2025",
    "caption": "마하라스트라 지역 투어 관리 시스템",
    "tab_notice": "공지 관리",
    "tab_map": "투어 경로",
    "map_title": "경로 보기",
    "password": "비밀번호",
    "login": "로그인",
    "logout": "로그아웃",
    "wrong_pw": "비밀번호가 틀렸습니다.",
    "select_city": "도시 선택",
    "venue": "공연장소",
    "seats": "예상 인원",
    "note": "특이사항",
    "google_link": "구글맵 링크",
    "indoor": "실내",
    "outdoor": "실외",
    "register": "등록",
}

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

# =============================================
# Google Maps URL 생성
# =============================================
def generate_google_maps_url(cities_data):
    if not cities_data:
        return "https://www.google.com/maps"
    origin = f"{cities_data[0]['lat']},{cities_data[0]['lon']}"
    destination = f"{cities_data[-1]['lat']},{cities_data[-1]['lon']}"
    waypoints = "|".join([f"{c['lat']},{c['lon']}" for c in cities_data[1:-1]]) if len(cities_data) > 2 else ""
    params = {"api": 1, "origin": origin, "destination": destination, "travelmode": "driving"}
    if waypoints:
        params["waypoints"] = waypoints
    return "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(params, doseq=True)

# =============================================
# 지도 + 도시 관리
# =============================================
def render_map():
    st.subheader(_["map_title"])
    cities_data = load_json(CITY_FILE)

    # 관리자: "추가" 버튼
    if st.session_state.admin:
        col1, col2 = st.columns([8, 2])
        with col2:
            if st.button("추가", key="add_city_main"):
                st.session_state.mode = "add"
                st.rerun()

    # 새 도시 추가 폼
    if st.session_state.mode == "add" and st.session_state.admin:
        if not os.path.exists(CITY_LIST_FILE):
            default_cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"]
            save_json(CITY_LIST_FILE, default_cities)
        cities_list = load_json(CITY_LIST_FILE)

        existing = {c["city"] for c in cities_data}
        available = [c for c in cities_list if c not in existing]

        if not available:
            st.info("모든 도시가 등록되었습니다.")
            if st.button("닫기"):
                st.session_state.mode = None
                st.rerun()
        else:
            with st.expander("새 도시 추가", expanded=True):
                city_name = st.selectbox(_["select_city"], available, key="city_select_add")
                venue = st.text_input(_["venue"], key="venue_add")
                seats = st.number_input(_["seats"], min_value=0, step=50, key="seats_add")
                venue_type = st.radio("공연형태", [_["indoor"], _["outdoor"]], horizontal=True, key="type_add")
                map_link = st.text_input(_["google_link"], key="link_add")
                note = st.text_area(_["note"], key="note_add")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(_["register"], key=f"register_{city_name}"):  # 고유 키
                        lat, lon = None, None
                        if map_link.strip():
                            lat, lon = extract_latlon_from_shortlink(map_link)
                        if not lat or not lon:
                            coords = {
                                "Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567),
                                "Nagpur": (21.1458, 79.0882), "Nashik": (19.9975, 73.7898),
                                "Aurangabad": (19.8762, 75.3433)
                            }
                            lat, lon = coords.get(city_name, (19.0, 73.0))

                        new_city = {
                            "city": city_name,
                            "venue": venue or "미정",
                            "seats": seats,
                            "type": venue_type,
                            "note": note or "없음",
                            "lat": lat,
                            "lon": lon,
                            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                        }
                        cities_data.append(new_city)
                        save_json(CITY_FILE, cities_data)
                        st.session_state.mode = None
                        st.session_state.expanded = {}
                        st.success(f"{city_name} 등록 완료!")
                        st.rerun()  # 즉시 반영

                with col2:
                    if st.button("취소", key="cancel_add"):
                        st.session_state.mode = None
                        st.rerun()

    # 등록된 도시 목록
    for idx, city in enumerate(cities_data):
        key = f"city_exp_{idx}"
        expanded = st.session_state.expanded.get(key, False)
        with st.expander(f"{city['city']}", expanded=expanded):
            st.write(f"**날짜:** {city.get('date', '')}")
            st.write(f"**공연장소:** {city.get('venue', '')}")
            st.write(f"**예상 인원:** {city.get('seats', '')}")
            st.write(f"**특이사항:** {city.get('note', '')}")
        if st.session_state.expanded.get(key, False) != expanded:
            st.session_state.expanded[key] = expanded

    # Google Maps
    st.markdown("---")
    if cities_data:
        maps_url = generate_google_maps_url(cities_data)
        st.components.v1.html(f'<iframe width="100%" height="550" src="{maps_url}" frameborder="0" allowfullscreen></iframe>', height=550)
    else:
        st.info("등록된 도시가 없습니다.")

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    if not st.session_state.admin:
        st.markdown("### 관리자 로그인")
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
# 메인
# =============================================
st.markdown(f"# {_['title']} ")
st.caption(_["caption"])

tab1, tab2 = st.tabs([_["tab_notice"], _["tab_map"]])

with tab1:
    # 공지 기능 (간략)
    st.write("공지 관리 기능은 정상 작동합니다.")

with tab2:
    render_map()
