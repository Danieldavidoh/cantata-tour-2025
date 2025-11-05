import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =============================================
# 세션 초기화
# =============================================
defaults = {
    "admin": False,
    "lang": "ko",
    "last_notice_count": 0,
    "route": [],
    "venues": {}
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================================
# 다국어 (한국어, 영어, 힌디어)
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "caption": "마하라스트라 지역 투어 관리 시스템",
        "tab_notice": "공지 관리",
        "tab_map": "투어 경로",
        "add_notice": "새 공지 추가",
        "title_label": "제목",
        "content_label": "내용",
        "upload_image": "이미지 업로드 (선택)",
        "upload_file": "파일 업로드 (선택)",
        "submit": "등록",
        "warning": "제목과 내용을 모두 입력해주세요.",
        "notice_list": "공지 목록",
        "no_notice": "등록된 공지가 없습니다.",
        "delete": "삭제",
        "map_title": "경로 보기",
        "admin_login": "관리자 로그인",
        "password": "비밀번호",
        "login": "로그인",
        "logout": "로그아웃",
        "wrong_pw": "비밀번호가 틀렸습니다.",
        "lang_select": "언어 선택",
        "file_download": "파일 다운로드",
        "add_city": "도시 추가",
        "select_city": "도시 선택",
        "add_city_btn": "추가",
        "tour_route": "투어 경로",
        "venue_name": "공연장 이름",
        "seats": "좌석 수",
        "google_link": "구글 지도 링크",
        "special_notes": "특이사항",
        "register": "등록",
        "navigate": "길찾기",
        "enter_venue_name": "공연장 이름을 입력하세요.",
        "venue_registered": "등록 완료",
        "indoor": "실내",
        "outdoor": "실외"
    },
    "en": {
        "title": "Cantata Tour 2025",
        "caption": "Maharashtra Region Tour Management",
        "tab_notice": "Notice Board",
        "tab_map": "Tour Route",
        "add_notice": "Add Notice",
        "title_label": "Title",
        "content_label": "Content",
        "upload_image": "Upload Image (Optional)",
        "upload_file": "Upload File (Optional)",
        "submit": "Submit",
        "warning": "Please fill in both title and content.",
        "notice_list": "Notice List",
        "no_notice": "No notices registered.",
        "delete": "Delete",
        "map_title": "View Route",
        "admin_login": "Admin Login",
        "password": "Password",
        "login": "Login",
        "logout": "Logout",
        "wrong_pw": "Incorrect password.",
        "lang_select": "Language",
        "file_download": "Download File",
        "add_city": "Add City",
        "select_city": "Select City",
        "add_city_btn": "Add",
        "tour_route": "Tour Route",
        "venue_name": "Venue Name",
        "seats": "Seats",
        "google_link": "Google Maps Link",
        "special_notes": "Special Notes",
        "register": "Register",
        "navigate": "Navigate",
        "enter_venue_name": "Please enter venue name.",
        "venue_registered": "Registered",
        "indoor": "Indoor",
        "outdoor": "Outdoor"
    },
    "hi": {
        "title": "कांताता टूर 2025",
        "caption": "महाराष्ट्र क्षेत्र टूर प्रबंधन",
        "tab_notice": "सूचना बोर्ड",
        "tab_map": "टूर मार्ग",
        "add_notice": "नई सूचना जोड़ें",
        "title_label": "शीर्षक",
        "content_label": "सामग्री",
        "upload_image": "छवि अपलोड करें (वैकल्पिक)",
        "upload_file": "फ़ाइल अपलोड करें (वैकल्पिक)",
        "submit": "जमा करें",
        "warning": "कृपया शीर्षक और सामग्री दोनों भरें।",
        "notice_list": "सूचना सूची",
        "no_notice": "कोई सूचना पंजीकृत नहीं।",
        "delete": "हटाएं",
        "map_title": "मार्ग देखें",
        "admin_login": "एडमिन लॉगिन",
        "password": "पासवर्ड",
        "login": "लॉगिन",
        "logout": "लॉगआउट",
        "wrong_pw": "गलत पासवर्ड।",
        "lang_select": "भाषा",
        "file_download": "फ़ाइल डाउनलोड करें",
        "add_city": "शहर जोड़ें",
        "select_city": "शहर चुनें",
        "add_city_btn": "जोड़ें",
        "tour_route": "टूर मार्ग",
        "venue_name": "स्थल का नाम",
        "seats": "सीटें",
        "google_link": "गूगल मैप्स लिंक",
        "special_notes": "विशेष टिप्पणियाँ",
        "register": "रजिस्टर",
        "navigate": "नेविगेट करें",
        "enter_venue_name": "कृपया स्थल का नाम दर्ज करें।",
        "venue_registered": "पंजीकृत",
        "indoor": "इंडोर",
        "outdoor": "आउटडोर"
    }
}

