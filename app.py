import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, requests, re

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
if "temp_seats" not in st.session_state:
    st.session_state.temp_seats = 0

# =============================================
# 다국어
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "caption": "마하라스트라",
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
# 구글맵 단축링크 → 좌표 + 네비 링크 추출 함수
# =============================================
def extract_latlon_from_shortlink(short_url):
    try:
        r = requests.get(short_url, allow_redirects=True, timeout=5)
        final_url = r.url
        match = re.search(r'@([0-9\.\-]+),([0-9\.\-]+)', final_url)
        if match:
            lat, lon = match.groups()
            nav_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
            return lat, lon, nav_url
        return None, None, None
    except:
        return None, None, None

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
# 메인 UI
# =============================================
st.markdown(f"# {_['title']}")
st.caption(_["caption"])

notice_tab_name = _["tab_notice_admin"] if st.session_state.admin else _["tab_notice_user"]
tab1, tab2 = st.tabs([notice_tab_name, _["tab_map"]])

# ---------------------------------------------
# 공지 탭
# ---------------------------------------------
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

# ---------------------------------------------
# 지도 탭
# ---------------------------------------------
with tab2:
    st.subheader(_["tour_route"])

    # 관리자: 도시 추가
    if st.session_state.admin:
        with st.expander("도시 추가", expanded=False):
            selected_city = st.text_input("도시명 입력")
            col1, col2 = st.columns([3, 1])
            with col1:
                venue_input = st.text_input(_["venue_name"], value="")
            with col2:
                col_plus, col_minus, col_display = st.columns([1, 1, 2])
                with col_plus:
                    if st.button("+50"):
                        st.session_state.temp_seats += 50
                        st.rerun()
                with col_minus:
                    if st.button("-50"):
                        st.session_state.temp_seats = max(0, st.session_state.temp_seats - 50)
                        st.rerun()
                with col_display:
                    st.write(f"**{st.session_state.temp_seats}**")

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
                    # 단축 링크 변환
                    lat, lon, nav_url = None, None, None
                    if google_link.startswith("http"):
                        lat, lon, nav_url = extract_latlon_from_shortlink(google_link)
                    st.session_state.venues[selected_city].append({
                        "Venue": venue_input,
                        "Seats": st.session_state.temp_seats,
                        "Google Maps Link": nav_url or google_link,
                        "Special Notes": notes,
                        "IndoorOutdoor": indoor_outdoor
                    })
                    st.success(_["venue_registered"])
                    st.session_state.temp_seats = 0
                    st.rerun()

    # 지도 표시
    st.subheader("Tour Map")
    center = (19.75, 75.71)
    m = folium.Map(location=center, zoom_start=7)
    points = []
    for city in st.session_state.route:
        venues = st.session_state.venues.get(city, [])
        popup_lines = []
        for v in venues:
            link_html = ""
            if v["Google Maps Link"].startswith("http"):
                link_html = f"<a href='{v['Google Maps Link']}' target='_blank'>길찾기</a>"
            popup_lines.append(f"<div style='text-align:center; font-size:1.1em;'><b>{v['Venue']}</b><br>{v['Seats']}석 | {v['IndoorOutdoor']}<br>{v.get('Special Notes','')}<br>{link_html}</div>")
        popup_html = "<br>".join(popup_lines)
        folium.Marker(
            location=center,
            popup=folium.Popup(popup_html, max_width=850),
            tooltip=city,
            icon=folium.Icon(icon="map-marker", color="red")
        ).add_to(m)
    st_folium(m, width=700, height=500)
