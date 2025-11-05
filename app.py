# app.py
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone

# =============================================
# 1. 강제 라이트 모드 + 안정화 CSS
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

st.markdown("""
<style>
    /* 전체 배경 강제 흰색 */
    .stApp, [data-testid="stAppViewContainer"], .css-1d391kg, .css-1v0mbdj {
        background-color: white !important;
        background-image: none !important;
    }
    /* 텍스트 강제 검정 */
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown, .stText {
        color: black !important;
    }
    /* 입력창 배경/글자 */
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox > div > div,
    .stDateInput > div > div {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ccc !important;
    }
    /* 버튼 */
    .stButton > button {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    /* 지도 안 깨지게 */
    iframe {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# 2. 파일/세션 초기화
# =============================================
NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

defaults = {
    "admin": False,
    "lang": "ko",
    "edit_index": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================================
# 3. 시간 + 다국어
# =============================================
india_time = datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
st.markdown(f"<p style='text-align:right;color:#666;font-size:0.9rem;'>🕓 {india_time} (Mumbai)</p>", unsafe_allow_html=True)

LANG = {
    "ko": { "title": "칸타타 투어 2025", "caption": "마하라스트라 투어 관리", "tab_notice": "공지", "tab_map": "투어 경로",
            "select_city": "도시 선택", "venue": "공연장소", "seats": "좌석수", "indoor": "실내", "outdoor": "실외",
            "google_link": "구글맵 링크", "note": "특이사항", "register": "등록", "save": "저장", "edit": "수정", "delete": "삭제",
            "date": "날짜", "tour_list": "투어 일정", "no_tour": "등록된 투어 없음", "map_title": "경로 보기" },
    "en": { "title": "Cantata Tour 2025", "caption": "Maharashtra Tour", "tab_notice": "Notices", "tab_map": "Route",
            "select_city": "Select City", "venue": "Venue", "seats": "Seats", "indoor": "Indoor", "outdoor": "Outdoor",
            "google_link": "Google Maps Link", "note": "Notes", "register": "Register", "save": "Save", "edit": "Edit", "delete": "Delete",
            "date": "Date", "tour_list": "Tour Schedule", "no_tour": "No tour yet", "map_title": "View Route" },
    "hi": { "title": "कांताता टूर 2025", "caption": "महाराष्ट्र टूर", "tab_notice": "सूचनाएँ", "tab_map": "मार्ग",
            "select_city": "शहर चुनें", "venue": "स्थल", "seats": "सीटें", "indoor": "इनडोर", "outdoor": "आउटडोर",
            "google_link": "गूगल मैप लिंक", "note": "टिप्पणियाँ", "register": "पंजीकृत करें", "save": "सहेजें", "edit": "संपादित करें", "delete": "हटाएं",
            "date": "तारीख", "tour_list": "टूर शेड्यूल", "no_tour": "कोई टूर नहीं", "map_title": "मार्ग देखें" },
}
_ = LANG[st.session_state.lang]

# =============================================
# 4. 유틸 함수
# =============================================
def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def extract_latlon(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=5)
        m = re.search(r'@([0-9\.\-]+),([0-9\.\-]+)', r.url)
        return float(m.group(1)), float(m.group(2)) if m else (None, None)
    except: return None, None

def nav_link(lat, lon):
    ua = st.context.headers.get("User-Agent", "") if hasattr(st, "context") else ""
    if "Android" in ua: return f"google.navigation:q={lat},{lon}"
    if "iPhone" in ua or "iPad" in ua: return f"comgooglemaps://?daddr={lat},{lon}&directionsmode=driving"
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

# =============================================
# 5. 공지 기능 (간소화)
# =============================================
def add_notice(t, c, img=None, file=None):
    img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
    if img_path: open(img_path, "wb").write(img.read())
    if file_path: open(file_path, "wb").write(file.read())
    notice = {"id": str(uuid.uuid4()), "title": t, "content": c, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
              "image": img_path, "file": file_path}
    data = load_json(NOTICE_FILE)
    data.insert(0, notice)
    save_json(NOTICE_FILE, data)
    st.toast("공지 등록됨")

def render_notices():
    data = load_json(NOTICE_FILE)
    if not data: st.info("공지 없음"); return
    for i, n in enumerate(data):
        with st.expander(f"{n['date']} | {n['title']}"):
            st.markdown(n["content"])
            if n.get("image"): st.image(n["image"])
            if n.get("file"):
                b64 = base64.b64encode(open(n["file"],"rb").read()).decode()
                st.markdown(f'<a href="data:file/octet-stream;base64,{b64}" download>파일 다운로드</a>', unsafe_allow_html=True)
            if st.session_state.admin and st.button("삭제", key=f"deln_{i}"):
                data.pop(i)
                save_json(NOTICE_FILE, data)
                st.rerun()

# =============================================
# 6. 지도 + 투어 관리 (완벽 안정화)
# =============================================
def render_map():
    st.subheader(_["map_title"])

    # 데이터 보정
    data = load_json(CITY_FILE)
    today = date.today().strftime("%Y-%m-%d")
    for d in data:
        d.setdefault("date", today)
        d.setdefault("venue", "")
        d.setdefault("seats", 0)
        d.setdefault("type", _["indoor"])
        d.setdefault("note", "")
    save_json(CITY_FILE, data)

    if st.session_state.admin:
        with st.expander("투어 추가/수정", expanded=bool(st.session_state.edit_index is not None)):
            cities = load_json(CITY_LIST_FILE) or ["Mumbai", "Pune", "Nagpur"]
            edit_idx = st.session_state.edit_index
            edit = data[edit_idx] if edit_idx is not None and edit_idx < len(data) else None

            city_opt = cities + ["+ 새 도시"]
            sel_city = st.selectbox(_("select_city"), city_opt, index=city_opt.index(edit["city"]) if edit and edit["city"] in city_opt else 0, key="city_sel")
            city = st.text_input("도시명", edit["city"] if edit else "") if sel_city == "+ 새 도시" else sel_city

            tour_date = st.date_input(_("date"), value=datetime.strptime(edit["date"], "%Y-%m-%d").date() if edit else date.today(), key="date_in")
            venue = st.text_input(_("venue"), edit["venue"] if edit else "", key="venue_in")
            seats = st.number_input(_("seats"), 0, step=50, value=edit["seats"] if edit else 0, key="seats_in")
            vtype = st.radio("형태", [_["indoor"], _["outdoor"]], horizontal=True, index=0 if (edit and edit["type"] == _["indoor"]) else 1, key="type_in")
            map_link = st.text_input(_("google_link"), edit.get("map_link", "") if edit else "", key="link_in")
            note = st.text_area(_("note"), edit["note"] if edit else "", key="note_in")

            if st.button(_["save"] if edit_idx is not None else _["register"], key="save_btn"):
                if not city: st.warning("도시 입력"); return
                lat, lon = extract_latlon(map_link)
                if not lat: st.warning("맵 링크 확인"); return
                nav = nav_link(lat, lon)
                entry = {"city": city, "date": tour_date.strftime("%Y-%m-%d"), "venue": venue, "seats": seats, "type": vtype,
                         "note": note, "lat": lat, "lon": lon, "nav_url": nav, "map_link": map_link}
                if edit_idx is not None:
                    data[edit_idx] = entry
                    st.session_state.edit_index = None
                else:
                    data.append(entry)
                data.sort(key=lambda x: x["date"])
                if city not in cities: cities.append(city); save_json(CITY_LIST_FILE, cities)
                save_json(CITY_FILE, data)
                st.success("저장됨")
                st.rerun()

        st.subheader(_["tour_list"])
        if not data:
            st.info(_["no_tour"])
        else:
            for i, c in enumerate(sorted(data, key=lambda x: x["date"])):
                with st.expander(f"{c['city']} | {c['date']} | {c['venue']} | {c['seats']}석 | {c['type']}"):
                    st.markdown(f"**길안내**: [{c['nav_url']}]({c['nav_url']})")
                    st.markdown(f"**특이사항**: {c['note']}")
                    c1, c2 = st.columns(2)
                    if c1.button("수정", key=f"edit_{i}_{c['date']}"):
                        st.session_state.edit_index = data.index(c)
                        st.rerun()
                    if c2.button("삭제", key=f"del_{i}_{c['date']}"):
                        data.remove(c)
                        save_json(CITY_FILE, data)
                        st.rerun()

    # 지도
    m = folium.Map([19.0, 73.0], zoom_start=6, tiles="CartoDB positron")
    coords = []
    for c in data:
        popup = f"<div style='text-align:center;white-space:nowrap;padding:8px;min-width:400px;font-size:13px;'><b>{c['city']}</b> | {c['date']} | {c['venue']} | {c['seats']}석 | {c['type']}</div>"
        folium.Marker([c["lat"], c["lon"]], popup=folium.Popup(popup, max_width=500), tooltip=c["city"],
                      icon=folium.Icon(color="red", icon="music", prefix="fa")).add_to(m)
        coords.append((c["lat"], c["lon"]))
    if len(coords) > 1:
        AntPath(coords, color="#ff1744", weight=5, opacity=0.8, delay=800).add_to(m)
    st_folium(m, width=900, height=550, key="map_unique")

# =============================================
# 7. 사이드바 + 메인
# =============================================
with st.sidebar:
    lang_map = {"한국어": "ko", "English": "en", "हिन्दी": "hi"}
    sel = st.selectbox("언어", list(lang_map.keys()), index=list(lang_map.values()).index(st.session_state.lang))
    if lang_map[sel] != st.session_state.lang:
        st.session_state.lang = lang_map[sel]
        st.rerun()

    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인") and pw == "0000":
            st.session_state.admin = True
            st.rerun()
    else:
        st.success("관리자 ON")
        if st.button("로그아웃"):
            st.session_state.admin = False
            st.rerun()

st.markdown(f"# {_['title']} 크리스마스")
st.caption(_["caption"])
t1, t2 = st.tabs([_["tab_notice"], _["tab_map"]])

with t1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input("제목")
            c = st.text_area("내용")
            img = st.file_uploader("이미지", type=["png","jpg"])
            f = st.file_uploader("파일")
            if st.form_submit_button("등록") and t and c:
                add_notice(t, c, img, f)
        render_notices()
    else:
        render_notices()
        st.button("새로고침", on_click=st.rerun)

with t2:
    render_map()
