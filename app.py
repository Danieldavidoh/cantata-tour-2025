import json, os, uuid, base64
import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezoneimport json, os, uuid, base64
import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
import random

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

# --- 2. 파일 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 3. 다국어 ---
LANG = {
    "ko": { "tab_notice": "공지", "tab_map": "투어 경로", "today": "오늘", "yesterday": "어제", "new_notice_alert": "새 공지가 도착했어요!", "warning": "제목·내용 입력", "edit": "수정", "save": "저장", "cancel": "취소", "add_city": "도시 추가", "indoor": "실내", "outdoor": "실외", "venue": "장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵 링크", "perf_date": "공연 날짜", "change_pw": "비밀번호 변경", "current_pw": "현재 비밀번호", "new_pw": "새 비밀번호", "confirm_pw": "새 비밀번호 확인", "pw_changed": "비밀번호 변경 완료!", "pw_mismatch": "비밀번호 불일치", "pw_error": "현재 비밀번호 오류", "select_city": "도시 선택 (클릭)" },
    "en": { "tab_notice": "Notice", "tab_map": "Tour Route", "today": "Today", "yesterday": "Yesterday", "new_notice_alert": "New notice!", "warning": "Enter title & content", "edit": "Edit", "save": "Save", "cancel": "Cancel", "add_city": "Add City", "indoor": "Indoor", "outdoor": "Outdoor", "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps Link", "perf_date": "Performance Date", "change_pw": "Change Password", "current_pw": "Current Password", "new_pw": "New Password", "confirm_pw": "Confirm Password", "pw_changed": "Password changed!", "pw_mismatch": "Passwords don't match", "pw_error": "Incorrect current password", "select_city": "Select City (Click)" },
    "hi": { "tab_notice": "सूचना", "tab_map": "टूर मार्ग", "today": "आज", "yesterday": "कल", "new_notice_alert": "नई सूचना!", "warning": "शीर्षक·सामग्री दर्ज करें", "edit": "संपादन", "save": "सहेजें", "cancel": "रद्द करें", "add_city": "शहर जोड़ें", "indoor": "इनडोर", "outdoor": "आउटडोर", "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप लिंक", "perf_date": "प्रदर्शन तिथि", "change_pw": "पासवर्ड बदलें", "current_pw": "वर्तमान पासवर्ड", "new_pw": "नया पासवर्ड", "confirm_pw": "पासवर्ड की पुष्टि करें", "pw_changed": "पासवर्ड बदल गया!", "pw_mismatch": "पासवर्ड मेल नहीं खाते", "pw_error": "गलत वर्तमान पासवर्ड", "select_city": "शहर चुनें (क्लिक)" }
}

# --- 4. 세션 상태 ---
defaults = { "admin": False, "lang": "ko", "edit_city": None, "adding_city": False, "tab_selection": "공지", "new_notice": False, "sound_played": False, "seen_notices": [], "expanded_notices": [], "expanded_cities": [], "last_tab": None, "alert_active": False, "current_alert_id": None, "password": "0009", "show_pw_form": False, "map_fullscreen": False }
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 5. JSON 헬퍼 ---
def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 6. 초기 도시 + 좌표 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도", "google_link": "https://goo.gl/maps/abc123", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-10"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브", "google_link": "https://goo.gl/maps/def456", "indoor": True, "date": "11/07 02:01", "perf_date": "2025-11-12"},
    {"city": "Pune", "venue": "Aga Khan Palace", "seats": "2500", "note": "역사적 장소", "google_link": "https://goo.gl/maps/pune2", "indoor": False, "date": "11/08 14:00", "perf_date": "2025-11-14"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시", "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-16"}
]
if not os.path.exists(CITY_FILE): save_json(CITY_FILE, DEFAULT_CITIES)

