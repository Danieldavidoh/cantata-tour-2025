import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
import math
import random
from geopy.distance import great_circle

# 1. 다국어 사전 (hi 포함)
LANG = {
    "en": {
        "title": "Cantata Tour 2025", "add_city": "Add City", "select_city": "Select City",
        "add_venue_btn": "Add Venue", "tour_route": "Tour Route", "remove": "Remove",
        "reset_btn": "Reset All", "performance_date": "Performance Date",
        "venue_name": "Venue Name", "seats": "Seats", "indoor_outdoor": "Indoor/Outdoor",
        "indoor": "Indoor", "outdoor": "Outdoor", "google_link": "Google Maps Link",
        "special_notes": "Special Notes", "register": "Register", "save": "Save",
        "tour_map": "Tour Map", "admin_mode": "Admin Mode", "guest_mode": "Guest Mode",
        "enter_password": "Enter password to access Admin Mode", "submit": "Submit",
        "drive_to": "Drive Here", "distance": "Distance (km)", "time": "Time (min)",
        "no_performance": "No Performance", "today_performance": "Today's Performance!",
        "past_performance": "Past Performance", "total_distance": "Total Distance",
        "total_time": "Total Time", "add_city_to_route": "Add City to Route",
        "city_placeholder": "Select City (Maharashtra)", "admin_input_mode": "Admin Input Mode",
        "guest_view_mode": "Guest View Mode", "date_changed": "Date updated",
        "venue_registered": "Venue registered", "enter_venue_name": "Enter venue name",
        "venue_deleted": "Venue deleted", "confirm_delete": "Confirm deletion",
        "venues_dates": "Registered Venues", "caption": "Click marker for details"
    },
    "ko": {
        "title": "칸타타 투어 2025", "add_city": "도시 추가", "select_city": "도시 선택",
        "add_venue_btn": "공연장 등록", "tour_route": "투어 경로", "remove": "삭제",
        "reset_btn": "전체 초기화", "performance_date": "공연 날짜",
        "venue_name": "공연장 이름", "seats": "좌석 수", "indoor_outdoor": "실내/실외",
        "indoor": "실내", "outdoor": "실외", "google_link": "구글 지도 링크",
        "special_notes": "특이사항", "register": "등록", "save": "저장",
        "tour_map": "투어 지도", "admin_mode": "관리자 모드", "guest_mode": "손님 모드",
        "enter_password": "관리자 모드 접근을 위한 비밀번호 입력", "submit": "제출",
        "drive_to": "길찾기", "distance": "거리 (km)", "time": "소요시간 (분)",
        "no_performance": "공연 없음", "today_performance": "오늘의 공연!",
        "past_performance": "지난 공연", "total_distance": "총 거리",
        "total_time": "총 소요시간", "add_city_to_route": "경로에 도시 추가",
        "city_placeholder": "도시 선택 (마하라스트라)", "admin_input_mode": "관리자 입력 모드",
        "guest_view_mode": "손님 보기 모드", "date_changed": "날짜 변경됨",
        "venue_registered": "공연장 등록됨", "enter_venue_name": "공연장 이름을 입력하세요",
        "venue_deleted": "공연장 삭제됨", "confirm_delete": "정말 삭제하시겠습니까?",
        "venues_dates": "등록된 공연장", "caption": "마커 클릭 시 상세정보 확인"
    },
    "hi": {
        "title": "कांताता टूर 2025", "add_city": "शहर जोड़ें", "select_city": "शहर चुनें",
        "add_venue_btn": "स्थल जोड़ें", "tour_route": "टूर मार्ग", "remove": "हटाएं",
        "reset_btn": "सब रीसेट करें", "performance_date": "प्रदर्शन तिथि",
        "venue_name": "स्थल का नाम", "seats": "सीटें", "indoor_outdoor": "इंडोर/आउटडोर",
        "indoor": "इंडोर", "outdoor": "आउटडोर", "google_link": "गूगल मैप्स लिंक",
        "special_notes": "विशेष टिप्पणियाँ", "register": "रजिस्टर", "save": "सहेजें",
        "tour_map": "टूर मैप", "admin_mode": "एडमिन मोड", "guest_mode": "गेस्ट मोड",
        "enter_password": "एडमिन मोड एक्सेस करने के लिए पासवर्ड दर्ज करें", "submit": "जमा करें",
        "drive_to": "यहाँ ड्राइव करें", "distance": "दूरी (किमी)", "time": "समय (मिनट)",
        "no_performance": "कोई प्रदर्शन नहीं", "today_performance": "आज का प्रदर्शन!",
        "past_performance": "पिछला प्रदर्शन", "total_distance": "कुल दूरी",
        "total_time": "कुल समय", "add_city_to_route": "मार्ग में शहर जोड़ें",
        "city_placeholder": "शहर चुनें (महाराष्ट्र)", "admin_input_mode": "एडमिन इनपुट मोड",
        "guest_view_mode": "गेस्ट व्यू मो드", "date_changed": "तारीख बदली गई",
        "venue_registered": "स्थल पंजीकृत", "enter_venue_name": "स्थल का नाम दर्ज करें",
        "venue_deleted": "स्थल हटाया गया", "confirm_delete": "क्या आप वाकई हटाना चाहते हैं?",
        "venues_dates": "पंजीकृत स्थान", "caption": "विवरण के लिए मार्कर पर क्लिक करें"
    },
}

