
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import folium
from streamlit_folium import st_folium
import math

# ---------------------------
# Cantata Tour - Full version
# - Restores full city list (sample ~100+ entries from Maharashtra)
# - Sidebar: language selector + admin mode (password 0691)
# - Admin: can add venues; Guest: view-only
# - Fixed rerun usage (only inside button handlers)
# ---------------------------

# Language dictionary
LANG = {
    "en": {
        "title": "Cantata Tour 2025", "select_city":"Select city", "add_city":"Add City",
        "performance_date":"Performance date", "venue_name":"Venue name", "seats":"Seats",
        "indoor":"Indoor","outdoor":"Outdoor","google_link":"Google Maps link","special_notes":"Special notes",
        "register":"Register","tour_route":"Tour Route","distance":"Distance","time":"Time","tour_map":"Tour Map",
        "admin_mode":"Admin Mode","guest_mode":"Guest Mode","enter_password":"Enter password to access Admin Mode",
        "submit":"Submit","reset_btn":"Reset All","venue_registered":"Venue registered successfully","confirm":"Confirm"
    },
    "ko": {
        "title": "칸타타 투어 2025", "select_city":"도시 선택", "add_city":"도시 추가",
        "performance_date":"공연 날짜", "venue_name":"공연장 이름", "seats":"좌석 수",
        "indoor":"실내","outdoor":"실외","google_link":"구글 지도 링크","special_notes":"특이사항",
        "register":"등록","tour_route":"투어 경로","distance":"거리","time":"소요시간","tour_map":"투어 지도",
        "admin_mode":"관리자 모드","guest_mode":"손님 모드","enter_password":"관리자 모드 접근을 위한 비밀번호 입력",
        "submit":"제출","reset_btn":"전체 초기화","venue_registered":"등록 완료","confirm":"확인"
    },
    "hi": {
        "title": "कांताता टूर 2025", "select_city":"शहर चुनें", "add_city":"शहर जोड़ें",
        "performance_date":"प्रदर्शन तिथि", "venue_name":"स्थल का नाम", "seats":"सीटें",
        "indoor":"इंडोर","outdoor":"आउटडोर","google_link":"गूगल मैप्स लिंक","special_notes":"विशेष टिप्पणियाँ",
        "register":"रजिस्टर","tour_route":"टूर मार्ग","distance":"दूरी","time":"समय","tour_map":"टूर मैप",
        "admin_mode":"एडमिन मोड","guest_mode":"गेस्ट मोड","enter_password":"एडमिन मोड एक्सेस करने के लिए पासवर्ड दर्ज करें",
        "submit":"जमा करें","reset_btn":"सब रीसेट करें","venue_registered":"रजिस्ट्रेशन सफल","confirm":"पुष्टि"
    }
}

# ---------------------------
# Helper: Distance Matrix
# ---------------------------
def get_distance_duration(origin, destination, api_key):
    if not api_key:
        return None
    o = f"{origin[0]},{origin[1]}"
    d = f"{destination[0]},{destination[1]}"
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": o,
        "destinations": d,
        "mode": "driving",
        "key": api_key,
        "units": "metric"
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        if data.get("rows") and data["rows"][0].get("elements"):
            el = data["rows"][0]["elements"][0]
            if el.get("status") == "OK":
                distance_text = el["distance"]["text"]
                distance_m = el["distance"]["value"]
                duration_text = el["duration"]["text"]
                duration_s = el["duration"]["value"]
                return distance_text, distance_m, duration_text, duration_s
    except Exception:
        return None
    return None