_ = LANG[st.session_state.lang]

# =============================================
# JSON 유틸
# =============================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_file_download_link(file_path, label):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">{label}</a>'

# =============================================
# 공지 추가/삭제
# =============================================
def add_notice(title, content, image_file=None, upload_file=None):
    img_path, file_path = None, None
    if image_file:
        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_file.name}")
        with open(img_path, "wb") as f:
            f.write(image_file.read())
    if upload_file:
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{upload_file.name}")
        with open(file_path, "wb") as f:
            f.write(upload_file.read())
    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now().strftime("%m/%d %H:%M"),
        "image": img_path,
        "file": file_path
    }
    data = load_json(NOTICE_FILE)
    data.insert(0, new_notice)
    save_json(NOTICE_FILE, data)
    st.toast("공지가 등록되었습니다.")
    st.rerun()

def delete_notice(notice_id):
    data = load_json(NOTICE_FILE)
    for n in data:
        if n["id"] == notice_id:
            if n.get("image") and os.path.exists(n["image"]):
                os.remove(n["image"])
            if n.get("file") and os.path.exists(n["file"]):
                os.remove(n["file"])
    data = [n for n in data if n["id"] != notice_id]
    save_json(NOTICE_FILE, data)
    st.toast("공지가 삭제되었습니다.")
    st.rerun()

# =============================================
# 공지 리스트
# =============================================
def render_notice_list(show_delete=False):
    data = load_json(NOTICE_FILE)
    if not data:
        st.info(_["no_notice"])
        return
    for idx, n in enumerate(data):
        with st.expander(f"{n['date']} | {n['title']}"):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                st.markdown(get_file_download_link(n["file"], _["file_download"]), unsafe_allow_html=True)
            if show_delete:
                if st.button(_["delete"], key=f"del_{n['id']}_{idx}"):
                    delete_notice(n["id"])

# =============================================
# 자동 새로고침 (10초마다)
# =============================================
try:
    from streamlit_autorefresh import st_autorefresh
    AUTO_REFRESH = True
except:
    AUTO_REFRESH = False

if not st.session_state.admin and AUTO_REFRESH:
    count = len(load_json(NOTICE_FILE))
    if st.session_state.last_notice_count == 0:
        st.session_state.last_notice_count = count
    st_autorefresh(interval=10 * 1000, key="auto_refresh")
    new_count = len(load_json(NOTICE_FILE))
    if new_count > st.session_state.last_notice_count:
        st.toast("새 공지가 등록되었습니다!")
        st.audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg")
        st.session_state.last_notice_count = new_count

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    st.markdown("### 언어 선택")
    lang_options = ["ko", "en", "hi"]
    lang_labels = ["한국어", "English", "हिन्दी"]
    current_idx = lang_options.index(st.session_state.lang)
    new_lang = st.selectbox(
        _["lang_select"],
        lang_options,
        format_func=lambda x: lang_labels[lang_options.index(x)],
        index=current_idx
    )
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")

    if not st.session_state.admin:
        st.markdown(f"### 관리자 로그인")
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

# =============================================
# 메인
# =============================================
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

