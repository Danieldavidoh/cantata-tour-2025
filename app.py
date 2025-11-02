import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
import math
import random

# ----------------------------------------------------------------------
# 1. 다국어 사전 (최소화)
# ----------------------------------------------------------------------
LANG = {
    "en": {
        "title": "Cantata Tour 2025", "tour_map": "Tour Map", "caption": "Mobile: Add to Home Screen -> Use like an app!",
        "admin_mode": "Admin Mode", "guest_mode": "Guest Mode", "enter_password": "Enter password", "submit": "Submit", "reset_btn": "Reset All"
    },
    "ko": {
        "title": "칸타타 투어 2025", "tour_map": "투어 지도", "caption": "모바일: 홈 화면에 추가 -> 앱처럼 사용!",
        "admin_mode": "관리자 모드", "guest_mode": "손님 모드", "enter_password": "비밀번호 입력", "submit": "제출", "reset_btn": "전체 초기화"
    },
    "hi": {
        "title": "कांताता टूर 2025", "tour_map": "टूर मैप", "caption": "मोबाइल: होम स्क्रीन पर जोड़ें -> ऐप की तरह उपयोग करें!",
        "admin_mode": "एडमिन मोड", "guest_mode": "गेस्ट मोड", "enter_password": "पासवर्ड दर्ज करें", "submit": "जमा करें", "reset_btn": "सब रीसेट करें"
    },
}

# ----------------------------------------------------------------------
# 2. 페이지 설정
# ----------------------------------------------------------------------
st.set_page_config(page_title="Cantata Tour 2025", layout="wide", initial_sidebar_state="collapsed")

# ----------------------------------------------------------------------
# 3. 테마 + 장식
# ----------------------------------------------------------------------
st.markdown("""
<style>
    .reportview-container {background:linear-gradient(to bottom,#0f0c29,#302b63,#24243e);overflow:hidden;position:relative;}
    .sidebar .sidebar-content {background:#228B22;color:white;}
    .Widget>label {color:#90EE90;font-weight:bold;}
    .christmas-title{font-size:3.5em!important;font-weight:bold;text-align:center;text-shadow:0 0 5px #FFF,0 0 10px #FFF,0 0 15px #FFF,0 0 20px #8B0000,0 0 35px #8B0000;letter-spacing:2px;position:relative;margin:20px 0;}
    .christmas-title .main{color:#FF0000!important;}
    .christmas-title .year{color:white!important;text-shadow:0 0 5px #FFF,0 0 10px #FFF,0 0 15px #FFF,0 0 20px #00BFFF;}
    .christmas-title::before{content:"❄️ ❄️ ❄️";position:absolute;top:-20px;left:50%;transform:translateX(-50%);font-size:0.6em;color:white;animation:snow-fall 3s infinite ease-in-out;}
    @keyframes snow-fall{0%,100%{transform:translateX(-50%) translateY(0);}50%{transform:translateX(-50%) translateY(10px);}}
    h1,h2,h3{color:#90EE90;text-shadow:1px 1px 3px #8B0000;text-align:center;}
    .stButton>button{background:#228B22;color:white;border:2px solid #8B0000;border-radius:12px;font-weight:bold;padding:10px;}
    .stButton>button:hover{background:#8B0000;color:white;}
    .christmas-decoration{position:absolute;font-size:2.5em;pointer-events:none;animation:float 6s infinite ease-in-out;z-index:10;}
    .gift{color:#FFD700;top:8%;left:5%;animation-delay:0s;}
    .candy-cane{color:#FF0000;top:8%;right:5%;animation-delay:1s;transform:rotate(15deg);}
    .stocking{color:#8B0000;top:25%;left:3%;animation-delay:2s;}
    .bell{color:#FFD700;top:25%;right:3%;animation-delay:3s;}
    .wreath{color:#228B22;top:45%;left:2%;animation-delay:4s;}
    .santa-hat{color:#FF0000;top:45%;right:2%;animation-delay:5s;}
    .tree{color:#228B22;bottom:20%;left:10%;animation-delay:0.5s;}
    .snowman{color:white;bottom:20%;right:10%;animation-delay:2.5s;}
    .candle{color:#FFA500;top:65%;left:8%;animation-delay:1.5s;}
    .star{color:#FFD700;top:65%;right:8%;animation-delay:3.5s;}
    @keyframes float{0%,100%{transform:translateY(0) rotate(0deg);}50%{transform:translateY(-20px) rotate(5deg);}}
    .snowflake{position:absolute;color:rgba(255,255,255,0.9);font-size:1.2em;pointer-events:none;animation:fall linear infinite;opacity:0.9;}
    @keyframes fall{0%{transform:translateY(-100vh) rotate(0deg);opacity:0.9;}100%{transform:translateY(100vh) rotate(360deg);opacity:0;}}
</style>
""", unsafe_allow_html=True)

