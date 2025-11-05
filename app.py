import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
import random

# ----------------------------------------------------------------------
# 1. 다국어 사전
# ----------------------------------------------------------------------
LANG = {
    "en": {
        "title": "Cantata Tour 2025", "add_city": "Add City", "select_city": "Select City",
        "add_city_btn": "Add City", "tour_route": "Tour Route", "venue_name": "Venue Name",
        "seats": "Seats", "google_link": "Google Maps Link", "special_notes": "Special Notes",
        "register": "Register", "navigate": "Navigate", "admin_mode": "Admin Mode",
        "guest_mode": "Guest Mode", "enter_password": "Enter password", "submit": "Submit",
        "reset_btn": "Reset All", "venue_registered": "Registered", "enter_venue_name": "Enter venue name"
    },
    "ko": {
        "title": "칸타타 투어 2025", "add_city": "도시 추가", "select_city": "도시 선택",
        "add_city_btn": "도시 추가", "tour_route": "투어 경로", "venue_name": "공연장 이름",
        "seats": "좌석 수", "google_link": "구글 지도 링크", "special_notes": "특이사항",
        "register": "등록", "navigate": "길찾기", "admin_mode": "관리자 모드",
        "guest_mode": "손님 모드", "enter_password": "비밀번호 입력", "submit": "제출",
        "reset_btn": "전체 초기화", "venue_registered": "등록 완료", "enter_venue_name": "공연장 이름 입력"
    },
    "hi": {
        "title": "कांताता टूर 2025", "add_city": "शहर जोड़ें", "select_city": "शहर चुनें",
        "add_city_btn": "शहर जोड़ें", "tour_route": "टूर मार्ग", "venue_name": "स्थल का नाम",
        "seats": "सीटें", "google_link": "गूगल मैप्स लिंक", "special_notes": "विशेष टिप्पणियाँ",
        "register": "रजिस्टर", "navigate": "नेविगेट करें", "admin_mode": "एडमिन मोड",
        "guest_mode": "गेस्ट मोड", "enter_password": "पासवर्ड दर्ज करें", "submit": "जमा करें",
        "reset_btn": "सब रीसेट करें", "venue_registered": "पंजीकरण सफल", "enter_venue_name": "स्थल का नाम दर्ज करें"
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
    .stTextInput>label,.stSelectbox>label,.stNumberInput>label{color:#90EE90;}
    .stExpander{background:rgba(139,0,0,0.4);border:1px solid #90EE90;border-radius:12px;}
    .stExpander>summary{color:#90EE90;font-weight:bold;font-size:1.5em!important;}
    .stExpander>div>div>label{font-size:1.2em!important;}
    .stMarkdown{color:#90EE90;}
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
        for k in ["route","venues"]: st.session_state.pop(k, None); st.rerun()

# ----------------------------------------------------------------------
# 5. 세션 + 도시/좌표
# ----------------------------------------------------------------------
cols = ["Venue","Seats","Google Maps Link","Special Notes"]
for k in ["route","venues"]: st.session_state.setdefault(k, [] if k=="route" else {})

cities = sorted([
    "Mumbai","Pune","Nagpur","Nashik","Thane","Aurangabad","Solapur","Amravati","Nanded","Kolhapur",
    "Akola","Latur","Ahmadnagar","Jalgaon","Dhule","Ichalkaranji","Malegaon","Bhusawal","Bhiwandi","Bhandara",
    "Beed","Buldana","Chandrapur","Dharashiv","Gondia","Hingoli","Jalna","Mira-Bhayandar","Nandurbar","Osmanabad",
    "Palghar","Parbhani","Ratnagiri","Sangli","Satara","Sindhudurg","Wardha","Washim","Yavatmal","Kalyan-Dombivli",
    "Ulhasnagar","Vasai-Virar","Sangli-Miraj-Kupwad","Nanded-Waghala","Bandra (Mumbai)","Colaba (Mumbai)","Andheri (Mumbai)",
    "Boric Nagar (Mumbai)","Navi Mumbai","Mumbai Suburban","Pimpri-Chinchwad (Pune)","Koregaon Park (Pune)","Kothrud (Pune)",
    "Hadapsar (Pune)","Pune Cantonment","Nashik Road","Deolali (Nashik)","Satpur (Nashik)","Aurangabad City","Jalgaon City",
    "Bhopalwadi (Aurangabad)","Nagpur City","Sitabuldi (Nagpur)","Jaripatka (Nagpur)","Solapur City","Hotgi (Solapur)",
    "Pandharpur (Solapur)","Amravati City","Badnera (Amravati)","Paratwada (Amravati)","Akola City","Murtizapur (Akola)",
    "Washim City","Mangrulpir (Washim)","Yavatmal City","Pusad (Yavatmal)","Darwha (Yavatmal)","Wardha City",
    "Sindi (Wardha)","Hinganghat (Wardha)","Chandrapur City","Brahmapuri (Chandrapur)","Mul (Chandrapur)","Gadchiroli",
    "Aheri (Gadchiroli)","Dhanora (Gadchiroli)","Gondia City","Tiroda (Gondia)","Arjuni Morgaon (Gondia)",
    "Bhandara City","Pauni (Bhandara)","Tumsar (Bhandara)","Nagbhid (Chandrapur)","Gadhinglaj (Kolhapur)",
    "Kagal (Kolhapur)","Ajra (Kolhapur)","Shiroli (Kolhapur)",
])

coords = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
    "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Amravati": (20.93, 77.75),
    "Nanded": (19.16, 77.31), "Kolhapur": (16.70, 74.24), "Akola": (20.70, 77.00), "Latur": (18.40, 76.57),
    "Ahmadnagar": (19.10, 74.75), "Jalgaon": (21.00, 75.57), "Dhule": (20.90, 74.77), "Ichalkaranji": (16.69, 74.47),
    "Malegaon": (20.55, 74.53), "Bhusawal": (21.05, 76.00), "Bhiwandi": (19.30, 73.06), "Bhandara": (21.17, 79.65),
    "Beed": (18.99, 75.76), "Buldana": (20.54, 76.18), "Chandrapur": (19.95, 79.30), "Dharashiv": (18.40, 76.57),
    "Gondia": (21.46, 80.19), "Hingoli": (19.72, 77.15), "Jalna": (19.85, 75.89), "Mira-Bhayandar": (19.28, 72.87),
    "Nandurbar": (21.37, 74.22), "Osmanabad": (18.18, 76.07), "Palghar": (19.70, 72.77), "Parbhani": (19.27, 76.77),
    "Ratnagiri": (16.99, 73.31), "Sangli": (16.85, 74.57), "Satara": (17.68, 74.02), "Sindhudurg": (16.24, 73.42),
    "Wardha": (20.75, 78.60), "Washim": (20.11, 77.13), "Yavatmal": (20.39, 78.12), "Kalyan-Dombivli": (19.24, 73.13),
    "Ulhasnagar": (19.22, 73.16), "Vasai-Virar": (19.37, 72.81), "Sangli-Miraj-Kupwad": (16.85, 74.57), "Nanded-Waghala": (19.16, 77.31),
    "Bandra (Mumbai)": (19.06, 72.84), "Colaba (Mumbai)": (18.92, 72.82), "Andheri (Mumbai)": (19.12, 72.84), "Boric Nagar (Mumbai)": (19.07, 72.88),
    "Navi Mumbai": (19.03, 73.00), "Mumbai Suburban": (19.07, 72.88), "Pimpri-Chinchwad (Pune)": (18.62, 73.80), "Koregaon Park (Pune)": (18.54, 73.90),
    "Kothrud (Pune)": (18.50, 73.81), "Hadapsar (Pune)": (18.51, 73.94), "Pune Cantonment": (18.50, 73.89), "Nashik Road": (20.00, 73.79),
    "Deolali (Nashik)": (19.94, 73.82), "Satpur (Nashik)": (20.01, 73.79), "Aurangabad City": (19.88, 75.34), "Jalgaon City": (21.00, 75.57),
    "Bhopalwadi (Aurangabad)": (19.88, 75.34), "Nagpur City": (21.15, 79.08), "Sitabuldi (Nagpur)": (21.14, 79.08), "Jaripatka (Nagpur)": (21.12, 79.07),
    "Solapur City": (17.67, 75.91), "Hotgi (Solapur)": (17.57, 75.95), "Pandharpur (Solapur)": (17.66, 75.32), "Amravati City": (20.93, 77.75),
    "Badnera (Amravati)": (20.84, 77.73), "Paratwada (Amravati)": (21.06, 77.21), "Akola City": (20.70, 77.00), "Murtizapur (Akola)": (20.73, 77.37),
    "Washim City": (20.11, 77.13), "Mangrulpir (Washim)": (20.31, 77.05), "Yavatmal City": (20.39, 78.12), "Pusad (Yavatmal)": (19.91, 77.57),
    "Darwha (Yavatmal)": (20.31, 77.78), "Wardha City": (20.75, 78.60), "Sindi (Wardha)": (20.82, 78.09), "Hinganghat (Wardha)": (20.58, 78.58),
    "Chandrapur City": (19.95, 79.30), "Brahmapuri (Chandrapur)": (20.61, 79.89), "Mul (Chandrapur)": (19.95, 79.06), "Gadchiroli": (20.09, 80.11),
    "Aheri (Gadchiroli)": (19.37, 80.18), "Dhanora (Gadchiroli)": (19.95, 80.15), "Gondia City": (21.46, 80.19), "Tiroda (Gondia)": (21.28, 79.68),
    "Arjuni Morgaon (Gondia)": (21.29, 80.20), "Bhandara City": (21.17, 79.65), "Pauni (Bhandara)": (21.07, 79.81), "Tumsar (Bhandara)": (21.37, 79.75),
    "Nagbhid (Chandrapur)": (20.29, 79.36), "Gadhinglaj (Kolhapur)": (16.23, 74.34), "Kagal (Kolhapur)": (16.57, 74.31), "Ajra (Kolhapur)": (16.67, 74.22),
    "Shiroli (Kolhapur)": (16.70, 74.24),
}

# ----------------------------------------------------------------------
# 6. 제목
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
# 7. 헬퍼
# ----------------------------------------------------------------------
def nav(url): return f"https://www.google.com/maps/dir/?api=1&destination={url}&travelmode=driving" if url and url.startswith("http") else ""

# ----------------------------------------------------------------------
# 8. 왼쪽 컬럼 - 도시 추가 + 투어 경로
# ----------------------------------------------------------------------
left, right = st.columns([1,3])
with left:
    # 도시 추가 섹션
    avail = [c for c in cities if c not in st.session_state.route]
    if avail:
        c1, c2 = st.columns([3,1])
        with c1:
            next_city = st.selectbox(_["select_city"], avail + ["공연없음"], index=len(avail), key="next_city_select")
        with c2:
            if st.button(_["add_city_btn"], key="add_city_btn"):
                if next_city != "공연없음":
                    st.session_state.route.append(next_city)
                st.rerun()

    st.markdown("---")
    st.subheader(_["tour_route"])

    # 투어 경로 섹션
    for city in st.session_state.route:
        t = st.session_state.venues
        has = city in t and not t.get(city, pd.DataFrame()).empty
        car_icon = ""
        if has:
            link = t[city].iloc[0]["Google Maps Link"]
            if link and link.startswith("http"):
                car_icon = f'<span style="float:right">[🚗]({nav(link)})</span>'
        with st.expander(f"**{city}**{car_icon}", expanded=False):
            # 등록 폼
            if (st.session_state.admin or st.session_state.get("guest_mode")) and not has:
                st.markdown("---")
                venue_name = st.text_input(_["venue_name"], key=f"v_{city}")
                seats = st.number_input(_["seats"], 1, step=50, key=f"s_{city}")
                google_link = st.text_input(_["google_link"], placeholder="https://...", key=f"l_{city}")
                special_notes = st.text_area(_["special_notes"], key=f"sn_{city}")
                _, btn = st.columns([4,1])
                with btn:
                    if st.button(_["register"], key=f"reg_{city}"):
                        if not venue_name:
                            st.error(_["enter_venue_name"])
                        else:
                            new_row = pd.DataFrame([{
                                "Venue": venue_name,
                                "Seats": seats,
                                "Google Maps Link": google_link,
                                "Special Notes": special_notes
                            }])
                            t[city] = pd.concat([t.get(city, pd.DataFrame(columns=cols)), new_row], ignore_index=True)
                            st.success(_["venue_registered"])
                            for k in [f"v_{city}", f"s_{city}", f"l_{city}", f"sn_{city}"]:
                                st.session_state.pop(k, None)
                            st.rerun()

            # 등록된 공연장
            if has:
                for idx, row in t[city].iterrows():
                    c1, c2, c3 = st.columns([3,1,1])
                    with c1:
                        st.write(f"**{row['Venue']}**")
                        st.caption(f"{row['Seats']} {_['seats']} | {row.get('Special Notes','')}")
                    with c3:
                        if row["Google Maps Link"].startswith("http"):
                            st.markdown(f'<div style="text-align:right">[🚗]({nav(row["Google Maps Link"])})</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 9. 오른쪽 컬럼 – 지도
# ----------------------------------------------------------------------
with right:
    st.subheader("Tour Map")
    center = coords.get(st.session_state.route[0] if st.session_state.route else "Mumbai", (19.75, 75.71))
    m = folium.Map(location=center, zoom_start=7, tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google")
    if len(st.session_state.route) > 1:
        points = [coords[c] for c in st.session_state.route]
        folium.PolyLine(points, color="red", weight=4).add_to(m)
    for city in st.session_state.route:
        df = st.session_state.venues.get(city, pd.DataFrame(columns=cols))
        link = next((r["Google Maps Link"] for _, r in df.iterrows() if r["Google Maps Link"].startswith("http")), None)
        popup_html = f"<b style='color:#8B0000'>{city}</b>"
        if link: popup_html = f'<a href="{nav(link)}" target="_blank" style="color:#90EE90">{popup_html}<br><i>{_["navigate"]}</i></a>'
        folium.CircleMarker(location=coords[city], radius=15, color="#90EE90", fill_color="#8B0000", popup=folium.Popup(popup_html, max_width=300)).add_to(m)
    st_folium(m, width=700, height=500)
