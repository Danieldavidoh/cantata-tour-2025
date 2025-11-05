import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, time

# =============================================
# 기본 설정
# =============================================
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =============================================
# 세션 초기화
# =============================================
if "admin" not in st.session_state:
    st.session_state.admin = False
if "lang" not in st.session_state:
    st.session_state.lang = "ko"
if "last_update" not in st.session_state:
    st.session_state.last_update = 0

# =============================================
# 다국어
# =============================================
LANG = {
    "ko": {
        "title": "칸타타 투어 2025",
        "caption": "마하라스트라 지역 투어 관리 시스템",
        "tab_notice": "공지 관리",
        "tab_map": "투어 경로",
        "add_notice": "새 공지 추가",
        "title_label": "제목",
        "content_label": "내용",
        "upload_image": "이미지 업로드 (선택)",
        "upload_file": "파일 업로드 (선택)",
        "submit": "등록",
        "warning": "제목과 내용을 모두 입력해주세요.",
        "notice_list": "공지 목록",
        "no_notice": "등록된 공지가 없습니다.",
        "delete": "삭제",
        "map_title": "경로 보기",
        "admin_login": "관리자 로그인",
        "password": "비밀번호",
        "login": "로그인",
        "logout": "로그아웃",
        "wrong_pw": "비밀번호가 틀렸습니다.",
        "lang_select": "언어 선택",
        "file_download": "📎 파일 다운로드"
    },
    "en": {
        "title": "Cantata Tour 2025",
        "caption": "Maharashtra Tour Management",
        "tab_notice": "Notice Board",
        "tab_map": "Tour Route",
        "add_notice": "Add Notice",
        "title_label": "Title",
        "content_label": "Content",
        "upload_image": "Upload Image (optional)",
        "upload_file": "Upload File (optional)",
        "submit": "Submit",
        "warning": "Please fill in both title and content.",
        "notice_list": "Notice List",
        "no_notice": "No notices yet.",
        "delete": "Delete",
        "map_title": "View Route",
        "admin_login": "Admin Login",
        "password": "Password",
        "login": "Login",
        "logout": "Logout",
        "wrong_pw": "Wrong password.",
        "lang_select": "Language",
        "file_download": "📎 Download File"
    },
}

_ = LANG[st.session_state.lang]

# =============================================
# JSON 유틸
# =============================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_file_download_link(file_path, label):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">{label}</a>'

# =============================================
# 공지 추가/삭제
# =============================================
def add_notice(title, content, image_file=None, upload_file=None):
    img_path, file_path = None, None

    if image_file:
        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_file.name}")
        with open(img_path, "wb") as f:
            f.write(image_file.read())

    if upload_file:
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{upload_file.name}")
        with open(file_path, "wb") as f:
            f.write(upload_file.read())

    new_notice = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "image": img_path,
        "file": file_path
    }

    data = load_json(NOTICE_FILE)
    data.insert(0, new_notice)
    save_json(NOTICE_FILE, data)
    st.session_state.last_update = os.path.getmtime(NOTICE_FILE)
    st.toast("✅ 공지가 등록되었습니다.")

def delete_notice(notice_id):
    data = load_json(NOTICE_FILE)
    for n in data:
        if n["id"] == notice_id:
            if n.get("image") and os.path.exists(n["image"]):
                os.remove(n["image"])
            if n.get("file") and os.path.exists(n["file"]):
                os.remove(n["file"])
    data = [n for n in data if n["id"] != notice_id]
    save_json(NOTICE_FILE, data)
    st.session_state.last_update = os.path.getmtime(NOTICE_FILE)
    st.toast("🗑️ 공지가 삭제되었습니다.")
    st.rerun()  # ✅ 삭제 시 바로 새로고침

# =============================================
# 공지 리스트
# =============================================
def render_notice_list(show_delete=False):
    data = load_json(NOTICE_FILE)
    if not data:
        st.info(_["no_notice"])
        return
    for idx, n in enumerate(data):
        with st.expander(f"📅 {n['date']} | {n['title']}"):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                st.markdown(get_file_download_link(n["file"], _["file_download"]), unsafe_allow_html=True)
            if show_delete:
                if st.button(_["delete"], key=f"del_{n['id']}_{idx}"):
                    delete_notice(n["id"])

# =============================================
# 지도
# =============================================
def render_map():
    st.subheader(_["map_title"])
    cities = [
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Nashik", "lat": 19.9975, "lon": 73.7898},
    ]
    m = folium.Map(location=[19.0, 73.0], zoom_start=7)
    coords = [(c["lat"], c["lon"]) for c in cities]
    for c in cities:
        folium.Marker([c["lat"], c["lon"]], popup=c["name"], tooltip=c["name"],
                      icon=folium.Icon(color="red", icon="music")).add_to(m)
    AntPath(coords, color="#ff1744", weight=5, delay=800).add_to(m)
    st_folium(m, width=900, height=550)

# =============================================
# 자동 새로고침 (일반 사용자만)
# =============================================
if not st.session_state.admin:
    import streamlit.runtime.scriptrunner as stsr
    from streamlit.runtime.scriptrunner import add_script_run_ctx
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    from streamlit.runtime.legacy_caching import caching

    st_autorefresh = st.experimental_rerun  # 대체: 10초마다 실행
    if os.path.exists(NOTICE_FILE):
        last_update = os.path.getmtime(NOTICE_FILE)
        if last_update != st.session_state.last_update:
            st.toast("🔔 새 공지가 등록되었습니다!")
            st.session_state.last_update = last_update
            st.rerun()
    time.sleep(10)

# =============================================
# 사이드바
# =============================================
with st.sidebar:
    new_lang = st.selectbox(
        _["lang_select"],
        ["ko", "en"],
        format_func=lambda x: {"ko": "한국어", "en": "English"}[x],
        index=["ko", "en"].index(st.session_state.lang)
    )
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")

    if not st.session_state.admin:
        st.markdown(f"### 🔐 {_['admin_login']}")
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0000":
                st.session_state.admin = True
                st.success("✅ 관리자 모드 ON")
                st.rerun()
            else:
                st.error(_["wrong_pw"])
    else:
        st.success("✅ 관리자 모드")
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.rerun()

# =============================================
# 메인
# =============================================
st.markdown(f"# {_['title']} 🎄")
st.caption(_["caption"])

tab1, tab2 = st.tabs([_["tab_notice"], _["tab_map"]])

with tab1:
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_["title_label"])
            c = st.text_area(_["content_label"])
            img = st.file_uploader(_["upload_image"], type=["png", "jpg", "jpeg"])
            f = st.file_uploader(_["upload_file"])
            submitted = st.form_submit_button(_["submit"])

        if submitted:
            if t.strip() and c.strip():
                add_notice(t, c, img, f)
                st.rerun()  # ✅ 폼 바깥 rerun → 즉시 갱신됨
            else:
                st.warning(_["warning"])
        render_notice_list(show_delete=True)
    else:
        render_notice_list(show_delete=False)

with tab2:
    render_map()
