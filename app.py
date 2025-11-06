import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =============================================
# 세션 초기화
# =============================================
defaults = {
    "admin": False,
    "lang": "ko",
    "last_notice_count": 0,
    "venue_input": "",
    "seat_count": 0,
    "venue_type": "실내",
    "note_input": "",
    "map_link": "",
    "selected_city": None,
    "mode": None,  # None, 'add', 'edit'
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

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
        "file_download": "📎 파일 다운로드",
        "add_city": "도시 추가",
        "select_city": "도시 선택",
        "venue": "공연장소",
        "seats": "예상 인원",
        "note": "특이사항",
        "google_link": "구글맵 링크 입력",
        "indoor": "실내",
        "outdoor": "실외",
        "register": "등록",
        "edit": "수정",
        "remove": "제거",
        "date": "날짜",
        "city_list": "도시 목록",
        "no_city": "등록된 도시가 없습니다.",
    },
}
_ = LANG[st.session_state.lang]

# =============================================
# 유틸
# =============================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_latlon_from_shortlink(short_url):
    """maps.app.goo.gl → 실제 좌표 추출"""
    try:
        r = requests.get(short_url, allow_redirects=True, timeout=5)
        final_url = r.url
        match = re.search(r'@([0-9\.\-]+),([0-9\.\-]+)', final_url)
        if match:
            return float(match.group(1)), float(match.group(2))
    except:
        pass
    return None, None

def make_navigation_link(lat, lon):
    """OS별 네비게이션 링크 생성"""
    ua = st.session_state.get("user_agent", "")
    if "Android" in ua:
        return f"google.navigation:q={lat},{lon}"
    elif "iPhone" in ua or "iPad" in ua:
        return f"comgooglemaps://?daddr={lat},{lon}&directionsmode=driving"
    else:
        return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

# =============================================
# 공지 기능
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
        "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
        "image": img_path,
        "file": file_path
    }

    data = load_json(NOTICE_FILE)
    data.insert(0, new_notice)
    save_json(NOTICE_FILE, data)
    st.toast("✅ 공지가 등록되었습니다.")
    st.rerun()

def render_notice_list(show_delete=False):
    data = load_json(NOTICE_FILE)
    if not data:
        st.info(_["no_notice"])
        return
    for idx, n in enumerate(data):
        with st.expander(f"📅 {n['date']} | {n['title']}"):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                href = f'<a href="data:file/octet-stream;base64,{base64.b64encode(open(n["file"],"rb").read()).decode()}" download="{os.path.basename(n["file"])}">{_["file_download"]}</a>'
                st.markdown(href, unsafe_allow_html=True)
            if show_delete and st.button(_["delete"], key=f"del_{idx}"):
                data.remove(n)
                save_json(NOTICE_FILE, data)
                st.toast("🗑️ 공지가 삭제되었습니다.")
                st.rerun()

