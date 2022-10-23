from pathlib import Path
import json

p_folder = Path('data/raw/lulc/Ganjam/Rangeilunda/Berhampur (M)/')
files = p_folder.glob('*.geojson')
data = {
    "type": "FeatureCollection", "name": "classification_4",
    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
    "features": []
}

for file in files:
    print(file)
    with open(file, 'r') as f:
        v_data = json.load(f)
        data['features'].extend(v_data['features'])

with open(p_folder / 'lulc.geojson', 'w') as f:
    json.dump(data, f, indent=2)

