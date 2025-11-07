import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Cantata Tour", layout="wide")

# --------------------------
# 배경 + 눈 효과 CSS
# --------------------------
page_bg = """
<style>
[data-testid="stAppViewContainer"] {
    background: url("background_christmas_dark.png");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}

.snowflake {
  position: fixed;
  top: -10px;
  color: white;
  font-size: 1em;
  pointer-events: none;
  animation-name: fall;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
}

@keyframes fall {
    0% {transform: translateY(0);}
    100% {transform: translateY(110vh);}
}
</style>
"""

st.markdown(page_bg, unsafe_allow_html=True)

import random
for i in range(120):
    st.markdown(
        f"<div class='snowflake' style='left: {random.randint(0,100)}vw; animation-duration:{random.randint(6,14)}s; opacity:{random.uniform(0.3,0.8)}'>❄</div>",
        unsafe_allow_html=True
    )

# --------------------------
# 로그인 (관리자 / 유저 모드)
# --------------------------
if "admin" not in st.session_state:
    st.session_state.admin = False

if not st.session_state.admin:
    st.title("Cantata Tour 2025 🎄")
    pwd = st.text_input("관리자 비밀번호 입력:", type="password")
    if pwd == "cantata2025":
        st.session_state.admin = True
        st.experimental_rerun()
    st.stop()

# --------------------------
# 데이터 불러오기
# --------------------------
try:
    df = pd.read_csv("cities.csv")
except:
    st.error("⚠ cities.csv 파일을 찾을 수 없습니다. 동일 폴더에 넣어주세요.")
    st.stop()

# --------------------------
# UI
# --------------------------
st.title("🎄 Cantata Tour 2025 — 관리자 모드")

selected_city = st.selectbox("도시 선택", df["city"].unique())

city_data = df[df["city"] == selected_city].iloc[0]

lat = city_data["lat"]
lon = city_data["lon"]

# --------------------------
# 지도 표시
# --------------------------
m = folium.Map(location=[lat, lon], zoom_start=12)
folium.Marker([lat, lon], tooltip=selected_city, icon=folium.Icon(color="red")).add_to(m)

st_folium(m, width=900, height=550)

# --------------------------
# 공연 정보 입력
# --------------------------
st.subheader("공연 정보 입력 / 수정")

date = st.text_input("📅 공연 날짜")
venue = st.text_input("🏛 공연 장소")
seats = st.text_input("💺 좌석 수")
map_link = st.text_input("🗺 구글맵 링크")

if st.button("저장하기"):
    df.loc[df["city"] == selected_city, ["date", "venue", "seats", "map_link"]] = [date, venue, seats, map_link]
    df.to_csv("cities.csv", index=False)
    st.success("✅ 저장되었습니다.")
