import json
import copy
import logging
import operator

from pathlib import Path
from pprint import pformat

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

base_url = 'https://bhunaksha.cg.nic.in/'
host_name = 'bhunaksha.cg.nic.in'
wms_url = base_url + 'WMS'

state_id = 22
state_name = 'Chhattisgarh'


base_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Host': host_name,
    'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
}


def setup_logging(log_level):
    from colorlog import ColoredFormatter
    formatter = ColoredFormatter("%(log_color)s%(asctime)s [%(levelname)-5s][%(process)d][%(threadName)s] %(message)s",
                                 datefmt='%Y-%m-%d %H:%M:%S',
	                             reset=True,
	                             log_colors={
	                             	'DEBUG':    'cyan',
	                             	'INFO':     'green',
	                             	'WARNING':  'yellow',
	                             	'ERROR':    'red',
	                             	'CRITICAL': 'red',
	                             },
	                             secondary_log_colors={},
	                             style='%')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logging.basicConfig(level=log_level, handlers=[handler])



def parse_hierarchy(el):
    drop_downs = el.find_all('select')
    level_infos = []
    for drop_down in drop_downs:
        lid = drop_down.attrs['id'].replace('level_', '')
        lname = drop_down.find_previous('div').next.text.replace(':', '').strip()
        level_info = { 'level_id': lid, 'level_name': lname }
        level_infos.append(level_info)
        options = drop_down.find_all('option')
        op_map = {}
        for o in options:
            value = o.attrs['value']
            name = o.text.strip()
            op_map[value] = name
        level_info['entries'] = op_map
    return level_infos


def get_hierarchy(level_id, selections, session):
    h_url = base_url + 'ScalarDatahandler'
    h_headers = {}
    h_headers.update(base_headers)
    del h_headers['Sec-Fetch-User']
    h_headers['Accept'] = 'text/html, */*; q=0.01'
    h_headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    h_headers['Referer'] = base_url
    h_headers['Origin'] = base_url
    h_headers['Sec-Fetch-Dest'] = 'empty'
    h_headers['Sec-Fetch-Mode'] = 'cors'
    h_headers['Sec-Fetch-Site'] = 'same-origin'
    h_headers['X-Requested-With'] = 'XMLHttpRequest'

    selections_str = ','.join(selections[1:])
    form_data = {
      'OP': '2',
      'level': str(level_id),
      'selections': selections_str,
      'state': str(state_id)
    }
    logger.info(f'get_hierarchy: {form_data}')
    resp = session.post(h_url, data=form_data, headers=h_headers)
    if not resp.ok:
        raise Exception(f'Unable to get hierarchy data for {level_id}, {selections}')
    soup = BeautifulSoup(resp.text, 'html.parser')
    return parse_hierarchy(soup)


def populate_level_map(level_infos, level_map):
    curr_map = level_map
    num_levels = len(level_infos)
    for i, linfo in enumerate(level_infos):
        last_level = ( i == num_levels - 1 )
        lid = linfo['level_id']
        lname = linfo['level_name']
        curr_map['done'] = last_level
        curr_map['level_id'] = lid
        curr_map['level_name'] = lname
        curr_map['entries'] = {}
        first_entry = None
        for k,v in linfo['entries'].items():
            new_entry = { 'name': v, 'done': last_level }
            if first_entry is None:
                first_entry = new_entry
            curr_map['entries'][k] = new_entry
        if last_level:
            break
        if first_entry is None:
            raise Exception(f'no entries for {linfo}')
        curr_map = first_entry


def traverse_and_populate_map(level_map, trail, session):
    logger.info(f'traverse called with trail {trail}')
    if level_map['done']:
        return True
    lid = level_map['level_id']
    entries = level_map['entries']
    for e_id, entry in entries.items():
        if entry['done']:
            continue
        has_entries = 'entries' in entry
        if not has_entries:
            level_infos = get_hierarchy(int(lid) + 1, trail + [str(e_id)], session)
            populate_level_map(level_infos, entry)
        traverse_and_populate_map(entry, trail + [str(e_id)], session)
    level_map['done'] = True
    

def get_level_map(table, session):
    level_map_file = Path('data/raw/level_map.json')
    if level_map_file.exists():
        level_map = json.loads(level_map_file.read_text(encoding='utf8'))
        return level_map

    level_map = {
        'done': False,
        'level_id': '0',
        'level_name': 'State',
        'entries': {
            state_id: {
                'name': state_name
            }
        }
    }
    level_infos = parse_hierarchy(table)
    populate_level_map(level_infos, level_map['entries'][state_id])
    traverse_and_populate_map(level_map, [], session)
    level_map_file.parent.mkdir(parents=True, exist_ok=True)
    level_map_file.write_text(json.dumps(level_map, indent=2, ensure_ascii=False), encoding='utf8')
    return level_map