CITY_COORDS = { "Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567), "Nagpur": (21.1458, 79.0882) }

# --- 7. 캐롤 사운드 ---
def play_carol():
    if os.path.exists("carol.wav"):
        st.session_state.sound_played = True
        st.markdown("<audio autoplay><source src='carol.wav' type='audio/wav'></audio>", unsafe_allow_html=True)

# --- 8. CSS + 눈 + 모바일 사이드바 숨김 ---
st.markdown("""
<style>
    /* 모바일에서 사이드바 숨기기 */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        .css-1d391kg { display: none !important; }
    }

    [data-testid="stAppViewContainer"] { background: url("background_christmas_dark.png"); background-size: cover; background-position: center; background-attachment: fixed; padding-top: 20px; }
    .main-title { text-align: center; font-size: 2.8em !important; font-weight: bold; color: #e74c3c; margin: 30px 0 40px 0 !important; text-shadow: 0 2px 5px rgba(0,0,0,0.3); }
    .tab-container { background: rgba(255,255,255,0.9); padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 20px 0; }
    .snowflake { position: fixed; top: -15px; color: white; font-size: 1.1em; pointer-events: none; animation: fall linear infinite; opacity: 0.3 !important; text-shadow: 0 0 4px rgba(255,255,255,0.6); z-index: 1; }
    @keyframes fall { 0% { transform: translateY(0) rotate(0deg); } 100% { transform: translateY(120vh) rotate(360deg); } }
    .alert-box { position: fixed; top: 20px; right: 20px; z-index: 9999; background: linear-gradient(135deg, #ff4757, #ff3742); color: white; padding: 18px 24px; border-radius: 16px; box-shadow: 0 10px 30px rgba(255,71,87,0.5); font-weight: bold; font-size: 17px; display: flex; align-items: center; gap: 14px; animation: slideIn 0.6s ease-out, pulse 1.8s infinite; border: 2px solid #fff; }
    @keyframes slideIn { from { transform: translateX(150%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.07); } }
    .fullscreen-map { position: fixed !important; top: 0; left: 0; width: 100vw !important; height: 100vh !important; z-index: 9998; background: white; }
</style>
""", unsafe_allow_html=True)

# --- 눈송이 (26개) ---
for i in range(26):
    left = random.randint(0, 100)
    duration = random.randint(10, 20)
    size = random.uniform(0.8, 1.4)
    delay = random.uniform(0, 10)
    st.markdown(f"<div class='snowflake' style='left:{left}vw; animation-duration:{duration}s; font-size:{size}em; animation-delay:{delay}s;'>❄</div>", unsafe_allow_html=True)

# --- 전체화면 지도 ---
st.markdown("""
<script>
    let mapClicked = false;
    document.addEventListener('click', function(e) {
        if (e.target.closest('.folium-map')) {
            if (!mapClicked) { const map = e.target.closest('.folium-map'); map.classList.add('fullscreen-map'); mapClicked = true; }
            else { const map = document.querySelector('.fullscreen-map'); if (map) map.classList.remove('fullscreen-map'); mapClicked = false; }
        }
    });
</script>
""", unsafe_allow_html=True)

# --- 9. 메인 컨테이너 ---
main_container = st.container()
with main_container:
    st.markdown('<h1 class="main-title">칸타타 투어 2025 마하라스트라</h1>', unsafe_allow_html=True)

    # --- 사이드바 (PC만 보임, 모바일 숨김) ---
    with st.sidebar:
        st.markdown("### 설정")
        lang_map = {"한국어": "ko", "English": "en", "हिंदी": "hi"}
        sel = st.selectbox("언어", list(lang_map.keys()), index=list(lang_map.values()).index(st.session_state.lang))
        if lang_map[sel] != st.session_state.lang:
            st.session_state.lang = lang_map[sel]
            st.session_state.tab_selection = _(f"tab_notice")
            st.rerun()

        st.markdown("---")
        if not st.session_state.admin:
            pw = st.text_input("비밀번호", type="password", key="pw_input")
            if st.button("로그인", key="login_btn"):
                if pw == st.session_state.password:
                    st.session_state.admin = True
                    st.rerun()
                else:
                    st.error("비밀번호 오류")
        else:
            st.success("관리자 모드")
            if st.button("로그아웃", key="logout_btn"):
                st.session_state.admin = False
                st.rerun()

            st.markdown("---")
            if st.button(_(f"change_pw"), key="show_pw_btn"):
                st.session_state.show_pw_form = True

            if st.session_state.get("show_pw_form", False):
                with st.form("change_pw_form"):
                    current_pw = st.text_input(_(f"current_pw"), type="password")
                    new_pw = st.text_input(_(f"new_pw"), type="password")
                    confirm_pw = st.text_input(_(f"confirm_pw"), type="password")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.form_submit_button("변경"):
                            if current_pw == "0691" and new_pw == confirm_pw and new_pw:
                                st.session_state.password = new_pw
                                st.success(_(f"pw_changed"))
                                st.session_state.show_pw_form = False
                                st.rerun()
                            elif new_pw != confirm_pw:
                                st.error(_(f"pw_mismatch"))
                            else:
                                st.error(_(f"pw_error"))
                    with c2:
                        if st.form_submit_button("취소"):
                            st.session_state.show_pw_form = False
                            st.rerun()

    # --- 메인 콘텐츠 ---
    st.markdown('<div class="tab-container">', unsafe_allow_html=True)
    tab_col1, tab_col2 = st.columns(2)
    with tab_col1:
        if st.button(_(f"tab_notice"), use_container_width=True, key="tab_notice_btn"):
            st.session_state.tab_selection = _(f"tab_notice")
            st.rerun()
    with tab_col2:
        if st.button(_(f"tab_map"), use_container_width=True, key="tab_map_btn"):
            st.session_state.tab_selection = _(f"tab_map")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.tab_selection == _(f"tab_notice"):
        if st.session_state.admin:
            with st.expander("공지 작성"):
                with st.form("notice_form", clear_on_submit=True):
                    title = st.text_input("제목")
                    content = st.text_area("내용")
                    img = st.file_uploader("이미지", type=["png", "jpg", "jpeg"])
                    file = st.file_uploader("첨부 파일")
                    if st.form_submit_button("등록"):
                        if title.strip() and content.strip():
                            img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
                            file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
                            if img: open(img_path, "wb").write(img.getbuffer())
                            if file: open(file_path, "wb").write(file.getbuffer())
                            notice = { "id": str(uuid.uuid4()), "title": title, "content": content, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"), "image": img_path, "file": file_path }
                            data = load_json(NOTICE_FILE)
                            data.insert(0, notice)
                            save_json(NOTICE_FILE, data)
                            st.success("공지 등록 완료!")
                            st.rerun()
                        else:
                            st.warning(_("warning"))

        data = load_json(NOTICE_FILE)
        for i, n in enumerate(data):
            with st.expander(f"{n['date']} | {n['title']}"):
                st.markdown(n["content"])
                if n.get("image") and os.path.exists(n["image"]): st.image(n["image"], use_column_width=True)
                if n.get("file") and os.path.exists(n["file"]):
                    b64 = base64.b64encode(open(n["file"], "rb").read()).decode()
                    st.markdown(f'<a href="data:file/txt;base64,{b64}" download="{os.path.basename(n["file"])}">다운로드</a>', unsafe_allow_html=True)
                if st.session_state.admin and st.button("삭제", key=f"del_n_{n['id']}"):
                    data.pop(i)
                    save_json(NOTICE_FILE, data)
                    st.rerun()

    else:
        # --- 관리자 모드: 도시 추가/수정 폼 ---
        if st.session_state.admin:
            with st.expander("도시 추가/수정", expanded=st.session_state.adding_city or st.session_state.edit_city):
                if st.session_state.get("adding_city") or st.button("도시 추가", key="add_city_btn"):
                    st.session_state.adding_city = True
                    with st.form("add_city_form"):
                        city = st.text_input("도시명")
                        venue = st.text_input("장소")
                        seats = st.text_input("예상 인원")
                        indoor = st.radio("유형", ["실내", "실외"])
                        note = st.text_area("특이사항")
                        google_link = st.text_input("구글맵 링크")
                        perf_date = st.date_input("공연 날짜")
                        if st.form_submit_button("저장"):
                            if city:
                                new_city = {
                                    "city": city, "venue": venue, "seats": seats,
                                    "indoor": indoor == "실내", "note": note,
                                    "google_link": google_link, "perf_date": str(perf_date),
                                    "date": datetime.now().strftime("%m/%d %H:%M")
                                }
                                data = load_json(CITY_FILE)
                                data.append(new_city)
                                save_json(CITY_FILE, data)
                                st.session_state.adding_city = False
                                st.success("도시 추가 완료!")
                                st.rerun()
                            else:
                                st.error("도시명 필수")

        # --- 지도 ---
        raw_cities = load_json(CITY_FILE)
        cities = sorted(raw_cities, key=lambda x: x.get("perf_date", "9999-12-31"))
        m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="OpenStreetMap")
        for i, c in enumerate(cities):
            coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
            is_future = c.get("perf_date", "9999-12-31") >= str(date.today())
            color = "red" if is_future else "gray"
            popup_html = f"<b>{c['city']}</b><br>{c.get('venue','—')}<br>{c.get('seats','—')}명<br>{'실내' if c.get('indoor') else '야외'}"
            folium.Marker(coords, popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=color, icon="music", prefix="fa")).add_to(m)
            if i < len(cities) - 1:
                nxt_coords = CITY_COORDS.get(cities[i+1]["city"], (18.5204, 73.8567))
                AntPath([coords, nxt_coords], color="#e74c3c", weight=6, opacity=0.3 if not is_future else 1.0, delay=800, dash_array=[20, 30]).add_to(m)
        st_folium(m, width=900, height=550, key="tour_map")

