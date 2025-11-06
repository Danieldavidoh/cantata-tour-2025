import streamlit as st
from datetime import datetime
import json, os, uuid, base64, re, requests
from pytz import timezone
from streamlit_autorefresh import st_autorefresh

# 3초 새로고침 (일반 모드)
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh")

# 기본 설정
st.set_page_config(page_title="कांताता टूर 2025 | Cantata Tour 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 세션 초기화
defaults = {
    "admin": False,
    "lang": "ko",
    "mode": None,
    "edit_city": None,
    "expanded": {}
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 다국어
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "caption": "마하라스트라 투어 관리 시스템",
        "tab_notice": "공지 관리",
        "tab_map": "투어 경로",
        "map_title": "경로 보기",
        "password": "비밀번호",
        "login": "로그인",
        "logout": "로그아웃",
        "wrong_pw": "비밀번호가 틀렸습니다.",
        "select_city": "도시 선택",
        "venue": "공연장소",
        "seats": "예상 인원",
        "note": "특이사항",
        "google_link": "구글맵 링크",
        "indoor": "실내",
        "outdoor": "실외",
        "register": "등록",
        "edit": "수정",
        "remove": "삭제",
        "date": "날짜",
        "add": "추가",
        "cancel": "취소",
        "title_label": "제목",
        "content_label": "내용",
        "upload_image": "이미지 업로드",
        "upload_file": "파일 업로드",
        "submit": "등록",
        "warning": "제목과 내용을 모두 입력해주세요.",
        "file_download": "파일 다운로드",
    },
    "en": {
        "title": "Cantata Tour 2025",
        "caption": "Maharashtra Tour Management System",
        "tab_notice": "Notice",
        "tab_map": "Tour Route",
        "map_title": "View Route",
        "password": "Password",
        "login": "Login",
        "logout": "Logout",
        "wrong_pw": "Wrong password.",
        "select_city": "Select City",
        "venue": "Venue",
        "seats": "Expected Attendance",
        "note": "Notes",
        "google_link": "Google Maps Link",
        "indoor": "Indoor",
        "outdoor": "Outdoor",
        "register": "Register",
        "edit": "Edit",
        "remove": "Remove",
        "date": "Date",
        "add": "Add",
        "cancel": "Cancel",
        "title_label": "Title",
        "content_label": "Content",
        "upload_image": "Upload Image",
        "upload_file": "Upload File",
        "submit": "Submit",
        "warning": "Please enter both title and content.",
        "file_download": "Download File",
    },
    "hi": {
        "title": "कांताता टूर 2025",
        "caption": "महाराष्ट्र टूर प्रबंधन प्रणाली",
        "tab_notice": "सूचना",
        "tab_map": "टूर मार्ग",
        "map_title": "मार्ग देखें",
        "password": "पासवर्ड",
        "login": "लॉगिन",
        "logout": "लॉगआउट",
        "wrong_pw": "गलत पासवर्ड।",
        "select_city": "शहर चुनें",
        "venue": "स्थल",
        "seats": "अपेक्षित उपस्थिति",
        "note": "नोट्स",
        "google_link": "गूगल मैप्स लिंक",
        "indoor": "इनडोर",
        "outdoor": "आउटडोर",
        "register": "रजिस्टर",
        "edit": "संपादित करें",
        "remove": "हटाएं",
        "date": "तारीख",
        "add": "जोड़ें",
        "cancel": "रद्द करें",
        "title_label": "शीर्षक",
        "content_label": "सामग्री",
        "upload_image": "छवि अपलोड करें",
        "upload_file": "फ़ाइल अपलोड करें",
        "submit": "जमा करें",
        "warning": "शीर्षक और सामग्री दोनों दर्ज करें।",
        "file_download": "फ़ाइल डाउनलोड करें",
    }
}
_ = LANG[st.session_state.lang]

