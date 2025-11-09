import json, os, uuid, base64, random
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh

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
def load_json(f): 
    if os.path.exists(f):
        try:
            return json.load(open(f, "r", encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 도시 목록 생성 ---
city_dict = {
    "Ahmadnagar": {"lat": 19.095193, "lon": 74.749596},
    "Akola": {"lat": 20.702269, "lon": 77.004699},
    "Ambernath": {"lat": 19.186354, "lon": 73.191948},
    "Amravati": {"lat": 20.93743, "lon": 77.779271},
    "Aurangabad": {"lat": 19.876165, "lon": 75.343314},
    "Badlapur": {"lat": 19.1088, "lon": 73.1311},
    "Bhandara": {"lat": 21.180052, "lon": 79.564987},
    "Bhiwandi": {"lat": 19.300282, "lon": 73.069645},
    "Bhusawal": {"lat": 21.02606, "lon": 75.830095},
    "Chandrapur": {"lat": 19.957275, "lon": 79.296875},
    "Chiplun": {"lat": 17.5322, "lon": 73.516},
    "Dhule": {"lat": 20.904964, "lon": 74.774651},
    "Dombivli": {"lat": 19.2183, "lon": 73.0865},
    "Gondia": {"lat": 21.4598, "lon": 80.195},
    "Hingoli": {"lat": 19.7146, "lon": 77.1424},
    "Ichalkaranji": {"lat": 16.6956, "lon": 74.4561},
    "Jalgaon": {"lat": 21.007542, "lon": 75.562554},
    "Jalna": {"lat": 19.833333, "lon": 75.883333},
    "Kalyan": {"lat": 19.240283, "lon": 73.13073},
    "Karad": {"lat": 17.284, "lon": 74.1779},
    "Karanja": {"lat": 20.7083, "lon": 76.93},
    "Karanja Lad": {"lat": 20.3969, "lon": 76.8908},
    "Karjat": {"lat": 18.9121, "lon": 73.3259},
    "Kavathe Mahankal": {"lat": 17.218, "lon": 74.416},
    "Khamgaon": {"lat": 20.691, "lon": 76.6886},
    "Khopoli": {"lat": 18.6958, "lon": 73.3207},
    "Kolad": {"lat": 18.5132, "lon": 73.2166},
    "Kolhapur": {"lat": 16.691031, "lon": 74.229523},
    "Kopargaon": {"lat": 19.883333, "lon": 74.483333},
    "Koparkhairane": {"lat": 19.0873, "lon": 72.9856},
    "Kothrud": {"lat": 18.507399, "lon": 73.807648},
    "Kudal": {"lat": 16.033333, "lon": 73.683333},
    "Kurla": {"lat": 19.0667, "lon": 72.8833},
    "Latur": {"lat": 18.406526, "lon": 76.560229},
    "Lonavala": {"lat": 18.75, "lon": 73.4},
    "Mahad": {"lat": 18.086, "lon": 73.3006},
    "Malegaon": {"lat": 20.555256, "lon": 74.525539},
    "Malkapur": {"lat": 20.4536, "lon": 76.3886},
    "Manmad": {"lat": 20.3333, "lon": 74.4333},
    "Mira-Bhayandar": {"lat": 19.271112, "lon": 72.854094},
    "Mumbai": {"lat": 19.07609, "lon": 72.877426},
    "Nagpur": {"lat": 21.1458, "lon": 79.088154},
    "Nanded": {"lat": 19.148733, "lon": 77.321011},
    "Nandurbar": {"lat": 21.317, "lon": 74.02},
    "Nashik": {"lat": 20.011645, "lon": 73.790332},
    "Niphad": {"lat": 20.074, "lon": 73.834},
    "Osmanabad": {"lat": 18.169111, "lon": 76.035309},
    "Palghar": {"lat": 19.691644, "lon": 72.768478},
    "Panaji": {"lat": 15.4909, "lon": 73.8278},
    "Panvel": {"lat": 18.989746, "lon": 73.117069},
    "Parbhani": {"lat": 19.270335, "lon": 76.773347},
    "Peth": {"lat": 18.125, "lon": 74.514},
    "Phaltan": {"lat": 17.9977, "lon": 74.4066},
    "Pune": {"lat": 18.52043, "lon": 73.856743},
    "Raigad": {"lat": 18.515048, "lon": 73.179436},
    "Ramtek": {"lat": 21.3142, "lon": 79.2676},
    "Ratnagiri": {"lat": 16.990174, "lon": 73.311902},
    "Sangli": {"lat": 16.855005, "lon": 74.56427},
    "Sangole": {"lat": 17.126, "lon": 75.0331},
    "Saswad": {"lat": 18.3461, "lon": 74.0335},
    "Satara": {"lat": 17.688481, "lon": 73.993631},
    "Sawantwadi": {"lat": 15.8964, "lon": 73.7626},
    "Shahada": {"lat": 21.1167, "lon": 74.5667},
    "Shirdi": {"lat": 19.7667, "lon": 74.4771},
    "Shirpur": {"lat": 21.1286, "lon": 74.4172},
    "Shirur": {"lat": 18.7939, "lon": 74.0305},
    "Shrirampur": {"lat": 19.6214, "lon": 73.8653},
    "Sinnar": {"lat": 19.8531, "lon": 73.9976},
    "Solan": {"lat": 30.9083, "lon": 77.0989},
    "Solapur": {"lat": 17.659921, "lon": 75.906393},
    "Talegaon": {"lat": 18.7519, "lon": 73.487},
    "Thane": {"lat": 19.218331, "lon": 72.978088},
    "Achalpur": {"lat": 20.1833, "lon": 77.6833},
    "Akot": {"lat": 21.1, "lon": 77.1167},
    "Ambajogai": {"lat": 18.9667, "lon": 76.6833},
    "Amalner": {"lat": 21.0333, "lon": 75.3333},
    "Anjangaon Surji": {"lat": 21.1167, "lon": 77.8667},
    "Arvi": {"lat": 20.45, "lon": 78.15},
    "Ashti": {"lat": 18.0, "lon": 76.25},
    "Atpadi": {"lat": 17.1667, "lon": 74.4167},
    "Baramati": {"lat": 18.15, "lon": 74.6},
    "Barshi": {"lat": 18.11, "lon": 76.06},
    "Basmat": {"lat": 18.7, "lon": 77.856},
    "Bhokar": {"lat": 19.5167, "lon": 77.3833},
    "Biloli": {"lat": 19.5333, "lon": 77.2167},
    "Chikhli": {"lat": 20.9, "lon": 76.0167},
    "Daund": {"lat": 18.4667, "lon": 74.65},
    "Deola": {"lat": 20.5667, "lon": 74.05},
    "Dhanora": {"lat": 20.7167, "lon": 79.0167},
    "Dharni": {"lat": 21.25, "lon": 78.2667},
    "Dharur": {"lat": 18.0833, "lon": 76.7},
    "Digras": {"lat": 19.45, "lon": 77.55},
    "Dindori": {"lat": 21.0, "lon": 79.0},
    "Erandol": {"lat": 21.0167, "lon": 75.2167},
    "Faizpur": {"lat": 21.1167, "lon": 75.7167},
    "Gadhinglaj": {"lat": 16.2333, "lon": 74.1333},
    "Guhagar": {"lat": 16.4, "lon": 73.4},
    "Hinganghat": {"lat": 20.0167, "lon": 78.7667},
    "Igatpuri": {"lat": 19.6961, "lon": 73.5212},
    "Junnar": {"lat": 19.2667, "lon": 73.8833},
    "Kankavli": {"lat": 16.3833, "lon": 73.5167},
    "Koregaon": {"lat": 17.2333, "lon": 74.1167},
    "Kupwad": {"lat": 16.7667, "lon": 74.4667},
    "Lonar": {"lat": 19.9833, "lon": 76.5167},
    "Mangaon": {"lat": 18.1869, "lon": 73.2555},
    "Mangalwedha": {"lat": 16.6667, "lon": 75.1333},
    "Morshi": {"lat": 20.0556, "lon": 77.7647},
    "Pandharpur": {"lat": 17.6658, "lon": 75.3203},
    "Parli": {"lat": 18.8778, "lon": 76.65},
    "Rahuri": {"lat": 19.2833, "lon": 74.5833},
    "Raver": {"lat": 20.5876, "lon": 75.9002},
    "Sangamner": {"lat": 19.3167, "lon": 74.5333},
    "Savner": {"lat": 21.0833, "lon": 79.1333},
    "Sillod": {"lat": 20.0667, "lon": 75.1833},
    "Tumsar": {"lat": 20.4623, "lon": 79.5429},
    "Udgir": {"lat": 18.4167, "lon": 77.1239},
    "Ulhasnagar": {"lat": 19.218451, "lon": 73.16024},
    "Vasai-Virar": {"lat": 19.391003, "lon": 72.839729},
    "Wadgaon Road": {"lat": 18.52, "lon": 73.85},
    "Wadwani": {"lat": 18.9, "lon": 76.69},
    "Wai": {"lat": 17.9524, "lon": 73.8775},
    "Wani": {"lat": 19.0, "lon": 78.002},
    "Wardha": {"lat": 20.745445, "lon": 78.602452},
    "Wardha Road": {"lat": 20.75, "lon": 78.6},
    "Yavatmal": {"lat": 20.389917, "lon": 78.130051}
}

# --- 도시 목록 생성 ---
major_cities = ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik", "Kalyan", "Vasai-Virar", "Aurangabad", "Solapur", "Mira-Bhayandar", "Bhiwandi", "Amravati", "Nanded", "Kolhapur", "Ulhasnagar", "Sangli", "Malegaon", "Jalgaon", "Akola", "Latur", "Dhule", "Ahmadnagar", "Chandrapur", "Parbhani", "Ichalkaranji", "Jalna", "Ambernath", "Bhusawal", "Panvel", "Dombivli"]

major_cities_available = [c for c in major_cities if c in city_dict]

remaining_cities = sorted([c for c in city_dict if c not in major_cities_available])

city_options = ["공연없음"] + major_cities_available + remaining_cities

# --- 초기 도시 ---
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, [])

# --- CSS ---
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
    [data-testid="stAppViewContainer"] { background: url("background_christmas_dark.png"); background-size: cover; background-attachment: fixed; padding-top: 0 !important; }
    .header-container { text-align: center; margin: 0 !important; }
    .christmas-decoration { display: flex; justify-content: center; gap: 12px; margin-bottom: 0 !important; }
    .christmas-decoration
