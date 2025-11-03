
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import folium
from streamlit_folium import st_folium
import math

# ---------------------------
# Cantata Tour - Improved app.py
# UI style: 1 (table / compact)
# Features:
#  - Table-like venue input
#  - Indoor/Outdoor toggle (color change)
#  - Register button clearly at the bottom of the form
#  - Distance & travel time calculation via Google Distance Matrix API
#  - Folium map showing route & distances
# ---------------------------

# Language dictionary (minimal subset)
LANG = {
    "en": {"title": "Cantata Tour 2025", "select_city":"Select city", "add_city":"Add City",
           "performance_date":"Performance date", "venue_name":"Venue name", "seats":"Seats",
           "indoor":"Indoor","outdoor":"Outdoor","google_link":"Google Maps link","special_notes":"Special notes",
           "register":"Register","tour_route":"Tour Route","distance":"Distance","time":"Time","tour_map":"Tour Map"},
    "ko": {"title": "칸타타 투어 2025", "select_city":"도시 선택", "add_city":"도시 추가",
           "performance_date":"공연 날짜", "venue_name":"공연장 이름", "seats":"좌석 수",
           "indoor":"실내","outdoor":"실외","google_link":"구글 지도 링크","special_notes":"특이사항",
           "register":"등록","tour_route":"투어 경로","distance":"거리","time":"소요시간","tour_map":"투어 지도"},
    "hi": {"title":"कांताता टूर 2025","select_city":"शहर चुनें","add_city":"शहर जोड़ें",
           "performance_date":"प्रदर्शन तिथि","venue_name":"स्थल का नाम","seats":"सीटें",
           "indoor":"इंडोर","outdoor":"आउटडोर","google_link":"गूगल मैप्स लिंक","special_notes":"विशेष टिप्पणियाँ",
           "register":"रजिस्टर","tour_route":"टूर मार्ग","distance":"दूरी","time":"समय","tour_map":"टूर मैप"},
}

# ---------------------------
# Helper: Distance Matrix
# ---------------------------
def get_distance_duration(origin, destination, api_key):
    """
    origin, destination: (lat, lng)
    returns: (distance_text, distance_meters, duration_text, duration_seconds)
    Uses Google Distance Matrix API (driving)
    """
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
    except Exception as e:
        st.error(f"Distance API error: {e}")
    return None

# ---------------------------
# Small city list + coords (sample)
# ---------------------------
cities = ["Mumbai","Pune","Nagpur","Nashik","Thane","Aurangabad","Solapur","Amravati"]
coords = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
    "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Amravati": (20.93, 77.75),
}

# ---------------------------
# Streamlit page setup
# ---------------------------
st.set_page_config(page_title="Cantata Tour", layout="wide")
st.title("🎄 " + "Cantata Tour 2025")

# language selector
lang = st.sidebar.radio("Language", ["ko","en","hi"], index=0, format_func=lambda x: {"en":"English","ko":"한국어","hi":"हिन्दी"}[x])
_ = LANG[lang]

# API key from secrets
API_KEY = st.secrets.get("API_KEY", None)

# initialize session state
st.session_state.setdefault("route", [])  # list of city names
st.session_state.setdefault("venues", {}) # dict: city -> dataframe of venues
st.session_state.setdefault("dates", {})  # city -> date
st.session_state.setdefault("indoor_state", {})  # city -> "실내"/"실외" label

# layout: left control, right map
left, right = st.columns([1,2])

