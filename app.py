import streamlit as st
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
        "file_download": "📎 파일 다운로드",
        "add_city": "도시 추가",
        "select_city": "도시 선택",
        "venue_name": "공연장 이름",
        "seats": "좌석 수",
        "google_link": "구글 지도 링크",
        "special_notes": "특이사항",
        "register": "등록",
        "navigate": "길찾기",
        "enter_venue_name": "공연장 이름을 입력하세요."
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
# 지도
# =============================================
def render_map():
    st.subheader(_["map_title"])
    cities = [
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Nashik", "lat": 19.9975, "lon": 73.7898},
    ]
    m = folium.Map(location=[19.0, 73.0], zoom_start=7)
    coords = [(c["lat"], c["lon"]) for c in cities]
    for c in cities:
        folium.Marker([c["lat"], c["lon"]], popup=c["name"], tooltip=c["name"],
                      icon=folium.Icon(color="red", icon="music")).add_to(m)
    AntPath(coords, color="#ff1744", weight=5, delay=800).add_to(m)
    st_folium(m, width=900, height=550)

# =============================================
# 자동 새로고침 (10초마다)
# =============================================
from streamlit_autorefresh import st_autorefresh

if not st.session_state.admin:
    count = len(load_json(NOTICE_FILE))
    if st.session_state.last_notice_count == 0:
        st.session_state.last_notice_count = count

    # 10초마다 새로고침
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
    render_map()

# ----------------------------------------------------------------------
# 6. 도시 추가 (관리자 모드에서만)
# ----------------------------------------------------------------------
if st.session_state.admin:
    st.markdown("### 도시 추가")
    avail = [c for c in cities if c not in st.session_state.route]
    if avail:
        c1, c2 = st.columns([3,1])
        with c1:
            next_city = st.selectbox(_["select_city"], avail + ["공연없음"], index=len(avail), key="next_city_select")
        with c2:
            if st.button(_["add_city_btn"], key="add_city_btn"):
                st.session_state.route.append(next_city)
                st.rerun()

# ----------------------------------------------------------------------
# 7. 투어 경로 (박스 추가)
# ----------------------------------------------------------------------
st.subheader(_["tour_route"])
for city in st.session_state.route:
    t = st.session_state.venues
    has = city in t and not t.get(city, pd.DataFrame()).empty
    car_icon = ""
    if has:
        link = t[city].iloc[0]["Google Maps Link"]
        if link and link.startswith("http"):
            car_icon = f'<span style="float:right">[🚗]({nav(link)})</span>'
    with st.expander(f"**{city}**{car_icon}", expanded=False):
        # 등록 폼
        if (st.session_state.admin or st.session_state.get("guest_mode")) and not has:
            st.markdown("---")
            venue_name = st.text_input(_["venue_name"], key=f"v_{city}")
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

        # 등록된 공연장
        if has:
            for idx, row in t[city].iterrows():
                c1, c2, c3 = st.columns([3,1,1])
                with c1:
                    st.write(f"**{row['Venue']}**")
                    st.caption(f"{row['Seats']} {_['seats']} | {row.get('Special Notes','')}")
                with c3:
                    if row["Google Maps Link"].startswith("http"):
                        st.markdown(f'<div style="text-align:right">[🚗]({nav(row["Google Maps Link"])})</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 9. 오른쪽 컬럼 – 지도
# ----------------------------------------------------------------------
with right:
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
