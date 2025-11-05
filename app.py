import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
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
        "seats": "좌석수",
        "note": "특이사항",
        "google_link": "구글맵 링크 입력",
        "indoor": "실내",
        "outdoor": "실외",
        "register": "등록",
        "edit": "수정",
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
        "date": datetime.now().strftime("%m/%d %H:%M"),
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
# 지도 + 도시 추가
# =============================================
def render_map():
    st.subheader(_["map_title"])

    if st.session_state.admin:
        with st.expander("➕ 도시 추가", expanded=False):
            cities_list = load_json("cities_list.json") if os.path.exists("cities_list.json") else ["공연없음"]
            city = st.selectbox(_["select_city"], cities_list)
            st.session_state.venue_input = st.text_input(_["venue"], st.session_state.venue_input)
            st.session_state.seat_count = st.number_input(_["seats"], min_value=0, step=50, value=st.session_state.seat_count)
            st.session_state.venue_type = st.radio("공연형태", [_["indoor"], _["outdoor"]], horizontal=True)
            st.session_state.map_link = st.text_input(_["google_link"], st.session_state.map_link)
            st.session_state.note_input = st.text_area(_["note"], st.session_state.note_input)

            if st.button(_["register"], key="register_city"):
                lat, lon = extract_latlon_from_shortlink(st.session_state.map_link)
                if not lat or not lon:
                    st.warning("⚠️ 올바른 구글맵 링크를 입력하세요.")
                    return
                nav_url = make_navigation_link(lat, lon)
                new_city = {
                    "city": city,
                    "venue": st.session_state.venue_input,
                    "seats": st.session_state.seat_count,
                    "type": st.session_state.venue_type,
                    "note": st.session_state.note_input,
                    "lat": lat,
                    "lon": lon,
                    "nav_url": nav_url,
                }
                data = load_json(CITY_FILE)
                data.append(new_city)
                save_json(CITY_FILE, data)
                st.toast("✅ 도시가 추가되었습니다.")
                st.rerun()

    # 지도 출력
    m = folium.Map(location=[19.0, 73.0], zoom_start=6)
    data = load_json(CITY_FILE)
    coords = []
    for c in data:
        lat, lon = c["lat"], c["lon"]
        popup_html = f"""
        <b>{c['city']}</b><br>
        장소: {c['venue']}<br>
        좌석수: {c['seats']}<br>
        형태: {c['type']}<br>
        <a href="{c['nav_url']}" target="_blank">🚗 길안내</a><br>
        특이사항: {c['note']}
        """
        folium.Marker([lat, lon], popup=popup_html, tooltip=c["city"], icon=folium.Icon(color="red", icon="music")).add_to(m)
        coords.append((lat, lon))
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
