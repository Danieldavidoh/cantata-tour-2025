import streamlit as st
import json
import os
import base64
from datetime import datetime

# =============================================
# 초기화
# =============================================
if "notice_data" not in st.session_state:
    st.session_state.notice_data = []
if "show_full_notice" not in st.session_state:
    st.session_state.show_full_notice = None
if "new_notice" not in st.session_state:
    st.session_state.new_notice = False
if "show_popup" not in st.session_state:
    st.session_state.show_popup = True
if "rerun_counter" not in st.session_state:
    st.session_state.rerun_counter = 0

# 데이터 파일
DATA_FILE = "notice_data.json"

def load_notice_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_notice_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 초기 로드
if not st.session_state.notice_data:
    st.session_state.notice_data = load_notice_data()

# 새 공지 감지
if st.session_state.notice_data:
    latest_id = max(n["id"] for n in st.session_state.notice_data)
    if "last_seen_id" not in st.session_state:
        st.session_state.last_seen_id = latest_id
    elif latest_id > st.session_state.last_seen_id:
        st.session_state.new_notice = True
        st.session_state.last_seen_id = latest_id
else:
    st.session_state.new_notice = False

# =============================================
# CSS 스타일
# =============================================
st.markdown("""
<style>
.speech-bubble {
    background: #fff;
    border-radius: 15px;
    padding: 10px 15px;
    margin: 10px 0;
    position: relative;
    max-width: 80%;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    align-self: flex-start;
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
.slide-alert {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #228B22;
    color: white;
    padding: 15px 25px;
    border-radius: 12px;
    font-weight: bold;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    z-index: 9999;
    animation: slideIn 0.5s ease-out;
    display: flex;
    align-items: center;
    gap: 10px;
}
@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
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
    color: white;
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

# =============================================
# 1. 투어지도
# =============================================
with st.expander("📍 투어지도", expanded=False):
    # 여기에 실제 지도 데이터 연결 (예: st.map, folium, etc.)
    st.write("지도 로딩 중...")
    # 예시: st.map(data)  # data = pd.DataFrame with lat, lon

st.markdown("---")

# =============================================
# 2. 공지현황
# =============================================
notice_expander = st.expander("📢 공지현황", expanded=False)
with notice_expander:
    if st.session_state.notice_data:
        st.session_state.rerun_counter += 1
        counter = st.session_state.rerun_counter
        placeholders = []

        for idx, notice in enumerate(st.session_state.notice_data):
            placeholder = st.empty()
            placeholders.append((placeholder, notice, counter, idx))

        for placeholder, notice, counter, idx in placeholders:
            with placeholder.container():
                unique_key = f"open_notice_{notice['id']}_{counter}_{idx}"
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

# =============================================
# 새 공지 슬라이드 알림
# =============================================
if st.session_state.new_notice and st.session_state.show_popup:
    st.markdown(f"""
    <div class="slide-alert">
        <span>🔔 새 공지사항이 도착했습니다!</span>
        <button onclick="document.querySelector('.slide-alert').remove(); 
                        document.getElementById('close_popup_hidden').click();" 
                style="background:none;border:none;color:white;font-size:18px;cursor:pointer;">×</button>
    </div>
    <button id="close_popup_hidden" style="display:none;"></button>
    """, unsafe_allow_html=True)
    if st.button("", key="close_popup_hidden"):
        st.session_state.show_popup = False
        st.rerun()

# 공지현황 펼치면 슬라이드 알림 제거
if notice_expander:
    st.markdown("""
    <script>
    setTimeout(() => {
        document.querySelector('.slide-alert')?.remove();
    }, 100);
    </script>
    """, unsafe_allow_html=True)

# =============================================
# 전체 화면 공지
# =============================================
if st.session_state.show_full_notice is not None:
    notice = next((n for n in st.session_state.notice_data if n["id"] == st.session_state.show_full_notice), None)
    if notice:
        content = notice["content"]
        if notice.get("file"):
            content += f"<br><img src='data:image/png;base64,{notice['file']}' style='max-width:100%; border-radius:10px;'>"

        st.button("", key="close_full_notice_hidden", on_click=lambda: None)
        if st.session_state.get("close_full_notice_hidden"):
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
        """, unsafe_allow_html=True)

# =============================================
# 앱 종료
# =============================================
st.stop()
