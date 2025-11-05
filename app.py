# app.py
import streamlit as st
from datetime import datetime
import json, os, uuid

# ---------------------------------------
# 기본 세팅
# ---------------------------------------
st.set_page_config(page_title="Cantata Tour 2025", page_icon="🎄", layout="wide")

# ---------------------------------------
# 세션 초기화
# ---------------------------------------
if "notice_data" not in st.session_state:
    st.session_state.notice_data = []
if "expanded_notices" not in st.session_state:
    st.session_state.expanded_notices = {}
if "admin" not in st.session_state:
    st.session_state.admin = False

NOTICE_FILE = "notice_data.json"

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

st.session_state.notice_data = load_json(NOTICE_FILE, [])

# ---------------------------------------
# 공지 삭제 함수
# ---------------------------------------
def delete_notice(notice_id):
    st.session_state.notice_data = [n for n in st.session_state.notice_data if n["id"] != notice_id]
    save_json(NOTICE_FILE, st.session_state.notice_data)
    st.success("공지 삭제됨")

    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# ---------------------------------------
# 공지 추가 함수
# ---------------------------------------
def add_notice(title, content):
    if not title or not content:
        st.warning("제목과 내용을 입력하세요.")
        return
    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    st.session_state.notice_data.append(new_notice)
    save_json(NOTICE_FILE, st.session_state.notice_data)
    st.success("공지 추가됨")

    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# ---------------------------------------
# 공지 리스트 렌더링
# ---------------------------------------
def render_notice_list(show_delete=False):
    st.subheader("📢 공지 목록")
    if not st.session_state.notice_data:
        st.info("등록된 공지가 없습니다.")
        return

    for n in st.session_state.notice_data:
        with st.expander(f"📅 {n['date']} | {n['title']}"):
            st.write(n["content"])
            if show_delete:
                if st.button("🗑️ 삭제", key=f"del_{n['id']}"):
                    delete_notice(n["id"])

# ---------------------------------------
# 메인 페이지 렌더
# ---------------------------------------
def main():
    st.title("🎄 Cantata Tour 2025")
    st.caption("마하라스트라 일정 관리 대시보드")

    st.markdown("---")

    # 관리자 로그인
    if not st.session_state.admin:
        pw = st.text_input("관리자 비밀번호", type="password")
        if st.button("로그인"):
            if pw == "0000":
                st.session_state.admin = True
                try:
                    st.rerun()
                except AttributeError:
                    st.experimental_rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
        return

    # 관리자 화면
    st.success("관리자 로그인 완료 ✅")

    title = st.text_input("공지 제목")
    content = st.text_area("공지 내용")
    if st.button("공지 추가"):
        add_notice(title, content)

    render_notice_list(show_delete=True)

# ---------------------------------------
# 앱 실행
# ---------------------------------------
if __name__ == "__main__":
    main()
