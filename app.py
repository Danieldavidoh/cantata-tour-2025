# =============================================
# 9. 공연장 & 날짜 (항상 보이도록 expanded=True + 화살표 위치 조정)
# =============================================
st.markdown("---")
st.subheader(_["venues_dates"])

for city in st.session_state.route:
    with st.expander(f"**{city}**", expanded=True):  # 항상 열려 있음
        # 공연 날짜
        cur = st.session_state.dates.get(city, datetime.now().date())
        new = st.date_input(_["performance_date"], cur, key=f"date_{city}")
        if new != cur:
            st.session_state.dates[city] = new
            st.success("날짜 변경됨")
            st.rerun()

        # 공연장 등록 폼
        if st.session_state.admin or st.session_state.guest_mode:
            st.markdown("---")
            col_left = st.container()
            with col_left:
                col1, col2 = st.columns([3, 1])
                with col1:
                    venue_name = st.text_input(_["venue_name"], key=f"v_{city}")
                with col2:
                    seats = st.number_input(_["seats"], 1, step=50, key=f"s_{city}")

                col3, col4 = st.columns([3, 1])
                with col3:
                    google_link = st.text_input(_["google_link"], placeholder="https://...", key=f"l_{city}")
                with col4:
                    io_key = f"io_{city}"
                    if io_key not in st.session_state:
                        st.session_state[io_key] = _["outdoor"]
                    if st.button(f"**{st.session_state[io_key]}**", key=f"io_toggle_{city}"):
                        st.session_state[io_key] = _["indoor"] if st.session_state[io_key] == _["outdoor"] else _["outdoor"]
                        st.rerun()

            # 등록 버튼 (왼쪽 끝)
            register_label = _["register"]
            if st.button(f"**{register_label}**", key=f"register_{city}"):
                if venue_name:
                    new_row = pd.DataFrame([{
                        'Venue': venue_name,
                        'Seats': seats,
                        'IndoorOutdoor': st.session_state[io_key],
                        'Google Maps Link': google_link
                    }])
                    target = st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
                    target[city] = pd.concat([target.get(city, pd.DataFrame()), new_row], ignore_index=True)
                    st.success("등록 완료")
                    st.rerun()
                else:
                    st.error("공연장 이름을 입력하세요.")

        # 공연장 목록
        df = st.session_state.admin_venues.get(city, pd.DataFrame()) if st.session_state.admin else st.session_state.venues.get(city, pd.DataFrame(columns=['Venue', 'Seats', 'IndoorOutdoor', 'Google Maps Link']))
        if not df.empty:
            for idx, row in df.iterrows():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**{row['Venue']}**")
                    st.caption(f"{row['Seats']} {_['seats']}")
                with col2:
                    color = "🟢" if row['IndoorOutdoor'] == _["indoor"] else "🔵"
                    st.write(f"{color} {row['IndoorOutdoor']}")
                with col3:
                    if row['Google Maps Link'].startswith("http"):
                        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={row['Google Maps Link']}&travelmode=driving"
                        st.markdown(f"[{_['drive_to']}]({maps_url})", unsafe_allow_html=True)
                with col4:
                    if st.session_state.admin or st.session_state.guest_mode:
                        if st.button(_["edit_venue"], key=f"edit_{city}_{idx}"):
                            st.session_state[f"edit_{city}_{idx}"] = True
                        if st.button(_["delete_venue"], key=f"del_{city}_{idx}"):
                            if st.checkbox(_["confirm_delete"], key=f"confirm_{city}_{idx}"):
                                target = st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
                                target[city] = target[city].drop(idx).reset_index(drop=True)
                                st.success("삭제 완료")
                                st.rerun()

                if st.session_state.get(f"edit_{city}_{idx}", False):
                    with st.form(key=f"edit_form_{city}_{idx}"):
                        ev = st.text_input("Venue", row['Venue'], key=f"ev_{city}_{idx}")
                        es = st.number_input("Seats", 1, value=row['Seats'], key=f"es_{city}_{idx}")
                        eio = st.selectbox("Type", [_[ "indoor" ], _["outdoor"]], index=0 if row['IndoorOutdoor'] == _["indoor"] else 1, key=f"eio_{city}_{idx}")
                        el = st.text_input("Google Link", row['Google Maps Link'], key=f"el_{city}_{idx}")
                        if st.form_submit_button("Save"):
                            target = st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
                            target[city].loc[idx] = [ev, es, eio, el]
                            del st.session_state[f"edit_{city}_{idx}"]
                            st.success("수정 완료")
                            st.rerun()

# =============================================
# 10. 지도 (점선 + 목적지 바로 앞 화살표)
# =============================================
st.markdown("---")
st.subheader(_["tour_map"])
center = coords.get(st.session_state.route[0] if st.session_state.route else 'Mumbai', (19.75, 75.71))
m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")

if len(st.session_state.route) > 1:
    points = [coords[c] for c in st.session_state.route]
    folium.PolyLine(points, color="red", weight=4, dash_array="10, 10").add_to(m)
    
    # 목적지 바로 앞에 화살표 (도착점에서 5% 전)
    for i in range(len(points) - 1):
        start = points[i]
        end = points[i + 1]
        # 도착점에서 5% 전 위치 계산
        arrow_lat = end[0] - (end[0] - start[0]) * 0.05
        arrow_lon = end[1] - (end[1] - start[1]) * 0.05
        folium.RegularPolygonMarker(
            location=[arrow_lat, arrow_lon],
            fill_color='red',
            number_of_sides=3,
            rotation=math.degrees(math.atan2(end[1] - start[1], end[0] - start[0])) - 90,
            radius=10
        ).add_to(m)

for city in st.session_state.route:
    df = st.session_state.admin_venues.get(city, pd.DataFrame()) if st.session_state.admin else st.session_state.venues.get(city, pd.DataFrame())
    link = next((r['Google Maps Link'] for _, r in df.iterrows() if r['Google Maps Link'].startswith('http')), None)
    popup = f"<b style='color:#8B0000'>{city}</b><br>{st.session_state.dates.get(city, 'TBD').strftime(_['date_format'])}"
    if link:
        popup = f'<a href="{link}" target="_blank" style="color:#90EE90">{popup}<br><i>{_["open_maps"]}</i></a>'
    folium.CircleMarker(coords[city], radius=15, color="#90EE90", fill_color="#8B0000", popup=folium.Popup(popup, max_width=300)).add_to(m)

folium_static(m, width=700, height=500)
st.caption(_["caption"])