# 유틸
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_latlon_from_shortlink(short_url):
    try:
        r = requests.get(short_url, allow_redirects=True, timeout=5)
        final_url = r.url
        match = re.search(r'@([0-9\.\-]+),([0-9\.\-]+)', final_url)
        if match:
            return float(match.group(1)), float(match.group(2))
    except:
        pass
    return None, None

# Google Maps Embed URL (단순 path만)
def generate_google_maps_embed_url(cities_data):
    if not cities_data:
        return "https://www.google.com/maps/embed"
    
    # 중심점
    lats = [c['lat'] for c in cities_data]
    lons = [c['lon'] for c in cities_data]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # 경로만
    path = "path=color:0xff0000ff|weight:5|" + "|".join([f"{c['lat']},{c['lon']}" for c in cities_data])
    
    return f"https://www.google.com/maps/embed/v1/view?center={center_lat},{center_lon}&zoom=7&{path}"

# 공지 기능
def add_notice(title, content, image_file=None, upload_file=None):
    img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_file.name}") if image_file else None
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{upload_file.name}") if upload_file else None
    if image_file:
        with open(img_path, "wb") as f:
            f.write(image_file.read())
    if upload_file:
        with open(file_path, "wb") as f:
            f.write(upload_file.read())
    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
        "image": img_path,
        "file": file_path
    }
    data = load_json(NOTICE_FILE)
    data.insert(0, new_notice)
    save_json(NOTICE_FILE, data)
    st.session_state.expanded = {}
    st.toast("공지가 등록되었습니다.")
    st.rerun()

def render_notice_list(show_delete=False):
    data = load_json(NOTICE_FILE)
    for idx, n in enumerate(data):
        key = f"notice_{idx}"
        expanded = st.session_state.expanded.get(key, False)
        with st.expander(f"{n['date']} | {n['title']}", expanded=expanded):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                href = f'<a href="data:file/octet-stream;base64,{base64.b64encode(open(n["file"], "rb").read()).decode()}" download="{os.path.basename(n["file"])}">{_["file_download"]}</a>'
                st.markdown(href, unsafe_allow_html=True)
            if show_delete and st.button(_["remove"], key=f"del_{idx}"):
                data.pop(idx)
                save_json(NOTICE_FILE, data)
                st.session_state.expanded = {}
                st.toast("공지가 삭제되었습니다.")
                st.rerun()
        if st.session_state.expanded.get(key, False) != expanded:
            st.session_state.expanded[key] = expanded

