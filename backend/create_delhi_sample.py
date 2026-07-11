import osmium
import os

class AreaExtractor(osmium.SimpleHandler):
    def __init__(self, writer, min_lat, max_lat, min_lon, max_lon):
        super().__init__()
        self.writer = writer
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lon = min_lon
        self.max_lon = max_lon
        self.nodes_written = set()

    def node(self, n):
        if n.location.valid():
            lat, lon = n.location.lat, n.location.lon
            if self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon:
                self.writer.add_node(n)
                self.nodes_written.add(n.id)

    def way(self, w):
        nodes_in_area = []
        for node_ref in w.nodes:
            if node_ref.ref in self.nodes_written:
                nodes_in_area.append(node_ref.ref)
        if len(nodes_in_area) >= 2:
            self.writer.add_way(w)

    def relation(self, r):
        pass

def main():
    min_lat = 28.5
    max_lat = 28.7
    min_lon = 77.1
    max_lon = 77.3

    input_file = 'D:/saferoute-ai/data/raw/osm/northern-zone-260626.osm.pbf'
    output_file = 'D:/saferoute-ai/backend/delhi_sample.osm.pbf'

    print(f'Extracting area: lat[{min_lat}, {max_lat}], lon[{min_lon}, {max_lon}]')
    print(f'Input: {input_file}')
    print(f'Output: {output_file}')

    if os.path.exists(output_file):
        os.remove(output_file)

    with osmium.SimpleWriter(output_file) as writer:
        extractor = AreaExtractor(writer, min_lat, max_lat, min_lon, max_lon)
        extractor.apply_file(input_file, locations=True)

    print('Extraction complete!')
    print(f'File size: {os.path.getsize(output_file)} bytes')

if __name__ == '__main__':
    main()