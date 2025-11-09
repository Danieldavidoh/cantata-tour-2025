import streamlit as st
from datetime import datetime, timedelta
from collections import OrderedDict

# --- 앱 설정 ---
st.set_page_config(
    page_title="Cantata Tour 2025 스케줄 관리 (시뮬레이션)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 10번 시뮬레이션용 데이터 생성 (확장된 투어 일정) ---
def generate_tour_data(count=10):
    """10개의 가상 도시 투어 데이터를 생성합니다."""
    
    # 10개의 고유한 도시와 시작 날짜를 정의합니다.
    cities = [
        "New York", "London", "Berlin", "Dubai", "Sydney", 
        "Rio de Janeiro", "Cairo", "Moscow", "Shanghai", "Mexico City"
    ]
    
    start_date = datetime(2025, 3, 1).date()
    extended_data = OrderedDict()
    
    for i in range(count):
        city_name = cities[i % len(cities)] # 도시 이름을 순환 사용
        
        # 고유 키: 도시 이름과 인덱스를 결합하여 키 중복 방지
        unique_key = f"{city_name} (S{i+1})" 
        tour_date = start_date + timedelta(days=i * 7) # 일주일 간격으로 날짜 설정
        
        extended_data[unique_key] = {
            "date": tour_date.strftime("%Y-%m-%d"), 
            "notes": f"Cantata Tour 2025 - {city_name} 시뮬레이션 일정 {i+1}번", 
            "city": city_name
        }
    return extended_data

# --- 세션 상태 초기화 및 데이터 로드/저장 로직 ---

def initialize_session_state():
    """앱 시작 시 세션 상태를 초기화합니다."""
    # tour_data가 없으면 10개의 시뮬레이션 데이터를 생성합니다.
    if 'tour_data' not in st.session_state:
        st.session_state.tour_data = generate_tour_data(10)
    
    # 'temp_tour_data'는 사용자가 입력하는 임시 데이터 공간입니다. (저장 전까지)
    if 'temp_tour_data' not in st.session_state:
        # 딥 카피를 사용하여 원본 데이터와 분리합니다.
        st.session_state.temp_tour_data = dict(st.session_state.tour_data)

    if 'last_saved_time' not in st.session_state:
        st.session_state.last_saved_time = "아직 저장되지 않았습니다."
    
    if 'simulation_count' not in st.session_state:
        st.session_state.simulation_count = 0

def save_data():
    """임시 데이터를 영구 데이터로 저장하고 저장 시간과 시뮬레이션 횟수를 업데이트합니다."""
    # temp_tour_data를 tour_data에 반영
    st.session_state.tour_data = dict(st.session_state.temp_tour_data)
    
    # 저장 시간 및 시뮬레이션 횟수 업데이트
    st.session_state.last_saved_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.simulation_count += 1
    
    st.success(f"데이터가 성공적으로 저장되었습니다. (저장 시간: {st.session_state.last_saved_time})")
    st.info(f"현재 시뮬레이션 횟수: **{st.session_state.simulation_count}**")

# --- UI 레이아웃 ---
initialize_session_state()

st.title("🎼 Cantata Tour 2025 스케줄 관리 시스템 (10회 시뮬레이션 모드)")
st.markdown("---")

col_info, col_save = st.columns([3, 1])

with col_info:
    st.subheader("현재 투어 스케줄")
    st.info(f"마지막 저장 시간: **{st.session_state.last_saved_time}** (저장 횟수: {st.session_state.simulation_count}회)")

with col_save:
    # 저장 버튼. 클릭 시 save_data 함수 실행
    if st.button("💾 스케줄 저장 (Save Changes)", use_container_width=True, type="primary"):
        save_data()
        st.experimental_rerun() # 저장 후 상태 갱신을 위해 리런

st.markdown("---")

# --- 투어 데이터 입력 및 표시 ---
st.subheader("10개 도시별 날짜 및 메모 수정 (저장 버튼 클릭 시 반영)")

# 데이터 표시를 위한 컬럼 설정
cols = st.columns(4)
cols[0].markdown("**투어 고유 키**")
cols[1].markdown("**영구 저장된 날짜**")
cols[2].markdown("**새로운 날짜 선택 (임시)**")
cols[3].markdown("**메모 (임시)**")
st.markdown("---")


# 임시 데이터(temp_tour_data)를 기반으로 UI를 생성하고 사용자 입력을 받습니다.
for i, (city_key, details) in enumerate(st.session_state.temp_tour_data.items()):
    
    # city_key는 'New York (S1)'과 같이 고유합니다.
    unique_widget_key = f"date_input_{city_key}"
    notes_widget_key = f"notes_input_{city_key}"
    
    # 현재 임시 데이터의 날짜를 datetime 객체로 변환
    try:
        temp_date = datetime.strptime(details['date'], "%Y-%m-%d").date()
    except ValueError:
        temp_date = datetime.now().date()
    
    # 영구 저장된 날짜를 가져와서 비교 표시
    permanently_saved_date = st.session_state.tour_data.get(city_key, {}).get("date", "N/A")

    # 새로운 행에 데이터를 표시
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"**{city_key}**") # 예: New York (S1)

    with col2:
        # 영구 저장된 날짜 표시
        st.markdown(f"*{permanently_saved_date}*")

    with col3:
        # st.date_input 위젯을 사용하여 날짜 선택
        # key 매개변수에 고유 키를 사용합니다.
        selected_date = st.date_input(
            "날짜 선택",
            value=temp_date,
            key=unique_widget_key, # ⭐ 고유 키 사용 ⭐
            label_visibility="collapsed"
        )
        
        # 선택된 날짜를 임시 데이터에 저장합니다. (experimental_rerun() 제거하여 부드러운 입력 가능)
        st.session_state.temp_tour_data[city_key]['date'] = selected_date.strftime("%Y-%m-%d")


    with col4:
        # st.text_area 위젯을 사용하여 메모 입력
        st.text_area(
            "메모", 
            value=details['notes'], 
            key=notes_widget_key, # ⭐ 고유 키 사용 ⭐
            label_visibility="collapsed",
            height=50
        )
        # 텍스트 영역의 내용이 변경되었을 때 임시 데이터에 저장합니다.
        st.session_state.temp_tour_data[city_key]['notes'] = st.session_state[notes_widget_key]

# --- 최종 데이터 확인 ---
st.markdown("---")
st.subheader("영구 저장된 전체 투어 데이터 (저장 버튼 클릭 후 갱신)")
st.json(st.session_state.tour_data)

st.sidebar.markdown("# Cantata Tour 정보")
st.sidebar.metric("총 투어 도시", len(st.session_state.tour_data))
st.sidebar.metric("저장된 시뮬레이션 횟수", st.session_state.simulation_count)
st.sidebar.markdown("사용자가 변경한 날짜와 메모는 **'스케줄 저장' 버튼을 누를 때** 영구 데이터에 반영됩니다. 이는 10번의 시뮬레이션 반복에 대한 단일 저장 행위로 간주됩니다.")
