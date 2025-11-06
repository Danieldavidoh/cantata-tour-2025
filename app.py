# app.py - 최종 패치 (2025.11.07) 🔥 화면 사라짐 완전 차단 + 마커·알림음·언어·관리자 ALL OK
# (이전 전체 코드에 아래 [핵심 패치]만 추가/교체)

# ... (import ~ render_notices() 동일) ...

# ==================== [11] 지도 & 투어 경로 (화면 사라짐 + 마커 완벽 복구) ====================
def render_map():
    st.subheader(_('map_title'))
    
    # --- 도시 추가 버튼 (관리자만) ---
    if st.session_state.admin:
        if st.button(_('add_city'), key="add_city_btn"):
            st.session_state.adding_cities.append(None)
            st.rerun()

    # --- 도시 데이터 로드 ---
    cities = sorted(load_json(CITY_FILE), key=lambda x: x.get("perf_date", "9999-12-31"))
    if not cities:
        st.info("⚠️ 등록된 도시가 없습니다. 관리자가 도시를 추가해주세요.")
        return  # 빈 지도 방지

    total_dist = 0
    city_details = []  # 화면 유지용 임시 저장

    # --- 도시 목록 + 거리 계산 ---
    for i, c in enumerate(cities):
        with st.expander(f"🎄 {c['city']} | {c.get('perf_date', '미정')}", expanded=False):
            st.write(f"📅 등록일: {c.get('date', '—')}")
            st.write(f"🎭 공연 날짜: {c.get('perf_date', '—')}")
            st.write(f"🏟️ 공연장소: {c.get('venue', '—')}")
            st.write(f"👥 예상 인원: {c.get('seats', '—')}명")
            st.write(f"📝 특이사항: {c.get('note', '—')}")

            # --- 관리자 버튼 ---
            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✏️ 수정", key=f"edit_{i}_{c['city']}"):
                        st.session_state.edit_city = c["city"]
                        st.rerun()
                with c2:
                    if st.button("🗑️ 삭제", key=f"del_{i}_{c['city']}"):
                        cities.pop(i)
                        save_json(CITY_FILE, cities)
                        st.rerun()

        # --- 거리 계산 ---
        if i < len(cities) - 1:
            d = haversine(c['lat'], c['lon'], cities[i+1]['lat'], cities[i+1]['lon'])
            total_dist += d
            st.markdown(f"<div style='text-align:center; color:#2ecc71; font-weight:bold;'>📍 {d:.0f}km →</div>", unsafe_allow_html=True)

        # --- 지도용 좌표 저장 ---
        city_details.append({
            "lat": c["lat"], "lon": c["lon"], "city": c["city"],
            "date": c.get("perf_date", ""), "venue": c.get("venue", ""),
            "seats": c.get("seats", ""), "note": c.get("note", "")
        })

    # --- 총 거리 표시 ---
    if len(cities) > 1:
        st.markdown(f"<div style='text-align:center; color:#e74c3c; font-size:1.3em; font-weight:bold; margin:15px 0;'>🎅 총 투어 거리: {total_dist:.0f}km 🎄</div>", unsafe_allow_html=True)

    # --- Folium 지도 (화면 사라짐 방지 핵심!) ---
    # 고유 키 + returned_objects=None + height 강제 지정
    map_key = f"map_{len(cities)}_{total_dist}"
    m = folium.Map(
        location=[19.0, 73.0],
        zoom_start=7,
        tiles="CartoDB positron",  # 부드러운 크리스마스 톤
        prefer_canvas=True
    )

    coords = []
    for idx, c in enumerate(city_details):
        # 🎄 크리스마스 트리 아이콘
        icon = folium.Icon(color="red", icon="tree-christmas", prefix="fa", icon_color="white")
        popup_html = f"""
        <div style="font-family:Arial; min-width:200px;">
            <b style="font-size:1.2em; color:#e74c3c;">🎄 {c['city']}</b><br>
            📅 {c['date'] or '미정'}<br>
            🎭 {c['venue'] or '—'}<br>
            👥 {c['seats'] or '—'}명<br>
            📝 {c['note'] or '—'}
        </div>
        """
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"🎄 {c['city']}",
            icon=icon
        ).add_to(m)
        coords.append((c["lat"], c["lon"]))

    # --- 경로선 (산타 썰매 애니메이션) ---
    if len(coords) > 1:
        AntPath(
            coords,
            color="#e74c3c",
            weight=6,
            opacity=0.9,
            delay=800,
            dash_array=[10, 20],
            pulse_color="#ff6b6b"
        ).add_to(m)

    # --- 지도 렌더링 (화면 유지 핵심!) ---
    st_folium(
        m,
        width=900,
        height=550,
        key=map_key,              # 고유 키 → 리렌더링 충돌 방지
        returned_objects=[]       # 불필요한 반환값 제거 → 깜빡임/사라짐 차단
    )

# ==================== [12] 탭 + 강제 이동 (탭 전환 시 화면 유지) ====================
tab1, tab2 = st.tabs([_("tab_notice"), _("tab_map")])

# 새 공지 시 공지 탭 강제 이동
if st.session_state.get("new_notice", False):
    st.session_state.active_tab = "공지"
    st.session_state.new_notice = False
    st.rerun()  # 강제 리렌더

with tab1:
    if st.session_state.get("active_tab") == "공지" or st.session_state.new_notice:
        if st.session_state.admin:
            with st.form("notice_form", clear_on_submit=True):
                t = st.text_input(_("title_label"))
                c = st.text_area(_("content_label"))
                img = st.file_uploader(_("upload_image"), type=["png","jpg","jpeg"])
                f = st.file_uploader(_("upload_file"))
                if st.form_submit_button(_("submit")):
                    if t.strip() and c.strip():
                        add_notice(t, c, img, f)
                    else:
                        st.warning(_("warning"))
        render_notices()

with tab2:
    # 탭 전환 시 무조건 지도 렌더
    render_map()