def get_vill_extent(session, trail):
    extent_url = base_url + 'rest/MapInfo/getVVVVExtentGeoref'
    form_data = {
       'state': str(state_id),
       'gisLevels': ','.join(trail),
       'srs': '0'
    }
    eheaders = {}
    eheaders.update(base_headers)
    del eheaders['Sec-Fetch-User']
    eheaders['Accept'] = '*/*'
    eheaders['Referer'] = base_url
    eheaders['Origin'] = base_url
    eheaders['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    eheaders['Sec-Fetch-Dest'] = 'empty'
    eheaders['Sec-Fetch-Mode'] = 'cors'
    eheaders['Sec-Fetch-Site'] = 'same-origin'
    resp = session.post(extent_url, data=form_data, headers=eheaders)
    if not resp.ok:
        raise Exception(f'Unable to get extent for {trail}')
    extent = json.loads(resp.text)
    return extent


def populate_rev_map(level_map, rev_map, trail):
    level_name = level_map['level_name']
    entries = level_map['entries']
    if level_name == 'Village':
        for e_id, entry in entries.items():
            rev_map[tuple(trail + [str(e_id)])] = entry['name'] 
        return

    for e_id, entry in entries.items():
        populate_rev_map(entry, rev_map, trail + [str(e_id)])


def get_vill_image(extent, folder, session):
    i_headers = {}
    i_headers.update(base_headers)
    del i_headers['Sec-Fetch-User']
    i_headers['Accept'] = 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
    i_headers['Referer'] = base_url
    i_headers['Origin'] = base_url
    i_headers['Sec-Fetch-Dest'] = 'image'
    i_headers['Sec-Fetch-Mode'] = 'no-cors'
    i_headers['Sec-Fetch-Site'] = 'same-origin'

    keys = [ "xmin", "ymin", "xmax", "ymax" ]
    bbox = operator.itemgetter(*keys)(extent)
    bbox = [ str(c) for c in bbox ]
    bbox_str = ','.join(bbox)
    qparams = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "FORMAT": "image/png",
        "TRANSPARENT": "true",
        "LAYERS": "VILLAGE_MAP",
        "transparent": "true",
        "state": str(state_id),
        "gis_code": extent['gisCode'],
        "overlay_codes": "",
        "CRS": "EPSG:3857",
        "STYLES": "VILLAGE_MAP",
        "FORMAT_OPTIONS": "dpi:180",
        "WIDTH": "2592",
        "HEIGHT": "1977",
        "BBOX": bbox_str
    }
    logger.info(f'{qparams=}')
    resp = session.get(wms_url, params=qparams, headers=i_headers)
    if not resp.ok:
        raise Exception(f'unable to retrieve img')
    img_file = folder / 'vill.png'
    bbox_file = folder / 'vill.png.bbox.json'
    logger.info(f'writing to {img_file}')
    with open(img_file, 'wb') as f:
        f.write(resp.content)
    with open(bbox_file, 'w') as f:
        json.dump(bbox, f)



if __name__ == '__main__':
    setup_logging(logging.INFO)
    session = requests.session()
    resp = session.get(base_url, headers=base_headers)
    if not resp.ok:
        raise Exception(f'Unable to get {base_url}')

    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', { 'id': 'state_selector' })
    inps = table.find_all('input', { 'type': 'hidden' })
    inp_map = {}
    for inp in inps:
        inp_map[inp.attrs['id']] = inp.attrs['value']
    logger.debug(f'{inp_map=}')
    level_map = get_level_map(table, session)
    logger.debug(pformat(level_map, sort_dicts=False))

    rev_map = {}
    populate_rev_map(level_map, rev_map, [])
    logger.info(f'num villages to scrape: {len(rev_map)}')
    for trail, name in rev_map.items():
        extent = get_vill_extent(session, trail[1:])
        logger.info(pformat(trail[1:]))
        soup = BeautifulSoup(extent['attribution'], 'html.parser')
        strs = list(soup.find('span').stripped_strings)
        for s in strs:
            if s.startswith('Updated on'):
                updated_on = s.replace('Updated on :', '')
                break

        vill_folder = Path('data/raw/' + '/'.join(trail))
        vill_folder.mkdir(parents=True, exist_ok=True)
        logger.info(pformat(extent))
        get_vill_image(extent, vill_folder, session)
        exit(0)
    

    



