import os
import json
import time
import subprocess
import shutil
from pathlib import Path
from pprint import pprint

import requests
from bs4 import BeautifulSoup

DEBUG = (os.environ.get('DEBUG', '0') == "1")

base_url = "https://odisha4kgeo.in/index.php/mapview/"
            
bucket_name = 'odisha4kgeo_data'

p_url = base_url + 'getGPExtent'
v_url = base_url + 'getVillageExtent'
lulc_url = base_url + 'viewLulcResult'
c_result_url  = base_url + 'viewCadistrialResult'
c_road_url    = base_url + 'viewCadistrialRoad'
c_river_url   = base_url + 'viewCadistrialRiver'
c_buildup_url = base_url + 'viewCadistrialBuildUP'


data_folder = Path('data/raw')
lulc_folder = Path('data/raw/lulc')
hierarchy_old = json.loads((data_folder / 'hierarchy.json').read_text())
hierarchy = json.loads((data_folder / 'hierarchy_new.json').read_text())

new_data_folder = Path('data/raw_new/')
new_data_folder.mkdir(exist_ok=True, parents=True)

class GatewayTimeoutException(Exception):
    pass


with open('data/raw/vill_dup_names.json', 'r') as f:
    vill_dup_names = json.load(f)

def run_external(cmd):
    print(f'running cmd - {cmd}')
    start = time.time()
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end = time.time()
    print(f'STDOUT: {res.stdout}')
    print(f'STDERR: {res.stderr}')
    print(f'command took {end - start} secs to run')
    if res.returncode != 0:
        raise Exception(f'command {cmd} failed')

def convert_file(shape_file):
    if not shape_file.exists():
        return
    print(f'converting {shape_file}')
    with open(shape_file, 'r') as f:
        data = json.load(f)

    for feat in data['features']:
        geom = feat['geometry']
        if geom is None:
            continue
        if 'crs' in geom:
            del geom['crs']
        geom_type = geom['type']
        if geom_type == 'GeometryCollection':
            geoms = geom['geometries']
        else:
            geoms = [geom]

        for geom in geoms:
            if 'crs' in geom:
                del geom['crs']

            geom_type = geom['type']
            if geom_type not in ['Polygon', 'MultiPolygon']:
                raise Exception(f'Unexpected {geom_type=}')
            coords = geom['coordinates']
            if geom_type == 'Polygon':
                for piece in coords:
                    for p in piece:
                        if len(p) == 2:
                            continue
                        if len(p) != 3:
                            raise Exception(f'Unexpected length of point {p}')
                        z = p.pop()
                        if z != 0.0:
                            raise Exception(f'Unexpected z value {z}')
            if geom_type == 'MultiPolygon':
                for poly in coords:
                    for piece in poly:
                        for p in piece:
                            if len(p) == 2:
                                continue
                            if len(p) != 3:
                                raise Exception(f'Unexpected length of point {p}')
                            z = p.pop()
                            if z != 0.0:
                                raise Exception(f'Unexpected z value {z}')

    with open(shape_file, 'w') as f:
        json.dump(data, f)


def get_shape_file(session, url, form_data, shape_file, strip_gj=False, referer='BoundaryView'):

    errors_file = data_folder / 'errors.txt'
        
    if shape_file.exists():
        return

    ref_url = base_url + referer
    headers = {
        'referer': ref_url,
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest'
    }
    if DEBUG:
        print(form_data)
    resp = session.post(url, data=form_data, headers=headers)
    if not resp.ok:
        if resp.status_code != 500:
            print(resp.status_code)
            print(resp.text)
            if resp.status_code == 504:
                raise GatewayTimeoutException()
            raise Exception(f'Unable to get data from {url=}, {form_data=}')

    if DEBUG:
        print(resp.text)

    resp_text = resp.text
    if resp_text.find('A PHP Error was encountered') != -1:
        form_data['url'] = url
        with open(errors_file, 'a') as f:
            f.write(json.dumps(form_data) + '\n')
        return
        
    if not strip_gj:
        geodata = json.loads(resp_text)['geojson']
        geodata = json.loads(geodata)
    else:
        geodata = json.loads(resp_text)
        for f in geodata['features']:
            props = f['properties']
            if 'geojson' in props:
                del props['geojson']

    tmp_file = str(shape_file).replace('.geojson', '.3857.geojson')
    with open(tmp_file, 'w') as f:
        json.dump(geodata, f)
    run_external(f'ogr2ogr -f GeoJSON -t_srs EPSG:4326 -s_srs EPSG:3857 "{shape_file}" "{tmp_file}"')
    Path(tmp_file).unlink()
 

session = requests.session()
bound_url = base_url + 'BoundaryView'
resp = session.get(bound_url)
if not resp.ok:
    raise Exception('Unable to get base page')

