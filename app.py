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
        "venue_registered": "등록 완료"
    },
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
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
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
from streamlit_autorefresh import st_autorefresh

if not st.session_state.admin:
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
    new_lang = st.selectbox("Language", ["ko"], index=0)
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

with tab2:
    # ----------------------------------------------------------------------
    # 도시/좌표 정의
    # ----------------------------------------------------------------------
    cols = ["Venue","Seats","Google Maps Link","Special Notes"]

    cities = sorted([
        "Mumbai","Pune","Nagpur","Nashik","Thane","Aurangabad","Solapur","Amravati","Nanded","Kolhapur",
        "Akola","Latur","Ahmadnagar","Jalgaon","Dhule","Ichalkaranji","Malegaon","Bhusawal","Bhiwandi","Bhandara",
        "Beed","Buldana","Chandrapur","Dharashiv","Gondia","Hingoli","Jalna","Mira-Bhayandar","Nandurbar","Osmanabad",
        "Palghar","Parbhani","Ratnagiri","Sangli","Satara","Sindhudurg","Wardha","Washim","Yavatmal","Kalyan-Dombivli",
        "Ulhasnagar","Vasai-Virar","Sangli-Miraj-Kupwad","Nanded-Waghala","Bandra (Mumbai)","Colaba (Mumbai)","Andheri (Mumbai)",
        "Boric Nagar (Mumbai)","Navi Mumbai","Mumbai Suburban","Pimpri-Chinchwad (Pune)","Koregaon Park (Pune)","Kothrud (Pune)",
        "Hadapsar (Pune)","Pune Cantonment","Nashik Road","Deolali (Nashik)","Satpur (Nashik)","Aurangabad City","Jalgaon City",
        "Bhopalwadi (Aurangabad)","Nagpur City","Sitabuldi (Nagpur)","Jaripatka (Nagpur)","Solapur City","Hotgi (Solapur)",
        "Pandharpur (Solapur)","Amravati City","Badnera (Amravati)","Paratwada (Amravati)","Akola City","Murtizapur (Akola)",
        "Washim City","Mangrulpir (Washim)","Yavatmal City","Pusad (Yavatmal)","Darwha (Yavatmal)","Wardha City",
        "Sindi (Wardha)","Hinganghat (Wardha)","Chandrapur City","Brahmapuri (Chandrapur)","Mul (Chandrapur)","Gadchiroli",
        "Aheri (Gadchiroli)","Dhanora (Gadchiroli)","Gondia City","Tiroda (Gondia)","Arjuni Morgaon (Gondia)",
        "Bhandara City","Pauni (Bhandara)","Tumsar (Bhandara)","Nagbhid (Chandrapur)","Gadhinglaj (Kolhapur)",
        "Kagal (Kolhapur)","Ajra (Kolhapur)","Shiroli (Kolhapur)",
    ])

    coords = {
        "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
        "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Amravati": (20.93, 77.75),
        "Nanded": (19.16, 77.31), "Kolhapur": (16.70, 74.24), "Akola": (20.70, 77.00), "Latur": (18.40, 76.57),
        "Ahmadnagar": (19.10, 74.75), "Jalgaon": (21.00, 75.57), "Dhule": (20.90, 74.77), "Ichalkaranji": (16.69, 74.47),
        "Malegaon": (20.55, 74.53), "Bhusawal": (21.05, 76.00), "Bhiwandi": (19.30, 73.06), "Bhandara": (21.17, 79.65),
        "Beed": (18.99, 75.76), "Buldana": (20.54, 76.18), "Chandrapur": (19.95, 79.30), "Dharashiv": (18.40, 76.57),
        "Gondia": (21.46, 80.19), "Hingoli": (19.72, 77.15), "Jalna": (19.85, 75.89), "Mira-Bhayandar": (19.28, 72.87),
        "Nandurbar": (21.37, 74.22), "Osmanabad": (18.18, 76.07), "Palghar": (19.70, 72.77), "Parbhani": (19.27, 76.77),
        "Ratnagiri": (16.99, 73.31), "Sangli": (16.85, 74.57), "Satara": (17.68, 74.02), "Sindhudurg": (16.24, 73.42),
        "Wardha": (20.75, 78.60), "Washim": (20.11, 77.13), "Yavatmal": (20.39, 78.12), "Kalyan-Dombivli": (19.24, 73.13),
        "Ulhasnagar": (19.22, 73.16), "Vasai-Virar": (19.37, 72.81), "Sangli-Miraj-Kupwad": (16.85, 74.57), "Nanded-Waghala": (19.16, 77.31),
        "Bandra (Mumbai)": (19.06, 72.84), "Colaba (Mumbai)": (18.92, 72.82), "Andheri (Mumbai)": (19.12, 72.84), "Boric Nagar (Mumbai)": (19.07, 72.88),
        "Navi Mumbai": (19.03, 73.00), "Mumbai Suburban": (19.07, 72.88), "Pimpri-Chinchwad (Pune)": (18.62, 73.80), "Koregaon Park (Pune)": (18.54, 73.90),
        "Kothrud (Pune)": (18.50, 73.81), "Hadapsar (Pune)": (18.51, 73.94), "Pune Cantonment": (18.50, 73.89), "Nashik Road": (20.00, 73.79),
        "Deolali (Nashik)": (19.94, 73.82), "Satpur (Nashik)": (20.01, 73.79), "Aurangabad City": (19.88, 75.34), "Jalgaon City": (21.00, 75.57),
        "Bhopalwadi (Aurangabad)": (19.88, 75.34), "Nagpur City": (21.15, 79.08), "Sitabuldi (Nagpur)": (21.14, 79.08), "Jaripatka (Nagpur)": (21.12, 79.07),
        "Solapur City": (17.67, 75.91), "Hotgi (Solapur)": (17.57, 75.95), "Pandharpur (Solapur)": (17.66, 75.32), "Amravati City": (20.93, 77.75),
        "Badnera (Amravati)": (20.84, 77.73), "Paratwada (Amravati)": (21.06, 77.21), "Akola City": (20.70, 77.00), "Murtizapur (Akola)": (20.73, 77.37),
        "Washim City": (20.11, 77.13), "Mangrulpir (Washim)": (20.31, 77.05), "Yavatmal City": (20.39, 78.12), "Pusad (Yavatmal)": (19.91, 77.57),
        "Darwha (Yavatmal)": (20.31, 77.78), "Wardha City": (20.75, 78.60), "Sindi (Wardha)": (20.82, 78.09), "Hinganghat (Wardha)": (20.58, 78.58),
        "Chandrapur City": (19.95, 79.30), "Brahmapuri (Chandrapur)": (20.61, 79.89), "Mul (Chandrapur)": (19.95, 79.06), "Gadchiroli": (20.09, 80.11),
        "Aheri (Gadchiroli)": (19.37, 80.18), "Dhanora (Gadchiroli)": (19.95, 80.15), "Gondia City": (21.46, 80.19), "Tiroda (Gondia)": (21.28, 79.68),
        "Arjuni Morgaon (Gondia)": (21.29, 80.20), "Bhandara City": (21.17, 79.65), "Pauni (Bhandara)": (21.07, 79.81), "Tumsar (Bhandara)": (21.37, 79.75),
        "Nagbhid (Chandrapur)": (20.29, 79.36), "Gadhinglaj (Kolhapur)": (16.23, 74.34), "Kagal (Kolhapur)": (16.57, 74.31), "Ajra (Kolhapur)": (16.67, 74.22),
        "Shiroli (Kolhapur)": (16.70, 74.24),
    }

    # ----------------------------------------------------------------------
    # 헬퍼
    # ----------------------------------------------------------------------
    def nav(url):
        return f"https://www.google.com/maps/dir/?api=1&destination={url}&travelmode=driving" if url and url.startswith("http") else ""

    # ----------------------------------------------------------------------
    # 도시 추가 (관리자 전용)
    # ----------------------------------------------------------------------
    if st.session_state.admin:
        st.markdown("### 도시 추가")
        avail = [c for c in cities if c not in st.session_state.route]
        if avail:
            c1, c2 = st.columns([3,1])
            with c1:
                next_city = st.selectbox(_["select_city"], ["공연없음"] + avail, index=0, key="next_city_select")
            with c2:
                if st.button(_["add_city_btn"], key="add_city_btn"):
                    if next_city != "공연없음":
                        st.session_state.route.append(next_city)
                    st.rerun()

    # ----------------------------------------------------------------------
    # 투어 경로 (접힌 박스)
    # ----------------------------------------------------------------------
    st.subheader(_["tour_route"])
    for city in st.session_state.route:
        t = st.session_state.venues
        has = city in t and not t.get(city, pd.DataFrame()).empty
        car_icon = ""
        if has:
            link = t[city].iloc[0]["Google Maps Link"]
            if link and link.startswith("http"):
                car_icon = f'<span style="float:right">[자동차]({nav(link)})</span>'
        with st.expander(f"**{city}**{car_icon}", expanded=False):
            if (st.session_state.admin or st.session_state.get("guest_mode")) and not has:
                st.markdown("---")
                col1, col2 = st.columns([3,1])
                with col1:
                    venue_name = st.text_input(_["venue_name"], key=f"v_{city}")
                with col2:
                    seats = st.number_input(_["seats"], 1, step=50, key=f"s_{city}")
                google_link = st.text_input(_["google_link"], placeholder="https://...", key=f"l_{city}")
                special_notes = st.text_area(_["special_notes"], key=f"sn_{city}")
                _, btn = st.columns([4,1])
                with btn:
                    if st.button(_["register"], key=f"reg_{city}"):
                        if not venue_name:
                            st.error(_["enter_venue_name"])
                        else:
                            new_row = pd.DataFrame([{
                                "Venue": venue_name,
                                "Seats": seats,
                                "Google Maps Link": google_link,
                                "Special Notes": special_notes
                            }])
                            t[city] = pd.concat([t.get(city, pd.DataFrame(columns=cols)), new_row], ignore_index=True)
                            st.success(_["venue_registered"])
                            for k in [f"v_{city}", f"s_{city}", f"l_{city}", f"sn_{city}"]:
                                st.session_state.pop(k, None)
                            st.rerun()

            if has:
                for idx, row in t[city].iterrows():
                    c1, c2, c3 = st.columns([3,1,1])
                    with c1:
                        st.write(f"**{row['Venue']}**")
                        st.caption(f"{row['Seats']} {_['seats']} | {row.get('Special Notes','')}")
                    with c3:
                        if row["Google Maps Link"].startswith("http"):
                            st.markdown(f'<div style="text-align:right">[자동차]({nav(row["Google Maps Link"])})</div>', unsafe_allow_html=True)

    # ----------------------------------------------------------------------
    # 지도 (Google Maps 스타일)
    # ----------------------------------------------------------------------
    st.subheader("Tour Map")
    center = coords.get(st.session_state.route[0] if st.session_state.route else "Mumbai", (19.75, 75.71))
    m = folium.Map(location=center, zoom_start=7, tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google")
    if len(st.session_state.route) > 1:
        points = [coords[c] for c in st.session_state.route]
        folium.PolyLine(points, color="red", weight=4).add_to(m)
    for city in st.session_state.route:
        df = st.session_state.venues.get(city, pd.DataFrame(columns=cols))
        link = next((r["Google Maps Link"] for _, r in df.iterrows() if r["Google Maps Link"].startswith("http")), None)
        popup_html = f"<b style='color:#8B0000'>{city}</b>"
        if link: popup_html = f'<a href="{nav(link)}" target="_blank" style="color:#90EE90">{popup_html}<br><i>{_["navigate"]}</i></a>'
        folium.CircleMarker(location=coords[city], radius=15, color="#90EE90", fill_color="#8B0000", popup=folium.Popup(popup_html, max_width=300)).add_to(m)
    st_folium(m, width=700, height=500)
