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
        "venue_registered": "등록 완료",
        "indoor": "실내",
        "outdoor": "실외"
    },
    "en": { ... },  # 생략 (필요시 추가)
    "hi": { ... }   # 생략 (필요시 추가)
}

_ = LANG[st.session_state.lang]

# =============================================
# 도시/좌표 정의 (NameError 해결)
# =============================================
coords = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
    "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Amravati": (20.93, 77.75),
    "Nanded": (19.16, 77.31), "Kolhapur": (16.70, 74.24), "Akola": (20.70, 77.00), "Latur": (18.40, 76.57),
    "Ahmednagar": (19.10, 74.75), "Jalgaon": (21.00, 75.57), "Dhule": (20.90, 74.77), "Ichalkaranji": (16.69, 74.47),
    "Malegaon": (20.55, 74.53), "Bhusawal": (21.05, 76.00), "Bhiwandi": (19.30, 73.06), "Bhandara": (21.17, 79.65),
    "Beed": (18.99, 75.76), "Buldhana": (20.54, 76.18), "Chandrapur": (19.95, 79.30), "Osmanabad": (18.18, 76.07),
    "Gondia": (21.46, 80.19), "Hingoli": (19.72, 77.15), "Jalna": (19.85, 75.89), "Mira-Bhayandar": (19.28, 72.87),
    "Nandurbar": (21.37, 74.22), "Palghar": (19.70, 72.77), "Parbhani": (19.27, 76.77), "Ratnagiri": (16.99, 73.31),
    "Sangli": (16.85, 74.57), "Satara": (17.68, 74.02), "Sindhudurg": (16.24, 73.42), "Wardha": (20.75, 78.60),
    "Washim": (20.11, 77.13), "Yavatmal": (20.39, 78.12), "Kalyan-Dombivli": (19.24, 73.13), "Ulhasnagar": (19.22, 73.16),
    "Vasai-Virar": (19.37, 72.81), "Sangli-Miraj-Kupwad": (16.85, 74.57), "Nanded-Waghala": (19.16, 77.31)
}

# =============================================
# 사이드바 + 로그인
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

    # 지도 (툴팁 제거 + 말풍선 넓게)
    st.subheader("Tour Map")
    if st.session_state.route:
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
            popup_html = "<br>".join(popup_lines)
            folium.CircleMarker(
                location=[lat, lon],
                radius=12,
                color="#90EE90",
                fill_color="#8B0000",
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=None  # 툴팁 제거
            ).add_to(m)
        if len(points) > 1:
            folium.PolyLine(points, color="red", weight=4).add_to(m)
        st_folium(m, width=700, height=500)
    else:
        st.info("등록된 도시가 없습니다.")
