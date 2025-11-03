
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import folium
from streamlit_folium import st_folium
import math

LANG = {
    "ko": {"title": "칸타타 투어 2025", "select_city":"도시 선택", "add_city":"도시 추가",
           "performance_date":"공연 날짜", "venue_name":"공연장 이름", "seats":"좌석 수",
           "indoor":"실내","outdoor":"실외","google_link":"구글 지도 링크","special_notes":"특이사항",
           "register":"등록","tour_route":"투어 경로","distance":"거리","time":"소요시간","tour_map":"투어 지도"},
}

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
        el = data["rows"][0]["elements"][0]
        if el["status"] == "OK":
            distance_text = el["distance"]["text"]
            distance_m = el["distance"]["value"]
            duration_text = el["duration"]["text"]
            duration_s = el["duration"]["value"]
            return distance_text, distance_m, duration_text, duration_s
    except:
        pass
    return None

cities = ["Mumbai","Pune","Nagpur","Nashik"]
coords = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
}

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

with left:
    st.subheader(_["tour_route"])
    avail = [c for c in cities if c not in st.session_state["route"]]
    next_city = st.selectbox(_["select_city"], options=avail)
    if st.button(_["add_city"]):
        st.session_state["route"].append(next_city)
        st.experimental_rerun()

    st.markdown("---")

    if st.session_state["route"]:
        for city in st.session_state["route"]:
            st.markdown(f"### {city}")
            df = st.session_state["venues"].get(city, pd.DataFrame(columns=['Venue','Seats','Type','Google Maps Link','Notes']))

            venue_name = st.text_input(_["venue_name"], key=f"v_{city}")
            seats = st.number_input(_["seats"], min_value=0, step=10, key=f"s_{city}")
            cur = st.session_state["indoor_state"].get(city, _["outdoor"])
            if st.button(cur, key=f"io_{city}"):
                st.session_state["indoor_state"][city] = _["indoor"] if cur == _["outdoor"] else _["outdoor"]
                st.experimental_rerun()
            google_link = st.text_input(_["google_link"], key=f"l_{city}")
            notes = st.text_area(_["special_notes"], key=f"n_{city}", height=80)

            date_val = st.date_input(_["performance_date"], value=st.session_state["dates"].get(city, datetime.now().date()), key=f"d_{city}")
            st.session_state["dates"][city] = date_val

            if st.button(_["register"], key=f"reg_{city}"):
                new_row = {
                    "Venue": venue_name,
                    "Seats": seats,
                    "Type": st.session_state["indoor_state"].get(city, _["outdoor"]),
                    "Google Maps Link": google_link or "",
                    "Notes": notes or ""
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state["venues"][city] = df
                for k in [f"v_{city}", f"s_{city}", f"l_{city}", f"n_{city}"]:
                    st.session_state.pop(k, None)
                st.success("등록 완료")
                st.experimental_rerun()

            if not df.empty:
                st.table(df[['Venue','Seats','Type']])

        if len(st.session_state["route"]) > 1 and API_KEY:
            for i in range(len(st.session_state["route"]) - 1):
                a = st.session_state["route"][i]
                b = st.session_state["route"][i+1]
                if a in coords and b in coords:
                    get_distance_duration(coords[a], coords[b], API_KEY)

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
            folium.CircleMarker(coords[city], radius=10, color="#90EE90", fill_color="#8B0000", popup=city).add_to(m)

    st_folium(m, width=700, height=600)
