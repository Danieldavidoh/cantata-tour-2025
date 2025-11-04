# ... (이전 코드 동일 – state, data, lang, cities, sidebar, theme, title 생략)

# =============================================
# 일반 모드
# =============================================
if not st.session_state.admin:
    # 공지현황 버튼
    if st.button("공지현황", key="notice_status_btn"):
        st.session_state.show_notice_list = True
        st.rerun()

    # 지도
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

    # 공지현황 박스 (아래 열림, X 삭제 없음)
    if st.session_state.show_notice_list:
        st.markdown(f"""
        <div id="notice-box">
            <button id="exit-button" onclick="document.getElementById('close_notice_list_hidden').click();">X</button>
            <div style="margin-top: 50px;">
        """, unsafe_allow_html=True)
        
        today_notices = [n for n in st.session_state.notice_data if datetime.strptime(n["timestamp"].split('.')[0], "%Y-%m-%d %H:%M:%S").date() == datetime.now().date()]
        for notice in today_notices:
            if st.button(notice["title"], key=f"user_notice_{notice['id']}"):
                st.session_state.show_full_notice = notice["id"]
                st.rerun()
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        if st.button("", key="close_notice_list_hidden"):
            st.session_state.show_notice_list = False
            st.rerun()

    # 전체 화면 공지
    if st.session_state.show_full_notice is not None:
        notice = next((n for n in st.session_state.notice_data if n["id"] == st.session_state.show_full_notice), None)
        if notice:
            content = notice["content"]
            if "file" in notice and notice["file"]:
                content += f"<br><img src='data:image/png;base64,{notice['file']}' style='max-width:100%;'>"

            close_clicked = st.button("", key="close_full_notice_hidden")
            if close_clicked:
                st.session_state.show_full_notice = None
                st.rerun()

            st.markdown(f"""
            <div id="full-screen-notice" onclick="document.getElementById('close_full_notice_hidden').click();">
                <button id="exit-button" onclick="event.stopPropagation(); document.getElementById('close_full_notice_hidden').click();">X</button>
                <div id="full-screen-notice-content" onclick="event.stopPropagation();">
                    <h3>{notice['title']}</h3>
                    <div>{content}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.stop()

# =============================================
# 관리자 모드
# =============================================
if st.session_state.admin:
    # 공지 입력
    st.markdown("---")
    st.subheader("공지사항 입력")
    
    col_input, col_button = st.columns([4, 1])
    with col_input:
        notice_title = st.text_input(_["notice_title"], key="notice_title_input")
        notice_content = st.text_area(_["notice_content"], key="notice_content_input")
        uploaded_file = st.file_uploader(_["upload_file"], type=["png", "jpg", "jpeg", "pdf", "txt"], key="notice_file_input")
    
    with col_button:
        st.write("")  # 공간
        st.write("")  # 공간
        if st.button("등록", key="register_notice_btn"):
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
                st.success("공지 등록 완료")
                st.session_state.new_notice = True
                st.rerun()
            else:
                st.error("제목과 내용을 입력하세요.")

    # 공지현황 박스
    with st.expander("공지현황", expanded=False):
        if st.session_state.notice_data:
            for notice in st.session_state.notice_data:
                col1, col2 = st.columns([9, 1])
                with col1:
                    if st.button(notice["title"], key=f"admin_notice_{notice['id']}"):
                        st.session_state.show_full_notice = notice["id"]
                        st.rerun()
                with col2:
                    if st.button("X", key=f"delete_notice_{notice['id']}"):
                        st.session_state.notice_data = [n for n in st.session_state.notice_data if n["id"] != notice["id"]]
                        save_notice_data(st.session_state.notice_data)
                        st.success("공지 삭제 완료")
                        st.rerun()
        else:
            st.write("공지가 없습니다.")

    # 전체 화면 공지 (관리자 클릭 시)
    if st.session_state.show_full_notice is not None:
        notice = next((n for n in st.session_state.notice_data if n["id"] == st.session_state.show_full_notice), None)
        if notice:
            content = notice["content"]
            if "file" in notice and notice["file"]:
                content += f"<br><img src='data:image/png;base64,{notice['file']}' style='max-width:100%;'>"

            close_clicked = st.button("", key="close_full_notice_hidden")
            if close_clicked:
                st.session_state.show_full_notice = None
                st.rerun()

            st.markdown(f"""
            <div id="full-screen-notice" onclick="document.getElementById('close_full_notice_hidden').click();">
                <button id="exit-button" onclick="event.stopPropagation(); document.getElementById('close_full_notice_hidden').click();">X</button>
                <div id="full-screen-notice-content" onclick="event.stopPropagation();">
                    <h3>{notice['title']}</h3>
                    <div>{content}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # (도시 입력, 지도 코드 생략 – 이전 유지)
