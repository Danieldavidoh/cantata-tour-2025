# app.py
import streamlit as st
from datetime import datetime, date
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
    "edit_index": None,  # 수정 모드 인덱스
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =============================================
# 뭄바이 기준 현재시간 (년도 제외)
# =============================================
india_time = datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
st.markdown(f"<p style='text-align:right;color:gray;font-size:0.9rem;'>🕓 {india_time} (Mumbai)</p>", unsafe_allow_html=True)

# =============================================
# 다국어 (ko, en, hi)
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
        "file_download": "파일 다운로드",
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
        "city": "도시",
        "date": "날짜",
        "tour_list": "추가된 투어 일정",
        "no_tour": "아직 추가된 투어가 없습니다.",
        "save": "저장",
    },
    "en": {
        "title": "Cantata Tour 2025",
        "caption": "Maharashtra Tour Management System",
        "tab_notice": "Notices",
        "tab_map": "Tour Route",
        "add_notice": "Add New Notice",
        "title_label": "Title",
        "content_label": "Content",
        "upload_image": "Upload Image (Optional)",
        "upload_file": "Upload File (Optional)",
        "submit": "Submit",
        "warning": "Please enter both title and content.",
        "notice_list": "Notice List",
        "no_notice": "No notices registered.",
        "delete": "Delete",
        "map_title": "View Route",
        "admin_login": "Admin Login",
        "password": "Password",
        "login": "Login",
        "logout": "Logout",
        "wrong_pw": "Incorrect password.",
        "file_download": "Download File",
        "add_city": "Add City",
        "select_city": "Select City",
        "venue": "Venue",
        "seats": "Seats",
        "note": "Notes",
        "google_link": "Enter Google Maps Link",
        "indoor": "Indoor",
        "outdoor": "Outdoor",
        "register": "Register",
        "edit": "Edit",
        "city": "City",
        "date": "Date",
        "tour_list": "Added Tour Schedule",
        "no_tour": "No tour added yet.",
        "save": "Save",
    },
    "hi": {
        "title": "कांताता टूर 2025",
        "caption": "महाराष्ट्र क्षेत्र टूर प्रबंधन प्रणाली",
        "tab_notice": "सूचनाएँ",
        "tab_map": "टूर मार्ग",
        "add_notice": "नई सूचना जोड़ें",
        "title_label": "शीर्षक",
        "content_label": "सामग्री",
        "upload_image": "छवि अपलोड करें (वैकल्पिक)",
        "upload_file": "फ़ाइल अपलोड करें (वैकल्पिक)",
        "submit": "जमा करें",
        "warning": "कृपया शीर्षक और सामग्री दोनों दर्ज करें।",
        "notice_list": "सूचना सूची",
        "no_notice": "कोई सूचना पंजीकृत नहीं है।",
        "delete": "हटाएं",
        "map_title": "मार्ग देखें",
        "admin_login": "प्रशासक लॉगिन",
        "password": "पासवर्ड",
        "login": "लॉगिन",
        "logout": "लॉगआउट",
        "wrong_pw": "गलत पासवर्ड।",
        "file_download": "फ़ाइल डाउनलोड",
        "add_city": "शहर जोड़ें",
        "select_city": "शहर चुनें",
        "venue": "स्थल",
        "seats": "सीटें",
        "note": "टिप्पणियाँ",
        "google_link": "गूगल मैप लिंक दर्ज करें",
        "indoor": "इनडोर",
        "outdoor": "आउटडोर",
        "register": "पंजीकृत करें",
        "edit": "संपादित करें",
        "city": "शहर",
        "date": "तारीख",
        "tour_list": "जोड़ा गया टूर शेड्यूल",
        "no_tour": "अभी तक कोई टूर नहीं जोड़ा गया।",
        "save": "सहेजें",
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
    ua = st.context.headers.get("User-Agent", "") if hasattr(st, "context") else ""
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
    st.toast("공지가 등록되었습니다.")
    st.rerun()

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
                with open(n["file"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(n["file"])}">{_["file_download"]}</a>'
                st.markdown(href, unsafe_allow_html=True)
            if show_delete and st.button(_["delete"], key=f"del_{idx}"):
                data.remove(n)
                save_json(NOTICE_FILE, data)
                st.toast("공지가 삭제되었습니다.")
                st.rerun()

# =============================================
# 지도 + 도시 추가 (완전 교체)
# =============================================
def render_map():
    st.subheader(_["map_title"])

    if st.session_state.admin:
        # === 도시 추가/수정 폼 ===
        with st.expander("도시 추가 / 수정", expanded=True):
            # 도시 목록 로드
            if not os.path.exists(CITY_LIST_FILE):
                default_cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Kolhapur", "Solapur", "Thane", "Ratnagiri", "Sangli"]
                save_json(CITY_LIST_FILE, default_cities)
            cities_list = load_json(CITY_LIST_FILE)

            # 수정 모드: 기존 데이터 로드
            edit_idx = st.session_state.get("edit_index")
            edit_data = None
            if edit_idx is not None:
                data = load_json(CITY_FILE)
                if 0 <= edit_idx < len(data):
                    edit_data = data[edit_idx]

            # 도시 선택
            city_options = cities_list + ["새 도시 입력..."]
            default_city = edit_data["city"] if edit_data else city_options[0]
            selected_city = st.selectbox(_["select_city"], city_options, index=city_options.index(default_city) if default_city in city_options else 0)

            # 신규 도시 입력
            if selected_city == "새 도시 입력...":
                city = st.text_input("새 도시 이름", value=edit_data["city"] if edit_data else "")
            else:
                city = selected_city

            # 날짜 (달력)
            default_date = datetime.strptime(edit_data["date"], "%Y-%m-%d").date() if edit_data and "date" in edit_data else date.today()
            tour_date = st.date_input(_["date"], value=default_date)

            # 공연장소, 좌석수, 형태
            venue = st.text_input(_["venue"], value=edit_data["venue"] if edit_data else "")
            seats = st.number_input(_["seats"], min_value=0, step=50, value=edit_data["seats"] if edit_data else 0)
            venue_type = st.radio("공연형태", [_["indoor"], _["outdoor"]], horizontal=True,
                                  index=0 if (edit_data and edit_data["type"] == _["indoor"]) else 1)

            # 구글맵 링크
            map_link = st.text_input(_["google_link"], value=edit_data.get("map_link", "") if edit_data else "")

            # 특이사항
            note = st.text_area(_["note"], value=edit_data["note"] if edit_data else "")

            # 등록 / 저장 버튼
            if st.button(_["save"] if edit_idx is not None else _["register"]):
                if not city.strip():
                    st.warning("도시 이름을 입력하세요.")
                    return
                lat, lon = extract_latlon_from_shortlink(map_link)
                if not lat or not lon:
                    st.warning("올바른 구글맵 링크를 입력하세요.")
                    return

                nav_url = make_navigation_link(lat, lon)
                new_entry = {
                    "city": city,
                    "date": tour_date.strftime("%Y-%m-%d"),
                    "venue": venue,
                    "seats": seats,
                    "type": venue_type,
                    "note": note,
                    "lat": lat,
                    "lon": lon,
                    "nav_url": nav_url,
                }

                data = load_json(CITY_FILE)
                if edit_idx is not None:
                    data[edit_idx] = new_entry
                    st.session_state.edit_index = None
                    st.toast("수정 완료!")
                else:
                    data.append(new_entry)
                    st.toast("도시 추가 완료!")

                # 날짜순 정렬
                data.sort(key=lambda x: x["date"])

                # 신규 도시면 목록에 추가
                if city not in cities_list:
                    cities_list.append(city)
                    save_json(CITY_LIST_FILE, cities_list)

                save_json(CITY_FILE, data)
                st.rerun()

        # === 추가된 투어 일정 리스트 ===
        st.subheader(_["tour_list"])
        data = load_json(CITY_FILE)
        if not data:
            st.info(_["no_tour"])
        else:
            for idx, c in enumerate(data):
                with st.expander(f"{c['city']} | {c['date']} | {c['venue']} | {c['seats']}명 | {c['type']}"):
                    st.markdown(f"**길안내**: [{c['nav_url']}]({c['nav_url']})")
                    st.markdown(f"**특이사항**: {c['note']}")
                    col1, col2 = st.columns(2)
                    if col1.button("수정", key=f"edit_{idx}"):
                        st.session_state.edit_index = idx
                        st.rerun()
                    if col2.button("제거", key=f"del_{idx}"):
                        data.pop(idx)
                        save_json(CITY_FILE, data)
                        st.toast("제거 완료!")
                        st.rerun()

    # === 지도 출력 ===
    m = folium.Map(location=[19.0, 73.0], zoom_start=6, tiles="CartoDB positron")
    data = load_json(CITY_FILE)
    coords = []

    for c in data:
        if not all(k in c for k in ["city", "lat", "lon", "date", "venue", "seats", "type"]):
            continue

        popup_html = f"""
        <div style="
            font-family: 'Malgun Gothic', sans-serif;
            font-size: 14px;
            text-align: center;
            white-space: nowrap;
            padding: 10px 16px;
            min-width: 420px;
            max-width: 550px;
        ">
            <b>{c['city']}</b> | {c['date']} | {c['venue']} | {c['seats']}석 | {c['type']}
        </div>
        """

        folium.Marker(
            [c["lat"], c["lon"]],
            popup=folium.Popup(popup_html, max_width=550),
            tooltip=c["city"],
            icon=folium.Icon(color="red", icon="music", prefix="fa")
        ).add_to(m)

        coords.append((c["lat"], c["lon"]))

    if len(coords) > 1:
        AntPath(coords, color="#ff1744", weight=5, opacity=0.8, delay=800, dash_array=[20, 30]).add_to(m)

    st_folium(m, width=900, height=550, key="tour_map")

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    st.markdown("### 언어 선택")
    lang_options = {"한국어": "ko", "English": "en", "हिन्दी": "hi"}
    display_options = list(lang_options.keys())
    current_idx = display_options.index(
        next((k for k, v in lang_options.items() if v == st.session_state.lang), "한국어")
    )
    selected_display = st.selectbox("Language", display_options, index=current_idx)
    new_lang = lang_options[selected_display]

    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")
    if not st.session_state.admin:
        st.markdown("### 관리자 로그인")
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
st.markdown(f"# {_['title']} 크리스마스")
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
    render_map()
