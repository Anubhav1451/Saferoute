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
        self.ways_in_box = 0

    def node(self, n):
        self.node_count += 1
        if n.location.valid():
            lat, lon = n.location.lat, n.location.lon
            if self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon:
                self.nodes_in_box += 1

    def way(self, w):
        self.way_count += 1
        # check if any node in way is within box (we don't have node coords here without loading locations)
        # For simplicity, we'll just count ways
        pass

def main():
    min_lat = 17.3
    max_lat = 17.5
    min_lon = 78.4
    max_lon = 78.6

    input_file = 'D:/saferoute-ai/data/raw/osm/northern-zone-260626.osm.pbf'
    handler = DebugHandler(min_lat, max_lat, min_lon, max_lon)
    print(f'Scanning file: {input_file}')
    handler.apply_file(input_file, locations=True)  # load locations for nodes
    print(f'Total nodes: {handler.node_count}')
    print(f'Nodes in box: {handler.nodes_in_box}')
    print(f'Total ways: {handler.way_count}')

if __name__ == '__main__':
    main()