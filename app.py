# app.py - 칸타타 투어 2025 (정리된 완성본)
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re
from math import radians, sin, cos, sqrt, asin, atan2, degrees
import requests
from pytz import timezone

# --- 설정 / 파일 경로 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
CITY_FILE = "cities.json"
NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
SOUND_PATH = "sounds/notice.mp3"  # 반드시 이 경로에 소리 파일을 넣어주세요
os.makedirs(UPLOAD_DIR, exist_ok=True)
if os.path.dirname(SOUND_PATH):
    os.makedirs(os.path.dirname(SOUND_PATH), exist_ok=True)

# --- 세션 기본값 ---
defaults = {
    "admin": False,
    "lang": "ko",
    "edit_city": None,
    "expanded": {},
    "pw": "0009",
    "seen_notices": [],
    "active_tab": "공지",
    "new_notice_added": False,
    "sidebar_city_select": "전체 보기",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 다국어 간단 정의 ---
LANG = {
    "ko": {
        "title_base": "칸타타 투어", "caption": "마하라스트라", "tab_notice": "공지", "tab_map": "투어 경로",
        "map_title": "경로 보기", "add_city": "도시 추가", "password": "비밀번호", "login": "로그인",
        "logout": "로그아웃", "wrong_pw": "비밀번호가 틀렸습니다.", "select_city": "도시 선택",
        "venue": "공연장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵 링크",
        "indoor": "실내", "outdoor": "실외", "register": "등록", "edit": "수정", "remove": "삭제",
        "date": "등록일", "performance_date": "공연 날짜", "cancel": "취소", "title_label": "제목",
        "content_label": "내용", "upload_image": "이미지 업로드", "upload_file": "파일 업로드",
        "submit": "등록", "warning": "제목과 내용을 모두 입력해주세요.", "file_download": "파일 다운로드",
        "pending": "미정", "est_time": "{hours}h {mins}m"
    }
}
_ = lambda key: LANG.get(st.session_state.lang, LANG["ko"]).get(key, key)

# --- 유틸리티 함수 ---
def _safe_filename(name: str) -> str:
    return re.sub(r'[^0-9a-zA-Z._-]', '_', name)

def load_json(path):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- 하버신 거리 (km) ---
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))

