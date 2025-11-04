# ... (이전 코드 동일 – state, data, lang, cities, sidebar, theme, title, 일반 모드 생략)

# =============================================
# 관리자 모드
# =============================================
if st.session_state.admin:
    # 공지 입력
    st.markdown("---")
    st.subheader("공지사항 입력")
    
    col_input, col_button = st.columns([4, 1])
    with col_input:
        notice_title = st.text_input(_["notice_title"], key="notice_title_input", value=st.session_state.get("notice_title_input", ""))
        notice_content = st.text_area(_["notice_content"], key="notice_content_input", value=st.session_state.get("notice_content_input", ""))
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

                # 입력 필드 리셋
                st.session_state.notice_title_input = ""
                st.session_state.notice_content_input = ""
                st.rerun()  # 모든 앱 새로고침
            else:
                st.error("제목과 내용을 입력하세요.")

    # 공지현황 박스 (중복 키 제거)
    with st.expander("공지현황", expanded=False):
        if st.session_state.notice_data:
            # 유니크 키를 위한 카운터
            if "notice_counter" not in st.session_state:
                st.session_state.notice_counter = 0
            st.session_state.notice_counter += 1
            counter = st.session_state.notice_counter

            for idx, notice in enumerate(st.session_state.notice_data):
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
            </style>
            """, unsafe_allow_html=True)

    # (도시 입력, 지도 코드 생략 – 이전 유지)