# ---------------------------
# Cities + Coordinates (expanded list from earlier conversation)
# Note: This is a large sample; you can extend it further as needed.
# ---------------------------
cities = sorted([
    "Mumbai","Pune","Nagpur","Nashik","Thane","Aurangabad","Solapur","Amravati","Nanded","Kolhapur",
    "Akola","Latur","Ahmadnagar","Jalgaon","Dhule","Ichalkaranji","Malegaon","Bhusawal","Bhiwandi","Bhandara",
    "Beed","Buldana","Chandrapur","Dharashiv","Gondia","Hingoli","Jalna","Mira-Bhayandar","Nandurbar","Osmanabad",
    "Palghar","Parbhani","Ratnagiri","Sangli","Satara","Sindhudurg","Wardha","Washim","Yavatmal","Kalyan-Dombivli",
    "Ulhasnagar","Vasai-Virar","Sangli-Miraj-Kupwad","Nanded-Waghala","Bandra (Mumbai)","Colaba (Mumbai)","Andheri (Mumbai)",
    "Navi Mumbai","Pimpri-Chinchwad (Pune)","Koregaon Park (Pune)","Kothrud (Pune)","Hadapsar (Pune)","Pune Cantonment",
    "Nashik Road","Deolali (Nashik)","Satpur (Nashik)","Aurangabad City","Jalgaon City","Bhopalwadi (Aurangabad)",
    "Nagpur City","Sitabuldi (Nagpur)","Jaripatka (Nagpur)","Solapur City","Hotgi (Solapur)","Pandharpur (Solapur)",
    "Amravati City","Badnera (Amravati)","Paratwada (Amravati)","Akola City","Murtizapur (Akola)","Washim City",
    "Mangrulpir (Washim)","Yavatmal City","Pusad (Yavatmal)","Darwha (Yavatmal)","Wardha City","Sindi (Wardha)",
    "Hinganghat (Wardha)","Chandrapur City","Brahmapuri (Chandrapur)","Mul (Chandrapur)","Gadchiroli",
    "Aheri (Gadchiroli)","Dhanora (Gadchiroli)","Gondia City","Tiroda (Gondia)","Arjuni Morgaon (Gondia)",
    "Bhandara City","Pauni (Bhandara)","Tumsar (Bhandara)","Nagbhid (Chandrapur)","Gadhinglaj (Kolhapur)",
    "Kagal (Kolhapur)","Ajra (Kolhapur)","Shiroli (Kolhapur)","Palghar City","Udgir","Osmanabad City"
])

coords = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
    "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Amravati": (20.93, 77.75),
    "Nanded": (19.16, 77.31), "Kolhapur": (16.70, 74.24), "Akola": (20.70, 77.00), "Latur": (18.40, 76.18),
    "Ahmadnagar": (19.10, 74.75), "Jalgaon": (21.00, 75.57), "Dhule": (20.90, 74.77), "Ichalkaranji": (16.69, 74.47),
    "Malegaon": (20.55, 74.53), "Bhusawal": (21.05, 76.00), "Bhiwandi": (19.30, 73.06), "Bhandara": (21.17, 79.65),
    "Beed": (18.99, 75.76), "Buldana": (20.54, 76.18), "Chandrapur": (19.95, 79.30), "Dharashiv": (18.40, 76.57),
    "Gondia": (21.46, 80.19), "Hingoli": (19.72, 77.15), "Jalna": (19.85, 75.89), "Mira-Bhayandar": (19.28, 72.87),
    "Nandurbar": (21.37, 74.22), "Osmanabad": (18.18, 76.07), "Palghar": (19.70, 72.77), "Parbhani": (19.27, 76.77),
    "Ratnagiri": (16.99, 73.31), "Sangli": (16.85, 74.57), "Satara": (17.68, 74.02), "Sindhudurg": (16.24, 73.42),
    "Wardha": (20.75, 78.60), "Washim": (20.11, 77.13), "Yavatmal": (20.39, 78.12), "Kalyan-Dombivli": (19.24, 73.13),
    "Ulhasnagar": (19.22, 73.16), "Vasai-Virar": (19.37, 72.81), "Sangli-Miraj-Kupwad": (16.85, 74.57), "Nanded-Waghala": (19.16, 77.31),
    "Bandra (Mumbai)": (19.06, 72.84), "Colaba (Mumbai)": (18.92, 72.82), "Andheri (Mumbai)": (19.12, 72.84),
    "Navi Mumbai": (19.03, 73.00), "Pimpri-Chinchwad (Pune)": (18.62, 73.80), "Koregaon Park (Pune)": (18.54, 73.90),
    "Kothrud (Pune)": (18.50, 73.81), "Hadapsar (Pune)": (18.51, 73.94), "Pune Cantonment": (18.50, 73.89),
    "Nashik Road": (20.00, 73.79), "Deolali (Nashik)": (19.94, 73.82), "Satpur (Nashik)": (20.01, 73.79),
    "Aurangabad City": (19.88, 75.34), "Jalgaon City": (21.00, 75.57), "Bhopalwadi (Aurangabad)": (19.88, 75.34),
    "Nagpur City": (21.15, 79.08), "Sitabuldi (Nagpur)": (21.14, 79.08), "Jaripatka (Nagpur)": (21.12, 79.07),
    "Solapur City": (17.67, 75.91), "Hotgi (Solapur)": (17.57, 75.95), "Pandharpur (Solapur)": (17.66, 75.32),
    "Amravati City": (20.93, 77.75), "Badnera (Amravati)": (20.84, 77.73), "Paratwada (Amravati)": (21.06, 77.21),
    "Akola City": (20.70, 77.00), "Murtizapur (Akola)": (20.73, 77.37), "Washim City": (20.11, 77.13),
    "Mangrulpir (Washim)": (20.31, 77.05), "Yavatmal City": (20.39, 78.12), "Pusad (Yavatmal)": (19.91, 77.57),
    "Darwha (Yavatmal)": (20.31, 77.78), "Wardha City": (20.75, 78.60), "Sindi (Wardha)": (20.82, 78.09),
    "Hinganghat (Wardha)": (20.58, 78.58), "Chandrapur City": (19.95, 79.30), "Brahmapuri (Chandrapur)": (20.61, 79.89),
    "Mul (Chandrapur)": (19.95, 79.06), "Gadchiroli": (20.09, 80.11), "Aheri (Gadchiroli)": (19.37, 80.18),
    "Dhanora (Gadchiroli)": (19.95, 80.15), "Gondia City": (21.46, 80.19), "Tiroda (Gondia)": (21.28, 79.68),
    "Arjuni Morgaon (Gondia)": (21.29, 80.20), "Bhandara City": (21.17, 79.65), "Pauni (Bhandara)": (21.07, 79.81),
    "Tumsar (Bhandara)": (21.37, 79.75), "Nagbhid (Chandrapur)": (20.29, 79.36), "Gadhinglaj (Kolhapur)": (16.23, 74.34),
    "Kagal (Kolhapur)": (16.57, 74.31), "Ajra (Kolhapur)": (16.67, 74.22), "Shiroli (Kolhapur)": (16.70, 74.24),
    "Palghar City": (19.70, 72.77), "Udgir": (18.37, 77.12), "Osmanabad City": (18.18, 76.07)
}

