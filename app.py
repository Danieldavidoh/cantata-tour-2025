import streamlit as st

# --- 기존 LANG/defaults 수정: set 안 되게 제대로 dict 정의 ---
LANG = {
    "ko": {
        "tab_notice": "공지",
        "tab_map": "투어 경로",
        "today": "오늘",
        "yesterday": "어제",
        "new_notice_alert": "새 공지가 도착했어요!",
        "warning": "제목·내용을 입력해주세요.",
        # ... 나머지 키 추가
    },
    # 다른 언어 추가
}

defaults = {
    "admin": False,
    "lang": "ko",
    # ... 나머지 세션 상태 기본값 추가 (로그에서 admin 등 보임)
}

# 세션 상태 초기화: 제대로 dict.items() 사용
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 로그인 부분: key 추가로 중복 ID 피함 ---
if not st.session_state.get("admin", False):
    pw = st.text_input("비밀번호", type="password")
    if st.button("로그인", key="login_success") and pw == "0009":
        st.session_state.admin = True
        st.rerun()
    elif st.button("로그인", key="login_fail"):
        st.error("비밀번호가 틀렸습니다.")
else:
    st.success("관리자 모드")

# --- SyntaxError 부분: dict 제대로 닫기 (line 215쯤) ---
some_dict = {
    "google_link": "https://goo.gl/maps/def456",
    "some_flag": True,  # 콤마 후 키 제대로
    "date": "11/07 02:01"  # 문자열로 OK, leading zero 문제 아님
}

# --- IndentationError: if-else 제대로 들여쓰기 (line 266-268쯤) ---
if some_condition:  # line 266
    # indented block
    pass
else:
    # indented block 추가
    pass

# --- 눈 효과: st.snow()는 한 번만 호출, 오류 후에 배치 ---
st.snow()  # 눈 내림. 하지만 이게 문제면 주석 처리 테스트: # st.snow()

# --- 나머지 앱 로직: 탭 등 ---
tab_notice, tab_map = st.tabs([LANG[st.session_state.lang]["tab_notice"], LANG[st.session_state.lang]["tab_map"]])
# ... 공지/맵 로직 추가

# Git 풀 후 테스트
