# app.py - Cantata Tour 2025 (Distance->Time avg 50km/h + line-parallel mid-labels)
import streamlit as st
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, sin, cos, sqrt, asin, atan2, degrees

# ====== 설정 ======
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 평균 속도 (km/h) — 사용자가 선택한 옵션 2: 거리→시간 변환 (avg speed)
AVG_SPEED_KMH = 50

# 자동 새로고침(사용자)
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh_user")

# 기본 세션값
defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "expanded": {},
    "adding_cities": [], "pw": "0009", "seen_notices": [], "active_tab": "공지",
    "new_notice": False, "sound_played": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# 다국어 (간단)
LANG = {
    "ko": { "title_base": "칸타타 투어", "caption": "마하라스트라", "tab_notice": "공지", "tab_map": "투어 경로",
            "map_title": "경로 보기", "add_city": "도시 추가", "password": "비밀번호", "login": "로그인",
            "logout": "로그아웃", "wrong_pw": "비밀번호가 틀렸습니다.", "select_city": "도시 선택",
            "venue": "공연장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵 링크",
            "indoor": "실내", "outdoor": "실외", "register": "등록", "edit": "수정", "remove": "삭제",
            "date": "등록일", "performance_date": "공연 날짜", "cancel": "취소", "title_label": "제목",
            "content_label": "내용", "upload_image": "이미지 업로드", "upload_file": "파일 업로드",
            "submit": "등록", "warning": "제목과 내용을 모두 입력해주세요.", "file_download": "파일 다운로드",
            "pending": "미정", "est_time": "{hours}h {mins}m" }
}
_ = lambda key: LANG.get(st.session_state.lang, LANG["ko"]).get(key, key)

# ====== 유틸 함수 ======
def load_json(f):
    try:
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fh:
                return json.load(fh)
    except Exception:
        return []
    return []

def save_json(f, d):
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=2)

def haversine(lat1, lon1, lat2, lon2):
    # km
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c

def format_duration_from_kmh(dist_km, avg_kmh=AVG_SPEED_KMH):
    # dist in km -> returns "Xh Ym" or "Zm"
    if dist_km <= 0:
        return ""
    total_minutes = int(dist_km * 60 / avg_kmh)
    hours = total_minutes // 60
    mins = total_minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"

def compute_bearing(lat1, lon1, lat2, lon2):
    # approximate bearing in degrees for rotation of label (map-space)
    # We compute angle so text aligns parallel to the line from point1 to point2.
    dy = lat2 - lat1
    dx = lon2 - lon1
    # atan2(dx, dy) gives angle relative to north; convert to degrees
    ang = degrees(atan2(dx, dy))
    return ang

# ====== 초기 데이터 (샘플) ======
PUNE_LAT, PUNE_LON = 18.5204, 73.8567
DEFAULT_CITIES = [
    {"city":"Mumbai","venue":"Gateway of India","seats":"5000","note":"인도 영화 수도","google_link":"https://goo.gl/maps/abc123","indoor":False,"lat":19.0760,"lon":72.8777,"perf_date":None,"date":"11/07 02:01"},
    {"city":"Pune","venue":"Shaniwar Wada","seats":"3000","note":"IT 허브","google_link":"https://goo.gl/maps/def456","indoor":True,"lat":18.5204,"lon":73.8567,"perf_date":None,"date":"11/07 02:01"},
    {"city":"Nagpur","venue":"Deekshabhoomi","seats":"2000","note":"오렌지 도시","google_link":"https://goo.gl/maps/ghi789","indoor":False,"lat":21.1458,"lon":79.0882,"perf_date":None,"date":"11/07 02:01"}
]
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