# 2. 페이지 설정 및 크리스마스 테마
st.set_page_config(page_title="Cantata Tour 2025", layout="wide", initial_sidebar_state="expanded")

# 크리스마스 CSS 테마
st.markdown("""
<style>
    .reportview-container {background:linear-gradient(to bottom,#0f0c29,#302b63,#24243e);overflow:auto;position:relative;color:#90EE90;}
    .stApp {background:transparent;}
    .stSidebar {background:#1e4d2b; color:white;}
    .Widget>label {color:#90EE90;font-weight:bold;}
    .stButton>button{background:#8B0000;color:white;border:2px solid #FFD700;border-radius:12px;font-weight:bold;padding:10px;}
    .stButton>button:hover{background:#FF0000;color:white;}
    .christmas-title{font-size:3.5em!important;font-weight:bold;text-align:center;text-shadow:0 0 5px #FFF,0 0 10px #FFF,0 0 15px #FFF,0 0 20px #8B0000,0 0 35px #8B0000;letter-spacing:2px;position:relative;margin:20px 0;}
    .christmas-title .main{color:#FF0000!important;}
    .christmas-title .year{color:white!important;text-shadow:0 0 5px #FFF,0 0 10px #FFF,0 0 15px #FFD700;}
    .stExpander{background:rgba(255,255,255,0.1);border:1px solid #90EE90;border-radius:12px;}
    .stExpander>summary{color:#FFD700;font-weight:bold;font-size:1.5em!important;}
    .route-item{background:rgba(255,255,255,0.05);border:1px solid #3CB371;padding:8px;border-radius:8px;margin-bottom:5px;color:#90EE90;}
    .route-item:hover{background:rgba(255,255,255,0.1);}
    .route-info{display:flex;justify-content:space-between;align-items:center;}
    .route-city{font-weight:bold;}
    .route-details{font-size:0.9em;color:#ADD8E6;}
    .past-perf{background-color: rgba(0, 0, 0, 0.5) !important; color: #808080 !important;}
</style>
""", unsafe_allow_html=True)

# 크리스마스 장식 + 눈 내리는 효과
deco = """
<div class="christmas-decoration gift" style="top:10%;left:1%;">🎁</div>
<div class="christmas-decoration candy-cane" style="top:5%;right:1%;">🍭</div>
<div class="christmas-decoration stocking" style="top:20%;left:90%;">🧦</div>
<div class="christmas-decoration bell" style="top:30%;left:5%;">🔔</div>
<div class="christmas-decoration wreath" style="top:40%;right:90%;">🌿</div>
<div class="christmas-decoration santa-hat" style="top:60%;left:5%;">🎅</div>
<div class="christmas-decoration tree" style="top:70%;right:5%;">🎄</div>
<div class="christmas-decoration snowman" style="top:15%;left:45%;">⛄</div>
<div class="christmas-decoration candle" style="top:80%;left:20%;">🕯️</div>
<div class="christmas-decoration star" style="top:80%;right:20%;">⭐</div>
"""
st.markdown(deco, unsafe_allow_html=True)

snow = "".join(
    f'<div class="snowflake" style="left:{random.randint(0,100)}%;top:{random.uniform(0,100)}%;font-size:{random.choice(["0.8em","1em","1.2em","1.4em"])};animation-duration:{random.uniform(8,20):.1f}s;animation-delay:{random.uniform(0,5):.1f}s;">❄️</div>'
    for _ in range(100)
)
st.markdown(snow, unsafe_allow_html=True)

# 3. 세션 상태 초기화
for k in ["admin", "show_pw", "guest_mode", "route", "dates", "venues", "admin_venues"]: 
    st.session_state.setdefault(k, False if k in ["admin", "show_pw", "guest_mode"] else ([] if k == "route" else {}))

# 4. 도시 및 좌표
cities = sorted([...])  # 기존 cities 리스트 유지 (생략)
coords = { ... }  # 기존 coords 딕셔너리 유지 (생략)
ALL_CITIES = sorted(list(coords.keys()))

# 5. 헬퍼 함수
def target_df(): 
    return st.session_state.admin_venues if st.session_state.admin else st.session_state.venues