# --- 탭 전환 ---
if st.session_state.tab_selection != st.session_state.get("last_tab"):
    st.session_state.last_tab = st.session_state.tab_selection
    st.rerun()
from streamlit_autorefresh import st_autorefresh
import random

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

# --- 2. 파일 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 3. 다국어 ---
LANG = {
    "ko": { "tab_notice": "공지", "tab_map": "투어 경로", "today": "오늘", "yesterday": "어제", "new_notice_alert": "새 공지가 도착했어요!", "warning": "제목·내용 입력", "edit": "수정", "save": "저장", "cancel": "취소", "add_city": "도시 추가", "indoor": "실내", "outdoor": "실외", "venue": "장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵 링크", "perf_date": "공연 날짜", "change_pw": "비밀번호 변경", "current_pw": "현재 비밀번호", "new_pw": "새 비밀번호", "confirm_pw": "새 비밀번호 확인", "pw_changed": "비밀번호 변경 완료!", "pw_mismatch": "비밀번호 불일치", "pw_error": "현재 비밀번호 오류", "select_city": "도시 선택 (클릭)" },
    "en": { "tab_notice": "Notice", "tab_map": "Tour Route", "today": "Today", "yesterday": "Yesterday", "new_notice_alert": "New notice!", "warning": "Enter title & content", "edit": "Edit", "save": "Save", "cancel": "Cancel", "add_city": "Add City", "indoor": "Indoor", "outdoor": "Outdoor", "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps Link", "perf_date": "Performance Date", "change_pw": "Change Password", "current_pw": "Current Password", "new_pw": "New Password", "confirm_pw": "Confirm Password", "pw_changed": "Password changed!", "pw_mismatch": "Passwords don't match", "pw_error": "Incorrect current password", "select_city": "Select City (Click)" },
    "hi": { "tab_notice": "सूचना", "tab_map": "टूर मार्ग", "today": "आज", "yesterday": "कल", "new_notice_alert": "नई सूचना!", "warning": "शीर्षक·सामग्री दर्ज करें", "edit": "संपादन", "save": "सहेजें", "cancel": "रद्द करें", "add_city": "शहर जोड़ें", "indoor": "इनडोर", "outdoor": "आउटडोर", "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप लिंक", "perf_date": "प्रदर्शन तिथि", "change_pw": "पासवर्ड बदलें", "current_pw": "वर्तमान पासवर्ड", "new_pw": "नया पासवर्ड", "confirm_pw": "पासवर्ड की पुष्टि करें", "pw_changed": "पासवर्ड बदल गया!", "pw_mismatch": "पासवर्ड मेल नहीं खाते", "pw_error": "गलत वर्तमान पासवर्ड", "select_city": "शहर चुनें (क्लिक)" }
}

