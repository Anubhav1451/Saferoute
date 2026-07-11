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

    # The method lines to insert
    method_lines = [
        "    def _get_directions_route(self, start: Coordinate, end: Coordinate) -> Optional[List[Dict]]:\\n",
        "        \\\"\\\"\\\"\\n",
        "        Call Mapbox Directions API to get a route between two points.\\n",
        "        Returns list of {'latitude': float, 'longitude': float} or None on failure.\\n",
        "        \\\"\\\"\\\"\\n",
        "        if not self.mapbox_token:\\n",
        "            logger.warning(\\\"MAPBOX_TOKEN not set; skipping directions.\\\")\\n",
        "            return None\\n",
        "\\n",
        "        # Format: lon,lat;lon,lat\\n",
        "        coordinates = f\\\"{start.longitude},{start.latitude};{end.longitude},{end.latitude}\\\"\\n",
        "        url = f\\\"https://api.mapbox.com/directions/v5/mapbox/driving/{coordinates}.json\\\"\\n",
        "        params = {\\n",
        "            \\\"access_token\\\": self.mapbox_token,\\n",
        "            \\\"geometries\\\": \\\"geojson\\\",\\n",
        "            \\\"overview\\\": \\\"full\\\",\\n",
        "            \\\"steps\\\": \\\"true\\\"\\n",
        "        }\\n",
        "        try:\\n",
        "            resp = requests.get(url, params=params, timeout=10)\\n",
        "            if resp.status_code != 200:\\n",
        "                logger.error(f\\\"Mapbox directions failed: {resp.status_code} {resp.text}\\\")\\n",
        "                return None\\n",
        "            data = resp.json()\\n",
        "            if data.get(\\\"code\\\") != \\\"Ok\\\" or not data.get(\\\"routes\\\"):\\n",
        "                logger.error(f\\\"Mapbox directions returned no routes: {data}\\\")\\n",
        "                return None\\n",
        "            # Extract the route geometry from the first route\\n",
        "            route = data[\\\"routes\\\"][0]\\n",
        "            geometry = route.get(\\\"geometry\\\")\\n",
        "            if not geometry or geometry.get(\\\"type\\\") != \\\"LineString\\\":\\n",
        "                return None\\n",
        "            coords_list = geometry.get(\\\"coordinates\\\")\\n",
        "            # Convert to list of dicts\\n",
        "            return [{\\\"latitude\\\": lat, \\\"longitude\\\": lon} for lon, lat in coords_list]\\n",
        "        except Exception as e:\\n",
        "            logger.error(f\\\"Error calling Mapbox directions: {e}\\\")\\n",
        "            return None\\n",
    ]

    # Insert the method lines at the insert_idx position
    lines[insert_idx:insert_idx] = method_lines

    with open(filename, 'w') as f:
        f.writelines(lines)

if __name__ == '__main__':
    main()