def date_str(city): 
    d = st.session_state.dates.get(city)
    return d.strftime("%Y-%m-%d") if d and isinstance(d, datetime.date) else _["no_performance"]

def nav_url(link): 
    return f"https://www.google.com/maps/search/?api=1&query={link}" if link and link.startswith("http") else "#"

def calculate_distance_time(city1, city2):
    if city1 in coords and city2 in coords:
        dist = great_circle(coords[city1], coords[city2]).kilometers
        time_min = round(dist / 60 * 60)
        return f"{dist:.1f} km", f"{time_min} min"
    return "?? km", "?? min"

# 6. 사이드바 (언어 + 모드)
with st.sidebar:
    st.markdown("### 🌐 Language")
    st.session_state.lang = st.radio("Select", ["ko","en","hi"], 
                                   format_func=lambda x: {"ko":"한국어","en":"English","hi":"हिन्दी"}[x], 
                                   index=0 if "lang" not in st.session_state else ["ko","en","hi"].index(st.session_state.lang))
    _ = LANG[st.session_state.lang]

    st.markdown("---")
    st.markdown("### 👑 Admin / Guest")
    if st.session_state.admin:
        st.success(_["admin_input_mode"])
        if st.button(_["guest_mode"]): 
            st.session_state.admin = False
            st.session_state.guest_mode = True
            st.session_state.show_pw = False
            st.rerun()
        if st.button(_["reset_btn"]):
            for key in ["route", "dates", "venues", "admin_venues"]:
                st.session_state[key] = [] if key == "route" else {}
            st.rerun()
    elif st.session_state.guest_mode:
        st.info(_["guest_view_mode"])
        if st.button(_["admin_mode"]): 
            st.session_state.guest_mode = False
            st.session_state.show_pw = True
            st.rerun()
    else:
        if st.button(_["admin_mode"]): 
            st.session_state.show_pw = True
        if st.session_state.show_pw:
            pw = st.text_input(_["enter_password"], type="password")
            if st.button(_["submit"]):
                if pw == "0691":
                    st.session_state.admin = True
                    st.session_state.show_pw = False
                    st.success("관리자 모드 활성화!")
                    st.rerun()
                else: 
                    st.error("비밀번호 오류")

# 7. 제목 렌더링
def render_ui():
    title_text = _["title"]
    parts = title_text.rsplit(" ", 1)
    title_html = f'<h1 class="christmas-title"><span>{parts[0]}</span> <span class="year">{parts[1] if len(parts)>1 else ""}</span></h1>'
    st.markdown(title_html, unsafe_allow_html=True)
render_ui()

# 8. 메인 화면
if "lang" not in st.session_state:
    st.session_state.lang = "ko"
_ = LANG[st.session_state.lang]