deco = """
<div class="christmas-decoration gift">🎁</div>
<div class="christmas-decoration candy-cane">🍭</div>
<div class="christmas-decoration stocking">🧦</div>
<div class="christmas-decoration bell">🔔</div>
<div class="christmas-decoration wreath">🌿</div>
<div class="christmas-decoration santa-hat">🎅</div>
<div class="christmas-decoration tree">🎄</div>
<div class="christmas-decoration snowman">⛄</div>
<div class="christmas-decoration candle">🕯️</div>
<div class="christmas-decoration star">⭐</div>
"""
snow = "".join(
    f'<div class="snowflake" style="left:{random.randint(0,100)}%;font-size:{random.choice(["0.8em","1em","1.2em","1.4em"])};animation-duration:{random.uniform(8,20):.1f}s;animation-delay:{random.uniform(0,5):.1f}s;">❄️</div>'
    for _ in range(80)
)
st.markdown(deco + snow, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 4. 사이드바
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Language")
    lang = st.radio("Select", ["en","ko","hi"], format_func=lambda x: {"en":"English","ko":"한국어","hi":"हिन्दी"}[x])
    _ = LANG[lang]
    st.markdown("---")
    st.markdown("### Admin")
    for k in ["admin","show_pw","guest_mode"]: st.session_state.setdefault(k, False)
    if st.session_state.admin:
        st.success("Admin Mode Active")
        if st.button(_["guest_mode"]): st.session_state.update(admin=False, guest_mode=True, show_pw=True); st.rerun()
    else:
        if st.button(_["admin_mode"]): st.session_state.show_pw = True
        if st.session_state.show_pw:
            pw = st.text_input(_["enter_password"], type="password")
            if st.button(_["submit"]):
                if pw == "0691": st.session_state.update(admin=True, show_pw=False, guest_mode=False); st.success("Activated!"); st.rerun()
                else: st.error("Incorrect")
    if st.session_state.admin and st.button(_["reset_btn"]):
        st.session_state.clear()
        st.rerun()

# ----------------------------------------------------------------------
# 5. 제목
# ----------------------------------------------------------------------
title_text = _["title"]
if lang == "ko":
    parts = title_text.split()
    title_html = f'<span class="main">{parts[0]}</span> <span class="year">{" ".join(parts[1:])}</span>'
else:
    parts = title_text.rsplit(" ", 1)
    title_html = f'<span class="main">{parts[0]}</span> <span class="year">{parts[1] if len(parts)>1 else ""}</span>'
st.markdown(f'<h1 class="christmas-title">{title_html}</h1>', unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 6. 지도만 표시 (투어 경로 블럭 제거)
# ----------------------------------------------------------------------
st.subheader(_["tour_map"])
center = (19.75, 75.71)  # Maharashtra 중심
m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")

# 예시 마커
example_cities = ["Mumbai", "Pune", "Nagpur", "Nashik"]
for city in example_cities:
    lat, lon = coords.get(city, center)
    folium.CircleMarker(
        location=[lat, lon],
        radius=15,
        color="#90EE90",
        fill_color="#8B0000",
        popup=folium.Popup(f"<b>{city}</b>", max_width=300)
    ).add_to(m)

st_folium(m, width=700, height=500)
st.caption(_["caption"])
