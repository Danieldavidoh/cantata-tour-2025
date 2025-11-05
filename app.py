# app.py - Spicy Fix: No More TypeError Bullshit
import streamlit as st
from datetime import datetime, date
import json, os, uuid, base64, re, requests
from pytz import timezone
import streamlit.components.v1 as components

# =============================================
# 1. 설정 + CSS (라이트 모드 강제)
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"] { background: white !important; }
    h1,h2,h3,p,div,span,label { color: black !important; }
    .stTextInput > div > div > input, .stTextArea textarea { background: white !important; color: black !important; }
    .stButton > button { background: #ff4b4b !important; color: white !important; }
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

defaults = {"admin": False, "lang": "ko", "edit_index": None, "gmaps_api_key": ""}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# =============================================
# 3. 다국어 (글로벌 업데이트)
# =============================================
def get_lang(lang_code):
    return {
        "ko": { "title": "칸타타 투어 2025", "tab_map": "투어 경로", "select_city": "도시 선택", "venue": "공연장소", "seats": "좌석수",
                "indoor": "실내", "outdoor": "실외", "google_link": "구글맵 링크", "note": "특이사항", "register": "등록", "save": "저장",
                "date": "날짜", "tour_list": "투어 일정", "map_title": "Google Maps 경로", "no_tour": "투어 없음" },
        "en": { "title": "Cantata Tour 2025", "tab_map": "Route", "select_city": "City", "venue": "Venue", "seats": "Seats",
                "indoor": "Indoor", "outdoor": "Outdoor", "google_link": "Maps Link", "note": "Notes", "register": "Add", "save": "Save",
                "date": "Date", "tour_list": "Schedule", "map_title": "Google Maps Route", "no_tour": "No tour" },
    }.get(lang_code, {})

# =============================================
# 4. 유틸
# =============================================
def load_json(f): return json.load(open(f,"r",encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def extract_latlon(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=5)
        m = re.search(r'@([0-9\.\-]+),([0-9\.\-]+)', r.url)
        return (float(m.group(1)), float(m.group(2))) if m else (None, None)
    except: return None, None

# =============================================
# 5. Google Maps HTML (waypoints 동적 생성)
# =============================================
def render_google_map(data, api_key):
    if not data or not api_key: return "<p>지도 로드 실패: 데이터 또는 API 키 확인.</p>"

    markers_js = ""
    waypoints_js = ""
    origin = f"{data[0]['lat']},{data[0]['lon']}"
    destination = f"{data[-1]['lat']},{data[-1]['lon']}"

    for i, c in enumerate(data):
        lat, lon = c["lat"], c["lon"]
        title = f"{c['city']} | {c.get('date','?')} | {c.get('venue','')} | {c['seats']}석 | {c['type']}"
        markers_js += f"""
        new google.maps.Marker({{
            position: {{lat: {lat}, lng: {lon}}},
            map: map,
            title: "{title.replace('"', '\\"')}",
            icon: {{ url: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png' }}
        }});
        """
        if 0 < i < len(data) - 1:
            waypoints_js += f"{{location: new google.maps.LatLng({lat}, {lon}), stopover: true}}," 

    html = f"""
    <!DOCTYPE html>
    <html><head>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" async defer></script>
        <style>#map {{ height: 100%; width: 100%; }} html,body {{ height: 100%; margin: 0; }}</style>
    </head><body>
        <div id="map"></div>
        <script>
            let map;
            function initMap() {{
                map = new google.maps.Map(document.getElementById("map"), {{
                    zoom: 6, center: {{lat: 19.0, lng: 73.0}}, mapTypeId: 'roadmap'
                }});
                {markers_js}
                const directionsService = new google.maps.DirectionsService();
                const directionsRenderer = new google.maps.DirectionsRenderer({{
                    polylineOptions: {{ strokeColor: '#ff1744', strokeWeight: 5 }},
                    suppressMarkers: true
                }});
                directionsRenderer.setMap(map);
                directionsService.route({{
                    origin: "{origin}",
                    destination: "{destination}",
                    waypoints: [ {waypoints_js.rstrip(',')} ],
                    travelMode: 'DRIVING'
                }}, (result, status) => {{
                    if (status === 'OK') directionsRenderer.setDirections(result);
                }});
            }}
        </script>
    </body></html>
    """
    return html

# =============================================
# 6. 지도 + 투어 관리 (TypeError 방지)
# =============================================
def render_map():
    lang = get_lang(st.session_state.lang)
    st.subheader(lang.get("map_title", "Google Maps Route"))

    # API 키 입력 (세션 기반)
    if not st.session_state.gmaps_api_key:
        with st.form("api_key_form", clear_on_submit=False):
            key = st.text_input("Google Maps API 키", type="password", key="api_input")
            if st.form_submit_button("저장", key="api_submit"):
                if key:
                    st.session_state.gmaps_api_key = key
                    st.success("API 키 저장됨 – 이제 지도 뜬다!")
                    st.rerun()
                else:
                    st.error("키를 제대로 입력해, 빈 거 아니야?")
        return

    # 데이터 로드 + 보정
    data = load_json(CITY_FILE)
    today = date.today().strftime("%Y-%m-%d")
    for d in data:
        d.setdefault("date", today)
        d.setdefault("venue", "")
        d.setdefault("seats", 0)
        d.setdefault("type", lang.get("indoor", "Indoor"))
        d.setdefault("note", "")
        if "lat" not in d or "lon" not in d:
            # 링크가 있으면 추출 (기존 데이터 보정)
            if d.get("map_link"):
                lat, lon = extract_latlon(d["map_link"])
                if lat: d["lat"], d["lon"] = lat, lon
    save_json(CITY_FILE, data)

    if st.session_state.admin:
        with st.expander("투어 추가/수정", expanded=bool(st.session_state.edit_index is not None)):
            cities = load_json(CITY_LIST_FILE) or ["Mumbai", "Pune"]
            edit_idx = st.session_state.get("edit_index")
            edit = {}
            if edit_idx is not None and 0 <= edit_idx < len(data):
                edit = data[edit_idx]

            # 도시 선택 (key 고유화로 TypeError 방지)
            city_opt = cities + ["+ 새 도시"]
            sel_idx = next((i for i, opt in enumerate(city_opt) if opt == edit.get("city")), 0)
            sel_city = st.selectbox(lang.get("select_city", "City"), city_opt, index=sel_idx, key=f"city_sel_{edit_idx if edit_idx else 'new'}")
            city = st.text_input("도시명", value=edit.get("city", ""), key=f"city_input_{edit_idx if edit_idx else 'new'}") if sel_city == "+ 새 도시" else sel_city

            # 나머지 입력 (key 고유화)
            tour_date = st.date_input(lang.get("date", "Date"), value=datetime.strptime(edit.get("date", today), "%Y-%m-%d").date() if edit.get("date") else date.today(), key=f"date_{edit_idx if edit_idx else 'new'}")
            venue = st.text_input(lang.get("venue", "Venue"), value=edit.get("venue", ""), key=f"venue_{edit_idx if edit_idx else 'new'}")
            seats = st.number_input(lang.get("seats", "Seats"), min_value=0, step=50, value=edit.get("seats", 0), key=f"seats_{edit_idx if edit_idx else 'new'}")
            vtype_idx = 0 if edit.get("type") == lang.get("indoor", "Indoor") else 1
            vtype = st.radio("형태", [lang.get("indoor", "Indoor"), lang.get("outdoor", "Outdoor")], horizontal=True, index=vtype_idx, key=f"type_{edit_idx if edit_idx else 'new'}")
            map_link = st.text_input(lang.get("google_link", "Maps Link"), value=edit.get("map_link", ""), key=f"link_{edit_idx if edit_idx else 'new'}")
            note = st.text_area(lang.get("note", "Notes"), value=edit.get("note", ""), key=f"note_{edit_idx if edit_idx else 'new'}")

            if st.button(lang.get("save", "Save") if edit_idx is not None else lang.get("register", "Add"), key=f"btn_{edit_idx if edit_idx else 'new'}"):
                if not city.strip():
                    st.warning("도시 이름을 제대로 입력해!")
                    return
                lat, lon = extract_latlon(map_link)
                if not lat or not lon:
                    st.warning("구글맵 링크가 유효한지 확인 – 좌표 못 뽑아!")
                    return
                entry = {
                    "city": city.strip(),
                    "date": tour_date.strftime("%Y-%m-%d"),
                    "venue": venue,
                    "seats": seats,
                    "type": vtype,
                    "note": note,
                    "lat": lat,
                    "lon": lon,
                    "map_link": map_link
                }
                if edit_idx is not None:
                    data[edit_idx] = entry
                    st.session_state.edit_index = None
                    st.success("수정 완료 – 매운 맛으로 업데이트!")
                else:
                    data.append(entry)
                    st.success("추가 완료 – 이제 지도에 뜬다!")
                data.sort(key=lambda x: x["date"])
                if city not in cities:
                    cities.append(city)
                    save_json(CITY_LIST_FILE, cities)
                save_json(CITY_FILE, data)
                st.rerun()

        # 투어 리스트
        st.subheader(lang.get("tour_list", "Schedule"))
        if not data:
            st.info(lang.get("no_tour", "No tour yet"))
        else:
            sorted_data = sorted(data, key=lambda x: x["date"])
            for i, c in enumerate(sorted_data):
                with st.expander(f"{c['city']} | {c['date']} | {c['venue']} | {c['seats']}석 | {c['type']}"):
                    st.markdown(f"**길안내**: [Google Maps 열기]({c.get('map_link', '#')})")
                    st.markdown(f"**특이사항**: {c.get('note', '없음')}")
                    col1, col2 = st.columns(2)
                    if col1.button("수정", key=f"edit_{i}_{c['city']}"):  # 고유 key
                        orig_idx = next(j for j, d in enumerate(data) if d["city"] == c["city"] and d["date"] == c["date"])
                        st.session_state.edit_index = orig_idx
                        st.rerun()
                    if col2.button("삭제", key=f"del_{i}_{c['city']}"):  # 고유 key
                        data[:] = [d for d in data if not (d["city"] == c["city"] and d["date"] == c["date"])]
                        save_json(CITY_FILE, data)
                        st.success("삭제 완료 – 깔끔하게 지움!")
                        st.rerun()

    # Google Maps 렌더 (데이터 있으면)
    if data:
        map_html = render_google_map([d for d in data if "lat" in d and "lon" in d], st.session_state.gmaps_api_key)
        components.html(map_html, height=600, scrolling=True)
    else:
        st.info("투어 추가부터 해 – 지도가 기다리고 있어!")

# =============================================
# 7. 사이드바 + 메인
# =============================================
with st.sidebar:
    lang_map = {"한국어": "ko", "English": "en"}
    display_opts = list(lang_map.keys())
    curr_idx = display_opts.index(next(k for k, v in lang_map.items() if v == st.session_state.lang))
    selected_display = st.selectbox("언어", display_opts, index=curr_idx, key="lang_select")
    new_lang = lang_map[selected_display]
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")
    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password", key="pw_input")
        if st.button("로그인", key="login_btn") and pw == "0000":
            st.session_state.admin = True
            st.success("관리자 모드 ON – 이제 난리 쳐!")
            st.rerun()
    else:
        st.success("관리자 모드 🔥")
        if st.button("로그아웃", key="logout_btn"):
            for k in ["admin", "edit_index"]: st.session_state.pop(k, None)
            st.rerun()

# =============================================
# 8. 메인 UI
# =============================================
lang = get_lang(st.session_state.lang)
st.markdown(f"# {lang.get('title', 'Cantata Tour 2025')} 🎄")
st.caption("마하라스트라 투어 관리 – 매운 맛으로 가자!")

tab1, tab2 = st.tabs(["공지사항", lang.get("tab_map", "Route")])

with tab1:
    st.info("공지 기능은 기본 – 필요시 확장해. 지금은 투어에 집중!")
    # 간단 공지 (생략 가능)

with tab2:
    render_map()
