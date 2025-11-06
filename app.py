# === 자동 새로고침 제거 ===
# if not st.session_state.get("admin", False):
#     st_autorefresh(interval=3000, key="auto_refresh")

# 대신 아래 추가
import time

def auto_update_notices(interval=10):
    """공지 영역만 주기적으로 업데이트"""
    placeholder = st.empty()
    while True:
        with placeholder.container():
            render_notice_list(show_delete=st.session_state.admin)
        time.sleep(interval)

# 아래 탭 섹션 교체
tab1, tab2 = st.tabs([f"🎁 {_('tab_notice')}", f"🗺️ {_('tab_map')}"])

with tab1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_("title_label"))
            c = st.text_area(_("content_label"))
            img = st.file_uploader(_("upload_image"), type=["png", "jpg", "jpeg"])
            f = st.file_uploader(_("upload_file"))
            if st.form_submit_button(_("submit")):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_("warning"))
        render_notice_list(show_delete=True)
    else:
        # 공지 자동 새로고침 (10초마다)
        auto_update_notices(interval=10)
        if st.button("닫기"):
            st.session_state.expanded = {}
            st.rerun()
