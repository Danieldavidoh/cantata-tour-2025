# ... (이전 코드 동일 – state, data, lang, cities, sidebar, theme, title, 일반 모드 생략)

# =============================================
# 관리자 모드
# =============================================
if st.session_state.admin:
    # 공지 입력 (오른쪽 등록 버튼)
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
                # 입력창 리셋
                st.session_state.notice_title_input = ""
                st.session_state.notice_content_input = ""
                st.rerun()
            else:
                st.error("제목과 내용을 입력하세요.")

    # 공지현황 버튼
    if st.button("공지현황", key="show_notice_status"):
        st.session_state.show_notice_status = True
    else:
        st.session_state.show_notice_status = False

    left, right = st.columns([1, 2])

    with left:
        # (도시 입력 생략 – 이전 코드 유지)

    with right:
        st.subheader(_["tour_map"])
        # (지도 코드 생략 – 이전 유지)

        # 공지현황 창
        if st.session_state.get("show_notice_status", False):
            st.markdown("---")
            st.subheader("공지 현황")
            if st.session_state.notice_data:
                for notice in st.session_state.notice_data:  # 최신순
                    col1, col2 = st.columns([9, 1])
                    with col1:
                        st.write(f"**{notice['title']}**")
                    with col2:
                        if st.button("X", key=f"delete_notice_{notice['id']}"):
                            st.session_state.notice_data = [n for n in st.session_state.notice_data if n["id"] != notice["id"]]
                            save_notice_data(st.session_state.notice_data)
                            st.success("공지 삭제 완료")
                            st.rerun()
            else:
                st.write("공지가 없습니다.")
