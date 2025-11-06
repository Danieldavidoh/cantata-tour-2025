import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, cos, sin, asin, sqrt

# =============================================
# 거리 계산
# =============================================
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * asin(sqrt(a)) * 6371  # km

# =============================================
# 기본 세팅
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh")

NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =============================================
# 세션 초기값
# =============================================
defaults = {
    "admin": False, "lang": "ko", "pw": "0009",
    "edit_city": None, "expanded": {}, "adding_cities": [],
    "seen_notices": []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================================
# 다국어
# =============================================
LANG = {
    "ko": {"tab_notice": "공지", "tab_map": "투어 경로", "map_title": "경로 보기",
           "add_city": "도시 추가", "select_city": "도시 선택", "venue": "공연장소",
           "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵 링크",
           "indoor": "실내", "outdoor": "실외", "register": "등록", "cancel": "취소",
           "edit": "수정", "remove": "삭제", "date": "등록일", 
           "performance_date": "공연 날짜", "title_label": "제목", 
           "content_label": "내용", "upload_image": "이미지 업로드", 
           "upload_file": "파일 업로드", "submit": "등록", "warning": "제목과 내용을 모두 입력해주세요.",
           "file_download": "파일 다운로드"},
    "en": {"tab_notice": "Notice", "tab_map": "Tour Route", "map_title": "View Route",
           "add_city": "Add City", "select_city": "Select City", "venue": "Venue",
           "seats": "Expected Attendance", "note": "Notes", "google_link": "Google Maps Link",
           "indoor": "Indoor", "outdoor": "Outdoor", "register": "Register", "cancel": "Cancel",
           "edit": "Edit", "remove": "Remove", "date": "Date",
           "performance_date": "Performance Date", "title_label": "Title",
           "content_label": "Content", "upload_image": "Upload Image",
           "upload_file": "Upload File", "submit": "Submit", 
           "warning": "Please enter both title and content.",
           "file_download": "Download File"}
}
_ = lambda k: LANG[st.session_state.lang].get(k, k)

# =============================================
# JSON 유틸
# =============================================
def load_json(f):
    if os.path.exists(f):
        with open(f, encoding="utf-8") as j:
            return json.load(j)
    return []

def save_json(f, d):
    with open(f, "w", encoding="utf-8") as j:
        json.dump(d, j, ensure_ascii=False, indent=2)

def extract_latlon_from_shortlink(short_url):
    try:
        r = requests.get(short_url, allow_redirects=True, timeout=5)
        match = re.search(r'@([0-9\.\-]+),([0-9\.\-]+)', r.url)
        if match:
            return float(match.group(1)), float(match.group(2))
    except:
        return (None, None)
    return (None, None)

# =============================================
# 공지사항
# =============================================
def add_notice(title, content, image_file=None, upload_file=None):
    img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_file.name}") if image_file else None
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{upload_file.name}") if upload_file else None
    if image_file: open(img_path, "wb").write(image_file.read())
    if upload_file: open(file_path, "wb").write(upload_file.read())

    data = load_json(NOTICE_FILE)
    data.insert(0, {
        "id": str(uuid.uuid4()), "title": title, "content": content,
        "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
        "image": img_path, "file": file_path
    })
    save_json(NOTICE_FILE, data)
    st.session_state.expanded, st.session_state.seen_notices = {}, []
    st.toast("공지가 등록되었습니다.")
    st.rerun()

def render_notice_list(show_delete=False):
    data = load_json(NOTICE_FILE)
    expanded_any = False

    for i, n in enumerate(data):
        key = f"notice_{i}"
        exp = st.session_state.expanded.get(key, False)
        with st.expander(f"{n['date']} | {n['title']}", expanded=exp):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                href = f'<a href="data:file/octet-stream;base64,{base64.b64encode(open(n["file"],"rb").read()).decode()}" download="{os.path.basename(n["file"])}">🎁 {_("file_download")}</a>'
                st.markdown(href, unsafe_allow_html=True)
            if show_delete and st.button(_("remove"), key=f"del_{i}"):
                data.pop(i); save_json(NOTICE_FILE, data); st.toast("삭제됨"); st.rerun()
        if exp: expanded_any = True
        st.session_state.expanded[key] = exp

    # 닫기 버튼 표시 조건
    if not st.session_state.admin and expanded_any:
        st.markdown(
            """
            <div style='text-align:right; margin-top:-20px;'>
                <button onclick="window.parent.postMessage('close_all', '*')" 
                style='background:#c0392b;color:white;border:none;padding:8px 14px;
                border-radius:8px;font-weight:bold;cursor:pointer;'>닫기</button>
            </div>
            <script>
            window.addEventListener('message', (e)=>{
              if(e.data==='close_all'){ 
                 const checkboxes=document.querySelectorAll('details');
                 checkboxes.forEach(d=>{d.open=false;});
              }
            });
            </script>
            """, unsafe_allow_html=True
        )

# =============================================
# 지도 및 도시 관리
# =============================================
def render_map():
    st.subheader(f"🗺️ {_('map_title')}")
    cities_data = load_json(CITY_FILE)
    cities_data = sorted(cities_data, key=lambda x: x.get("perf_date","9999-12-31"))

    # 지도 먼저 표시
    st.markdown("### 🎄 지도 보기")
    m = folium.Map(location=[19.0, 73.0], zoom_start=6)
    coords = []
    today = datetime.now().date()

    # popup 스타일 (한줄 유지)
    style = "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:220px;"
    for c in cities_data:
        popup_html = f"""
        <div style="{style}">
        <b>{c['city']}</b> | {c.get('perf_date','')}<br>
        {c.get('venue','')} | {c.get('seats','')}명 | {c.get('type','')}<br>
        <a href="{c.get('map_link','#')}" target="_blank">길안내</a><br>
        📝 {c.get('note','')}
        </div>
        """
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=popup_html,
            tooltip=c["city"],
            icon=folium.Icon(color="red", icon="music")
        ).add_to(m)
        coords.append((c["lat"], c["lon"]))

    if coords:
        AntPath(coords, color="#e74c3c", weight=5, delay=800).add_to(m)
    st_folium(m, width=900, height=550)

    # 지도 아래 도시 목록/편집
    st.markdown("---")
    for idx, c in enumerate(cities_data):
        with st.expander(f"🎁 {c['city']} | {c.get('perf_date','')}"):
            st.write(f"🏛️ {c['venue']} | 👥 {c['seats']} | 🗓 {c['perf_date']}")
            st.write(f"📝 {c['note']}")

# =============================================
# 탭 구성
# =============================================
tab1, tab2 = st.tabs([f"🎁 {_('tab_notice')}", f"🗺️ {_('tab_map')}"])

with tab1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_("title_label"))
            c = st.text_area(_("content_label"))
            i = st.file_uploader(_("upload_image"), type=["png","jpg","jpeg"])
            f = st.file_uploader(_("upload_file"))
            if st.form_submit_button(_("submit")):
                if t.strip() and c.strip(): add_notice(t, c, i, f)
                else: st.warning(_("warning"))
        render_notice_list(True)
    else:
        render_notice_list(False)

with tab2:
    render_map()
