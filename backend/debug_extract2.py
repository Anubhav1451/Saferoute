import osmium
import os

class DebugHandler(osmium.SimpleHandler):
    def __init__(self, min_lat, max_lat, min_lon, max_lon):
        super().__init__()
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lon = min_lon
        self.max_lon = max_lon
        self.node_count = 0
        self.way_count = 0
        self.nodes_in_box = 0

    def node(self, n):
        self.node_count += 1
        if n.location.valid():
            lat, lon = n.location.lat, n.location.lon
            if self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon:
                self.nodes_in_box += 1

    def way(self, w):
        self.way_count += 1

def main():
    min_lat = 28.5
    max_lat = 28.7
    min_lon = 77.1
    max_lon = 77.3

    input_file = 'D:/saferoute-ai/data/raw/osm/northern-zone-260626.osm.pbf'
    handler = DebugHandler(min_lat, max_lat, min_lon, max_lon)
    print(f'Scanning file: {input_file}')
    print(f'Box: lat[{min_lat}, {max_lat}], lon[{min_lon}, {max_lon}]')
    handler.apply_file(input_file, locations=True)
    print(f'Total nodes: {handler.node_count}')
    print(f'Nodes in box: {handler.nodes_in_box}')
    print(f'Total ways: {handler.way_count}')

if __name__ == '__main__':
    main()