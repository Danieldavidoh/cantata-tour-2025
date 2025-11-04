import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from math import radians, sin, cos, sqrt, atan2
import json
import os
import uuid

# =============================================
# 파일 저장
# =============================================
VENUE_FILE = "venue_data.json"
NOTICE_FILE = "notice_data.json"


def load_venue_data():
    if os.path.exists(VENUE_FILE):
        with open(VENUE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_venue_data(data):
    with open(VENUE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_notice_data():
    if os.path.exists(NOTICE_FILE):
        with open(NOTICE_FILE, "r") as f:
            return json.load(f)
    return []


def save_notice_data(data):
    with open(NOTICE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =============================================
# Streamlit 기본 상태
# =============================================
st.set_page_config(page_title="Cantata Tour", layout="wide")
if "lang" not in st.session_state: st.session_state.lang = "ko"
if "admin" not in st.session_state: st.session_state.admin = False
if "route" not in st.session_state: st.session_state.route = []
if "expand_all" not in st.session_state: st.session_state.expand_all = True

# 공유 데이터 로드
st.session_state.venue_data = load_venue_data()
st.session_state.notice_data = load_notice_data()
if "new_notice" not in st.session_state: st.session_state.new_notice = False
if "viewed_notice" not in st.session_state: st.session_state.viewed_notice = set()

# 간단한 언어팩 (원본에서 일부 항목만 사용)
LANG = {
    "ko": {"title": "칸타타 투어", "subtitle": "마하라슈트라", "select_city": "도시 선택", "add_city": "추가",
           "register": "등록", "venue": "공연장", "seats": "좌석 수", "indoor": "실내", "outdoor": "실외",
           "google": "구글 지도 링크", "notes": "특이사항", "tour_map": "투어 지도", "tour_route": "경로",
           "password": "관리자 비밀번호", "login": "로그인", "logout": "로그아웃", "date": "공연 날짜",
           "total": "총 거리 및 소요시간", "already_added": "이미 추가된 도시입니다.", "lang_name": "한국어",
           "notice_title": "공지 제목", "notice_content": "공지 내용", "notice_button": "공지", "new_notice": "새로운 공지",
           "notices": "이전 공지"}
}
_ = LANG[st.session_state.lang]

# =============================================
# Helper: 거리 계산
# =============================================
def distance_km(p1, p2):
    R = 6371
    lat1, lon1 = radians(p1[0]), radians(p1[1])
    lat2, lon2 = radians(p2[0]), radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# =============================================
# 간단한 도시/좌표 (생략된 목록 중 일부만 사용)
# =============================================
cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Thane"]
coords = {"Mumbai": (19.0760,72.8777), "Pune": (18.5204,73.8567), "Nagpur": (21.1458,79.0882), "Nashik": (19.9975,73.7898), "Thane": (19.2183,72.9781)}

# =============================================
# 사이드바: 관리자 로그인
# =============================================
with st.sidebar:
    st.write("**Admin**")
    if not st.session_state.admin:
        pw = st.text_input(_["password"], type="password")
        if st.button(_["login"]):
            if pw == "0691":
                st.session_state.admin = True
                st.success("관리자 모드 활성화")
                st.experimental_rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
    else:
        if st.button(_["logout"]):
            st.session_state.admin = False
            st.experimental_rerun()

# =============================================
# 스타일 (공지 말풍선 / 메가폰 아이콘 등)
# =============================================
st.markdown("""
<style>
.notice-bubble{
  position:fixed;
  left:50%;
  top:35%;
  transform:translate(-50%,-50%);
  background: rgba(255,255,255,0.96);
  color:#000;
  padding:20px;
  border-radius:12px;
  width:60%;
  box-shadow:0 8px 30px rgba(0,0,0,0.6);
  z-index:9999;
}
.notice-list{background:transparent; color:#ddd}
.notice-button{font-weight:800}
.new-pill{background:#ff3b3b; color:white; padding:2px 8px; border-radius:12px; margin-left:6px}
.megaphone{font-size:18px; margin-left:6px}
</style>
""", unsafe_allow_html=True)

# =============================================
# Title
# =============================================
st.markdown(f"<h1 style='text-align:center; color:#ff3333'>{_['title']} <span style='color:#fff'>2025 🎄</span></h1><h2 style='text-align:center; color:#ccc'>{_['subtitle']}</h2>", unsafe_allow_html=True)

# =============================================
# Layout: 좌/우
# =============================================
left, right = st.columns([1,2])

# 관리자 모드에서는 제목 밑 -> 공지 입력란을 보여주고,
# 일반모드(비관리자)에서는 도시선택 블럭을 제거하고 오직 제목과 투어지도만 보여준다.

# Right panel always shows map
with right:
    st.subheader(_["tour_map"])
    m = folium.Map(location=(19.75,75.71), zoom_start=6, tiles="CartoDB positron")
    points = [coords[c] for c in st.session_state.route if c in coords]
    if len(points) >= 2:
        AntPath(points, color="red", weight=4, delay=800).add_to(m)
    for c in st.session_state.route:
        if c in coords:
            data = st.session_state.venue_data.get(c, {})
            popup = f"<b>{c}</b><br>"
            if "date" in data:
                popup += f"{data['date']}<br>{data['venue']}<br>Seats: {data['seats']}<br>{data['type']}<br>"
            if "google" in data and data["google"]:
                popup += f"<a href='{data['google']}' target='_blank'>Google Maps</a>"
            folium.Marker(coords[c], popup=popup,
                          icon=folium.Icon(color="red", icon="music", prefix="fa")).add_to(m)
    st_folium(m, width=900, height=650)

# Left panel
with left:
    # -----------------------------
    # 관리자 전용: 공지 입력란 (제목 밑, 도시선택 앞)
    # -----------------------------
    if st.session_state.admin:
        st.markdown("### Admin: Post Notice")
        n_title = st.text_input(_["notice_title"], key="admin_notice_title")
        n_content = st.text_area(_["notice_content"], key="admin_notice_content")
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("공지 등록", key="post_notice"):
                if n_title.strip() and n_content.strip():
                    notice = {
                        "id": str(uuid.uuid4()),
                        "title": n_title.strip(),
                        "content": n_content.strip(),
                        "time": datetime.utcnow().isoformat() + "Z"
                    }
                    st.session_state.notice_data.insert(0, notice)
                    save_notice_data(st.session_state.notice_data)
                    # 모든 입력칸 접히도록: expand_all False
                    st.session_state.expand_all = False
                    # 새 공지 플래그 설정 (다른 세션이 감지 가능하게 저장)
                    st.session_state.new_notice = True
                    st.success("공지 등록됨. 모든 입력칸이 접혔습니다.")
                    st.experimental_rerun()
                else:
                    st.error("제목과 내용을 모두 입력하세요.")
        with col2:
            if st.button("미리보기", key="preview_notice"):
                st.info(f"{n_title}\n\n{n_content}")

    # -----------------------------
    # 일반/관리자 공통: 도시 선택(관리자일때만)
    # -----------------------------
    if st.session_state.admin:
        c1, c2 = st.columns([3,1])
        with c1:
            selected_city = st.selectbox(_["select_city"], cities, key="select_city")
        with c2:
            if st.button(_["add_city"], key="add_city"):
                if selected_city not in st.session_state.route:
                    st.session_state.route.append(selected_city)
                    st.experimental_rerun()
                else:
                    st.warning(_["already_added"])
    else:
        # 일반모드: 도시선택 블럭 제거 (요청사항)
        # 대신 공지 버튼을 보여줌 (도시선택 추가버튼 반대쪽의 위치 역할)
        btn_col1, btn_col2 = st.columns([1,1])
        with btn_col1:
            st.write("")
        with btn_col2:
            # 최신 공지 확인 버튼
            latest_notice = st.session_state.notice_data[0] if st.session_state.notice_data else None
            unread = latest_notice and (latest_notice["id"] not in st.session_state.viewed_notice)
            label = _["notice_button"]
            if unread:
                label = f"{_["new_notice"]} 🔊"
            if st.button(label, key="view_notice_button"):
                if latest_notice:
                    # 사용자에서 공지 확인 처리
                    st.session_state.viewed_notice.add(latest_notice["id"])
                    # 만약 모든 사용자가 확인하면 new_notice 플래그는 관리자가 끄도록 하거나 타임아웃
                    # 여기서는 로컬 세션에서만 처리됩니다.
                    # 공지 내용을 중간 말풍선으로 보여주기
                    st.markdown(f"<div class='notice-bubble'><h3>{latest_notice['title']}</h3><p>{latest_notice['content']}</p><div style='text-align:right'><button onclick=\"window.location.reload()\">확인</button></div></div>", unsafe_allow_html=True)
                else:
                    st.info("등록된 공지가 없습니다.")

    # -----------------------------
    # 관리자 모드: 투어 경로 입력 (접힘 제어 가능)
    # 일반모드: 요청대로 경로 블럭 제거
    # -----------------------------
    if st.session_state.admin:
        st.markdown("---")
        st.subheader(_["tour_route"])
        total_distance = 0.0
        total_hours = 0.0
        for i, c in enumerate(st.session_state.route):
            # expander의 열린/접힘 상태는 st.session_state.expand_all에 따름
            with st.expander(f"{c}", expanded=st.session_state.expand_all):
                today = datetime.now().date()
                date = st.date_input(_["date"], value=today, min_value=today, key=f"date_{c}")
                venue = st.text_input(_["venue"], key=f"venue_{c}")
                seats = st.number_input(_["seats"], min_value=0, step=50, key=f"seats_{c}")
                google = st.text_input(_["google"], key=f"google_{c}")
                notes = st.text_area(_["notes"], key=f"notes_{c}")
                io = st.radio("Type", [_["indoor"], _["outdoor"]], key=f"io_{c}")
                if st.button(_["register"], key=f"reg_{c}"):
                    st.session_state.venue_data[c] = {
                        "date": str(date), "venue": venue, "seats": seats,
                        "type": io, "google": google, "notes": notes
                    }
                    save_venue_data(st.session_state.venue_data)
                    st.success("저장되었습니다.")
                    # 접힘 처리
                    st.session_state.expand_all = False
                    st.experimental_rerun()

            if i > 0:
                prev = st.session_state.route[i - 1]
                if prev in coords and c in coords:
                    dist = distance_km(coords[prev], coords[c])
                    time_hr = dist / 60.0
                    total_distance += dist
                    total_hours += time_hr
                    st.markdown(f"<p style='text-align:center; color:#90EE90; font-weight:bold; margin:5px 0;'>{dist:.1f} km / {time_hr:.1f} 시간</p>", unsafe_allow_html=True)

        if len(st.session_state.route) > 1:
            st.markdown("---")
            st.markdown(f"### {_['total']}")
            st.success(f"**{total_distance:.1f} km** | **{total_hours:.1f} 시간**")

    # -----------------------------
    # 공지 목록 (모두에게 보여짐)
    # 아래에는 이전 공지들이 쌓임
    # -----------------------------
    st.markdown("---")
    st.subheader(_["notices"])
    if st.session_state.notice_data:
        for n in st.session_state.notice_data:
            seen = n["id"] in st.session_state.viewed_notice
            badge = "" if seen else "<span class='new-pill'>NEW</span>"
            st.markdown(f"**{n['title']}** <small>({n['time']})</small> {badge}")
            st.write(n['content'])
            st.markdown("---")
    else:
        st.info("공지사항이 없습니다.")

# =============================================
# 앱 시작시: 새로운 공지가 있고 사용자가 확인하지 않았다면
# - 앱이 켜지지 않은 상태에서 푸시를 보내려면 Firebase Cloud Messaging(FCM) 등
#   별도 푸시 서비스와 모바일 앱(네이티브) 구현이 필요합니다. Streamlit만으로는 불가능합니다.
# - 대신 앱을 켰을 때 새 공지가 있으면 자동으로 소리와 팝업(중간 말풍선)으로 알려줄 수 있습니다.
# =============================================

latest = st.session_state.notice_data[0] if st.session_state.notice_data else None
if latest and latest['id'] not in st.session_state.viewed_notice:
    # 페이지가 로드될 때 자동으로 알림 재생 및 큰 팝업을 띄움
    play_html = f"""
    <script>
    // Web Audio API로 간단한 비프음 재생
    try{{
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      var o = ctx.createOscillator();
      var g = ctx.createGain();
      o.type = 'sine';
      o.frequency.value = 880;
      o.connect(g);
      g.connect(ctx.destination);
      o.start();
      g.gain.exponentialRampToValueAtTime(0.00001, ctx.currentTime + 0.6);
      setTimeout(function(){o.stop();}, 700);
    }}catch(e){{console.log(e)}}
    </script>
    <div class='notice-bubble'>
      <h3>{latest['title']}</h3>
      <p>{latest['content']}</p>
      <div style='text-align:right'><button onclick="window.location.href=window.location.href+'#ack';">확인</button></div>
    </div>
    """
    st.components.v1.html(play_html, height=1)

# =============================================
# 주의 및 설명 (로그 메시지)
# =============================================
st.markdown("""
**알림:**
- "앱을 켜지 않은 상태"에서 푸시 알림을 보내려면 **Firebase Cloud Messaging(FCM)** 같은
  푸시 서비스와 모바일 네이티브 앱(또는 PWA) 연동이 필요합니다. Streamlit만으로는 시스템 푸시가 불가능합니다.
- 이 예제에서는 앱이 열린 세션에서 자동 새로고침(사용자 브라우저가 열려있을 때) 시 새 공지를 감지하여
  소리와 팝업을 재생하도록 구현했습니다.
""")
