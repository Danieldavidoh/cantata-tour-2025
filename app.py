import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
import math
import random

# ------------------- 1. 다국어 -------------------
LANG = {
    "en": {"title": "Cantata Tour 2025", "add_city": "Add City", "select_city": "Select City", "add_city_btn": "Add City",
           "performance_date": "Performance Date", "venue_name": "Venue Name", "seats": "Seats", "google_link": "Google Maps Link",
           "special_notes": "Special Notes", "register": "Register", "navigate": "Navigate", "date_format": "%b %d, %Y",
           "admin_mode": "Admin Mode", "guest_mode": "Guest Mode", "enter_password": "Enter password", "submit": "Submit",
           "reset_btn": "Reset All", "venue_registered": "Registered", "enter_venue_name": "Enter venue name"},
    "ko": {"title": "칸타타 투어 2025", "add_city": "도시 추가", "select_city": "도시 선택", "add_city_btn": "도시 추가",
           "performance_date": "공연 날짜", "venue_name": "공연장 이름", "seats": "좌석 수", "google_link": "구글 지도 링크",
           "special_notes": "특이사항", "register": "등록", "navigate": "길찾기", "date_format": "%Y년 %m월 %d일",
           "admin_mode": "관리자 모드", "guest_mode": "손님 모드", "enter_password": "비밀번호 입력", "submit": "제출",
           "reset_btn": "전체 초기화", "venue_registered": "등록 완료", "enter_venue_name": "공연장 이름 입력"},
    "hi": {"title": "कांताता टूर 2025", "add_city": "शहर जोड़ें", "select_city": "शहर चुनें", "add_city_btn": "शहर जोड़ें",
           "performance_date": "प्रदर्शन तिथि", "venue_name": "स्थल का नाम", "seats": "सीटें", "google_link": "गूगल मैप्स लिंक",
           "special_notes": "विशेष टिप्पणियाँ", "register": "रजिस्टर", "navigate": "नेविगेट करें", "date_format": "%d %b %Y",
           "admin_mode": "एडमिन मोड", "guest_mode": "गेस्ट मोड", "enter_password": "पासवर्ड दर्ज करें", "submit": "जमा करें",
           "reset_btn": "सब रीसेट करें", "venue_registered": "पंजीकरण सफल", "enter_venue_name": "स्थल का नाम दर्ज करें"},
}
_ = LANG[st.sidebar.radio("Language", ["en","ko","hi"], format_func=lambda x: {"en":"EN","ko":"KO","hi":"HI"}[x])]

# ------------------- 2. 설정 -------------------
st.set_page_config(page_title="Cantata Tour 2025", layout="wide", initial_sidebar_state="collapsed")

