# ... (이전 코드 동일 – state, data, lang, cities, sidebar, theme, title, 일반 모드 생략)

# =============================================
# 관리자 모드
# =============================================
if st.session_state.admin:
    # 공지 입력 (최상단)
    st.markdown("---")
    st.subheader("공지사항 입력")
    notice_title = st.text_input(_["notice_title"])
    notice_content = st.text_area(_["notice_content"])
    uploaded_file = st.file_uploader(_["upload_file"], type=["png", "jpg", "jpeg", "pdf", "txt"])
    
    if st.button(_["notice_save"]):
        if notice_title and notice_content:
            file_b64 = None
            if uploaded_file:
                file_b64 = base64.b64encode(uploaded_file.read()).decode()
            new_notice = {
                "id": len(st.session_state.notice_data) + 1,
                "title": notice_title,
                "content": notice_content,
                "file": file_b64,
                "timestamp": str(datetime.now())
            }
            st.session_state.notice_data.insert(0, new_notice)
            save_notice_data(st.session_state.notice_data)
            st.success("공지 추가 완료")
            st.session_state.new_notice = True
            st.rerun()

    left, right = st.columns([1, 2])

    with left:
        c1, c2 = st.columns([3, 1])
        with c1:
            selected_city = st.selectbox(_["select_city"], cities)
        with c2:
            if st.button(_["add_city"]):
                if selected_city not in st.session_state.route:
                    st.session_state.route.append(selected_city)
                    st.session_state.exp_state[selected_city] = False
                    st.rerun()
                else:
                    st.warning(_["already_added"])

        st.markdown("---")
        st.subheader(_["tour_route"])

        total_distance = 0.0
        total_hours = 0.0

        for i, c in enumerate(st.session_state.route):
            expanded = st.session_state.exp_state.get(c, False)
            with st.expander(f"{c}", expanded=expanded):
                today = datetime.now().date()
                date = st.date_input(_["date"], value=today, min_value=today, key=f"date_{c}")
                venue = st.text_input(_["venue"], key=f"venue_{c}")
                seats = st.number_input(_["seats"], min_value=0, step=50, key=f"seats_{c}")
                google = st.text_input(_["google"], key=f"google_{c}")
                notes = st.text_area(_["notes"], key=f"notes_{c}")
                io = st.radio("Type", [_["indoor"], _["outdoor"]], key=f"io_{c}")

                if st.button(_["register"], key=f"reg_{c}"):
                    st.session_state.venue_data[c] = {
                        "date": str(date), "venue": venue, "seats": seats,
                        "type": io, "google": google, "notes": notes
                    }
                    save_venue_data(st.session_state.venue_data)
                    st.success("저장되었습니다.")
                    st.session_state.exp_state[c] = False
                    st.rerun()

            if i > 0:
                prev = st.session_state.route[i - 1]
                if prev in coords and c in coords:
                    dist = distance_km(coords[prev], coords[c])
                    time_hr = dist / 60.0
                    total_distance += dist
                    total_hours += time_hr
                    st.markdown(f"<p style='text-align:center; color:#90EE90; font-weight:bold;'>{dist:.1f} km / {time_hr:.1f} 시간</p>", unsafe_allow_html=True)

        if len(st.session_state.route) > 1:
            st.markdown("---")
            st.markdown(f"### {_['total']}")
            st.success(f"**{total_distance:.1f} km** | **{total_hours:.1f} 시간**")

    with right:
        st.subheader(_["tour_map"])
        try:
            GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        except:
            st.error("Google Maps API 키 없음")
            st.stop()

        m = folium.Map(location=(19.75, 75.71), zoom_start=6,
                       tiles=f"https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_API_KEY}",
                       attr="Google")

        points = [coords[c] for c in st.session_state.route if c in coords]
        if len(points) >= 2:
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]
                dist = distance_km(p1, p2)
                time_hr = dist / 60.0
                mid_lat = (p1[0] + p2[0]) / 2
                mid_lng = (p1[1] + p2[1]) / 2
                folium.Marker(
                    location=[mid_lat, mid_lng],
                    icon=folium.DivIcon(html=f"""
                        <div class="distance-label">
                            {dist:.1f} km / {time_hr:.1f} h
                        </div>
                    """)
                ).add_to(m)
            AntPath(points, color="red", weight=4, delay=800).add_to(m)

        for c in st.session_state.route:
            if c in coords:
                data = st.session_state.venue_data.get(c, {})
                popup = f"<b>{c}</b><br>"
                if "date" in data:
                    popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data['type']}<br>"
                if "google" in data and data["google"]:
                    lat, lng = re.search(r'@(\d+\.\d+),(\d+\.\d+)', data["google"]) or (None, None)
                    nav_link = f"https://www.google.com/maps/dir/?api=1&destination={lat.group(1)},{lng.group(1)}" if lat and lng else data["google"]
                    popup += f"<a href='{nav_link}' target='_blank'>네비 시작</a>"
                folium.Marker(coords[c], popup=popup,
                              icon=folium.Icon(color="red", icon="music", prefix="fa")).add_to(m)

        st_folium(m, width=900, height=650)

        # 오른쪽 최신순 공지 리스트 + X 버튼 삭제
        st.markdown("---")
        st.subheader("최신순 공지")
        if st.session_state.notice_data:
            for notice in st.session_state.notice_data:  # 최신순 (insert(0,)으로 이미 최신 위)
                col1, col2 = st.columns([9, 1])
                with col1:
                    st.write(f"**{notice['title']}**")
                with col2:
                    if st.button("X", key=f"delete_{notice['id']}"):
                        st.session_state.notice_data = [n for n in st.session_state.notice_data if n["id"] != notice["id"]]
                        save_notice_data(st.session_state.notice_data)
                        st.success("공지 삭제 완료")
                        st.rerun()
        else:
            st.write("공지가 없습니다.")
