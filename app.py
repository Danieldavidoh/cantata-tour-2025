# =============================================
# 3. 페이지 설정 + 사이드바 (언어 선택 간격 조정)
# =============================================
st.set_page_config(page_title="Cantata Tour 2025", layout="wide", initial_sidebar_state="collapsed")

with st.sidebar:
    st.markdown("### Language")
    
    # 언어 선택 라디오 버튼 (간격 넓힘)
    st.markdown("""
    <style>
        div[data-testid="stRadio"] > label {
            margin-bottom: 20px !important;  /* 각 항목 간격 넓힘 */
            padding: 10px 0;
        }
        div[data-testid="stRadio"] > label > div {
            font-size: 1.1em;
        }
    </style>
    """, unsafe_allow_html=True)
    
    lang = st.radio(
        label="Select",
        options=["en", "ko", "hi"],
        format_func=lambda x: {"en": "English", "ko": "한국어", "hi": "हिन्दी"}[x],
        horizontal=False
    )
    _ = LANG[lang]
