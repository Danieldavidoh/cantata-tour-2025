# app.py
import streamlit as st
from datetime import datetime, date
import json, os, uuid, base64, re, requests
from pytz import timezone
import streamlit.components.v1 as components

# =============================================
# 1. 설정 + 강제 라이트 모드
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

# Google Maps API 키 입력 (보안 위해 세션에 저장)
if "gmaps_api_key" not in st.session_state:
    st.session_state.gmaps_api_key = ""

st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"] { background: white !important; }
    h1,h2,h3,p,div,span,label { color: black !important; }
    .stTextInput > div > div > input, .stTextArea textarea { background: white !important; color: black !important; }
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

defaults = {"admin": False, "lang": "ko", "edit_index": None}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# =============================================
# 3. 시간 + 다국어
# =============================================
india_time = datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
st.markdown(f"<p style='text-align:right;color:#666;font-size:0.9rem;'>Mumbai {india_time}</p>", unsafe_allow_html=True)

LANG = {
    "ko": { "title": "칸타타 투어 2025", "tab_map": "투어 경로", "select_city": "도시 선택", "venue": "공연장소", "seats": "좌석수",
            "indoor": "실내", "outdoor": "실외", "google_link": "구글맵 링크", "note": "특이사항", "register": "등록", "save": "저장",
            "date": "날짜", "tour_list": "투어 일정", "map_title": "Google Maps 경로" },
    "en": { "title": "Cantata Tour 2025", "tab_map": "Route", "select_city": "City", "venue": "Venue", "seats": "Seats",
            "indoor": "Indoor", "outdoor": "Outdoor", "google_link": "Maps Link", "note": "Notes", "register": "Add", "save": "Save",
            "date": "Date", "tour_list": "Schedule", "map_title": "Google Maps Route" },
}
_ = LANG[st.session_state.lang]

