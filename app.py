import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone
from streamlit_autorefresh import st_autorefresh

# 3초 새로고침 (일반 모드)
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh")

# 기본 설정
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 세션 초기화
defaults = {
    "admin": False,
    "lang": "ko",
    "edit_city": None,
    "expanded": {},
    "adding_cities": []
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 다국어 딕셔너리
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "caption": "마하라스트라 투어 관리 시스템",
        "tab_notice": "공지 관리",
        "tab_map": "투어 경로",
        "map_title": "경로 보기",
        "add": "추가",  # ← 여기 추가!
        "add_city": "도시 추가",  # ← 기존 버튼용
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
        "date": "등록일",
        "performance_date": "공연 날짜",
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
        "add": "Add",  # ← 추가
        "add_city": "Add City",
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
        "date": "Registered On",
        "performance_date": "Performance Date",
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
        "add": "जोड़ें",  # ← 추가
        "add_city": "शहर जोड़ें",
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
        "performance_date": "प्रदर्शन तिथि",
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

# 번역 함수
_ = lambda key: LANG[st.session_state.lang].get(key, key)

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
                href = f'<a href="data:file/octet-stream;base64,{base64.b64encode(open(n["file"], "rb").read()).decode()}" download="{os.path.basename(n["file"])}">{_("file_download")}</a>'
                st.markdown(href, unsafe_allow_html=True)
            if show_delete and st.button(_("remove"), key=f"del_{idx}"):
                data.pop(idx)
                save_json(NOTICE_FILE, data)
                st.session_state.expanded = {}
                st.toast("공지가 삭제되었습니다.")
                st.rerun()
        if st.session_state.expanded.get(key, False) != expanded:
            st.session_state.expanded[key] = expanded

# 지도 + 도시 관리
def render_map():
    col_title, col_btn = st.columns([6, 1])
    with col_title:
        st.subheader(_("map_title"))
    with col_btn:
        if st.session_state.admin:
            if st.button(_("add_city"), key="btn_add_city"):  # ← "도시 추가"
                st.session_state.adding_cities.append(None)
                st.rerun()

    cities_data = load_json(CITY_FILE)
    cities_data = sorted(cities_data, key=lambda x: x.get("perf_date", "9999-12-31"))

    if not os.path.exists(CITY_LIST_FILE):
        default_cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"]
        save_json(CITY_LIST_FILE, default_cities)
    cities_list = load_json(CITY_LIST_FILE)
    existing = {c["city"] for c in cities_data}
    available = [c for c in cities_list if c not in existing]

    # --- 동적 추가 폼 ---
    for i in range(len(st.session_state.adding_cities)):
        with st.container():
            col_sel, col_del = st.columns([8, 1])
            with col_sel:
                options = [None] + available
                current = st.session_state.adding_cities[i]
                idx = options.index(current) if current in options else 0
                city_name = st.selectbox(
                    _("select_city"),
                    options,
                    index=idx,
                    key=f"add_select_{i}"
                )
                st.session_state.adding_cities[i] = city_name
            with col_del:
                if st.button("×", key=f"remove_add_{i}"):
                    st.session_state.adding_cities.pop(i)
                    st.rerun()

            if city_name:
                venue = st.text_input(_("venue"), key=f"add_venue_{i}")
                seats = st.number_input(_("seats"), min_value=0, step=50, key=f"add_seats_{i}")
                perf_date = st.date_input(_("performance_date"), key=f"add_perf_date_{i}")
                venue_type = st.radio("공연형태", [_("indoor"), _("outdoor")], horizontal=True, key=f"add_type_{i}")
                map_link = st.text_input(_("google_link"), key=f"add_link_{i}")
                note = st.text_area(_("note"), key=f"add_note_{i}")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button(_("register"), key=f"reg_{i}"):
                        lat, lon = extract_latlon_from_shortlink(map_link) if map_link.strip() else (None, None)
                        if not lat or not lon:
                            coords = { "Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567), "Nagpur": (21.1458, 79.0882), "Nashik": (19.9975, 73.7898), "Aurangabad": (19.8762, 75.3433) }
                            lat, lon = coords.get(city_name, (19.0, 73.0))

                        new_city = {
                            "city": city_name,
                            "venue": venue or "미정",
                            "seats": seats,
                            "type": venue_type,
                            "perf_date": perf_date.strftime("%Y-%m-%d"),
                            "map_link": map_link,
                            "note": note or "없음",
                            "lat": lat,
                            "lon": lon,
                            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                        }
                        cities_data.append(new_city)
                        save_json(CITY_FILE, cities_data)
                        st.session_state.adding_cities.pop(i)
                        st.success(f"[{city_name}] 등록 완료!")
                        st.rerun()
                with c2:
                    if st.button(_("cancel"), key=f"cancel_{i}"):
                        st.session_state.adding_cities.pop(i)
                        st.rerun()

            st.markdown("---")

    # --- 기존 도시 목록 ---
    for idx, city in enumerate(cities_data):
        key = f"city_{idx}"
        expanded = st.session_state.expanded.get(key, False)
        with st.expander(f"{city['city']} | {city.get('perf_date', '')}", expanded=expanded):
            st.write(f"**{_('date')}:** {city.get('date', '')}")
            st.write(f"**{_('performance_date')}:** {city.get('perf_date', '')}")
            st.write(f"**{_('venue')}:** {city.get('venue', '')}")
            st.write(f"**{_('seats')}:** {city.get('seats', '')}")
            st.write(f"**{_('note')}:** {city.get('note', '')}")

            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(_("edit"), key=f"edit_{idx}"):
                        st.session_state.edit_city = city["city"]
                        st.rerun()
                with c2:
                    if st.button(_("remove"), key=f"del_{idx}"):
                        cities_data.pop(idx)
                        save_json(CITY_FILE, cities_data)
                        st.session_state.expanded = {}
                        st.toast("도시 삭제됨")
                        st.rerun()
        if st.session_state.expanded.get(key, False) != expanded:
            st.session_state.expanded[key] = expanded

    # --- 수정 모드 ---
    if st.session_state.edit_city:
        edit_city_obj = next((c for c in cities_data if c["city"] == st.session_state.edit_city), None)
        if not edit_city_obj:
            st.session_state.edit_city = None
            st.rerun()

        idx = next(i for i, c in enumerate(cities_data) if c["city"] == st.session_state.edit_city)

        st.markdown("### 도시 수정")
        venue = st.text_input(_("venue"), value=edit_city_obj.get("venue", ""), key="edit_venue")
        seats = st.number_input(_("seats"), min_value=0, step=50, value=edit_city_obj.get("seats", 0), key="edit_seats")
        perf_date = st.date_input(_("performance_date"), value=datetime.strptime(edit_city_obj.get("perf_date", "2025-01-01"), "%Y-%m-%d").date(), key="edit_perf_date")
        venue_type = st.radio("공연형태", [_("indoor"), _("outdoor")], index=0 if edit_city_obj.get("type") == _("indoor") else 1, horizontal=True, key="edit_type")
        map_link = st.text_input(_("google_link"), value=edit_city_obj.get("map_link", ""), key="edit_link")
        note = st.text_area(_("note"), value=edit_city_obj.get("note", ""), key="edit_note")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("수정 완료", key="edit_submit"):
                lat, lon = extract_latlon_from_shortlink(map_link) if map_link.strip() else (None, None)
                if not lat or not lon:
                    coords = { "Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567), "Nagpur": (21.1458, 79.0882), "Nashik": (19.9975, 73.7898), "Aurangabad": (19.8762, 75.3433) }
                    lat, lon = coords.get(edit_city_obj["city"], (19.0, 73.0))

                cities_data[idx].update({
                    "venue": venue or "미정",
                    "seats": seats,
                    "type": venue_type,
                    "perf_date": perf_date.strftime("%Y-%m-%d"),
                    "map_link": map_link,
                    "note": note or "없음",
                    "lat": lat,
                    "lon": lon,
                    "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                })
                save_json(CITY_FILE, cities_data)
                st.session_state.edit_city = None
                st.success(f"[{edit_city_obj['city']}] 수정 완료!")
                st.rerun()
        with c2:
            if st.button(_("cancel"), key="edit_cancel"):
                st.session_state.edit_city = None
                st.rerun()

    # --- 지도 ---
    st.markdown("---")
    m = folium.Map(location=[19.0, 73.0], zoom_start=6)
    coords = []
    today = datetime.now().date()

    # 당일 마커용 애니메이션 그룹
    bounce_group = folium.plugins.MarkerCluster().add_to(m)

    for c in cities_data:
        perf_date_str = c.get('perf_date')
        perf_date = datetime.strptime(perf_date_str, "%Y-%m-%d").date() if perf_date_str else None

        popup_html = f"""
        <b>{c['city']}</b><br>
        날짜: {c.get('perf_date','')}<br>
        장소: {c.get('venue','')}<br>
        인원: {c.get('seats','')}<br>
        형태: {c.get('type','')}<br>
        <a href="{c.get('map_link','#')}" target="_blank">길안내</a><br>
        특이사항: {c.get('note','')}
        """

        # 기본 아이콘
        icon = folium.Icon(color="red", icon="music")

        if perf_date:
            if perf_date < today:
                # 지난 날짜: 투명
                folium.Marker(
                    [c["lat"], c["lon"]], popup=popup_html, tooltip=c["city"],
                    icon=icon, opacity=0.4
                ).add_to(m)
            elif perf_date == today:
                # 당일: 위아래 움직임 (bounce)
                folium.Marker(
                    [c["lat"], c["lon"]], popup=popup_html, tooltip=c["city"],
                    icon=icon
                ).add_to(bounce_group)
            else:
                # 미래: 정상
                folium.Marker(
                    [c["lat"], c["lon"]], popup=popup_html, tooltip=c["city"],
                    icon=icon
                ).add_to(m)
        else:
            folium.Marker(
                [c["lat"], c["lon"]], popup=popup_html, tooltip=c["city"],
                icon=icon
            ).add_to(m)

        coords.append((c["lat"], c["lon"]))

    if coords:
        AntPath(coords, color="#ff1744", weight=5, delay=800, dash_array=[10, 20]).add_to(m)

    # 당일 마커 애니메이션 스크립트 추가
    bounce_js = """
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        setTimeout(function() {
            const markers = document.querySelectorAll('.leaflet-marker-icon');
            markers.forEach(marker => {
                if (marker.parentNode.parentNode.classList.contains('leaflet-cluster-anim')) return;
                let up = true;
                let pos = 0;
                setInterval(() => {
                    pos = up ? pos + 2 : pos - 2;
                    marker.style.transform = `translateY(${pos}px)`;
                    if (pos >= 10 || pos <= -10) up = !up;
                }, 50);
            });
        }, 1000);
    });
    </script>
    """
    m.get_root().html.add_child(folium.Element(bounce_js))

    st_folium(m, width=900, height=550)

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
        pw = st.text_input(_("password"), type="password")
        if st.button(_("login")):
            if pw == "0000":
                st.session_state.admin = True
                st.success("관리자 모드 ON")
                st.rerun()
            else:
                st.error(_("wrong_pw"))
    else:
        st.success("관리자 모드")
        if st.button(_("logout")):
            st.session_state.admin = False
            st.rerun()

# 메인 제목
st.markdown(f"# {_('title')} ")
st.caption(_("caption"))

# 탭 정의
tab1, tab2 = st.tabs([_("tab_notice"), _("tab_map")])

with tab1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_("title_label"))
            c = st.text_area(_("content_label"))
            img = st.file_uploader(_("upload_image"), type=["png", "jpg", "jpeg"])
            f = st.file_uploader(_("upload_file"))
            if st.form_submit_button(_("submit")):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_("warning"))
        render_notice_list(show_delete=True)
    else:
        render_notice_list(show_delete=False)
        if st.button("새로고침"):
            st.rerun()

with tab2:
    render_map()
