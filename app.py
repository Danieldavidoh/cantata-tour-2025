# ... (이전 코드 동일 – state, data, lang, cities, sidebar, theme, title, 일반 모드 상단 생략)

# 전체 화면 공지 (X 버튼 안에)
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
            <div id="full-screen-notice-content" onclick="event.stopPropagation();">
                <button id="exit-button" onclick="event.stopPropagation(); document.getElementById('close_full_notice_hidden').click();">X</button>
                <h3>{notice['title']}</h3>
                <div>{content}</div>
            </div>
        </div>
        <style>
        #full-screen-notice-content {
            position: relative;
            background: #228B22;
            padding: 30px;
            border-radius: 15px;
            max-width: 90%;
            max-height: 90%;
            overflow-y: auto;
        }
        #exit-button {
            position: absolute;
            top: 10px;
            right: 10px;
            background: #ff3b3b;
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            font-weight: bold;
            font-size: 18px;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(255, 59, 59, 0.8);
        }
        #exit-button:hover {
            background: #cc0000;
            transform: scale(1.1);
        }
        </style>
        """, unsafe_allow_html=True)

    st.stop()
