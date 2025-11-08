import json, os, uuid, base64, random
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
import pandas as pd

st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
CSV_FILE = "maharashtra_cities_200_batch_filled.csv"
os.makedirs(UPLOAD_DIR, exist_ok=True)

LANG = {
    "ko": {"title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
           "tab_notice": "공지", "tab_map": "투어 경로", "indoor": "실내", "outdoor": "실외",
           "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵", "perf_date": "공연 날짜",
           "warning": "제목·내용 입력", "delete": "제거", "menu": "메뉴", "login": "로그인", "logout": "로그아웃",
           "add_city": "도시 추가", "city": "도시", "import_cities": "CSV 도시 일괄 추가", "import_success": "도시 일괄 추가 완료!",
           "search_city": "도시 검색"},
    "en": {"title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
           "tab_notice": "Notice", "tab_map": "Tour Route", "indoor": "Indoor", "outdoor": "Outdoor",
           "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps", "perf_date": "Performance Date",
           "warning": "Enter title & content", "delete": "Remove", "menu": "Menu", "login": "Login", "logout": "Logout",
           "add_city": "Add City", "city": "City", "import_cities": "Import All Cities from CSV", "import_success": "Cities imported successfully!",
           "search_city": "Search City"},
    "hi": {"title_cantata": "कैंटाटा टूर", "title_year": "2025", "title_region": "महाराष्ट्र",
           "tab_notice": "सूचना", "tab_map": "टूर मार्ग", "indoor": "इनडोर", "outdoor": "आउटडोर",
           "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप", "perf_date": "प्रदर्शन तिथि",
           "warning": "शीर्षक·सामग्री दर्ज करें", "delete": "हटाएं", "menu": "मेनू", "login": "लॉगिन", "logout": "लॉगआउट",
           "add_city": "शहर जोड़ें", "city": "शहर", "import_cities": "CSV से सभी शहर आयात करें", "import_success": "शहर सफलतापूर्वक आयात किए गए!",
           "search_city": "शहर खोजें"}
}

defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- CSV에서 도시 + 좌표 로드 (기본값) ---
def load_cities_from_csv():
    if not os.path.exists(CSV_FILE):
        st.error(f"{CSV_FILE} 파일이 없습니다. 프로젝트 폴더에 업로드하세요.")
        return []
    df = pd.read_csv(CSV_FILE)
    cities = []
    seen = set()
    for _, row in df.iterrows():
        city = str(row['city']).strip()
        if not city or city in seen:
            continue
        seen.add(city)
        lat = float(row['latitude']) if pd.notna(row['latitude']) else 18.5204
        lon = float(row['longitude']) if pd.notna(row['longitude']) else 73.8567
        cities.append({
            "city": city,
            "venue": "",
            "seats": "",
            "note": "",
            "google_link": "",
            "indoor": False,
            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
            "perf_date": "",
            "lat": lat,
            "lon": lon
        })
    return cities

# --- 초기 데이터 생성 ---
if not os.path.exists(CITY_FILE):
    default_cities = load_cities_from_csv()
    save_json(CITY_FILE, default_cities)

# --- CSV 재로딩 (관리자용) ---
def import_cities_from_csv():
    new_cities = load_cities_from_csv()
    save_json(CITY_FILE, new_cities)
    st.success(f"{len(new_cities)}개 도시가 성공적으로 로드되었습니다!")

