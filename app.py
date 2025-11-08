# 세션 초기화 (기존 코드 상단에 있음)
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False, "adding_city": False}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v
