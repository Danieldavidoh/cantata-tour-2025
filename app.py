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

# --- 자동 새로고침 ---
if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

# --- 파일 경로 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 다국어 ---
LANG = {
    "ko": {
        "title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
        "tab_notice": "공지", "tab_map": "투어 경로", "indoor": "실내", "outdoor": "실외",
        "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵",
        "warning": "도시와 장소를 입력하세요", "delete": "제거", "menu": "메뉴", "login": "로그인", "logout": "로그아웃",
        "add_city": "추가", "register": "등록", "update": "수정", "remove": "제거",
        "date": "등록일"
    },
    "en": {
        "title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
        "tab_notice": "Notice", "tab_map": "Tour Route", "indoor": "Indoor", "outdoor": "Outdoor",
        "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps",
        "warning": "Enter city and venue", "delete": "Remove", "menu": "Menu", "login": "Login", "logout": "Logout",
        "add_city": "Add", "register": "Register", "update": "Update", "remove": "Remove",
        "date": "Date"
    },
    "hi": {
        "title_cantata": "कैंटाटा टूर", "title_year": "२०२५", "title_region": "महाराष्ट्र",
        "tab_notice": "सूचना", "tab_map": "टूर रूट", "indoor": "इनडोर", "outdoor": "आउटडोर",
        "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप्स",
        "warning": "शहर और स्थल दर्ज करें", "delete": "हटाएं", "menu": "मेनू", "login": "लॉगिन", "logout": "लॉगआउट",
        "add_city": "जोड़ें", "register": "रजिस्टर", "update": "अपडेट", "remove": "हटाएं",
        "date": "तारीख"
    }
}

# --- 세션 초기화 (lang 보장) ---
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
    elif k == "lang" and not isinstance(st.session_state[k], str):
        st.session_state[k] = "ko"

# --- 번역 함수 ---
def _(key):
    lang = st.session_state.lang if isinstance(st.session_state.lang, str) else "ko"
    return LANG.get(lang, LANG["ko"]).get(key, key)

