import os
import json
import traceback
import time
import subprocess
import shutil
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEBUG = (os.environ.get('DEBUG', '0') == "1")

base_url = "https://odisha4kgeo.in/index.php/mapview/"
bucket_name = 'odisha4kgeo_data'
data_folder = Path('data/raw')
data_folder.mkdir(parents=True, exist_ok=True)

class GatewayTimeoutException(Exception):
    pass

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


def get_hierarchy(session, soup):
    hierarchy_file = data_folder / 'hierarchy.json'
    if hierarchy_file.exists():
        with open(hierarchy_file, 'r') as f:
            h_data = json.load(f)
            return h_data

    ref_url = base_url + 'BoundaryView'
    headers = {
        'referer': ref_url,
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest'
    }
    hierarchy = {}
    nav = soup.find('nav', {'id': 'subnav1'})
    sel = nav.find('select', {'id': 'lulcdistrict'})
    options = sel.find_all('option')
    for option in options:
        val = option.attrs['value']
        if val == "-1":
            continue
        dist_name = option.text.strip()
        hierarchy[dist_name] = { 'id': val , 'blocks': {} }
  
    for d_name, d_info in hierarchy.items():
        block_url = base_url + 'getBlocks'
        form_data = { 'district': d_info['id'] }
        print(f'get block info for district: {d_name}')
        resp = session.post(block_url, data=form_data, headers=headers)
        if not resp.ok:
            raise Exception(f'Unable to get block list for {d_name}, {d_info}')

        block_data = json.loads(resp.text)
        for be in block_data:
            b_name = be['block_name']
            b_id = be['block_code']
            b_info = { 'id': b_id, 'panchayats': {} }
            d_info['blocks'][b_name] = b_info
            panchayat_url = base_url + 'getRevenueGP'
            b_form_data = { 'blocks': b_id, 'district': d_name }
            print(f'getting panchayat list for {d_name}, {b_name}')
            resp = session.post(panchayat_url, data=b_form_data, headers=headers)
            if not resp.ok:
                raise Exception(f'Unable to get panchayat list for {d_name}, {b_name}')
            panchayat_data = json.loads(resp.text)
            for pe in panchayat_data:
                p_name = pe['grampanchayat_name']
                p_id = pe['grampanchayat_code']
                p_info = { 'id': p_id, 'villages': {} }
                b_info['panchayats'][p_name] = p_info
                village_url = base_url + 'getVillage'
                v_form_data = {
                    'lulcgp': p_id,
                    'blocks': b_id
                }
                print(f'getting village list for {d_name}, {b_name}, {p_name}')
                resp = session.post(village_url, data=v_form_data, headers=headers)
                if not resp.ok:
                    raise Exception(f'Unable to get village list for {d_name}, {b_name}, {p_name}')
                village_data = json.loads(resp.text)
                for ve in village_data:
                    v_id = ve['revenue_village_code']
                    v_name = ve['revenue_village_name']
                    p_info['villages'][v_name] = { 'id': v_id }
    
    with open(hierarchy_file, 'w') as f:
        json.dump(hierarchy, f)
    return hierarchy




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
 

def get_geo_data(hierarchy, session):
 
    d_url = base_url + 'getDistrictExtent'
    b_url = base_url + 'getBlockExtent'
    p_url = base_url + 'getGPExtent'
    v_url = base_url + 'getVillageExtent'
    c_result_url  = base_url + 'viewCadistrialResult'
    c_road_url    = base_url + 'viewCadistrialRoad'
    c_river_url   = base_url + 'viewCadistrialRiver'
    c_buildup_url = base_url + 'viewCadistrialBuildUP'
    for d_name, d_info in hierarchy.items():
        d_done_file = data_folder / f'{d_name}.done'
        if d_done_file.exists():
            continue
        d_folder = data_folder / d_name
        d_folder.mkdir(exist_ok=True, parents=True)
        print(f'getting district geo data: {d_name}')

        d_shape_file = d_folder / 'shape.geojson'
        d_form_data = { 'district': d_info['id'] }
        get_shape_file(session, d_url, d_form_data, d_shape_file)
       
        for b_name, b_info in d_info['blocks'].items():
            b_form_data = { 'blocks': b_info['id'] }
            b_folder = d_folder / b_name
            b_folder.mkdir(exist_ok=True, parents=True)
            print(f'getting block geo data: {b_name}')
            b_shape_file = b_folder / 'shaoe.geojson'
            get_shape_file(session, b_url, b_form_data, b_shape_file)
            for p_name, p_info in b_info['panchayats'].items():
                p_form_data = { 'lulcgp': p_info['id'] }
                p_folder = b_folder / p_name
                p_folder.mkdir(exist_ok=True, parents=True)
                p_shape_file = p_folder / 'shape.geojson'
                get_shape_file(session, p_url, p_form_data, p_shape_file)
                for v_name, v_info in p_info['villages'].items():
                    v_id = v_info['id']
                    try:
                        int(v_id)
                    except ValueError:
                        print(f'found non int {v_id} for {v_name}, {v_info}')
                        continue

                    if v_id in [ 'N/A', 'Unsurveyed Village', 'Sea_Gap', 'NO CODE', 'Plot Area' ]:
                        continue
                    v_form_data = { 'lulcvillage': v_id, 'lulcgp': p_info['id'] }
                    v_folder = p_folder / v_name
                    v_folder.mkdir(exist_ok=True, parents=True)
                    v_shape_file = v_folder / 'shape.geojson'
                    get_shape_file(session, v_url, v_form_data, v_shape_file)

                    c_form_data = {
                        'district': d_name,
                        'block': b_name,
                        'value': v_id,
                        'field': 'revenue_village_code'
                    }
                    c_result_shape_file  = v_folder / 'cadastral_result.geojson'
                    c_road_shape_file    = v_folder / 'cadastral_road.geojson'
                    c_river_shape_file   = v_folder / 'cadastral_river.geojson'
                    c_buildup_shape_file = v_folder / 'cadastral_buildup.geojson'

                    get_shape_file(session, c_result_url, c_form_data, c_result_shape_file, strip_gj=True)
                    get_shape_file(session, c_road_url, c_form_data, c_road_shape_file, strip_gj=True)
                    get_shape_file(session, c_river_url, c_form_data, c_river_shape_file, strip_gj=True)
                    get_shape_file(session, c_buildup_url, c_form_data, c_buildup_shape_file, strip_gj=True)
            
        comp_file = data_folder / f'{d_name}.7z'
        run_external(f'7z a {comp_file} {d_folder}')
        to_send = comp_file.name
        run_external(f'gsutil -m cp {comp_file} gs://{bucket_name}/{to_send}')
        d_done_file.write_text('done')
        shutil.rmtree(d_folder)
        comp_file.unlink()


