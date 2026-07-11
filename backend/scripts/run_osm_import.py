"""Driver script to run the OSM importer from the backend context."""
import os
import sys

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.data_ingestion.osm_importer import OSMImporter

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import OSM road data')
    parser.add_argument('--file', required=True, help='Path to .osm.pbf file')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size')
    args = parser.parse_args()

    importer = OSMImporter()
    importer.batch_size = args.batch_size
    result = importer.run(filepath=args.file)
    print(f'Result: {result}')
