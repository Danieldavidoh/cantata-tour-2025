import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import json, os, uuid, base64, re, requests
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
from math import radians, cos, sin, asin, sqrt

# Haversine 거리 계산
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))  # km

# 새로고침
if not st.session_state.get("admin", False):
    st_autorefresh(interval=3000, key="auto_refresh")

# 기본 설정
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
CITY_LIST_FILE = "cities_list.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 세션 초기화
defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "expanded": {},
    "adding_cities": [], "pw": "0009", "seen_notices": [],
    "active_tab": "notice"
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# 다국어
LANG = {
    "ko": {"title_base": "칸타타 투어", "caption": "마하라스트라",
           "tab_notice": "공지", "tab_map": "투어 경로", "map_title": "경로 보기",
           "add_city": "도시 추가", "password": "비밀번호", "login": "로그인",
           "logout": "로그아웃", "wrong_pw": "비밀번호가 틀렸습니다.",
           "select_city": "도시 선택", "venue": "공연장소", "seats": "예상 인원",
           "note": "특이사항", "google_link": "구글맵 링크",
           "indoor": "실내", "outdoor": "실외", "register": "등록",
           "edit": "수정", "remove": "삭제", "date": "등록일",
           "performance_date": "공연 날짜", "cancel": "취소",
           "title_label": "제목", "content_label": "내용",
           "upload_image": "이미지 업로드", "upload_file": "파일 업로드",
           "submit": "등록", "warning": "제목과 내용을 모두 입력해주세요.",
           "file_download": "파일 다운로드", "change_pw": "비밀번호 변경",
           "new_pw": "새 비밀번호", "confirm_pw": "비밀번호 확인",
           "pw_changed": "비밀번호가 변경되었습니다.",
           "pw_mismatch": "비밀번호가 일치하지 않습니다."}
}
_ = lambda k: LANG[st.session_state.lang].get(k, k)

