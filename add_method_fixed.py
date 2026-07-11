import sys

def main():
    filename = r"D:\\saferoute-ai\\backend\\app\\services\\routing.py"
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Find the index of the line that contains "# --------------------- ROUTE COST ---------------------"
    target = "# --------------------- ROUTE COST ---------------------"
    insert_idx = None
    for i, line in enumerate(lines):
        if target in line:
            # We want to insert before this line
            insert_idx = i
            break

    if insert_idx is None:
        print("Target line not found")
        sys.exit(1)

    # The method text with proper newlines
    method_text = """    def _get_directions_route(self, start: Coordinate, end: Coordinate) -> Optional[List[Dict]]:
        \"\"\"
        Call Mapbox Directions API to get a route between two points.
        Returns list of {'latitude': float, 'longitude': float} or None on failure.
        \"\"\"
        if not self.mapbox_token:
            logger.warning("MAPBOX_TOKEN not set; skipping directions.")
            return None

        # Format: lon,lat;lon,lat
        coordinates = f"{start.longitude},{start.latitude};{end.longitude},{end.latitude}"
        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coordinates}.json"
        params = {
            "access_token": self.mapbox_token,
            "geometries": "geojson",
            "overview": "full",
            "steps": "true"
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Mapbox directions failed: {resp.status_code} {resp.text}")
                return None
            data = resp.json()
            if data.get("code") != "Ok" or not data.get("routes"):
                logger.error(f"Mapbox directions returned no routes: {data}")
                return None
            # Extract the route geometry from the first route
            route = data["routes"][0]
            geometry = route.get("geometry")
            if not geometry or geometry.get("type") != "LineString":
                return None
            coords_list = geometry.get("coordinates")
            # Convert to list of dicts
            return [{"latitude": lat, "longitude": lon} for lon, lat in coords_list]
        except Exception as e:
            logger.error(f"Error calling Mapbox directions: {e}")
            return None
"""
    # Split the method text into lines
    method_lines = method_text.splitlines(keepends=True)  # This keeps the newline at the end of each line

    # Insert the method lines at the insert_idx position
    lines[insert_idx:insert_idx] = method_lines

    with open(filename, 'w') as f:
        f.writelines(lines)

if __name__ == '__main__':
    main()