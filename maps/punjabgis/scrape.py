import requests
import re
import json
import xmltodict
from bs4 import BeautifulSoup
from pathlib import Path
from pprint import pprint

data_dir = Path('data/')
data_dir.mkdir(exist_ok=True, parents=True)
base_url = "https://punjabgis.punjab.gov.in/geoserver"
WMS_VERSION = "1.1.1"
ID_PROP = 'fid'
SORT_KEY = None
#SORT_KEY = 'object_id'
MAX_RECORDS = 1000
epsg = 'EPSG:4326'
SSL_VERIFY = True
mode = 'WFS'

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
        resp = requests.get(OWS_url, params=capabilities_query_params, verify=SSL_VERIFY)
        if not resp.ok:
            raise Exception(f'Unable to get capabilities from {OWS_url}')

        with open(data_dir / 'capabilities.xml', 'w') as f:
            f.write(resp.text)
    parsed = xmltodict.parse(cap_file.read_text())
    layers = parsed['WMT_MS_Capabilities']['Capability']['Layer']['Layer']
    #for l in layers:
    #    pprint(l.get('Name', None))
    return layers


def get_wfs_features(resp_text):
    data = json.loads(resp_text)
    feats = data['features']
    for feat in feats:
        if 'id' in feat:
            feat['properties']['fid'] = feat['id']
            del feat['id']
        if 'geometry_name' in feat:
            feat['properties']['geometry_name'] = feat['geometry_name']
            del feat['geometry_name']
    return feats


def make_wfs_call(l_name, l_bbox_str, start_index):
    group = l_name.split(':')[0]
    url = f'{base_url}/{group}/ows'
    params = {
        'service': 'WFS',
        'version': '1.0.0',
        'outputFormat': 'application/json',
        'request': 'GetFeature',
        'typeName': l_name,
        'maxFeatures': MAX_RECORDS,
        'startIndex': start_index,
    }
    if group == 'test':
        params['sortBy'] = 'gid'
    #if SORT_KEY is not None:
    #    params['sortBy']  = SORT_KEY
    resp = requests.get(url, params=params, verify=SSL_VERIFY)
    if not resp.ok:
        raise Exception(f'Unable to get records, {l_name=} {start_index=}')

    try:
        feats = get_wfs_features(resp.text)
    except Exception  as ex:
        print(ex)
        print('parsing failed')
        print(resp.text)
        return None
    return feats
   


def make_wms_call(l_name, l_bbox_str, start_index):
    group = l_name.split(':')[0]
    url = f'{base_url}/{group}/wms'

    params = {}
    params.update(map_query_params)
    params['startIndex'] = start_index
    params['maxFeatures'] = MAX_RECORDS
    params['layers']  = l_name
    params['srs']     = epsg
    params['width']   = 575
    params['height']  = 768
    params['styles']  = ''
    params['bbox']    = l_bbox_str
    if SORT_KEY is not None:
        params['sortBy']  = SORT_KEY
    params['format']  = 'application/atom xml'
    #pprint(params)
    resp = requests.get(url, params=params, verify=SSL_VERIFY)
    if not resp.ok:
        raise Exception(f'Unable to get records, {l_name=} {start_index=}')
    #Path('temp.xml').write_text(resp.text)
    try:
        feats = get_features(resp.text)
    except Exception as ex:
        print(ex)
        print('parsing failed')
        print(resp.text)
        return None

    return feats


def get_layer(l_name, l_bbox_str):
    layer_file = data_dir / f'{l_name.replace(":","__")}.geojsonl'
    state_file = Path(str(layer_file.resolve()) + '.state')
    status_file = Path(str(layer_file.resolve()) + '.status')
    if status_file.exists():
        status = status_file.read_text().strip()
    else:
        status = 'starting'
        status_file.write_text(status)

    if status in ['done', 'failed']:
        return
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

    while True:
       print(f'making call with {start_index=} {downloaded_count=}')
       if mode == 'WMS':
           feats = make_wms_call(l_name, l_bbox_str, start_index)
       else:
           feats = make_wfs_call(l_name, l_bbox_str, start_index)
       if feats is None:
           status_file.write_text('failed')
           break
       num_feats = len(feats)
       with open(layer_file, 'a') as f:
           for feat in feats:
               f.write(json.dumps(feat))
               f.write('\n')
           f.flush()
       if num_feats < MAX_RECORDS:
           status_file.write_text('done')
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
    pprint(l_info)
    bboxes = l_info.get('BoundingBox', [])
    if type(bboxes) != list: 
        bboxes = [bboxes]
    bbox = None
    for b in bboxes:
        if b['@SRS'] == epsg:
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
    return props

def get_points(georss_polygon):
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
    return points



def get_feature(entry):
    content = entry.get('content', {}).get('#text', '')
    props = get_props(content)

    where = entry['georss:where']
    if 'georss:polygon' in where:
        points = get_points(where['georss:polygon'])
        geom = { 'type': 'Polygon', 'coordinates': [points] }
    elif 'georss:line' in where:
        points = get_points(where['georss:line'])
        geom = { 'type': 'LineString', 'coordinates': points }
    elif 'georss:point' in where:
        points = get_points(where['georss:point'])
        geom = { 'type': 'Point', 'coordinates': points[0] }
    else:
        raise Exception(f'unexpected content in {where}')

    return { 'type': 'Feature', 'geometry': geom, 'properties': props }

def get_features(xml):
    xml = re.sub(r'&#([a-zA-Z0-9]+);?', r'[#\1;]', xml)
    try:
        parsed = xmltodict.parse(xml)
    except:
        Path('temp.xml').write_text(xml)
        raise
    #pprint(parsed)
    entries = parsed['feed']['entry']
    if type(entries) is not list:
        entries = [entries]
    feats = []
    for entry in entries:
        feat = get_feature(entry)
        feats.append(feat)
    return feats



if __name__ == '__main__':
    #resp_text = Path('temp.json').read_text()
    #feats = get_wfs_features(resp_text)
    #pprint(feats)
    #exit(0)
    lnames = []
    with open('layers.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line != '':
                lnames.append(line)
    #layers = get_layer_list()
    #lnames = [l.get('Name', None) for l in layers]
    #lnames = [ n for n in lnames if n.startswith('geo_rism') and n.endswith('cadastral') ]
    #pprint(lnames)
    #exit(0)
    #layer_name = 'cadastral_data_wms:view_fmb'
    #layer_name = 'cadastral_data_wms:view_cadastral'
    #layer_name = 'Police_Jurisdiction:Data_Sharing_Police_Jurisdiction'
    #layer_name = 'generic_viewer:traffic police jurisdiction'
    #layer_name = 'generic_viewer:gcc_buildings'
    #lnames = [ 'Punjab_Cadstral_Mapping:cm_status' ]
    lnames = [ l for l in lnames if l.endswith('_killa_polygon') ]
    for layer_name in lnames:
        #if layer_name in [ 'GOP:revenue_fazilka_bhangar_khera_97_killa_polygon',
        #                   'GOP:revenue_fazilka_burj_mohar_wala_120_killa_polygon']:
        #    continue
        print(f'getting {layer_name=}')
        #layer_info = find_layer(layers, layer_name)
        #if layer_info is None:
        #    raise Exception(f'{layer_name} not found')

        #layer_bbox_str = get_bbox_str(layer_info)
        layer_bbox_str = '-180,0,180,90'

        get_layer(layer_name, layer_bbox_str)



