import streamlit as st
import json, os, uuid, math
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from folium.features import DivIcon
from folium.plugins import AntPath
from pytz import timezone
from streamlit_autorefresh import st_autorefresh

# ========== 기본 설정 ==========
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

CITY_FILE = "cities.json"
NOTICE_FILE = "notice.json"

# ========== 다국어 지원 ==========
LANG = {
    "ko": {
        "title": "칸타타 투어",
        "subtitle": "마하라스트라",
        "select_city": "도시 선택",
        "add_city": "도시 추가",
        "tour_path": "🗺️ 투어 경로",
        "notice": "📢 공지",
        "type": "유형",
        "date": "공연 날짜",
        "today": "오늘",
        "nav": "길찾기",
    },
    "en": {
        "title": "Cantata Tour",
        "subtitle": "Maharashtra",
        "select_city": "Select City",
        "add_city": "Add City",
        "tour_path": "🗺️ Tour Path",
        "notice": "📢 Notice",
        "type": "Type",
        "date": "Performance Date",
        "today": "Today",
        "nav": "Navigate",
    },
    "hi": {
        "title": "कैंटाटा टूर",
        "subtitle": "महाराष्ट्र",
        "select_city": "शहर चुनें",
        "add_city"
