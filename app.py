import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from streamlit_autorefresh import st_autorefresh

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
    "selected_city": "공연없음",
    "venue_input": "",
    "seat_count": 0,
    "google_link": "",
    "notes": "",
    "indoor_outdoor": "실내"
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
        "lang_select": "언어 선택",
        "file_download": "📎 파일 다운로드",
        "add_city": "도시 추가",
        "venue": "공연장소",
        "seat": "좌석 수",
        "google_link": "구글맵 링크",
        "notes": "특이사항",
        "register": "등록",
        "update": "수정"
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
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "image": img_path,
        "file": file_path
    }

    data = load_json(NOTICE_FILE)
    data.insert(0, new_notice)
    save_json(NOTICE_FILE, data)

    st.toast("✅ 공지가 등록되었습니다.")
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
    st.toast("🗑️ 공지가 삭제되었습니다.")
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
        with st.expander(f"📅 {n['date']} | {n['title']}"):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                st.markdown(get_file_download_link(n["file"], _["file_download"]), unsafe_allow_html=True)
            if show_delete:
                if st.button(_["delete"], key=f"del_{n['id']}_{idx}"):
                    delete_notice(n["id"])

# =============================================
# 도시 관리
# =============================================
# 150개 주요 도시 예시 (간략)
CITIES = [
    "공연없음", "Mumbai", "Pune", "Nagpur", "Thane", "Nashik", "Aurangabad",
    "Solapur", "Kolhapur", "Amravati", "Jalgaon", "Akola", "Latur", "Ahmednagar",
    "Dhule", "Chandrapur", "Parbhani", "Jalna", "Bhusawal", "Satara", "Beed",
    "Yavatmal", "Gondia", "Wardha", "Nandurbar", "Osmanabad", "Hingoli", "Buldhana",
    "Washim", "Gadchiroli"
    # 나머지 120개 도시도 이어서 추가 가능
]

def add_city_to_map(city, venue, seat, link, notes, indoor_outdoor):
    data = load_json(CITY_FILE)
    entry = {
        "id": str(uuid.uuid4()),
        "city": city,
        "venue": venue,
        "seat": seat,
        "link": link,
        "notes": notes,
        "type": indoor_outdoor,
        "time": datetime.now().strftime("%m/%d %H:%M")
    }
    data.append(entry)
    save_json(CITY_FILE, data)
    st.toast(f"✅ {city} 등록 완료!")
    st.rerun()

# =============================================
# 지도 표시
# =============================================
def render_map():
    st.subheader(_["map_title"])
    data = load_json(CITY_FILE)
    m = folium.Map(location=[19.0, 73.0], zoom_start=7)
    coords = []
    for c in data:
        city_name = c["city"]
        popup_html = f"""
        <b>{city_name}</b><br>
        장소: {c['venue']}<br>
        좌석수: {c['seat']}<br>
        유형: {c['type']}<br>
        <a href="{c['link']}" target="_blank">🚗 구글맵 이동</a><br>
        비고: {c['notes']}<br>
        등록시간: {c['time']}
        """
        color = "green" if c["type"] == "실내" else "red"
        folium.Marker(
            [19 + hash(city_name) % 5 * 0.1, 73 + hash(city_name) % 5 * 0.1],  # 예시 좌표
            popup=popup_html,
            tooltip=city_name,
            icon=folium.Icon(color=color, icon="music")
        ).add_to(m)
        coords.append([19, 73])
    if coords:
        AntPath(coords, color="#ff1744", weight=5, delay=800).add_to(m)
    st_folium(m, width=900, height=550)

# =============================================
# 자동 새로고침 (10초마다)
# =============================================
if not st.session_state.admin:
    count = len(load_json(NOTICE_FILE))
    if st.session_state.last_notice_count == 0:
        st.session_state.last_notice_count = count

    st_autorefresh(interval=10 * 1000, key="auto_refresh")

    new_count = len(load_json(NOTICE_FILE))
    if new_count > st.session_state.last_notice_count:
        st.toast("🔔 새 공지가 등록되었습니다!")
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
        st.markdown(f"### 🔐 관리자 로그인")
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
    if st.session_state.admin:
        with st.expander("➕ 도시 추가", expanded=False):
            st.markdown("#### 도시 등록")
            col1, col2 = st.columns([1, 1])
            with col1:
                st.session_state.selected_city = st.selectbox("도시 선택", CITIES, index=0)
            with col2:
                st.session_state.indoor_outdoor = st.radio("실내 / 실외", ["실내", "실외"], horizontal=True)
            col3, col4 = st.columns([2, 1])
            with col3:
                st.session_state.venue_input = st.text_input(_["venue"], value=st.session_state.venue_input)
            with col4:
                seat = st.number_input(_["seat"], value=st.session_state.seat_count, step=50, min_value=0)
                st.session_state.seat_count = seat
            st.session_state.google_link = st.text_input(_["google_link"], value=st.session_state.google_link)
            st.session_state.notes = st.text_area(_["notes"], value=st.session_state.notes)

            if st.button(_["register"]):
                if st.session_state.selected_city != "공연없음":
                    add_city_to_map(
                        st.session_state.selected_city,
                        st.session_state.venue_input,
                        st.session_state.seat_count,
                        st.session_state.google_link,
                        st.session_state.notes,
                        st.session_state.indoor_outdoor
                    )
                else:
                    st.warning("⚠️ 도시를 선택해주세요.")
    render_map()