# =============================================
# 지도 + 도시 관리
# =============================================
def render_map():
    st.subheader(_["map_title"])

    # 항상 최신 데이터 로드
    cities_data = load_json(CITY_FILE)

    if st.session_state.admin:
        # 도시 목록 제목 + 플러스 버튼
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown("#### 🏙️ " + _["city_list"])
        with col2:
            if st.button("➕", key="add_city_btn"):
                st.session_state.mode = "add"
                st.session_state.selected_city = None
                st.session_state.venue_input = ""
                st.session_state.seat_count = 0
                st.session_state.venue_type = _["indoor"]
                st.session_state.note_input = ""
                st.session_state.map_link = ""
                st.rerun()

        # 새 도시 추가 모드일 때 입력 폼 표시
        if st.session_state.mode == "add":
            # cities_list.json 존재하지 않으면 기본 도시 생성
            if not os.path.exists(CITY_LIST_FILE):
                default_cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad",
                                  "Kolhapur", "Solapur", "Thane", "Ratnagiri", "Sangli"]
                save_json(CITY_LIST_FILE, default_cities)
            cities_list = load_json(CITY_LIST_FILE)

            city_name = st.selectbox(_["select_city"], cities_list, key="new_city_select")
            venue = st.text_input(_["venue"])
            seats = st.number_input(_["seats"], min_value=0, step=50)
            venue_type = st.radio("공연형태", [_["indoor"], _["outdoor"]], horizontal=True)
            map_link = st.text_input(_["google_link"])
            note = st.text_area(_["note"])

            c1, c2 = st.columns(2)
            with c1:
                if st.button(_["register"]):
                    lat, lon = extract_latlon_from_shortlink(map_link)
                    if not lat or not lon:
                        st.warning("⚠️ 올바른 구글맵 링크를 입력하세요.")
                    else:
                        nav_url = make_navigation_link(lat, lon)
                        new_city = {
                            "city": city_name,
                            "venue": venue,
                            "seats": seats,
                            "type": venue_type,
                            "note": note,
                            "lat": lat,
                            "lon": lon,
                            "nav_url": nav_url,
                            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                        }
                        cities_data.append(new_city)
                        save_json(CITY_FILE, cities_data)
                        st.session_state.mode = None
                        st.toast("✅ 도시가 추가되었습니다.")
                        st.rerun()
            with c2:
                if st.button("취소"):
                    st.session_state.mode = None
                    st.rerun()

    # 기존 도시 목록 expander로 표시 (관리자/일반 공통, 하지만 관리자만 버튼 있음)
    if not cities_data:
        st.info(_["no_city"])
    else:
        for idx, city in enumerate(cities_data):
            with st.expander(f"{city['city']}"):
                st.markdown(f"**{_['date']}:** {city.get('date', 'N/A')}")
                st.markdown(f"**{_['venue']}:** {city.get('venue', '')}")
                st.markdown(f"**{_['seats']}:** {city.get('seats', '')}")
                st.markdown(f"**{_['google_link']}:** {city.get('nav_url', '')}")
                st.markdown(f"**{_['note']}:** {city.get('note', '')}")

                if st.session_state.admin:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button(_["edit"], key=f"edit_{idx}"):
                            st.session_state.mode = "edit"
                            st.session_state.selected_city = city['city']
                            st.session_state.venue_input = city.get('venue', '')
                            st.session_state.seat_count = city.get('seats', 0)
                            st.session_state.venue_type = city.get('type', _["indoor"])
                            st.session_state.note_input = city.get('note', '')
                            st.session_state.map_link = city.get('nav_url', '')
                            st.rerun()
                    with c2:
                        if st.button(_["remove"], key=f"remove_{idx}"):
                            cities_data = [c for c in cities_data if c['city'] != city['city']]
                            save_json(CITY_FILE, cities_data)
                            st.toast("🗑️ 도시가 제거되었습니다.")
                            st.rerun()

        # 수정 모드일 때 입력 폼 표시 (expander 밖)
        if st.session_state.mode == "edit" and st.session_state.selected_city:
            selected_city_data = next((c for c in cities_data if c['city'] == st.session_state.selected_city), None)
            if selected_city_data:
                st.markdown("---")
                st.subheader(f"{st.session_state.selected_city} 수정")
                venue = st.text_input(_["venue"], value=st.session_state.venue_input)
                seats = st.number_input(_["seats"], min_value=0, step=50, value=st.session_state.seat_count)
                venue_type = st.radio("공연형태", [_["indoor"], _["outdoor"]], index=0 if st.session_state.venue_type == _["indoor"] else 1, horizontal=True)
                map_link = st.text_input(_["google_link"], value=st.session_state.map_link)
                note = st.text_area(_["note"], value=st.session_state.note_input)

                c1, c2 = st.columns(2)
                with c1:
                    if st.button(_["register"]):
                        lat, lon = extract_latlon_from_shortlink(map_link)
                        if not lat or not lon:
                            st.warning("⚠️ 올바른 구글맵 링크를 입력하세요.")
                        else:
                            nav_url = make_navigation_link(lat, lon)
                            updated_city = {
                                "city": st.session_state.selected_city,
                                "venue": venue,
                                "seats": seats,
                                "type": venue_type,
                                "note": note,
                                "lat": lat,
                                "lon": lon,
                                "nav_url": nav_url,
                                "date": selected_city_data['date']  # 기존 날짜 유지
                            }
                            for i, c in enumerate(cities_data):
                                if c['city'] == st.session_state.selected_city:
                                    cities_data[i] = updated_city
                                    break
                            save_json(CITY_FILE, cities_data)
                            st.session_state.mode = None
                            st.session_state.selected_city = None
                            st.toast("✏️ 도시가 수정되었습니다.")
                            st.rerun()
                with c2:
                    if st.button("취소"):
                        st.session_state.mode = None
                        st.session_state.selected_city = None
                        st.rerun()

    # 지도 출력 (관리자/일반 공통)
    st.markdown("---")
    m = folium.Map(location=[19.0, 73.0], zoom_start=6)
    coords = []
    for c in cities_data:
        if not all(k in c for k in ["city", "lat", "lon"]):
            continue
        popup_html = f"""
        <b>{c['city']}</b><br>
        장소: {c.get('venue', '')}<br>
        인원: {c.get('seats', '')}<br>
        형태: {c.get('type', '')}<br>
        <a href="{c.get('nav_url', '#')}" target="_blank">🚗 길안내</a><br>
        특이사항: {c.get('note', '')}
        """
        folium.Marker([c["lat"], c["lon"]], popup=popup_html, tooltip=c["city"],
                      icon=folium.Icon(color="red", icon="music")).add_to(m)
        coords.append((c["lat"], c["lon"]))
    if coords:
        AntPath(coords, color="#ff1744", weight=5, delay=800).add_to(m)
    st_folium(m, width=900, height=550)

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
        st.markdown("### 🔐 관리자 로그인")
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0000":
                st.session_state.admin = True
                st.success("✅ 관리자 모드 ON")
                st.rerun()
            else:
                st.error(_["wrong_pw"])
    else:
        st.success("✅ 관리자 모드")
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 메인
# =============================================
st.markdown(f"# {_['title']} 🎄")
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
        if st.button("🔄 새로고침"):
            st.rerun()

with tab2:
    render_map()