# --- JSON 헬퍼 ---
def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- CSV 데이터 로드 및 도시 목록 생성 ---
CSV_CITIES = [
    {"city": "Ahmadnagar", "lat": 19.095193, "lon": 74.749596},
    {"city": "Akola", "lat": 20.702269, "lon": 77.004699},
    {"city": "Ambernath", "lat": 19.186354, "lon": 73.191948},
    {"city": "Amravati", "lat": 20.93743, "lon": 77.779271},
    {"city": "Aurangabad", "lat": 19.876165, "lon": 75.343314},
    {"city": "Badlapur", "lat": 19.1088, "lon": 73.1311},
    {"city": "Bhandara", "lat": 21.180052, "lon": 79.564987},
    {"city": "Bhiwandi", "lat": 19.300282, "lon": 73.069645},
    {"city": "Bhusawal", "lat": 21.02606, "lon": 75.830095},
    {"city": "Chandrapur", "lat": 19.957275, "lon": 79.296875},
    {"city": "Chiplun", "lat": 17.5322, "lon": 73.516},
    {"city": "Dhule", "lat": 20.904964, "lon": 74.774651},
    {"city": "Dombivli", "lat": 19.2183, "lon": 73.0865},
    {"city": "Gondia", "lat": 21.4598, "lon": 80.195},
    {"city": "Hingoli", "lat": 19.7146, "lon": 77.1424},
    {"city": "Ichalkaranji", "lat": 16.6956, "lon": 74.4561},
    {"city": "Jalgaon", "lat": 21.007542, "lon": 75.562554},
    {"city": "Jalna", "lat": 19.833333, "lon": 75.883333},
    {"city": "Kalyan", "lat": 19.240283, "lon": 73.13073},
    {"city": "Karad", "lat": 17.284, "lon": 74.1779},
    {"city": "Karanja", "lat": 20.7083, "lon": 76.93},
    {"city": "Karanja Lad", "lat": 20.3969, "lon": 76.8908},
    {"city": "Karjat", "lat": 18.9121, "lon": 73.3259},
    {"city": "Kavathe Mahankal", "lat": 17.218, "lon": 74.416},
    {"city": "Khamgaon", "lat": 20.691, "lon": 76.6886},
    {"city": "Khopoli", "lat": 18.6958, "lon": 73.3207},
    {"city": "Kolad", "lat": 18.5132, "lon": 73.2166},
    {"city": "Kolhapur", "lat": 16.691031, "lon": 74.229523},
    {"city": "Kopargaon", "lat": 19.883333, "lon": 74.483333},
    {"city": "Koparkhairane", "lat": 19.0873, "lon": 72.9856},
    {"city": "Kothrud", "lat": 18.507399, "lon": 73.807648},
    {"city": "Kudal", "lat": 16.033333, "lon": 73.683333},
    {"city": "Kurla", "lat": 19.0667, "lon": 72.8833},
    {"city": "Latur", "lat": 18.406526, "lon": 76.560229},
    {"city": "Lonavala", "lat": 18.75, "lon": 73.4},
    {"city": "Mahad", "lat": 18.086, "lon": 73.3006},
    {"city": "Malegaon", "lat": 20.555256, "lon": 74.525539},
    {"city": "Malkapur", "lat": 20.4536, "lon": 76.3886},
    {"city": "Manmad", "lat": 20.3333, "lon": 74.4333},
    {"city": "Mira-Bhayandar", "lat": 19.271112, "lon": 72.854094},
    {"city": "Mumbai", "lat": 19.07609, "lon": 72.877426},
    {"city": "Nagpur", "lat": 21.1458, "lon": 79.088154},
    {"city": "Nanded", "lat": 19.148733, "lon": 77.321011},
    {"city": "Nandurbar", "lat": 21.317, "lon": 74.02},
    {"city": "Nashik", "lat": 20.011645, "lon": 73.790332},
    {"city": "Niphad", "lat": 20.074, "lon": 73.834},
    {"city": "Osmanabad", "lat": 18.169111, "lon": 76.035309},
    {"city": "Palghar", "lat": 19.691644, "lon": 72.768478},
    {"city": "Panaji", "lat": 15.4909, "lon": 73.8278},
    {"city": "Panvel", "lat": 18.989746, "lon": 73.117069},
    {"city": "Parbhani", "lat": 19.270335, "lon": 76.773347},
    {"city": "Peth", "lat": 18.125, "lon": 74.514},
    {"city": "Phaltan", "lat": 17.9977, "lon": 74.4066},
    {"city": "Pune", "lat": 18.52043, "lon": 73.856743},
    {"city": "Raigad", "lat": 18.515048, "lon": 73.179436},
    {"city": "Ramtek", "lat": 21.3142, "lon": 79.2676},
    {"city": "Ratnagiri", "lat": 16.990174, "lon": 73.311902},
    {"city": "Sangli", "lat": 16.855005, "lon": 74.56427},
    {"city": "Sangole", "lat": 17.126, "lon": 75.0331},
    {"city": "Saswad", "lat": 18.3461, "lon": 74.0335},
    {"city": "Satara", "lat": 17.688481, "lon": 73.993631},
    {"city": "Sawantwadi", "lat": 15.8964, "lon": 73.7626},
    {"city": "Shahada", "lat": 21.1167, "lon": 74.5667},
    {"city": "Shirdi", "lat": 19.7667, "lon": 74.4771},
    {"city": "Shirpur", "lat": 21.1286, "lon": 74.4172},
    {"city": "Shirur", "lat": 18.7939, "lon": 74.0305},
    {"city": "Shrirampur", "lat": 19.6214, "lon": 73.8653},
    {"city": "Sinnar", "lat": 19.8531, "lon": 73.9976},
    {"city": "Solan", "lat": 30.9083, "lon": 77.0989},
    {"city": "Solapur", "lat": 17.659921, "lon": 75.906393},
    {"city": "Talegaon", "lat": 18.7519, "lon": 73.487},
    {"city": "Thane", "lat": 19.218331, "lon": 72.978088},
    {"city": "Achalpur", "lat": 20.1833, "lon": 77.6833},
    {"city": "Akot", "lat": 21.1, "lon": 77.1167},
    {"city": "Ambajogai", "lat": 18.9667, "lon": 76.6833},
    {"city": "Amalner", "lat": 21.0333, "lon": 75.3333},
    {"city": "Anjangaon Surji", "lat": 21.1167, "lon": 77.8667},
    {"city": "Arvi", "lat": 20.45, "lon": 78.15},
    {"city": "Ashti", "lat": 18.0, "lon": 76.25},
    {"city": "Atpadi", "lat": 17.1667, "lon": 74.4167},
    {"city": "Baramati", "lat": 18.15, "lon": 74.6},
    {"city": "Barshi", "lat": 18.11, "lon": 76.06},
    {"city": "Basmat", "lat": 18.7, "lon": 77.856},
    {"city": "Bhokar", "lat": 19.5167, "lon": 77.3833},
    {"city": "Biloli", "lat": 19.5333, "lon": 77.2167},
    {"city": "Chikhli", "lat": 20.9, "lon": 76.0167},
    {"city": "Daund", "lat": 18.4667, "lon": 74.65},
    {"city": "Deola", "lat": 20.5667, "lon": 74.05},
    {"city": "Dhanora", "lat": 20.7167, "lon": 79.0167},
    {"city": "Dharni", "lat": 21.25, "lon": 78.2667},
    {"city": "Dharur", "lat": 18.0833, "lon": 76.7},
    {"city": "Digras", "lat": 19.45, "lon": 77.55},
    {"city": "Dindori", "lat": 21.0, "lon": 79.0},
    {"city": "Dondaicha", "lat": None, "lon": None},  # 좌표 누락
    {"city": "Erandol", "lat": 21.0167, "lon": 75.2167},
    {"city": "Faizpur", "lat": 21.1167, "lon": 75.7167},
    {"city": "Gadhinglaj", "lat": 16.2333, "lon": 74.1333},
    {"city": "Guhagar", "lat": 16.4, "lon": 73.4},
    {"city": "Hinganghat", "lat": 20.0167, "lon": 78.7667},
    {"city": "Igatpuri", "lat": 19.6961, "lon": 73.5212},
    {"city": "Junnar", "lat": 19.2667, "lon": 73.8833},
    {"city": "Kankavli", "lat": 16.3833, "lon": 73.5167},
    {"city": "Koregaon", "lat": 17.2333, "lon": 74.1167},
    {"city": "Kupwad", "lat": 16.7667, "lon": 74.4667},
    {"city": "Lonar", "lat": 19.9833, "lon": 76.5167},
    {"city": "Mangaon", "lat": 18.1869, "lon": 73.2555},
    {"city": "Mangalwedha", "lat": 16.6667, "lon": 75.1333},
    {"city": "Morshi", "lat": 20.0556, "lon": 77.7647},
    {"city": "Pandharpur", "lat": 17.6658, "lon": 75.3203},
    {"city": "Parli", "lat": 18.8778, "lon": 76.65},
    {"city": "Rahuri", "lat": 19.2833, "lon": 74.5833},
    {"city": "Raver", "lat": 20.5876, "lon": 75.9002},
    {"city": "Sangamner", "lat": 19.3167, "lon": 74.5333},
    {"city": "Savner", "lat": 21.0833, "lon": 79.1333},
    {"city": "Sillod", "lat": 20.0667, "lon": 75.1833},
    {"city": "Tumsar", "lat": 20.4623, "lon": 79.5429},
    {"city": "Udgir", "lat": 18.4167, "lon": 77.1239},
    {"city": "Ulhasnagar", "lat": 19.218451, "lon": 73.16024},
    {"city": "Vasai-Virar", "lat": 19.391003, "lon": 72.839729},
    {"city": "Wadgaon Road", "lat": 18.52, "lon": 73.85},
    {"city": "Wadwani", "lat": 18.9, "lon": 76.69},
    {"city": "Wai", "lat": 17.9524, "lon": 73.8775},
    {"city": "Wani", "lat": 19.0, "lon": 78.002},
    {"city": "Wardha", "lat": 20.745445, "lon": 78.602452},
    {"city": "Wardha Road", "lat": 20.75, "lon": 78.6},
    {"city": "Yavatmal", "lat": 20.389917, "lon": 78.130051}
]