# ---------------------------
# Streamlit setup
# ---------------------------
st.set_page_config(page_title="Cantata Tour", layout="wide", initial_sidebar_state="expanded")

# Sidebar: language + admin
with st.sidebar:
    st.markdown("## Settings")
    lang = st.radio("Language", ["ko","en","hi"], index=0, format_func=lambda x: {"en":"English","ko":"한국어","hi":"हिन्दी"}[x])
    _ = LANG[lang]
    st.markdown("---")

    # admin state init
    st.session_state.setdefault("admin", False)
    st.session_state.setdefault("show_pw", False)
    st.session_state.setdefault("guest_mode", False)

    if st.session_state.admin:
        st.success(_["admin_mode"] + " Active")
        if st.button(_["guest_mode"]):
            st.session_state.update(admin=False, guest_mode=True, show_pw=False)
            st.experimental_rerun()
        if st.button(_["reset_btn"]):
            for k in ["route","venues","dates","indoor_state"]: 
                st.session_state.pop(k, None)
            st.experimental_rerun()
    else:
        if st.button(_["admin_mode"]):
            st.session_state.show_pw = True
        if st.session_state.show_pw:
            pw = st.text_input(_["enter_password"], type="password")
            if st.button(_["submit"]):
                if pw == "0691":
                    st.session_state.update(admin=True, show_pw=False, guest_mode=False)
                    st.success("Activated")
                    st.experimental_rerun()
                else:
                    st.error("Incorrect password")

# After sidebar, set language strings
_ = LANG[lang]

# API Key
API_KEY = st.secrets.get("API_KEY", None)

# Session defaults
st.session_state.setdefault("route", [])
st.session_state.setdefault("venues", {})  # city -> DataFrame
st.session_state.setdefault("dates", {})
st.session_state.setdefault("indoor_state", {})

# Page title
st.title(f"🎄 {_['title']}")

# Layout: left controls, right map
left, right = st.columns([1,2])

