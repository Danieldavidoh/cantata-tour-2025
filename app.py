import json, os, uuid, base64, random
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
import pandas as pd

# --- 기본 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
CSV_FILE = "마하라스트라 도시목록.csv"

# --- 언어팩 ---
LANG = {
    "ko": {
        "title": "칸타타 투어 2025 마하라스트라",
        "tab_notice": "공지",
        "tab_map": "투어 경로",
        "add_city": "도시 추가",
        "city": "도시",
        "venue": "공연 장소",
        "perf_date": "공연 날짜",
        "note": "특이사항",
        "google_link": "구글맵 링크",
        "seats": "예상 인원",
        "indoor": "실내",
        "outdoor": "실외",
        "delete": "삭제",
        "no_show": "공연 없음",
        "warning": "도시와 공연 장소를 입력하세요.",
        "success_add": "도시 추가 완료!"
    }
}
_ = lambda k: LANG["ko"].get(k, k)

# --- 유틸 ---
def load_json(path):
    try:
        return json.load(open(path, "r", encoding="utf-8")) if os.path.exists(path) else []
    except Exception:
        return []

def save_json(path, data):
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 도시 좌표 ---
CITY_COORDS = {
    "Mumbai": (19.07, 72.88),
    "Pune": (18.52, 73.86),
    "Nagpur": (21.15, 79.08),
    "Nashik": (20.00, 73.79),
    "Aurangabad": (19.88, 75.34),
    "Thane": (19.22, 72.98),
    "Kolhapur": (16.70, 74.24),
    "Solapur": (17.67, 75.91),
    "Amravati": (20.93, 77.75)
}

# --- 안전한 도시 목록 정리 함수 ---
def get_city_list():
    data = load_json(CITY_FILE)
    names = []

    # 다양한 구조에 대응
    if isinstance(data, list):
        for c in data:
            if isinstance(c, dict):
                name = c.get("city") or c.get("name") or ""
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())
            elif isinstance(c, str) and c.strip():
                names.append(c.strip())
    names = sorted(set(names))

    # 비어 있으면 좌표 목록으로 대체
    if not names:
        names = sorted(CITY_COORDS.keys())

    return names

# --- 도시 선택 UI (새 버전) ---
def select_city_section():
    st.markdown("### 🏙️ " + _("add_city"))

    cities = get_city_list()
    no_show_label = _("no_show")

    with st.form("city_form", clear_on_submit=True):
        selected_city = st.selectbox(_("city"), [no_show_label] + cities, key="select_city_box")
        perf_date = st.date_input(_("perf_date"), value=date.today())
        venue = st.text_input(_("venue"))
        note = st.text_input(_("note"))
        google_link = st.text_input(_("google_link"))

        col1, col2 = st.columns([1, 2])
        with col1:
            indoor = st.radio("장소 유형", [(_("indoor"), True), (_("outdoor"), False)],
                              format_func=lambda x: x[0], horizontal=True)[1]
        with col2:
            seats = st.number_input(_("seats"), min_value=0, max_value=10000, value=500, step=50)

        submit = st.form_submit_button("등록")
        if submit:
            if selected_city != no_show_label and venue.strip():
                lat, lon = CITY_COORDS.get(selected_city, (18.52, 73.86))
                city_data = {
                    "city": selected_city,
                    "venue": venue,
                    "note": note,
                    "google_link": google_link,
                    "indoor": indoor,
                    "seats": str(seats),
                    "perf_date": str(perf_date),
                    "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
                    "lat": lat,
                    "lon": lon
                }
                data = load_json(CITY_FILE)
                data.append(city_data)
                save_json(CITY_FILE, data)
                st.success(_("success_add"))
                st.session_state["select_city_box"] = no_show_label
                st.rerun()
            else:
                st.warning(_("warning"))

# --- 지도 ---
def show_map():
    cities = load_json(CITY_FILE)
    if not cities:
        st.info("도시 데이터가 없습니다.")
        return
    m = folium.Map(location=[18.52, 73.86], zoom_start=7)
    for i, c in enumerate(cities):
        lat = c.get("lat", 18.52)
        lon = c.get("lon", 73.86)
        city = c.get("city", "")
        perf_date = c.get("perf_date", "")
        venue = c.get("venue", "")
        popup_html = f"<b>{city}</b><br>📅 {perf_date}<br>🏛️ {venue}"
        folium.Marker([lat, lon],
                      popup=popup_html,
                      icon=folium.Icon(color="red", icon="music", prefix="fa")).add_to(m)
        if i < len(cities) - 1:
            nxt = cities[i + 1]
            AntPath([[lat, lon], [nxt.get("lat", 0), nxt.get("lon", 0)]], color="#e74c3c", weight=5).add_to(m)
    st_folium(m, width=900, height=550, key="tour_map")

# --- 본문 ---
st.markdown(f"<h1 style='text-align:center; color:white;'>{_('title')}</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button(_("tab_notice")):
        st.session_state.show_notice = not st.session_state.get("show_notice", False)
        st.session_state.show_map = False
        st.rerun()
with col2:
    if st.button(_("tab_map")):
        st.session_state.show_map = not st.session_state.get("show_map", False)
        st.session_state.show_notice = False
        st.rerun()

# --- 공지 ---
if st.session_state.get("show_notice", False):
    data = load_json(NOTICE_FILE)
    for n in data:
        st.markdown(f"### 🗓️ {n.get('date','')} — {n.get('title','')}")
        st.write(n.get("content", ""))

# --- 지도 / 도시 관리 ---
if st.session_state.get("show_map", False):
    if st.session_state.get("admin", True):  # 관리자 전용
        select_city_section()
    show_map()
