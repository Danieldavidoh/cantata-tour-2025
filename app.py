# =============================================
# 지도 + 도시 추가 (KeyError 방지 + 레거시 데이터 호환)
# =============================================
def render_map():
    st.subheader(_["map_title"])

    # === 데이터 보정: date 필드 없으면 추가 ===
    data = load_json(CITY_FILE)
    today_str = date.today().strftime("%Y-%m-%d")
    for entry in data:
        if "date" not in entry:
            entry["date"] = today_str  # 기본값: 오늘
    save_json(CITY_FILE, data)  # 보정된 데이터 저장

    if st.session_state.admin:
        # === 도시 추가/수정 폼 ===
        with st.expander("도시 추가 / 수정", expanded=True):
            # 도시 목록 로드
            if not os.path.exists(CITY_LIST_FILE):
                default_cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad",
                                  "Kolhapur", "Solapur", "Thane", "Ratnagiri", "Sangli"]
                save_json(CITY_LIST_FILE, default_cities)
            cities_list = load_json(CITY_LIST_FILE)

            # 수정 모드
            edit_idx = st.session_state.get("edit_index")
            edit_data = None
            if edit_idx is not None and 0 <= edit_idx < len(data):
                edit_data = data[edit_idx]

            # 도시 선택
            city_options = cities_list + ["새 도시 입력..."]
            default_city = edit_data["city"] if edit_data else city_options[0]
            selected_city_idx = city_options.index(default_city) if default_city in city_options else 0
            selected_city = st.selectbox(_["select_city"], city_options, index=selected_city_idx)

            # 신규 도시 입력
            if selected_city == "새 도시 입력...":
                city = st.text_input("새 도시 이름", value=edit_data["city"] if edit_data else "")
            else:
                city = selected_city

            # 날짜 (달력)
            default_date = datetime.strptime(edit_data["date"], "%Y-%m-%d").date() if edit_data else date.today()
            tour_date = st.date_input(_["date"], value=default_date)

            # 공연장소, 좌석수, 형태
            venue = st.text_input(_["venue"], value=edit_data.get("venue", "") if edit_data else "")
            seats = st.number_input(_["seats"], min_value=0, step=50, value=edit_data.get("seats", 0) if edit_data else 0)
            type_val = edit_data.get("type", _["indoor"]) if edit_data else _["indoor"]
            venue_type = st.radio("공연형태", [_["indoor"], _["outdoor"]], horizontal=True,
                                  index=0 if type_val == _["indoor"] else 1)

            # 구글맵 링크
            map_link = st.text_input(_["google_link"], value=edit_data.get("map_link", "") if edit_data else "")

            # 특이사항
            note = st.text_area(_["note"], value=edit_data.get("note", "") if edit_data else "")

            # 등록 / 저장 버튼
            if st.button(_["save"] if edit_idx is not None else _["register"]):
                if not city.strip():
                    st.warning("도시 이름을 입력하세요.")
                    return
                lat, lon = extract_latlon_from_shortlink(map_link)
                if not lat or not lon:
                    st.warning("올바른 구글맵 링크를 입력하세요.")
                    return

                nav_url = make_navigation_link(lat, lon)
                new_entry = {
                    "city": city,
                    "date": tour_date.strftime("%Y-%m-%d"),
                    "venue": venue,
                    "seats": seats,
                    "type": venue_type,
                    "note": note,
                    "lat": lat,
                    "lon": lon,
                    "nav_url": nav_url,
                }

                if edit_idx is not None:
                    data[edit_idx] = new_entry
                    st.session_state.edit_index = None
                    st.toast("수정 완료!")
                else:
                    data.append(new_entry)
                    st.toast("도시 추가 완료!")

                # 날짜순 정렬
                data.sort(key=lambda x: x.get("date", today_str))

                # 신규 도시면 목록에 추가
                if city not in cities_list:
                    cities_list.append(city)
                    save_json(CITY_LIST_FILE, cities_list)

                save_json(CITY_FILE, data)
                st.rerun()

        # === 추가된 투어 일정 리스트 ===
        st.subheader(_["tour_list"])
        if not data:
            st.info(_["no_tour"])
        else:
            # 날짜순 정렬 (보장)
            data_sorted = sorted(data, key=lambda x: x.get("date", today_str))
            for idx, c in enumerate(data_sorted):
                with st.expander(f"{c['city']} | {c.get('date', '?')} | {c.get('venue', '미정')} | {c.get('seats', 0)}명 | {c.get('type', '')}"):
                    st.markdown(f"**길안내**: [{c.get('nav_url', 'N/A')}]({c.get('nav_url', '#')})")
                    st.markdown(f"**특이사항**: {c.get('note', '없음')}")
                    col1, col2 = st.columns(2)
                    if col1.button("수정", key=f"edit_{idx}"):
                        # 원본 인덱스 찾기 (정렬 후라서 재검색)
                        orig_idx = next(i for i, d in enumerate(data) if d["city"] == c["city"] and d["date"] == c["date"])
                        st.session_state.edit_index = orig_idx
                        st.rerun()
                    if col2.button("제거", key=f"del_{idx}"):
                        orig_idx = next(i for i, d in enumerate(data) if d["city"] == c["city"] and d["date"] == c["date"])
                        data.pop(orig_idx)
                        save_json(CITY_FILE, data)
                        st.toast("제거 완료!")
                        st.rerun()

    # === 지도 출력 ===
    m = folium.Map(location=[19.0, 73.0], zoom_start=6, tiles="CartoDB positron")
    coords = []

    for c in data:
        if not all(k in c for k in ["city", "lat", "lon"]):
            continue

        popup_html = f"""
        <div style="
            font-family: 'Malgun Gothic', sans-serif;
            font-size: 14px;
            text-align: center;
            white-space: nowrap;
            padding: 10px 16px;
            min-width: 420px;
            max-width: 550px;
        ">
            <b>{c['city']}</b> | {c.get('date', '?')} | {c.get('venue', '미정')} | {c.get('seats', 0)}석 | {c.get('type', '')}
        </div>
        """

        folium.Marker(
            [c["lat"], c["lon"]],
            popup=folium.Popup(popup_html, max_width=550),
            tooltip=c["city"],
            icon=folium.Icon(color="red", icon="music", prefix="fa")
        ).add_to(m)

        coords.append((c["lat"], c["lon"]))

    if len(coords) > 1:
        AntPath(coords, color="#ff1744", weight=5, opacity=0.8, delay=800, dash_array=[20, 30]).add_to(m)

    st_folium(m, width=900, height=550, key="tour_map")
