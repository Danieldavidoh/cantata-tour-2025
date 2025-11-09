import streamlit as st
from datetime import datetime, timedelta
from collections import OrderedDict
import random
import pandas as pd
import numpy as np # For map coordinates

# --- App Configuration ---
st.set_page_config(
    page_title="Cantata Tour 2025 Schedule Manager (Simulation)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 10x Simulation Data Generation ---
def generate_tour_data(count=10):
    """Generates virtual tour data including coordinates."""
    
    # 10 unique cities and their approximate coordinates for map simulation
    city_configs = [
        {"name": "New York", "lat": 40.71, "lon": -74.01}, 
        {"name": "London", "lat": 51.51, "lon": -0.13}, 
        {"name": "Berlin", "lat": 52.52, "lon": 13.40}, 
        {"name": "Dubai", "lat": 25.20, "lon": 55.27}, 
        {"name": "Sydney", "lat": -33.87, "lon": 151.21}, 
        {"name": "Rio de Janeiro", "lat": -22.91, "lon": -43.21}, 
        {"name": "Cairo", "lat": 30.04, "lon": 31.24}, 
        {"name": "Moscow", "lat": 55.75, "lon": 37.62}, 
        {"name": "Shanghai", "lat": 31.23, "lon": 121.47}, 
        {"name": "Mexico City", "lat": 19.43, "lon": -99.13}
    ]
    
    start_date = datetime(2025, 3, 1).date()
    extended_data = OrderedDict()
    
    for i in range(count):
        config = city_configs[i % len(city_configs)]
        
        unique_key = f"{config['name']} (S{i+1})"
        tour_date = start_date + timedelta(days=i * 7 + random.randint(0, 3)) 
        
        extended_data[unique_key] = {
            "date": tour_date.strftime("%Y-%m-%d"), 
            "notes": f"Cantata Tour 2025 - {config['name']} 시뮬레이션 일정 {i+1}번", 
            "city": config['name'],
            "lat": config['lat'] + random.uniform(-0.5, 0.5), # Add small variance
            "lon": config['lon'] + random.uniform(-0.5, 0.5)
        }
    return extended_data

# --- Session State Initialization and Data Handling ---

def initialize_session_state():
    """Initializes session state variables."""
    if 'tour_data' not in st.session_state:
        st.session_state.tour_data = generate_tour_data(10)
    
    if 'temp_tour_data' not in st.session_state:
        st.session_state.temp_tour_data = dict(st.session_state.tour_data)

    if 'last_saved_time' not in st.session_state:
        st.session_state.last_saved_time = "아직 저장되지 않았습니다."
    
    if 'simulation_count' not in st.session_state:
        st.session_state.simulation_count = 0

def save_data(city_key=None, is_popover_save=False):
    """Saves temporary data to permanent data and updates metrics."""
    
    if is_popover_save and city_key:
        # Save only the specific city data from popover to temp_tour_data
        # Note: In this simulation structure, actual saving to permanent data still requires the main button click.
        # This function updates the temp state and provides visual feedback.
        st.session_state.temp_tour_data[city_key]['date'] = st.session_state[f"popover_date_{city_key}"].strftime("%Y-%m-%d")
        st.session_state.temp_tour_data[city_key]['notes'] = st.session_state[f"popover_notes_{city_key}"]
        st.success(f"**{city_key}**의 변경 사항이 임시 저장되었습니다. 메인 **'스케줄 저장'** 버튼을 눌러 영구 저장하세요.")
        return 

    # Main Save Logic
    st.session_state.tour_data = dict(st.session_state.temp_tour_data)
    st.session_state.last_saved_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.simulation_count += 1
    
    st.success(f"데이터가 성공적으로 저장되었습니다. (저장 시간: {st.session_state.last_saved_time})")
    st.info(f"현재 시뮬레이션 횟수: **{st.session_state.simulation_count}회**")
    st.experimental_rerun() 


# --- UI Layout ---
initialize_session_state()

st.title("🎼 Cantata Tour 2025 스케줄 관리 시스템 (지도/수정 기능 포함)")
st.markdown("---")

col_info, col_save = st.columns([3, 1])

with col_info:
    st.subheader("현재 투어 스케줄")
    st.info(f"마지막 저장 시간: **{st.session_state.last_saved_time}** (저장 횟수: {st.session_state.simulation_count}회)")

with col_save:
    if st.button("💾 스케줄 저장 (Save All)", use_container_width=True, type="primary"):
        save_data()


st.markdown("---")

# --- Map Display ---
st.subheader("🌐 투어 도시 위치 및 스케줄 수정 (지도)")

# Create a DataFrame for map plotting
map_data_list = []
for city_key, details in st.session_state.temp_tour_data.items():
    map_data_list.append({
        "city_key": city_key,
        "lat": details['lat'],
        "lon": details['lon'],
        "date": details['date'],
        "notes": details['notes']
    })
df_map = pd.DataFrame(map_data_list)

# Map center calculation
if not df_map.empty:
    mean_lat = df_map['lat'].mean()
    mean_lon = df_map['lon'].mean()
else:
    mean_lat, mean_lon = 0, 0 # Default to (0, 0) if no data

st.map(df_map, latitude='lat', longitude='lon', zoom=2, use_container_width=True)


# --- Popover (Edit Button) Layout ---
st.markdown("### 📌 도시별 스케줄 수정")
st.markdown("---")

# Arrange the popover buttons in rows of 5
keys_list = list(st.session_state.temp_tour_data.keys())
num_cols = 5
cols = st.columns(num_cols)

for i, city_key in enumerate(keys_list):
    details = st.session_state.temp_tour_data[city_key]
    
    with cols[i % num_cols]:
        # Popover initiation button (Modify Button)
        with st.popover(f"수정: {city_key}", use_container_width=True):
            
            st.markdown(f"**도시:** {details['city']}")
            st.markdown(f"**고유 키:** {city_key}")
            st.markdown("---")

            # 1. Date Input (Initial value based on temp data)
            current_date_obj = datetime.strptime(details['date'], "%Y-%m-%d").date()
            selected_date_popover = st.date_input(
                "**날짜:**",
                value=current_date_obj,
                key=f"popover_date_{city_key}", # Unique key for popover date
            )

            # 2. Notes Input (Initial value based on temp data)
            st.text_area(
                "**메모:**", 
                value=details['notes'], 
                key=f"popover_notes_{city_key}", # Unique key for popover notes
                height=100
            )

            # 3. Modify Registration Button
            if st.button("수정 등록", key=f"popover_save_{city_key}", type="primary", use_container_width=True):
                # Save data specific to this city from the popover inputs
                save_data(city_key=city_key, is_popover_save=True)
                # Note: No rerun here to keep the popover open for immediate feedback if desired, 
                # but we rely on the main button for permanent saving.


# --- Final Data Confirmation (Dataframe Display) ---
st.markdown("---")
st.subheader("최종 영구 저장된 전체 투어 데이터 목록")

# Convert permanent data to DataFrame for sorting and display
data_list = []
for city_key, details in st.session_state.tour_data.items():
    data_list.append({
        "* 고유 키": city_key, # Add * to the column name as requested
        "* 도시": details['city'],
        "* 날짜": details['date'],
        "* 메모": details['notes']
    })

df = pd.DataFrame(data_list)
df_sorted = df.sort_values(by="* 날짜", ascending=True)

st.dataframe(df_sorted, use_container_width=True, hide_index=True)

# --- Sidebar Metrics ---
st.sidebar.markdown("# Tour Information")
st.sidebar.metric("Total Tour Cities", len(st.session_state.tour_data))
st.sidebar.metric("Saved Simulation Count", st.session_state.simulation_count)
st.sidebar.markdown("Changes made via the **'수정'** popovers are *temporarily* saved. Click the main **'스케줄 저장'** button to make changes *permanent*.")
