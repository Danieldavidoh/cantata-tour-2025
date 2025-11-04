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
            for idx, notice in enumerate(st.session_state.notice_data):
                placeholder = st.empty()
                placeholders.append((placeholder, notice, counter, idx))

            for placeholder, notice, counter, idx in placeholders:
                with placeholder.container():
                    unique_key = f"open_notice_{notice['id']}_{counter}_{idx}"
                    # 말풍선 + 버튼
                    st.markdown(f"""
                    <div class="speech-bubble">
                        <div style="font-weight: bold; color: #228B22;">{notice['title']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("열기", key=unique_key, use_container_width=True):
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
            <div id="full-screen-notice">
                <button id="new-exit-button" onclick="document.getElementById('close_full_notice_hidden').click();">나가기</button>
                <div id="full-screen-notice-content">
                    <h3>{notice['title']}</h3>
                    <div>{content}</div>
                </div>
            </div>
            <style>
            #full-screen-notice {
                position: fixed;
                top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.95);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            #full-screen-notice-content {
                background: #228B22;
                padding: 30px;
                border-radius: 15px;
                max-width: 90%;
                max-height: 90%;
                overflow-y: auto;
                position: relative;
            }
            #new-exit-button {
                position: absolute;
                top: 10px;
                right: 10px;
                background: #ff3b3b;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 0 10px rgba(255, 59, 59, 0.8);
            }
            #new-exit-button:hover {
                background: #cc0000;
                transform: scale(1.05);
            }
            .speech-bubble {
                background: #fff;
                border-radius: 15px;
                padding: 10px 15px;
                margin: 10px 0;
                position: relative;
                max-width: 80%;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            .speech-bubble:after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 50%;
                width: 0;
                height: 0;
                border: 10px solid transparent;
                border-top-color: #fff;
                border-bottom: 0;
                margin-left: -10px;
                margin-bottom: -10px;
            }
            </style>
            """, unsafe_allow_html=True)

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
            for idx, notice in enumerate(st.session_state.notice_data):
                placeholder = st.empty()
                placeholders.append((placeholder, notice, counter, idx))

            for placeholder, notice, counter, idx in placeholders:
                with placeholder.container():
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
