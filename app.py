# app.py - 칸타타 투어 2025 (folium 기반, 전체 패치 적용)
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re
from math import radians, sin, cos, sqrt, asin, atan2, degrees
import requests
from pytz import timezone

# --- 설정 및 파일 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
CITY_FILE = "cities.json"
NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
SOUND_PATH = "sounds/notice.mp3"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SOUND_PATH), exist_ok=True) if os.path.dirname(SOUND_PATH) else None

# --- 세션 기본값 ---
defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "expanded": {}, "adding_cities": [],
    "pw": "0009", "seen_notices": [], "active_tab": "공지", "new_notice": False, "sound_played": False,
    "new_notice_added": False, "sidebar_city_select": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 언어(간단) ---
LANG = {
    "ko": {"title_base":"칸타타 투어","caption":"마하라스트라","tab_notice":"공지","tab_map":"투어 경로",
           "map_title":"경로 보기","password":"비밀번호","login":"로그인","logout":"로그아웃",
           "wrong_pw":"비밀번호가 틀렸습니다.","select_city":"도시 선택","venue":"공연장소",
           "seats":"예상 인원","note":"특이사항","google_link":"구글맵 링크","indoor":"실내",
           "register":"등록","title_label":"제목","content_label":"내용","upload_image":"이미지 업로드",
           "upload_file":"파일 업로드","submit":"등록","warning":"제목과 내용을 모두 입력해주세요.",
           "pending":"미정","est_time":"{hours}h {mins}m"}
}
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# --- 안전 파일명 헬퍼 ---
def _safe_filename(name):
    return re.sub(r'[^0-9a-zA-Z._-]', '_', name)

# --- json 헬퍼 ---
def load_json(f):
    try:
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                return json.load(fp)
    except:
        pass
    return []

def save_json(f, d):
    with open(f, "w", encoding="utf-8") as fp:
        json.dump(d, fp, ensure_ascii=False, indent=2)

# --- 하버신 거리 ---
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))

