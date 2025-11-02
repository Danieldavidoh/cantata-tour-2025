import streamlit as st
from datetime import date
import uuid # 고유 ID 생성을 위해 사용

# --- 초기 설정 및 데이터 ---

# 언어 설정 데이터 (일정 데이터는 동적 관리를 위해 session_state로 이동)
language_data = {
    "ko": {
        "title": "다니엘 다비도프 칸타타 투어 2025",
        "artist_name": "다니엘 다비도프",
        "tour_name": "칸타타 투어 2025",
        "description": "2025년 다니엘 다비도프의 새로운 칸타타 투어에 오신 것을 환영합니다.",
        "bio_heading": "아티스트 소개",
        "bio_text": "다니엘 다비도프는 현대 클래식 음악계의 떠오르는 별입니다. 그의 칸타타 작품은 전통과 혁신을 결합한 깊은 감동을 선사합니다.",
        "tour_dates_heading": "투어 일정 관리",
        "tickets_button": "티켓 구매하기",
        "contact_heading": "문의",
        "contact_email": "info@danieldavidoh.com",
        "footer_text": "© 2025 다니엘 다비도프. All rights reserved.",
        "register_button": "등록",
        "add_new_tour": "새로운 투어 일정 추가",
    },
    "en": {
        "title": "Daniel Davidoh Cantata Tour 2025",
        "artist_name": "Daniel Davidoh",
        "tour_name": "Cantata Tour 2025",
        "description": "Welcome to Daniel Davidoh's new Cantata Tour in 2025.",
        "bio_heading": "Artist Biography",
        "bio_text": "Daniel Davidoh is a rising star in the contemporary classical music scene. His Cantata works offer profound emotion, blending tradition and innovation.",
        "tour_dates_heading": "Manage Tour Dates",
        "tickets_button": "Buy Tickets",
        "contact_heading": "Contact",
        "contact_email": "info@danieldavidoh.com",
        "footer_text": "© 2025 Daniel Davidoh. All rights reserved.",
        "register_button": "Register",
        "add_new_tour": "Add New Tour Date",
    }
}

# 기본 투어 일정 데이터 (session_state 초기화용)
initial_schedule_ko = [
    {"id": str(uuid.uuid4()), "city": "서울", "date": date(2025, 5, 10), "venue": "예술의전당 콘서트홀", "seats": "2,500석", "gmap_url": "https://goo.gl/maps/example-seoul", "notes": "국립 오케스트라 협연."},
    {"id": str(uuid.uuid4()), "city": "부산", "date": date(2025, 5, 15), "venue": "부산 시민회관 대극장", "seats": "1,600석", "gmap_url": "https://goo.gl/maps/example-busan", "notes": "새로운 칸타타 초연."},
    {"id": str(uuid.uuid4()), "city": "대구", "date": date(2025, 5, 20), "venue": "대구 콘서트 하우스", "seats": "1,000석", "gmap_url": "https://goo.gl/maps/example-daegu", "notes": "특별 게스트 보컬 참여."},
]
initial_schedule_en = [
    {"id": str(uuid.uuid4()), "city": "Seoul", "date": date(2025, 5, 10), "venue": "Seoul Arts Center Concert Hall", "seats": "2,500", "gmap_url": "https://goo.gl/maps/example-seoul", "notes": "In collaboration with the National Orchestra."},
    {"id": str(uuid.uuid4()), "city": "Busan", "date": date(2025, 5, 15), "venue": "Busan Citizens Hall Grand Theater", "seats": "1,600", "gmap_url": "https://goo.gl/maps/example-busan", "notes": "World premiere of a new cantata."},
    {"id": str(uuid.uuid4()), "city": "Daegu", "date": date(2025, 5, 20), "venue": "Daegu Concert House", "seats": "1,000", "gmap_url": "https://goo.gl/maps/example-daegu", "notes": "Featuring special guest vocalist."},
]

