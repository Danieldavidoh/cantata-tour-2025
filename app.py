
import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# Language dictionary
LANG = {
    "en": {"title": "Cantata Tour 2025", "add_city": "Add City", "select_city": "Select City",
           "register": "Register", "venue_name": "Venue", "seats": "Seats",
           "indoor": "Indoor", "outdoor": "Outdoor", "google_link": "Google Maps Link",
           "special_notes": "Notes", "tour_route": "Tour Route", "tour_map": "Tour Map",
           "admin_mode": "Admin Mode", "guest_mode": "Guest Mode", "password": "Enter Admin Password",
           "submit": "Submit", "date": "Date"},
    "ko": {"title": "칸타타 투어 2025", "add_city": "도시 추가", "select_city": "도시 선택",
           "register": "등록", "venue_name": "공연장", "seats": "좌석 수",
           "indoor": "실내", "outdoor": "실외", "google_link": "구글 링크",
           "special_notes": "특이사항", "tour_route": "투어 경로", "tour_map": "투어 지도",
           "admin_mode": "관리자 모드", "guest_mode": "손님 모드", "password": "관리자 비밀번호 입력",
           "submit": "확인", "date": "날짜"},
    "hi": {"title": "कांताता टूर 2025", "add_city": "शहर जोड़ें", "select_city": "शहर चुनें",
           "register": "रजिस्टर", "venue_name": "स्थल", "seats": "सीटें",
           "indoor": "इंडोर", "outdoor": "आउटडोर", "google_link": "गूगल लिंक",
           "special_notes": "टिप्पणियाँ", "tour_route": "टूर मार्ग", "tour_map": "टूर मानचित्र",
           "admin_mode": "एडमिन मोड", "guest_mode": "गेस्ट मोड", "password": "पासवर्ड दर्ज करें",
           "submit": "सबमिट", "date": "तारीख"}
}

cities = ["Mumbai","Pune","Nagpur","Nashik"]
coords = {"Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79)}

st.set_page_config(layout="wide")

# Language select
lang = st.selectbox("Language / 언어 / भाषा", ["ko","en","hi"])
_ = LANG[lang]

# Admin mode
if "admin" not in st.session_state:
    st.session_state.admin = False

if not st.session_state.admin:
    if st.button(_["admin_mode"]):
        pw = st.text_input(_["password"], type="password")
        if pw == "0691":
            st.session_state.admin = True
            st.experimental_rerun()
else:
    if st.button(_["guest_mode"]):
        st.session_state.admin = False
        st.experimental_rerun()

st.title(_["title"])

if "route" not in st.session_state:
    st.session_state.route = []
if "data" not in st.session_state:
    st.session_state.data = {}

left, right = st.columns([1,3])

with left:
    selected_city = st.selectbox(_["select_city"], [c for c in cities if c not in st.session_state.route])
    if st.button(_["add_city"]):
        st.session_state.route.append(selected_city)
        st.experimental_rerun()

    st.subheader(_["tour_route"])
    for city in st.session_state.route:
        with st.expander(city):
            date = st.date_input(_["date"], datetime.now(), key=f"date_{city}")
            venue = st.text_input(_["venue_name"], key=f"venue_{city}")
            seats = st.number_input(_["seats"], 0, 5000, key=f"seats_{city}")
            google = st.text_input(_["google_link"], key=f"google_{city}")
            notes = st.text_area(_["special_notes"], key=f"notes_{city}")
            if st.button(_["register"], key=f"reg_{city}"):
                st.session_state.data[city] = {"date": date, "venue": venue, "seats": seats, "google": google, "notes": notes}
                st.experimental_rerun()

with right:
    st.subheader(_["tour_map"])
    center = (19.75, 75.71)
    m = folium.Map(location=center, zoom_start=7)
    for city in st.session_state.route:
        if city in coords:
            folium.Marker(coords[city], popup=city).add_to(m)
    st_folium(m, width=700, height=500)
