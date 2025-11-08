# app.py
import streamlit as st
import json, os
from datetime import datetime, date
from pytz import timezone
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath

# =============================================
# 페이지 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

CITY_FILE = "cities.json"
NOTICE_FILE = "notice.json"

# =============================================
# 언어팩
# =============================================
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

# =============================================
# 도시 좌표 데이터
# =============================================
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

# =============================================
# JSON 유틸 함수
# =============================================
def load_json(file):
    try:
        if not os.path.exists(file):
            return []
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =============================================
# 도시 리스트 로드 (자동 복구)
# =============================================
def get_city_list():
    data = load_json(CITY_FILE)
    city_names = []

    if isinstance(data, list):
        for c in data:
            if isinstance(c, dict):
                name = c.get("city") or c.get("name")
                if name and isinstance(name, str):
                    city_names.append(name.strip())
            elif isinstance(c, str):
                city_names.append(c.strip())

    # 중복 제거 및 정렬
    city_names = sorted(set([x for x in city_names if x]))

    # 아무 것도 없으면 기본 좌표 목록 사용
    if not city_names:
        city_names = sorted(CITY_COORDS.keys())

    return city_names

# =============================================
# 도시 추가 폼
# =============================================
def city_select_form():
    st.subheader("🎵 " + _("add_city"))

    cities = get_city_list()
    no_show = _("no_show")

    if "selected_city" not in st.session_state:
        st.session_state.selected_city = no_show

    with st.form("add_city_form", clear_on_submit=True):
        selected = st.selectbox(_("city"), [no_show] + cities, key="city_selector")
        perf_date = st.date_input(_("perf_date"), value=date.today())
        venue = st.text_input(_("venue"))
        note = st.text_input(_("note"))
        google_link = st.text_input(_("google_link"))

        col1, col2 = st.columns([1, 2])
        with col1:
            indoor = st.radio(
                "장소 유형",
                [(_("indoor"), True), (_("outdoor"), False)],
                format_func=lambda x: x[0],
                horizontal=True,
            )[1]
        with col2:
            seats = st.number_input(_("seats"), min_value=0, max_value=10000, value=500, step=50)

        if st.form_submit_button("등록"):
            if selected != no_show and venue.strip():
                lat, lon = CITY_COORDS.get(selected, (18.52, 73.86))
                new_city = {
                    "city": selected,
                    "venue": venue,
                    "note": note,
                    "google_link": google_link,
                    "indoor": indoor,
                    "seats": str(seats),
                    "perf_date": str(perf_date),
                    "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
                    "lat": lat,
                    "lon": lon,
                }
                data = load_json(CITY_FILE)
                data.append(new_city)
                save_json(CITY_FILE, data)
                st.success(_("success_add"))
                st.session_state.selected_city = no_show
                st.rerun()
            else:
                st.warning(_("warning"))

# =============================================
# 지도 표시
# =============================================
def show_map():
    data = load_json(CITY_FILE)
    if not data:
        st.info("도시 데이터가 없습니다.")
        return

    m = folium.Map(location=[18.52, 73.86], zoom_start=7)
    for i, c in enumerate(data):
        lat = c.get("lat", 18.52)
        lon = c.get("lon", 73.86)
        popup = (
            f"<b>{c.get('city','')}</b><br>"
            f"{_('perf_date')}: {c.get('perf_date','')}<br>"
            f"{_('venue')}: {c.get('venue','')}"
        )
        folium.Marker(
            [lat, lon],
            popup=popup,
            icon=folium.Icon(color="red", icon="music", prefix="fa"),
        ).add_to(m)

        if i < len(data) - 1:
            nxt = data[i + 1]
            AntPath(
                [[lat, lon], [nxt.get("lat", 0), nxt.get("lon", 0)]],
                color="#e74c3c",
            ).add_to(m)

    st_folium(m, width=900, height=550, key="tour_map")

# =============================================
# 메인 UI
# =============================================
st.markdown(
    f"<h1 style='text-align:center;color:white;'>{_('title')}</h1>",
    unsafe_allow_html=True,
)

tab1, tab2 = st.columns(2)
if tab1.button(_("tab_notice")):
    st.session_state.page = "notice"
if tab2.button(_("tab_map")):
    st.session_state.page = "map"

page = st.session_state.get("page", "map")

if page == "map":
    city_select_form()
    show_map()
else:
    data = load_json(NOTICE_FILE)
    st.subheader("📢 공지사항")
    if not data:
        st.info("등록된 공지가 없습니다.")
    for n in data:
        st.markdown(f"### {n.get('title','')}")
        st.write(n.get("content", ""))