# --- 4. 세션 상태 ---
defaults = { "admin": False, "lang": "ko", "edit_city": None, "adding_city": False, "tab_selection": "공지", "new_notice": False, "sound_played": False, "seen_notices": [], "expanded_notices": [], "expanded_cities": [], "last_tab": None, "alert_active": False, "current_alert_id": None, "password": "0009", "show_pw_form": False, "map_fullscreen": False }
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 5. JSON 헬퍼 ---
def load_json(f):
    return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []

def save_json(f, d):
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 6. 초기 도시 + 좌표 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도", "google_link": "https://goo.gl/maps/abc123", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-10"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브", "google_link": "https://goo.gl/maps/def456", "indoor": True, "date": "11/07 02:01", "perf_date": "2025-11-12"},
    {"city": "Pune", "venue": "Aga Khan Palace", "seats": "2500", "note": "역사적 장소", "google_link": "https://goo.gl/maps/pune2", "indoor": False, "date": "11/08 14:00", "perf_date": "2025-11-14"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시", "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "date": "11/07 02:01", "perf_date": "2025-11-16"}
]
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

CITY_COORDS = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882)
}

# --- 7. 캐롤 사운드 ---
def play_carol():
    if os.path.exists("carol.wav"):
        st.session_state.sound_played = True
        st.markdown("<audio autoplay><source src='carol.wav' type='audio/wav'></audio>", unsafe_allow_html=True)