# --- 실제 교통 시간 (Google Directions 사용, 없으면 fallback) ---
@st.cache_data(ttl=1800, show_spinner=False)
def get_real_travel_time(lat1, lon1, lat2, lon2):
    api_key = st.secrets.get("GOOGLE_MAPS_API_KEY", None)
    if api_key:
        try:
            origin = f"{lat1},{lon1}"
            dest = f"{lat2},{lon2}"
            url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={dest}&mode=driving&key={api_key}"
            r = requests.get(url, timeout=8)
            d = r.json()
            if d.get("status") == "OK":
                leg = d["routes"][0]["legs"][0]
                dist_km = leg["distance"]["value"] / 1000.0
                mins = int(leg["duration"]["value"] // 60)
                return dist_km, mins
        except Exception:
            pass
    # fallback: haversine + 55km/h 평균 속도
    dist_km = haversine(lat1, lon1, lat2, lon2)
    mins = int(dist_km * 60 / 55)
    return dist_km, mins

# --- 기본 도시 (존재하지 않으면 생성) ---
DEFAULT_CITIES = [
    {"city":"Mumbai","venue":"Gateway of India","seats":"5000","note":"인도 영화 수도","google_link":"", "indoor":False,"lat":19.0760,"lon":72.8777,"perf_date":None,"date":datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")},
    {"city":"Pune","venue":"Shaniwar Wada","seats":"3000","note":"IT 허브","google_link":"", "indoor":True,"lat":18.5204,"lon":73.8567,"perf_date":None,"date":datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")},
    {"city":"Nagpur","venue":"Deekshabhoomi","seats":"2000","note":"오렌지 도시","google_link":"", "indoor":False,"lat":21.1458,"lon":79.0882,"perf_date":None,"date":datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")}
]
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

# --- 공지 기능 (알림 플래그 포함) ---
def add_notice(title, content, img=None, file=None):
    img_path = None
    file_path = None
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

    # 표시 플래그 설정 및 새로고침
    st.session_state["new_notice_added"] = True
    st.session_state["active_tab"] = _("tab_notice")
    st.experimental_rerun()

def render_notices():
    data = load_json(NOTICE_FILE)
    for i, n in enumerate(data):
        new_flag = n["id"] not in st.session_state.get("seen_notices", []) and not st.session_state.get("admin", False)
        title = f"{n.get('date','')} | {n.get('title','')}"
        if new_flag:
            title += ' <span style="background:#e74c3c;color:#fff;border-radius:6px;padding:2px 6px;font-size:0.8em;margin-left:6px;">NEW</span>'
        with st.expander(title, expanded=False):
            st.markdown(n.get("content",""))
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                with open(n["file"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                st.markdown(f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(n["file"])}">파일 다운로드</a>', unsafe_allow_html=True)
            if st.session_state.get("admin", False) and st.button("삭제", key=f"del_notice_{i}"):
                data.pop(i)
                save_json(NOTICE_FILE, data)
                st.experimental_rerun()
        if new_flag:
            # mark seen for this session
            st.session_state.setdefault("seen_notices", []).append(n["id"])

# --- 사이드바 UI (언어/로그인/도시 선택) ---
with st.sidebar:
    st.title(_("title_base"))
    st.caption(_("caption"))
    st.markdown("---")
    if not st.session_state.get("admin", False):
        pw = st.text_input(_("password"), type="password")
        if st.button(_("login")):
            if pw == st.session_state.get("pw"):
                st.session_state["admin"] = True
                st.experimental_rerun()
            else:
                st.error(_("wrong_pw"))
    else:
        if st.button(_("logout")):
            st.session_state["admin"] = False
            st.experimental_rerun()
    st.markdown("---")
    # 사이드바 도시필터 (변경 시 모든 expander 닫기)
    all_cities = [c["city"] for c in load_json(CITY_FILE)]
    sb_options = ["전체 보기"] + all_cities
    sel = st.selectbox(_("select_city"), options=sb_options, index=0)
    if st.session_state.get("sidebar_city_select") != sel:
        st.session_state["sidebar_city_select"] = sel
        st.session_state["expanded"] = {}

# --- 상단: 새 공지 알림 (따뜻한 문구 B 스타일) ---
if st.session_state.get("new_notice_added", False):
    st.success("📢 새 공지가 등록되었습니다 😊 확인해주세요.")
    if os.path.exists(SOUND_PATH):
        try:
            st.audio(SOUND_PATH, autoplay=True)
        except Exception:
            pass
    st.session_state["new_notice_added"] = False

# --- 지도 렌더링 (folium) ---
def render_map():
    st.subheader(_("map_title"))
    today = date.today()

    raw = load_json(CITY_FILE)
    # normalize perf_date -> string 'YYYY-MM-DD' or None
    for c in raw:
        pd = c.get("perf_date")
        if not pd or pd in ("", "None", "null"):
            c["perf_date"] = None
        else:
            try:
                # keep string if matches YYYY-MM-DD
                _ = datetime.strptime(pd, "%Y-%m-%d")
            except:
                c["perf_date"] = None

    # sort by perf_date with None last
    full_order = sorted(raw, key=lambda x: x.get("perf_date") or "9999-12-31")
    # apply sidebar filter
    sel = st.session_state.get("sidebar_city_select", "전체 보기")
    if sel and sel != "전체 보기":
        display_list = [c for c in full_order if c["city"] == sel]
    else:
        display_list = full_order

    if not display_list:
        st.warning("도시 없음")
        return

    # build map centered on first displayed city
    center = (display_list[0]["lat"], display_list[0]["lon"])
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")

    # precompute segments along full_order (tour sequence)
    segments = []
    for i in range(len(full_order)-1):
        a = full_order[i]
        b = full_order[i+1]
        dist_km, mins = get_real_travel_time(a["lat"], a["lon"], b["lat"], b["lon"])
        segments.append({"a": a, "b": b, "dist_km": dist_km, "mins": mins})

    # compute today_index in full_order (first city with date == today)
    today_index = -1
    for i, c in enumerate(full_order):
        if c.get("perf_date"):
            try:
                pd_obj = datetime.strptime(c["perf_date"], "%Y-%m-%d").date()
                if pd_obj == today:
                    today_index = i
                    break
            except:
                pass

    # add markers for display_list
    for idx, c in enumerate(display_list):
        is_past = False
        if c.get("perf_date"):
            try:
                pd_obj = datetime.strptime(c["perf_date"], "%Y-%m-%d").date()
                if pd_obj < today:
                    is_past = True
            except:
                is_past = False

        marker_opacity = 0.5 if is_past else 1.0
        folium.CircleMarker(
            (c["lat"], c["lon"]),
            radius=7,
            color="#e74c3c" if not is_past else "rgba(231,76,60,0.5)",
            fill=True,
            fillOpacity=marker_opacity,
            popup=folium.Popup(f"<b>{c['city']}</b><br>{c.get('perf_date') or _('pending')}<br>{c.get('venue','—')}", max_width=260)
        ).add_to(m)

    # add segments and parallel labels (use midpoints)
    for seg_idx, seg in enumerate(segments):
        a = seg["a"]; b = seg["b"]
        a_lat, a_lon = a["lat"], a["lon"]; b_lat, b_lon = b["lat"], b["lon"]

        # determine if this segment is past based on 'from' city index relative to today_index
        seg_is_past = False
        try:
            from_idx = next(i for i, cc in enumerate(full_order) if cc["city"] == a["city"])
            if today_index != -1 and from_idx < today_index:
                seg_is_past = True
        except StopIteration:
            seg_is_past = False

        line_opacity = 0.5 if seg_is_past else 1.0
        AntPath(locations=[(a_lat, a_lon), (b_lat, b_lon)], color="#e74c3c", weight=6, opacity=line_opacity, delay=800, dash_array=[20,30]).add_to(m)

        # midpoint + angle
        mid_lat = (a_lat + b_lat)/2.0
        mid_lon = (a_lon + b_lon)/2.0
        dx = b_lon - a_lon
        dy = b_lat - a_lat
        angle = degrees(atan2(dx, dy))

        hours = seg["mins"] // 60
        mins = seg["mins"] % 60
        time_str = f"{hours}h {mins}m" if hours else f"{mins}m"
        dist_str = f"{seg['dist_km']:.0f}km {time_str}"

        # DivIcon rotated to be parallel with segment
        label_html = f"""
        <div style="
            transform: rotate({angle}deg);
            -webkit-transform: rotate({angle}deg);
            background: rgba(231,76,60,{0.45 if seg_is_past else 0.95});
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight:600;
            white-space:nowrap;
            box-shadow: 0 1px 4px rgba(0,0,0,0.3);
        ">{dist_str}</div>
        """
        folium.map.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=label_html), interactive=False).add_to(m)

    # show map
    st_folium(m, width=1000, height=650, key=f"map_{len(full_order)}")

    # show collapsed expanders list (all collapsed by default; open only if stored in session_state)
    st.markdown("---")
    st.subheader("공연 도시 목록")
    for c in full_order:
        if sel and sel != "전체 보기" and c["city"] != sel:
            continue
        display_date = c.get("perf_date") or _("pending")
        expanded_flag = bool(st.session_state.get("expanded", {}).get(c["city"], False))
        with st.expander(f"{c['city']} | {display_date}", expanded=expanded_flag):
            st.write(f"등록일: {c.get('date','—')}")
            st.write(f"공연 날짜: {display_date}")
            st.write(f"장소: {c.get('venue','—')}")
            st.write(f"예상 인원: {c.get('seats','—')}")
            st.write(f"특이사항: {c.get('note','—')}")
            if c.get("google_link"):
                st.markdown(f"[구글맵 보기]({c.get('google_link')})")
            if st.session_state.get("admin", False):
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("수정", key=f"edit_{c['city']}"):
                        st.session_state["edit_city"] = c["city"]
                        st.experimental_rerun()
                with c2:
                    if st.button("삭제", key=f"del_{c['city']}"):
                        data = load_json(CITY_FILE)
                        idx = next((i for i,x in enumerate(data) if x["city"]==c["city"]), None)
                        if idx is not None:
                            data.pop(idx)
                            save_json(CITY_FILE, data)
                            st.experimental_rerun()

# --- 탭 --- (탭 전환 시 expander 초기화)
tab1, tab2 = st.tabs([_("tab_notice"), _("tab_map")])

with tab1:
    # on tab change, reset expanders
    if st.session_state.get("active_tab") != _("tab_notice"):
        st.session_state["active_tab"] = _("tab_notice")
        st.session_state["expanded"] = {}
    if st.session_state.get("admin", False):
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

# --- 관리자: 도시 편집 (하단) ---
if st.session_state.get("admin", False):
    st.markdown("---")
    st.subheader("관리자: 도시 편집/추가")
    data = load_json(CITY_FILE)
    option = [d["city"] for d in data] + ["새로 추가"]
    edit_choice = st.selectbox("편집할 도시 선택", options=option, index=0)
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
        new_city = st.selectbox("추가할 도시", options=[ "Mumbai","Pune","Nagpur" ])
        new_venue = st.text_input("공연장소 (새)")
        new_lat, new_lon = (18.5204, 73.8567)
        new_perf = st.text_input("공연 날짜 (YYYY-MM-DD)", value="")
        if st.button("추가"):
            new_item = {"city": new_city, "venue": new_venue, "seats":"0", "note":"", "google_link":"", "indoor":True, "lat":new_lat, "lon":new_lon, "perf_date": new_perf.strip() if new_perf.strip() else None, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")}
            data.append(new_item)
            save_json(CITY_FILE, data)
            st.success("도시 추가됨")
            st.experimental_rerun()

# --- 끝 ---