# session_state 초기화 함수
def initialize_session_state(lang_code):
    if "schedule" not in st.session_state:
        if lang_code == "ko":
            st.session_state.schedule = initial_schedule_ko
        else:
            st.session_state.schedule = initial_schedule_en
    if "is_adding_new" not in st.session_state:
        st.session_state.is_adding_new = False
    if "temp_new_city" not in st.session_state:
        st.session_state.temp_new_city = ""
        st.session_state.temp_new_date = date.today()
        st.session_state.temp_new_venue = ""
        st.session_state.temp_new_seats = ""
        st.session_state.temp_new_gmap = ""
        st.session_state.temp_new_notes = ""


# --- 함수 정의 ---

def save_tour_details(schedule_id, city, date_obj, venue, seats, gmap_url, notes):
    """특정 ID를 가진 일정의 세부 정보를 업데이트합니다."""
    for item in st.session_state.schedule:
        if item["id"] == schedule_id:
            item.update({
                "city": city,
                "date": date_obj,
                "venue": venue,
                "seats": seats,
                "gmap_url": gmap_url,
                "notes": notes,
            })
            break

def add_new_tour_date():
    """새로운 투어 일정을 목록에 추가합니다."""
    new_item = {
        "id": str(uuid.uuid4()),
        "city": st.session_state.temp_new_city,
        "date": st.session_state.temp_new_date,
        "venue": st.session_state.temp_new_venue,
        "seats": st.session_state.temp_new_seats,
        "gmap_url": st.session_state.temp_new_gmap,
        "notes": st.session_state.temp_new_notes,
    }
    st.session_state.schedule.append(new_item)
    
    # 임시 상태 초기화 및 폼 닫기
    st.session_state.is_adding_new = False
    st.session_state.temp_new_city = ""
    st.session_state.temp_new_date = date.today()
    st.session_state.temp_new_venue = ""
    st.session_state.temp_new_seats = ""
    st.session_state.temp_new_gmap = ""
    st.session_state.temp_new_notes = ""
    st.toast("새로운 일정이 추가되었습니다!", icon="✅")

# --- Streamlit 앱 로직 시작 ---

# 언어 선택 (사이드바)
lang = st.sidebar.selectbox("Language / 언어", ["ko", "en"])
t = language_data[lang]

# 세션 상태 초기화 (선택된 언어에 따라)
initialize_session_state(lang)

# 메인 레이아웃 설정
st.set_page_config(page_title=t["title"], layout="wide")

st.title(t["title"])
st.subheader(f"{t['artist_name']} - {t['tour_name']}")

st.markdown("---")

# 투어 소개
st.header(t["description"])
st.image("https://placehold.co/1200x400/0A192F/AABBCF?text=Cantata+Tour+2025+Poster", use_column_width=True)

st.markdown("---")

# 아티스트 소개 섹션
st.subheader(t["bio_heading"])
st.info(t["bio_text"])

st.markdown("---")

# 투어 일정 관리 섹션
st.subheader(t["tour_dates_heading"])

# 새 일정 추가 버튼
if st.button(t["add_new_tour"], disabled=st.session_state.is_adding_new):
    st.session_state.is_adding_new = True

# 새 일정 추가 폼
if st.session_state.is_adding_new:
    with st.form(key="new_tour_form", clear_on_submit=False):
        st.markdown("**새 투어 정보 입력**")
        
        # 2열 레이아웃
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.temp_new_city = st.text_input("도시명", key="new_city_input")
            st.session_state.temp_new_date = st.date_input("공연 날짜", key="new_date_input", min_value=date.today())
            st.session_state.temp_new_venue = st.text_input("공연 장소", key="new_venue_input")
            st.session_state.temp_new_seats = st.text_input("좌석 수", key="new_seats_input")
        
        with col2:
            st.session_state.temp_new_notes = st.text_area("특이 사항", key="new_notes_input", height=100)
            st.session_state.temp_new_gmap = st.text_input("구글맵 링크", key="new_gmap_input", help="내비게이션에 사용할 구글맵 URL을 입력하세요.")
        
        # 등록 버튼 (오른쪽 정렬)
        submit_col_left, submit_col_right = st.columns([5, 1])
        with submit_col_right:
            st.form_submit_button(t["register_button"], on_click=add_new_tour_date, 
                                  help="입력한 정보를 저장하고 새 일정 추가 창을 닫습니다.")
        
    st.markdown("---")