with left:
    st.subheader(_["tour_route"])
    # available cities not already in route
    available = [c for c in cities if c not in st.session_state["route"]]
    if not available:
        st.info("All cities added.")
    else:
        next_city = st.selectbox(_["select_city"], options=available, key="next_city_select")
        if st.button(_["add_city"], key="add_city_btn"):
            st.session_state["route"].append(next_city)
            st.rerun()

    st.markdown("---")

    # Show route items
    if st.session_state["route"]:
        for idx, city in enumerate(st.session_state["route"]):
            df = st.session_state["venues"].get(city, pd.DataFrame(columns=["Venue","Seats","Type","Google Maps Link","Notes"]))
            # Header row: city name + date (if set)
            date_label = st.session_state["dates"].get(city)
            header = f"{idx+1}. {city}" + (f" — {date_label}" if date_label else "")
            with st.expander(header, expanded=False):
                # compact input row
                c1, c2, c3, c4 = st.columns([3,1,1,2])
                with c1:
                    venue_name = st.text_input(_["venue_name"], key=f"v_{city}")
                with c2:
                    seats = st.number_input(_["seats"], min_value=0, step=10, key=f"s_{city}")
                with c3:
                    cur = st.session_state["indoor_state"].get(city, _["outdoor"])
                    if st.button(cur, key=f"io_btn_{city}"):
                        st.session_state["indoor_state"][city] = _["indoor"] if cur == _["outdoor"] else _["outdoor"]
                        st.rerun()
                with c4:
                    google_link = st.text_input(_["google_link"], key=f"l_{city}")
                notes = st.text_area(_["special_notes"], key=f"n_{city}", height=80)

                date_val = st.date_input(_["performance_date"], value=st.session_state["dates"].get(city, datetime.now().date()), key=f"d_{city}")
                st.session_state["dates"][city] = date_val

                # Register (admin only)
                if st.session_state.get("admin", False):
                    if st.button(_["register"], key=f"reg_{city}"):
                        if not venue_name:
                            st.error(_["venue_name"] + " is required")
                        else:
                            new_row = {
                                "Venue": venue_name,
                                "Seats": int(seats) if seats else 0,
                                "Type": st.session_state["indoor_state"].get(city, _["outdoor"]),
                                "Google Maps Link": google_link or "",
                                "Notes": notes or ""
                            }
                            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                            st.session_state["venues"][city] = df
                            # clear inputs
                            for k in [f"v_{city}", f"s_{city}", f"l_{city}", f"n_{city}"]:
                                st.session_state.pop(k, None)
                            st.success(_["venue_registered"])
                            st.rerun()
                else:
                    st.info("Guest mode: viewing only. Log in as admin to edit.")

                # Show registered venues
                if not df.empty:
                    st.table(df[["Venue","Seats","Type"]])

            # show distance/time to next city (if coords and API key)
            if idx < len(st.session_state["route"]) - 1:
                a = city
                b = st.session_state["route"][idx+1]
                if a in coords and b in coords and API_KEY:
                    res = get_distance_duration(coords[a], coords[b], API_KEY)
                    if res:
                        dist_txt, _, dur_txt, _ = res
                        st.markdown(f"**{_['distance']}**: {dist_txt} | **{_['time']}**: {dur_txt}")

with right:
    st.subheader(_["tour_map"])
    center = coords.get(st.session_state["route"][0] if st.session_state["route"] else "Mumbai", (19.07, 75.71))
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")

    pts = [coords[c] for c in st.session_state["route"] if c in coords]
    if pts:
        folium.PolyLine(pts, color="red", weight=4, dash_array="10,10").add_to(m)
        if len(pts) > 1 and API_KEY:
            for i in range(len(pts)-1):
                res = get_distance_duration(pts[i], pts[i+1], API_KEY)
                if res:
                    dist_txt, _, dur_txt, _ = res
                    mid_lat = (pts[i][0] + pts[i+1][0]) / 2
                    mid_lng = (pts[i][1] + pts[i+1][1]) / 2
                    folium.Marker(
                        location=[mid_lat, mid_lng],
                        icon=folium.DivIcon(
                            html=f"<div style='font-size:12px;color:#8B0000;background:white;padding:2px;border-radius:4px;'>{dist_txt} | {dur_txt}</div>"
                        )
                    ).add_to(m)

    for city in st.session_state["route"]:
        if city in coords:
            folium.CircleMarker(location=coords[city], radius=10, color="#90EE90", fill_color="#8B0000", popup=city).add_to(m)

    st_folium(m, width=800, height=650)

# Footer notes
st.markdown("---")
st.caption("Tip: Set your Google API key in .streamlit/secrets.toml to enable distance/time calculations.")
