# --- 버튼 라인 아래에 초기 화면 구성 시작 ---
st.markdown("<div class='main-content'>", unsafe_allow_html=True)

# === 초기 화면: 아무것도 안 보이게, 버튼만 유지 ===
# 공지와 지도는 버튼 클릭 시에만 열리도록
# 초기에는 notice_open = False, map_open = False 로 시작

# --- 공지 섹션 (초기 접힘) ---
if st.session_state.notice_open:
    st.markdown("## 📢 " + _("tab_notice"))
    if st.session_state.admin:
        with st.expander("✍️ " + "공지 작성", expanded=False):
            with st.form("notice_form", clear_on_submit=True):
                title = st.text_input("제목", key="notice_title")
                content = st.text_area("내용", key="notice_content")
                img = st.file_uploader("이미지", type=["png", "jpg", "jpeg"], key="notice_img")
                file = st.file_uploader("첨부 파일", key="notice_file")
                if st.form_submit_button("등록"):
                    if title.strip() and content.strip():
                        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
                        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
                        if img: open(img_path, "wb").write(img.getbuffer())
                        if file: open(file_path, "wb").write(file.getbuffer())
                        notice = {
                            "id": str(uuid.uuid4()),
                            "title": title,
                            "content": content,
                            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
                            "image": img_path,
                            "file": file_path
                        }
                        data = load_json(NOTICE_FILE)
                        data.insert(0, notice)
                        save_json(NOTICE_FILE, data)
                        st.success("공지 등록 완료!")
                        st.rerun()
                    else:
                        st.warning(_("warning"))

    data = load_json(NOTICE_FILE)
    if not data:
        st.info("아직 등록된 공지가 없습니다.")
    else:
        for i, n in enumerate(data):
            with st.expander(f"📅 {n['date']} | {n['title']}", expanded=False):
                st.markdown(n["content"])
                if n.get("image") and os.path.exists(n["image"]):
                    st.image(n["image"], use_column_width=True)
                if n.get("file") and os.path.exists(n["file"]):
                    b64 = base64.b64encode(open(n["file"], "rb").read()).decode()
                    st.markdown(
                        f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(n["file"])}">'
                        f'📎 다운로드: {os.path.basename(n["file"])}</a>',
                        unsafe_allow_html=True
                    )
                if st.session_state.admin and st.button(_("delete"), key=f"del_n_{n['id']}"):
                    data.pop(i)
                    save_json(NOTICE_FILE, data)
                    st.rerun()

# --- 지도 섹션 (초기 접힘) ---
if st.session_state.map_open:
    st.markdown("## 🗺️ " + _("tab_map"))
    cities = load_json(CITY_FILE)
    if not cities:
        st.warning("등록된 도시가 없습니다.")
    else:
        m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="OpenStreetMap")
        for i, c in enumerate(cities):
            coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
            lat, lon = coords
            is_future = c.get("perf_date", "9999-12-31") >= str(date.today())
            color = "red" if is_future else "gray"
            indoor_text = _("indoor") if c.get("indoor") else _("outdoor")
            popup_html = f"""
            <div style='font-size:14px; line-height:1.6; font-family: sans-serif;'>
                <b>{c['city']}</b><br>
                📅 {_('perf_date')}: {c.get('perf_date','미정')}<br>
                🎭 {_('venue')}: {c.get('venue','—')}<br>
                👥 {_('seats')}: {c.get('seats','—')}<br>
                🏠 {indoor_text}<br>
                <a href='https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving' target='_blank'>
                    🧭 {_('google_link')}
                </a>
            </div>
            """
            folium.Marker(
                coords,
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=color, icon="music", prefix="fa")
            ).add_to(m)

            if i < len(cities) - 1:
                nxt_coords = CITY_COORDS.get(cities[i+1]["city"], (18.5204, 73.8567))
                AntPath(
                    [coords, nxt_coords],
                    color="#e74c3c",
                    weight=6,
                    opacity=1.0 if is_future else 0.3,
                    delay=600
                ).add_to(m)

        st_folium(m, width=900, height=550, key="tour_map")

# --- 초기 화면: 아무것도 안 보일 때 환영 메시지 (선택) ---
if not st.session_state.notice_open and not st.session_state.map_open:
    st.markdown("""
    <div style='text-align:center; margin-top: 40px; padding: 30px; background: rgba(255,255,255,0.1); border-radius: 20px; backdrop-filter: blur(5px);'>
        <h2 style='color: #fff; text-shadow: 0 0 10px rgba(255,255,255,0.5);'>
            🎄 환영합니다! 🎄
        </h2>
        <p style='color: #ddd; font-size: 1.2em;'>
            위 버튼을 눌러 <b>공지사항</b> 또는 <b>투어 일정</b>을 확인하세요.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # .main-content 종료
