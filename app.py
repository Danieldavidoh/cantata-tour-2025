import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
import random

# --- 1. 기본 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

if not st.session_state.get("admin", False):
    st_autorefresh(interval=5000, key="auto_refresh_user")

# --- 2. 파일 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 3. 다국어 (완전 정의) ---
LANG = {
    "ko": {
        "tab_notice": "공지", "tab_map": "투어 경로", "today": "오늘", "yesterday": "어제",
        "new_notice_alert": "새 공지가 도착했어요!", "warning": "제목·내용 입력",
        "edit": "수정", "save": "저장", "cancel": "취소", "add_city": "도시 추가",
        "indoor": "실내", "outdoor": "실외", "venue": "장소", "seats": "예상 인원",
        "note": "특이사항", "google_link": "구글맵 링크", "perf_date": "공연 날짜",
        "change_pw": "비밀번호 변경", "current_pw": "현재 비밀번호", "new_pw": "새 비밀번호",
        "confirm_pw": "새 비밀번호 확인", "pw_changed": "비밀번호 변경 완료!", "pw_mismatch": "비밀번호 불일치",
        "pw_error": "현재 비밀번호 오류", "select_city": "도시 선택 (클릭)"
    },
    "en": {
        "tab_notice": "Notice", "tab_map": "Tour Route", "today": "Today", "yesterday": "Yesterday",
        "new_notice_alert": "New notice!", "warning": "Enter title & content",
        "edit": "Edit", "save": "Save", "cancel": "Cancel", "add_city": "Add City",
        "indoor": "Indoor", "outdoor": "Outdoor", "venue": "Venue", "seats": "Expected",
        "note": "Note", "google_link": "Google Maps Link", "perf_date": "Performance Date",
        "change_pw": "Change Password", "current_pw": "Current Password", "new_pw": "New Password",
        "confirm_pw": "Confirm Password", "pw_changed": "Password changed!", "pw_mismatch": "Passwords don't match",
        "pw_error": "Incorrect current password", "select_city": "Select City (Click)"
    },
    "hi": {
        "tab_notice": "सूचना", "tab_map": "टूर मार्ग", "today": "आज", "yesterday": "कल",
        "new_notice_alert": "नई सूचना!", "warning": "शीर्षक·सामग्री दर्ज करें",
        "edit": "संपादन", "save": "सहेजें", "cancel": "रद्द करें", "add_city": "शहर जोड़ें",
        "indoor": "इनडोर", "outdoor": "आउटडोर", "venue": "स्थल", "seats": "अपेक्षित",
        "note": "नोट", "google_link": "गूगल मैप लिंक", "perf_date": "प्रदर्शन तिथि",
        "change_pw": "पासवर्ड बदलें", "current_pw": "वर्तमान पासवर्ड", "new_pw": "नया पासवर्ड",
        "confirm_pw": "पासवर्ड की पुष्टि करें", "pw_changed": "पासवर्ड बदल गया!", "pw_mismatch": "पासवर्ड मेल नहीं खाते",
        "pw_error": "गलत वर्तमान पासवर्ड", "select_city": "शहर चुनें (क्लिक)"
    }
}

# --- 4. 세션 상태 기본값 (완전 정의) ---
defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "adding_city": False,
    "tab_selection": "공지", "new_notice": False, "sound_played": False,
    "seen_notices": [], "expanded_notices": [], "expanded_cities": [],
    "last_tab": None, "alert_active": False, "current_alert_id": None,
    "password": "0009", "show_pw_form": False, "map_fullscreen": False
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 5. 캐롤 사운드 ---
def play_carol():
    if os.path.exists("carol.wav"):
        st.session_state.sound_played = True
        st.markdown("""
        <audio autoplay>
            <source src="carol.wav" type="audio/wav">
        </audio>
        """, unsafe_allow_html=True)

