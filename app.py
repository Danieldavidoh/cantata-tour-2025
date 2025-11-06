def render_map():
    st.subheader(_('map_title'))
    PUNE_LAT, PUNE_LON = 18.5204, 73.8567
    today = date.today()
    raw_cities = load_json(CITY_FILE)
    cities = []
    for city in raw_cities:
        try:
            perf_date = city.get("perf_date")
            if perf_date is None or perf_date == "9999-12-31":
                perf_date = None
            elif not isinstance(perf_date, str):
                perf_date = str(perf_date)
            city["perf_date"] = perf_date
            cities.append(city)
        except:
            continue
    cities = sorted(cities, key=lambda x: x.get("perf_date", "9999-12-31") or "9999-12-31")

    # --- 수정/추가 폼 생략 (기존 코드 유지) ---
    # (생략된 부분은 기존 코드 그대로 복사해서 사용)

    if not cities:
        st.warning("도시 없음")
        m = folium.Map(location=[PUNE_LAT, PUNE_LON], zoom_start=9, tiles="CartoDB positron")
        folium.Marker([PUNE_LAT, PUNE_LON], popup="시작", icon=folium.Icon(color="green", icon="star", prefix="fa")).add_to(m)
        st_folium(m, width=900, height=550, key="empty_map")
        return

    total_dist = 0
    coords = []
    m = folium.Map(location=[PUNE_LAT, PUNE_LON], zoom_start=9, tiles="CartoDB positron")

    # Google 스타일 아이콘 HTML
    google_icon_html = '''
    <div style="position: relative; width: 30px; height: 40px; margin-left: -15px; margin-top: -40px;">
        <div style="position: absolute; bottom: 0; left: 0; width: 30px; height: 30px; background: {color}; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); box-shadow: 0 0 6px rgba(0,0,0,0.3);"></div>
        <div style="position: absolute; top: 6px; left: 6px; width: 18px; height: 18px; background: white; border-radius: 50%; transform: rotate(45deg);"></div>
        <div style="position: absolute; top: 9px; left: 9px; width: 12px; height: 12px; background: {inner_color}; border-radius: 50%; transform: rotate(45deg);"></div>
    </div>
    '''

    # --- 도시 마커 + 과거 공연 흐리게 처리 ---
    for i, c in enumerate(cities):
        display_date = _("pending") if not c.get("perf_date") else c["perf_date"]
        try:
            perf_date_obj = datetime.strptime(c['perf_date'], "%Y-%m-%d").date() if c.get('perf_date') else None
        except:
            perf_date_obj = None

        # 과거 공연 → 흐리게
        is_past = perf_date_obj and perf_date_obj < today
        opacity = 0.4 if is_past else 1.0

        if is_past:
            color = "#cccccc"; inner = "#999999"
        elif perf_date_obj and perf_date_obj == today:
            color = "#000000"; inner = "#ffffff"
        else:
            color = "#ea4335" if c.get("indoor") else "#4285f4"
            inner = "#ffffff"

        # 투명도 적용된 아이콘
        icon_html = google_icon_html.format(color=color, inner_color=inner)
        icon_html = f'<div style="opacity: {opacity};">{icon_html}</div>'
        icon = folium.DivIcon(html=icon_html)

        folium.Marker(
            [c["lat"], c["lon"]],
            popup=f"<b>{c['city']}</b><br>{display_date}<br>{c.get('venue','—')}",
            tooltip=c["city"],
            icon=icon
        ).add_to(m)

        # --- 도시 정보 expander (기존 유지) ---
        with st.expander(f"{c['city']} | {display_date}"):
            st.write(f"등록일: {c.get('date', '—')}")
            st.write(f"공연 날짜: {display_date}")
            st.write(f"장소: {c.get('venue', '—')}")
            st.write(f"예상 인원: {c.get('seats', '—')}")
            st.write(f"특이사항: {c.get('note', '—')}")
            if c.get("google_link"):
                st.markdown(f"[구글맵 보기]({c['google_link']})")
            if st.session_state.admin and not st.session_state.get("edit_city"):
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("수정", key=f"edit_{i}"):
                        st.session_state.edit_city = c["city"]
                        st.rerun()
                with c2:
                    if st.button("삭제", key=f"del_{i}"):
                        cities.pop(i)
                        save_json(CITY_FILE, cities)
                        st.rerun()

        coords.append((c['lat'], c['lon']))

    # --- AntPath 라인 + 라인과 평행한 라벨 (완전 새로 구현) ---
    if len(coords) > 1:
        AntPath(coords, color="#e74c3c", weight=6, opacity=0.9, delay=800, dash_array=[20, 30]).add_to(m)

        for i in range(len(cities) - 1):
            c1, c2 = cities[i], cities[i+1]
            dist_km, mins = get_real_travel_time(c1['lat'], c1['lon'], c2['lat'], c2['lon'])
            total_dist += dist_km
            hours = mins // 60
            mins_remain = mins % 60
            time_str = _(f"est_time").format(hours=hours, mins=mins_remain) if hours or mins_remain else ""
            label_text = f"{dist_km:.0f}km {time_str}".strip()

            # 중간 지점
            mid_lat = (c1['lat'] + c2['lat']) / 2
            mid_lon = (c1['lon'] + c2['lon']) / 2

            # 방위각 계산 (도 → 라디안)
            dx = c2['lon'] - c1['lon']
            dy = c2['lat'] - c1['lat']
            bearing = degrees(atan2(dx, dy))  # 0=북, 90=동

            # 라벨 회전 각도 (항상 가독성 유지: 90~270도 사이면 180도 뒤집기)
            rotate = bearing
            if 90 < bearing < 270:
                rotate += 180

            # 라인 위쪽으로 약간 오프셋 (거리 기반)
            offset_distance = 0.0008  # 약 80m 정도 위로
            lat_offset = offset_distance * cos(radians(bearing))
            lon_offset = offset_distance * sin(radians(bearing)) / cos(radians(c1['lat']))  # 경도 보정
            label_lat = mid_lat + lat_offset
            label_lon = mid_lon + lon_offset

            # 최종 라벨 (라인과 완벽 평행, 뒤집힘 방지, 말풍선 없음)
            label_html = f'''
            <div style="
                position: relative;
                color: #e74c3c;
                font-weight: bold;
                font-size: 13px;
                white-space: nowrap;
                text-shadow: 0 0 6px white, 0 0 3px white;
                transform: translate(-50%, -50%) rotate({rotate}deg);
                transform-origin: center;
                pointer-events: none;
                z-index: 1000;
            ">
                {label_text}
            </div>
            '''

            folium.Marker(
                [label_lat, label_lon],
                icon=folium.DivIcon(html=label_html)
            ).add_to(m)

    # 총 거리 표시
    if len(cities) > 1:
        st.markdown(f"<div style='text-align:center;color:#e74c3c;font-size:1.3em;margin:15px 0;font-weight:bold;'>총 거리: {total_dist:.0f}km</div>", unsafe_allow_html=True)

    # 지도 렌더링
    st_folium(m, width=900, height=550, key=f"map_{len(cities)}")
