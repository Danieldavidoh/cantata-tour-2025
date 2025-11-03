
import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath

# --- language (kept small) ---
LANG = {
    "ko": {"title":"칸타타 투어 2025","select_city":"도시 선택","add_city":"도시 추가","register":"등록",
           "venue":"공연장","seats":"좌석 수","indoor":"실내","outdoor":"실외","google":"구글 링크",
           "notes":"특이사항","tour_map":"투어 지도","tour_route":"투어 경로","password":"관리자 비밀번호","login":"로그인","logout":"로그아웃"},
    "en": {"title":"Cantata Tour 2025","select_city":"Select city","add_city":"Add City","register":"Register",
           "venue":"Venue","seats":"Seats","indoor":"Indoor","outdoor":"Outdoor","google":"Google link",
           "notes":"Notes","tour_map":"Tour Map","tour_route":"Tour Route","password":"Admin password","login":"Log in","logout":"Log out"}
}

# --- cities and coords (sample expanded list) ---
cities = sorted([
    "Mumbai","Pune","Nagpur","Nashik","Thane","Aurangabad","Solapur","Amravati","Nanded","Kolhapur",
    "Akola","Latur","Ahmadnagar","Jalgaon","Dhule","Malegaon","Bhusawal","Bhiwandi","Bhandara","Beed"
])
coords = {
    "Mumbai": (19.07,72.88),"Pune":(18.52,73.86),"Nagpur":(21.15,79.08),"Nashik":(20.00,73.79),"Thane":(19.22,72.98),
    "Aurangabad":(19.88,75.34),"Solapur":(17.67,75.91),"Amravati":(20.93,77.75),"Nanded":(19.16,77.31),"Kolhapur":(16.70,74.24),
    "Akola":(20.70,77.00),"Latur":(18.40,76.18),"Ahmadnagar":(19.10,74.75),"Jalgaon":(21.00,75.57),"Dhule":(20.90,74.77),
    "Malegaon":(20.55,74.53),"Bhusawal":(21.05,76.00),"Bhiwandi":(19.30,73.06),"Bhandara":(21.17,79.65),"Beed":(18.99,75.76)
}

# --- Streamlit setup ---
st.set_page_config(page_title="Cantata Tour", layout="wide")
if "lang" not in st.session_state: st.session_state.lang = "ko"
if "admin" not in st.session_state: st.session_state.admin = False
if "route" not in st.session_state: st.session_state.route = []
if "venues" not in st.session_state: st.session_state.venues = {}  # city -> list of dicts (venues)
if "dates" not in st.session_state: st.session_state.dates = {}

# --- Sidebar: language + admin login ---
with st.sidebar:
    st.selectbox("Language / 언어", ["ko","en"], index=0, key="lang_select", on_change=lambda: st.session_state.update(lang=st.session_state.lang_select) )
    _ = LANG[st.session_state.lang]
    st.markdown("---")
    st.write("### Admin")
    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password", key="pw_input")
        if st.button(_["login"]):
            if pw == "0691":
                st.session_state.admin = True
                st.success("Admin activated")
            else:
                st.error("Wrong password")
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.success("Logged out")
    st.markdown("---")
    st.write("Tip: Add cities from the left panel. Click markers on the map to see details.")

# refresh language variable after possible change
_ = LANG[st.session_state.lang]

st.title(f"🎄 {_['title']}")

# --- Layout ---
left, right = st.columns([1,2])

with left:
    st.subheader(_["tour_route"])
    # city selector (only cities not in route)
    available = [c for c in cities if c not in st.session_state.route]
    if available:
        city = st.selectbox(_["select_city"], available, key="city_sel")
        if st.button(_["add_city"]):
            st.session_state.route.append(city)
            # initialize empty venue list for new city
            st.session_state.venues.setdefault(city, [])
            st.experimental_rerun()
    else:
        st.info("All cities added.")

    st.markdown("---")
    # For each city in route show expander with inputs and list of registered venues
    for idx, c in enumerate(st.session_state.route):
        header = f"{idx+1}. {c}"
        with st.expander(header, expanded=False):
            # inputs
            dcol1, dcol2 = st.columns([2,1])
            with dcol1:
                date = st.date_input("Date", value=st.session_state.dates.get(c, datetime.now().date()), key=f"date_{c}")
                st.session_state.dates[c] = date
                venue_name = st.text_input("Venue name", key=f"vn_{c}")
                seats = st.number_input("Seats", min_value=0, step=10, key=f"se_{c}")
                google = st.text_input("Google Maps link (http...)", key=f"gl_{c}")
                notes = st.text_area("Notes", key=f"nt_{c}")
            with dcol2:
                # indoor/outdoor toggle
                cur = st.session_state.get("indoor_"+c, "Outdoor")
                if st.button(cur, key=f"iotoggle_{c}"):
                    st.session_state["indoor_"+c] = "Indoor" if cur == "Outdoor" else "Outdoor"
                st.write("")  # spacing

            # Register button - only for admin
            if st.session_state.admin:
                if st.button("Register venue", key=f"reg_{c}"):
                    if not venue_name:
                        st.error("Venue name required")
                    else:
                        entry = {"date": str(st.session_state.dates[c]), "venue": venue_name, "seats": int(seats),
                                 "type": st.session_state.get("indoor_"+c, "Outdoor"), "google": google, "notes": notes}
                        st.session_state.venues.setdefault(c, []).append(entry)
                        # clear inputs
                        for k in [f"vn_{c}", f"se_{c}", f"gl_{c}", f"nt_{c}"]:
                            if k in st.session_state: st.session_state.pop(k)
                        st.success("Registered")
                        st.experimental_rerun()
            else:
                st.info("Guest mode — log in as admin to register venues.")

            # show existing venues
            vlist = st.session_state.venues.get(c, [])
            if vlist:
                st.write("Registered venues:")
                for i, v in enumerate(vlist):
                    st.markdown(f"- **{v['venue']}** ({v['date']}) — {v['seats']} seats — {v['type']}")
                    if v["google"]:
                        st.markdown(f"  - [Open in Google Maps]({v['google']})")

with right:
    st.subheader(_["tour_map"])
    # center default
    center = (19.75, 75.71)
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")

    # draw AntPath (animated dashed) for route
    pts = [coords[c] for c in st.session_state.route if c in coords]
    if len(pts) >= 2:
        AntPath(pts, color="#d62728", weight=4, delay=1000).add_to(m)

    # add markers with popups showing registered info (or "no data")
    for c in st.session_state.route:
        loc = coords.get(c)
        if not loc: continue
        vlist = st.session_state.venues.get(c, [])
        popup_html = f"<b>{c}</b><br>"
        popup_html += f"<i>{st.session_state.dates.get(c,'')}</i><br>"
        if vlist:
            for v in vlist:
                popup_html += f"<hr><b>{v['venue']}</b><br>{v['date']} — {v['seats']} seats — {v['type']}<br>"
                if v['google']:
                    popup_html += f"<a href='{v['google']}' target='_blank'>Open Maps</a><br>"
                if v['notes']:
                    popup_html += f"<small>{v['notes']}</small><br>"
        else:
            popup_html += "<i>No venue data registered</i>"
        folium.CircleMarker(location=loc, radius=8, color="#1f9d8a", fill=True, fill_color="#d62728", popup=folium.Popup(popup_html, max_width=300)).add_to(m)

    st_folium(m, width=900, height=650)

# footer note
st.markdown('---')
st.caption("Fixed: admin login, animated/dashed route (AntPath), and detailed city popups.")

