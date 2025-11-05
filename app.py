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
TOURS_FILE = "tours.json"
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
# 편집용 인덱스/아이디
if "edit_tour_id" not in st.session_state:
    st.session_state.edit_tour_id = None

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
        "no_perf": "공연없음",
        "add_city_label": "도시 선택 (공연없음 기본)",
        "venue_label": "공연장소",
        "seats_label": "좌석 수",
        "gmap_label": "구글 맵 링크 (옵션)",
        "notes_label": "특이사항",
        "indoor_label": "실내 / 실외",
        "add_button": "도시 추가",
        "edit_button": "수정",
        "save_button": "저장",
        "reset_button": "초기화"
    },
}

_ = LANG[st.session_state.lang]

# =============================================
# CITIES (150개) - 요청하신 리스트 (이전 메시지 내용 반영)
# =============================================
CITIES = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882),
    "Thane": (19.2183, 72.9781),
    "Nashik": (19.9975, 73.7898),
    "Aurangabad": (19.8762, 75.3433),
    "Solapur": (17.6599, 75.9064),
    "Kolhapur": (16.7050, 74.2433),
    "Amravati": (20.9374, 77.7797),
    "Jalgaon": (21.0077, 75.5626),
    "Akola": (20.7096, 76.9981),
    "Latur": (18.4088, 76.5604),
    "Ahmednagar": (19.0946, 74.7384),
    "Dhule": (20.9042, 74.7749),
    "Chandrapur": (19.9615, 79.2961),
    "Parbhani": (19.2616, 76.7797),
    "Jalna": (19.8295, 75.8808),
    "Bhusawal": (21.0455, 75.7882),
    "Satara": (17.6859, 74.0183),
    "Beed": (18.9890, 75.7602),
    "Yavatmal": (20.3890, 78.1208),
    "Gondia": (21.4620, 80.1960),
    "Wardha": (20.7453, 78.6022),
    "Nandurbar": (21.3702, 74.2428),
    "Osmanabad": (18.1860, 76.0419),
    "Hingoli": (19.7178, 77.1485),
    "Buldhana": (20.4680, 76.3632),
    "Washim": (20.1115, 77.1333),
    "Gadchiroli": (20.1833, 80.2833),
    "Ichalkaranji": (16.6912, 74.4605),
    "Malegaon": (20.5537, 74.5288),
    "Barshi": (18.2333, 75.7000),
    "Panvel": (18.9880, 73.1100),
    "Badlapur": (19.1550, 73.2650),
    "Ulhasnagar": (19.2167, 73.1500),
    "Kalyan": (19.2403, 73.1305),
    "Dombivli": (19.2183, 73.0860),
    "Navi Mumbai": (19.0330, 73.0297),
    "Mira-Bhayandar": (19.2952, 72.8544),
    "Vasai-Virar": (19.3919, 72.8397),
    "Sangli": (16.8524, 74.5815),
    "Miraj": (16.8244, 74.6480),
    "Ratnagiri": (16.9902, 73.3120),
    "Sindhudurg": (16.1247, 73.6535),
    "Palghar": (19.6960, 72.7680),
    "Boisar": (19.8000, 72.7500),
    "Vapi": (20.3667, 72.9047),
    "Dahanu": (19.9678, 72.7330),
    "Karad": (17.2890, 74.1840),
    "Islampur": (17.0480, 74.2640),
    "Ambajogai": (18.7333, 76.3833),
    "Nanded": (19.1383, 77.3210),
    "Basmat": (19.3167, 77.1667),
    "Hinganghat": (20.5600, 78.8330),
    "Wani": (20.0667, 78.9500),
    "Umred": (20.8500, 79.3333),
    "Bhandara": (21.1700, 79.6500),
    "Tumsar": (21.3833, 79.7333),
    "Deolali": (19.9400, 73.8333),
    "Manmad": (20.2533, 74.4375),
    "Sinnar": (19.8500, 74.0000),
    "Shrirampur": (19.6200, 74.6600),
    "Kopargaon": (19.8833, 74.4833),
    "Shirdi": (19.7667, 74.4833),
    "Pathardi": (19.1667, 75.1667),
    "Paithan": (19.4833, 75.3833),
    "Gangapur": (19.7000, 75.0000),
    "Sillod": (20.3000, 75.6500),
    "Kannad": (20.4000, 75.1333),
    "Soygaon": (20.6000, 75.6333),
    "Chikhli": (20.3500, 76.2500),
    "Malkapur": (20.8833, 76.2000),
    "Deulgaon Raja": (20.0167, 76.0333),
    "Mehkar": (20.1500, 76.5833),
    "Khamgaon": (20.7000, 76.5667),
    "Shegaon": (20.7833, 76.6833),
    "Lonar": (19.9833, 76.5167),
    "Mangrulpir": (20.3133, 77.3422),
    "Risod": (20.2000, 76.7833),
    "Karanja": (20.4833, 77.5000),
    "Pusad": (19.9000, 77.5833),
    "Digras": (20.1000, 77.7167),
    "Umarkhed": (19.6000, 77.7000),
    "Arni": (20.3833, 78.0333),
    "Pandharkawada": (20.0170, 78.5260),
    "Darwha": (20.3167, 77.7667),
    "Kalamb": (19.0167, 73.9500),
    "Ner": (20.5000, 77.5000),
    "Patur": (20.4500, 76.9333),
    "Akot": (21.1000, 77.0583),
    "Murtizapur": (20.7333, 77.3667),
    "Balapur": (20.6667, 76.7833),
    "Daryapur": (20.9333, 77.3167),
    "Achalpur": (21.2561, 77.5100),
    "Dharangaon": (21.0167, 75.2833),
    "Yawal": (21.1700, 75.6850),
    "Raver": (21.2475, 75.9258),
    "Erandol": (20.9050, 75.3264),
    "Chalisgaon": (20.4619, 75.0052),
    "Pachora": (20.6667, 75.3500),
    "Bodwad": (20.8833, 75.6667),
    "Bhadgaon": (20.6667, 75.2333),
    "Parola": (20.8833, 75.1200),
    "Shahada": (21.5500, 74.4667),
    "Taloda": (21.5667, 74.2167),
    "Navapur": (21.1667, 74.0667),
    "Sakri": (20.9167, 74.2000),
    "Shirpur": (21.3500, 74.8833),
    "Faizpur": (21.1667, 75.8500),
    "Nandgaon": (20.3167, 74.6500),
    "Chandvad": (20.3167, 74.2500),
    "Surgana": (20.5667, 73.6167),
    "Igatpuri": (19.7000, 73.5500),
    "Jawhar": (19.9167, 73.2333),
    "Vikramgad": (19.7167, 73.0333),
    "Shahapur": (19.4500, 73.3333),
    "Ambarnath": (19.2000, 73.1833),
    "Khadakwasla": (18.4333, 73.7667),
    "Alibag": (18.6400, 72.8700),
    "Murud": (18.3300, 72.9700),
    "Mangaon": (18.0833, 73.2833),
    "Roha": (18.4333, 73.1167),
    "Mahad": (18.0833, 73.4167),
    "Poladpur": (18.0000, 73.4833),
    "Khed": (17.7167, 73.3833),
    "Chiplun": (17.5333, 73.5167),
    "Guhagar": (17.4833, 73.2000),
    "Dapoli": (17.7500, 73.1833),
    "Mandangad": (17.9833, 73.2500),
    "Lanja": (16.8500, 73.5500),
    "Rajapur": (16.6700, 73.5170),
    "Kankavli": (16.2667, 73.7000),
    "Kudal": (16.0000, 73.6833),
    "Sawantwadi": (15.9000, 73.8167),
}

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
# 공지 추가/삭제 (기존)
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
# TOURS 관리 추가 (새 파일: tours.json)
# =============================================
def load_tours():
    if os.path.exists(TOURS_FILE):
        with open(TOURS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_tours(tours):
    with open(TOURS_FILE, "w", encoding="utf-8") as f:
        json.dump(tours, f, ensure_ascii=False, indent=2)

def add_tour_entry(city, venue, seats, gmap, notes, indoor):
    tours = load_tours()
    new = {
        "id": str(uuid.uuid4()),
        "city": city,
        "venue": venue,
        "seats": seats,
        "gmap": gmap,
        "notes": notes,
        "indoor": indoor,
        "date_added": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    tours.insert(0, new)
    save_tours(tours)
    st.toast(f"✅ {city}가 추가되었습니다.")
    st.session_state.edit_tour_id = None
    st.rerun()

def update_tour_entry(tour_id, city, venue, seats, gmap, notes, indoor):
    tours = load_tours()
    for t in tours:
        if t["id"] == tour_id:
            t.update({
                "city": city,
                "venue": venue,
                "seats": seats,
                "gmap": gmap,
                "notes": notes,
                "indoor": indoor,
            })
            break
    save_tours(tours)
    st.toast("✅ 변경사항이 저장되었습니다.")
    st.session_state.edit_tour_id = None
    st.rerun()

def delete_tour_entry(tour_id):
    tours = load_tours()
    tours = [t for t in tours if t["id"] != tour_id]
    save_tours(tours)
    st.toast("🗑️ 경로 항목이 삭제되었습니다.")
    st.rerun()

# =============================================
# 공지 리스트 (기존)
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
# 지도 렌더 (투어 포함)
# =============================================
def render_map():
    st.subheader(_["map_title"])
    # 기본 예시 도시 (기존 유지) + tours.json에 저장된 항목 마커로 추가
    cities = [
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Nashik", "lat": 19.9975, "lon": 73.7898},
    ]
    m = folium.Map(location=[19.0, 73.0], zoom_start=7)

    # 기본 마커들
    coords = [(c["lat"], c["lon"]) for c in cities]
    for c in cities:
        folium.Marker([c["lat"], c["lon"]], popup=c["name"], tooltip=c["name"],
                      icon=folium.Icon(color="red", icon="music")).add_to(m)

    # tours.json 로드해서 마커 추가 + 경로선
    tours = load_tours()
    tour_coords = []
    for t in reversed(tours):  # 저장된 순서대로 지도에 표시(상단이 최근)
        city_name = t["city"]
        if city_name in CITIES:
            lat, lon = CITIES[city_name]
            tour_coords.append((lat, lon))
            # 팝업 HTML: 공연장, 좌석, 실내/실외, 노트, 구글맵 링크(자동차 아이콘)
            gmap_html = ""
            if t.get("gmap"):
                # 자동차 이모지에 링크 연결 (새 창)
                gmap_html = f'<a href="{t["gmap"]}" target="_blank" title="Navigate">🚗</a>'
            indoor_text = "실내" if t.get("indoor") else "실외"
            popup_html = f"""
            <div style="max-width:300px">
              <b>{city_name}</b><br/>
              공연장: {t.get('venue','') or '-'}<br/>
              좌석: {t.get('seats',0)}<br/>
              유형: {indoor_text}<br/>
              {f'특이사항: {t.get("notes","")}' if t.get("notes") else ''}
              <div style="margin-top:6px">{gmap_html}</div>
            </div>
            """
            folium.Marker([lat, lon],
                          popup=folium.Popup(popup_html, max_width=350),
                          tooltip=city_name,
                          icon=folium.Icon(color="green", icon="music")
                          ).add_to(m)
    # 경로 선 (AntPath) — 표시 가능한 좌표이상이면 연결
    if len(tour_coords) >= 2:
        AntPath(tour_coords[::-1], color="#ff1744", weight=5, delay=800).add_to(m)

    st_folium(m, width=900, height=550)

# =============================================
# 자동 새로고침 (10초마다) (기존)
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
# 사이드바 (기존)
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
# 메인 (기존)
# =============================================
st.markdown(f"# {_['title']} 🎄")
st.caption(_["caption"])

tab1, tab2 = st.tabs([_["tab_notice"], _["tab_map"]])

# ---------- 탭1: 공지 (기존) ----------
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

# ---------- 탭2: 투어 경로 + 도시 추가 (요청 반영) ----------
with tab2:
    # --- 관리자 전용: 도시 추가 블록 (경로 보기 위)
    if st.session_state.admin:
        st.markdown("### ➕ 도시 추가")
        # 한 줄: 도시 선택 (공연없음 기본)
        col_city, col_venue, col_seats = st.columns([3,4,2])
        with col_city:
            city_options = [_["no_perf"]] + sorted(list(CITIES.keys()))
            selected_city = st.selectbox(_["add_city_label"], city_options, index=0)
        with col_venue:
            venue_input = st.text_input(_["venue_label"], key="venue_input")
        with col_seats:
            # seats with +/- buttons step 50
            if "seats_tmp" not in st.session_state:
                st.session_state.seats_tmp = 0
            c1, c2, c3 = st.columns([1,2,1])
            with c1:
                if st.button("-", key="seats_minus"):
                    st.session_state.seats_tmp = max(0, st.session_state.seats_tmp - 50)
            with c2:
                st.session_state.seats_tmp = st.number_input(_["seats_label"], min_value=0, step=50, value=st.session_state.seats_tmp, key="seats_input")
            with c3:
                if st.button("+", key="seats_plus"):
                    st.session_state.seats_tmp = st.session_state.seats_tmp + 50

        # 다음 줄: gmap, notes, indoor/outdoor
        col_gmap, col_notes, col_io = st.columns([4,4,2])
        with col_gmap:
            gmap_input = st.text_input(_["gmap_label"], placeholder="https://www.google.com/maps/...", key="gmap_input")
        with col_notes:
            notes_input = st.text_area(_["notes_label"], key="notes_input", height=60)
        with col_io:
            indoor_input = st.radio(_["indoor_label"], options=["실내", "실외"], index=1, key="indoor_input")
            indoor_bool = True if indoor_input == "실내" else False

        # 추가 / 초기화 버튼
        col_add, col_reset = st.columns([1,1])
        with col_add:
            if st.button(_["add_button"]):
                if selected_city == _["no_perf"] or not selected_city:
                    st.warning("도시를 선택해 주세요.")
                else:
                    # 추가 저장
                    add_tour_entry(
                        city=selected_city,
                        venue=venue_input.strip(),
                        seats=int(st.session_state.seats_tmp),
                        gmap=gmap_input.strip(),
                        notes=notes_input.strip(),
                        indoor=indoor_bool
                    )
                    # 초기화
                    st.session_state.seats_tmp = 0
                    st.session_state.venue_input = ""
                    st.session_state.gmap_input = ""
                    st.session_state.notes_input = ""
        with col_reset:
            if st.button(_["reset_button"]):
                st.session_state.seats_tmp = 0
                st.session_state.venue_input = ""
                st.session_state.gmap_input = ""
                st.session_state.notes_input = ""
                st.success("입력값이 초기화되었습니다.")

        st.markdown("---")

        # 관리자: 추가된 투어 항목들(접힘, 편집 가능)
        st.subheader("📝 등록된 공연 목록 (클릭하여 수정)")
        tours = load_tours()
        if not tours:
            st.info("등록된 공연이 없습니다.")
        else:
            for idx, t in enumerate(tours):
                # 각 항목은 기본 접힘, Edit 버튼 누르면 expander 열림
                collapsed = True
                if st.session_state.edit_tour_id == t["id"]:
                    collapsed = False
                with st.expander(f"{t['city']} — {t.get('venue','-')} (좌석: {t.get('seats',0)})", expanded=not collapsed):
                    colA, colB = st.columns([3,1])
                    with colA:
                        edit_city = st.selectbox("도시", [_["no_perf"]] + sorted(list(CITIES.keys())), index=(sorted(list(CITIES.keys())).index(t["city"]) + 1) if t["city"] in CITIES else 0, key=f"edit_city_{t['id']}")
                        edit_venue = st.text_input("공연장소", value=t.get("venue",""), key=f"edit_venue_{t['id']}")
                        # seats with +/- buttons
                        if f"seats_tmp_{t['id']}" not in st.session_state:
                            st.session_state[f"seats_tmp_{t['id']}"] = int(t.get("seats",0))
                        c1, c2, c3 = st.columns([1,2,1])
                        with c1:
                            if st.button("-", key=f"edit_seats_minus_{t['id']}"):
                                st.session_state[f"seats_tmp_{t['id']}"] = max(0, st.session_state[f"seats_tmp_{t['id']}"] - 50)
                        with c2:
                            st.session_state[f"seats_tmp_{t['id']}"] = st.number_input("좌석 수", min_value=0, step=50, value=st.session_state[f"seats_tmp_{t['id']}"], key=f"edit_seats_input_{t['id']}")
                        with c3:
                            if st.button("+", key=f"edit_seats_plus_{t['id']}"):
                                st.session_state[f"seats_tmp_{t['id']}"] = st.session_state[f"seats_tmp_{t['id']}"] + 50

                        edit_gmap = st.text_input("구글맵 링크", value=t.get("gmap",""), key=f"edit_gmap_{t['id']}")
                        edit_notes = st.text_area("특이사항", value=t.get("notes",""), key=f"edit_notes_{t['id']}")
                        edit_indoor = st.radio("실내/실외", options=["실내","실외"], index=0 if t.get("indoor") else 1, key=f"edit_indoor_{t['id']}")
                        edit_indoor_bool = True if edit_indoor == "실내" else False

                    with colB:
                        if st.button(_["save_button"], key=f"save_{t['id']}"):
                            if edit_city == _["no_perf"]:
                                st.warning("도시를 선택해 주세요.")
                            else:
                                update_tour_entry(
                                    tour_id=t["id"],
                                    city=edit_city,
                                    venue=edit_venue.strip(),
                                    seats=int(st.session_state[f"seats_tmp_{t['id']}"]),
                                    gmap=edit_gmap.strip(),
                                    notes=edit_notes.strip(),
                                    indoor=edit_indoor_bool
                                )
                        if st.button(_["delete"], key=f"del_tour_{t['id']}"):
                            delete_tour_entry(t["id"])
                        # 편집 열기/닫기 토글용 버튼
                        if st.session_state.edit_tour_id == t["id"]:
                            if st.button("접기", key=f"fold_{t['id']}"):
                                st.session_state.edit_tour_id = None
                                st.rerun()
                        else:
                            if st.button(_["edit_button"], key=f"open_{t['id']}"):
                                st.session_state.edit_tour_id = t["id"]
                                st.rerun()

    else:
        st.info("관리자만 도시를 추가/수정할 수 있습니다. 사이드바에서 로그인 해주세요.")

    # --- 지도 렌더(항목 포함) ---
    render_map()
