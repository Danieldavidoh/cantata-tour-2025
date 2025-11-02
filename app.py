import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import math
import random # Top으로 이동
# =============================================
# 1. 다국어 사전 (추가 키들: 하드코딩 메시지 다국어화)
# =============================================
LANG = {
    "en": {
        "title": "Cantata Tour 2025",
        "add_city": "Add City",
        "select_city": "Select City",
        "add_city_btn": "Add City",
        "tour_route": "Tour Route",
        "remove": "Remove",
        "reset_btn": "Reset All",
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
        "caption": "Mobile: Add to Home Screen -> Use like an app!",
        "date_format": "%b %d, %Y",
        "admin_mode": "Admin Mode",
        "guest_mode": "Guest Mode",
        "enter_password": "Enter password to access Admin Mode",
        "submit": "Submit",
        "drive_to": "Drive Here",
        "edit_venue": "Edit",
        "delete_venue": "Delete",
        "confirm_delete": "Are you sure you want to delete?",
        # 추가 키들
        "date_changed": "Date changed",
        "venue_registered": "Venue registered successfully",
        "venue_deleted": "Venue deleted successfully",
        "venue_updated": "Venue updated successfully",
        "enter_venue_name": "Please enter a venue name",
        "edit_venue_label": "Venue Name",
        "edit_seats_label": "Seats",
        "edit_type_label": "Type",
        "edit_google_label": "Google Maps Link",
    },
    "ko": {
        "title": "칸타타 투어 2025",
        "add_city": "도시 추가",
        "select_city": "도시 선택",
        "add_city_btn": "도시 추가",
        "tour_route": "투어 경로",
        "remove": "삭제",
        "reset_btn": "전체 초기화",
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
        "caption": "모바일: 홈 화면에 추가 -> 앱처럼 사용!",
        "date_format": "%Y년 %m월 %d일",
        "admin_mode": "관리자 모드",
        "guest_mode": "손님 모드",
        "enter_password": "관리자 모드 접근을 위한 비밀번호 입력",
        "submit": "제출",
        "drive_to": "길찾기",
        "edit_venue": "편집",
        "delete_venue": "삭제",
        "confirm_delete": "정말 삭제하시겠습니까?",
        # 추가 키들
        "date_changed": "날짜 변경됨",
        "venue_registered": "등록 완료",
        "venue_deleted": "삭제 완료",
        "venue_updated": "수정 완료",
        "enter_venue_name": "공연장 이름을 입력하세요.",
        "edit_venue_label": "공연장 이름",
        "edit_seats_label": "좌석 수",
        "edit_type_label": "유형",
        "edit_google_label": "구글 지도 링크",
    },
    "hi": {
        "title": "कांताता टूर 2025",
        "add_city": "शहर जोड़ें",
        "select_city": "शहर चुनें",
        "add_city_btn": "शहर जोड़ें",
        "tour_route": "टूर मार्ग",
        "remove": "हटाएं",
        "reset_btn": "सब रीसेट करें",
        "venues_dates": "स्थल और तिथियाँ",
        "performance_date": "प्रदर्शन तिथि",
        "venue_name": "स्थल का नाम",
        "seats": "सीटें",
        "indoor_outdoor": "इंडोर/आउटडोर",
        "indoor": "इंडोर",
        "outdoor": "आउटडोर",
        "google_link": "गूगल मैप्स लिंक",
        "register": "रजिस्टर",
        "add_venue": "स्थल जोड़ें",
        "edit": "संपादित करें",
        "open_maps": "गूगल मैप्स में खोलें",
        "save": "सहेजें",
        "delete": "हटाएँ",
        "tour_map": "टूर मैप",
        "caption": "मोबाइल: होम स्क्रीन पर जोड़ें -> ऐप की तरह उपयोग करें!",
        "date_format": "%d %b %Y",
        "admin_mode": "एडमिन मोड",
        "guest_mode": "गेस्ट मोड",
        "enter_password": "एडमिन मोड एक्सेस करने के लिए पासवर्ड दर्ज करें",
        "submit": "जमा करें",
        "drive_to": "यहाँ ड्राइव करें",
        "edit_venue": "संपादित करें",
        "delete_venue": "हटाएँ",
        "confirm_delete": "क्या आप वाकई हटाना चाहते हैं?",
        # 추가 키들
        "date_changed": "तिथि बदली गई",
        "venue_registered": "पंजीकरण सफल",
        "venue_deleted": "स्थल हटा दिया गया",
        "venue_updated": "स्थल अपडेट किया गया",
        "enter_venue_name": "कृपया स्थल का नाम दर्ज करें",
        "edit_venue_label": "स्थल का नाम",
        "edit_seats_label": "सीटें",
        "edit_type_label": "प्रकार",
        "edit_google_label": "गूगल मैप्स लिंक",
    },
}
# =============================================
# 2. 페이지 설정 (맨 위로 이동!)
# =============================================
st.set_page_config(page_title="Cantata Tour 2025", layout="wide", initial_sidebar_state="collapsed")
# =============================================
# 3. 크리스마스 테마 CSS + 장식 (전체 UI에 고르게 배치)
# =============================================
st.markdown("""
<style>
    .reportview-container {
        background: linear-gradient(to bottom, #0f0c29, #302b63, #24243e);
        overflow: hidden;
        position: relative;
    }
    .sidebar .sidebar-content { background: #228B22; color: white; }
    .Widget>label { color: #90EE90; font-weight: bold; }
    .christmas-title {
        font-size: 3.5em !important;
        font-weight: bold;
        text-align: center;
        text-shadow
