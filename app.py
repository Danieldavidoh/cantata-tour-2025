import streamlit as st
import json, os, uuid
from datetime import datetime, date
from pytz import timezone
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from streamlit_autorefresh import st_autorefresh

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

CITY_FILE = "cities.json"
NOTICE_FILE = "notice.json"

# =============================================
# 유틸
# =============================================
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =============================================
# 기본 데이터
# =============================================
CITY_COORDS = {
    "Mumbai": (19.07609, 72.877426),
    "Pune": (18.52043, 73.856743),
    "Nagpur": (21.1458, 79.088154),
}
DEFAULT_CITIES = [
    {"city": k, "venue": "", "seats": "", "note": "", "google_link": "", "indoor": False,
     "date": "", "perf_date": "", "lat": v[0], "lon": v[1]}
    for k, v in CITY_COORDS.items()
]

# =============================================
# 데이터 로드
# =============================================
cities = load_json(CITY_FILE, DEFAULT_CITIES)
notices = load_json(NOTICE_FILE, [])

# =============================================
# 관리자 모드 여부
# =============================================
is_admin = st.sidebar.checkbox("관리자 모드", False)

# =============================================
# 상단 타이틀
# =============================================
st.title("칸타타 투어 2025")
st.markdown("---")

# =============================================
# 공지 영역
# =============================================
if notices:
    st.subheader("📢 공지사항")
    for n in reversed(notices):
        st.markdown(f"**[{n['time']}]** {n['text']}")
else:
    st.info("현재 등록된 공지가 없습니다.")

# =============================================
# 관리자: 공지 관리
# =============================================
if is_admin:
    st.markdown("### 📋 공지 추가 / 관리")
    new_notice = st.text_area("새 공지 작성", "")
    if st.button("공지 등록"):
        if new_notice.strip():
            tz = timezone("Asia/Kolkata")
            now = datetime.now(tz)
            formatted = now.strftime("%m/%d %H:%M")
            notices.append({"id": str(uuid.uuid4()), "text": new_notice.strip(), "time": formatted})
            save_json(NOTICE_FILE, notices)
            st.success("공지 등록 완료!")
            st.experimental_rerun()

    if notices:
        if st.button("모든 공지 삭제"):
            save_json(NOTICE_FILE, [])
            st.warning("모든 공지가 삭제되었습니다.")
            st.experimental_rerun()

st.markdown("---")

# =============================================
# 도시 선택
# =============================================
city_names = [c["city"] for c in cities]
selected_city = st.selectbox("도시 선택", ["공연 없음"] + city_names, index=0)
st.markdown("---")

# =============================================
# 관리자 모드: 도시 추가/관리
# =============================================
if is_admin:
    st.subheader("🗺️ 투어 경로 관리")

    # 도시 목록 표시
    st.markdown("#### 현재 등록된 도시")
    if cities:
        for c in cities:
            st.write(f"- **{c['city']}** | 공연일자: {c['perf_date']} | 장소: {c['venue']}")
    else:
        st.info("등록된 도시가 없습니다.")

    st.markdown("#### 도시 추가 (도시 이름 제외됨)")
    # 도시 이름 입력 필드를 제거하고 나머지만 유지
    with st.form("add_city_form"):
        perf_date = st.date_input("공연 날짜", date.today())
        venue = st.text_input("공연 장소")
        seats = st.text_input("좌석 수")
        note = st.text_area("비고")
        google_link = st.text_input("구글 지도 링크")
        indoor = st.checkbox("실내 공연")
        lat = st.number_input("위도 (Latitude)", value=18.52043, format="%.6f")
        lon = st.number_input("경도 (Longitude)", value=73.856743, format="%.6f")

        submitted = st.form_submit_button("도시 추가")
        if submitted:
            # 도시명은 입력하지 않으므로 자동 생성
            new_city = {
                "city": f"City-{len(cities) + 1}",
                "venue": venue,
                "seats": seats,
                "note": note,
                "google_link": google_link,
                "indoor": indoor,
                "date": str(perf_date),
                "perf_date": perf_date.strftime("%m/%d"),
                "lat": lat,
                "lon": lon
            }
            cities.append(new_city)
            save_json(CITY_FILE, cities)
            st.success(f"{new_city['city']} 추가 완료!")
            st.experimental_rerun()

st.markdown("---")

# =============================================
# 지도 표시
# =============================================
st.subheader("📍 투어 경로")
if not cities:
    st.info("등록된 도시가 없습니다.")
else:
    m = folium.Map(location=[18.52043, 73.856743], zoom_start=6)
    for i, c in enumerate(cities):
        popup_text = f"{c['city']}<br>{c['perf_date']}<br>{c['venue']}"
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=popup_text,
            icon=folium.Icon(color="red", icon="music", prefix="fa")
        ).add_to(m)
        if i < len(cities) - 1:
            next_c = cities[i + 1]
            AntPath([[c["lat"], c["lon"]], [next_c["lat"], next_c["lon"]]],
                    color="#e74c3c", weight=4).add_to(m)

    st_folium(m, width=900, height=500)

# =============================================
# 자동 새로고침
# =============================================
st_autorefresh(interval=60 * 1000, key="data_refresh")
