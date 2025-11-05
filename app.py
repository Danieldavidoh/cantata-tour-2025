# =============================================
# 5. Google Maps HTML (SyntaxError 완전 해결)
# =============================================
def render_google_map(data, api_key):
    if not data or not api_key:
        return "<p style='color:red;'>지도 로드 실패: API 키 또는 데이터 없음</p>"

    # 마커 생성
    markers = ""
    for c in data:
        lat, lon = c["lat"], c["lon"]
        title = f"{c['city']} | {c.get('venue','')} | {c['seats']}석 | {c['type']}"
        markers += (
            f"new google.maps.Marker({{"
            f"position:{{lat:{lat},lng:{lon}}},"
            f"map:map,"
            f"title:\"{title}\","
            f"icon:'http://maps.google.com/mapfiles/ms/icons/red-dot.png'"
            f"}});"
        )

    # 경로 설정 (2개 이상일 때만)
    origin = f"{data[0]['lat']},{data[0]['lon']}"
    destination = f"{data[-1]['lat']},{data[-1]['lon']}"
    waypoints = ""
    if len(data) > 2:
        for c in data[1:-1]:
            lat, lon = c["lat"], c["lon"]
            waypoints += f"{{location:new google.maps.LatLng({lat},{lon}),stopover:true}},"

    # .format() 사용 → f-string 충돌 완전 회피
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" async defer></script>
        <style>#map{{height:100%;width:100%}}html,body{{height:100%;margin:0;padding:0}}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            let map;
            function initMap() {{
                map = new google.maps.Map(document.getElementById("map"), {{
                    zoom: 6,
                    center: {{lat: 19.0, lng: 73.0}},
                    mapTypeId: 'roadmap'
                }});
                {markers}
                {directions}
            }}
        </script>
    </body>
    </html>
    """

    # 경로가 있을 때만 DirectionsService 추가
    if len(data) > 1:
        directions_js = f"""
                const directionsService = new google.maps.DirectionsService();
                const directionsRenderer = new google.maps.DirectionsRenderer({{
                    polylineOptions: {{ strokeColor: '#ff1744', strokeWeight: 5 }},
                    suppressMarkers: true
                }});
                directionsRenderer.setMap(map);
                directionsService.route({{
                    origin: "{origin}",
                    destination: "{destination}",
                    waypoints: [ {waypoints.rstrip(',')} ],
                    travelMode: 'DRIVING'
                }}, function(result, status) {{
                    if (status === 'OK') {{
                        directionsRenderer.setDirections(result);
                    }}
                }});
        """
    else:
        directions_js = ""

    return html_template.format(
        api_key=api_key,
        markers=markers,
        directions=directions_js
    )
