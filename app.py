import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone
import math

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 기존 데이터 강제 초기화 (테스트용)
if os.path.exists(CITY_FILE):
    os.remove(CITY_FILE)

# =============================================
# 세션 초기화
# =============================================
defaults = {
    "admin": False,
    "lang": "ko",
    "mode": None,
    "expanded": {},
    "current_tab": "tab_map"
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =============================================
# 다국어 (언어 선택 삭제 → ko 고정)
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
    "distance": "거리",
    "duration": "소요시간",
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

def make_navigation_link(lat, lon):
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

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
            if st.button("추가", key="add_city_btn"):
                st.session_state.mode = "add"
                st.rerun()

    # 새 도시 추가 폼
    if st.session_state.mode == "add" and st.session_state.admin:
        if not os.path.exists(CITY_LIST_FILE):
            default_cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Kolhapur", "Solapur", "Thane"]
            save_json(CITY_LIST_FILE, default_cities)
        cities_list = load_json(CITY_LIST_FILE)

        existing = {c["city"] for c in cities_data}
        available_cities = [c for c in cities_list if c not in existing]

        if not available_cities:
            st.info("모든 도시가 등록되었습니다.")
            if st.button("닫기"):
                st.session_state.mode = None
                st.rerun()
        else:
            with st.expander("새 도시 추가", expanded=True):
                city_name = st.selectbox(_["select_city"], available_cities)
                venue = st.text_input(_["venue"])
                seats = st.number_input(_["seats"], min_value=0, step=50)
                venue_type = st.radio("공연형태", [_["indoor"], _["outdoor"]], horizontal=True)
                map_link = st.text_input(_["google_link"])
                note = st.text_area(_["note"])

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(_["register"], key="reg_city"):
                        lat, lon = None, None
                        if map_link:
                            lat, lon = extract_latlon_from_shortlink(map_link)
                        if not lat or not lon:
                            coords = {
                                "Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567),
                                "Nagpur": (21.1458, 79.0882), "Nashik": (19.9975, 73.7898),
                                "Aurangabad": (19.8762, 75.3433), "Kolhapur": (16.7050, 74.2433),
                                "Solapur": (17.6599, 75.9064), "Thane": (19.2183, 72.9781),
                            }
                            lat, lon = coords.get(city_name, (19.0, 73.0))

                        nav_url = make_navigation_link(lat, lon)
                        new_city = {
                            "city": city_name,
                            "venue": venue or "미정",
                            "seats": seats,
                            "type": venue_type,
                            "note": note or "없음",
                            "lat": lat,
                            "lon": lon,
                            "nav_url": nav_url,
                            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                        }
                        cities_data.append(new_city)
                        save_json(CITY_FILE, cities_data)
                        st.session_state.mode = None
                        st.session_state.expanded = {}  # 모든 창 접기

                        if len(cities_data) > 1:
                            prev = cities_data[-2]
                            dist = calculate_distance(prev["lat"], prev["lon"], lat, lon)
                            duration = dist / 60
                            st.success(f"{prev['city']} → {city_name}\n거리: {dist:.1f}km / 소요시간: {duration:.1f}h")
                        else:
                            st.success("첫 도시 등록 완료!")
                        st.rerun()

                with col2:
                    if st.button("취소"):
                        st.session_state.mode = None
                        st.rerun()

    # 등록된 도시들 차례대로 표시 (바로 아래에 쌓임)
    for idx, city in enumerate(cities_data):
        key = f"city_exp_{idx}"
        expanded = st.session_state.expanded.get(key, False)
        with st.expander(f"{city['city']}", expanded=expanded):
            st.write(f"**날짜:** {city.get('date', '')}")
            st.write(f"**공연장소:** {city.get('venue', '')}")
            st.write(f"**예상 인원:** {city.get('seats', '')}")
            st.write(f"**구글맵:** {city.get('nav_url', '')}")
            st.write(f"**특이사항:** {city.get('note', '')}")
        if st.session_state.expanded.get(key, False) != expanded:
            st.session_state.expanded[key] = expanded

    # 지도
    st.markdown("---")
    m = folium.Map(location=[19.0, 73.0], zoom_start=6)
    coords = []
    for c in cities_data:
        popup_html = f"""
        <b>{c['city']}</b><br>
        장소: {c.get('venue','')}<br>
        인원: {c.get('seats','')}<br>
        <a href="{c.get('nav_url','#')}" target="_blank">길안내</a>
        """
        folium.Marker([c["lat"], c["lon"]], popup=popup_html, tooltip=c["city"],
                      icon=folium.Icon(color="red", icon="music")).add_to(m)
        coords.append((c["lat"], c["lon"]))
    if coords:
        AntPath(coords, color="#ff1744", weight=5, delay=800).add_to(m)
    st_folium(m, width=900, height=550)

# =============================================
# 사이드바 (언어선택 삭제)
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

if tab1:
    st.session_state.current_tab = "tab_notice"
elif tab2:
    st.session_state.current_tab = "tab_map"

with tab1:
    # 공지 기능 생략 (기존 코드 그대로 사용 가능)
    st.write("공지 관리 기능은 유지됩니다.")

with tab2:
    render_map()
