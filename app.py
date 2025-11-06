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
    "edit_city": None,
    "expanded": {},
    "current_tab": "tab_map"
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =============================================
# 다국어
# =============================================
LANG = {
    "ko": {
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
        "edit": "수정",
        "remove": "삭제",
        "date": "날짜",
        "add": "추가",
        "cancel": "취소",
    },
    "en": {
        "title": "Cantata Tour 2025",
        "caption": "Maharashtra Tour Management System",
        "tab_notice": "Notice",
        "tab_map": "Tour Route",
        "map_title": "View Route",
        "password": "Password",
        "login": "Login",
        "logout": "Logout",
        "wrong_pw": "Wrong password.",
        "select_city": "Select City",
        "venue": "Venue",
        "seats": "Expected Attendance",
        "note": "Notes",
        "google_link": "Google Maps Link",
        "indoor": "Indoor",
        "outdoor": "Outdoor",
        "register": "Register",
        "edit": "Edit",
        "remove": "Remove",
        "date": "Date",
        "add": "Add",
        "cancel": "Cancel",
    }
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

# =============================================
# Google Maps URL 생성
# =============================================
def generate_google_maps_url(cities_data):
    if not cities_data:
        return "https://www.google.com/maps"
    origin = f"{cities_data[0]['lat']},{cities_data[0]['lon']}"
    destination = f"{cities_data[-1]['lat']},{cities_data[-1]['lon']}"
    waypoints = "|".join([f"{c['lat']},{c['lon']}" for c in cities_data[1:-1]]) if len(cities_data) > 2 else ""
    params = {
        "api": 1,
        "origin": origin,
        "destination": destination,
        "travelmode": "driving"
    }
    if waypoints:
        params["waypoints"] = waypoints
    return "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(params, doseq=True)

# =============================================
# 지도 + 도시 관리
# =============================================
def render_map():
    st.subheader(_["map_title"])
    cities_data = load_json(CITY_FILE)

    # 관리자: 추가 버튼
    if st.session_state.admin:
        col1, col2 = st.columns([8, 2])
        with col2:
            if st.button(_["add"], key="add_main"):
                st.session_state.mode = "add"
                st.session_state.edit_city = None
                st.rerun()

    # 새 도시 추가
    if st.session_state.mode == "add" and st.session_state.admin:
        if not os.path.exists(CITY_LIST_FILE):
            default_cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"]
            save_json(CITY_LIST_FILE, default_cities)
        cities_list = load_json(CITY_LIST_FILE)
        existing = {c["city"] for c in cities_data}
        available = [c for c in cities_list if c not in existing]

        if not available:
            st.info("All cities registered" if st.session_state.lang == "en" else "모든 도시 등록됨")
            if st.button("Close" if st.session_state.lang == "en" else "닫기"):
                st.session_state.mode = None
                st.rerun()
        else:
            with st.expander("Add New City" if st.session_state.lang == "en" else "새 도시 추가", expanded=True):
                city_name = st.selectbox(_["select_city"], available, key="add_select")
                venue = st.text_input(_["venue"], key="add_venue")
                seats = st.number_input(_["seats"], min_value=0, step=50, key="add_seats")
                venue_type = st.radio("Venue Type" if st.session_state.lang == "en" else "공연형태", 
                                    [_["indoor"], _["outdoor"]], horizontal=True, key="add_type")
                map_link = st.text_input(_["google_link"], key="add_link")
                note = st.text_area(_["note"], key="add_note")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button(_["register"], key=f"reg_{city_name}"):
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
                            "venue": venue or ("TBD" if st.session_state.lang == "en" else "미정"),
                            "seats": seats,
                            "type": venue_type,
                            "note": note or ("None" if st.session_state.lang == "en" else "없음"),
                            "lat": lat,
                            "lon": lon,
                            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                        }
                        cities_data.append(new_city)
                        save_json(CITY_FILE, cities_data)
                        st.session_state.mode = None
                        st.session_state.expanded = {}
                        st.success(f"{city_name} registered!" if st.session_state.lang == "en" else f"{city_name} 등록 완료!")
                        st.rerun()

                with c2:
                    if st.button(_["cancel"], key="cancel_add"):
                        st.session_state.mode = None
                        st.rerun()

    # 도시 목록 + 수정/삭제
    for idx, city in enumerate(cities_data):
        key = f"city_{idx}"
        expanded = st.session_state.expanded.get(key, False)
        with st.expander(f"{city['city']}", expanded=expanded):
            st.write(f"**{_['date']}:** {city.get('date', '')}")
            st.write(f"**{_['venue']}:** {city.get('venue', '')}")
            st.write(f"**{_['seats']}:** {city.get('seats', '')}")
            st.write(f"**{_['note']}:** {city.get('note', '')}")

            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(_["edit"], key=f"edit_{idx}"):
                        st.session_state.mode = "edit"
                        st.session_state.edit_city = city["city"]
                        st.rerun()
                with c2:
                    if st.button(_["remove"], key=f"del_{idx}"):
                        cities_data.pop(idx)
                        save_json(CITY_FILE, cities_data)
                        st.session_state.expanded = {}
                        st.toast("City removed" if st.session_state.lang == "en" else "도시 삭제됨")
                        st.rerun()

        if st.session_state.expanded.get(key, False) != expanded:
            st.session_state.expanded[key] = expanded

    # 수정 모드
    if st.session_state.mode == "edit" and st.session_state.edit_city and st.session_state.admin:
        city = next((c for c in cities_data if c["city"] == st.session_state.edit_city), None)
        if city:
            with st.expander(f"Edit {city['city']}" if st.session_state.lang == "en" else f"{city['city']} 수정", expanded=True):
                venue = st.text_input(_["venue"], value=city["venue"], key="edit_venue")
                seats = st.number_input(_["seats"], min_value=0, step=50, value=city["seats"], key="edit_seats")
                venue_type = st.radio("Venue Type" if st.session_state.lang == "en" else "공연형태", 
                                    [_["indoor"], _["outdoor"]], 
                                    index=0 if city["type"] == _["indoor"] else 1, 
                                    horizontal=True, key="edit_type")
                map_link = st.text_input(_["google_link"], value="", key="edit_link")
                note = st.text_area(_["note"], value=city["note"], key="edit_note")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Save" if st.session_state.lang == "en" else "저장", key="save_edit"):
                        lat, lon = city["lat"], city["lon"]
                        if map_link.strip():
                            new_lat, new_lon = extract_latlon_from_shortlink(map_link)
                            if new_lat and new_lon:
                                lat, lon = new_lat, new_lon

                        updated = {
                            "city": city["city"],
                            "venue": venue or "TBD",
                            "seats": seats,
                            "type": venue_type,
                            "note": note or "None",
                            "lat": lat,
                            "lon": lon,
                            "date": city["date"]
                        }
                        for i, c in enumerate(cities_data):
                            if c["city"] == city["city"]:
                                cities_data[i] = updated
                                break
                        save_json(CITY_FILE, cities_data)
                        st.session_state.mode = None
                        st.session_state.edit_city = None
                        st.session_state.expanded = {}
                        st.success("Updated!" if st.session_state.lang == "en" else "수정 완료!")
                        st.rerun()

                with c2:
                    if st.button(_["cancel"], key="cancel_edit"):
                        st.session_state.mode = None
                        st.session_state.edit_city = None
                        st.rerun()

    # Google Maps (즉시 반영)
    st.markdown("---")
    if cities_data:
        maps_url = generate_google_maps_url(cities_data)
        iframe = f'''
        <iframe 
            width="100%" 
            height="550" 
            style="border:0" 
            loading="lazy" 
            allowfullscreen 
            referrerpolicy="no-referrer-when-downgrade"
            src="{maps_url}">
        </iframe>
        '''
        st.components.v1.html(iframe, height=550)
    else:
        st.info("No cities registered." if st.session_state.lang == "en" else "등록된 도시 없음")

# =============================================
# 사이드바 (언어 + 로그인)
# =============================================
with st.sidebar:
    # 언어 선택
    lang = st.selectbox("Language" if st.session_state.lang == "en" else "언어", ["한국어", "English"], 
                        index=0 if st.session_state.lang == "ko" else 1)
    new_lang = "ko" if lang == "한국어" else "en"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")

    # 관리자 로그인
    if not st.session_state.admin:
        st.markdown("### Admin Login")
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0000":
                st.session_state.admin = True
                st.success("Admin mode ON")
                st.rerun()
            else:
                st.error(_["wrong_pw"])
    else:
        st.success("Admin mode")
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
    st.write("Notice management works." if st.session_state.lang == "en" else "공지 관리 기능 정상 작동")

with tab2:
    render_map()