# 중복 제거 및 유효 좌표만 필터링
city_dict = {}
for c in CSV_CITIES:
    if c["lat"] is not None and c["lon"] is not None:
        city_dict[c["city"]] = {"lat": c["lat"], "lon": c["lon"]}

major_cities = ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik", "Kalyan", "Vasai-Virar", "Aurangabad", "Solapur", "Mira-Bhayandar", "Bhiwandi", "Amravati", "Nanded", "Kolhapur", "Ulhasnagar", "Sangli", "Malegaon", "Jalgaon", "Akola", "Latur", "Dhule", "Ahmadnagar", "Chandrapur", "Parbhani", "Ichalkaranji", "Jalna", "Ambernath", "Bhusawal", "Panvel", "Dombivli"]

# 주요 도시 중 city_dict에 있는 것만
major_cities_available = [c for c in major_cities if c in city_dict]

# 나머지 도시 알파벳 순
remaining_cities = sorted([c for c in city_dict if c not in major_cities_available])

city_options = ["공연없음"] + major_cities_available + remaining_cities

# --- 초기 도시 (기존 DEFAULT_CITIES는 더 이상 사용하지 않음) ---
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, [])

# --- CSS ---
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
    .add-city-btn { background:white !important; color:black !important; font-weight:bold; border-radius:50%; width:40px; height:40px; font-size:1.5rem; display:flex; align-items:center; justify-content:center; }
    .selectbox-small { width: 70% !important; }
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
                        notice = {"id": str(uuid.uuid4()), "title": title, "content": content,
                                         "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
                                         "image": img_path, "file": file_path}
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