# ====== 공지 기능 (기본) ======
def add_notice(title, content, img=None, file=None):
    img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
    if img: open(img_path,"wb").write(img.read())
    if file: open(file_path,"wb").write(file.read())
    notice = {"id":str(uuid.uuid4()), "title":title, "content":content, "date":datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"), "image":img_path, "file":file_path}
    data = load_json(NOTICE_FILE)
    data.insert(0, notice)
    save_json(NOTICE_FILE, data)
    st.session_state.seen_notices = []
    st.session_state.new_notice = True
    st.session_state.active_tab = "공지"
    st.rerun()

def render_notices():
    data = load_json(NOTICE_FILE)
    has_new = False
    for i, n in enumerate(data):
        new = n["id"] not in st.session_state.seen_notices and not st.session_state.admin
        if new: has_new = True
        title = f"{n['date']} | {n['title']}"
        if new: title += ' <span style="background:#e74c3c;color:white;padding:2px 6px;border-radius:6px">NEW</span>'
        with st.expander(title, expanded=False):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                with open(n["file"], "rb") as fh:
                    b64 = base64.b64encode(fh.read()).decode()
                st.markdown(f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(n["file"])}">파일 다운로드</a>', unsafe_allow_html=True)
            if st.session_state.admin and st.button("삭제", key=f"del_n{i}"):
                data.pop(i); save_json(NOTICE_FILE, data); st.rerun()
            if new and not st.session_state.admin:
                st.session_state.seen_notices.append(n["id"])
    # sound
    if has_new and not st.session_state.get("sound_played", False):
        # 간단히 브라우저 오디오 호출 (base64 placeholder)
        st.markdown("<script> /* play sound */ </script>", unsafe_allow_html=True)
        st.session_state.sound_played = True
    elif not has_new:
        st.session_state.sound_played = False

# ====== 지도 렌더링 ======
def render_map():
    st.subheader(_("map_title"))
    today = date.today()
    raw = load_json(CITY_FILE)
    cities = []
    for c in raw:
        try:
            # normalize perf_date to string or None
            pd = c.get("perf_date")
            if pd is None:
                c["perf_date"] = None
            else:
                # keep string as-is
                c["perf_date"] = str(pd)
            cities.append(c)
        except:
            continue
    # sort by perf_date where None -> end
    def key_fn(x):
        return x.get("perf_date") or "9999-12-31"
    cities = sorted(cities, key=key_fn)

    # admin add form
    if st.session_state.admin:
        with st.expander("도시 추가", expanded=False):
            with st.form("add_city", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    city_name = st.text_input(_("select_city"), placeholder="예: Pune")
                    venue = st.text_input(_("venue"))
                    perf_date_val = st.date_input(_("performance_date"), value=None)
                with col2:
                    seats = st.number_input(_("seats"), min_value=0, step=50, value=500)
                    note = st.text_area(_("note"))
                    gmap = st.text_input(_("google_link"))
                indoor = st.checkbox(_("indoor"), value=True)
                lat = st.number_input("위도 (Lat)", format="%.6f", value=PUNE_LAT)
                lon = st.number_input("경도 (Lon)", format="%.6f", value=PUNE_LON)
                if st.form_submit_button(_("register")):
                    if not city_name.strip() or not venue.strip():
                        st.error("도시명과 장소는 필수입니다.")
                    else:
                        new = {
                            "city": city_name.strip(), "venue": venue.strip(), "seats": str(seats), "note": note.strip(),
                            "google_link": gmap.strip(), "indoor": indoor, "lat": float(lat), "lon": float(lon),
                            "perf_date": str(perf_date_val) if perf_date_val else None,
                            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")
                        }
                        data = load_json(CITY_FILE)
                        data.append(new); save_json(CITY_FILE, data)
                        st.success("등록 완료"); st.rerun()

    # if empty
    if not cities:
        st.warning("아직 등록된 도시가 없습니다.")
        m = folium.Map(location=[PUNE_LAT, PUNE_LON], zoom_start=8, tiles="CartoDB positron")
        folium.CircleMarker(location=[PUNE_LAT, PUNE_LON], radius=8, color="#2ecc71", fill=True, fill_opacity=1).add_to(m)
        st_folium(m, width=900, height=550)
        return

    # create map
    m = folium.Map(location=[PUNE_LAT, PUNE_LON], zoom_start=7, tiles="CartoDB positron")
    coords = []
    total_dist = 0.0

    for i, c in enumerate(cities):
        lat = c.get("lat")
        lon = c.get("lon")
        if lat is None or lon is None:
            continue

        # determine past / today / future
        perf_date = c.get("perf_date")
        try:
            perf_obj = datetime.strptime(perf_date, "%Y-%m-%d").date() if perf_date else None
        except:
            perf_obj = None

        # style based on date
        if perf_obj and perf_obj < today:
            # past -> faded
            fill_opacity = 0.35
            stroke_color = "#9aa0a6"
            radius = 6
        elif perf_obj and perf_obj == today:
            fill_opacity = 1.0
            stroke_color = "#000000"
            radius = 8
        else:
            fill_opacity = 1.0
            stroke_color = "#e74c3c" if c.get("indoor") else "#2475d3"
            radius = 8

        # draw circle marker (no popup)
        try:
            folium.CircleMarker(location=[lat, lon],
                                radius=radius,
                                color=stroke_color,
                                fill=True,
                                fill_color=stroke_color,
                                fill_opacity=fill_opacity,
                                weight=1).add_to(m)
        except Exception:
            pass

        # show city info in sidebar expansion
        with st.expander(f"{c.get('city','(무명)')} | {c.get('perf_date') or _('pending')}"):
            st.write(f"등록일: {c.get('date','—')}")
            st.write(f"공연 날짜: {c.get('perf_date') or _('pending')}")
            st.write(f"장소: {c.get('venue','—')}")
            st.write(f"예상 인원: {c.get('seats','—')}")
            st.write(f"특이사항: {c.get('note','—')}")
            if c.get("google_link"):
                st.markdown(f"[구글맵 보기]({c['google_link']})")
            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("수정", key=f"edit_{i}"):
                        st.session_state.edit_city = c.get("city"); st.rerun()
                with c2:
                    if st.button("삭제", key=f"del_{i}"):
                        data = load_json(CITY_FILE)
                        # remove by matching city & lat/lon roughly
                        for idx, item in enumerate(data):
                            if item.get("city") == c.get("city") and item.get("lat") == c.get("lat") and item.get("lon") == c.get("lon"):
                                data.pop(idx)
                                break
                        save_json(CITY_FILE, data)
                        st.rerun()

        # compute segment info (to next)
        if i < len(cities) - 1:
            nextc = cities[i+1]
            nlat = nextc.get("lat"); nlon = nextc.get("lon")
            if nlat is not None and nlon is not None:
                dist_km = haversine(lat, lon, nlat, nlon)
                total_dist += dist_km
                # compute estimated time using avg speed
                time_str = format_duration_from_kmh(dist_km, AVG_SPEED_KMH)
                # label text: distance + time
                label_text = f"{dist_km:.0f} km"
                if time_str:
                    label_text += f" • {time_str}"

                # midpoint
                mid_lat = (lat + nlat) / 2
                mid_lon = (lon + nlon) / 2

                # bearing for rotation
                angle = compute_bearing(lat, lon, nlat, nlon)
                # create rotated divicon placed slightly above the line:
                # translateY(-10px) to push label above the line; rotate by angle
                div_html = f'''
                    <div style="
                        transform: translate(-50%, -50%) rotate({angle}deg) translateY(-8px);
                        transform-origin: center;
                        white-space: nowrap;
                        font-weight: 600;
                        color: #e74c3c;
                        text-shadow: 0 0 4px rgba(255,255,255,0.8);
                        pointer-events: none;
                        background: rgba(255,255,255,0.0);
                    ">
                        {label_text}
                    </div>
                '''
                try:
                    folium.map.Marker(
                        [mid_lat, mid_lon],
                        icon=folium.DivIcon(html=div_html)
                    ).add_to(m)
                except Exception:
                    # fallback: non-rotated label
                    folium.map.Marker(
                        [mid_lat, mid_lon],
                        icon=folium.DivIcon(html=f'<div style="font-weight:600;color:#e74c3c">{label_text}</div>')
                    ).add_to(m)

        coords.append((lat, lon))

    # draw path if >1 coord
    valid_coords = [c for c in coords if c and None not in c]
    if len(valid_coords) > 1:
        try:
            AntPath(valid_coords, color="#e74c3c", weight=6, opacity=0.9, delay=800).add_to(m)
        except Exception:
            folium.PolyLine(valid_coords, color="#e74c3c", weight=4, opacity=0.8).add_to(m)

    # total distance display
    if len(cities) > 1:
        st.markdown(f"<div style='text-align:center;color:#e74c3c;font-size:1.2em;margin:12px 0'>총 거리: {total_dist:.0f} km</div>", unsafe_allow_html=True)

    # render map
    st_folium(m, width=900, height=550)

# ====== 탭 / UI ======
tab1, tab2 = st.tabs([_("tab_notice"), _("tab_map")])

if st.session_state.get("new_notice", False):
    st.session_state.active_tab = "공지"
    st.session_state.new_notice = False
    st.rerun()

with tab1:
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
    render_map()