# 기존 일정 리스트 및 수정 폼
for i, item in enumerate(st.session_state.schedule):
    # 닫힌 박스 (City, Date, Map Icon)
    collapsed_cols = st.columns([3, 3, 1])
    
    # 닫힌 상태에서 City와 Date 표시
    collapsed_cols[0].markdown(f"**{item['city']}**")
    collapsed_cols[1].markdown(f"**{item['date'].strftime('%Y년 %m월 %d일') if isinstance(item['date'], date) else item['date']}**")

    # 구글맵 아이콘 (오른쪽 끝)
    if item['gmap_url']:
        # 클릭 시 구글맵 내비게이션으로 바로 연결
        # 📍 아이콘을 사용하여 내비게이션 링크를 만듭니다.
        # Streamlit에서는 직접적인 '내비게이션 시작' API 접근이 어려우므로, 링크를 제공합니다.
        # 구글맵 링크는 보통 https://www.google.com/maps/dir/?api=1&destination=VENUE_NAME_OR_LAT_LNG 형식으로 내비게이션 시작을 지원하지만,
        # 사용자가 입력한 URL을 그대로 사용합니다.
        link_markdown = f'<a href="{item["gmap_url"]}" target="_blank" style="text-decoration: none; font-size: 24px;" title="구글맵 내비게이션으로 이동">📍</a>'
        collapsed_cols[2].markdown(link_markdown, unsafe_allow_html=True)

    # 클릭하면 펼쳐지는 입력/수정 폼
    with st.expander(f"**{item['city']}** 세부 정보 수정 (클릭하여 펼치기)"):
        with st.form(key=f"edit_form_{item['id']}"):
            
            # 현재 값들을 미리 가져옵니다. (날짜는 date 객체로 변환하여 사용)
            current_date_obj = item['date'] if isinstance(item['date'], date) else date.fromisoformat(item['date'])

            col_edit_1, col_edit_2 = st.columns(2)
            
            with col_edit_1:
                # 도시명 (수정 불가하도록 표시)
                st.markdown(f"**도시명:** {item['city']}")
                
                # 공연 날짜 (달력 클릭만)
                new_date = st.date_input("공연 날짜", value=current_date_obj, key=f"date_{item['id']}", min_value=date.today())
                
                # 공연 장소 (직접 입력)
                new_venue = st.text_input("공연 장소", value=item['venue'], key=f"venue_{item['id']}")
                
                # 좌석 수 (직접 입력)
                new_seats = st.text_input("좌석 수", value=item['seats'], key=f"seats_{item['id']}")

            with col_edit_2:
                # 특이 사항 (직접 입력)
                new_notes = st.text_area("특이 사항", value=item['notes'], key=f"notes_{item['id']}", height=100)
                
                # 구글맵 링크 (직접 입력)
                new_gmap_url = st.text_input("구글맵 링크", value=item['gmap_url'], key=f"gmap_{item['id']}", help="내비게이션에 사용할 구글맵 URL을 입력하세요.")

            # 등록 버튼 (오른쪽 정렬)
            submit_col_left, submit_col_right = st.columns([5, 1])
            with submit_col_right:
                submitted = st.form_submit_button(t["register_button"], 
                    on_click=save_tour_details,
                    args=(item['id'], item['city'], new_date, new_venue, new_seats, new_gmap_url, new_notes),
                    help="수정된 정보를 저장하고 창을 닫습니다."
                )
                if submitted:
                    # 폼 제출 후에는 Streamlit이 재실행되어 변경 사항이 반영되고 Expander가 닫힙니다.
                    st.toast(f"{item['city']} 일정이 업데이트되었습니다!", icon="💾")

    st.markdown("---", help="구분선") # 각 항목을 명확하게 구분

st.markdown("---")

# 티켓 구매 버튼
if st.button(t["tickets_button"]):
    st.balloons()
    st.toast("티켓 예매 페이지로 이동합니다! (가상)", icon="🎉")

st.markdown("---")

# 문의 섹션 (푸터 역할)
st.markdown(f"**{t['contact_heading']}**: [{t['contact_email']}](mailto:{t['contact_email']})")
st.caption(t["footer_text"])

# Streamlit 앱 실행: streamlit run app.py
