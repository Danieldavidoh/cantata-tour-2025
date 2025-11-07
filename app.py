import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, sin, cos, sqrt, asin, atan2, degrees
import requests

# ── 기본 설정 ─────────────────────────────────────
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh_user")

# ── 파일 ───────────────────────────────────────
NOTICE_FILE = "notice.json"
CITY_FILE   = "cities.json"
UPLOAD_DIR  = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── 다국어 (핵심만) ───────────────────────────────
LANG = {
    "ko": {"tab_notice":"공지","tab_map":"투어 경로","today":"오늘","yesterday":"어제",
           "new_notice_alert":"새 공지가 도착했어요!","warning":"제목·내용 입력"},
    "en": {"tab_notice":"Notice","tab_map":"Tour Route","today":"Today","yesterday":"Yesterday",
           "new_notice_alert":"New notice!","warning":"Enter title & content"},
    "hi": {"tab_notice":"सूचना","tab_map":"टूर मार्ग","today":"आज","yesterday":"कल",
           "new_notice_alert":"नई सूचना!","warning":"शीर्षक·सामग्री दर्ज करें"}
}
defaults = {"admin":False,"lang":"ko","edit_city":None,"tab_selection":"공지",
            "new_notice":False,"sound_played":False,"seen_notices":[],"expanded_notices":[],
            "expanded_cities":[],"last_tab":None,"alert_active":False,"current_alert_id":None}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v
_ = lambda k: LANG.get(st.session_state.lang, LANG["ko"]).get(k, k)

# ── 크리스마스 사운드 (Base64) ─────────────────────
CHRISTMAS_CAROL_WAV = "UklGRu4FAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA..."

# ── 알림 CSS (제목 아래 고정) ───────────────────────
st.markdown(f"""
<style>
.stApp{{background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#f0f0f0}}
.christmas-title{{text-align:center;margin:20px 0}}
.cantata{{font-size:3em;color:#e74c3c;text-shadow:0 0 10px #ff6b6b}}
.year{{font-size:2.8em;color:#ecf0f1;text-shadow:0 0 8px #fff}}
.maha{{font-size:1.8em;color:#3498db;font-style:italic;text-shadow:0 0 6px #74b9ff}}
.christmas-alert{{position:fixed;top:140px;right:10%;background:linear-gradient(45deg,#c21500,#ffc500,#ff6b35);
    background-size:400%;color:white;padding:16px 36px;border-radius:70px;font-weight:900;
    font-size:1.3em;z-index:99999;box-shadow:0 0 40px rgba(255,255,255,.8);
    animation:pulseBg 2s infinite,shake .6s infinite alternate;border:4px solid #fff;
    text-shadow:0 0 15px #000;font-family:'Comic Sans MS',cursive;white-space:nowrap}}
.christmas-alert .close-btn{{position:absolute;top:8px;right:12px;background:#c21500;
    color:white;border:none;border-radius:50%;width:28px;height:28px;font-weight:bold;cursor:pointer}}
@keyframes pulseBg{{0%,100%{{background-position:0% 50%}}50%{{background-position:100% 50%}}}}
@keyframes shake{{0%{{transform:translateX(0)}}100%{{transform:translateX(-4px)}}}}
@media(max-width:768px){.christmas-alert{{top:120px;right:5%;font-size:1.1em;padding:12px 24px}}}
</style>
<script>
function playChristmasCarol(){{
    const audio=new Audio('data:audio/wav;base64,{CHRISTMAS_CAROL_WAV}');
    audio.volume=1.0;
    const ctx=new (window.AudioContext||window.webkitAudioContext)();
    const src=ctx.createMediaElementSource(audio);
    const gain=ctx.createGain();gain.gain.value=5;
    src.connect(gain).connect(ctx.destination);
    audio.play().catch(()=>{});
}}
</script>
""", unsafe_allow_html=True)

st.markdown('<div class="christmas-title"><div class="cantata">칸타타 투어</div><div class="year">2025</div><div class="maha">마하라스트라</div></div>', unsafe_allow_html=True)

# ── 사이드바 ───────────────────────────────────
with st.sidebar:
    lang_map={"한국어":"ko","English":"en","हिंदी":"hi"}
    sel=st.selectbox("언어",list(lang_map.keys()),index=list(lang_map.values()).index(st.session_state.lang))
    if lang_map[sel]!=st.session_state.lang:
        st.session_state.lang=lang_map[sel]; st.session_state.tab_selection=_(f"tab_notice"); st.rerun()
    st.markdown("---")
    if not st.session_state.admin:
        pw=st.text_input("비밀번호",type="password",key="pw")
        if st.button("로그인",key="login"):
            if pw=="0009": st.session_state.admin=True; st.rerun()
            else: st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")
        if st.button("로그아웃",key="logout"): st.session_state.admin=False; st.rerun()

