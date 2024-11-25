import requests
import time
import re
import json
import xmltodict
from bs4 import BeautifulSoup
from pathlib import Path
from pprint import pprint

data_dir = Path('data/')
data_dir.mkdir(exist_ok=True, parents=True)
base_url = "https://tngis.tn.gov.in/geoserver"
WMS_VERSION = "1.1.1"
ID_PROP = 'fid'
SORT_KEY = 'id'
#SORT_KEY = None
#SORT_KEY = 'object_id'
#MAX_RECORDS = 1000
MAX_RECORDS = 1000

OWS_url = f"{base_url}/ows"
capabilities_query_params = {
    "service": "wms",
    "version": WMS_VERSION,
    "request": "GetCapabilities"
}

map_query_params = {
    "service": "wms",
    "version": WMS_VERSION,
    "request": "GetMap"
}


def get_layer_list():
    cap_file = data_dir / 'capabilities.xml'
    if not cap_file.exists():
        resp = requests.get(OWS_url, params=capabilities_query_params)
        if not resp.ok:
            raise Exception(f'Unable to get capabilities from {OWS_url}')

        with open(data_dir / 'capabilities.xml', 'w') as f:
            f.write(resp.text)
    parsed = xmltodict.parse(cap_file.read_text())
    layers = parsed['WMS_Capabilities']['Capability']['Layer']['Layer']
    #for l in layers:
    #    pprint(l.get('Name', None))
    return layers

def make_request(url, params):
    delay = 10
    num_retries = 0
    while True:
        if num_retries > 3:
            raise Exception('Unable to get records')
        if num_retries > 0:
            print(f'retrying in {num_retries*delay}')
            time.sleep(num_retries*delay)
        try:
            resp = requests.get(url, params=params)
            if not resp.ok:
                print('bad response')
                num_retries += 1
                continue
            return resp
        except requests.exceptions.ConnectionError:
            print('connection failed')
            num_retries += 1
            continue


def get_layer(l_name, l_bbox_str):
    layer_file = data_dir / f'{l_name.replace(":","__")}.geojsonl'
    state_file = Path(str(layer_file.resolve()) + '.state')
    downloaded_count = 0
    start_index = 0
    if state_file.exists():
        state = json.loads(state_file.read_text())
        downloaded_count = state['downloaded_count']
        start_index      = state['start_index']

    seen_count = 0
    seen_ids = set()
    seen_geoms = set()
    if layer_file.exists():
        with open(layer_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line == '':
                    continue
                #feat = json.loads(line)
                #seen_id = feat['properties'].get('id', None)
                #if seen_id is not None:
                #    seen_ids.add(seen_id)
                #seen_geoms.add(hash(json.dumps(feat['geometry'])))
                seen_count += 1
                if seen_count % 100000 == 0:
                    print(f'done reading {seen_count} old entries')

    if seen_count != downloaded_count:
         raise Exception(f'{seen_count=} != {downloaded_count=}')

    group = l_name.split(':')[0]
    url = f'{base_url}/{group}/wms'
    while True:
       print(f'making call with {start_index=} {downloaded_count=}')
       params = {}
       params.update(map_query_params)
       params['startIndex'] = start_index
       params['maxFeatures'] = MAX_RECORDS
       params['layers']  = l_name
       params['srs']     = 'EPSG:4326'
       params['width']   = 575
       params['height']  = 768
       params['styles']  = ''
       params['bbox']    = l_bbox_str
       params['format']  = 'application/atom xml'
       if SORT_KEY is not None:
           params['sortBy']  = SORT_KEY
       resp = make_request(url, params)
       #Path('temp.xml').write_text(resp.text)
       feats = get_features(resp.text)
       num_feats = len(feats)
       with open(layer_file, 'a') as f:
           for feat in feats:
               f.write(json.dumps(feat))
               f.write('\n')
           f.flush()
       if num_feats < MAX_RECORDS:
           break

       start_index += MAX_RECORDS
       downloaded_count += num_feats
       state_file.write_text(json.dumps({'downloaded_count' : downloaded_count,
                                         'start_index'      : start_index }))

def find_layer(layers, layer_name):
    for l in layers:
        if l.get('Name', None) == layer_name:
            layer_info = l
            return l
    return None

def get_bbox_str(l_info):
    bboxes = l_info.get('BoundingBox', [])
    bbox = None
    for b in bboxes:
        if b['@CRS'] == 'EPSG:4326':
            bbox = b
            break
    if bbox is None:
        return None

    return f'{bbox["@miny"]},{bbox["@minx"]},{bbox["@maxy"]},{bbox["@maxx"]}'


def get_props(content):
    soup = BeautifulSoup(content, 'lxml')
    lis = soup.find_all('li')
    props = {}
    for li in lis:
        txt = li.text.strip()
        parts = txt.split(':', 1)
        if len(parts) != 2:
            return { 'unparsed': content }
        props[parts[0]] = parts[1].strip()
    return props

def get_geom(georss_polygon):
    points = []
    curr_p = []
    for c in georss_polygon.split(' '):
        if len(curr_p) == 2:
            curr_p.reverse()
            points.append(curr_p)
            curr_p = []
        curr_p.append(round(float(c), 7))
    if len(curr_p) == 2:
        curr_p.reverse()
        points.append(curr_p)
        curr_p = []

    return { 'type': 'Polygon', 'coordinates': [points] }


def get_feature(entry):
    content = entry.get('content', {}).get('#text', '')
    props = get_props(content)

    geom = get_geom(entry['georss:where']['georss:polygon'])

    return { 'type': 'Feature', 'geometry': geom, 'properties': props }

def get_features(xml):
    xml = re.sub(r'&#([a-zA-Z0-9]+);?', r'[#\1;]', xml)
    try:
        parsed = xmltodict.parse(xml)
        entries = parsed['feed']['entry']
    except:
        Path('temp.xml').write_text(xml)
        raise
    feats = []
    for entry in entries:
        feat = get_feature(entry)
        feats.append(feat)
    return feats



if __name__ == '__main__':
    layers = get_layer_list()
    #pprint([l.get('Name', None) for l in layers])
    #exit(0)
    layer_name = 'cadastral_data_wms:view_fmb'
    #layer_name = 'cadastral_data_wms:view_cadastral'
    #layer_name = 'Police_Jurisdiction:Data_Sharing_Police_Jurisdiction'
    #layer_name = 'generic_viewer:traffic police jurisdiction'
    #layer_name = 'generic_viewer:gcc_buildings'
    #layer_name = 'generic_viewer:slum_boundary'
    layer_info = find_layer(layers, layer_name)
    if layer_info is None:
        raise Exception(f'{layer_name} not found')

    layer_bbox_str = get_bbox_str(layer_info)

    #pprint(layer_bbox_str)
    get_layer(layer_name, layer_bbox_str)