session_lulc = requests.session()
lulc_view_url = base_url + 'LulcView'
resp = session.get(lulc_view_url)
if not resp.ok:
    raise Exception('Unable to get lulc page')



d_map = {}
for d_info in hierarchy:
    d_id = d_info['id']
    d_map[d_id] = d_info

for d_name, d_info in hierarchy_old.items():
    print(f'handling {d_name}')
    d_id = d_info['id']
    new_d_done_file = new_data_folder / f'{d_id}.done'
    if new_d_done_file.exists():
        continue

    comp_file = data_folder / f'{d_name}.7z'
    to_send = comp_file.name
    if not comp_file.exists():
        run_external(f'gsutil -m cp gs://{bucket_name}/{to_send} {comp_file}')
    if not data_folder.joinpath(d_name).exists():
        run_external(f'7z x {comp_file}')

    comp_lulc_file = data_folder / 'lulc' / f'{d_name}.7z'
    to_send_lulc = comp_lulc_file.name
    if not comp_lulc_file.exists():
        run_external(f'gsutil -m cp gs://{bucket_name}/lulc/{to_send_lulc} {comp_lulc_file}')
    if not data_folder.joinpath('lulc', d_name).exists():
        run_external(f'7z x {comp_lulc_file}')

    d_folder = data_folder / d_name
    new_d_folder = new_data_folder / f'{d_id}'
    new_d_folder.mkdir(exist_ok=True, parents=True)
    d_shape_file = d_folder / 'shape.geojson'
    new_d_shape_file = new_d_folder / 'shape.geojson'
    shutil.copy(str(d_shape_file), str(new_d_shape_file))
    convert_file(new_d_shape_file)

    for b_name, b_info in d_info['blocks'].items():
        b_id = b_info['id']
        b_folder = d_folder / b_name
        b_shape_file = b_folder / 'shaoe.geojson'
        new_b_folder = new_d_folder / f'{b_id}'
        new_b_folder.mkdir(exist_ok=True, parents=True)
        new_b_shape_file = new_b_folder / 'shape.geojson'
        shutil.copy(str(b_shape_file), str(new_b_shape_file))
        convert_file(new_b_shape_file)
        for p_name, p_info in b_info['panchayats'].items():
            p_id = p_info['id']
            p_folder = b_folder / p_name
            p_shape_file = p_folder / 'shape.geojson'
            new_p_folder = new_b_folder / f'{p_id}'
            new_p_folder.mkdir(exist_ok=True, parents=True)
            new_p_shape_file = new_p_folder / 'shape.geojson'
            shutil.copy(str(p_shape_file), str(new_p_shape_file))
            convert_file(new_p_shape_file)
            p_lulc_file = Path(str(p_folder).replace('data/raw', 'data/raw/lulc')) / 'lulc.geojson' 
            new_p_lulc_file = new_p_folder / 'lulc.geojson'
            shutil.copy(str(p_lulc_file), str(new_p_lulc_file))
            convert_file(new_p_lulc_file)
            for v_name, v_info in p_info['villages'].items():
                v_id = v_info['id']
                v_folder = p_folder / v_name
                new_v_folder = new_p_folder / f'{v_id}'
                new_v_folder.mkdir(exist_ok=True, parents=True)
                for typ in [ 'shape', 'cadastral_result', 'cadastral_buildup', 'cadastral_river', 'cadastral_road' ]:
                    v_type_file = v_folder / f'{typ}.geojson'
                    new_v_type_file = new_v_folder / f'{typ}.geojson'
                    if v_type_file.exists():
                        shutil.copy(str(v_type_file), str(new_v_type_file))
                        convert_file(new_v_type_file)
 
    d_info_new = d_map[d_id]
    for b_info in d_info_new['blocks']:
        b_id = b_info['id']
        b_name = b_info['name']
        new_b_folder = new_d_folder / f'{b_id}'
        for p_info in b_info['panchayats']:
            p_id = p_info['id']
            p_name = p_info['name']
            new_p_folder = new_b_folder / f'{p_id}'
            new_p_folder.mkdir(exist_ok=True, parents=True)
            new_p_shape_file = new_p_folder / 'shape.geojson'
            if not new_p_shape_file.exists():
                p_form_data = { 'lulcgp': p_info['id'] }
                get_shape_file(session, p_url, p_form_data, new_p_shape_file)
                convert_file(new_p_shape_file)
            new_p_lulc_file = new_p_folder / 'lulc.geojson'
            has_dup_names = False
            if d_id in vill_dup_names:
                if b_id in vill_dup_names[d_id]:
                    if p_id in vill_dup_names[d_id][b_id]:
                        has_dup_names = True
            if has_dup_names and new_p_lulc_file.exists():
                new_p_lulc_file.unlink()

            get_vill_lulc_files = False
            if not new_p_lulc_file.exists():
                p_lulc_form_data = {
                    'block': b_name,
                    'field': 'classification_3',
                    'value': 'All',
                    'grampanchyat': p_info['id'],
                    'field1': 'classification_4',
                    'fieldValue': 'All'
                }
                try:
                    get_shape_file(session_lulc, lulc_url, p_lulc_form_data, new_p_lulc_file, strip_gj=True, referer='LulcView')
                    convert_file(new_p_lulc_file)
                except GatewayTimeoutException:
                    print(f'got gateway timeout getting lulc data for {d_name=} {b_name=} {p_name=}')
                    get_vill_lulc_files = True

                    session_lulc = requests.session()
                    lulc_view_url = base_url + 'LulcView'
                    resp = session.get(lulc_view_url)
                    if not resp.ok:
                        raise Exception('Unable to get lulc page')

            vill_lulc_files = []
            for v_info in p_info['villages']:
                v_id = v_info['id']
                v_name = v_info['name']
                try:
                    int(v_id)
                except ValueError:
                    print(f'found non int {v_id} for {v_name}, {v_info}')
                    continue
                v_name = v_info['name']
                new_v_folder = new_p_folder / f'{v_id}'
                new_v_folder.mkdir(exist_ok=True, parents=True)
                new_v_shape_file = new_v_folder / 'shape.geojson'
                if not new_v_shape_file.exists():
                    v_form_data = { 'lulcvillage': v_id, 'lulcgp': p_id }
                    get_shape_file(session, v_url, v_form_data, new_v_shape_file)
                    convert_file(new_v_shape_file)

                c_form_data = {
                    'district': d_name,
                    'block': b_name,
                    'value': v_id,
                    'field': 'revenue_village_code'
                }
                new_c_result_shape_file  = new_v_folder / 'cadastral_result.geojson'
                new_c_road_shape_file    = new_v_folder / 'cadastral_road.geojson'
                new_c_river_shape_file   = new_v_folder / 'cadastral_river.geojson'
                new_c_buildup_shape_file = new_v_folder / 'cadastral_buildup.geojson'

                if not new_c_result_shape_file.exists():
                    get_shape_file(session, c_result_url, c_form_data, new_c_result_shape_file, strip_gj=True)
                    convert_file(new_c_result_shape_file)
                if not new_c_road_shape_file.exists():
                    get_shape_file(session, c_road_url, c_form_data, new_c_road_shape_file, strip_gj=True)
                    convert_file(new_c_road_shape_file)
                if not new_c_river_shape_file.exists():
                    get_shape_file(session, c_river_url, c_form_data, new_c_river_shape_file, strip_gj=True)
                    convert_file(new_c_river_shape_file)
                if not new_c_buildup_shape_file.exists():
                    get_shape_file(session, c_buildup_url, c_form_data, new_c_buildup_shape_file, strip_gj=True)
                    convert_file(new_c_buildup_shape_file)

                if get_vill_lulc_files:
                    v_lulc_form_data = {
                        'block': b_name,
                        'field': 'classification_4',
                        'value': 'All',
                        'village': v_id
                    }
                    new_v_lulc_file = new_v_folder / 'lulc.geojson'
                    get_shape_file(session_lulc, lulc_url, v_lulc_form_data, new_v_lulc_file, strip_gj=True, referer='LulcView')
                    convert_file(new_v_lulc_file)
                    vill_lulc_files.append(new_v_lulc_file)
            if get_vill_lulc_files:
                print(f'combining {vill_lulc_files} to {new_p_lulc_file}')
                data = {
                    "type": "FeatureCollection", "name": "classification_4",
                    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
                    "features": []
                }
                for v_file in vill_lulc_files:
                    with open(v_file, 'r') as f:
                        v_data = json.load(f)
                        data['features'].extend(v_data['features'])
                with open(new_p_lulc_file, 'w') as f:
                    json.dump(data, f, indent=2)
                for v_file in vill_lulc_files:
                    v_file.unlink()

    new_comp_file = new_data_folder / f'{d_name}.7z'
    run_external(f'7z a {new_comp_file} {new_d_folder}')
    to_send = new_comp_file.name
    run_external(f'gsutil -m cp {new_comp_file} gs://{bucket_name}/new/{to_send}')
    new_d_done_file.write_text('done')

    shutil.rmtree(str(new_d_folder))
    new_comp_file.unlink()
    shutil.rmtree(str(d_folder))
    comp_file.unlink()
    shutil.rmtree(str(d_folder).replace('data/raw', 'data/raw/lulc'))
    comp_lulc_file.unlink()


