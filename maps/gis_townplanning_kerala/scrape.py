import requests
import re
import json
import xmltodict
from bs4 import BeautifulSoup
from pathlib import Path
from pprint import pprint

data_dir = Path('data/')
data_dir.mkdir(exist_ok=True, parents=True)
base_url = "http://gis.townplanning.kerala.gov.in:8080/geoserver"
WMS_VERSION = "1.1.1"
ID_PROP = 'fid'
SORT_KEY = None
MAX_RECORDS = 100

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
    layers = parsed['WMT_MS_Capabilities']['Capability']['Layer']['Layer']
    #for l in layers:
    #    pprint(l.get('Name', None))
    return layers

def get_layer(l_name, l_bbox_str):
    layer_file = data_dir / f'{l_name.replace(":","__")}.geojsonl'
    seen_count = 0
    if layer_file.exists():
        with open(layer_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line == '':
                    continue
                #feat = json.loads(line)
                seen_count += 1

    group = l_name.split(':')[0]
    url = f'{base_url}/{group}/wms'
    start_index = seen_count
    total_count = seen_count
    while True:
        params = {}
        params.update(map_query_params)
        params['startindex'] = start_index
        params['maxfeatures'] = MAX_RECORDS
        params['layers']  = l_name
        params['srs']     = 'EPSG:4326'
        params['width']   = 768
        params['height']  = 625
        #params['styles']  = ''
        params['bbox']    = l_bbox_str
        if SORT_KEY is not None:
            params['sortBy']  = SORT_KEY
        params['format']  = 'application/atom xml'
        resp = requests.get(url, params=params)
        if not resp.ok:
            raise Exception(f'Unable to get records, {l_name=} {start_index=}')
        Path('temp.xml').write_text(resp.text)
        feats = get_features(resp.text)
        with open(layer_file, 'a') as f:
            for feat in feats:
                f.write(json.dumps(feat))
                f.write('\n')
        num_feats = len(feats)
        if num_feats < MAX_RECORDS:
            break
        start_index += MAX_RECORDS
        total_count += num_feats
        print(f'done with {total_count} feats')

def find_layer(layers, layer_name):
    for l in layers:
        if l.get('Name', None) == layer_name:
            layer_info = l
            return l
    return None

def get_bbox_str(l_info):
    bboxes = l_info.get('BoundingBox', [])
    if type(bboxes) != list:
        bboxes = [bboxes]
    bbox = None
    for b in bboxes:
        if b.get('@CRS', '') == 'EPSG:4326' or b.get('@SRS', '') == 'EPSG:4326':
            bbox = b
            break
    if bbox is None:
        return None

    return f'{bbox["@minx"]},{bbox["@miny"]},{bbox["@maxx"]},{bbox["@maxy"]}'


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
    if len(props) == 0:
        return { 'unparsed': content }
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
    except:
        Path('temp.xml').write_text(xml)
        raise
    entries = parsed['feed'].get('entry', [])
    feats = []
    for entry in entries:
        feat = get_feature(entry)
        feats.append(feat)
    return feats


layer_names = [
    'tcp:survey_boundary_chav',
    'tcp:survey_boundary_fer',	
    'tcp:survey_boundary_kad',	
    'tcp:survey_boundary_kar',	
    'tcp:survey_boundary_kas',	
    'tcp:survey_boundary_kot',	
    'tcp:survey_boundary_kov',	
    'tcp:survey_boundary_koy',	
    'tcp:survey_boundary_koz',	
    'tcp:survey_boundary_mal',	
    'tcp:survey_boundary_mat',	
    'tcp:survey_boundary_med',	
    'tcp:survey_boundary_ned',	
    'tcp:survey_boundary_nil',	
    'tcp:survey_boundary_nor',	
    'tcp:survey_boundary_ola',	
    'tcp:survey_boundary_par',	
    'tcp:survey_boundary_per',	
    'tcp:survey_boundary_pon',	
    'tcp:survey_boundary_ram',	
    'tcp:survey_boundary_tha',	
    'tcp:survey_boundary_vat',	
    'tcp:survey_boundary_pal',	
]

layer_names_landuse = [
'tcp:land_use_ala',
#'tcp:land_use_cha',
'tcp:land_use_chav',
'tcp:land_use_fer',
'tcp:land_use_kad',
'tcp:land_use_kar',
'tcp:land_use_kas',
'tcp:land_use_kot',
'tcp:land_use_kov',
'tcp:land_use_koy',
'tcp:land_use_koz',
'tcp:land_use_mal',
'tcp:land_use_mat',
'tcp:land_use_med',
'tcp:land_use_ned',
'tcp:land_use_nil',
'tcp:land_use_nor',
'tcp:land_use_ola',
'tcp:land_use_pal',
'tcp:land_use_pala',
'tcp:land_use_par',
'tcp:land_use_per',
'tcp:land_use_pon',
'tcp:land_use_ram',
'tcp:land_use_tha',
#'tcp:land_use_vat',
]


if __name__ == '__main__':
    #layers = get_layer_list()
    #exit(0)
    layer_name = 'tcp:survey_boundary_chav'
    #layer_info = find_layer(layers, layer_name)
    #if layer_info is None:
    #    raise Exception(f'{layer_name} not found')

    #layer_bbox_str = get_bbox_str(layer_info)
    layer_bbox_str = '-180.0,-90.0,180.0,90.0'

    #pprint(layer_bbox_str)
    for layer_name in layer_names_landuse:
        print(f'getting {layer_name}')
        get_layer(layer_name, layer_bbox_str)