# --- 실제 교통 시간 (Google Directions fallback to haversine) ---
@st.cache_data(ttl=1800, show_spinner=False)
def get_real_travel_time(lat1, lon1, lat2, lon2):
    api_key = st.secrets.get("GOOGLE_MAPS_API_KEY", None)
    try:
        if not api_key:
            raise ValueError("No API key - fallback")
        origin = f"{lat1},{lon1}"
        dest = f"{lat2},{lon2}"
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={dest}&mode=driving&key={api_key}"
        r = requests.get(url, timeout=8)
        d = r.json()
        if d.get("status") == "OK":
            leg = d["routes"][0]["legs"][0]
            dist = leg["distance"]["value"] / 1000.0
            mins = int(leg["duration"]["value"] // 60)
            return dist, mins
    except Exception as e:
        try: st.write("get_real_travel_time fallback:", e)
        except: pass
    dist = haversine(lat1, lon1, lat2, lon2)
    mins = int(dist * 60 / 55)
    return dist, mins

# --- 내장 도시 목록 및 좌표 (사용자 제공) ---
cities = sorted([
    "Mumbai","Pune","Nagpur","Nashik","Thane","Aurangabad","Solapur","Amravati","Nanded","Kolhapur",
    "Akola","Latur","Ahmadnagar","Jalgaon","Dhule","Ichalkaranji","Malegaon","Bhusawal","Bhiwandi","Bhandara",
    "Beed","Buldana","Chandrapur","Dharashiv","Gondia","Hingoli","Jalna","Mira-Bhayandar","Nandurbar","Osmanabad",
    "Palghar","Parbhani","Ratnagiri","Sangli","Satara","Sindhudurg","Wardha","Washim","Yavatmal","Kalyan-Dombivli",
    "Ulhasnagar","Vasai-Virar","Sangli-Miraj-Kupwad","Nanded-Waghala","Bandra (Mumbai)","Colaba (Mumbai)","Andheri (Mumbai)",
    "Navi Mumbai","Pimpri-Chinchwad (Pune)","Kothrud (Pune)","Hadapsar (Pune)","Pune Cantonment",
    "Nashik Road","Deolali (Nashik)","Satpur (Nashik)","Aurangabad City","Jalgaon City",
    "Nagpur City","Sitabuldi (Nagpur)","Jaripatka (Nagpur)","Solapur City","Pandharpur (Solapur)",
    "Amravati City","Badnera (Amravati)","Akola City","Washim City","Yavatmal City",
    "Wardha City","Chandrapur City","Gadchiroli","Gondia City","Bhandara City",
    "Gadhinglaj (Kolhapur)","Kagal (Kolhapur)"
])
coords = {
    "Mumbai": (19.07, 72.88), "Pune": (18.52, 73.86), "Nagpur": (21.15, 79.08), "Nashik": (20.00, 73.79),
    "Thane": (19.22, 72.98), "Aurangabad": (19.88, 75.34), "Solapur": (17.67, 75.91), "Amravati": (20.93, 77.75),
    "Nanded": (19.16, 77.31), "Kolhapur": (16.70, 74.24), "Akola": (20.70, 77.00), "Latur": (18.40, 76.18),
    "Ahmadnagar": (19.10, 74.75), "Jalgaon": (21.00, 75.57), "Dhule": (20.90, 74.77), "Ichalkaranji": (16.69, 74.47),
    "Malegaon": (20.55, 74.53), "Bhusawal": (21.05, 76.00), "Bhiwandi": (19.30, 73.06), "Bhandara": (21.17, 79.65),
    "Beed": (18.99, 75.76), "Buldana": (20.54, 76.18), "Chandrapur": (19.95, 79.30), "Dharashiv": (18.40, 76.57),
    "Gondia": (21.46, 80.19), "Hingoli": (19.72, 77.15), "Jalna": (19.85, 75.89), "Mira-Bhayandar": (19.28, 72.87),
    "Nandurbar": (21.37, 74.22), "Osmanabad": (18.18, 76.07), "Palghar": (19.70, 72.77), "Parbhani": (19.27, 76.77),
    "Ratnagiri": (16.99, 73.31), "Sangli": (16.85, 74.57), "Satara": (17.68, 74.02), "Sindhudurg": (16.24, 73.42),
    "Wardha": (20.75, 78.60), "Washim": (20.11, 77.13), "Yavatmal": (20.39, 78.12), "Kalyan-Dombivli": (19.24, 73.13),
    "Ulhasnagar": (19.22, 73.16), "Vasai-Virar": (19.37, 72.81), "Sangli-Miraj-Kupwad": (16.85, 74.57), "Nanded-Waghala": (19.16, 77.31),
    "Bandra (Mumbai)": (19.06, 72.84), "Colaba (Mumbai)": (18.92, 72.82), "Andheri (Mumbai)": (19.12, 72.84),
    "Navi Mumbai": (19.03, 73.00), "Pimpri-Chinchwad (Pune)": (18.62, 73.80), "Kothrud (Pune)": (18.50, 73.81), "Hadapsar (Pune)": (18.51, 73.94),
    "Pune Cantonment": (18.50, 73.89), "Nashik Road": (20.00, 73.79), "Deolali (Nashik)": (19.94, 73.82), "Satpur (Nashik)": (20.01, 73.79),
    "Aurangabad City": (19.88, 75.34), "Jalgaon City": (21.00, 75.57), "Nagpur City": (21.15, 79.08), "Sitabuldi (Nagpur)": (21.14, 79.08),
    "Jaripatka (Nagpur)": (21.12, 79.07), "Solapur City": (17.67, 75.91), "Pandharpur (Solapur)": (17.66, 75.32), "Amravati City": (20.93, 77.75),
    "Badnera (Amravati)": (20.84, 77.73), "Akola City": (20.70, 77.00), "Washim City": (20.11, 77.13), "Yavatmal City": (20.39, 78.12),
    "Wardha City": (20.75, 78.60), "Chandrapur City": (19.95, 79.30), "Gadchiroli": (20.09, 80.11), "Gondia City": (21.46, 80.19),
    "Bhandara City": (21.17, 79.65), "Gadhinglaj (Kolhapur)": (16.23, 74.34), "Kagal (Kolhapur)": (16.57, 74.31)
}

# --- 초기 데이터 파일 생성(없으면) ---
if not os.path.exists(CITY_FILE):
    # 기본: cities 순서대로 coords를 사용해 기본 항목 생성 (perf_date는 None)
    base = []
    now = datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
    for name in cities:
        lat, lon = coords.get(name, (18.5204, 73.8567))
        base.append({"city": name, "venue": "", "seats": "0", "note": "", "google_link": "", "indoor": True, "lat": lat, "lon": lon, "perf_date": None, "date": now})
    save_json(CITY_FILE, base)

# --- 공지 기능 (add sets new_notice_added flag) ---
def add_notice(title, content, img=None, file=None):
    img_path = None; file_path = None
    if img:
        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{_safe_filename(img.name)}")
        open(img_path, "wb").write(img.read())
    if file:
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{_safe_filename(file.name)}")
        open(file_path, "wb").write(file.read())
    notice = {"id": str(uuid.uuid4()), "title": title, "content": content, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"), "image": img_path, "file": file_path}
    data = load_json(NOTICE_FILE)
    data.insert(0, notice)
    save_json(NOTICE_FILE, data)
    st.session_state["new_notice_added"] = True
    st.session_state["active_tab"] = _("tab_notice")
    st.experimental_rerun()

def render_notices():
    data = load_json(NOTICE_FILE)
    for i, n in enumerate(data):
        with st.expander(f"{n.get('date','')} | {n.get('title','')}", expanded=False):
            st.markdown(n.get("content",""))
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                with open(n["file"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                st.markdown(f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(n["file"])}">파일 다운로드</a>', unsafe_allow_html=True)
            if st.session_state.admin and st.button("삭제", key=f"del_notice_{i}"):
                data.pop(i); save_json(NOTICE_FILE, data); st.experimental_rerun()

# --- 사이드바 (언어, 로그인, 도시 선택) ---
with st.sidebar:
    st.title(_("title_base"))
    st.caption(_("caption") if "caption" in LANG["ko"] else "")
    lang_options = ["한국어"]
    selected = st.selectbox("언어", lang_options, index=0)
    st.markdown("---")
    if not st.session_state.admin:
        pw = st.text_input(_("password"), type="password")
        if st.button(_("login")):
            if pw == st.session_state.pw:
                st.session_state.admin = True
                st.experimental_rerun()
            else:
                st.error(_("wrong_pw"))
    else:
        if st.button(_("logout")):
            st.session_state.admin = False
            st.experimental_rerun()

    st.markdown("---")
    # 사이드바 도시 선택 (변경 시 expander 닫힘)
    sb_city = st.selectbox(_("select_city"), options=["전체 보기"] + cities, index=0)
    if st.session_state.get("sidebar_city_select") != sb_city:
        st.session_state["sidebar_city_select"] = sb_city
        # 탭/페이지 이동 효과: 모든 expander 초기화
        st.session_state["expanded"] = {}

# --- 페이지 상단 알림 처리 (새 공지) ---
if st.session_state.get("new_notice_added", False):
    # 스타일 B: 따뜻한 문구
    st.success("📢 새 공지가 등록되었습니다 😊 확인해주세요.")
    if os.path.exists(SOUND_PATH):
        try:
            st.audio(SOUND_PATH, autoplay=True)
        except:
            pass
    st.session_state["new_notice_added"] = False

# --- 지도 렌더링 함수 (folium) ---
def render_map():
    st.subheader(_("map_title"))
    raw = load_json(CITY_FILE)
    # normalize perf_date to YYYY-MM-DD or None
    for c in raw:
        pd = c.get("perf_date")
        if not pd or pd in ("", "None", "null"):
            c["perf_date"] = None
        else:
            try:
                # allow YYYY-MM-DD
                _ = datetime.strptime(pd, "%Y-%m-%d")
            except:
                c["perf_date"] = None

    # sort by perf_date (None at end)
    cities_list = sorted(raw, key=lambda x: x.get("perf_date") or "9999-12-31")

    # filter by sidebar selection if not "전체 보기"
    sel = st.session_state.get("sidebar_city_select")
    if sel and sel != "전체 보기":
        cities_list = [c for c in cities_list if c["city"] == sel]

    if not cities_list:
        st.warning("도시 없음")
        return

    # center map on first city's coords
    center = (cities_list[0]["lat"], cities_list[0]["lon"])
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")

    today = date.today()

    # Precompute segments (consecutive in the currently displayed full list)
    # We will compute segments based on the full file order (not the filtered one) to maintain tour order
    full = sorted(load_json(CITY_FILE), key=lambda x: x.get("perf_date") or "9999-12-31")
    segments = []
    for i in range(len(full)-1):
        a = full[i]; b = full[i+1]
        dist_km, mins = get_real_travel_time(a['lat'], a['lon'], b['lat'], b['lon'])
        segments.append({"a": a, "b": b, "dist_km": dist_km, "mins": mins})

    # Draw markers and list expanders
    for idx, c in enumerate(cities_list):
        # determine if past
        pd = c.get("perf_date")
        is_past = False
        if pd:
            try:
                pd_obj = datetime.strptime(pd, "%Y-%m-%d").date()
                if pd_obj < today:
                    is_past = True
            except:
                is_past = False

        marker_color = "red" if not is_past else "#e74c3c"
        marker_opacity = 1.0 if not is_past else 0.5

        folium.CircleMarker(
            location=(c["lat"], c["lon"]),
            radius=8,
            color=marker_color,
            fill=True,
            fillOpacity=marker_opacity,
            opacity=marker_opacity,
            popup=folium.Popup(f"<b>{c['city']}</b><br>{c.get('perf_date') or _('pending')}<br>{c.get('venue','—')}", max_width=250)
        ).add_to(m)

    # Draw segments with parallel labels
    for seg in segments:
        a = seg["a"]; b = seg["b"]
        a_lat, a_lon = a["lat"], a["lon"]
        b_lat, b_lon = b["lat"], b["lon"]
        # determine if this segment is past: if 'from' city (a) is before today
        a_pd = a.get("perf_date")
        seg_is_past = False
        if a_pd:
            try:
                a_pd_obj = datetime.strptime(a_pd, "%Y-%m-%d").date()
                if a_pd_obj < today:
                    seg_is_past = True
            except:
                seg_is_past = False

        line_opacity = 0.5 if seg_is_past else 1.0
        line_color = "#e74c3c"

        AntPath(locations=[(a_lat, a_lon), (b_lat, b_lon)], color=line_color, weight=6, opacity=line_opacity, delay=800, dash_array=[20,30]).add_to(m)

        # midpoint for label
        mid_lat = (a_lat + b_lat) / 2.0
        mid_lon = (a_lon + b_lon) / 2.0

        # compute angle (small-distance approx)
        dx = b_lon - a_lon
        dy = b_lat - a_lat
        angle = degrees(atan2(dx, dy))

        hours = int(seg["mins"]) // 60
        mins = int(seg["mins"]) % 60
        time_str = (f"{hours}h {mins}m" if hours else f"{mins}m")
        dist_str = f"{seg['dist_km']:.0f}km {time_str}"

        # DivIcon with rotation (parallel to line)
        label_html = f"""
        <div style="
            transform: rotate({angle}deg);
            -webkit-transform: rotate({angle}deg);
            background: rgba(231,76,60,{0.45 if seg_is_past else 0.95});
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            box-shadow: 0 1px 4px rgba(0,0,0,0.3);
            white-space: nowrap;
        ">{dist_str}</div>
        """
        folium.map.Marker(
            [mid_lat, mid_lon],
            icon=folium.DivIcon(html=label_html),
            interactive=False
        ).add_to(m)

    # display map
    st_data = st_folium(m, width=900, height=600, returned_objects=[], key=f"map_{len(full)}")

    # After map render, show expanders for each city in the sidebar area (or main) - all collapsed by default
    st.markdown("---")
    st.subheader("공연 도시 목록")
    full_sorted = sorted(load_json(CITY_FILE), key=lambda x: x.get("perf_date") or "9999-12-31")
    for i, c in enumerate(full_sorted):
        # respect sidebar filter
        if sel and sel != "전체 보기" and c["city"] != sel:
            continue
        display_date = c.get("perf_date") or _("pending")
        # All expanders default to closed (expanded=False). If you need to open one, set via st.session_state['expanded'][city]=True
        expanded_flag = bool(st.session_state.get("expanded", {}).get(c["city"], False))
        with st.expander(f"{c['city']} | {display_date}", expanded=expanded_flag):
            st.write(f"등록일: {c.get('date', '—')}")
            st.write(f"공연 날짜: {display_date}")
            st.write(f"장소: {c.get('venue', '—')}")
            st.write(f"예상 인원: {c.get('seats', '—')}")
            st.write(f"특이사항: {c.get('note', '—')}")
            if c.get("google_link"):
                st.markdown(f"[구글맵 보기]({c.get('google_link')})")
            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("수정", key=f"edit_{i}"):
                        st.session_state["edit_city"] = c["city"]
                        st.experimental_rerun()
                with c2:
                    if st.button("삭제", key=f"del_{i}"):
                        data = load_json(CITY_FILE)
                        idx_del = next((j for j, item in enumerate(data) if item.get("city") == c.get("city")), None)
                        if idx_del is not None:
                            data.pop(idx_del)
                            save_json(CITY_FILE, data)
                        st.experimental_rerun()

# --- 탭 생성 (공지 / 지도) ---
tab1, tab2 = st.tabs([_("tab_notice"), _("tab_map")])

with tab1:
    # ensure expanders collapsed on tab change
    if st.session_state.get("active_tab") != _("tab_notice"):
        st.session_state["active_tab"] = _("tab_notice")
        st.session_state["expanded"] = {}
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_("title_label"))
            c = st.text_area(_("content_label"))
            img = st.file_uploader(_("upload_image"), type=["png","jpg","jpeg"])
            f = st.file_uploader(_("upload_file"))
            if st.form_submit_button(_("submit")):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_("warning"))
    render_notices()

with tab2:
    if st.session_state.get("active_tab") != _("tab_map"):
        st.session_state["active_tab"] = _("tab_map")
        st.session_state["expanded"] = {}
    render_map()

# --- 관리자: 도시 추가 / 편집 간단 UI (하단) ---
if st.session_state.admin:
    st.markdown("---")
    st.subheader("관리자: 도시 편집/추가")
    data = load_json(CITY_FILE)
    # 편집 대상 선택
    edit_choice = st.selectbox("편집할 도시 선택", options=[d["city"] for d in data] + ["새로 추가"], index=0)
    if edit_choice != "새로 추가":
        item = next((x for x in data if x["city"] == edit_choice), None)
        if item:
            col1, col2 = st.columns(2)
            with col1:
                venue = st.text_input("공연장소", value=item.get("venue",""))
                perf_date = st.text_input("공연 날짜 (YYYY-MM-DD)", value=item.get("perf_date") or "")
            with col2:
                seats = st.text_input("예상 인원", value=item.get("seats","0"))
                note = st.text_area("특이사항", value=item.get("note",""))
            if st.button("저장"):
                for i,d in enumerate(data):
                    if d["city"] == item["city"]:
                        data[i]["venue"] = venue.strip()
                        data[i]["perf_date"] = perf_date.strip() if perf_date.strip() else None
                        data[i]["seats"] = seats
                        data[i]["note"] = note
                        save_json(CITY_FILE, data)
                        st.success("저장 완료")
                        st.experimental_rerun()
            if st.button("취소"):
                st.experimental_rerun()
    else:
        new_city = st.selectbox("추가할 도시", options=cities)
        new_venue = st.text_input("공연장소 (새)")
        new_lat, new_lon = coords.get(new_city, (18.5204, 73.8567))
        new_perf = st.text_input("공연 날짜 (YYYY-MM-DD)", value="")
        if st.button("추가"):
            new_item = {"city": new_city, "venue": new_venue, "seats":"0", "note":"", "google_link":"", "indoor":True, "lat":new_lat, "lon":new_lon, "perf_date": new_perf.strip() if new_perf.strip() else None, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")}
            data.append(new_item)
            save_json(CITY_FILE, data)
            st.success("도시 추가됨")
            st.experimental_rerun()

# --- 끝 ---
