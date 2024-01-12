#import pip_system_certs.wrapt_requests
#import requests
import json
from owslib.wfs import WebFeatureService
from pprint import pprint
from pathlib import Path
from util import compress_and_push_to_gcs

data_dir = Path('data/')
prefix = 'WBAMRUT:'
batch_size = 100

layers_to_scrape = [
    "Bus_Stop_Pnt",
    "wb_building_footprint",
    "Cadastre_Poly",
    "Slum_Boundary",
    "Revenue_Ward_Boundary",
    "Zone_Boundary",
    "wb_borough_boundary",
    "wb_municipal_boundary",
    "wb_ward_boundary",
    "wb_tree",
    "ULU_Poly",
    "Lighthouse",
    "Community_toilet",
    "DairyBooth",
    "Fire_Station",
    "GCP_Pnt",
    "Garb_Coll_Pnt",
    "Natural_Gas_NW_Line",
    "Locality_Boundary",
    "Sew_NW_Line",
    "Sew_NW_Pnt",
    "Str_Drain_NW_Line",
    "Str_Drain_NW_Pnt",
]

layer_batch_size_map = {
    "wb_building_footprint": 1000,
    "Cadastre_Poly": 1000,
    "wb_tree": 1000,
}

wfs_url = "https://nagargispariseva.wb.gov.in/geoserver/WBAMRUT/wfs"

bucket_name = 'wb_amrut_data'

if __name__ == '__main__':
    data_dir.mkdir(exist_ok=True, parents=True)
    wfs = WebFeatureService(wfs_url, version='1.0.0')
    for layername_full in wfs.contents.keys():
        layername = layername_full[len(prefix):]
        if layername not in layers_to_scrape:
            continue
        print(layername)
        layer_file = data_dir / f'{layername}.geojsonl'
        layer_file_status = data_dir / f'{layername}.status'

        count = 0
        if layer_file.exists():
            with open(layer_file, 'r') as f:
                for line in f:
                    if line.strip() == '':
                        continue
                    count += 1

        if not layer_file_status.exists():
            layer_file_status.write_text('wip')
        else:
            completed = compress_and_push_to_gcs(data_dir, layer_file, layer_file_status, bucket_name=bucket_name)
            if completed:
                continue

        layer_batch_size = layer_batch_size_map.get(layername, batch_size)
        with open(layer_file, 'a') as outf:
            while True:
                resp = wfs.getfeature(srsname='EPSG:4326',
                                      typename=[layername],
                                      outputFormat='JSON',
                                      maxfeatures=layer_batch_size, 
                                      startindex=count)
                value = resp.getvalue()
                data = json.loads(value)
                feats = data['features']
                for feat in feats:
                    outf.write(json.dumps(feat))
                    outf.write('\n')
                ret_count = len(feats)
                count += ret_count
                print(f'done with {count} entries')
                if ret_count < batch_size:
                    break

        layer_file_status.write_text('downloaded')
        compress_and_push_to_gcs(data_dir, layer_file, layer_file_status, bucket_name=bucket_name)