# =============================================
# 4. 유틸
# =============================================
def load_json(f): return json.load(open(f,"r",encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def extract_latlon(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=5)
        m = re.search(r'@([0-9\.\-]+),([0-9\.\-]+)', r.url)
        return float(m.group(1)), float(m.group(2)) if m else (None, None)
    except: return None, None

# =============================================
# 5. Google Maps HTML 생성
# =============================================
def render_google_map(data, api_key):
    if not api_key:
        return "<p style='color:red;'>Google Maps API 키를 입력하세요.</p>"

    markers = ""
    waypoints = ""
    origin = None
    destination = None

    for i, c in enumerate(data):
        lat, lon = c["lat"], c["lon"]
        title = f"{c['city']} | {c.get('date','?')} | {c.get('venue','')} | {c['seats']}석 | {c['type']}"
        markers += f"""
        new google.maps.Marker({{
            position: {{lat: {lat}, lng: {lon}}},
            map: map,
            title: "{title}",
            icon: {{ url: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png' }}
        }});
        """
        if i == 0:
            origin = f"{lat},{lon}"
        elif i == len(data) - 1:
            destination = f"{lat},{lon}"
        else:
            waypoints += f"|via:{lat},{lon}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" async defer></script>
        <style> #map {{ height: 100%; width: 100%; }} html, body {{ height: 100%; margin: 0; }} </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            let map;
            function initMap() {{
                map = new google.maps.Map(document.getElementById("map"), {{
                    zoom: 6,
                    center: {{lat: 19.0, lng: 73.0}},
                    mapTypeId: 'roadmap'
                }});
                {markers}
                const directionsService = new google.maps.DirectionsService();
                const directionsRenderer = new google.maps.DirectionsRenderer({{
                    polylineOptions: {{ strokeColor: '#ff1744', strokeWeight: 5 }},
                    suppressMarkers: true
                }});
                directionsRenderer.setMap(map);
                directionsService.route({{
                    origin: "{origin}",
                    destination: "{destination}",
                    waypoints: [{{
                        location: new google.maps.LatLng({data[1]["lat"]}, {data[1]["lon"]}) 
                    }}] || [],
                    travelMode: 'DRIVING'
                }}, (result, status) => {{
                    if (status === 'OK') directionsRenderer.setDirections(result);
                }});
            }}
        </script>
    </body>
    </html>
    """
    return html

# =============================================
# 6. 지도 + 투어 관리
# =============================================
def render_map():
    st.subheader(_["map_title"])

    # API 키 입력 (최초 1회)
    if not st.session_state.gmaps_api_key:
        with st.form("api_form"):
            key = st.text_input("Google Maps API 키 입력", type="password")
            if st.form_submit_button("저장"):
                if key:
                    st.session_state.gmaps_api_key = key
                    st.success("API 키 저장됨")
                    st.rerun()
                else:
                    st.error("키를 입력하세요")
        return

    # 데이터 보정
    data = load_json(CITY_FILE)
    today = date.today().strftime("%Y-%m-%d")
    for d in data: d.setdefault("date", today)

    if st.session_state.admin:
        with st.expander("투어 추가/수정", expanded=bool(st.session_state.edit_index)):
            cities = load_json(CITY_LIST_FILE) or ["Mumbai", "Pune"]
            edit_idx = st.session_state.edit_index
            edit = data[edit_idx] if edit_idx is not None and edit_idx < len(data) else None

            city_opt = cities + ["+ 새 도시"]
            sel_city = st.selectbox(_("select_city"), city_opt, key="city")
            city = st.text_input("도시명", edit["city"] if edit else "") if sel_city == "+ 새 도시" else sel_city

            tour_date = st.date_input(_("date"), value=datetime.strptime(edit["date"], "%Y-%m-%d").date() if edit else date.today())
            venue = st.text_input(_("venue"), edit.get("venue", "") if edit else "")
            seats = st.number_input(_("seats"), 0, step=50, value=edit.get("seats", 0) if edit else 0)
            vtype = st.radio("형태", [_["indoor"], _["outdoor"]], horizontal=True, index=0 if edit and edit.get("type") == _["indoor"] else 1)
            map_link = st.text_input(_("google_link"), edit.get("map_link", "") if edit else "")
            note = st.text_area(_("note"), edit.get("note", "") if edit else "")

            if st.button(_["save"] if edit_idx else _["register"]):
                if not city: st.warning("도시 입력"); return
                lat, lon = extract_latlon(map_link)
                if not lat: st.warning("맵 링크 확인"); return
                entry = { "city": city, "date": tour_date.strftime("%Y-%m-%d"), "venue": venue, "seats": seats, "type": vtype,
                          "note": note, "lat": lat, "lon": lon, "map_link": map_link }
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
            st.info("등록된 투어 없음")
        else:
            for i, c in enumerate(sorted(data, key=lambda x: x["date"])):
                with st.expander(f"{c['city']} | {c['date']} | {c['venue']}"):
                    st.markdown(f"**길안내**: [Google Maps]({c['map_link']})")
                    st.markdown(f"**특이사항**: {c['note']}")
                    c1, c2 = st.columns(2)
                    if c1.button("수정", key=f"e{i}"):
                        st.session_state.edit_index = data.index(c)
                        st.rerun()
                    if c2.button("삭제", key=f"d{i}"):
                        data.remove(c)
                        save_json(CITY_FILE, data)
                        st.rerun()

    # Google Maps 렌더링
    if data:
        map_html = render_google_map(data, st.session_state.gmaps_api_key)
        components.html(map_html, height=600)
    else:
        st.info("추가된 도시가 없으면 지도가 표시되지 않습니다.")

# =============================================
# 7. 사이드바 + 메인
# =============================================
with st.sidebar:
    lang_map = {"한국어": "ko", "English": "en"}
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
        st.success("관리자")
        if st.button("로그아웃"):
            st.session_state.admin = False
            st.rerun()

st.markdown(f"# {_['title']} 크리스마스")
t1, t2 = st.tabs(["공지", _["tab_map"]])

with t1:
    if st.session_state.admin:
        with st.form("nf"):
            t = st.text_input("제목")
            c = st.text_area("내용")
            if st.form_submit_button("등록") and t and c:
                # 공지 저장 로직 (간소화)
                pass
    st.write("공지 목록")

with t2:
    render_map()
