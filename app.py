import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
import math
import random

# ----------------------------------------------------------------------
# 1. 다국어 사전 (완전)
# ----------------------------------------------------------------------
LANG = {
    "en": {
        "title": "Cantata Tour 2025", "add_city": "Add City", "select_city": "Select City",
        "add_city_btn": "Add City", "tour_route": "Tour Route", "remove": "Remove",
        "reset_btn": "Reset All", "venues_dates": "Tour Route", "performance_date": "Performance Date",
        "venue_name": "Venue Name", "seats": "Seats", "indoor_outdoor": "Indoor/Outdoor",
        "indoor": "Indoor", "outdoor": "Outdoor", "google_link": "Google Maps Link",
        "special_notes": "Special Notes", "register": "Register", "add_venue": "Add Venue",
        "edit": "Edit", "open_maps": "Open in Google Maps", "navigate": "Navigate",
        "save": "Save", "delete": "Delete", "tour_map": "Tour Map",
        "caption": "Mobile: Add to Home Screen -> Use like an app!", "date_format": "%b %d, %Y",
        "admin_mode": "Admin Mode", "guest_mode": "Guest Mode", "enter_password": "Enter password to access Admin Mode",
        "submit": "Submit", "drive_to": "Drive Here", "edit_venue": "Edit", "delete_venue": "Delete",
        "confirm_delete": "Are you sure you want to delete?", "date_changed": "Date changed",
        "venue_registered": "Venue registered successfully", "venue_deleted": "Venue deleted successfully",
        "venue_updated": "Venue updated successfully", "enter_venue_name": "Please enter a venue name",
        "edit_venue_label": "Venue Name", "edit_seats_label": "Seats", "edit_type_label": "Type",
        "edit_google_label": "Google Maps Link", "edit_notes_label": "Special Notes",
    },
    "ko": {
        "title": "칸타타 투어 2025", "add_city": "도시 추가", "select_city": "도시 선택",
        "add_city_btn": "도시 추가", "tour_route": "투어 경로", "remove": "삭제",
        "reset_btn": "전체 초기화", "venues_dates": "투어 경로", "performance_date": "공연 날짜",
        "venue_name": "공연장 이름", "seats": "좌석 수", "indoor_outdoor": "실내/실외",
        "indoor": "실내", "outdoor": "실외", "google_link": "구글 지도 링크",
        "special_notes": "특이사항", "register": "등록", "add_venue": "공연장 추가",
        "edit": "편집", "open_maps": "구글 지도 열기", "navigate": "길찾기",
        "save": "저장", "delete": "삭제", "tour_map": "투어 지도",
        "caption": "모바일: 홈 화면에 추가 -> 앱처럼 사용!", "date_format": "%Y년 %m월 %d일",
        "admin_mode": "관리자 모드", "guest_mode": "손님 모드", "enter_password": "관리자 모드 접근을 위한 비밀번호 입력",
        "submit": "제출", "drive_to": "길찾기", "edit_venue": "편집", "delete_venue": "삭제",
        "confirm_delete": "정말 삭제하시겠습니까?", "date_changed": "날짜 변경됨",
        "venue_registered": "등록 완료", "venue_deleted": "삭제 완료",
        "venue_updated": "수정 완료", "enter_venue_name": "공연장 이름을 입력하세요.",
        "edit_venue_label": "공연장 이름", "edit_seats_label": "좌석 수", "edit_type_label": "유형",
        "edit_google_label": "구글 지도 링크", "edit_notes_label": "특이사항",
    },
    "hi": {
        "title": "कांताता टूर 2025", "add_city": "शहर जोड़ें", "select_city": "शहर चुनें",
        "add_city_btn": "शहर जोड़ें", "tour_route": "टूर मार्ग", "remove": "हटाएं",
        "reset_btn": "सब रीसेट करें", "venues_dates": "टूर मार्ग", "performance_date": "प्रदर्शन तिथि",
        "venue_name": "स्थल का नाम", "seats": "सीटें", "indoor_outdoor": "इंडोर/आउटडोर",
        "indoor": "इंडोर", "outdoor": "आउटडोर", "google_link": "गूगल मैप्स लिंक",
        "special_notes": "विशेष टिप्पणियाँ", "register": "रजिस्टर", "add_venue": "स्थल जोड़ें",
        "edit": "संपादित करें", "open_maps": "गूगल मैप्स में खोलें", "navigate": "नेविगेट करें",
        "save": "सहेजें", "delete": "हटाएँ", "tour_map": "टूर मैप",
        "caption": "मोबाइल: होम स्क्रीन पर जोड़ें -> ऐप की तरह उपयोग करें!", "date_format": "%d %b %Y",
        "admin_mode": "एडमिन मोड", "guest_mode": "गेस्ट मोड", "enter_password": "एडमिन मोड एक्सेस करने के लिए पासवर्ड दर्ज करें",
        "submit": "जमा करें", "drive_to": "यहाँ ड्राइव करें", "edit_venue": "संपादित करें", "delete_venue": "हटाएँ",
        "confirm_delete": "क्या आप वाकई हटाना चाहते हैं?", "date_changed": "तिथि बदली गई",
        "venue_registered": "पंजीकरण सफल", "venue_deleted": "स्थल हटा दिया गया",
        "venue_updated": "स्थल अपडेट किया गया", "enter_venue_name": "कृपया स्थल का नाम दर्ज करें",
        "edit_venue_label": "स्थल का नाम", "edit_seats_label": "सीटें", "edit_type_label": "प्रकार",
        "edit_google_label": "गूगल मैप्स लिंक", "edit_notes_label": "विशेष टिप्पणियाँ",
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
        for k in ["route","dates","venues","admin_venues"]: st.session_state.pop(k, None); st.rerun()

# ----------------------------------------------------------------------
# 5. 세션 + 도시/좌표
# ----------------------------------------------------------------------
cols = ["Venue","Seats","IndoorOutdoor","Google Maps Link","Special Notes"]
for k in ["route","dates","venues","admin_venues"]: st.session_state.setdefault(k, [] if k=="route" else {})

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
def target(): return st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
def date_str(c): d = st.session_state.dates.get(c); return d.strftime(_["date_format"]) if d else "TBD"
def nav(url): return f"https://www.google.com/maps/dir/?api=1&destination={url}&travelmode=driving" if url and url.startswith("http") else ""

# ----------------------------------------------------------------------
# 8. 왼쪽 컬럼 - 투어 경로 (개조 버전)
# ----------------------------------------------------------------------
left, right = st.columns([1,3])
with left:
    avail = [c for c in cities if c not in st.session_state.route]
    if avail:
        c1, c2 = st.columns([2,1])
        with c1:
            next_city = st.selectbox(_["select_city"], avail, key="next_city_select_v2")
        with c2:
            if st.button(_["add_city_btn"], key="add_city_btn_v2"):
                st.session_state.route.append(next_city)
                st.rerun()
    st.markdown("---")
    if st.session_state.route:
        st.subheader(_["venues_dates"])
        for city in st.session_state.route:
            t = target()
            has = city in t and not t.get(city, pd.DataFrame()).empty
            # 구글맵 아이콘 (등록 후 오른쪽 끝, 🚗 아이콘으로 네비 연결)
            map_icon = ""
            if has:
                first_link = t[city].iloc[0]["Google Maps Link"]
                if first_link and first_link.startswith("http"):
                    nav_url = nav(first_link)
                    map_icon = f'<span style="float:right"><a href="{nav_url}" target="_blank" style="color:#90EE90">🚗</a></span>'
            # expander 라벨: 등록 전 "도시", 등록 후 "도시 – 날짜" + 아이콘
            expander_label = f"**{city}**"
            if has:
                expander_label += f" – {date_str(city)}"
            expander_label += map_icon
            with st.expander(expander_label, expanded=not has):  # 등록 전 펼침, 등록 후 닫힘
                # 공연 날짜 (달력 클릭 기반)
                cur = st.session_state.dates.get(city, datetime.now().date())
                new = st.date_input(
                    _["performance_date"],
                    cur,
                    key=f"date_{city}_v2",
                    format="YYYY-MM-DD"
                )
                if new != cur:
                    st.session_state.dates[city] = new
                    st.success(_["date_changed"])
                    st.rerun()

                # 등록 폼 (관리자/손님 모드 + 등록 안 됐을 때)
                if (st.session_state.admin or st.session_state.guest_mode) and not has:
                    st.markdown("---")
                    # 공연장 + 좌석
                    col1, col2 = st.columns([3,1])
                    with col1: venue_name = st.text_input(_["venue_name"], key=f"v_{city}_v2")
                    with col2: seats = st.number_input(_["seats"], min_value=1, step=50, key=f"s_{city}_v2")
                    # 구글 링크 + 실내/실외 (기존 유지)
                    col3, col4 = st.columns([3,1])
                    with col3: google_link = st.text_input(_["google_link"], placeholder="https://...", key=f"l_{city}_v2")
                    with col4:
                        io_key = f"io_{city}_v2"
                        st.session_state.setdefault(io_key, _["outdoor"])
                        if st.button(f"**{st.session_state[io_key]}**", key=f"io_btn_{city}_v2"):
                            st.session_state[io_key] = _["indoor"] if st.session_state[io_key] == _["outdoor"] else _["outdoor"]
                            st.rerun()
                    # 특이사항 + 등록 버튼 (오른쪽 끝)
                    sn_col, btn_col = st.columns([4,1])
                    with sn_col: special_notes = st.text_area(_["special_notes"], key=f"sn_{city}_v2")
                    with btn_col:
                        if st.button(_["register"], key=f"reg_{city}_v2"):
                            if not venue_name:
                                st.error(_["enter_venue_name"])
                            else:
                                new_row = pd.DataFrame([{
                                    "Venue": venue_name,
                                    "Seats": seats,
                                    "IndoorOutdoor": st.session_state[io_key],
                                    "Google Maps Link": google_link,
                                    "Special Notes": special_notes
                                }])
                                t[city] = pd.concat([t.get(city, pd.DataFrame(columns=cols)), new_row], ignore_index=True)
                                st.success(_["venue_registered"])
                                # 입력 초기화
                                for k in [f"v_{city}_v2", f"s_{city}_v2", f"l_{city}_v2", f"sn_{city}_v2", f"io_{city}_v2"]:
                                    st.session_state.pop(k, None)
                                st.rerun()

                # 등록된 공연장 목록 (등록 후 닫힌 상태에서 볼 수 있지만, 펼치면 보임)
                if has:
                    for idx, row in t[city].iterrows():
                        col1, col2, col3, col4 = st.columns([3,1,1,1])
                        with col1:
                            st.write(f"**{row['Venue']}**")
                            st.caption(f"{row['Seats']} {_['seats']} | {row.get('Special Notes','')}")
                        with col2:
                            st.write(row["IndoorOutdoor"])
                        with col3:
                            if row["Google Maps Link"].startswith("http"):
                                nav_url = nav(row["Google Maps Link"])
                                st.markdown(f'<div style="text-align:right"><a href="{nav_url}" target="_blank" style="color:#90EE90">🚗</a></div>', unsafe_allow_html=True)
                        with col4:
                            if st.session_state.admin or st.session_state.guest_mode:
                                if st.button(_["delete"], key=f"del_{city}_{idx}_v2"):
                                    if st.checkbox(_["confirm_delete"], key=f"confirm_{city}_{idx}_v2"):
                                        t[city] = t[city].drop(idx).reset_index(drop=True)
                                        if t[city].empty: t.pop(city, None)
                                        st.success(_["venue_deleted"])
                                        st.rerun()

# ----------------------------------------------------------------------
# 9. 오른쪽 컬럼 – 지도 (기존 유지)
# ----------------------------------------------------------------------
with right:
    st.markdown("---")
    st.subheader(_["tour_map"])
    center = coords.get(st.session_state.route[0] if st.session_state.route else "Mumbai", (19.75, 75.71))
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")
    if len(st.session_state.route) > 1:
        points = [coords[c] for c in st.session_state.route if c in coords]
        folium.PolyLine(points, color="red", weight=4, dash_array="10,10").add_to(m)
        for i in range(len(points) - 1):
            start, end = points[i], points[i + 1]
            arrow_lat = end[0] - (end[0] - start[0]) * 0.05
            arrow_lon = end[1] - (end[1] - start[1]) * 0.05
            folium.RegularPolygonMarker(location=[arrow_lat, arrow_lon], fill_color="red", number_of_sides=3, rotation=math.degrees(math.atan2(end[1] - start[1], end[0] - start[0])) - 90, radius=10).add_to(m)
    for city in st.session_state.route:
        if city in coords:
            df = target().get(city, pd.DataFrame(columns=cols))
            link = next((r["Google Maps Link"] for _, r in df.iterrows() if r["Google Maps Link"].startswith("http")), None)
            popup_html = f"<b style='color:#8B0000'>{city}</b><br>{date_str(city)}"
            if link: popup_html = f'<a href="{nav(link)}" target="_blank" style="color:#90EE90">{popup_html}<br><i>{_["navigate"]}</i></a>'
            folium.CircleMarker(location=coords[city], radius=15, color="#90EE90", fill_color="#8B0000", popup=folium.Popup(popup_html, max_width=300)).add_to(m)
    st_folium(m, width=700, height=500)
    st.caption(_["caption"])  # ← 완벽하게 고침! (.) 제거