# ------------------- 3. 테마 -------------------
st.markdown("""
<style>
    .reportview-container {background:linear-gradient(#0f0c29,#302b63,#24243e);}
    .christmas-title {font-size:3.5em!important;text-align:center;color:#FF0000;text-shadow:0 0 20px #8B0000;}
    .christmas-title .year {color:white;text-shadow:0 0 20px #00BFFF;}
    h1,h2,h3 {color:#90EE90;text-shadow:1px 1px 3px #8B0000;text-align:center;}
    .stButton>button {background:#228B22;color:white;border:2px solid #8B0000;border-radius:12px;}
    .stButton>button:hover {background:#8B0000;}
    .stExpander {background:rgba(139,0,0,0.4);border:1px solid #90EE90;border-radius:12px;}
    .stExpander>summary {color:#90EE90;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# ------------------- 4. 세션 & 데이터 -------------------
cols = ["Venue","Seats","IndoorOutdoor","Google Maps Link","Special Notes"]
for k in ["route","dates","venues","admin_venues"]: st.session_state.setdefault(k, [] if k=="route" else {})

cities = sorted([...])  # 기존 도시 리스트 (생략)
coords = { ... }  # 기존 좌표 (생략)

def target(): return st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
def date_str(c): return st.session_state.dates.get(c, datetime.now().date()).strftime(_["date_format"])
def nav(url): return f"https://www.google.com/maps/dir/?api=1&destination={url}&travelmode=driving" if url and url.startswith("http") else ""

# ------------------- 5. 사이드바 -------------------
with st.sidebar:
    st.markdown("### Admin")
    st.session_state.admin = st.session_state.get("admin", False)
    if st.session_state.admin:
        st.success("Admin Mode")
        if st.button(_["guest_mode"]): st.session_state.admin = False; st.rerun()
    else:
        if st.button(_["admin_mode"]): st.session_state.show_pw = True
        if st.session_state.get("show_pw"):
            pw = st.text_input(_["enter_password"], type="password")
            if st.button(_["submit"]):
                if pw == "0691": st.session_state.admin = True; st.success("Activated!"); st.rerun()
                else: st.error("Incorrect")
    if st.session_state.admin and st.button(_["reset_btn"]):
        for k in ["route","dates","venues","admin_venues"]: st.session_state.pop(k, None)
        st.rerun()

# ------------------- 6. 제목 -------------------
title_parts = _["title"].rsplit(" ", 1) if lang != "ko" else _["title"].split()
st.markdown(f'<h1 class="christmas-title"><span class="main">{title_parts[0]}</span> <span class="year">{" ".join(title_parts[1:])}</span></h1>', unsafe_allow_html=True)

# ------------------- 7. 도시 박스 렌더링 -------------------
def render_city_expander(city):
    t = target()
    has = city in t and not t.get(city, pd.DataFrame()).empty
    car = f' <span style="float:right">[🚗]({nav(t[city].iloc[0]["Google Maps Link"])})</span>' if has and t[city].iloc[0]["Google Maps Link"].startswith("http") else ""
    with st.expander(f"**{city}** – {date_str(city)}{car}", expanded=not has):
        # 날짜
        new = st.date_input(_["performance_date"], st.session_state.dates.get(city, datetime.now().date()), key=f"d_{city}", format="YYYY-MM-DD")
        if new != st.session_state.dates.get(city): st.session_state.dates[city] = new; st.success("날짜 변경"); st.rerun()

        # 등록 폼
        if (st.session_state.admin or st.session_state.get("guest_mode")) and not has:
            c1, c2 = st.columns([3,1])
            with c1: venue = st.text_input(_["venue_name"], key=f"v_{city}")
            with c2: seats = st.number_input(_["seats"], 1, step=50, key=f"s_{city}")
            c3, c4 = st.columns([3,1])
            with c3: link = st.text_input(_["google_link"], placeholder="https://...", key=f"l_{city}")
            with c4:
                io = st.session_state[f"io_{city}"] = st.session_state.get(f"io_{city}", _["outdoor"])
                if st.button(f"**{io}**", key=f"io_{city}"): st.session_state[f"io_{city}"] = _["indoor"] if io == _["outdoor"] else _["outdoor"]; st.rerun()
            sn, btn = st.columns([4,1])
            with sn: notes = st.text_area(_["special_notes"], key=f"n_{city}")
            with btn:
                if st.button(_["register"], key=f"r_{city}"):
                    if not venue: st.error(_["enter_venue_name"])
                    else:
                        t[city] = pd.concat([t.get(city, pd.DataFrame(columns=cols)), pd.DataFrame([{
                            "Venue": venue, "Seats": seats, "IndoorOutdoor": st.session_state[f"io_{city}"],
                            "Google Maps Link": link, "Special Notes": notes
                        }])], ignore_index=True)
                        st.success(_["venue_registered"])
                        for k in [f"v_{city}", f"s_{city}", f"l_{city}", f"n_{city}"]: st.session_state.pop(k, None)
                        st.rerun()

        # 등록된 공연장
        if has:
            for idx, row in t[city].iterrows():
                c1, c2, c3, c4 = st.columns([3,1,1,1])
                with c1: st.write(f"**{row['Venue']}**"); st.caption(f"{row['Seats']} seats | {row.get('Special Notes','')}")
                with c2: st.write(f"{'실내' if row['IndoorOutdoor'] == _['indoor'] else '실외'}")
                with c3:
                    if row["Google Maps Link"].startswith("http"):
                        st.markdown(f'<div style="text-align:right">[🚗]({nav(row["Google Maps Link"])})</div>', unsafe_allow_html=True)
                with c4:
                    if st.session_state.admin or st.session_state.get("guest_mode"):
                        if st.button("삭제", key=f"del_{city}_{idx}"):
                            if st.checkbox("확인", key=f"chk_{city}_{idx}"):
                                t[city].drop(idx, inplace=True)
                                if t[city].empty: t.pop(city)
                                st.success("삭제 완료"); st.rerun()

# ------------------- 8. 메인 레이아웃 -------------------
left, right = st.columns([1,3])
with left:
    avail = [c for c in cities if c not in st.session_state.route]
    if avail:
        c1, c2 = st.columns([2,1])
        with c1: next_city = st.selectbox(_["select_city"], avail, key="next_city")
        with c2:
            if st.button(_["add_city_btn"], key="add_btn"):
                st.session_state.route.append(next_city)
                st.rerun()
    if st.session_state.route:
        for city in st.session_state.route:
            render_city_expander(city)

# ------------------- 9. 지도 -------------------
with right:
    st.subheader("Tour Map")
    m = folium.Map(location=coords.get(st.session_state.route[0] if st.session_state.route else "Mumbai", (19.75, 75.71)), zoom_start=7, tiles="CartoDB positron")
    if len(st.session_state.route) > 1:
        points = [coords[c] for c in st.session_state.route]
        folium.PolyLine(points, color="red", weight=4, dash_array="10,10").add_to(m)
        for i in range(len(points)-1):
            s, e = points[i], points[i+1]
            folium.RegularPolygonMarker(
                location=[e[0] - (e[0]-s[0])*0.05, e[1] - (e[1]-s[1])*0.05],
                fill_color="red", number_of_sides=3,
                rotation=math.degrees(math.atan2(e[1]-s[1], e[0]-s[0])) - 90, radius=10
            ).add_to(m)
    for city in st.session_state.route:
        df = target().get(city, pd.DataFrame())
        link = next((r["Google Maps Link"] for _, r in df.iterrows() if r["Google Maps Link"].startswith("http")), None)
        popup = f"<b>{city}</b><br>{date_str(city)}"
        if link: popup = f'<a href="{nav(link)}" target="_blank" style="color:#90EE90">{popup}<br><i>길찾기</i></a>'
        folium.CircleMarker(location=coords[city], radius=15, color="#90EE90", fill_color="#8B0000", popup=folium.Popup(popup, max_width=300)).add_to(m)
    st_folium(m, width=700, height=500)