st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
    [data-testid="stAppViewContainer"] { background: url("background_christmas_dark.png"); background-size: cover; background-position: center; background-attachment: fixed; padding-top: 0 !important; margin: 0 !important; }
    .header-container { text-align: center; margin: 0 !important; padding: 0 !important; }
    .christmas-decoration { display: flex; justify-content: center; gap: 12px; margin: 0 !important; padding: 0 !important; margin-bottom: 0 !important; }
    .christmas-decoration i { color: #fff; text-shadow: 0 0 10px rgba(255,255,255,0.6); animation: float 3s ease-in-out infinite; opacity: 0.95; }
    .christmas-decoration i:nth-child(1) { font-size: 2.1em; animation-delay: 0s; }
    .christmas-decoration i:nth-child(2) { font-size: 1.9em; animation-delay: 0.4s; }
    .christmas-decoration i:nth-child(3) { font-size: 2.4em; animation-delay: 0.8s; }
    .christmas-decoration i:nth-child(4) { font-size: 2.0em; animation-delay: 1.2s; }
    .christmas-decoration i:nth-child(5) { font-size: 2.5em; animation-delay: 1.6s; }
    .christmas-decoration i:nth-child(6) { font-size: 1.8em; animation-delay: 2.0s; }
    .christmas-decoration i:nth-child(7) { font-size: 2.3em; animation-delay: 2.4s; }
    @keyframes float { 0%, 100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-6px) rotate(4deg); } }
    .main-title { font-size: 2.8em !important; font-weight: bold; text-align: center; text-shadow: 0 3px 8px rgba(0,0,0,0.6); margin: 0 !important; padding: 0 !important; line-height: 1.2; margin-top: 0 !important; margin-bottom: 0 !important; }
    .button-row { display: flex; justify-content: center; gap: 20px; margin: 0 !important; padding: 0 15px !important; margin-top: 0 !important; }
    .tab-btn { background: rgba(255,255,255,0.96); color: #c62828; border: none; border-radius: 20px; padding: 10px 20px; font-weight: bold; font-size: 1.1em; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: all 0.3s ease; flex: 1; max-width: 200px; }
    .tab-btn:hover { background: #d32f2f; color: white; transform: translateY(-2px); }
    .snowflake { position:fixed; top:-15px; color:#fff; font-size:1.1em; pointer-events:none; animation:fall linear infinite; opacity:0.3; z-index:1; }
    @keyframes fall { 0% { transform:translateY(0) rotate(0deg); } 100% { transform:translateY(120vh) rotate(360deg); } }
    .hamburger { position:fixed; top:15px; left:15px; z-index:10000; background:rgba(0,0,0,.6); color:#fff; border:none; border-radius:50%; width:50px; height:50px; font-size:24px; cursor:pointer; box-shadow:0 0 10px rgba(0,0,0,.3); }
    .sidebar-mobile { position:fixed; top:0; left:-300px; width:280px; height:100vh; background:rgba(30,30,30,.95); color:#fff; padding:20px; transition:left .3s; z-index:9999; overflow-y:auto; }
    .sidebar-mobile.open { left:0; }
    .overlay { position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,.5); z-index:9998; display:none; }
    .overlay.open { display:block; }
    @media(min-width:769px) { .hamburger, .sidebar-mobile, .overlay { display:none !important; } section[data-testid="stSidebar"] { display:block !important; } }
    .stButton>button { border:none !important; -webkit-appearance:none !important; }
</style>
""", unsafe_allow_html=True)

for i in range(52):
    left = random.randint(0, 100)
    duration = random.randint(10, 20)
    size = random.uniform(0.8, 1.4)
    delay = random.uniform(0, 10)
    st.markdown(f"<div class='snowflake' style='left:{left}vw; animation-duration:{duration}s; font-size:{size}em; animation-delay:{delay}s;'>❄</div>", unsafe_allow_html=True)

st.markdown('<div class="header-container">', unsafe_allow_html=True)
st.markdown('''
<div class="christmas-decoration">
    <i class="fas fa-gift"></i>
    <i class="fas fa-candy-cane"></i>
    <i class="fas fa-socks"></i>
    <i class="fas fa-sleigh"></i>
    <i class="fas fa-deer"></i>
    <i class="fas fa-tree"></i>
    <i class="fas fa-bell"></i>
</div>
''', unsafe_allow_html=True)
title_html = f'<h1 class="main-title"><span style="color:red;">{_("title_cantata")}</span> <span style="color:white;">{_("title_year")}</span> <span style="color:green; font-size:67%;">{_("title_region")}</span></h1>'
st.markdown(title_html, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="button-row">', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    if st.button(_("tab_notice"), key="btn_notice", use_container_width=True):
        st.session_state.notice_open = not st.session_state.notice_open
        st.session_state.map_open = False
        st.rerun()
with col2:
    if st.button(_("tab_map"), key="btn_map", use_container_width=True):
        st.session_state.map_open = not st.session_state.map_open
        st.session_state.notice_open = False
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.notice_open:
    if st.session_state.admin:
        with st.expander("공지 작성"):
            with st.form("notice_form", clear_on_submit=True):
                title = st.text_input("제목", key="notice_title")
                content = st.text_area("내용", key="notice_content")
                img = st.file_uploader("이미지", type=["png", "jpg", "jpeg"], key="notice_img")
                file = st.file_uploader("첨부 파일", key="notice_file")
                if st.form_submit_button("등록"):
                    if title.strip() and content.strip():
                        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
                        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
                        if img: open(img_path, "wb").write(img.getbuffer())
                        if file: open(file_path, "wb").write(file.getbuffer())
                        notice = {"id": str(uuid.uuid4()), "title": title, "content": content, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"), "image": img_path, "file": file_path}
                        data = load_json(NOTICE_FILE)
                        data.insert(0, notice)
                        save_json(NOTICE_FILE, data)
                        st.success("공지 등록 완료!")
                        st.rerun()
                    else:
                        st.warning(_("warning"))
    data = load_json(NOTICE_FILE)
    for i, n in enumerate(data):
        with st.expander(f"{n['date']} | {n['title']}", expanded=False):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]): st.image(n["image"], use_column_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                b64 = base64.b64encode(open(n["file"], "rb").read()).decode()
                st.markdown(f'<a href="data:file/txt;base64,{b64}" download="{os.path.basename(n["file"])}">다운로드</a>', unsafe_allow_html=True)
            if st.session_state.admin and st.button(_("delete"), key=f"del_n_{n['id']}"):
                data.pop(i); save_json(NOTICE_FILE, data); st.rerun()

if st.session_state.map_open:
    if st.session_state.admin:
        if st.button(_("import_cities"), key="import_csv_cities"):
            import_cities_from_csv()
            st.rerun()

    cities = load_json(CITY_FILE)
    city_names = sorted({c['city'] for c in cities})

    if st.session_state.admin:
        st.header(_("add_city"))
        search_term = st.text_input(_("search_city"))
        filtered_cities = [c for c in city_names if search_term.lower() in c.lower()]
        with st.form("city_form", clear_on_submit=True):
            selected_city = st.selectbox(_("city"), options=[""] + sorted(filtered_cities), index=0)
            perf_date = st.date_input(_("perf_date"), value=None)
            venue = st.text_input(_("venue"))
            note = st.text_input(_("note"))
            google_link = st.text_input(_("google_link"))

            col_indoor, col_seats = st.columns([1, 2])
            with col_indoor:
                indoor_option = st.radio("장소 유형", [(_("indoor"), True), (_("outdoor"), False)], format_func=lambda x: x[0], horizontal=True)
                indoor = indoor_option[1]
            with col_seats:
                seats = st.number_input(_("seats"), min_value=0, max_value=10000, value=500, step=50, format="%d")

            if st.form_submit_button("추가"):
                if selected_city and venue:
                    # 좌표는 CSV에서 가져오거나 기본값
                    city_data = next((c for c in cities if c["city"] == selected_city), {})
                    lat = city_data.get("lat", 18.5204)
                    lon = city_data.get("lon", 73.8567)
                    new_city = {
                        "city": selected_city,
                        "venue": venue,
                        "seats": str(seats),
                        "note": note,
                        "google_link": google_link,
                        "indoor": indoor,
                        "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
                        "perf_date": str(perf_date) if perf_date else "",
                        "lat": lat, "lon": lon
                    }
                    cities.append(new_city)
                    save_json(CITY_FILE, cities)
                    st.success("도시 추가 완료!")
                    st.rerun()
                else:
                    st.warning("도시와 공연 장소를 입력하세요.")

    m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="OpenStreetMap")
    for i, c in enumerate(cities):
        lat, lon = c["lat"], c["lon"]
        coords = (lat, lon)
        is_future = c.get("perf_date", "9999-12-31") >= str(date.today())
        color = "red" if is_future else "gray"
        indoor_text = _("indoor") if c.get("indoor") else _("outdoor")
        popup_html = f"<div style='font-size:14px; line-height:1.6;'><b>{c['city']}</b><br>{_('perf_date')}: {c.get('perf_date','미정')}<br>{_('venue')}: {c.get('venue','—')}<br>{_('seats')}: {c.get('seats','—')}<br>{indoor_text}<br><a href='https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving' target='_blank'>{_('google_link')}</a></div>"
        folium.Marker(coords, popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=color, icon="music", prefix="fa")).add_to(m)
        if i < len(cities) - 1:
            nxt_city = cities[i+1]
            AntPath([coords, (nxt_city["lat"], nxt_city["lon"])], color="#e74c3c", weight=6, opacity=0.3 if not is_future else 1.0).add_to(m)
    st_folium(m, width=900, height=550, key="tour_map")

    if st.session_state.admin:
        st.subheader("도시 목록 관리")
        for i, c in enumerate(cities):
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(f"{c['city']} - {c['venue']} ({c.get('perf_date', '미정')})")
            with cols[1]:
                if st.button(_("delete"), key=f"del_c_{i}"):
                    cities.pop(i)
                    save_json(CITY_FILE, cities)
                    st.rerun()

st.markdown(f'''
<button class="hamburger" onclick="document.querySelector('.sidebar-mobile').classList.toggle('open'); document.querySelector('.overlay').classList.toggle('open');">☰</button>
<div class="overlay" onclick="document.querySelector('.sidebar-mobile').classList.remove('open'); this.classList.remove('open');"></div>
<div class="sidebar-mobile">
    <h3 style="color:white;">{_("menu")}</h3>
    <select onchange="window.location.href='?lang='+this.value" style="width:100%; padding:8px; margin:10px 0;">
        <option value="ko" {'selected' if st.session_state.lang=="ko" else ''}>한국어</option>
        <option value="en" {'selected' if st.session_state.lang=="en" else ''}>English</option>
        <option value="hi" {'selected' if st.session_state.lang=="hi" else ''}>हिंदी</option>
    </select>
    {'''
        <input type="password" placeholder="비밀번호" id="mobile_pw" style="width:100%; padding:8px; margin:10px 0;">
        <button onclick="if(document.getElementById(\'mobile_pw\').value==\'0009\') window.location.href=\'?admin=true\'; else alert(\'비밀번호 오류\');" style="width:100%; padding:10px; background:#e74c3c; color:white; border:none; border-radius:8px;">{_("login")}</button>
    ''' if not st.session_state.admin else f'''
        <button onclick="window.location.href=\'?admin=false\'" style="width:100%; padding:10px; background:#27ae60; color:white; border:none; border-radius:8px; margin:10px 0;">{_("logout")}</button>
    ''' }
</div>
''', unsafe_allow_html=True)

with st.sidebar:
    lang_map = {"한국어": "ko", "English": "en", "हिंदी": "hi"}
    sel = st.selectbox("언어", list(lang_map.keys()), index=list(lang_map.values()).index(st.session_state.lang))
    if lang_map[sel] != st.session_state.lang:
        st.session_state.lang = lang_map[sel]
        st.rerun()
    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password", key="pw_input")
        if st.button("로그인", key="login_btn"):
            if pw == "0009":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃", key="logout_btn"):
            st.session_state.admin = False
            st.rerun()
