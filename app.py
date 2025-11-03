
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import folium
from streamlit_folium import st_folium

# ---------------------------
# Language dictionary
# ---------------------------
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "select_city": "도시 선택",
        "add_city": "도시 추가",
        "tour_route": "투어 경로",
        "performance_date": "공연 날짜",
        "venue_name": "공연장 이름",
        "seats": "좌석 수",
        "indoor": "실내",
        "outdoor": "실외",
        "google_link": "구글 지도 링크",
        "special_notes": "특이사항",
        "register": "등록",
        "tour_map": "투어 지도",
        "distance": "거리",
        "time": "소요시간"
    }
}

# ---------------------------
# Distance API helper
# ---------------------------
def get_distance_duration(origin, destination, api_key):
    if not api_key:
        return None
    o = f"{origin[0]},{origin[1]}"
    d = f"{destination[0]},{destination[1]}"
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": o, "destinations": d, "mode": "driving", "key": api_key, "units": "metric"}
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        el = data["rows"][0]["elements"][0]
        if el["status"] == "OK":
            return (
                el["distance"]["text"],
                el["distance"]["value"],
                el["duration"]["text"],
                el["duration"]["value"]
            )
    except:
        return None
    return None

# ---------------------------
# Cities + Coordinates (example subset)
# ---------------------------
cities = ["Mumbai","Pune","Nagpur","Nashik"]
coords = {
    "Mumbai": (19.07, 72.88),
    "Pune": (18.52, 73.86),
    "Nagpur": (21.15, 79.08),
    "Nashik": (20.00, 73.79),
}

# ---------------------------
# Init App
# ---------------------------
st.set_page_config(page_title="Cantata Tour", layout="wide")
lang = "ko"
_ = LANG[lang]

st.title("🎄 " + _["title"])

API_KEY = st.secrets.get("API_KEY", None)

st.session_state.setdefault("route", [])
st.session_state.setdefault("venues", {})
st.session_state.setdefault("dates", {})
st.session_state.setdefault("indoor_state", {})

left, right = st.columns([1,2])

# ---------------------------
# LEFT PANEL
# ---------------------------
with left:
    st.subheader(_["tour_route"])

    # City Select
    available = [c for c in cities if c not in st.session_state.route]
    selected_city = st.selectbox(_["select_city"], available)

    if st.button(_["add_city"]):
        st.session_state.route.append(selected_city)
        st.rerun()

    st.markdown("---")

    # Per-city venue editor
    for city in st.session_state.route:
        st.markdown(f"### {city}")

        df = st.session_state.venues.get(city, pd.DataFrame(columns=["Venue","Seats","Type","Google Maps Link","Notes"]))

        # Inputs (compact table row style)
        venue = st.text_input(_["venue_name"], key=f"v_{city}")
        seats = st.number_input(_["seats"], min_value=0, step=10, key=f"s_{city}")
        current_type = st.session_state.indoor_state.get(city, _["outdoor"])

        if st.button(current_type, key=f"type_{city}"):
            st.session_state.indoor_state[city] = _["indoor"] if current_type == _["outdoor"] else _["outdoor"]
            st.rerun()

        link = st.text_input(_["google_link"], key=f"l_{city}")
        notes = st.text_area(_["special_notes"], key=f"n_{city}", height=70)

        date_val = st.date_input(_["performance_date"], value=st.session_state.dates.get(city, datetime.now().date()), key=f"d_{city}")
        st.session_state.dates[city] = date_val

        # Register button
        if st.button(_["register"], key=f"reg_{city}"):
            if venue:
                new_entry = {
                    "Venue": venue,
                    "Seats": seats,
                    "Type": st.session_state.indoor_state.get(city, _["outdoor"]),
                    "Google Maps Link": link or "",
                    "Notes": notes or ""
                }
                df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                st.session_state.venues[city] = df

                # Clear inputs
                for k in [f"v_{city}", f"s_{city}", f"l_{city}", f"n_{city}"]:
                    st.session_state.pop(k, None)

                st.success("등록 완료")
                st.rerun()
            else:
                st.error("공연장 이름은 필수입니다.")

        # Show list
        if not df.empty:
            st.table(df[["Venue","Seats","Type"]])

        st.markdown("---")

# ---------------------------
# RIGHT PANEL (MAP)
# ---------------------------
with right:
    st.subheader(_["tour_map"])
    center = coords.get(st.session_state.route[0], (19.07, 75.71))
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")

    points = [coords[c] for c in st.session_state.route if c in coords]

    if len(points) >= 2:
        folium.PolyLine(points, color="red", weight=4, dash_array="10,10").add_to(m)

        if API_KEY:
            for i in range(len(points)-1):
                dist = get_distance_duration(points[i], points[i+1], API_KEY)
                if dist:
                    dist_txt, _, dur_txt, _ = dist
                    mid_lat = (points[i][0] + points[i+1][0]) / 2
                    mid_lng = (points[i][1] + points[i+1][1]) / 2
                    folium.Marker(
                        location=[mid_lat, mid_lng],
                        icon=folium.DivIcon(
                            html=f"<div style='font-size:12px;color:#8B0000;background:white;padding:2px;border-radius:4px;'>{dist_txt} | {dur_txt}</div>"
                        )
                    ).add_to(m)

    # City markers
    for c in st.session_state.route:
        if c in coords:
            folium.CircleMarker(coords[c], radius=10, color="#90EE90", fill_color="#8B0000", popup=c).add_to(m)

    st_folium(m, width=750, height=600)