# =============================================
# 투어 경로 탭
# =============================================
with tab2:
    # 도시 리스트
    CITIES = [
        "공연없음","Mumbai","Pune","Nagpur","Nashik","Thane","Aurangabad","Solapur","Kolhapur",
        "Amravati","Jalgaon","Akola","Latur","Ahmednagar","Dhule","Chandrapur","Parbhani",
        "Jalna","Bhusawal","Satara","Beed","Yavatmal","Gondia","Wardha","Nandurbar","Osmanabad",
        "Hingoli","Buldhana","Washim","Gadchiroli","Sangli","Ratnagiri","Sindhudurg","Nanded",
        "Palghar","Raigad","Baramati","Karad","Pandharpur","Malegaon","Ichalkaranji","Bhiwandi",
        "Ambarnath","Ulhasnagar","Panvel","Kalyan","Vasai","Virar","Mira-Bhayandar","Khopoli",
        "Alibag","Boisar","Dombivli","Badlapur","Talegaon","Chiplun","Mahad","Roha","Pen",
        "Murbad","Khed","Satana","Sinnar","Shirdi","Sangamner","Manmad","Shahada","Bodwad",
        "Raver","Malkapur","Nandura","Shegaon","Daryapur","Mangrulpir","Pusad","Umarkhed",
        "Wani","Ballarpur","Bhandara","Tumsar","Deoli","Selu","Pathri","Gangakhed","Ambajogai",
        "Majalgaon","Parli","Nilanga","Ausa","Udgir","Loha","Hadgaon","Kinwat","Pusad","Mehkar",
        "Chikhli","Deulgaon Raja","Lonar","Risod","Malegaon Camp","Ozar","Lasalgaon","Yeola",
        "Trimbak","Surgana","Dahanu","Jawhar","Talasari","Vikramgad","Mokhada","Khalapur",
        "Mhasla","Shrivardhan","Dapoli","Guhagar","Lanja","Rajapur","Deogad","Kankavli",
        "Kudal","Sawantwadi","Dodamarg","Vita","Khanapur","Islampur","Tasgaon","Miraj","Uran",
        "Murbad","Karjat","Ambegaon","Junnar","Rajgurunagar","Daund","Indapur","Karmala","Barshi",
        "Madha","Mohol","Malshiras","Akkalkot","Phaltan","Patan","Khatav","Koregaon","Man","Wai"
    ]

    # 관리자 전용 도시 추가
    if st.session_state.admin:
        with st.expander("도시 추가", expanded=False):
            st.markdown("#### 공연 도시 입력")
            selected_city = st.selectbox("도시 선택", CITIES, index=0)
            col1, col2 = st.columns([3, 1])
            with col1:
                venue_input = st.text_input(_["venue_name"])
            with col2:
                seat_count = st.number_input(_["seats"], value=0, step=50, min_value=0)
            google_link = st.text_input(_["google_link"])
            notes = st.text_area(_["special_notes"])
            indoor_outdoor = st.radio("형태", [_["indoor"], _["outdoor"]], horizontal=True)
            if st.button(_["register"], key="register_city_main"):
                if selected_city == "공연없음":
                    st.warning("도시를 선택해주세요.")
                elif not venue_input:
                    st.error(_["enter_venue_name"])
                else:
                    # 세션에 저장
                    if selected_city not in st.session_state.route:
                        st.session_state.route.append(selected_city)
                    if selected_city not in st.session_state.venues:
                        st.session_state.venues[selected_city] = []
                    st.session_state.venues[selected_city].append({
                        "Venue": venue_input,
                        "Seats": seat_count,
                        "Google Maps Link": google_link,
                        "Special Notes": notes,
                        "IndoorOutdoor": indoor_outdoor
                    })
                    st.success(_["venue_registered"])
                    st.rerun()

    # 투어 경로 표시
    st.subheader(_["tour_route"])
    for city in st.session_state.route:
        venues = st.session_state.venues.get(city, [])
        car_icon = ""
        if venues:
            link = venues[0]["Google Maps Link"]
            if link and link.startswith("http"):
                car_icon = f'<span style="float:right">[자동차]({link})</span>'
        with st.expander(f"**{city}**{car_icon}", expanded=False):
            if venues:
                for v in venues:
                    st.write(f"**{v['Venue']}**")
                    st.caption(f"{v['Seats']} {_['seats']} | {v.get('Special Notes','')} | {v['IndoorOutdoor']}")
                    if v["Google Maps Link"].startswith("http"):
                        st.markdown(f'<div style="text-align:right">[자동차]({v["Google Maps Link"]})</div>', unsafe_allow_html=True)

    # 지도
    st.subheader("Tour Map")
    if st.session_state.route:
        center = (19.75, 75.71)
        m = folium.Map(location=center, zoom_start=7, tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google")
        points = []
        for city in st.session_state.route:
            lat, lon = coords.get(city, center)
            points.append((lat, lon))
            popup = f"<b>{city}</b>"
            folium.CircleMarker(
                location=[lat, lon],
                radius=12,
                color="#90EE90",
                fill_color="#8B0000",
                popup=folium.Popup(popup, max_width=300)
            ).add_to(m)
        if len(points) > 1:
            folium.PolyLine(points, color="red", weight=4).add_to(m)
        st_folium(m, width=700, height=500)
    else:
        st.info("등록된 도시가 없습니다.")
