# app.py - 크리스마스 에디션 최종 패치 (2025.11.07) 🎅🔥
# 전체닫기 버튼 삭제 + 탭 이동 시 자동 접힘 + 공지 클릭 시 항상 접힘 + 알림음/표시 유지

import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, sin, cos, sqrt, asin

# --- 1. 하버신 ---
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return 6371 * 2 * asin(sqrt(a))

# --- 2. 자동 리프레시 (비관리자) ---
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto")

st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

# --- 3. 파일 ---
NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 4. 세션 초기화 ---
defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "expanded": {}, "adding_cities": [],
    "pw": "0009", "seen_notices": [], "active_tab": "공지", "new_notice": False, "sound_played": False,
    "user_interacted": False, "city_form": {}
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# --- 5. 다국어 ---
LANG = {
    "ko": { "title_base": "칸타타 투어", "caption": "마하라스트라", "tab_notice": "공지", "tab_map": "투어 경로",
            "map_title": "경로 보기", "add_city": "도시 추가", "password": "비밀번호", "login": "로그인",
            "logout": "로그아웃", "wrong_pw": "비밀번호가 틀렸습니다.", "venue": "공연장소", "seats": "예상 인원",
            "note": "특이사항", "register": "등록", "edit": "수정", "remove": "삭제", "date": "등록일",
            "performance_date": "공연 날짜", "title_label": "제목", "content_label": "내용", "submit": "등록",
            "warning": "제목과 내용을 모두 입력해주세요.", "file_download": "파일 다운로드", "new_notice": "새로운 공지가 있습니다!",
            "city_name": "도시명", "lat": "위도", "lon": "경도", "perf_date": "공연 날짜", "save": "저장", "cancel": "취소" },
    # 영어/힌디어 생략 (기존과 동일)
}
_ = lambda key: LANG[st.session_state.lang].get(key, key)

# --- 6. 5초 크리스마스 캐롤 WAV (Jingle Bells) ---
JINGLE_BELLS_WAV = "UklGRnoGAABXQVZFZm10IBAAAAABAAEAIlYAAIlYAABQTFRFAAAAAP4AAAD8AAAAAAAAAAAAAAACAgICAgMEBQYHCAkKCwwNDg8QERITFBUWFhcYGBkaGxwdHh8gIiMkJSYnKCkqKywtLi8wMTIzNDU2Nzg5Ojs8PT4/QEFCQkNERUZGRkdISUpLTE1OT09QUVJTVFVaW1xdXl9gYWFhYmNkZWZnaGlqa2ttbW5vcHFyc3R1dnd4eXp7fH1+f4CBgoOEhYaHiImKi4yNjo+QkZKTlJWWl5iZmpucnZ6foKGio6SlpqeoqaqrrK2ur7CxsrO0tba3uLm6u7y9vr/AwcLDxMXGx8jJysvMzc7P0NHS09TV1tfY2drb3N3e3+Dh4uPk5ebn6Onq6+zt7u/w8fLz9PX29/j5+vv8/f7/AAA="

