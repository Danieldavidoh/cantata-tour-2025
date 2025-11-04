# ... (이전 코드 동일 – state, data, lang, cities, sidebar, theme, title 생략)

# =============================================
# 일반 모드
# =============================================
if not st.session_state.admin:
    # 투어지도
    with st.expander("투어지도", expanded=False):
        # ... (지도 코드 생략)

    # 투어지도 아래 공지현황 버튼 (말풍선)
    st.markdown("---")
    notice_expander = st.expander("공지현황", expanded=False)
    with notice_expander:
        if st.session_state.notice_data:
            # 유니크 키를 위한 카운터 증가
            st.session_state.rerun_counter += 1
            counter = st.session_state.rerun_counter

            placeholders = []
            for notice in st.session_state.notice_data:
                placeholder = st.empty()
                placeholders.append((placeholder, notice, counter))

            for placeholder, notice, counter in placeholders:
                with placeholder.container():
                    unique_key = f"open_notice_{notice['id']}_{counter}"
                    st.markdown(f"""
                    <div class="speech-bubble">
                        <button class="notice-title-btn" onclick="document.getElementById('{unique_key}').click();">{notice['title']}</button>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("", key=unique_key):
                        st.session_state.show_full_notice = notice["id"]
                        st.rerun()
        else:
            st.write("공지가 없습니다.")

    # 새 공지 슬라이드 알림 + 캐롤
    if st.session_state.new_notice and st.session_state.show_popup:
        # ... (알림 코드 생략)

    # 공지현황 클릭 시 슬라이드 사라짐
    if notice_expander:
        st.markdown("<script>document.querySelector('.slide-alert')?.remove();</script>", unsafe_allow_html=True)

    # 전체 화면 공지 (새 나가기 버튼)
    if st.session_state.show_full_notice is not None:
        # ... (공지 내용 코드 생략)

    st.stop()

# =============================================
# 관리자 모드
# =============================================
if st.session_state.admin:
    # 공지 입력
    # ... (입력 코드 생략)

    # 공지현황 박스 (중복 키 제거)
    with st.expander("공지현황", expanded=False):
        if st.session_state.notice_data:
            # 유니크 키를 위한 카운터
            st.session_state.notice_counter += 1
            counter = st.session_state.notice_counter

            placeholders = []
            for notice in st.session_state.notice_data:
                placeholder = st.empty()
                placeholders.append((placeholder, notice, counter))

            for placeholder, notice, counter in placeholders:
                with placeholder.container():
                    idx = st.session_state.notice_data.index(notice)
                    unique_id = f"{notice['id']}_{counter}_{idx}"
                    col1, col2 = st.columns([9, 1])
                    with col1:
                        if st.button(notice["title"], key=f"admin_notice_view_{unique_id}"):
                            st.session_state.show_full_notice = notice["id"]
                            st.rerun()
                    with col2:
                        if st.button("X", key=f"admin_notice_delete_{unique_id}"):
                            st.session_state.notice_data = [n for n in st.session_state.notice_data if n["id"] != notice["id"]]
                            save_notice_data(st.session_state.notice_data)
                            st.success("공지 삭제 완료")
                            st.rerun()
        else:
            st.write("공지가 없습니다.")

    # 전체 화면 공지 (관리자 클릭 시)
    # ... (공지 내용 코드 생략)
