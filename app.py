import json, os, uuid, base64, random
import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
LANG = {
    "ko": {"title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
           "tab_notice": "공지", "tab_map": "투어 경로", "indoor": "실내", "outdoor": "실외",
           "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵",
           "warning": "도시와 장소를 입력하세요", "delete": "제거", "menu": "메뉴", "login": "로그인", "logout": "로그아웃",
           "add_city": "도시", "add_more": "추가", "save_all": "저장", "date": "날짜", "perf_date": "공연 날짜",
           "register": "등록", "update": "수정", "remove": "제거"},
    "en": {"title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
           "tab_notice": "Notice", "tab_map": "Tour Route", "indoor": "Indoor", "outdoor": "Outdoor",
           "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps",
           "warning": "Enter city and venue", "delete": "Remove", "menu": "Menu", "login": "Login", "logout": "Logout",
           "add_city": "City", "add_more": "Add More", "save_all": "Save All", "date": "Date", "perf_date": "Performance Date",
           "register": "Register", "update": "Update", "remove": "Remove"}
}
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)
def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
# --- 초기 데이터 (Mumbai, Pune, Nagpur) ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "", "seats": "", "note": "", "google_link": "", "indoor": False, "date": "", "perf_date": "", "lat": 19.07609, "lon": 72.877426},
    {"city": "Pune", "venue": "", "seats": "", "note": "", "google_link": "", "indoor": False, "date": "", "perf_date": "", "lat": 18.52043, "lon": 73.856743},
    {"city": "Nagpur", "venue": "", "seats": "", "note": "", "google_link": "", "indoor": False, "date": "", "perf_date": "", "lat": 21.1458, "lon": 79.088154}
]
if not os.path.exists(CITY_FILE): save_json(CITY_FILE, DEFAULT_CITIES)
# --- CSS & 눈송이 ---
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
    [data-testid="stAppViewContainer"] { background: url("background_christmas_dark.png"); background-size: cover; background-attachment: fixed; padding-top: 0 !important; }
    .header-container { text-align: center; margin: 0 !important; }
    .christmas-decoration { display: flex; justify-content: center; gap: 12px; margin-bottom: 0 !important; }
    .christmas-decoration i { color: #fff; text-shadow: 0 0 10px rgba(255,255,255,0.6); animation: float 3s ease-in-out infinite; }
    @keyframes float { 0%, 100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-6px) rotate(4deg); } }
    .main-title { font-size: 2.8em !important; font-weight: bold; text-shadow: 0 3px 8px rgba(0,0,0,0.6); margin: 0 !important; line-height: 1.2; }
    .button-row { display: flex; justify-content: center; gap: 20px; margin-top: 0 !important; }
    .tab-btn { background: rgba(255,255,255,0.96); color: #c62828; border: none; border-radius: 20px; padding: 10px 20px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: all 0.3s; flex: 1; max-width: 200px; }
    .tab-btn:hover { background: #d32f2f; color: white; transform: translateY(-2px); }
    .snowflake { position:fixed; top:-15px; color:#fff; font-size:1.1em; pointer-events:none; animation:fall linear infinite; opacity:0.3; z-index:1; }
    @keyframes fall { 0% { transform:translateY(0) rotate(0deg); } 100% { transform:translateY(120vh) rotate(360deg); } }
    .hamburger { position:fixed; top:15px; left:15px; z-index:10000; background:rgba(0,0,0,.6); color:#fff; border:none; border-radius:50%; width:50px; height:50px; font-size:24px; cursor:pointer; }
    .sidebar-mobile { position:fixed; top:0; left:-300px; width:280px; height:100vh; background:rgba(30,30,30,.95); color:#fff; padding:20px; transition:left .3s; z-index:9999; }
    .sidebar-mobile.open { left:0; }
    .overlay { position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,.5); z-index:9998; display:none; }
    .overlay.open { display:block; }
    @media(min-width:769px) { .hamburger, .sidebar-mobile, .overlay { display:none !important; } }
    .stButton>button { border:none !important; }
</style>
""", unsafe_allow_html=True)
for i in range(52):
    st.markdown(f"<div class='snowflake' style='left:{random.randint(0,100)}vw; animation-duration:{random.randint(10,20)}s; font-size:{random.uniform(0.8,1.4)}em; animation-delay:{random.uniform(0,10)}s;'>❄</div>", unsafe_allow_html=True)
# --- 헤더 ---
st.markdown('<div class="header-container">', unsafe_allow_html=True)
st.markdown('''
<div class="christmas-decoration">
    <i class="fas fa-gift"></i><i class="fas fa-candy-cane"></i><i class="fas fa-socks"></i>
    <i class="fas fa-sleigh"></i><i class="fas fa-deer"></i><i class="fas fa-tree"></i><i class="fas fa-bell"></i>
</div>
''', unsafe_allow_html=True)
st.markdown(f'<h1 class="main-title"><span style="color:red;">{_("title_cantata")}</span> <span style="color:white;">{_("title_year")}</span> <span style="color:green; font-size:67%;">{_("title_region")}</span></h1>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
# --- 탭 버튼 ---
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
# --- 공지 ---
if st.session_state.notice_open:
    if st.session_state.admin:
        with st.expander("공지 작성"):
            with st.form("notice_form", clear_on_submit=True):
                title = st.text_input("제목")
                content = st.text_area("내용")
                img = st.file_uploader("이미지", type=["png","jpg","jpeg"])
                file = st.file_uploader("첨부 파일")
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
                        st.success("등록 완료!")
                        st.rerun()
                    else:
                        st.warning(_("warning"))
    for i, n in enumerate(load_json(NOTICE_FILE)):
        with st.expander(f"{n['date']} | {n['title']}", expanded=False):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]): st.image(n["image"], use_column_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                b64 = base64.b64encode(open(n["file"], "rb").read()).decode()
                st.markdown(f'<a href="data:file/txt;base64,{b64}" download="{os.path.basename(n["file"])}">다운로드</a>', unsafe_allow_html=True)
            if st.session_state.admin and st.button(_("delete"), key=f"del_n_{n['id']}"):
                data = load_json(NOTICE_FILE)
                data.pop(i)
                save_json(NOTICE_FILE, data)
                st.rerun()
# --- 지도 & 도시 추가 ---
if st.session_state.map_open:
    cities = load_json(CITY_FILE)
    city_options = ["Mumbai", "Pune", "Nagpur"]
    if st.session_state.admin:
        st.header(_("add_city"))
        if 'new_cities' not in st.session_state:
            st.session_state.new_cities = []
        if st.button("+", key="add_city_block"):
            st.session_state.new_cities.append({
                "city": city_options[0], "venue": "", "seats": 500, "note": "", "google_link": "", "indoor": False,
                "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"), "perf_date": ""
            })
            st.rerun()
        for idx, new_city in enumerate(st.session_state.new_cities):
            with st.container():
                cols = st.columns([9, 1])
                with cols[0]:
                    selected_city = st.selectbox(_("city"), options=city_options, key=f"city_select_{idx}", index=city_options.index(new_city["city"]))
                    new_city["city"] = selected_city
                    new_city["lat"] = next(c["lat"] for c in DEFAULT_CITIES if c["city"] == selected_city)
                    new_city["lon"] = next(c["lon"] for c in DEFAULT_CITIES if c["city"] == selected_city)
                with cols[1]:
                    pass  # 빈 공간으로 바 클릭 영역 확보
                with st.expander(f"{new_city['city']} 상세", expanded=False):
                    new_city["date"] = st.text_input(_("date"), value=new_city["date"], key=f"date_{idx}")
                    new_city["venue"] = st.text_input(_("venue"), value=new_city["venue"], key=f"venue_{idx}")
                    new_city["seats"] = st.number_input(_("seats"), min_value=0, value=new_city["seats"], step=50, key=f"seats_{idx}")
                    new_city["indoor"] = st.checkbox(_("indoor"), value=new_city["indoor"], key=f"indoor_{idx}")
                    new_city["google_link"] = st.text_input(_("google_link"), value=new_city["google_link"], key=f"google_link_{idx}")
                    new_city["note"] = st.text_input(_("note"), value=new_city["note"], key=f"note_{idx}")
                    new_city["perf_date"] = st.text_input(_("perf_date"), value=new_city["perf_date"], key=f"perf_date_{idx}")
                    btn_cols = st.columns(3)
                    with btn_cols[0]:
                        if st.button(_("register"), key=f"register_{idx}"):
                            if new_city["city"] and new_city["venue"]:
                                cities.append(new_city.copy())
                                save_json(CITY_FILE, cities)
                                st.session_state.new_cities.pop(idx)
                                st.success("등록 완료!")
                                st.rerun()
                            else:
                                st.warning(_("warning"))
                    with btn_cols[1]:
                        if st.button(_("update"), key=f"update_{idx}"):
                            if new_city["city"] and new_city["venue"]:
                                # 기존 cities에 업데이트 (새로운 블록이므로 등록과 유사하나, 이미 추가된 경우를 가정)
                                st.info("업데이트 기능은 기존 도시 관리에서 사용하세요. 여기서는 등록으로 처리됩니다.")
                            else:
                                st.warning(_("warning"))
                    with btn_cols[2]:
                        if st.button(_("remove"), key=f"remove_{idx}"):
                            st.session_state.new_cities.pop(idx)
                            st.rerun()
    # --- 지도 ---
    m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="OpenStreetMap")
    for i, c in enumerate(cities):
        lat, lon = c["lat"], c["lon"]
        color = "red" if not c.get("perf_date") else "gray"
        indoor_text = _("indoor") if c.get("indoor") else _("outdoor")
        popup_html = f"<b>{c['city']}</b><br>{_('venue')}: {c.get('venue','—')}<br>{_('seats')}: {c.get('seats','—')}<br>{indoor_text}"
        folium.Marker((lat, lon), popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=color, icon="music", prefix="fa")).add_to(m)
        if i < len(cities) - 1:
            nxt = cities[i+1]
            AntPath([(lat, lon), (nxt["lat"], nxt["lon"])], color="#e74c3c", weight=6, opacity=0.7).add_to(m)
    st_folium(m, width=900, height=550, key="tour_map")
    # --- 도시 관리 ---
    if st.session_state.admin:
        st.subheader("도시 목록 관리")
        for i, c in enumerate(cities):
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(f"{c['city']} - {c['venue']}")
            with cols[1]:
                if st.button(_("delete"), key=f"del_c_{i}"):
                    cities.pop(i)
                    save_json(CITY_FILE, cities)
                    st.rerun()
# --- 모바일 메뉴 & 사이드바 ---
st.markdown(f'''
<button class="hamburger" onclick="document.querySelector('.sidebar-mobile').classList.toggle('open'); document.querySelector('.overlay').classList.toggle('open');">☰</button>
<div class="overlay" onclick="document.querySelector('.sidebar-mobile').classList.remove('open'); this.classList.remove('open');"></div>
<div class="sidebar-mobile">
    <h3 style="color:white;">{_("menu")}</h3>
    <select onchange="window.location.href='?lang='+this.value" style="width:100%; padding:8px; margin:10px 0;">
        <option value="ko" {'selected' if st.session_state.lang=="ko" else ''}>한국어</option>
        <option value="en" {'selected' if st.session_state.lang=="en" else ''}>English</option>
    </select>
    {'''
        <input type="password" placeholder="비밀번호" id="mobile_pw" style="width:100%; padding:8px; margin:10px 0;">
        <button onclick="if(document.getElementById(\'mobile_pw\').value==\'0009\') window.location.href=\'?admin=true\'; else alert(\'오류\');" style="width:100%; padding:10px; background:#e74c3c; color:white; border:none; border-radius:8px;">{_("login")}</button>
    ''' if not st.session_state.admin else f'''
        <button onclick="window.location.href=\'?admin=false\'" style="width:100%; padding:10px; background:#27ae60; color:white; border:none; border-radius:8px;">{_("logout")}</button>
    ''' }
</div>
''', unsafe_allow_html=True)
with st.sidebar:
    sel = st.selectbox("언어", ["한국어", "English"], index=0 if st.session_state.lang == "ko" else 1)
    if sel == "English" and st.session_state.lang != "en":
        st.session_state.lang = "en"
        st.rerun()
    elif sel == "한국어" and st.session_state.lang != "ko":
        st.session_state.lang = "ko"
        st.rerun()
    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if pw == "0009":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃"):
            st.session_state.admin = False
            st.rerun()
