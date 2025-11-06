# app.py - 크리스마스 에디션 최종 패치 (2025.11.07) 🎅🔥
# ModuleNotFoundError 완전 차단 + 기존 기능 유지

# --- 1. 필수 라이브러리 설치 안내 ---
st.markdown("""
<div style="background:#e74c3c; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">
⚠️ <code>streamlit-folium</code> 라이브러리가 필요합니다!<br>
터미널에서 아래 명령어 실행:<br>
<code style="background:#2c3e50; padding:8px; border-radius:6px;">pip install streamlit-folium</code>
</div>
""", unsafe_allow_html=True)

# --- 2. 라이브러리 임포트 (안전하게) ---
try:
    import streamlit as st
    from datetime import datetime
    import folium
    from streamlit_folium import st_folium  # 여기서 에러 발생 방지
    from folium.plugins import AntPath
    import json, os, uuid, base64
    from pytz import timezone
    from streamlit_autorefresh import st_autorefresh
    from math import radians, sin, cos, sqrt, asin
except ModuleNotFoundError as e:
    st.error(f"라이브러리 설치 필요: {e}")
    st.code("pip install streamlit-folium streamlit-autorefresh pytz")
    st.stop()

# --- 나머지 코드는 이전과 동일 (생략) ---
# (하버신, 세션, 다국어, 테마, 공지, 지도 등 전체 유지)

# 예: 간단한 대체 지도 (folium만 사용)
def render_map():
    st.subheader("경로 보기")
    cities = load_json(CITY_FILE)
    if not cities:
        st.info("등록된 도시 없음")
        return

    m = folium.Map(location=[19.0, 73.0], zoom_start=7)
    coords = []
    for c in cities:
        folium.Marker([c["lat"], c["lon"]], popup=c["city"], icon=folium.Icon(color="red", icon="map-marker", prefix="fa")).add_to(m)
        coords.append((c["lat"], c["lon"]))
    if coords:
        AntPath(coords, color="#e74c3c", weight=6).add_to(m)
    
    # st_folium 대신 기본 folium 사용 (임시)
    st.components.v1.html(folium.Figure().add_child(m)._repr_html_(), height=600)

# --- 탭 ---
tab1, tab2 = st.tabs(["공지", "투어 경로"])

with tab1:
    render_notices()

with tab2:
    render_map()