# --- 투어 경로 & 도시 추가 ---
if st.session_state.map_open:
    cities = load_json(CITY_FILE)
    
    # 임시로 추가되었으나 아직 저장되지 않은 도시 (세션에만 존재)
    if 'new_cities' not in st.session_state:
        st.session_state.new_cities = []
        
    # 모든 도시 목록 (기존 저장된 것 + 세션의 임시 추가된 것)
    all_cities_data = cities + st.session_state.new_cities
    
    # --- 지도 초기화 ---
    # Pune 중심 (18.52043, 73.856743)
    m = folium.Map(location=[18.52043, 73.856743], zoom_start=7, tiles="OpenStreetMap")

    # --- 마커 및 경로 표시 ---
    route_points = []
    
    # 도시들을 날짜 순으로 정렬 (저장된 도시만 정렬 가능)
    sorted_cities = sorted(cities, key=lambda x: x.get('date', '9999-12-31'))
    
    # 임시로 추가된 도시들을 포함하여 표시할 리스트 생성
    display_cities = []
    
    # 1. 저장된 도시 (날짜 순서)
    for city_data in sorted_cities:
        if city_data['city'] in city_dict: # 좌표가 있는 경우에만
             city_with_sort_key = city_data.copy()
             city_with_sort_key['sort_date_key'] = city_data.get('date', '9999-12-31')
             display_cities.append(city_with_sort_key)
             
    # 2. 임시로 추가된 도시 (아직 저장되지 않은 도시) - 중복 방지 로직 필요
    existing_city_names = {c['city'] for c in display_cities}
    for new_city in st.session_state.new_cities:
        if new_city['city'] not in existing_city_names:
            # 세션에 저장된 날짜 포맷이 다를 수 있으므로 안전하게 처리
            try:
                if isinstance(new_city['date'], date):
                    date_str = new_city['date'].strftime("%Y-%m-%d")
                elif isinstance(new_city['date'], str):
                     date_str = new_city['date']
                else:
                    date_str = '9999-12-31' # 날짜 정보 없으면 맨 뒤
            except:
                date_str = '9999-12-31'
                
            city_with_sort_key = new_city.copy()
            city_with_sort_key['sort_date_key'] = date_str
            display_cities.append(city_with_sort_key)

    # 최종 표시할 리스트를 날짜 키로 정렬
    display_cities = sorted(display_cities, key=lambda x: x.get('sort_date_key', '9999-12-31'))
    
    # 마커 찍기
    for city_data in display_cities:
        city_name = city_data['city']
        lat = city_data.get('lat')
        lon = city_data.get('lon')
        
        if lat and lon:
            # Google Maps 링크가 있으면 해당 좌표를 우선 사용 (여기서는 원래 좌표를 사용하고 팝업에 링크만 표시)
            
            # Popup HTML 구성
            popup_html = f"<b>{city_name}</b><br>"
            popup_html += f"{_('venue')}: {city_data.get('venue', 'N/A')}<br>"
            popup_html += f"{_('seats')}: {city_data.get('seats', 'N/A')}<br>"
            date_display = city_data.get('date', 'N/A')
            # date가 date 객체일 수도 있으므로 문자열로 통일
            if isinstance(date_display, date):
                 date_display = date_display.strftime("%Y-%m-%d")
            popup_html += f"{_('date')}: {date_display[:10]}<br>"
            
            if city_data.get('google_link'):
                popup_html += f'<a href="{city_data["google_link"]}" target="_blank">{_("google_link")}</a>'
            
            # 아이콘 색상 설정 (예: Indoor는 빨강, Outdoor는 파랑)
            icon_color = 'red' if city_data.get('indoor') else 'blue'
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=city_name,
                icon=folium.Icon(color=icon_color, icon='info-sign')
            ).add_to(m)
            
            route_points.append([lat, lon])

    # 경로 그리기 (AntPath 사용)
    if len(route_points) > 1:
        AntPath(route_points, options={"color": "#FF0000", "weight": 5, "opacity": 0.8}).add_to(m)


    st_folium(m, width=900, height=550, key="tour_map")

    if st.session_state.admin:
        
        # 도시 선택 박스 + 추가 버튼 (나란히 배치)
        col_select, col_add = st.columns([2, 1])
        with col_select:
            selected_city = st.selectbox(
                "도시", options=city_options, key="city_select_header", index=0,
                help="추가할 도시 선택", label_visibility="collapsed"
            )
        with col_add:
            # 버튼 클릭 시 임시 리스트에 추가하고 맵 키를 변경하여 강제 리렌더링 유도
            if st.button(_("add_city"), key="add_city_header_btn", help="도시 추가"):
                existing_city_names_full = {c['city'] for c in cities} | {c['city'] for c in st.session_state.new_cities}
                if selected_city != "공연없음" and selected_city not in existing_city_names_full: 
                    lat = city_dict[selected_city]["lat"]
                    lon = city_dict[selected_city]["lon"]
                    new_city = {
                        "city": selected_city, "venue": "", "seats": 500, "note": "", "google_link": "", "indoor": True,
                        "date": date.today(), "lat": lat, "lon": lon, "id": str(uuid.uuid4()) # ID 추가
                    }
                    st.session_state.new_cities.append(new_city)
                    # 상세 입력창 열림 상태 설정 및 강제 리렌더링
                    st.session_state[f"expand_{selected_city}"] = True
                    st.rerun()
                elif selected_city != "공연없음" and selected_city in existing_city_names_full:
                    st.warning(f"{selected_city}는 이미 목록에 있습니다.")


        st.markdown("---")
        st.subheader("임시 등록 도시 수정")
        
        # 새로 추가된 도시들
        if 'new_cities' in st.session_state and st.session_state.new_cities:
            
            cities_to_process = list(st.session_state.new_cities)
            
            for i, new_city in enumerate(cities_to_process):
                city_name = new_city['city']
                
                # 고유 키 생성: 도시 이름 + 인덱스를 조합
                unique_key_suffix = f"{city_name}_{i}_new"
                
                with st.expander(f"{city_name} (임시)", expanded=st.session_state.get(f"expand_{city_name}", False)):
                    col1, col2 = st.columns(2)
                    with col1:
                        current_date = new_city.get("date")
                        if isinstance(current_date, str) and current_date:
                            try:
                                current_date = datetime.strptime(current_date, "%Y-%m-%d").date()
                            except:
                                current_date = date.today()
                        elif not isinstance(current_date, date):
                            current_date = date.today()
                            
                        # 키를 고유하게 변경
                        new_city["date"] = st.date_input(_("date"), value=current_date, key=f"date_{unique_key_suffix}")
                        new_city["venue"] = st.text_input(_("venue"), value=new_city.get("venue", ""), key=f"venue_{unique_key_suffix}")
                        new_city["seats"] = st.number_input(_("seats"), min_value=0, value=int(new_city.get("seats", 500)), step=50, key=f"seats_{unique_key_suffix}")
                    with col2:
                        # 키를 고유하게 변경
                        new_city["google_link"] = st.text_input(_("google_link"), value=new_city.get("google_link", ""), key=f"google_link_{unique_key_suffix}")
                        new_city["note"] = st.text_input(_("note"), value=new_city.get("note", ""), key=f"note_{unique_key_suffix}")

                    col_radio, col_reg, col_rem = st.columns([3, 1, 1])
                    with col_radio:
                        # 키를 고유하게 변경
                        venue_type = st.radio(
                            "공연 장소 유형", [_("indoor"), _("outdoor")],
                            index=0 if new_city.get("indoor", True) else 1,
                            horizontal=True, key=f"venue_type_{unique_key_suffix}"
                        )
                        new_city["indoor"] = venue_type == _("indoor")
                    with col_reg:
                        # 키를 고유하게 변경
                        if st.button(_("register"), key=f"reg_{unique_key_suffix}"):
                            if new_city.get("venue"):
                                save_city = new_city.copy()
                                # DB에 저장할 형태 맞추기
                                save_city["date"] = save_city["date"].strftime("%Y-%m-%d")
                                save_city["seats"] = str(save_city["seats"])
                                if 'sort_date_key' in save_city: del save_city['sort_date_key'] 
                                cities.insert(0, save_city)
                                save_json(CITY_FILE, cities)
                                
                                # 세션에서 제거하고 다시 로드
                                st.session_state.new_cities.pop(i)
                                st.success("등록 완료!")
                                st.rerun()
                            else:
                                st.warning(_("warning"))
                    with col_rem:
                        # 키를 고유하게 변경
                        if st.button(_("remove"), key=f"rem_{unique_key_suffix}"):
                            st.session_state.new_cities.pop(i)
                            st.rerun()
                            
    st.markdown("---")
    if cities:
        st.subheader("저장된 투어 도시")
        # 저장된 도시들을 보여주는 테이블
        df = pd.DataFrame(cities)
        df = df.sort_values(by='date', ascending=False)
        st.dataframe(df[['city', 'venue', 'date', 'seats']], use_container_width=True)
        
        # **기존 도시 수정 및 삭제 로직 (키 중복 해결)**
        for i, city_data in enumerate(cities):
            city_name = city_data['city']
            
            # 고유 키 생성: 도시 이름 + 인덱스
            unique_key_suffix = f"{city_name}_{i}"
            
            with st.expander(f"{city_data['date']} | {city_name}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    # 날짜 포맷 변환
                    try:
                        current_date = datetime.strptime(city_data['date'], "%Y-%m-%d").date()
                    except:
                        current_date = date.today()
                        
                    # 💡 오류 발생 지점: 키에 인덱스(i) 추가
                    city_data['date'] = st.date_input(_("date"), value=current_date, key=f"date_saved_{unique_key_suffix}")
                    city_data['venue'] = st.text_input(_("venue"), value=city_data.get("venue", ""), key=f"venue_saved_{unique_key_suffix}")
                    city_data['seats'] = st.number_input(_("seats"), min_value=0, value=int(city_data.get("seats", 500)), step=50, key=f"seats_saved_{unique_key_suffix}")
                with col2:
                    # 💡 키에 인덱스(i) 추가
                    city_data['google_link'] = st.text_input(_("google_link"), value=city_data.get("google_link", ""), key=f"google_link_saved_{unique_key_suffix}")
                    city_data['note'] = st.text_input(_("note"), value=city_data.get("note", ""), key=f"note_saved_{unique_key_suffix}")

                col_radio, col_upd, col_rem = st.columns([3, 1, 1])
                with col_radio:
                    # 💡 키에 인덱스(i) 추가
                    venue_type = st.radio(
                        "공연 장소 유형", [_("indoor"), _("outdoor")],
                        index=0 if city_data.get("indoor", True) else 1,
                        horizontal=True, key=f"venue_type_saved_{unique_key_suffix}"
                    )
                    city_data["indoor"] = venue_type == _("indoor")
                with col_upd:
                    # 💡 키에 인덱스(i) 추가
                    if st.button(_("update"), key=f"upd_{unique_key_suffix}"):
                        city_data["date"] = city_data["date"].strftime("%Y-%m-%d")
                        city_data["seats"] = str(city_data["seats"])
                        cities[i] = city_data
                        save_json(CITY_FILE, cities)
                        st.success(f"{city_name} 정보 업데이트 완료!")
                        st.rerun()
                with col_rem:
                    # 💡 키에 인덱스(i) 추가
                    if st.button(_("remove"), key=f"rem_saved_{unique_key_suffix}"):
                        cities.pop(i)
                        save_json(CITY_FILE, cities)
                        st.success(f"{city_name} 제거 완료!")
                        st.rerun()
    else:
        st.info("등록된 투어 도시가 없습니다.")


# --- 사이드바 & 모바일 ---
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
        <button onclick="if(document.getElementById('mobile_pw').value=='0009') window.location.href='?admin=true'; else alert('오류');" style="width:100%; padding:10px; background:#e74c3c; color:white; border:none; border-radius:8px;">{_("login")}</button>
    ''' if not st.session_state.admin else f'''
        <button onclick="window.location.href='?admin=false'" style="width:100%; padding:10px; background:#27ae60; color:white; border:none; border-radius:8px;">{_("logout")}</button>
    '''}
</div>
''', unsafe_allow_html=True)

with st.sidebar:
    sel = st.selectbox("언어", ["한국어", "English", "हिंदी"], index=0 if st.session_state.lang == "ko" else 1 if st.session_state.lang == "en" else 2)
    if sel == "English" and st.session_state.lang != "en":
        st.session_state.lang = "en"
        st.rerun()
    elif sel == "한국어" and st.session_state.lang != "ko":
        st.session_state.lang = "ko"
        st.rerun()
    elif sel == "हिंदी" and st.session_state.lang != "hi":
        st.session_state.lang = "hi"
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
