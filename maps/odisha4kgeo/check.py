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

vill_dup_names = {}

def get_hierarchy_new(session, soup):
    hierarchy_file = data_folder / 'hierarchy_new.json'
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
    hierarchy = []
    nav = soup.find('nav', {'id': 'subnav1'})
    sel = nav.find('select', {'id': 'lulcdistrict'})
    options = sel.find_all('option')
    for option in options:
        val = option.attrs['value']
        if val == "-1":
            continue
        dist_name = option.text.strip()
        hierarchy.append({ 'name': dist_name, 'id': val , 'blocks': [] })
  
    for d_info in hierarchy:
        block_url = base_url + 'getBlocks'
        d_name = d_info['name']
        form_data = { 'district': d_info['id'] }
        print(f'get block info for district: {d_name}')
        resp = session.post(block_url, data=form_data, headers=headers)
        if not resp.ok:
            raise Exception(f'Unable to get block list for {d_name}, {d_info}')

        block_data = json.loads(resp.text)
        for be in block_data:
            b_name = be['block_name']
            b_id = be['block_code']
            b_info = { 'name': b_name, 'id': b_id, 'panchayats': [] }
            d_info['blocks'].append(b_info)
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
                p_info = { 'id': p_id, 'name': p_name, 'villages': [] }
                b_info['panchayats'].append(p_info)
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
                    v_info =  {'name': v_name, 'id': v_id }
                    p_info['villages'].append(v_info)
 
    with open(hierarchy_file, 'w') as f:
        json.dump(hierarchy, f)
    return hierarchy



if __name__ == '__main__':
    hierarchy = get_hierarchy_new(None, None)
    for d_info in hierarchy:
        d_name = d_info['name']
        d_id = d_info['id']
        for b_info in d_info['blocks']:
            b_name = b_info['name']
            b_id = b_info['id']
            p_name_map = dict()
            p_id_map = dict()
            for p_info in b_info['panchayats']:
                p_name = p_info['name']
                p_id = p_info['id']
                p_id_int = int(p_id)
                if p_id in p_id_map:
                    prev = p_id_map[p_id]
                    if prev != p_name:
                        print(f'ERROR: {p_id=} repeated for {d_name=}, {b_name=}, curr={p_name}, prev={prev}')
                p_id_map[p_id] = p_name
                if p_name in p_name_map:
                    prev = p_name_map[p_name]
                    if prev != p_id:
                        print(f'ERROR: {p_name=} repeated for {d_name=}, {b_name=}, curr={p_id}, prev={prev}')
                p_name_map[p_name] = p_id
                v_name_map = dict()
                v_id_map = dict()
                for v_info in p_info['villages']:
                    v_name = v_info['name']
                    v_id = v_info['id']
                    try:
                        int(v_id)
                    except ValueError:
                        continue
                    if v_id in v_id_map:
                        prev = v_id_map[v_id]
                        if prev != v_name:
                            print(f'ERROR: {v_id=} repeated for {d_name=}, {b_name=}, {p_name=}, curr={v_name}, prev={prev}')
                    v_id_map[v_id] = v_name
                    if v_name in v_name_map:
                        prev = v_name_map[v_name]
                        if prev != v_id:
                            if d_id not in vill_dup_names:
                                vill_dup_names[d_id] = {}
                            if b_id not in vill_dup_names[d_id]:
                                vill_dup_names[d_id][b_id] = {}
                            if p_id not in vill_dup_names[d_id][b_id]:
                                vill_dup_names[d_id][b_id][p_id] = {}
                            print(f'ERROR: {v_name=} repeated for {d_name=}, {b_name=}, {p_name=}, curr={v_id}, prev={prev}')
                    v_name_map[v_name] = v_id

    with open('data/raw/vill_dup_names.json', 'w') as f:
        json.dump(vill_dup_names, f)
