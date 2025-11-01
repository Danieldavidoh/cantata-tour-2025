import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
import math

# =============================================
# 1. 다국어 사전 (영어 / 한국어 / 힌디어)
# =============================================
LANG = {
    "en": {
        "title": "🎼 Cantata Tour <span style='font-size:1.1rem; color:#888; font-weight:normal;'>(Maharashtra)</span>",
        "start_city": "Starting City",
        "start_btn": "🚀 Start",
        "reset_btn": "🔄 Reset All",
        "next_city": "Next City",
        "add_btn": "➕ Add",
        "current_route": "### Current Route",
        "total_distance": "Total Distance",
        "total_time": "Total Time",
        "venues_dates": "Venues & Dates",
        "performance_date": "Performance Date",
        "venue_name": "Venue Name",
        "seats": "Seats",
        "indoor_outdoor": "Indoor/Outdoor",
        "indoor": "Indoor",
        "outdoor": "Outdoor",
        "google_link": "Google Maps Link",
        "register": "Register",
        "add_venue": "Add Venue",
        "edit": "Edit",
        "open_maps": "Open in Google Maps",
        "save": "Save",
        "delete": "Delete",
        "tour_map": "Tour Map",
        "caption": "Mobile: ⋮ → 'Add to Home Screen' → Use like an app!",
        "date_format": "%b %d, %Y",  # Jan 01, 2025
        "admin_mode": "Admin Mode",
        "password": "Password",
        "enter_password": "Enter password to access Admin Mode",
        "submit": "Submit",
    },
    "ko": {
        "title": "🎼 칸타타 투어 <span style='font-size:1.1rem; color:#888; font-weight:normal;'>(마하라슈트라)</span>",
        "start_city": "출발 도시",
        "start_btn": "🚀 시작",
        "reset_btn": "🔄 전체 초기화",
        "next_city": "다음 도시",
        "add_btn": "➕ 추가",
        "current_route": "### 현재 경로",
        "total_distance": "총 거리",
        "total_time": "총 소요시간",
        "venues_dates": "공연장 & 날짜",
        "performance_date": "공연 날짜",
        "venue_name": "공연장 이름",
        "seats": "좌석 수",
        "indoor_outdoor": "실내/실외",
        "indoor": "실내",
        "outdoor": "실외",
        "google_link": "구글 지도 링크",
        "register": "등록",
        "add_venue": "공연장 추가",
        "edit": "편집",
        "open_maps": "구글 지도 열기",
        "save": "저장",
        "delete": "삭제",
        "tour_map": "투어 지도",
        "caption": "모바일: ⋮ → '홈 화면에 추가' → 앱처럼 사용!",
        "date_format": "%Y년 %m월 %d일",  # 2025년 01월 01일
        "admin_mode": "관리자 모드",
        "password": "비밀번호",
        "enter_password": "관리자 모드 접근을 위한 비밀번호 입력",
        "submit": "제출",
    },
    "hi": {
        "title": "🎼 कांताता टूर <span style='font-size:1.1rem; color:#888; font-weight:normal;'>(महाराष्ट्र)</span>",
        "start_city": "प्रारंभिक शहर",
        "start_btn
