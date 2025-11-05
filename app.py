with st.expander("➕ 도시 관리", expanded=False):
    cities_list = load_json(CITY_LIST_FILE)
    city = st.selectbox(_["select_city"], cities_list)
    date = st.date_input("공연 날짜")
    venue = st.text_input(_["venue"])
    seats = st.number_input(_["seats"], min_value=0, step=50)
    venue_type = st.radio("공연 형태", [_["indoor"], _["outdoor"]], horizontal=True)
    map_link = st.text_input(_["google_link"])
    note = st.text_area(_["note"])

    data = load_json(CITY_FILE)
    existing = next((x for x in data if x["city"] == city and x["date"] == str(date)), None)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📍 등록"):
            lat, lon = extract_latlon_from_shortlink(map_link)
            if not lat:
                st.warning("⚠️ 올바른 구글맵 링크를 입력하세요.")
            else:
                new_item = {
                    "id": str(uuid.uuid4()),
                    "city": city,
                    "date": str(date),
                    "venue": venue,
                    "seats": seats,
                    "type": venue_type,
                    "note": note,
                    "lat": lat,
                    "lon": lon,
                    "nav_url": make_navigation_link(lat, lon)
                }
                data.append(new_item)
                save_json(CITY_FILE, data)
                st.success("✅ 도시가 등록되었습니다.")
                st.rerun()
    with col2:
        if st.button("✏️ 수정"):
            if existing:
                existing.update({
                    "venue": venue,
                    "seats": seats,
                    "type": venue_type,
                    "note": note,
                    "lat": lat,
                    "lon": lon,
                    "nav_url": make_navigation_link(lat, lon)
                })
                save_json(CITY_FILE, data)
                st.success("✅ 수정 완료")
                st.rerun()
            else:
                st.warning("⚠️ 수정할 데이터가 없습니다.")
    with col3:
        if st.button("🗑️ 삭제"):
            if existing:
                data.remove(existing)
                save_json(CITY_FILE, data)
                st.success("🗑️ 삭제 완료")
                st.rerun()
            else:
                st.warning("⚠️ 삭제할 항목이 없습니다.")