# --- 8. CSS + 눈 효과 + 레이아웃 ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: url("background_christmas_dark.png"); background-size: cover; background-position: center; background-attachment: fixed; padding-top: 20px; }
    .main-title { text-align: center; font-size: 2.8em !important; font-weight: bold; color: #e74c3c; margin: 30px 0 40px 0 !important; text-shadow: 0 2px 5px rgba(0,0,0,0.3); }
    .tab-container { background: rgba(255,255,255,0.9); padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 20px 0; }
    .snowflake { position: fixed; top: -15px; color: white; font-size: 1.1em; pointer-events: none; animation: fall linear infinite; opacity: 0.3 !important; text-shadow: 0 0 4px rgba(255,255,255,0.6); z-index: 1; }
    @keyframes fall { 0% { transform: translateY(0) rotate(0deg); } 100% { transform: translateY(120vh) rotate(360deg); } }
    .alert-box { position: fixed; top: 20px; right: 20px; z-index: 9999; background: linear-gradient(135deg, #ff4757, #ff3742); color: white; padding: 18px 24px; border-radius: 16px; box-shadow: 0 10px 30px rgba(255,71,87,0.5); font-weight: bold; font-size: 17px; display: flex; align-items: center; gap: 14px; animation: slideIn 0.6s ease-out, pulse 1.8s infinite; border: 2px solid #fff; }
    @keyframes slideIn { from { transform: translateX(150%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.07); } }
    .fullscreen-map { position: fixed !important; top: 0; left: 0; width: 100vw !important; height: 100vh !important; z-index: 9998; background: white; }
    .css-1d391kg { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# --- 눈송이 (26개) ---
for i in range(26):
    left = random.randint(0, 100)
    duration = random.randint(10, 20)
    size = random.uniform(0.8, 1.4)
    delay = random.uniform(0, 10)
    st.markdown(f"<div class='snowflake' style='left:{left}vw; animation-duration:{duration}s; font-size:{size}em; animation-delay:{delay}s;'>❄</div>", unsafe_allow_html=True)

# --- 전체화면 지도 ---
st.markdown("""
<script>
    let mapClicked = false;
    document.addEventListener('click', function(e) {
        if (e.target.closest('.folium-map')) {
            if (!mapClicked) { const map = e.target.closest('.folium-map'); map.classList.add('fullscreen-map'); mapClicked = true; }
            else { const map = document.querySelector('.fullscreen-map'); if (map) map.classList.remove('fullscreen-map'); mapClicked = false; }
        }
    });
</script>
""", unsafe_allow_html=True)

# --- 9. 메인 컨테이너 ---
main_container = st.container()
with main_container:
    st.markdown('<h1 class="main-title">칸타타 투어 2025 마하라스트라</h1>', unsafe_allow_html=True)

    col_sidebar, col_main = st.columns([1, 4])

    with col_sidebar:
        st.markdown("### 설정")
        lang_map = {"한국어": "ko", "English": "en", "हिंदी": "hi"}
        sel = st.selectbox("언어", list(lang_map.keys()), index=list(lang_map.values()).index(st.session_state.lang))
        if lang_map[sel] != st.session_state.lang:
            st.session_state.lang = lang_map[sel]
            st.session_state.tab_selection = _(f"tab_notice")
            st.rerun()

        st.markdown("---")
        if not st.session_state.admin:
            pw = st.text_input("비밀번호", type="password", key="pw_input")
            if st.button("로그인", key="login_btn"):
                if pw == st.session_state.password:
                    st.session_state.admin = True
                    st.rerun()
                else:
                    st.error("비밀번호 오류")
        else:
            st.success("관리자 모드")
            if st.button("로그아웃", key="logout_btn"):
                st.session_state.admin = False
                st.rerun()

            st.markdown("---")
            if st.button(_(f"change_pw"), key="show_pw_btn"):
                st.session_state.show_pw_form = True

            if st.session_state.get("show_pw_form", False):
                with st.form("change_pw_form"):
                    st.markdown("### 비밀번호 변경")
                    current_pw = st.text_input(_(f"current_pw"), type="password")
                    new_pw = st.text_input(_(f"new_pw"), type="password")
                    confirm_pw = st.text_input(_(f"confirm_pw"), type="password")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.form_submit_button("변경"):
                            if current_pw == "0691" and new_pw == confirm_pw and new_pw:
                                st.session_state.password = new_pw
                                st.success(_(f"pw_changed"))
                                st.session_state.show_pw_form = False
                                st.rerun()
                            elif new_pw != confirm_pw:
                                st.error(_(f"pw_mismatch"))
                            else:
                                st.error(_(f"pw_error"))
                    with c2:
                        if st.form_submit_button("취소"):
                            st.session_state.show_pw_form = False
                            st.rerun()

    with col_main:
        st.markdown('<div class="tab-container">', unsafe_allow_html=True)
        tab_col1, tab_col2 = st.columns(2)
        with tab_col1:
            if st.button(_(f"tab_notice"), use_container_width=True, key="tab_notice_btn"):
                st.session_state.tab_selection = _(f"tab_notice")
                st.rerun()
        with tab_col2:
            if st.button(_(f"tab_map"), use_container_width=True, key="tab_map_btn"):
                st.session_state.tab_selection = _(f"tab_map")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.tab_selection == _(f"tab_notice"):
            if st.session_state.admin:
                with st.expander("공지 작성"):
                    with st.form("notice_form", clear_on_submit=True):
                        title = st.text_input("제목")
                        content = st.text_area("내용")
                        img = st.file_uploader("이미지", type=["png", "jpg", "jpeg"])
                        file = st.file_uploader("첨부 파일")
                        if st.form_submit_button("등록"):
                            if title.strip() and content.strip():
                                img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
                                file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
                                if img: open(img_path, "wb").write(img.getbuffer())
                                if file: open(file_path, "wb").write(file.getbuffer())
                                notice = { "id": str(uuid.uuid4()), "title": title, "content": content, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"), "image": img_path, "file": file_path }
                                data = load_json(NOTICE_FILE)
                                data.insert(0, notice)
                                save_json(NOTICE_FILE, data)
                                st.success("공지 등록 완료!")
                                st.rerun()
                            else:
                                st.warning(_("warning"))

            data = load_json(NOTICE_FILE)
            for i, n in enumerate(data):
                with st.expander(f"{n['date']} | {n['title']}"):
                    st.markdown(n["content"])
                    if n.get("image") and os.path.exists(n["image"]): st.image(n["image"], use_column_width=True)
                    if n.get("file") and os.path.exists(n["file"]):
                        b64 = base64.b64encode(open(n["file"], "rb").read()).decode()
                        st.markdown(f'<a href="data:file/txt;base64,{b64}" download="{os.path.basename(n["file"])}">다운로드</a>', unsafe_allow_html=True)
                    if st.session_state.admin and st.button("삭제", key=f"del_n_{n['id']}"):
                        data.pop(i)
                        save_json(NOTICE_FILE, data)
                        st.rerun()

        else:
            raw_cities = load_json(CITY_FILE)
            cities = sorted(raw_cities, key=lambda x: x.get("perf_date", "9999-12-31"))
            m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="OpenStreetMap")
            for i, c in enumerate(cities):
                coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
                is_future = c.get("perf_date", "9999-12-31") >= str(date.today())
                color = "red" if is_future else "gray"
                popup_html = f"<b>{c['city']}</b><br>{c.get('venue','—')}<br>{c.get('seats','—')}명<br>{'실내' if c.get('indoor') else '야외'}"
                folium.Marker(coords, popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=color, icon="music", prefix="fa")).add_to(m)
                if i < len(cities) - 1:
                    nxt_coords = CITY_COORDS.get(cities[i+1]["city"], (18.5204, 73.8567))
                    AntPath([coords, nxt_coords], color="#e74c3c", weight=6, opacity=0.3 if not is_future else 1.0, delay=800, dash_array=[20, 30]).add_to(m)
            st_folium(m, width=900, height=550, key="tour_map")

# --- 탭 전환 ---
if st.session_state.tab_selection != st.session_state.get("last_tab"):
    st.session_state.last_tab = st.session_state.tab_selection
    st.rerun()