# 지도 + 도시 관리
def render_map():
    st.subheader(_["map_title"])
    cities_data = load_json(CITY_FILE)

    if st.session_state.admin:
        col1, col2 = st.columns([8, 2])
        with col2:
            if st.button(_["add"], key="add_main"):
                st.session_state.mode = "add"
                st.rerun()

    if st.session_state.mode == "add" and st.session_state.admin:
        if not os.path.exists(CITY_LIST_FILE):
            default_cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"]
            save_json(CITY_LIST_FILE, default_cities)
        cities_list = load_json(CITY_LIST_FILE)
        existing = {c["city"] for c in cities_data}
        available = [c for c in cities_list if c not in existing]

        if not available:
            st.info("모든 도시 등록됨")
            if st.button("닫기"):
                st.session_state.mode = None
                st.rerun()
        else:
            with st.expander("새 도시 추가", expanded=True):
                city_name = st.selectbox(_["select_city"], available, key="add_select")
                venue = st.text_input(_["venue"], key="add_venue")
                seats = st.number_input(_["seats"], min_value=0, step=50, key="add_seats")
                venue_type = st.radio("공연형태", [_["indoor"], _["outdoor"]], horizontal=True, key="add_type")
                map_link = st.text_input(_["google_link"], key="add_link")
                note = st.text_area(_["note"], key="add_note")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button(_["register"], key=f"reg_{city_name}"):
                        lat, lon = None, None
                        if map_link.strip():
                            lat, lon = extract_latlon_from_shortlink(map_link)
                        if not lat or not lon:
                            coords = {
                                "Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567),
                                "Nagpur": (21.1458, 79.0882), "Nashik": (19.9975, 73.7898),
                                "Aurangabad": (19.8762, 75.3433)
                            }
                            lat, lon = coords.get(city_name, (19.0, 73.0))

                        new_city = {
                            "city": city_name,
                            "venue": venue or "미정",
                            "seats": seats,
                            "type": venue_type,
                            "note": note or "없음",
                            "lat": lat,
                            "lon": lon,
                            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                        }
                        cities_data.append(new_city)
                        save_json(CITY_FILE, cities_data)
                        st.session_state.mode = None
                        st.session_state.expanded = {}
                        st.success(f"{city_name} 등록 완료!")
                        st.rerun()

                with c2:
                    if st.button(_["cancel"], key="cancel_add"):
                        st.session_state.mode = None
                        st.rerun()

    # 도시 목록
    for idx, city in enumerate(cities_data):
        key = f"city_{idx}"
        expanded = st.session_state.expanded.get(key, False)
        with st.expander(f"{city['city']}", expanded=expanded):
            st.write(f"**{_['date']}:** {city.get('date', '')}")
            st.write(f"**{_['venue']}:** {city.get('venue', '')}")
            st.write(f"**{_['seats']}:** {city.get('seats', '')}")
            st.write(f"**{_['note']}:** {city.get('note', '')}")
            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(_["edit"], key=f"edit_{idx}"):
                        st.session_state.mode = "edit"
                        st.session_state.edit_city = city["city"]
                        st.rerun()
                with c2:
                    if st.button(_["remove"], key=f"del_{idx}"):
                        cities_data.pop(idx)
                        save_json(CITY_FILE, cities_data)
                        st.session_state.expanded = {}
                        st.toast("도시 삭제됨")
                        st.rerun()
        if st.session_state.expanded.get(key, False) != expanded:
            st.session_state.expanded[key] = expanded

    # Google Maps Embed (path만)
    st.markdown("---")
    if cities_data:
        embed_url = generate_google_maps_embed_url(cities_data)
        iframe = f'''
        <iframe 
            width="100%" 
            height="550" 
            style="border:0" 
            loading="lazy" 
            allowfullscreen 
            src="{embed_url}">
        </iframe>
        '''
        st.components.v1.html(iframe, height=550)
    else:
        st.info("등록된 도시 없음")

# 사이드바
with st.sidebar:
    lang_options = ["한국어", "English", "हिंदी"]
    lang_map = {"한국어": "ko", "English": "en", "हिंदी": "hi"}
    current_idx = lang_options.index("한국어" if st.session_state.lang == "ko" else "English" if st.session_state.lang == "en" else "हिंदी")
    selected_lang = st.selectbox("언어", lang_options, index=current_idx)
    new_lang = lang_map[selected_lang]
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")

    if not st.session_state.admin:
        st.markdown("### 관리자 로그인")
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0000":
                st.session_state.admin = True
                st.success("관리자 모드 ON")
                st.rerun()
            else:
                st.error(_["wrong_pw"])
    else:
        st.success("관리자 모드")
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.rerun()

# 메인
st.markdown(f"# {_['title']} ")
st.caption(_["caption"])

tab1, tab2 = st.tabs([_["tab_notice"], _["tab_map"]])

with tab1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_["title_label"])
            c = st.text_area(_["content_label"])
            img = st.file_uploader(_["upload_image"], type=["png", "jpg", "jpeg"])
            f = st.file_uploader(_["upload_file"])
            if st.form_submit_button(_["submit"]):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_["warning"])
        render_notice_list(show_delete=True)
    else:
        render_notice_list(show_delete=False)
        if st.button("새로고침"):
            st.rerun()

with tab2:
    render_map()
