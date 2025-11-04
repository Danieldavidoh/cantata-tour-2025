# ... (이전 코드 동일 – state, data, lang, cities, sidebar 생략)

# =============================================
# Theme (화면 위로 올리기)
# =============================================
st.markdown("""
<style>
.stApp { 
    background: radial-gradient(circle at 20% 20%, #0a0a0f 0%, #000000 100%); 
    color: #ffffff; 
    margin-top: -120px;  /* 칸타타투어 반만큼 위로 올림 */
}
h1 { 
    color: #ff3333 !important; 
    text-align: center; 
    font-weight: 900; 
    font-size: 4.3em; 
    text-shadow: 0 0 25px #b71c1c, 0 0 15px #00ff99; 
}
h1 span.year { color: #ffffff; font-weight: 800; font-size: 0.8em; vertical-align: super; }
h1 span.subtitle { color: #cccccc; font-size: 0.45em; vertical-align: super; margin-left: 5px; }
/* ... (기존 스타일 생략) */
</style>
""", unsafe_allow_html=True)

# =============================================
# Title
# =============================================
st.markdown(f"<h1>{_['title']} <span class='year'>2025</span><span class='subtitle'>마하라스트라</span> 🎄</h1>", unsafe_allow_html=True)

# =============================================
# 일반 모드
# =============================================
if not st.session_state.admin:
    # 투어지도
    with st.expander("투어지도", expanded=False):
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
                    match = re.search(r'@(\d+\.\d+),(\d+\.\d+)', data["google"])
                    lat, lng = (match.group(1), match.group(2)) if match else (None, None)
                    nav_link = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}" if lat and lng else data["google"]
                    popup += f"<a href='{nav_link}' target='_blank'>네비 시작</a>"
                folium.Marker(coords[c], popup=popup,
                              icon=folium.Icon(color="red", icon="music", prefix="fa")).add_to(m)

        st_folium(m, width=900, height=650)

    # 투어지도 아래 공지현황 버튼 (X 삭제 없음)
    st.markdown("---")
    with st.expander("공지현황", expanded=False):
        if st.session_state.notice_data:
            for notice in st.session_state.notice_data:
                if st.button(notice["title"], key=f"user_notice_{notice['id']}"):
                    st.session_state.show_full_notice = notice["id"]
                    st.rerun()
        else:
            st.write("공지가 없습니다.")

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
# 관리자 모드 (생략 – 이전 유지)
# =============================================
