import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64

# =============================================
# 필수 패키지
# =============================================
# pip install streamlit-autorefresh

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
if "admin" not in st.session_state:
    st.session_state.admin = False
if "lang" not in st.session_state:
    st.session_state.lang = "ko"
if "last_notice_count" not in st.session_state:
    st.session_state.last_notice_count = 0
if "route" not in st.session_state:
    st.session_state.route = []
if "venues" not in st.session_state:
    st.session_state.venues = {}

# =============================================
# 다국어
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "caption": "마하라스트라 지역 투어 관리 시스템",
        "tab_notice_user": "공지 현황",
        "tab_notice_admin": "공지 관리",
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
# 자동 새로고침 (일반 모드에서만 5초)
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
    st_autorefresh(interval=5000, key="auto_refresh")
    new_count = len(load_json(NOTICE_FILE))
    if new_count > st.session_state.last_notice_count:
        st.toast("새 공지가 등록되었습니다!")
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

# 탭 이름 동적 변경
notice_tab_name = _["tab_notice_admin"] if st.session_state.admin else _["tab_notice_user"]
tab1, tab2 = st.tabs([notice_tab_name, _["tab_map"]])

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

# =============================================
# 투어 경로 탭
# =============================================
with tab2:
    # 도시 리스트
    CITIES = sorted([
        "Mumbai","Pune","Nagpur","Nashik","Thane","Aurangabad","Solapur","Kolhapur",
        "Amravati","Jalgaon","Akola","Latur","Ahmednagar","Dhule","Chandrapur","Parbhani",
        "Jalna","Bhusawal","Satara","Beed","Yavatmal","Gondia","Wardha","Nandurbar","Osmanabad",
        "Hingoli","Buldhana","Washim","Gadchiroli","Sangli","Ratnagiri","Sindhudurg","Nanded",
        "Palghar","Raigad","Baramati","Karad","Pandharpur","Malegaon","Ichalkaranji","Bhiwandi",
        "Ambarnath","Ulhasnagar","Panvel","Kalyan","Vasai","Virar","Mira-Bhayandar","Khopoli",
        "Alibag","Boisar","Dombivli","Badlapur","Talegaon","Chiplun","Mahad","Roha","Pen",
        "Murbad","Khed","Satana","Sinnar","Shirdi","Sangamner","Manmad","Shahada","Bodwad",
        "Raver","Malkapur","Nandura","Shegaon","Daryapur","Mangrulpir","Pusad","Umarkhed",
        "Wani","Ballarpur","Bhandara","Tumsar","Deoli","Selu","Pathri","Gangakhed","Ambajogai",
        "Majalgaon","Parli","Nilanga","Ausa","Udgir","Loha","Hadgaon","Kinwat","Mehkar",
        "Chikhli","Deulgaon Raja","Lonar","Risod","Malegaon Camp","Ozar","Lasalgaon","Yeola",
        "Trimbak","Surgana","Dahanu","Jawhar","Talasari","Vikramgad","Mokhada","Khalapur",
        "Mhasla","Shrivardhan","Dapoli","Guhagar","Lanja","Rajapur","Deogad","Kankavli",
        "Kudal","Sawantwadi","Dodamarg","Vita","Khanapur","Islampur","Tasgaon","Miraj","Uran",
        "Karjat","Ambegaon","Junnar","Rajgurunagar","Daund","Indapur","Karmala","Barshi",
        "Madha","Mohol","Malshiras","Akkalkot","Phaltan","Patan","Khatav","Koregaon","Man","Wai"
    ])

    # 좌표
    coords = {
        "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
        "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Kolhapur": (16.70, 74.24),
        "Amravati": (20.93, 77.75), "Jalgaon": (21.00, 75.57), "Akola": (20.70, 77.00), "Latur": (18.40, 76.57),
        "Ahmednagar": (19.10, 74.75), "Dhule": (20.90, 74.77), "Chandrapur": (19.95, 79.30), "Parbhani": (19.27, 76.77),
        "Jalna": (19.85, 75.89), "Bhusawal": (21.05, 76.00), "Satara": (17.68, 74.02), "Beed": (18.99, 75.76),
        "Yavatmal": (20.39, 78.12), "Gondia": (21.46, 80.19), "Wardha": (20.75, 78.60), "Nandurbar": (21.37, 74.22),
        "Osmanabad": (18.18, 76.07), "Hingoli": (19.72, 77.15), "Buldhana": (20.54, 76.18), "Washim": (20.11, 77.13),
        "Gadchiroli": (20.09, 80.11), "Sangli": (16.85, 74.57), "Ratnagiri": (16.99, 73.31), "Sindhudurg": (16.24, 73.42),
        "Nanded": (19.16, 77.31), "Palghar": (19.70, 72.77), "Raigad": (18.52, 73.33), "Baramati": (18.15, 74.46),
        "Karad": (17.28, 74.18), "Pandharpur": (17.67, 75.33), "Malegaon": (20.55, 74.53), "Ichalkaranji": (16.69, 74.46),
        "Bhiwandi": (19.30, 73.06), "Ambarnath": (19.21, 73.19), "Ulhasnagar": (19.22, 73.16), "Panvel": (18.99, 73.11),
        "Kalyan": (19.24, 73.13), "Vasai": (19.36, 72.81), "Virar": (19.46, 72.81), "Mira-Bhayandar": (19.28, 72.86),
        "Khopoli": (18.78, 73.34), "Alibag": (18.64, 72.87), "Boisar": (19.80, 72.75), "Dombivli": (19.21, 73.08),
        "Badlapur": (19.16, 73.27), "Talegaon": (18.72, 73.68), "Chiplun": (17.53, 73.52), "Mahad": (18.08, 73.42),
        "Roha": (18.44, 73.12), "Pen": (18.73, 73.10), "Murbad": (19.25, 73.39), "Khed": (17.72, 73.38),
        "Satana": (20.59, 74.20), "Sinnar": (19.85, 74.00), "Shirdi": (19.76, 74.47), "Sangamner": (19.57, 74.21),
        "Manmad": (20.25, 74.43), "Shahada": (21.54, 74.47), "Bodwad": (20.90, 76.21), "Raver": (21.24, 76.03),
        "Malkapur": (20.88, 76.20), "Nandura": (20.83, 76.45), "Shegaon": (20.79, 76.69), "Daryapur": (20.92, 77.33),
        "Mangrulpir": (20.31, 77.34), "Pusad": (19.91, 77.57), "Umarkhed": (19.66, 77.68), "Wani": (20.05, 78.95),
        "Ballarpur": (19.85, 79.35), "Bhandara": (21.17, 79.65), "Tumsar": (21.38, 79.73), "Deoli": (20.65, 78.48),
        "Selu": (19.45, 76.45), "Pathri": (19.26, 76.43), "Gangakhed": (18.97, 76.76), "Ambajogai": (18.73, 76.38),
        "Majalgaon": (19.15, 76.21), "Parli": (18.85, 76.53), "Nilanga": (18.13, 76.75), "Ausa": (18.25, 76.50),
        "Udgir": (18.39, 77.11), "Loha": (18.95, 77.13), "Hadgaon": (19.49, 77.66), "Kinwat": (19.62, 78.20),
        "Mehkar": (20.15, 76.57), "Chikhli": (20.35, 76.25), "Deulgaon Raja": (20.02, 76.03), "Lonar": (19.98, 76.52),
        "Risod": (19.97, 76.78), "Malegaon Camp": (20.55, 74.53), "Ozar": (20.09, 73.92), "Lasalgaon": (20.15, 74.24),
        "Yeola": (20.04, 74.48), "Trimbak": (19.93, 73.53), "Surgana": (20.56, 73.62), "Dahanu": (19.98, 72.73),
        "Jawhar": (19.91, 73.23), "Talasari": (20.27, 72.91), "Vikramgad": (19.78, 72.97), "Mokhada": (19.93, 73.35),
        "Khalapur": (18.83, 73.28), "Mhasla": (18.13, 73.11), "Shrivardhan": (18.05, 73.02), "Dapoli": (17.77, 73.19),
        "Guhagar": (17.48, 73.19), "Lanja": (16.86, 73.55), "Rajapur": (16.66, 73.52), "Deogad": (16.52, 73.38),
        "Kankavli": (16.27, 73.70), "Kudal": (16.01, 73.68), "Sawantwadi": (15.90, 73.82), "Dodamarg": (15.75, 74.08),
        "Vita": (17.27, 74.53), "Khanapur": (17.20, 74.70), "Islampur": (17.05, 74.26), "Tasgaon": (17.03, 74.60),
        "Miraj": (16.82, 74.63), "Uran": (18.88, 72.95), "Karjat": (18.91, 73.33), "Ambegaon": (19.12, 73.73),
        "Junnar": (19.21, 73.87), "Rajgurunagar": (18.86, 73.89), "Daund": (18.46, 74.58), "Indapur": (18.30, 75.03),
        "Karmala": (18.40, 75.19), "Barshi": (18.23, 75.69), "Madha": (18.03, 75.51), "Mohol": (17.81, 75.65),
        "Malshiras": (17.50, 74.88), "Akkalkot": (17.52, 76.20), "Phaltan": (17.99, 74.43), "Patan": (17.37, 73.90),
        "Khatav": (17.66, 74.36), "Koregaon": (17.70, 74.17), "Man": (18.15, 74.44), "Wai": (17.95, 73.89)
    }

    # 관리자 전용 도시 추가 (입력창 깨끗하게!)
    if st.session_state.admin:
        with st.expander("도시 추가", expanded=False):
            st.markdown("#### 공연 도시 입력")
            selected_city = st.selectbox("도시 선택", CITIES, index=0)
            col1, col2 = st.columns([3, 1])
            with col1:
                venue_input = st.text_input(_["venue_name"], value="")
            with col2:
                seat_count = st.number_input(_["seats"], value=0, step=50, min_value=0)
            google_link = st.text_input(_["google_link"], value="")
            notes = st.text_area(_["special_notes"], value="")
            indoor_outdoor = st.radio("형태", [_["indoor"], _["outdoor"]], horizontal=True)
            if st.button(_["register"], key="register_city_main"):
                if not venue_input:
                    st.error(_["enter_venue_name"])
                else:
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

    # 지도 (항상 표시)
    st.subheader("Tour Map")
    center = (19.75, 75.71)
    m = folium.Map(location=center, zoom_start=7, tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google")
    points = []
    for city in st.session_state.route:
        lat, lon = coords.get(city, center)
        points.append((lat, lon))
        venues = st.session_state.venues.get(city, [])
        popup_lines = []
        for v in venues:
            line = f"<b>{v['Venue']}</b><br>{v['Seats']}석 | {v['IndoorOutdoor']}"
            if v.get('Special Notes'):
                line += f"<br>{v['Special Notes']}"
            if v["Google Maps Link"].startswith("http"):
                line += f"<br><a href='{v['Google Maps Link']}' target='_blank'>자동차 구글맵</a>"
            popup_lines.append(line + "<hr>")
        popup_html = "<br>".join(popup_lines) if popup_lines else f"<b>{city}</b>"
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=450),
            tooltip=None,
            icon=folium.Icon(icon="map-marker", prefix="fa", color="red")
        ).add_to(m)
    if len(points) > 1:
        AntPath(points, color="#ff1744", weight=5, delay=1000, dash_array=[10, 20]).add_to(m)
    st_folium(m, width=700, height=500)