split_further_map = {}

def get_lulc_geo_data(hierarchy, session):

    lulc_url = base_url + 'viewLulcResult'
    for d_name, d_info in hierarchy.items():
        lulc_folder = data_folder / 'lulc'
        d_done_file = lulc_folder / f'{d_name}.done'
        if d_done_file.exists():
            continue
        d_folder = lulc_folder / d_name
        d_folder.mkdir(exist_ok=True, parents=True)
        print(f'getting district geo data: {d_name}')

        for b_name, b_info in d_info['blocks'].items():
            b_folder = d_folder / b_name
            b_folder.mkdir(exist_ok=True, parents=True)
            print(f'getting block geo data: {b_name}')
            for p_name, p_info in b_info['panchayats'].items():
                print(f'getting panchayat geo data: {p_name}')
                p_form_data = {
                    'block': b_name,
                    'field': 'classification_3',
                    'value': 'All',
                    'grampanchyat': p_info['id'],
                    'field1': 'classification_4',
                    'fieldValue': 'All'
                }
                p_folder = b_folder / p_name
                p_folder.mkdir(exist_ok=True, parents=True)
                p_shape_file = p_folder / 'lulc.geojson'
                if str(p_shape_file) not in split_further_map:
                    split_further = False
                    try:
                        get_shape_file(session, lulc_url, p_form_data, p_shape_file, strip_gj=True, referer='LulcView')
                    except GatewayTimeoutException:
                        split_further = True
                        split_further_map[str(p_shape_file)] = True
                        
                        with open('data/raw/lulc/split_further.txt', 'a') as f:
                            f.write(str(p_shape_file) + '\n')

                    if not split_further:
                        continue

                v_files = []
                for v_name, v_info in p_info['villages'].items():
                    print(f'getting village geo data: {v_name}')
                    v_form_data = {
                        'block': b_name,
                        'field': 'classification_4',
                        'value': 'All',
                        'village': v_info['id']
                    }
                    v_id = v_info['id']
                    try:
                        int(v_id)
                    except ValueError:
                        print(f'found non int {v_id} for {v_name}, {v_info}')
                        continue
                    v_shape_file = p_folder / f'{v_name}.lulc.geojson'
                    get_shape_file(session, lulc_url, v_form_data, v_shape_file, strip_gj=True, referer='LulcView')
                    v_files.append(v_shape_file)
                print(f'combining {v_files} to {p_shape_file}')
                data = {
                    "type": "FeatureCollection", "name": "classification_4",
                    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
                    "features": []
                }
                for v_file in v_files:
                    with open(v_file, 'r') as f:
                        v_data = json.load(f)
                        data['features'].extend(v_data['features'])
                with open(p_shape_file, 'w') as f:
                    json.dump(data, f, indent=2)
                for v_file in v_files:
                    v_file.unlink()


        comp_file = lulc_folder / f'{d_name}.7z'
        run_external(f'7z a {comp_file} {d_folder}')
        to_send = f'lulc/{comp_file.name}'
        run_external(f'gsutil -m cp {comp_file} gs://{bucket_name}/{to_send}')
        d_done_file.write_text('done')
        shutil.rmtree(d_folder)
        comp_file.unlink()



def scrape():
    session = requests.session()

    #bound_url = base_url + 'BoundaryView'
    #resp = session.get(bound_url)
    #if not resp.ok:
    #    raise Exception('Unable to get base page')

    #soup = BeautifulSoup(resp.text, 'html.parser')
    #hierarchy = get_hierarchy(session, soup)
    #hierarchy = get_hierarchy_new(session, soup)

    #get_geo_data(hierarchy, session)

    lulc_url = base_url + 'LulcView'
    resp = session.get(lulc_url)
    if not resp.ok:
        raise Exception('Unable to get lulc page')

    soup = BeautifulSoup(resp.text, 'html.parser')
    hierarchy = get_hierarchy(session, soup)
    get_lulc_geo_data(hierarchy, session)


if __name__ == '__main__':
    count = 0
    while True:
        to_sleep = min(900, count*5)
        print(f'sleeping {to_sleep} secs')
        time.sleep(to_sleep)
        try:
            scrape()
            print('All Done!')
            exit(0)
        except Exception:
            print('Got Exception:')
            traceback.print_exc()
            count += 1


