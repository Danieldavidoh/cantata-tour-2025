import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
import requests

# --- 1. 기본 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh_user")

# --- 2. 파일 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 3. 다국어 ---
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

defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "adding_city": False,
    "tab_selection": "공지", "new_notice": False, "sound_played": False,
    "seen_notices": [], "expanded_notices": [], "expanded_cities": [],
    "last_tab": None, "alert_active": False, "current_alert_id": None,
    "password": "0009", "show_pw_form": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 4. 캐롤 사운드 (강제 재생 보장) ---
def play_carol():
    if os.path.exists("carol.wav"):
        st.session_state.sound_played = True
        st.markdown(f"""
        <audio autoplay>
            <source src="carol.wav" type="audio/wav">
        </audio>
        """, unsafe_allow_html=True)

# --- 5. 알림 CSS + 아이콘 스타일 ---
st.markdown("""
<style>
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
    
    .city-label {
        color: #e74c3c !important;
        font-weight: bold;
        font-size: 1.1em;
    }
    .city-icon {
        margin-right: 8px;
        font-size: 1.2em;
    }
    
    /* 탭 아래로 내리기 */
    .main-title {
        margin-top: 40px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 6. 사이드바 ---
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

# --- 7. JSON 헬퍼 ---
def load_json(f):
    return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []

def save_json(f, d):
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 8. 초기 도시 ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도",
     "google_link": "https://goo.gl/maps/abc123", "indoor": False, "date": "11/07 02:01"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브",
     "google_link": "https://goo.gl/maps/def456", "indoor": True, "date": "11/07 02:01"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시",
     "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "date": "11/07 02:01"}
]
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

# --- 9. 하드코딩 좌표 ---
CITY_COORDS = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882)
}

# --- 10. 공지 기능 ---
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

    # 일반 사용자용 알림 강제 활성화
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
            return _(f"today")
        elif dt.date() == today - timedelta(days=1):
            return _(f"yesterday")
        else:
            return d  # 숫자로 표시
    except:
        return d

def render_notices():
    data = load_json(NOTICE_FILE)
    
    for i, n in enumerate(data):
        is_new = False
        if st.session_state.admin:
            badge = ''
        else:
            if n["id"] not in st.session_state.seen_notices:
                is_new = True
                badge = ' NEW'
            else:
                badge = ''

        formatted_date = format_notice_date(n['date'])
        title = f"{formatted_date} | {n['title']}{badge}"
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

            # 일반 사용자: 열 때 NEW 제거 + 알림 해제
            if not st.session_state.admin and is_new and expanded:
                if n["id"] not in st.session_state.seen_notices:
                    st.session_state.seen_notices.append(n["id"])
                if n["id"] == st.session_state.current_alert_id:
                    st.session_state.alert_active = False
                st.rerun()

            if expanded and exp_key not in st.session_state.expanded_notices:
                st.session_state.expanded_notices.append(exp_key)
            elif not expanded and exp_key in st.session_state.expanded_notices:
                st.session_state.expanded_notices.remove(exp_key)

    # 알림 팝업 (일반 사용자만 + 강제 표시)
    if not st.session_state.admin and st.session_state.alert_active and st.session_state.current_alert_id:
        play_carol()  # 사운드 강제 재생
        st.markdown(f"""
        <div class="alert-box" id="alert">
            <span>{_("new_notice_alert")}</span>
            <span class="alert-close" onclick="document.getElementById('alert').remove()">×</span>
        </div>
        <script>
            setTimeout(() => {{
                if (document.getElementById('alert')) {{
                    document.querySelector('[data-testid="stRadio"] input[value="{_(f'tab_notice')}"]').click();
                }}
            }}, 100);
        </script>
        """, unsafe_allow_html=True)

# --- 11. 지도 + 도시 추가/수정 ---
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
    city_names = [c["city"] for c in raw_cities]

    # --- 도시 추가 폼 ---
    if st.session_state.admin:
        if st.button(_(f"add_city"), key="add_city_btn"):
            st.session_state.adding_city = True

        if st.session_state.get("adding_city"):
            st.markdown("### 새 도시 추가")
            with st.form("add_city_form"):
                selected_city = st.selectbox(_(f"select_city"), options=city_names + ["<새 도시 입력>"])
                if selected_city == "<새 도시 입력>":
                    new_city = st.text_input("새 도시명")
                else:
                    new_city = selected_city

                venue = st.text_input(_(f"venue"))
                seats = st.text_input(_(f"seats"))
                indoor = st.radio("장소 유형", [_(f"indoor"), _(f"outdoor")])
                note = st.text_area(_(f"note"))
                google_link = st.text_input(_(f"google_link"))
                perf_date_input = st.date_input(_(f"perf_date"), value=None)
                perf_date = perf_date_input.strftime("%Y-%m-%d") if perf_date_input else None

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button(_(f"save")):
                        if new_city and new_city not in city_names:
                            new_data = {
                                "city": new_city, "venue": venue, "seats": seats,
                                "indoor": indoor == _(f"indoor"), "note": note,
                                "google_link": google_link,
                                "perf_date": perf_date,
                                "date": datetime.now().strftime("%m/%d %H:%M")
                            }
                            raw_cities.append(new_data)
                            save_json(CITY_FILE, raw_cities)
                            st.session_state.adding_city = False
                            st.success("도시 추가 완료!")
                            st.rerun()
                        else:
                            st.error("도시명 중복 또는 비어있음")
                with col2:
                    if st.form_submit_button(_(f"cancel")):
                        st.session_state.adding_city = False
                        st.rerun()

    # --- 도시 수정 폼 ---
    if st.session_state.admin and st.session_state.get("edit_city"):
        city_to_edit = next((c for c in raw_cities if c["city"] == st.session_state.edit_city), None)
        if city_to_edit:
            st.markdown("### 도시 정보 수정")
            with st.form("edit_city_form"):
                city = st.selectbox("도시 선택", options=city_names,
                                    index=city_names.index(st.session_state.edit_city))
                venue = st.text_input(_(f"venue"), value=city_to_edit["venue"])
                seats = st.text_input(_(f"seats"), value=city_to_edit["seats"])
                indoor = st.radio("장소 유형", [_(f"indoor"), _(f"outdoor")],
                                  index=0 if city_to_edit.get("indoor", False) else 1)
                note = st.text_area(_(f"note"), value=city_to_edit.get("note", ""))
                google_link = st.text_input(_(f"google_link"), value=city_to_edit.get("google_link", ""))
                perf_date_input = st.date_input(_(f"perf_date"), value=(
                    datetime.strptime(city_to_edit["perf_date"], "%Y-%m-%d").date()
                    if city_to_edit.get("perf_date") and city_to_edit["perf_date"] != "9999-12-31"
                    else None
                ))
                perf_date = perf_date_input.strftime("%Y-%m-%d") if perf_date_input else None

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button(_(f"save")):
                        updated = {
                            "city": city, "venue": venue, "seats": seats,
                            "indoor": indoor == _(f"indoor"), "note": note,
                            "google_link": google_link,
                            "perf_date": perf_date,
                            "date": city_to_edit["date"]
                        }
                        raw_cities = [updated if c["city"] == st.session_state.edit_city else c for c in raw_cities]
                        save_json(CITY_FILE, raw_cities)
                        st.session_state.edit_city = None
                        st.success("수정 완료!")
                        st.rerun()
                with col2:
                    if st.form_submit_button(_(f"cancel")):
                        st.session_state.edit_city = None
                        st.rerun()

    # --- 지도 ---
    m = folium.Map(location=[18.5204, 73.8567], zoom_start=7, tiles="CartoDB positron")

    for i, c in enumerate(cities):
        is_past = (c.get('perf_date') and c['perf_date'] != "9999-12-31" and
                   datetime.strptime(c['perf_date'], "%Y-%m-%d").date() < today)
        color = "red" if not is_past else "gray"

        # 수정: 올바른 좌표 추출
        coords = CITY_COORDS.get(c["city"], (18.5204, 73.8567))
        indoor_text = _(f"indoor") if c.get("indoor") else _(f"outdoor")
        perf_date_formatted = format_date_with_weekday(c.get("perf_date"))
        popup_html = f"""
        <b>{c['city']}</b><br>
        {perf_date_formatted}<br>
        {c.get('venue','—')}<br>
        유형: {indoor_text}
        """
        folium.Marker(
            coords,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=c["city"],
            icon=folium.Icon(color=color, icon="music", prefix="fa")
        ).add_to(m)

        if i < len(cities) - 1:
            nxt = cities[i + 1]
            nxt_coords = CITY_COORDS.get(nxt["city"], (18.5204, 73.8567))
            opacity = 0.3 if is_past else 1.0
            AntPath([coords, nxt_coords],
                    color="#e74c3c", weight=6, opacity=opacity, delay=800, dash_array=[20, 30]).add_to(m)

        exp_key = f"city_{c['city']}"
        expanded = exp_key in st.session_state.expanded_cities
        with st.expander(f"{c['city']} | {format_date_with_weekday(c.get('perf_date'))}", expanded=expanded):
            # 수정: 중괄호 이스케이프 문제 해결
            indoor_icon = "🏠" if c.get("indoor") else "🌳"
            st.markdown(f"""
            <div>
                <span class="city-icon">📍</span>
                <span class="city-label">{_(f'venue')}:</span> {c.get('venue','—')}
            </div>
            <div>
                <span class="city-icon">👥</span>
                <span class="city-label">{_(f'seats')}:</span> {c.get('seats','—')}
            </div>
            <div>
                <span class="city-icon">{indoor_icon}</span>
                <span class="city-label">유형:</span> {indoor_text}
            </div>
            <div>
                <span class="city-icon">📝</span>
                <span class="city-label">{_(f'note')}:</span> {c.get('note','—')}
            </div>
            """, unsafe_allow_html=True)

            if c.get("google_link"):
                st.markdown(f"[구글맵 보기]({c['google_link']})")

            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(_(f"edit"), key=f"edit_{c['city']}"):
                        st.session_state.edit_city = c["city"]
                        st.rerun()
                with c2:
                    if st.button("삭제", key=f"del_{c['city']}"):
                        raw_cities = [x for x in raw_cities if x["city"] != c["city"]]
                        save_json(CITY_FILE, raw_cities)
                        st.rerun()

            if expanded and exp_key not in st.session_state.expanded_cities:
                st.session_state.expanded_cities.append(exp_key)
            elif not expanded and exp_key in st.session_state.expanded_cities:
                st.session_state.expanded_cities.remove(exp_key)

    st_folium(m, width=900, height=550, key="tour_map")

# --- 12. 탭 ---
tab_selection = st.radio(
    "탭 선택",
    [_(f"tab_notice"), _(f"tab_map")],
    index=0 if st.session_state.tab_selection == _(f"tab_notice") else 1,
    horizontal=True,
    key="main_tab"
)

if tab_selection != st.session_state.get("last_tab"):
    st.session_state.expanded_notices = []
    st.session_state.expanded_cities = []
    st.session_state.last_tab = tab_selection
    st.rerun()

if st.session_state.get("new_notice", False):
    st.session_state.tab_selection = _(f"tab_notice")
    st.session_state.new_notice = False
    st.rerun()

# --- 13. 렌더링 (제목 아래로 내림) ---
st.markdown('<div class="main-title"># 칸타타 투어 2025 마하라스트라</div>', unsafe_allow_html=True)

if tab_selection == _(f"tab_notice"):
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