# --- 6. CSS + 배경 + 눈 효과 (투명도 50%) ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: url("background_christmas_dark.png");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .snowflake {
        position: fixed;
        top: -15px;
        color: white;
        font-size: 1.3em;
        pointer-events: none;
        animation: fall linear infinite;
        opacity: 0.5 !important;
        text-shadow: 0 0 6px rgba(255,255,255,0.8);
        z-index: 1;
    }
    @keyframes fall {
        0%   { transform: translateY(0) rotate(0deg); }
        100% { transform: translateY(120vh) rotate(360deg); }
    }
    .alert-box {
        position: fixed; top: 20px; right: 20px; z-index: 9999;
        background: linear-gradient(135deg, #ff4757, #ff3742); color: white; padding: 18px 24px;
        border-radius: 16px; box-shadow: 0 10px 30px rgba(255, 71, 87, 0.5);
        font-weight: bold; font-size: 17px; display: flex; align-items: center; gap: 14px;
        animation: slideIn 0.6s ease-out, pulse 1.8s infinite;
        border: 2px solid #fff;
    }
    @keyframes slideIn { from { transform: translateX(150%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.07); } }
    .alert-close { cursor: pointer; font-size: 26px; font-weight: bold; }
    .city-label { color: #e74c3c !important; font-weight: bold; font-size: 1.1em; }
    .city-icon { margin-right: 8px; font-size: 1.2em; }
    .fullscreen-map {
        position: fixed !important; top: 0; left: 0; width: 100vw !important; height: 100vh !important;
        z-index: 9998; background: white;
    }
</style>
""", unsafe_allow_html=True)

# --- 눈송이 생성 (80개, 50% 투명) ---
for i in range(80):
    left = random.randint(0, 100)
    duration = random.randint(8, 16)
    size = random.uniform(0.9, 1.8)
    delay = random.uniform(0, 5)
    st.markdown(
        f"<div class='snowflake' style='left:{left}vw; animation-duration:{duration}s; font-size:{size}em; animation-delay:{delay}s;'>❄</div>",
        unsafe_allow_html=True
    )

# --- 전체화면 지도 클릭 ---
st.markdown("""
<script>
    let mapClicked = false;
    document.addEventListener('click', function(e) {
        if (e.target.closest('.folium-map')) {
            if (!mapClicked) {
                const map = e.target.closest('.folium-map');
                map.classList.add('fullscreen-map');
                mapClicked = true;
            } else {
                const map = document.querySelector('.fullscreen-map');
                if (map) map.classList.remove('fullscreen-map');
                mapClicked = false;
            }
        }
    });
</script>
""", unsafe_allow_html=True)

# --- 7. 제목 ---
st.markdown('# 칸타타 투어 2025 마하라스트라')

# --- 8. 사이드바 ---
with st.sidebar:
    lang_map = {"한국어": "ko", "English": "en", "हिंदी": "hi"}
    sel = st.selectbox("언어", list(lang_map.keys()),
                       index=list(lang_map.values()).index(st.session_state.lang))
    if lang_map[sel] != st.session_state.lang:
        st.session_state.lang = lang_map[sel]
        st.session_state.tab_selection = _(f"tab_notice")
        st.rerun()

    st.markdown("---")
    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password", key="pw")
        if st.button("로그인", key="login"):
            if pw == st.session_state.password:
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃", key="logout"):
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
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("변경"):
                        if current_pw == "0691":
                            if new_pw == confirm_pw and new_pw:
                                st.session_state.password = new_pw
                                st.success(_(f"pw_changed"))
                                st.session_state.show_pw_form = False
                                st.rerun()
                            else:
                                st.error(_(f"pw_mismatch"))
                        else:
                            st.error(_(f"pw_error"))
                with col2:
                    if st.form_submit_button("취소"):
                        st.session_state.show_pw_form = False
                        st.rerun()

# --- 9. JSON 헬퍼 ---
def load_json(f):
    return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []

def save_json(f, d):
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 10. 초기 도시 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도",
     "google_link": "https://goo.gl/maps/abc123", "indoor": False, "date": "11/07 02:01"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브",
     "google_link": "https://goo.gl/maps/def456", "indoor": True, "date": "11/07 02:01"},
    {"city": "Pune", "venue": "Aga Khan Palace", "seats": "2500", "note": "역사적 장소",
     "google_link": "https://goo.gl/maps/pune2", "indoor": False, "date": "11/08 14:00"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시",
     "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "date": "11/07 02:01"}
]
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

# --- 11. 좌표 ---
CITY_COORDS = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882)
}

# --- 12. 공지 기능 ---
def add_notice(title, content, img=None, file=None):
    img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
    if img:
        with open(img_path, "wb") as f:
            f.write(img.getbuffer())
    if file:
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
    notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
        "image": img_path,
        "file": file_path
    }
    data = load_json(NOTICE_FILE)
    data.insert(0, notice)
    save_json(NOTICE_FILE, data)

    st.session_state.new_notice = True
    st.session_state.alert_active = True
    st.session_state.current_alert_id = notice["id"]
    st.session_state.sound_played = False
    play_carol()
    st.rerun()

def format_notice_date(d):
    try:
        dt = datetime.strptime(d, "%m/%d %H:%M")
        today = date.today()
        if dt.date() == today:
            return f"{_(f'today')} {dt.strftime('%H:%M')}"
        elif dt.date() == today - timedelta(days=1):
            return f"{_(f'yesterday')} {dt.strftime('%H:%M')}"
        else:
            return d
    except:
        return d

def render_notices():
    data = load_json(NOTICE_FILE)
    for i, n in enumerate(data):
        formatted_date = format_notice_date(n['date'])
        title = f"{formatted_date} | {n['title']}"
        exp_key = f"notice_{n['id']}"
        expanded = exp_key in st.session_state.expanded_notices

        with st.expander(title, expanded=expanded):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_column_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                b64 = base64.b64encode(open(n["file"], "rb").read()).decode()
                href = f'<a href="data:file/txt;base64,{b64}" download="{os.path.basename(n["file"])}">다운로드</a>'
                st.markdown(href, unsafe_allow_html=True)

            if st.session_state.admin and st.button("삭제", key=f"del_n_{n['id']}"):
                data.pop(i)
                save_json(NOTICE_FILE, data)
                st.rerun()

            if not st.session_state.admin and n["id"] not in st.session_state.seen_notices and expanded:
                st.session_state.seen_notices.append(n["id"])
                if n["id"] == st.session_state.current_alert_id:
                    st.session_state.alert_active = False
                st.rerun()

            if expanded and exp_key not in st.session_state.expanded_notices:
                st.session_state.expanded_notices.append(exp_key)
            elif not expanded and exp_key in st.session_state.expanded_notices:
                st.session_state.expanded_notices.remove(exp_key)

    if not st.session_state.admin and st.session_state.alert_active and st.session_state.current_alert_id:
        play_carol()
        st.markdown(f"""
        <div class="alert-box" id="alert">
            <span>{_("new_notice_alert")}</span>
            <span class="alert-close" onclick="document.getElementById('alert').remove()">X</span>
        </div>
        <script>
            setTimeout(() => {{
                if (document.getElementById('alert')) {{
                    document.querySelector('[data-testid="stRadio"] input[value="{_(f'tab_notice')}"]').click();
                }}
            }}, 100);
        </script>
        """, unsafe_allow_html=True)

# --- 13. 지도 함수 ---
def format_date_with_weekday(perf_date):
    if perf_date and perf_date != "9999-12-31":
        dt = datetime.strptime(perf_date, "%Y-%m-%d")
        weekday = dt.strftime("%A")
        if st.session_state.lang == "ko":
            weekdays = {"Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일", "Thursday": "목요일",
                        "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"}
            weekday = weekdays.get(weekday, weekday)
        return f"{perf_date} ({weekday})"
    return "미정"

def render_map():
    st.subheader("경로 보기")
    today = date.today()
    raw_cities = load_json(CITY_FILE)
    cities = sorted(raw_cities, key=lambda x: x.get("perf_date", "9999-12-31"))

    # 일반 도로 지도
    m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="OpenStreetMap")

    for i, c in enumerate(cities):
        is_past = (c.get('perf_date') and c['perf_date'] != "9999-12-31" and
                   datetime.strptime(c['perf_date'], "%Y-%m-%d").date() < today)
        color = "red" if not is_past else "gray"

        coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
        indoor_text = _(f"indoor") if c.get("indoor") else _(f"outdoor")
        perf_date_formatted = format_date_with_weekday(c.get("perf_date"))
        lat, lon = coords
        google_nav = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"

        popup_html = f"""
        <div style="font-size: 14px; line-height: 1.6;">
            <b>{c['city']}</b><br>
            날짜: <b>{perf_date_formatted}</b><br>
            장소: {c.get('venue','—')}<br>
            인원: {c.get('seats','—')}<br>
            유형: {indoor_text}
        </div>
        """
        folium.Marker(
            coords,
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=color, icon="music", prefix="fa")
        ).add_to(m)

        if i < len(cities) - 1:
            nxt = cities[i + 1]
            nxt_coords = CITY_COORDS.get(nxt["city"], (18.5204, 73.8567))
            opacity = 0.3 if is_past else 1.0
            AntPath([coords, nxt_coords], color="#e74c3c", weight=6, opacity=opacity, delay=800, dash_array=[20, 30]).add_to(m)

        exp_key = f"city_{c['city']}"
        expanded = exp_key in st.session_state.expanded_cities
        with st.expander(f"{c['city']} | {format_date_with_weekday(c.get('perf_date'))}", expanded=expanded):
            st.markdown(f"""
            <div><span style="font-weight:bold;color:#e74c3c;">장소:</span> {c.get('venue','—')}</div>
            <div><span style="font-weight:bold;color:#e74c3c;">인원:</span> {c.get('seats','—')}</div>
            <div><span style="font-weight:bold;color:#e74c3c;">유형:</span> {indoor_text}</div>
            <div><span style="font-weight:bold;color:#e74c3c;">특이사항:</span> {c.get('note','—')}</div>
            """, unsafe_allow_html=True)
            st.markdown(f"[길 안내 (Google Maps)]({google_nav})", unsafe_allow_html=True)

            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("수정", key=f"edit_{c['city']}"):
                        st.session_state.edit_city = c["city"]
                        st.rerun()
                with c2:
                    if st.button("삭제", key=f"del_{c['city']}"):
                        raw_cities = [x for x in raw_cities if x["city"] != c["city"]]
                        save_json(CITY_FILE, raw_cities)
                        st.rerun()

    st_folium(m, width=900, height=550, key="tour_map")

# --- 14. 탭 ---
col1, col2 = st.columns(2)
with col1:
    if st.button(_(f"tab_notice"), use_container_width=True):
        st.session_state.tab_selection = _(f"tab_notice")
        st.rerun()
with col2:
    if st.button(_(f"tab_map"), use_container_width=True):
        st.session_state.tab_selection = _(f"tab_map")
        st.rerun()

if st.session_state.tab_selection != st.session_state.get("last_tab"):
    st.session_state.expanded_notices = []
    st.session_state.expanded_cities = []
    st.session_state.last_tab = st.session_state.tab_selection
    st.rerun()

if st.session_state.get("new_notice", False):
    st.session_state.tab_selection = _(f"tab_notice")
    st.session_state.new_notice = False
    st.rerun()

# --- 15. 렌더링 ---
if st.session_state.tab_selection == _(f"tab_notice"):
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            title = st.text_input("제목")
            content = st.text_area("내용")
            img = st.file_uploader("이미지", type=["png", "jpg", "jpeg"])
            file = st.file_uploader("첨부 파일")
            if st.form_submit_button("등록"):
                if title.strip() and content.strip():
                    add_notice(title, content, img, file)
                else:
                    st.warning(_("warning"))
    render_notices()
else:
    render_map()