with left:
    st.subheader(_["tour_route"])
    # add city selector (compact)
    avail = [c for c in cities if c not in st.session_state["route"]]
    col1, col2 = st.columns([3,1])
    with col1:
        next_city = st.selectbox(_["select_city"], options=avail)
    with col2:
        if st.button(_["add_city"]):
            st.session_state["route"].append(next_city)
            st.experimental_rerun()

    st.markdown("---")

    if st.session_state["route"]:
        # show route with compact table-style controls
        for i, city in enumerate(st.session_state["route"]):
            st.markdown(f"### {city}")
            df = st.session_state["venues"].get(city, pd.DataFrame(columns=['Venue','Seats','Type','Google Maps Link','Notes']))
            # show existing venues for city
            if not df.empty:
                st.table(df[['Venue','Seats','Type']].assign(**{_["distance"]:"", _["time"]:""}))
            # compact input row - table like using columns
            vcol1, vcol2, vcol3, vcol4 = st.columns([3,1,1,3])
            with vcol1:
                venue_name = st.text_input(_["venue_name"], key=f"v_{city}")
            with vcol2:
                seats = st.number_input(_["seats"], min_value=0, step=10, key=f"s_{city}")
            with vcol3:
                # indoor/outdoor toggle as a two-state button
                cur = st.session_state["indoor_state"].get(city, _["outdoor"])
                if st.button(cur, key=f"io_{city}"):
                    # toggle
                    st.session_state["indoor_state"][city] = _["indoor"] if cur == _["outdoor"] else _["outdoor"]
                    st.experimental_rerun()
            with vcol4:
                google_link = st.text_input(_["google_link"], key=f"l_{city}")
            # notes (full width)
            notes = st.text_area(_["special_notes"], key=f"n_{city}", height=80)

            # date picker
            date_val = st.date_input(_["performance_date"], value=st.session_state["dates"].get(city, datetime.now().date()), key=f"d_{city}")
            st.session_state["dates"][city] = date_val

            # register button (clear and placed under inputs)
            if st.button(_["register"], key=f"reg_{city}"):
                if not venue_name:
                    st.error(_["venue_name"] + " " + "is required")
                else:
                    new_row = {
                        "Venue": venue_name,
                        "Seats": seats,
                        "Type": st.session_state["indoor_state"].get(city, _["outdoor"]),
                        "Google Maps Link": google_link or "",
                        "Notes": notes or ""
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state["venues"][city] = df
                    # clear inputs
                    for k in [f"v_{city}", f"s_{city}", f"l_{city}", f"n_{city}"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.success(_("venue_registered") if False else "Registered")
                    st.experimental_rerun()

            st.markdown("---")

        # compute segment distances if 2+ cities
        if len(st.session_state["route"]) > 1 and API_KEY:
            distances = []
            total_m = 0
            total_s = 0
            for i in range(len(st.session_state["route"]) - 1):
                a = st.session_state["route"][i]
                b = st.session_state["route"][i+1]
                if a in coords and b in coords:
                    res = get_distance_duration(coords[a], coords[b], API_KEY)
                    if res:
                        distance_text, distance_m, duration_text, duration_s = res
                        distances.append((a,b,distance_text,duration_text,distance_m,duration_s))
                        total_m += distance_m
                        total_s += duration_s
            # display summary
            if distances:
                st.subheader("Summary")
                for (a,b,dist_txt,dur_txt,_,_) in distances:
                    st.write(f"{a} → {b} : {_['distance'] if False else 'Distance'} {dist_txt} | {_['time'] if False else 'Time'} {dur_txt}")
                st.write("Total distance (km):", round(total_m/1000,2))
                st.write("Total time (h):", round(total_s/3600,2))
        elif len(st.session_state["route"]) > 1 and not API_KEY:
            st.info("API key not set. Distances will not be calculated. Put API_KEY in .streamlit/secrets.toml")

with right:
    st.subheader(_["tour_map"])
    center = coords.get(st.session_state["route"][0] if st.session_state["route"] else "Mumbai", (19.07, 75.71))
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")
    # draw route
    pts = [coords[c] for c in st.session_state["route"] if c in coords]
    if pts:
        folium.PolyLine(pts, color="red", weight=4, dash_array="10,10").add_to(m)
        # annotate midpoints with distances if API_KEY
        if len(pts) > 1 and API_KEY:
            for i in range(len(pts)-1):
                res = get_distance_duration(pts[i], pts[i+1], API_KEY)
                if res:
                    dist_txt, _, dur_txt, _ = res
                    mid_lat = (pts[i][0]+pts[i+1][0])/2
                    mid_lng = (pts[i][1]+pts[i+1][1])/2
                    folium.map.Marker([mid_lat, mid_lng], icon=folium.DivIcon(html=f\"<div style='font-size:12px;color:#8B0000;background:white;padding:2px;border-radius:4px;'>{dist_txt} | {dur_txt}</div>\")).add_to(m)
    # add markers
    for city in st.session_state["route"]:
        if city in coords:
            folium.CircleMarker(location=coords[city], radius=10, color="#90EE90", fill_color="#8B0000", popup=city).add_to(m)
    st_folium(m, width=700, height=600)