# ── JSON 헬퍼 ───────────────────────────────────
def load_json(f): return json.load(open(f,"r",encoding="utf-8")) if os.path.exists(f) else []
def save_json(f,d): json.dump(d,open(f,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

# ── 초기 도시 ───────────────────────────────────
DEFAULT_CITIES=[{"city":"Mumbai","venue":"Gateway of India","seats":"5000","note":"인도 영화 수도",
                 "google_link":"https://goo.gl/maps/abc123","indoor":False,"lat":19.0760,"lon":72.8777,
                 "perf_date":None,"date":"11/07 02:01"},
                {"city":"Pune","venue":"Shaniwar Wada","seats":"3000","note":"IT 허브",
                 "google_link":"https://goo.gl/maps/def456","indoor":True,"lat":18.5204,"lon":73.8567,
                 "perf_date":None,"date":"11/07 02:01"},
                {"city":"Nagpur","venue":"Deekshabhoomi","seats":"2000","note":"오렌지 도시",
                 "google_link":"https://goo.gl/maps/ghi789","indoor":False,"lat":21.1458,"lon":79.0882,
                 "perf_date":None,"date":"11/07 02:01"}]
if not os.path.exists(CITY_FILE): save_json(CITY_FILE,DEFAULT_CITIES)

# ── 거리 계산 (Google API + 폴백) ─────────────────
def get_real_travel_time(lat1,lon1,lat2,lon2):
    try:
        key=st.secrets.get("GOOGLE_API_KEY","")
        if key:
            url="https://maps.googleapis.com/maps/api/distancematrix/json"
            p={"origins":f"{lat1},{lon1}","destinations":f"{lat2},{lon2}","key":key,"mode":"driving"}
            r=requests.get(url,params=p,timeout=5).json()
            if r["rows"][0]["elements"][0]["status"]=="OK":
                d=r["rows"][0]["elements"][0]["distance"]["value"]/1000
                m=r["rows"][0]["elements"][0]["duration"]["value"]//60
                return d,m
    except:pass
    R=6371; dl=radians(lat2-lat1); dn=radians(lon2-lon1)
    a=sin(dl/2)**2+cos(radians(lat1))*cos(radians(lat2))*sin(dn/2)**2
    return R*2*asin(sqrt(a)),int(R*2*asin(sqrt(a))/80*60)

# ── 공지 기능 (일반 사용자만 알림) ─────────────────
def add_notice(title,content,img=None,file=None):
    img_path = os.path.join(UPLOAD_DIR,f"{uuid.uuid4()}_{img.name}") if img else None
    file_path= os.path.join(UPLOAD_DIR,f"{uuid.uuid4()}_{file.name}") if file else None
    if img: open(img_path,"wb").write(img.read())
    if file: open(file_path,"wb").write(file.read())
    notice={"id":str(uuid.uuid4()),"title":title,"content":content,
            "date":datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
            "image":img_path,"file":file_path}
    data=load_json(NOTICE_FILE); data.insert(0,notice); save_json(NOTICE_FILE,data)
    if not st.session_state.admin:
        st.session_state.seen_notices=[]; st.session_state.new_notice=True
        st.session_state.alert_active=True; st.session_state.current_alert_id=notice["id"]
    st.rerun()

def render_notices():
    data=load_json(NOTICE_FILE); has_new=False; latest_id=None
    if not st.session_state.admin:
        for n in data:
            if n["id"] not in st.session_state.seen_notices:
                has_new=True; latest_id=n["id"]
    for i,n in enumerate(data):
        badge=' <span class="new-badge">NEW</span>' if (not st.session_state.admin and n["id"] not in st.session_state.seen_notices) else ''
        title=f"{format_notice_date(n['date'])} | {n['title']}{badge}"
        exp_key=f"notice_{n['id']}"
        expanded=exp_key in st.session_state.expanded_notices
        with st.expander(title,expanded=expanded):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]): st.image(n["image"],width="stretch")
            if n.get("file") and os.path.exists(n["file"]):
                b64=base64.b64encode(open(n["file"],"rb").read()).decode()
                st.markdown(f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(n["file"])}">다운로드</a>',unsafe_allow_html=True)
            if st.session_state.admin and st.button("삭제",key=f"del_n_{n['id']}"):
                data.pop(i); save_json(NOTICE_FILE,data); st.rerun()
            if not st.session_state.admin and n["id"] not in st.session_state.seen_notices:
                st.session_state.seen_notices.append(n["id"])
            if expanded and exp_key not in st.session_state.expanded_notices:
                st.session_state.expanded_notices.append(exp_key)
            elif not expanded and exp_key in st.session_state.expanded_notices:
                st.session_state.expanded_notices.remove(exp_key)
            if not st.session_state.admin and expanded and n["id"]==st.session_state.current_alert_id:
                st.session_state.alert_active=False; st.rerun()
    if not st.session_state.admin and st.session_state.alert_active and st.session_state.current_alert_id:
        st.markdown("<script>playChristmasCarol();</script>",unsafe_allow_html=True)
        st.markdown(f'<div class="christmas-alert"><span>{_("new_notice_alert")}</span><button class="close-btn" onclick="this.parentElement.remove()">×</button></div>',unsafe_allow_html=True)

