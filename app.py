# ... (이전 코드 생략) ...

# --- 탭 구성 ---
tab1, tab2 = st.tabs([_("tab_notice"), _("tab_map")])

# =============================================================================
# 탭 1: 공지사항 (Notice)
# =============================================================================
with tab1:
    # ... (탭 1 내용 생략) ...

# =============================================================================
# 탭 2: 투어 경로 (Map)
# =============================================================================
with tab2:
    st.subheader(f"🗺️ {_('tab_map')}")
    
    # --- 관리자: 투어 일정 관리 ---
    if st.session_state.admin:
        st.markdown(f"**{_('register')} {_('tab_map')} {_('set_data')}**")
        
        # --- 일정 등록 폼 ---
        with st.expander(_("add_city"), expanded=False):
            with st.form("schedule_form", clear_on_submit=True):
                col_c, col_d, col_v = st.columns(3)
                
                # "공연없음"이 제거된 city_options 사용
                city_name_input = col_c.selectbox(_('city_name'), options=city_options, index=0, key="new_city_select")
                schedule_date = col_d.date_input(_("date"), key="new_date_input")
                venue_name = col_v.text_input(_("venue"), placeholder=_("venue_placeholder"), key="new_venue_input")
                
                # NEW: 가능성(%) 필드 추가
                col_l, col_s, col_n, col_p = st.columns(4)
                
                type_options_map = {_("indoor"): "indoor", _("outdoor"): "outdoor"} # Display -> Internal Key
                selected_display_type = col_l.radio(_("type"), list(type_options_map.keys()))
                type_sel = type_options_map[selected_display_type] # Internal key
                
                # 예상인원 기본값을 500으로, step을 50으로 변경
                expected_seats = col_s.number_input(_("seats"), min_value=0, value=500, step=50, help=_("seats_tooltip"))
                google_link = col_n.text_input(_("google_link"), placeholder=_("google_link_placeholder"))
                
                # NEW: 가능성 슬라이더
                probability = col_p.slider(_("probability"), min_value=0, max_value=100, value=100, step=5)


                note = st.text_area(_("note"), placeholder=_("note_placeholder"))
                
                submitted = st.form_submit_button(_("register"))
                
                if submitted:
                    if not city_name_input or not venue_name or not schedule_date:
                        pass
                    elif city_name_input not in city_dict:
                        pass
                    else:
                        # NEW: 도시/날짜 중복 검사
                        is_duplicate = any(
                            s.get('city') == city_name_input and s.get('date') == schedule_date.strftime("%Y-%m-%d")
                            for s in tour_schedule
                        )
                        
                        if is_duplicate:
                            pass
                        else:
                            coords = city_dict[city_name_input]
                            new_schedule_entry = {
                                "id": str(uuid.uuid4()),
                                "city": city_name_input,
                                "venue": venue_name,
                                "lat": coords["lat"],
                                "lon": coords["lon"],
                                "date": schedule_date.strftime("%Y-%m-%d"),
                                "type": type_sel, # Internal key로 저장
                                "seats": str(expected_seats),
                                "note": note,
                                "google_link": google_link,
                                "probability": probability, # NEW: 가능성 저장
                                "reg_date": datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
                            }
                            tour_schedule.append(new_schedule_entry)
                            save_json(CITY_FILE, tour_schedule)
                            safe_rerun()
        
        # --- 관리자: 일정 보기, 수정/삭제 및 전체 삭제 ---
        valid_schedule = [
            item 
            for item in tour_schedule 
            if isinstance(item, dict) and item.get('id') and item.get('city') and item.get('venue')
        ]
        
        if valid_schedule:
            st.subheader(_("tour_schedule_management"))
            
            # **수정된 부분: 전체 삭제 버튼 추가**
            col_manage_title, col_manage_delete = st.columns([5, 1])
            with col_manage_title:
                st.markdown(f"**{_('existing_notices')}**") # 레이블 변경
            with col_manage_delete:
                # 전체 일정 제거 버튼 (확인 절차 없이 즉시 제거)
                if st.button(_("remove"), help="전체 투어 일정을 제거합니다.", key="delete_all_schedule"):
                    tour_schedule.clear()
                    save_json(CITY_FILE, tour_schedule)
                    safe_rerun()


            schedule_dict = {item['id']: item for item in valid_schedule}
            sorted_schedule_items = sorted(schedule_dict.items(), key=lambda x: x[1].get('date', '9999-12-31'))
            type_options_map_rev = {"indoor": _("indoor"), "outdoor": _("outdoor")} # Internal Key -> Display

            for item_id, item in sorted_schedule_items:
                translated_type = type_options_map_rev.get(item.get('type', 'outdoor'), _("outdoor"))
                probability_val = item.get('probability', 100) # NEW: 확률 값 가져오기
                
                header_text = f"[{item.get('date', 'N/A')}] {item['city']} - {item['venue']} ({translated_type}) | {_('probability')}: {probability_val}%"

                with st.expander(header_text, expanded=False):
                    # **수정된 부분: 수정/삭제 버튼 레이아웃 조정**
                    col_u, col_d = st.columns([1, 5])
                    
                    with col_u:
                        if st.button(_("update"), key=f"upd_s_{item_id}"):
                            st.session_state[f"edit_mode_{item_id}"] = True
                            safe_rerun()
                        if st.button(_("remove"), key=f"del_s_{item_id}"):
                            tour_schedule[:] = [s for s in tour_schedule if s.get('id') != item_id]
                            save_json(CITY_FILE, tour_schedule)
                            safe_rerun()

                    if st.session_state.get(f"edit_mode_{item_id}"):
                        with st.form(f"edit_form_{item_id}"):
                            col_uc, col_ud, col_uv = st.columns(3)
                            
                            try:
                                initial_date = datetime.strptime(item.get('date', '2025-01-01'), "%Y-%m-%d").date()
                            except ValueError:
                                initial_date = date.today()
                                
                            updated_city = col_uc.selectbox(_("city"), city_options, index=city_options.index(item.get('city', "Pune") if item.get('city') in city_options else city_options[0]))
                            updated_date = col_ud.date_input(_("date"), value=initial_date)
                            updated_venue = col_uv.text_input(_("venue"), value=item.get('venue'))
                            
                            col_ul, col_us, col_ug, col_up = st.columns(4) # NEW: 4개 컬럼
                            current_map_type = item.get('type', 'outdoor')
                            current_map_index = 0 if current_map_type == "indoor" else 1
                            map_type_list = list(type_options_map_rev.values())
                            updated_display_type = col_ul.radio(_("type"), map_type_list, index=current_map_index, key=f"update_map_type_{item_id}")
                            updated_type = "indoor" if updated_display_type == _("indoor") else "outdoor"
                            
                            seats_value = item.get('seats', '0')
                            updated_seats = col_us.number_input(_("seats"), min_value=0, value=int(seats_value) if str(seats_value).isdigit() else 500, step=50)
                            updated_google = col_ug.text_input(_("google_link"), value=item.get('google_link', ''))

                            # NEW: 가능성 슬라이더
                            updated_probability = col_up.slider(_("probability"), min_value=0, max_value=100, value=item.get('probability', 100), step=5)

                            updated_note = st.text_area(_("note"), value=item.get('note'))
                            
                            if st.form_submit_button(_("update")):
                                for idx, s in enumerate(tour_schedule):
                                    if s.get('id') == item_id:
                                        coords = city_dict.get(updated_city, {'lat': s.get('lat', 0), 'lon': s.get('lon', 0)})
                                        
                                        tour_schedule[idx] = {
                                            "id": item_id,
                                            "city": updated_city,
                                            "venue": updated_venue,
                                            "lat": coords["lat"],
                                            "lon": coords["lon"],
                                            "date": updated_date.strftime("%Y-%m-%d"),
                                            "type": updated_type,
                                            "seats": str(updated_seats),
                                            "note": updated_note,
                                            "google_link": updated_google,
                                            "probability": updated_probability, # NEW: 가능성 저장
                                            "reg_date": s.get('reg_date', datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S"))
                                        }
                                        save_json(CITY_FILE, tour_schedule)
                                        st.session_state[f"edit_mode_{item_id}"] = False
                                        safe_rerun()
                    
                    if not st.session_state.get(f"edit_mode_{item_id}"):
                        st.markdown(f"**{_('date')}:** {item.get('date', 'N/A')} ({item.get('reg_date', '')})")
                        st.markdown(f"**{_('venue')}:** {item.get('venue', 'N/A')}")
                        st.markdown(f"**{_('seats')}:** {item.get('seats', 'N/A')}")
                        st.markdown(f"**{_('type')}:** {translated_type}")
                        st.markdown(f"**{_('probability')}:** {probability_val}%") # NEW: 가능성 표시
                        if item.get('google_link'):
                            google_link_url = item['google_link'] 
                            st.markdown(f"**{_('google_link')}:** [{_('google_link')}]({google_link_url})")
                        st.markdown(f"**{_('note')}:** {item.get('note', 'N/A')}")
        else:
            st.write(_("no_schedule"))

        # --- 지도 표시 (사용자 & 관리자 공통) ---
        # ... (지도 그리기 로직 생략 - 변경 없음) ...
        current_date = date.today()
        schedule_for_map = sorted([
            s for s in tour_schedule 
            if s.get('date') and s.get('lat') is not None and s.get('lon') is not None and s.get('id')
        ], key=lambda x: x['date'])
        
        # 수정: 기본 중심 좌표를 Aurangabad로 설정
        AURANGABAD_COORDS = city_dict.get("Aurangabad", {'lat': 19.876165, 'lon': 75.343314})
        start_coords = [AURANGABAD_COORDS['lat'], AURANGABAD_COORDS['lon']]
        
        m = folium.Map(location=start_coords, zoom_start=8)
        locations = []
        
        for item in schedule_for_map:
            lat = item['lat']
            lon = item['lon']
            date_str = item['date']
            
            try:
                event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                event_date = current_date + timedelta(days=365)
                
            is_past = event_date < current_date
            
            # 요청 반영: 아이콘 색상은 항상 빨간색
            icon_color = '#BB3333' # 버건디 레드 계열
            
            # 요청 반영: 지난 도시는 25% 투명도
            opacity_val = 0.25 if is_past else 1.0
            
            # 팝업 내용 (번역 및 실내/실외, 구글맵 포함)
            type_options_map_rev = {"indoor": _("indoor"), "outdoor": _("outdoor")} # Internal Key -> Display
            translated_type = type_options_map_rev.get(item.get('type', 'outdoor'), _("outdoor"))
            map_type_icon = '🏠' if item.get('type') == 'indoor' else '🌳'
            probability_val = item.get('probability', 100) # NEW: 확률 값 가져오기
            
            # --- 수정된 부분: 도시 이름을 빨간색으로 표시 ---
            city_name_display = item.get('city', 'N/A')
            red_city_name = f'<span style="color: #BB3333; font-weight: bold;">{city_name_display}</span>'
            
            # NEW: 막대 그래프 HTML 생성
            bar_color = "red" if probability_val < 50 else "gold" if probability_val < 90 else "#66BB66" # Green
            
            prob_bar_html = f"""
            <div style="margin-top: 5px;">
                <b>{_('probability')}:</b>
                <div style="width: 100%; height: 10px; background-color: #333; border-radius: 5px; overflow: hidden; margin-top: 3px;">
                    <div style="width: {probability_val}%; height: 100%; background-color: {bar_color};"></div>
                </div>
                <span style="font-size: 12px; font-weight: bold; color: {bar_color};">{probability_val}%</span>
            </div>
            """
            
            popup_html = f"""
            <div style="color: #FAFAFA; background-color: #1A1A1A; padding: 10px; border-radius: 8px;">
                <b>{_('city')}:</b> {red_city_name}<br>
                <b>{_('date')}:</b> {date_str}<br>
                <b>{_('venue')}:</b> {item.get('venue', 'N/A')}<br>
                <b>{_('type')}:</b> {map_type_icon} {translated_type}<br>
                {prob_bar_html}
            """
            
            if item.get('google_link'):
                google_link_url = item['google_link'] 
                popup_html += f'<a href="{google_link_url}" target="_blank" style="color: #FFD700; text-decoration: none; display: block; margin-top: 5px;">{_("google_link")}</a>'
            
            popup_html += "</div>" # 팝업 전체 닫기
            
            # 요청 반영: DivIcon을 사용하여 2/3 크기 (scale 0.666) 아이콘으로 조정 (항상 빨간색)
            city_initial = item.get('city', 'A')[0]
            marker_icon_html = f"""
                <div style="
                    transform: scale(0.666); 
                    opacity: {opacity_val};
                    text-align: center;
                    white-space: nowrap;
                ">
                    <i class="fa fa-map-marker fa-3x" style="color: {icon_color};"></i>
                    <div style="font-size: 10px; color: black; font-weight: bold; position: absolute; top: 12px; left: 13px;">{city_initial}</div>
                </div>
            """
            
            # 요청 반영: 말풍선 터치 시 나오는 작은 말풍선 제거 (tooltip 제거)
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.DivIcon(
                    icon_size=(30, 45),
                    icon_anchor=(15, 45),
                    html=marker_icon_html
                )
            ).add_to(m)
            
            locations.append([lat, lon])

        # 4. AntPath (경로 애니메이션) - 과거/미래 분리 및 스타일 적용
        if len(locations) > 1:
            current_index = -1
            for i, item in enumerate(schedule_for_map):
                try:
                    event_date = datetime.strptime(item['date'], "%Y-%m-%d").date()
                    if event_date >= current_date:
                        current_index = i
                        break
                except ValueError:
                    continue
            
            if current_index == -1: 
                past_segments = locations
                future_segments = []
            elif current_index == 0: 
                past_segments = []
                future_segments = locations
            else: 
                past_segments = locations[:current_index + 1]
                future_segments = locations[current_index:]

            # 요청 반영: 지난 도시/라인 25% 투명도의 빨간색 선
            if len(past_segments) > 1:
                folium.PolyLine(
                    locations=past_segments,
                    color="#BB3333",
                    weight=5,
                    opacity=0.25, # 25% 투명도
                    tooltip=_("past_route")
                ).add_to(m)
                
            # Future segments (animated line and individual PolyLines for tooltip)
            if len(future_segments) > 1:
                # 1. AntPath for the continuous animation effect (속도 1/2 조정)
                AntPath(
                    future_segments, 
                    use="regular", 
                    # dash_array를 수정하여 화살표 모양으로 시뮬레이션
                    dash_array='30, 20', # 화살표 모양을 위한 점선 길이 조정
                    color='#BB3333', 
                    weight=5, 
                    opacity=0.8,
                    # dash_factor를 음수로 설정하여 역방향 이동 효과 (<<<<< 모양) 시뮬레이션
                    options={"delay": 24000, "dash_factor": -0.1, "color": "#BB3333"} 
                ).add_to(m)

                # 2. Add invisible PolyLines for hover tooltips on each segment
                for i in range(len(future_segments) - 1):
                    p1 = future_segments[i]
                    p2 = future_segments[i+1]
                    
                    # 거리 및 시간 계산
                    segment_info = calculate_distance_and_time(p1, p2)
                    
                    # 투명한 PolyLine을 생성하여 툴팁 영역으로 사용 (쉬운 터치/호버 감지)
                    folium.PolyLine(
                        locations=[p1, p2],
                        color="transparent", 
                        weight=15, # 두껍게 하여 호버 영역 확장
                        opacity=0, 
                        tooltip=folium.Tooltip(
                            segment_info, 
                            permanent=False, 
                            direction="top", 
                            sticky=True,
                            style="background-color: #2D2D2D; color: #FAFAFA; padding: 5px; border-radius: 5px;"
                        )
                    ).add_to(m)
            
        elif locations:
            # 단일 도시일 때도 25% 투명도 적용
            try:
                single_item_date = datetime.strptime(schedule_for_map[0]['date'], "%Y-%m-%d").date()
                single_is_past = single_item_date < current_date
            except ValueError:
                single_is_past = False
                
            folium.Circle(
                location=locations[0],
                radius=1000,
                color='#BB3333',
                fill=True,
                fill_color='#BB3333',
                fill_opacity=0.25 if single_is_past else 0.8,
                tooltip=_("single_location")
            ).add_to(m)

        # 지도 표시
        st_folium(m, width=1000, height=600)
        
        # 지도 아래 불필요한 텍스트 제거 완료


# ... (이하 CSS 생략) ...