# ==================== 관리자 모드 ====================
if st.session_state.admin:
    st.subheader(_["admin_input_mode"])
    df_route = target_df()
    left_col, right_col = st.columns([1, 2])

    with left_col:
        st.markdown(f"### 🗺️ {_['add_city_to_route']}")
        avail = [c for c in ALL_CITIES if c not in st.session_state.route]
        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            city_options = [_["city_placeholder"]] + avail
            selected_city_name = st.selectbox(_["select_city"], city_options, key="city_select_admin")
        with col_btn:
            if st.button(_["add_city_to_route"], key="add_route_city_admin") and selected_city_name != _["city_placeholder"]:
                if selected_city_name not in st.session_state.route:
                    st.session_state.route.append(selected_city_name)
                    st.session_state.dates[selected_city_name] = datetime.now().date()
                    for df in [st.session_state.venues, st.session_state.admin_venues]:
                        df[selected_city_name] = pd.DataFrame(columns=["Venue","Seats","IndoorOutdoor","Google Maps Link","Special Notes"])
                    st.success(f"{selected_city_name} 추가됨")
                    st.rerun()

        st.markdown("---")
        if st.session_state.route:
            st.subheader(_["tour_route"])
            total_dist = total_time_min = 0
            prev_coord = None

            for i, city in enumerate(st.session_state.route):
                city_coord = coords.get(city)
                is_past = st.session_state.dates.get(city) and st.session_state.dates[city] < datetime.now().date()
                is_today = st.session_state.dates.get(city) and st.session_state.dates[city] == datetime.now().date()
                today_icon = "🔴" if is_today else ""
                has_venue_data = city in df_route and not df_route[city].empty
                map_link = next((r["Google Maps Link"] for _, r in df_route[city].iterrows() if r.get("Google Maps Link", "").startswith("http")), None)
                nav_icon = f'<a href="{nav_url(map_link)}" target="_blank" style="color:#90EE90; float:right;"><b style="font-size:1.3em;">🚗</b></a>' if map_link else ""

                with st.expander(f"**{city}** {today_icon} {nav_icon}", expanded=False):
                    st.markdown(f"#### {city} - {_['performance_date']}")
                    cur_date = st.session_state.dates.get(city, datetime.now().date())
                    new_date = st.date_input(_["performance_date"], value=cur_date, format="YYYY-MM-DD", key=f"date_input_{city}")
                    if new_date != cur_date:
                        st.session_state.dates[city] = new_date
                        st.success(_["date_changed"])
                        st.rerun()

                    st.markdown("---")
                    st.markdown(f"#### {_['venue_name']} / {_['google_link']} / {_['special_notes']}")
                    venue_name = st.text_input(_["venue_name"], key=f"v_{city}_admin")
                    seats = st.number_input(_["seats"], min_value=1, step=50, key=f"s_{city}_admin")
                    google_link = st.text_input(_["google_link"], placeholder="https://...", key=f"l_{city}_admin")
                    special_notes = st.text_area(_["special_notes"], key=f"sn_{city}_admin")

                    io_key = f"io_{city}_admin"
                    current_io = st.session_state.get(io_key, _["outdoor"])
                    toggle_label = f"{_['outdoor']} ➜ {_['indoor']}" if current_io == _["outdoor"] else f"{_['indoor']} ➜ {_['outdoor']}"

                    col_io, col_reg = st.columns([1, 1])
                    with col_io:
                        if st.button(toggle_label, key=f"io_btn_{city}", help="실외/실내 전환 | Toggle Indoor/Outdoor", use_container_width=True):
                            st.session_state[io_key] = _["indoor"] if current_io == _["outdoor"] else _["outdoor"]
                            st.rerun()
                    with col_reg:
                        if st.button(_["register"], key=f"reg_{city}_admin"):
                            if not venue_name:
                                st.error(_["enter_venue_name"])
                            else:
                                new_row = pd.DataFrame([{
                                    "Venue": venue_name, "Seats": seats, "IndoorOutdoor": st.session_state[io_key],
                                    "Google Maps Link": google_link, "Special Notes": special_notes
                                }])
                                if city not in df_route:
                                    df_route[city] = pd.DataFrame(columns=new_row.columns)
                                df_route[city] = pd.concat([df_route[city], new_row], ignore_index=True)
                                st.success(_["venue_registered"])
                                st.rerun()

                    if has_venue_data:
                        st.markdown("---")
                        st.markdown(f"##### {_['venues_dates']}")
                        for idx, row in df_route[city].iterrows():
                            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                            with col1:
                                st.write(f"**{row['Venue']}** ({row['IndoorOutdoor']})")
                                st.caption(f"{row.get('Seats', 'N/A')} | {row.get('Special Notes', '')}")
                            with col2:
                                if row.get("Google Maps Link", "").startswith("http"):
                                    st.markdown(f'<div style="text-align:right"><a href="{nav_url(row["Google Maps Link"])}" target="_blank" style="color:#FFD700;">🚗</a></div>', unsafe_allow_html=True)
                            with col4:
                                if st.button(_["remove"], key=f"del_{city}_{idx}_admin"):
                                    if st.checkbox(_["confirm_delete"], key=f"confirm_{city}_{idx}_admin"):
                                        df_route[city] = df_route[city].drop(idx).reset_index(drop=True)
                                        if df_route[city].empty: df_route.pop(city, None)
                                        st.success(_["venue_deleted"])
                                        st.rerun()

                # 거리 표시
                dist_str, time_str = "Start", ""
                if i > 0 and prev_coord and city_coord:
                    dist_str, time_str = calculate_distance_time(st.session_state.route[i-1], city)
                    total_dist += float(dist_str.split()[0])
                    total_time_min += int(time_str.split()[0])
                display_html = f"""
                <div class="route-item {'past-perf' if is_past else ''}">
                    <div class="route-info">
                        <div class="route-city">{today_icon} {city} ({date_str(city)})</div>
                        <div class="route-details">
                            {dist_str} | {time_str} <span style="color:red;">{nav_icon}</span>
                        </div>
                    </div>
                </div>
                """
                st.markdown(display_html, unsafe_allow_html=True)
                prev_coord = city_coord

            st.markdown("---")
            st.markdown(f"<h3 style='color:#FFD700;'>▶️ {_['total_distance']}: {total_dist:.1f} km | {_['total_time']}: {total_time_min} min</h3>", unsafe_allow_html=True)

    with right_col:
        # 지도 (관리자 모드) - 기존 코드 유지 (생략)
        pass  # (기존 지도 코드 그대로)

# ==================== 게스트 모드 ====================
else:
    st.subheader(_["guest_view_mode"])
    # 게스트 모드 UI (기존과 동일, 생략)
    pass

# 초기 언어 설정
if "lang" not in st.session_state:
    st.session_state.lang = "ko"
render_ui()
