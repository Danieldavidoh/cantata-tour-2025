import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import math, random
from datetime import datetime

# ------------------------------------------------------------
# 1. CONFIG & LANG
# ------------------------------------------------------------
st.set_page_config(page_title="Cantata Tour 2025", layout="wide", initial_sidebar_state="collapsed")
LANG = {  # (기존 LANG 그대로 복사 – 생략)
    "en": { "title": "Cantata Tour 2025", "add_city": "Add City", ... },
    "ko": { "title": "칸타타 투어 2025", "add_city": "도시 추가", ... },
    "hi": { "title": "कांताता टूर 2025", "add_city": "शहर जोड़ें", ... },
}
# ------------------------------------------------------------
# 2. CSS + 장식 (한 번에 삽입)
# ------------------------------------------------------------
st.markdown(f"""
<style>
    .reportview-container {{background:linear-gradient(#0f0c29,#302b63,#24243e);overflow:hidden;position:relative}}
    .christmas-title {{font-size:3.5em!important;font-weight:bold;text-align:center;text-shadow:0 0 5px #FFF,0 0 10px #FFF,0 0 15px #FFF,0 0 20px #8B0000;}}
    .christmas-title .main {{color:#FF0000!important}} .christmas-title .year {{color:white!important;text-shadow:0 0 5px #FFF,0 0 20px #00BFFF}}
    .stButton>button {{background:#228B22;color:white;border:2px solid #8B0000;border-radius:12px;font-weight:bold}}
    .stButton>button:hover {{background:#8B0000}}
    .christmas-decoration {{position:absolute;font-size:2.5em;pointer-events:none;animation:float 6s infinite;z-index:10}}
    @keyframes float {{0%,100%{{transform:translateY(0) rotate(0)}} 50%{{transform:translateY(-20px) rotate(5deg)}}}}
    .snowflake {{position:absolute;color:rgba(255,255,255,.9);font-size:1.2em;pointer-events:none;animation:fall linear infinite}}
    @keyframes fall {{0%{{transform:translateY(-100vh)}} 100%{{transform:translateY(100vh) rotate(360deg);opacity:0}}}}
</style>
<div class="christmas-decoration" style="top:8%;left:5%;color:#FFD700">🎁</div>
<div class="christmas-decoration" style="top:8%;right:5%;color:#FF0000;transform:rotate(15deg)">🍭</div>
<div class="christmas-decoration" style="top:25%;left:3%;color:#8B0000">🧦</div>
<div class="christmas-decoration" style="top:25%;right:3%;color:#FFD700">🔔</div>
<div class="christmas-decoration" style="top:45%;left:2%;color:#228B22">🌿</div>
<div class="christmas-decoration" style="top:45%;right:2%;color:#FF0000">🎅</div>
<div class="christmas-decoration" style="bottom:20%;left:10%;color:#228B22">🎄</div>
<div class="christmas-decoration" style="bottom:20%;right:10%;color:white">⛄</div>
<div class="christmas-decoration" style="top:65%;left:8%;color:#FFA500">🕯️</div>
<div class="christmas-decoration" style="top:65%;right:8%;color:#FFD700">⭐</div>
{''.join(f'<div class="snowflake" style="left:{random.randint(0,100)}%;font-size:{random.choice([".8","1","1.2","1.4"])}em;animation-duration:{random.uniform(8,20):.1f}s;animation-delay:{random.uniform(0,5):.1f}s">❄️</div>' for _ in range(80))}
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# 3. SIDEBAR (언어 + 관리자)
# ------------------------------------------------------------
with st.sidebar:
    lang = st.radio("Language", ["en","ko","hi"], format_func=lambda x: {"en":"EN","ko":"KR","hi":"HI"}[x])
    _ = LANG[lang]
    for k in ["admin","show_pw","guest_mode"]: st.session_state.setdefault(k, False)
    if st.session_state.admin:
        st.success("ADMIN ON")
        if st.button(_["guest_mode"]): st.session_state.update(admin=False, guest_mode=True, show_pw=True); st.rerun()
    else:
        if st.button(_["admin_mode"]): st.session_state.show_pw = True
        if st.session_state.show_pw:
            pw = st.text_input(_["enter_password"], type="password")
            if st.button(_["submit"]) and pw == "0691":
                st.session_state.update(admin=True, show_pw=False, guest_mode=False); st.success("ON"); st.rerun()
            elif st.button(_["submit"]): st.error("X")
    if st.session_state.admin and st.button(_["reset_btn"]):
        for k in ["route","dates","venues","admin_venues"]: st.session_state.pop(k, None); st.rerun()

# ------------------------------------------------------------
# 4. 세션 초기화 + 도시/좌표
# ------------------------------------------------------------
cols = ["Venue","Seats","IndoorOutdoor","Google Maps Link","Special Notes"]
for k in ["route","dates","venues","admin_venues"]:
    st.session_state.setdefault(k, [] if k=="route" else {} if "dates" in k else {})
cities = sorted([...])  # (기존 도시 리스트 그대로)
coords = { ... }  # (기존 좌표 딕셔너리 그대로)

# ------------------------------------------------------------
# 5. 제목
# ------------------------------------------------------------
parts = _["title"].rsplit(" ",1)
title_html = f'<span class="main">{parts[0]}</span> <span class="year">{parts[1] if len(parts)>1 else ""}</span>'
if lang=="ko": title_html = f'<span class="main">{_[\"title\"].split()[0]}</span> <span class="year">{" ".join(_["title"].split()[1:])}</span>'
st.markdown(f'<h1 class="christmas-title">{title_html}</h1>', unsafe_allow_html=True)

# ------------------------------------------------------------
# 6. 헬퍼 함수
# ------------------------------------------------------------
def target(): return st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
def date_str(city): 
    d = st.session_state.dates.get(city)
    return d.strftime(_["date_format"]) if d else "TBD"
def nav_link(url): return f"https://www.google.com/maps/dir/?api=1&destination={url}&travelmode=driving" if url and url.startswith("http") else ""
def add_venue(city, row):
    t = target()
    t[city] = pd.concat([t.get(city, pd.DataFrame(columns=cols)), pd.DataFrame([row])], ignore_index=True)

# ------------------------------------------------------------
# 7. LEFT: 도시 추가 + 공연장 관리
# ------------------------------------------------------------
left, right = st.columns([1,3])
with left:
    avail = [c for c in cities if c not in st.session_state.route]
    if avail:
        c1,c2 = st.columns([2,1])
        with c1: next_city = st.selectbox(_["select_city"], avail)
        with c2: st.button(_["add_city_btn"], on_click=lambda: st.session_state.route.append(next_city) or st.rerun())
    if st.session_state.route:
        st.subheader(_["venues_dates"])
        for city in st.session_state.route:
            t = target()
            has = city in t and not t[city].empty
            icon = f' [🗺️]({nav_link(t[city].iloc[0]["Google Maps Link"])})' if has else ""
            with st.expander(f"**{city}** – {date_str(city)} ({len(t[city]) if has else 0} venues){icon}"):
                # 날짜
                cur = st.session_state.dates.get(city, datetime.now().date())
                if st.date_input(_["performance_date"], cur, key=f"d_{city}") != cur:
                    st.session_state.dates[city] = _; st.success(_["date_changed"]); st.rerun()
                # 등록 폼
                if (st.session_state.admin or st.session_state.guest_mode) and not has:
                    v = st.text_input(_["venue_name"], key=f"v_{city}")
                    s = st.number_input(_["seats"], 1, step=50, key=f"s_{city}")
                    l = st.text_input(_["google_link"], key=f"l_{city}")
                    io = st.session_state[f"io_{city}"] = st.session_state.get(f"io_{city}", _["outdoor"])
                    if st.button(f"**{io}**", key=f"io_{city}"):
                        st.session_state[f"io_{city}"] = _["indoor"] if io==_["outdoor"] else _["outdoor"]; st.rerun()
                    n = st.text_area(_["special_notes"], key=f"n_{city}")
                    if st.button(_["register"], key=f"reg_{city}") and v:
                        add_venue(city, {"Venue":v,"Seats":s,"IndoorOutdoor":io,"Google Maps Link":l,"Special Notes":n})
                        for k in [f"v_{city}",f"s_{city}",f"l_{city}",f"n_{city}"]: st.session_state.pop(k,None)
                        st.success(_["venue_registered"]); st.rerun()
                    elif st.button(_["register"], key=f"reg_{city}"): st.error(_["enter_venue_name"])
                # 목록
                if has:
                    for i,row in t[city].iterrows():
                        c1,c2,c3,c4 = st.columns([3,1,1,1])
                        with c1: st.write(f"**{row.Venue}**"); st.caption(f"{row.Seats} seats | {row['Special Notes']}")
                        with c2: st.write(f"{'🟢' if row.IndoorOutdoor==_['indoor'] else '🔵'} {row.IndoorOutdoor}")
                        with c3: st.markdown(f"[🗺️ {_['navigate']}]({nav_link(row['Google Maps Link'])})", unsafe_allow_html=True)
                        with c4:
                            if st.session_state.admin or st.session_state.guest_mode:
                                ek = f"e_{city}_{i}"
                                if st.button("Edit", key=f"eb_{city}_{i}"): st.session_state[ek]=True
                                if st.button("Del", key=f"db_{city}_{i}") and st.checkbox("Sure?", key=f"dc_{city}_{i}"):
                                    t[city].drop(i, inplace=True); t[city].reset_index(drop=True, inplace=True)
                                    if t[city].empty: t.pop(city,None); st.success(_["venue_deleted"]); st.rerun()
                        if st.session_state.get(ek):
                            with st.form(key=f"f_{city}_{i}"):
                                ev = st.text_input("Name", row.Venue, key=f"ev_{city}_{i}")
                                es = st.number_input("Seats", 1, value=row.Seats, key=f"es_{city}_{i}")
                                eio = st.selectbox("Type", [_["indoor"],_["outdoor"]], index=0 if row.IndoorOutdoor==_["indoor"] else 1, key=f"eio_{city}_{i}")
                                el = st.text_input("Link", row["Google Maps Link"], key=f"el_{city}_{i}")
                                en = st.text_area("Notes", row["Special Notes"], key=f"en_{city}_{i}")
                                if st.form_submit_button("Save"):
                                    t[city].loc[i] = [ev,es,eio,el,en]; st.session_state.pop(ek,None); st.success(_["venue_updated"]); st.rerun()

# ------------------------------------------------------------
# 8. RIGHT: 지도
# ------------------------------------------------------------
with right:
    st.subheader(_["tour_map"])
    m = folium.Map(location=coords.get(st.session_state.route[0] if st.session_state.route else "Mumbai", (19.75,75.71)), zoom_start=7, tiles="CartoDB positron")
    if len(st.session_state.route)>1:
        pts = [coords[c] for c in st.session_state.route]
        folium.PolyLine(pts, color="red", weight=4, dash_array="10,10").add_to(m)
        for a,b in zip(pts, pts[1:]):
            arrow = (b[0]-(b[0]-a[0])*0.05, b[1]-(b[1]-a[1])*0.05)
            folium.RegularPolygonMarker(arrow, fill_color="red", number_of_sides=3,
                rotation=math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))-90, radius=10).add_to(m)
    for city in st.session_state.route:
        df = target().get(city, pd.DataFrame())
        link = next((r["Google Maps Link"] for _,r in df.iterrows() if r["Google Maps Link"].startswith("http")), None)
        popup = f"<b style='color:#8B0000'>{city}</b><br>{date_str(city)}"
        if link: popup = f'<a href="{nav_link(link)}" target="_blank" style="color:#90EE90">{popup}<br><i>{_["navigate"]}</i></a>'
        folium.CircleMarker(coords[city], radius=15, color="#90EE90", fill_color="#8B0000",
                            popup=folium.Popup(popup, max_width=300)).add_to(m)
    st_folium(m, width=700, height=500)
    st.caption(_["caption"])