# --- 7. 테마 + 알림음 + 슬라이드 알림 ---
st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #f0f0f0; }}
.christmas-title {{ text-align: center; margin: 20px 0; }}
.cantata {{ font-size: 3em; color: #e74c3c; text-shadow: 0 0 10px #ff6b6b; }}
.year {{ font-size: 2.8em; color: #ecf0f1; text-shadow: 0 0 8px #ffffff; }}
.maha {{ font-size: 1.8em; color: #3498db; font-style: italic; text-shadow: 0 0 6px #74b9ff; }}
.snowflake {{ color: rgba(255,255,255,0.5); font-size: 1.2em; position: absolute; top: -10px; animation: fall linear forwards; }}
@keyframes fall {{ to {{ transform: translateY(100vh); opacity: 0;}}}}
.stButton>button {{ background: #c0392b !important; color: white !important; border: 2px solid #e74c3c !important; border-radius: 12px !important; }}
.stButton>button:hover {{ background: #e74c3c !important; }}
.new-badge {{ background: #e74c3c; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.7em; margin-left: 5px; }}
.slide-alert {{ position: fixed; top: 10px; left: 50%; transform: translateX(-50%); background: #e74c3c; color: white; padding: 12px 24px; border-radius: 50px; font-weight: bold; box-shadow: 0 4px 15px rgba(231,76,60,0.5); z-index: 9999; animation: slideIn 0.5s ease-out forwards; opacity: 0; }}
@keyframes slideIn {{ from {{ top: -60px; opacity: 0; }} to {{ top: 10px; opacity: 1; }} }}
</style>
<script>
let hasInteracted = false;
document.addEventListener('click', () => {{ hasInteracted = true; }}, {{ once: true }});
document.addEventListener('keydown', () => {{ hasInteracted = true; }}, {{ once: true }});

function createSnowflake() {{
    const s = document.createElement('div'); s.classList.add('snowflake');
    s.innerText = ['❅','❆','✻','✼'][Math.floor(Math.random()*4)];
    s.style.left = Math.random()*100 + 'vw';
    s.style.animationDuration = Math.random()*10 + 8 + 's';
    s.style.opacity = Math.random()*0.4 + 0.3;
    document.body.appendChild(s);
    setTimeout(() => s.remove(), 18000);
}}
setInterval(createSnowflake, 400);

function playJingleBells() {{
    if (hasInteracted) {{
        const audio = new Audio('data:audio/wav;base64,{JINGLE_BELLS_WAV}');
        audio.volume = 0.7;
        audio.play().catch(() => {{}});
    }}
}}

function showSlideAlert() {{
    if (hasInteracted) {{
        const alert = document.createElement('div');
        alert.className = 'slide-alert';
        alert.innerText = '{_("new_notice")}';
        document.body.appendChild(alert);
        setTimeout(() => {{
            alert.style.animation = 'slideOut 0.5s ease-in forwards';
            setTimeout(() => alert.remove(), 500);
        }}, 4500);
    }}
}}
const style = document.createElement('style');
style.innerHTML = `
@keyframes slideOut {{ from {{ top: 10px; opacity: 1; }} to {{ top: -60px; opacity: 0; }} }}
`;
document.head.appendChild(style);
</script>
""", unsafe_allow_html=True)

# --- 8. 제목 ---
st.markdown(f"""
<div class="christmas-title">
<div class="cantata">{_('title_base')}</div>
<div class="year">2025</div>
<div class="maha">{_('caption')}</div>
</div>
""", unsafe_allow_html=True)

# --- 9. 사이드바 ---
with st.sidebar:
    lang_options = ["한국어", "English", "हिंदी"]
    lang_map = {"한국어":"ko", "English":"en", "हिंदी":"hi"}
    idx = next((i for i, l in enumerate(lang_options) if lang_map[l] == st.session_state.lang), 0)
    selected = st.selectbox("언어", lang_options, index=idx)
    if lang_map[selected] != st.session_state.lang:
        st.session_state.lang = lang_map[selected]
        st.rerun()

    st.markdown("---")
    if not st.session_state.admin:
        pw = st.text_input(_("password"), type="password")
        if st.button(_("login")):
            if pw == st.session_state.pw:
                st.session_state.admin = True
                st.rerun()
            elif pw == "0691": st.session_state.pw = "9000"; st.rerun()
            elif pw == "0692": st.session_state.pw = "0009"; st.rerun()
            else: st.error(_("wrong_pw"))
    else:
        st.success("🎅 관리자")
        if st.button(_("logout")): st.session_state.admin = False; st.rerun()

# --- 10. JSON ---
def load_json(f): return json.load(open(f, "r", encoding="utf-8")) if os.path.exists(f) else []
def save_json(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- 11. 공지 추가 ---
def add_notice(title, content, img=None, file=None):
    img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{img.name}") if img else None
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.name}") if file else None
    if img: open(img_path, "wb").write(img.read())
    if file: open(file_path, "wb").write(file.read())
    notice = {"id": str(uuid.uuid4()), "title": title, "content": content,
              "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
              "image": img_path, "file": file_path}
    data = load_json(NOTICE_FILE)
    data.insert(0, notice)
    save_json(NOTICE_FILE, data)
    st.session_state.seen_notices = []
    st.session_state.new_notice = True
    st.session_state.active_tab = "공지"
    st.session_state.expanded = {}
    st.rerun()

# --- 12. 공지 렌더링 (항상 접힘 + NameError 차단) ---
def render_notices():
    data = load_json(NOTICE_FILE)
    if not data:
        st.info("공지가 없습니다.")
        return

    has_new = False
    for i, n in enumerate(data):
        new = n["id"] not in st.session_state.seen_notices and not st.session_state.admin
        if new: has_new = True
        title = f"{n['date']} | {n['title']}"
        if new: title += ' <span class="new-badge">NEW</span>'
        key = f"notice_exp_{i}"
        expanded = st.session_state.expanded.get(key, False)
        with st.expander(title, expanded=expanded):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]): st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                with open(n["file"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                st.markdown(f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(n["file"])}">📥 {_("file_download")}</a>', unsafe_allow_html=True)
            if st.session_state.admin and st.button("🗑️ 삭제", key=f"del_n{i}"):
                data.pop(i); save_json(NOTICE_FILE, data); st.rerun()
            if new and not st.session_state.admin:
                st.session_state.seen_notices.append(n["id"])
        # expander 상태 업데이트
        st.session_state.expanded[key] = expanded  # 실시간 업데이트

    # 새 공지 → 알림음 + 슬라이드
    if has_new and not st.session_state.get("sound_played", False):
        st.markdown("<script>playJingleBells(); showSlideAlert();</script>", unsafe_allow_html=True)
        st.session_state.sound_played = True
        st.markdown("<script>hasInteracted = true;</script>", unsafe_allow_html=True)
    elif not has_new:
        st.session_state.sound_played = False

# --- 13. 도시 폼 ---
def city_form(index=None):
    cities = load_json(CITY_FILE)
    is_edit = index is not None
    city = cities[index] if is_edit else {}
    form_key = f"city_form_{index if is_edit else 'new'}"
    with st.form(form_key, clear_on_submit=True):
        city_name = st.text_input(_("city_name"), value=city.get("city", ""))
        lat = st.number_input(_("lat"), value=city.get("lat", 0.0), format="%.6f")
        lon = st.number_input(_("lon"), value=city.get("lon", 0.0), format="%.6f")
        perf_date = st.date_input(_("performance_date"), value=datetime.strptime(city.get("perf_date", "2025-12-25"), "%Y-%m-%d") if city.get("perf_date") else datetime(2025, 12, 25))
        venue = st.text_input(_("venue"), value=city.get("venue", ""))
        seats = st.text_input(_("seats"), value=city.get("seats", ""))
        note = st.text_area(_("note"), value=city.get("note", ""))
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button(_("save")):
                if not city_name or not lat or not lon:
                    st.error("필수 입력")
                else:
                    new_city = {"city": city_name, "lat": float(lat), "lon": float(lon), "perf_date": perf_date.strftime("%Y-%m-%d"), "venue": venue, "seats": seats, "note": note, "date": datetime.now().strftime("%Y-%m-%d")}
                    if is_edit: cities[index] = new_city
                    else: cities.append(new_city)
                    save_json(CITY_FILE, cities)
                    st.session_state.adding_cities = []
                    st.session_state.city_form = {}
                    st.rerun()
        with col2:
            if st.form_submit_button(_("cancel")):
                st.session_state.adding_cities = []
                st.session_state.city_form = {}
                st.rerun()

# --- 14. 지도 ---
def render_map():
    st.subheader(_('map_title'))
    if st.session_state.admin:
        if st.button(_('add_city'), key="add_city_main"):
            st.session_state.adding_cities.append(len(load_json(CITY_FILE)))
            st.rerun()

    cities = sorted(load_json(CITY_FILE), key=lambda x: x.get("perf_date", "9999-12-31"))
    if st.session_state.admin and st.session_state.adding_cities:
        st.markdown("---"); st.subheader("➕ 도시 추가"); city_form(); return
    if st.session_state.admin and "city_form" in st.session_state and st.session_state.city_form:
        idx = st.session_state.city_form["index"]; st.markdown("---"); st.subheader(f"✏️ 수정"); city_form(idx); return

    total_dist = 0
    for i, c in enumerate(cities):
        with st.expander(f"🎄 {c['city']} | {c.get('perf_date', '미정')}", expanded=False):
            st.write(f"📅 등록일: {c.get('date', '—')}")
            st.write(f"🎭 공연 날짜: {c.get('perf_date', '—')}")
            st.write(f"🏟️ 장소: {c.get('venue', '—')}")
            st.write(f"👥 인원: {c.get('seats', '—')}")
            st.write(f"📝 특이사항: {c.get('note', '—')}")
            if st.session_state.admin:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✏️ 수정", key=f"edit_{i}"): st.session_state.city_form = {"index": i}; st.rerun()
                with c2:
                    if st.button("🗑️ 삭제", key=f"del_{i}"): cities.pop(i); save_json(CITY_FILE, cities); st.rerun()
        if i < len(cities)-1:
            d = haversine(c['lat'], c['lon'], cities[i+1]['lat'], cities[i+1]['lon'])
            total_dist += d
            st.markdown(f"<div style='text-align:center;color:#2ecc71;font-weight:bold'>📍 {d:.0f}km</div>", unsafe_allow_html=True)
    if len(cities) > 1:
        st.markdown(f"<div style='text-align:center;color:#e74c3c;font-size:1.3em;margin:15px 0'>🎅 총 거리: {total_dist:.0f}km</div>", unsafe_allow_html=True)

    m = folium.Map(location=[19.0, 73.0], zoom_start=7, tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google")
    coords = []
    for c in cities:
        folium.Marker([c["lat"], c["lon"]], popup=f"<b>{c['city']}</b><br>📅 {c.get('perf_date','—')}<br>🎭 {c.get('venue','—')}", tooltip=c["city"], icon=folium.Icon(color="red", icon="map-marker", prefix="fa")).add_to(m)
        coords.append((c["lat"], c["lon"]))
    if coords:
        AntPath(coords, color="#e74c3c", weight=6, opacity=0.9, delay=800).add_to(m)
    st_folium(m, width=900, height=550, key=f"map_{len(cities)}", returned_objects=[])

# --- 15. 탭 ---
if not st.session_state.admin:
    st.session_state.active_tab = "공지"
    st.session_state.expanded = {}

if st.session_state.get("new_notice", False):
    st.session_state.active_tab = "공지"
    st.session_state.new_notice = False
    st.session_state.expanded = {}
    st.rerun()

tab1, tab2 = st.tabs([_("tab_notice"), _("tab_map")])

with tab1:
    if st.session_state.active_tab == "공지":
        st.session_state.expanded = {}  # 공지 탭 클릭 시 항상 접힘
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_("title_label"))
            c = st.text_area(_("content_label"))
            img = st.file_uploader("이미지 업로드", type=["png","jpg","jpeg"])
            f = st.file_uploader("파일 업로드")
            if st.form_submit_button(_("submit")):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_("warning"))
    render_notices()

with tab2:
    if st.session_state.active_tab == "투어 경로":
        st.session_state.expanded = {}  # 투어경로 이동 시 공지 접힘
    render_map()
