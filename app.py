
import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath

# --- language ---
LANG = {
    "ko": {"title":"칸타타 투어 2025","select_city":"도시 선택","add_city":"도시 추가",
           "register":"등록","venue":"공연장","seats":"좌석 수","indoor":"실내","outdoor":"실외",
           "google":"구글 지도 링크","notes":"특이사항","tour_map":"투어 지도","tour_route":"투어 경로",
           "password":"관리자 비밀번호","login":"로그인","logout":"로그아웃","date":"공연 날짜"},
    "en": {"title":"Cantata Tour 2025","select_city":"Select City","add_city":"Add City",
           "register":"Register","venue":"Venue","seats":"Seats","indoor":"Indoor","outdoor":"Outdoor",
           "google":"Google Maps Link","notes":"Notes","tour_map":"Tour Map","tour_route":"Tour Route",
           "password":"Admin Password","login":"Log in","logout":"Log out","date":"Date"}
}

# --- cities and coordinates ---
cities = sorted([
    "Mumbai","Pune","Nagpur","Nashik","Thane","Aurangabad","Solapur","Amravati","Nanded","Kolhapur",
    "Akola","Latur","Ahmadnagar","Jalgaon","Dhule","Malegaon","Bhusawal","Bhiwandi","Bhandara","Beed"
])

coords = {
    "Mumbai":(19.07,72.88),"Pune":(18.52,73.86),"Nagpur":(21.15,79.08),"Nashik":(20.00,73.79),"Thane":(19.22,72.98),
    "Aurangabad":(19.88,75.34),"Solapur":(17.67,75.91),"Amravati":(20.93,77.75),"Nanded":(19.16,77.31),"Kolhapur":(16.70,74.24),
    "Akola":(20.70,77.00),"Latur":(18.40,76.18),"Ahmadnagar":(19.10,74.75),"Jalgaon":(21.00,75.57),"Dhule":(20.90,74.77),
    "Malegaon":(20.55,74.53),"Bhusawal":(21.05,76.00),"Bhiwandi":(19.30,73.06),"Bhandara":(21.17,79.65),"Beed":(18.99,75.76)
}

# --- Streamlit state setup ---
st.set_page_config(page_title="Cantata Tour", layout="wide")

if "lang" not in st.session_state: st.session_state.lang = "ko"
if "admin" not in st.session_state: st.session_state.admin = False
if "route" not in st.session_state: st.session_state.route = []
if "venue_data" not in st.session_state: st.session_state.venue_data = {}  # city -> dict

# --- Sidebar ---
with st.sidebar:
    lang_selected = st.selectbox("Language / 언어", ["ko","en"], index=0)
    st.session_state.lang = lang_selected
    _ = LANG[st.session_state.lang]

    st.markdown("---")
    st.write("### Admin")

    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0691":
                st.session_state.admin = True
                st.success("✅ 관리자 모드 활성화")
                st.experimental_rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.success("👋 손님 모드로 전환합니다.")
            st.experimental_rerun()

_ = LANG[st.session_state.lang]
st.title(f"🎄 {_['title']}")

left, right = st.columns([1,2])

# --- Left panel ---
with left:
    st.subheader(_["tour_route"])

    available = [c for c in cities if c not in st.session_state.route]
    if available:
        selected_city = st.selectbox(_["select_city"], available)
        if st.button(_["add_city"]):
            st.session_state.route.append(selected_city)
            st.session_state.venue_data[selected_city] = {}
            st.experimental_rerun()

    st.markdown("---")

    for c in st.session_state.route:
        with st.expander(c):
            date = st.date_input(_["date"], value=datetime.now().date(), key=f"date_{c}")
            venue = st.text_input(_["venue"], key=f"venue_{c}")
            seats = st.number_input(_["seats"], min_value=0, step=50, key=f"seats_{c}")
            google = st.text_input(_["google"], key=f"google_{c}")
            notes = st.text_area(_["notes"], key=f"notes_{c}")

            indoor_outdoor = st.radio("Type / 유형", [_["indoor"], _["outdoor"]], key=f"io_{c}")

            if st.session_state.admin:
                if st.button(_["register"], key=f"reg_{c}"):
                    st.session_state.venue_data[c] = {
                        "date": str(date),
                        "venue": venue,
                        "seats": seats,
                        "type": indoor_outdoor,
                        "google": google,
                        "notes": notes
                    }
                    st.success("✅ 저장되었습니다.")
                    st.experimental_rerun()
            else:
                st.info("관리자 모드에서만 저장 가능합니다.")

# --- Right panel: MAP ---
with right:
    st.subheader(_["tour_map"])

    m = folium.Map(location=(19.75,75.71), zoom_start=7, tiles="CartoDB positron")

    points = [coords[c] for c in st.session_state.route if c in coords]
    if len(points) >= 2:
        AntPath(points, color="red", weight=4, delay=800).add_to(m)

    for c in st.session_state.route:
        if c in coords:
            data = st.session_state.venue_data.get(c, {})
            popup = f"<b>{c}</b><br>"
            if "date" in data:
                popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data['type']}<br>"
            if "google" in data and data["google"]:
                popup += f"<a href='{data['google']}' target='_blank'>📍 Google Maps</a>"
            folium.Marker(coords[c], popup=popup).add_to(m)

    st_folium(m, width=900, height=650)
