# app.py - 수정판 (2025.11.07) 🔥 지도 마커 복구 + 크리스마스 알림음 유지
# (이전 코드 전체 복사 후 아래 [지도 부분]만 교체하세요)

# ... (위쪽 코드 생략: import ~ render_notices() 까지 동일) ...

# ==================== [11] 지도 & 투어 경로 (마커 복구 완료!) ====================
def render_map():
    st.subheader(_('map_title'))
    if st.session_state.admin and st.button(_('add_city')):
        st.session_state.adding_cities.append(None)
        st.rerun()

    cities = sorted(load_json(CITY_FILE), key=lambda x: x.get("perf_date", "9999-12-31"))
    total_dist = 0

    for i, c in enumerate(cities):
        with st.expander(f"{c['city']} | {c.get('perf_date', '미정')}"):
            st.write(f"등록일: {c.get('date', '—')}")
            st.write(f"공연 날짜: {c.get('perf_date', '—')}")
            st.write(f"공연장소: {c.get('venue', '—')}")
            st.write(f"예상 인원: {c.get('seats', '—')}")
            st.write(f"특이사항: {c.get('note', '—')}")

            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✏️ 수정", key=f"edit_city_{i}"):
                        st.session_state.edit_city = c["city"]
                        st.rerun()
                with c2:
                    if st.button("🗑️ 삭제", key=f"del_city_{i}"):
                        cities.pop(i)
                        save_json(CITY_FILE, cities)
                        st.rerun()

        if i < len(cities) - 1:
            d = haversine(c['lat'], c['lon'], cities[i+1]['lat'], cities[i+1]['lon'])
            total_dist += d
            st.markdown(f"<div style='text-align:center;color:#2ecc71'>📍 {d:.0f}km</div>", unsafe_allow_html=True)

    if len(cities) > 1:
        st.markdown(f"<div style='text-align:center;color:#e74c3c;font-size:1.2em'>🎄 총 거리: {total_dist:.0f}km</div>", unsafe_allow_html=True)

    # 🎯 마커 복구: 아이콘 명시 + 팝업 강화
    m = folium.Map(location=[19.0, 73.0], zoom_start=7, tiles="OpenStreetMap")
    coords = []
    for c in cities:
        # 크리스마스 트리 아이콘으로 위치 표시 🔥
        icon = folium.Icon(color="red", icon="tree-christmas", prefix="fa")
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=folium.Popup(
                f"<b style='font-size:1.1em'>{c['city']}</b><br>"
                f"📅 {c.get('perf_date','—')}<br>"
                f"🎭 {c.get('venue','—')}<br>"
                f"👥 {c.get('seats','—')}명<br>"
                f"📝 {c.get('note','—')}",
                max_width=300
            ),
            tooltip=f"🎄 {c['city']}",
            icon=icon  # ← 이 줄이 핵심! 사라졌던 마커 복구
        ).add_to(m)
        coords.append((c["lat"], c["lon"]))

    if coords:
        AntPath(coords, color="#e74c3c", weight=6, opacity=0.8, delay=600).add_to(m)

    # 지도 크기 고정 + 반응형
    st_folium(m, width=900, height=550, key="tour_map")

# ... (아래 탭 부분 동일) ...
