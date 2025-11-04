# ... (이전 코드 동일 – 데이터, 언어, 도시, state, sidebar, theme, title, 관리자 모드 생략)

# =============================================
# 일반 모드
# =============================================
if not st.session_state.admin:
    # 공지 버튼 (모바일 고정)
    neon_class = "neon" if st.session_state.new_notice else ""
    button_label = f"{_['new_notice']} 📢" if st.session_state.new_notice else _["notice_button"]
    st.markdown(f"""
    <div id="notice-button" class="{neon_class}" onclick="document.getElementById('notice_btn_hidden').click();">
        {button_label}
    </div>
    """, unsafe_allow_html=True)
    if st.button("", key="notice_btn_hidden"):
        st.session_state.show_notice_list = not st.session_state.show_notice_list
        if st.session_state.new_notice:
            st.session_state.new_notice = False
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

    # 공지 리스트 (지도 위 고정)
    if st.session_state.show_notice_list:
        st.markdown(f"""
        <div id="notice-list">
            <h4>{_['notices']}</h4>
        """, unsafe_allow_html=True)
        today_notices = [n for n in st.session_state.notice_data if datetime.strptime(n["timestamp"].split('.')[0], "%Y-%m-%d %H:%M:%S").date() == datetime.now().date()]
        for notice in today_notices:
            if st.button(notice["title"], key=f"notice_{notice['id']}"):
                st.session_state.show_full_notice = notice["id"]
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 전체 화면 공지 (전체 클릭 시 닫힘 – 버튼 제거)
    if st.session_state.show_full_notice is not None:
        notice = next((n for n in st.session_state.notice_data if n["id"] == st.session_state.show_full_notice), None)
        if notice:
            content = notice["content"]
            if "file" in notice and notice["file"]:
                content += f"<br><img src='data:image/png;base64,{notice['file']}' style='max-width:100%;'>"
            st.markdown(f"""
            <div id="full-screen-notice" onclick="document.getElementById('close_full_notice_hidden').click();">
                <div id="full-screen-notice-content" onclick="event.stopPropagation();">
                    <h3>{notice['title']}</h3>
                    <div>{content}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # 숨겨진 버튼으로 Streamlit 상태 업데이트
            if st.button("", key="close_full_notice_hidden"):
                st.session_state.show_full_notice = None
                st.rerun()

    # 새 공지 팝업 (전체 클릭 시 닫힘)
    if st.session_state.new_notice and st.session_state.show_popup:
        st.markdown("""
        <audio autoplay>
            <source src="https://www.soundjay.com/holiday/christmas-bells-1.mp3" type="audio/mpeg">
        </audio>
        <script>
            setTimeout(() => { document.querySelector('audio').pause(); }, 5000);
        </script>
        """, unsafe_allow_html=True)
        latest = st.session_state.notice_data[0]
        st.markdown(f"""
        <div id="full-screen-notice" onclick="document.getElementById('close_popup_hidden').click();">
            <div id="full-screen-notice-content" onclick="event.stopPropagation();">
                <h3>{latest['title']}</h3>
                <p>{latest['content']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("", key="close_popup_hidden"):
            st.session_state.show_popup = False
            st.rerun()

    st.stop()

# =============================================
# 관리자 모드 (이전 코드 유지)
# =============================================
# (이전 관리자 코드 그대로)