# === 크리스마스 밤 테마 + 눈 + 알림음 ===
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg,#0f0c29,#302b63,#24243e); color:#f0f0f0; font-family:'Segoe UI',sans-serif; overflow:hidden;}
.christmas-title{text-align:center;margin:20px 0;}
.cantata{font-size:3em;font-weight:bold;color:#e74c3c;text-shadow:0 0 10px #ff6b6b;}
.year{font-size:2.8em;font-weight:bold;color:#ecf0f1;text-shadow:0 0 8px #fff;}
.maha{font-size:1.8em;color:#3498db;font-style:italic;text-shadow:0 0 6px #74b9ff;}
.snowflake{color:rgba(255,255,255,0.5);font-size:1.2em;position:absolute;top:-10px;animation:fall linear forwards;}
@keyframes fall{to{transform:translateY(100vh);opacity:0;}}
</style>
<script>
function createSnowflake(){
 const s=document.createElement('div');
 s.classList.add('snowflake');
 s.innerText=['❅','❆','✻','✼'][Math.floor(Math.random()*4)];
 s.style.left=Math.random()*100+'vw';
 s.style.animationDuration=Math.random()*10+8+'s';
 s.style.opacity=Math.random()*0.4+0.3;
 document.body.appendChild(s);
 setTimeout(()=>s.remove(),18000);
}
setInterval(createSnowflake,400);
function playNotification(){
 const a=new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU'+Array(100).fill('A').join(''));
 a.play().catch(()=>{});
}
</script>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="christmas-title">
<div class="cantata">{_('title_base')}</div>
<div class="year">2025</div>
<div class="maha">{_('caption')}</div>
</div>
""", unsafe_allow_html=True)

# ===== 유틸 =====
def load_json(f): return json.load(open(f,encoding="utf-8")) if os.path.exists(f) else []
def save_json(f,d): json.dump(d,open(f,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
def extract_latlon_from_shortlink(url):
    try:
        r=requests.get(url,allow_redirects=True,timeout=5)
        m=re.search(r'@([0-9\.\-]+),([0-9\.\-]+)',r.url)
        if m: return float(m[1]),float(m[2])
    except: pass
    return None,None

# === 공지 기능 ===
def add_notice(title, content, image=None, file=None):
    img=file_path=None
    if image: img=os.path.join(UPLOAD_DIR,f"{uuid.uuid4()}_{image.name}"); open(img,"wb").write(image.read())
    if file: file_path=os.path.join(UPLOAD_DIR,f"{uuid.uuid4()}_{file.name}"); open(file_path,"wb").write(file.read())
    new={"id":str(uuid.uuid4()),"title":title,"content":content,
         "date":datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"),
         "image":img,"file":file_path}
    data=load_json(NOTICE_FILE); data.insert(0,new); save_json(NOTICE_FILE,data)
    st.session_state.expanded={}; st.session_state.seen_notices=[]
    st.toast("새 공지가 등록되었습니다!"); st.session_state.active_tab="notice"; st.rerun()

def render_notice_list(show_delete=False):
    data=load_json(NOTICE_FILE); has_new=False
    for i,n in enumerate(data):
        nid=n["id"]; is_new=nid not in st.session_state.seen_notices
        if is_new and not st.session_state.admin: has_new=True
        title=f"{n['date']} | {n['title']}"
        with st.expander(title):
            st.markdown(n["content"])
            if n.get("image") and os.path.exists(n["image"]): st.image(n["image"],use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                href=f'<a href="data:file/octet-stream;base64,{base64.b64encode(open(n["file"],"rb").read()).decode()}" download="{os.path.basename(n["file"])}">{_("file_download")}</a>'
                st.markdown(href,unsafe_allow_html=True)
            if show_delete and st.button(_("remove"),key=f"del_{i}"):
                data.pop(i); save_json(NOTICE_FILE,data); st.toast("삭제 완료"); st.rerun()
            if is_new: st.session_state.seen_notices.append(nid)
    if has_new and not st.session_state.get("sound_played",False):
        st.markdown('<script>playNotification();</script>',unsafe_allow_html=True)
        st.session_state.sound_played=True; st.session_state.active_tab="notice"; st.rerun()
    elif not has_new: st.session_state.sound_played=False

# === 지도 ===
def render_map():
    col1,col2=st.columns([5,2])
    with col1: st.subheader(_( "map_title" ))
    with col2:
        if st.session_state.admin and st.button(_( "add_city" ),use_container_width=True):
            st.session_state.adding_cities.append(None); st.rerun()

    cities=load_json(CITY_FILE)
    cities=sorted(cities,key=lambda x:x.get("perf_date","9999-12-31"))
    if not os.path.exists(CITY_LIST_FILE): save_json(CITY_LIST_FILE,["Mumbai","Pune","Nagpur","Nashik","Aurangabad"])
    citylist=load_json(CITY_LIST_FILE)
    exist={c["city"] for c in cities}
    avail=[c for c in citylist if c not in exist]

    for i in range(len(st.session_state.adding_cities)):
        with st.container():
            st.markdown("---")
            col1,col2=st.columns([7,1])
            with col1:
                opts=[None]+avail; cur=st.session_state.adding_cities[i]
                sel=st.selectbox(_( "select_city" ),opts,index=opts.index(cur) if cur in opts else 0,key=f"add_sel_{i}")
                if sel!=cur: st.session_state.adding_cities[i]=sel
            with col2:
                if st.button("×",key=f"deladd_{i}"): st.session_state.adding_cities.pop(i); st.rerun()
            if sel:
                venue=st.text_input(_( "venue" ),key=f"v_{i}")
                seats=st.number_input(_( "seats" ),min_value=0,step=50,key=f"s_{i}")
                date=st.date_input(_( "performance_date" ),key=f"d_{i}")
                vtype=st.radio("공연형태",[_("indoor"),_("outdoor")],horizontal=True,key=f"t_{i}")
                link=st.text_input(_( "google_link" ),key=f"l_{i}")
                note=st.text_area(_( "note" ),key=f"n_{i}")
                c1,c2=st.columns(2)
                with c1:
                    if st.button(_( "register" ),key=f"reg_{i}",use_container_width=True):
                        lat,lon=extract_latlon_from_shortlink(link) if link.strip() else (None,None)
                        if not lat: lat,lon={"Mumbai":(19.07,72.88),"Pune":(18.52,73.86),"Nagpur":(21.15,79.09),"Nashik":(19.99,73.78),"Aurangabad":(19.87,75.34)}.get(sel,(19,73))
                        cities.append({"city":sel,"venue":venue or "미정","seats":seats,"type":vtype,"perf_date":date.strftime("%Y-%m-%d"),
                                       "map_link":link,"note":note or "없음","lat":lat,"lon":lon,
                                       "date":datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")})
                        save_json(CITY_FILE,cities); st.session_state.adding_cities.pop(i)
                        st.success(f"{sel} 등록 완료!"); st.rerun()
                with c2:
                    if st.button(_( "cancel" ),key=f"can_{i}",use_container_width=True):
                        st.session_state.adding_cities.pop(i); st.rerun()

    totald=0; totaltime=0; speed=65
    for i,c in enumerate(cities):
        key=f"exp_{i}"
        with st.expander(f"{c['city']} | {c.get('perf_date','')}"):
            st.write(f"{_('date')}: {c.get('date','')}")
            st.write(f"{_('performance_date')}: {c.get('perf_date','')}")
            st.write(f"{_('venue')}: {c.get('venue','')}")
            st.write(f"{_('seats')}: {c.get('seats','')}")
            st.write(f"{_('note')}: {c.get('note','')}")
            if st.session_state.admin:
                c1,c2=st.columns(2)
                with c1:
                    if st.button(_( "edit" ),key=f"edit_{i}",use_container_width=True):
                        st.session_state.edit_city=c["city"]; st.rerun()
                with c2:
                    if st.button(_( "remove" ),key=f"rem_{i}",use_container_width=True):
                        cities.pop(i); save_json(CITY_FILE,cities); st.toast("삭제됨"); st.rerun()
        if i<len(cities)-1:
            n=cities[i+1]; d=haversine(c["lat"],c["lon"],n["lat"],n["lon"]); t=d/speed
            st.markdown(f'<div style="text-align:center;margin:10px 0;color:#2ecc71;">{d:.0f}km / {t:.1f}h</div>',unsafe_allow_html=True)
            totald+=d; totaltime+=t
    if len(cities)>1:
        st.markdown(f'<div style="text-align:center;margin:20px 0;font-size:1.1em;color:#e74c3c;">총 거리: {totald:.0f}km / {totaltime:.1f}h</div>',unsafe_allow_html=True)

    m=folium.Map(location=[19,73],zoom_start=6)
    coords=[]; today=datetime.now().date()
    for c in cities:
        perf=datetime.strptime(c.get('perf_date'),"%Y-%m-%d").date() if c.get('perf_date') else None
        popup=f"{c['city']}<br>날짜:{c.get('perf_date','')}<br>장소:{c.get('venue','')}<br>인원:{c.get('seats','')}<br>형태:{c.get('type','')}<br><a href='{c.get('map_link','#')}' target='_blank'>길안내</a><br>특이사항:{c.get('note','')}"
        folium.Marker([c["lat"],c["lon"]],popup=popup,tooltip=c["city"],icon=folium.Icon(color="red",icon="music"),opacity=1.0).add_to(m)
        coords.append((c["lat"],c["lon"]))
    if coords: AntPath(coords,color="#e74c3c",weight=5,delay=800).add_to(m)
    st_folium(m,width=900,height=550)

# === 탭 ===
tabs=[_( "tab_notice" ),_( "tab_map" )]
tab=st.session_state.active_tab
idx=0 if tab=="notice" else 1
selected=st.tabs([f"{tabs[0]}",f"{tabs[1]}"])
with selected[0]:
    if st.session_state.admin:
        with st.form("notice_form",clear_on_submit=True):
            t=st.text_input(_( "title_label" ))
            c=st.text_area(_( "content_label" ))
            img=st.file_uploader(_( "upload_image" ),type=["png","jpg","jpeg"])
            f=st.file_uploader(_( "upload_file" ))
            if st.form_submit_button(_( "submit" )):
                if t.strip() and c.strip(): add_notice(t,c,img,f)
                else: st.warning(_( "warning" ))
        render_notice_list(show_delete=True)
    else: render_notice_list(show_delete=False)
with selected[1]: render_map()
