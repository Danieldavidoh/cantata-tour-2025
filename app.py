# app.py - 완전 리뉴얼: 흰색 화면 + 박스 입력 + Google Maps
import streamlit as st
from datetime import datetime, date
import json, os, uuid, base64, re, requests
from pytz import timezone
import streamlit.components.v1 as components

# =============================================
# 1. 강제 라이트 모드 + CSS
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], .css-1d391kg { 
        background: white !important; 
        color: black !important; 
    }
    h1,h2,h3,p,div,span,label,.stMarkdown { color: black !important; }
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox > div > div > div { 
        background: white !important; 
        color: black !important; 
        border: 1px solid #ccc !important; 
    }
    .stButton > button { 
        background: #ff4b4b !important; 
        color: white !important; 
        border-radius: 8px !important; 
    }
    .city-box { 
        border: 2px solid #ddd; 
        border-radius: 12px; 
        padding: 20px; 
        background: #f9f9f9; 
        margin-bottom: 15px; 
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
    "admin": False, "lang": "ko", "edit_index": None, "gmaps_api_key": "",
    "show_add_box": False
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# =============================================
# 3. 시간 + 다국어 (동적)
# =============================================
india_time = datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
st.markdown(f"<p style='text-align:right;color:#666;font-size:0.9rem;'>Mumbai {india_time}</p>", unsafe_allow_html=True)

LANG = {
    "ko": { "title": "칸타타 투어 2025", "tab_map": "투어 경로", "add_city_btn": "+ 도시 추가", "select_city": "도시 선택", 
            "venue": "공연장소", "seats": "좌석수", "indoor": "실내", "outdoor": "실외", "google_link": "구글맵 링크", 
            "note": "특이사항", "register": "등록", "edit": "수정", "delete": "삭제", "save": "저장", 
            "map_title": "Google Maps 경로", "tour_list": "추가된 도시", "no_tour": "등록된 도시 없음" },
    "en": { "title": "Cantata Tour 2025", "tab_map": "Route", "add_city_btn": "+ Add City", "select_city": "Select City", 
            "venue": "Venue", "seats": "Seats", "indoor": "Indoor", "outdoor": "Outdoor", "google_link": "Maps Link", 
            "note": "Notes", "register": "Add", "edit": "Edit", "delete": "Delete", "save": "Save", 
            "map_title": "Google Maps Route", "tour_list": "Added Cities", "no_tour": "No city added" },
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
        return (float(m.group(1)), float(m.group(2))) if m else (None, None)
    except: return None, None

# =============================================
# 5. Google Maps HTML
# =============================================
def render_google_map(data, api_key):
    if not data or not api_key: return "<p>지도 로드 실패</p>"

    markers = ""
    waypoints = ""
    origin = f"{data[0]['lat']},{data[0]['lon']}"
    destination = f"{data[-1]['lat']},{data[-1]['lon']}"

    for i, c in enumerate(data):
        lat, lon = c["lat"], c["lon"]
        title = f"{c['city']} | {c.get('date','?')} | {c.get('venue','')} | {c['seats']}석 | {c['type']}"
        markers += f"new google.maps.Marker({{position:{{lat:{lat},lng:{lon}}},map:map,title:\"{title}\",icon:'http://maps.google.com/mapfiles/ms/icons/red-dot.png'}});"
        if 0 < i < len(data)-1:
            waypoints += f"{{location:new google.maps.LatLng({lat},{lon}),stopover:true}},"

    return f"""
    <!DOCTYPE html><html><head>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" async defer></script>
        <style>#map{{height:100%;width:100%}}html,body{{height:100%;margin:0}}</style>
    </head><body>
        <div id="map"></div>
        <script>
            let map;
            function initMap() {{
                map = new google.maps.Map(document.getElementById("map"), {{zoom:6,center:{{lat:19.0,lng:73.0}}}});
                {markers}
                const ds = new google.maps.DirectionsService();
                const dr = new google.maps.DirectionsRenderer({{polylineOptions:{{strokeColor:'#ff1744',strokeWeight:5}},suppressMarkers:true}});
                dr.setMap(map);
                ds.route({{origin:"{origin}",destination:"{destination}",waypoints:[ {waypoints.rstrip(',')} ],travelMode:'DRIVING'}}, 
                (res,st)=>{if(st==='OK')dr.setDirections(res);});
            }}
        </script>
    </body></html>
    """

# =============================================
# 6. 지도 + 도시 관리 (박스 입력)
# =============================================
def render_map():
    st.subheader(_["map_title"])

    # API 키 입력
    if not st.session_state.gmaps_api_key:
        with st.form("api_form"):
            key = st.text_input("Google Maps API 키", type="password")
            if st.form_submit_button("저장"):
                if key: st.session_state.gmaps_api_key = key; st.rerun()
                else: st.error("키 입력")
        return

    data = load_json(CITY_FILE)
    cities = load_json(CITY_LIST_FILE) or ["Mumbai", "Pune", "Nagpur"]

    # 도시 추가 버튼
    if st.button(_["add_city_btn"], key="add_city_btn"):
        st.session_state.show_add_box = True
        st.session_state.edit_index = None

    # 입력 박스
    if st.session_state.show_add_box or st.session_state.edit_index is not None:
        edit_idx = st.session_state.edit_index
        edit = data[edit_idx] if edit_idx is not None and edit_idx < len(data) else {}

        with st.container():
            st.markdown("<div class='city-box'>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 2])

            with col1:
                city_opt = cities + ["+ 새 도시"]
                sel_city = st.selectbox(_("select_city"), city_opt, key=f"sel_{edit_idx if edit_idx else 'new'}")
                city = st.text_input("도시명", value=edit.get("city", ""), key=f"city_{edit_idx if edit_idx else 'new'}") if sel_city == "+ 새 도시" else sel_city

                venue = st.text_input(_("venue"), value=edit.get("venue", ""), key=f"venue_{edit_idx}")
                seats = st.number_input(_("seats"), 0, step=50, value=edit.get("seats", 0), key=f"seats_{edit_idx}")
                vtype = st.radio("형태", [_["indoor"], _["outdoor"]], horizontal=True, 
                                index=0 if edit.get("type") == _["indoor"] else 1, key=f"type_{edit_idx}")

            with col2:
                map_link = st.text_input(_("google_link"), value=edit.get("map_link", ""), key=f"link_{edit_idx}")
                note = st.text_area(_("note"), value=edit.get("note", ""), height=120, key=f"note_{edit_idx}")

            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button(_["register"] if edit_idx is None else _["save"], key=f"reg_{edit_idx}"):
                    if not city: st.warning("도시 입력"); return
                    lat, lon = extract_latlon(map_link)
                    if not lat: st.warning("맵 링크 확인"); return
                    entry = {"city": city, "venue": venue, "seats": seats, "type": vtype, "note": note, 
                             "lat": lat, "lon": lon, "map_link": map_link}
                    if edit_idx is not None:
                        data[edit_idx] = entry
                        st.session_state.edit_index = None
                    else:
                        data.append(entry)
                    if city not in cities: cities.append(city); save_json(CITY_LIST_FILE, cities)
                    save_json(CITY_FILE, data)
                    st.session_state.show_add_box = False
                    st.success("저장됨")
                    st.rerun()

            with col_btn2:
                if edit_idx is not None and st.button(_("edit"), key=f"edit_btn_{edit_idx}"):
                    st.session_state.edit_index = edit_idx
                    st.rerun()

            with col_btn3:
                if st.button(_("delete"), key=f"del_btn_{edit_idx if edit_idx else 'new'}"):
                    if edit_idx is not None:
                        data.pop(edit_idx)
                        save_json(CITY_FILE, data)
                    st.session_state.show_add_box = False
                    st.session_state.edit_index = None
                    st.success("삭제됨")
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # 추가된 도시 리스트
    st.subheader(_["tour_list"])
    if not data:
        st.info(_["no_tour"])
    else:
        for i, c in enumerate(data):
            with st.expander(f"{c['city']} | {c.get('venue','')} | {c['seats']}석 | {c['type']}"):
                st.markdown(f"**특이사항**: {c.get('note','없음')}")
                if st.button("수정", key=f"edit_list_{i}"):
                    st.session_state.edit_index = i
                    st.session_state.show_add_box = True
                    st.rerun()

    # Google Maps
    if data:
        map_html = render_google_map(data, st.session_state.gmaps_api_key)
        components.html(map_html, height=600)

# =============================================
# 7. 사이드바 + 메인
# =============================================
with st.sidebar:
    lang_map = {"한국어": "ko", "English": "en"}
    opts = list(lang_map.keys())
    curr = opts.index(next(k for k, v in lang_map.items() if v == st.session_state.lang))
    sel = st.selectbox("언어", opts, index=curr, key="lang_sel")
    if lang_map[sel] != st.session_state.lang:
        st.session_state.lang = lang_map[sel]
        st.rerun()

    if not st.session_state.admin:
        pw = st.text_input("비밀번호", type="password", key="pw")
        if st.button("로그인", key="login") and pw == "0000":
            st.session_state.admin = True
            st.rerun()
    else:
        st.success("관리자")
        if st.button("로그아웃", key="logout"):
            st.session_state.admin = False
            st.rerun()

st.markdown(f"# {_['title']} 크리스마스")
tab1, tab2 = st.tabs(["공지", _["tab_map"]])

with tab1:
    st.info("공지 기능은 기본 제공")

with tab2:
    render_map()
