import streamlit as st
from datetime import datetime, timedelta
from collections import OrderedDict
import random
import pandas as pd # pandas is used for data display and sorting

# --- App Configuration ---
st.set_page_config(
    page_title="Cantata Tour 2025 Schedule Manager (Simulation)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 10x Simulation Data Generation ---
def generate_tour_data(count=10):
    """Generates virtual tour data for 10 unique cities/stages."""
    
    # Define 10 unique cities and a base start date
    cities = [
        "New York", "London", "Berlin", "Dubai", "Sydney", 
        "Rio de Janeiro", "Cairo", "Moscow", "Shanghai", "Mexico City"
    ]
    
    start_date = datetime(2025, 3, 1).date()
    extended_data = OrderedDict()
    
    for i in range(count):
        city_name = cities[i % len(cities)]
        
        # Unique Key: Combine city name and index (e.g., 'New York (S1)') to ensure widget key uniqueness
        unique_key = f"{city_name} (S{i+1})" 
        # Set date spaced one week apart with some random variance
        tour_date = start_date + timedelta(days=i * 7 + random.randint(0, 3)) 
        
        extended_data[unique_key] = {
            "date": tour_date.strftime("%Y-%m-%d"), 
            "notes": f"Cantata Tour 2025 - {city_name} 시뮬레이션 일정 {i+1}번", 
            "city": city_name
        }
    return extended_data

# --- Session State Initialization and Data Handling ---

def initialize_session_state():
    """Initializes session state variables."""
    # tour_data: The permanent, saved schedule data.
    if 'tour_data' not in st.session_state:
        st.session_state.tour_data = generate_tour_data(10)
    
    # temp_tour_data: Temporary storage for user input before saving.
    if 'temp_tour_data' not in st.session_state:
        # Use a dictionary copy to separate temporary changes from permanent data
        st.session_state.temp_tour_data = dict(st.session_state.tour_data)

    if 'last_saved_time' not in st.session_state:
        st.session_state.last_saved_time = "아직 저장되지 않았습니다."
    
    # simulation_count: Tracks how many times the user has saved the schedule.
    if 'simulation_count' not in st.session_state:
        st.session_state.simulation_count = 0

def save_data():
    """Saves temporary data to permanent data, updates save time, and increments simulation count."""
    
    # 1. Update permanent data with temporary inputs
    st.session_state.tour_data = dict(st.session_state.temp_tour_data)
    
    # 2. Update metadata
    st.session_state.last_saved_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.simulation_count += 1
    
    # 3. Provide feedback
    st.success(f"데이터가 성공적으로 저장되었습니다. (저장 시간: {st.session_state.last_saved_time})")
    st.info(f"현재 시뮬레이션 횟수: **{st.session_state.simulation_count}회**")

# --- UI Layout ---
initialize_session_state()

st.title("🎼 Cantata Tour 2025 스케줄 관리 시스템 (10회 시뮬레이션 모드)")
st.markdown("---")

col_info, col_save = st.columns([3, 1])

with col_info:
    st.subheader("현재 투어 스케줄")
    st.info(f"마지막 저장 시간: **{st.session_state.last_saved_time}** (저장 횟수: {st.session_state.simulation_count}회)")

with col_save:
    # Save button. Executes save_data function on click.
    if st.button("💾 스케줄 저장 (Save Changes)", use_container_width=True, type="primary"):
        save_data()
        # Rerun is required to fully refresh the data table and sidebar metrics
        st.experimental_rerun() 

st.markdown("---")

# --- Tour Data Input and Display ---
st.subheader("10개 도시별 날짜 및 메모 수정 (저장 버튼 클릭 시 반영)")

# Define columns for the input table
cols = st.columns(4)
cols[0].markdown("**Tour Unique Key**")
cols[1].markdown("**Permanently Saved Date**")
cols[2].markdown("**Select New Date (Temporary)**")
cols[3].markdown("**Notes (Temporary)**")
st.markdown("---")


# Iterate through the temporary data for input fields
for i, (city_key, details) in enumerate(st.session_state.temp_tour_data.items()):
    
    # --- CRITICAL: Generate unique keys for widgets to prevent StreamlitDuplicateElementKey ---
    unique_date_key = f"date_input_{city_key}_{i}"
    unique_notes_key = f"notes_input_{city_key}_{i}"
    
    # Prepare the date value for the date_input widget
    try:
        temp_date = datetime.strptime(details['date'], "%Y-%m-%d").date()
    except ValueError:
        temp_date = datetime.now().date()
    
    # Retrieve the permanently saved date for comparison display
    permanently_saved_date = st.session_state.tour_data.get(city_key, {}).get("date", "N/A")

    # Display data in new row columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"**{city_key}**") 

    with col2:
        # Display the permanently saved date
        st.markdown(f"*{permanently_saved_date}*")

    with col3:
        # st.date_input widget
        selected_date = st.date_input(
            "날짜 선택",
            value=temp_date,
            key=unique_date_key, # Use the unique key
            label_visibility="collapsed"
        )
        
        # Update the temporary data state immediately on date change
        st.session_state.temp_tour_data[city_key]['date'] = selected_date.strftime("%Y-%m-%d")


    with col4:
        # st.text_area widget
        st.text_area(
            "메모", 
            value=details['notes'], 
            key=unique_notes_key, # Use the unique key
            label_visibility="collapsed",
            height=50
        )
        # Update notes content to the temporary data state using the widget's current value
        st.session_state.temp_tour_data[city_key]['notes'] = st.session_state[unique_notes_key]

# --- Final Data Confirmation (Dataframe Display) ---
st.markdown("---")
st.subheader("영구 저장된 전체 투어 데이터 상세")

# Convert permanent data to DataFrame for sorting and display
data_list = []
for city_key, details in st.session_state.tour_data.items():
    data_list.append({
        "고유 키": city_key,
        "도시": details['city'],
        "날짜": details['date'],
        "메모": details['notes']
    })

df = pd.DataFrame(data_list)
# Sort by date for logical display
df_sorted = df.sort_values(by="날짜", ascending=True)

st.dataframe(df_sorted, use_container_width=True, hide_index=True)

# --- Sidebar Metrics ---
st.sidebar.markdown("# Tour Information")
st.sidebar.metric("Total Tour Cities", len(st.session_state.tour_data))
st.sidebar.metric("Saved Simulation Count", st.session_state.simulation_count)
st.sidebar.markdown("Changes to dates and notes are reflected in the permanent data only when you click the **'Save Schedule'** button.")s