# ── 지도 (거리·시간 라벨을 **연결선과 평행**하게) ───────
def render_map():
    st.subheader("경로 보기")
    today=date.today()
    raw_cities=load_json(CITY_FILE)
    cities=sorted([c|{"perf_date":c.get("perf_date") if c.get("perf_date") not in [None,"9999-12-31"] else "9999-12-31"} for c in raw_cities],
                  key=lambda x:x["perf_date"] if x["perf_date"]!="9999-12-31" else "9999-12-31")

    m=folium.Map(location=[18.5204,73.8567],zoom_start=9,tiles="CartoDB positron")
    if not cities:
        folium.Marker([18.5204,73.8567],popup="시작",icon=folium.Icon(color="green",icon="star",prefix="fa")).add_to(m)
    else:
        for i,c in enumerate(cities):
            is_past=c.get('perf_date') and c['perf_date']!="9999-12-31" and datetime.strptime(c['perf_date'],"%Y-%m-%d").date()<today
            opacity=0.3 if is_past else 1.0
            folium.Marker([c["lat"],c["lon"]],popup=folium.Popup(f"<b>{c['city']}</b><br>{c.get('perf_date','미정')}<br>{c.get('venue','—')}",max_width=280),
                          tooltip=c["city"],icon=folium.Icon(color="red",icon="music",prefix="fa",opacity=opacity)).add_to(m)

            if i<len(cities)-1:
                nxt=cities[i+1]
                dist,mins=get_real_travel_time(c['lat'],c['lon'],nxt['lat'],nxt['lon'])
                label=f"{dist:.0f}km → {mins//60}h {mins%60}m"
                mid_lat,mid_lon=(c['lat']+nxt['lat'])/2,(c['lon']+nxt['lon'])/2
                bearing=degrees(atan2(nxt['lon']-c['lon'],nxt['lat']-c['lat']))
                # 90° 초과 뒤집힘 방지
                bearing=(bearing+360)%360
                if 90<bearing<270: bearing+=180; bearing%=360
                path_op=0.3 if is_past else 1.0

                folium.Marker([mid_lat,mid_lon],icon=folium.DivIcon(html=f'''
                    <div style="transform:translate(-50%,-50%) rotate({bearing}deg);
                                color:black;font-weight:900;font-size:13px;white-space:nowrap;
                                text-shadow:2px 2px 4px white,-2px -2px 4px white,
                                            2px -2px 4px white,-2px 2px 4px white;
                                opacity:{path_op}">{label}</div>''')).add_to(m)

                AntPath([(c['lat'],c['lon']),(nxt['lat'],nxt['lon'])],
                        color="#e74c3c",weight=6,opacity=path_op,delay=800,dash_array=[20,30]).add_to(m)

            # 도시 expander (수정·삭제)
            exp_key=f"city_{c['city']}"
            expanded=exp_key in st.session_state.expanded_cities
            with st.expander(f"{c['city']} | {c.get('perf_date','미정')}",expanded=expanded):
                for k,v in {"등록일":"date","공연 날짜":"perf_date","장소":"venue","예상 인원":"seats","특이사항":"note"}.items():
                    st.write(f"{k}: {c.get(v,'—')}")
                if c.get("google_link"): st.markdown(f"[구글맵 보기]({c['google_link']})")
                if st.session_state.admin:
                    c1,c2=st.columns(2)
                    with c1:
                        if st.button("수정",key=f"edit_{c['city']}_{i}"):
                            st.session_state.edit_city=c["city"]; st.rerun()
                    with c2:
                        if st.button("삭제",key=f"del_{c['city']}_{i}"):
                            raw_cities=[x for x in raw_cities if x["city"]!=c["city"]]
                            save_json(CITY_FILE,raw_cities); st.rerun()
                if expanded and exp_key not in st.session_state.expanded_cities:
                    st.session_state.expanded_cities.append(exp_key)
                elif not expanded and exp_key in st.session_state.expanded_cities:
                    st.session_state.expanded_cities.remove(exp_key)

    st_folium(m,width=900,height=550,key="tour_map")

# ── 탭 ───────────────────────────────────────
tab_selection=st.radio("탭 선택",[_(f"tab_notice"),_(f"tab_map")],
                       index=0 if st.session_state.tab_selection==_(f"tab_notice") else 1,
                       horizontal=True,key="main_tab")

if tab_selection!=st.session_state.get("last_tab"):
    st.session_state.expanded_notices=[]; st.session_state.expanded_cities=[]
    st.session_state.last_tab=tab_selection; st.rerun()

if st.session_state.get("new_notice",False):
    st.session_state.tab_selection=_(f"tab_notice"); st.session_state.new_notice=False; st.rerun()

# ── 렌더링 ───────────────────────────────────
if tab_selection==_(f"tab_notice"):
    if st.session_state.admin:
        with st.form("notice_form",clear_on_submit=True):
            title=st.text_input("제목"); content=st.text_area("내용")
            img=st.file_uploader("이미지",type=["png","jpg"]); file=st.file_uploader("파일")
            if st.form_submit_button("등록"):
                if title.strip() and content.strip(): add_notice(title,content,img,file)
                else: st.warning(_("warning"))
    render_notices()
else:
    render_map()
