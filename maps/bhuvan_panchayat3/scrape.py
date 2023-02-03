import json
import os
import os.path
import sys
import random

import requests

random.seed()

in_s_codes = []
if len(sys.argv) > 1:
    in_s_codes = sys.argv[1:]

graphql_url = 'https://bhuvan-panchayat3.nrsc.gov.in/graphql'

session = requests.Session()
def make_graphql_req(q_str, variables):
    req_dict = {
        'query': q_str,
        'variables': variables
    }
    headers = { 'Content-Type': 'application/json' }
    data = None
    retriable = True
    try:
        web_data = session.post(graphql_url, data=json.dumps(req_dict), headers=headers, timeout=30)
        if web_data.ok:
            resp = json.loads(web_data.text)
            data = resp['data']
        else:
            #if web_data.status_code == 400:
            #    retriable = False
            raise ValueError('bad web request.. {}: {}'.format(web_data.status_code, web_data.text))
    except Exception as ex:
        print('got exception while requesting: {}, exception: {}'.format(req_dict, ex))

    return data, retriable

def get_from_file(fname):
    if not os.path.exists(fname):
        return None
    if os.stat(fname).st_size == 0:
        return {}
    with open(fname) as f:
        return json.load(f)


def dump_mapping(fname, mapping):
    dirname = os.path.dirname(fname)
    if dirname != '':
        os.makedirs(dirname, exist_ok=True)
    try:
        print('writing file: {}'.format(fname))
        with open(fname, 'w') as f:
            if mapping is not None:
                json.dump(mapping, f, indent=4)
    except KeyboardInterrupt:
        os.remove(fname)


def get_all_states():
    fname = 'mapping.json'
    query = """
        query StateQuery {
          data: allStates(orderBy: STNAME_ASC) {
            nodes {
              code: stcode
              name: stname
            }
          }
        }
    """
    variables = {}
    return query, variables, fname



def get_all_dists(s_code):
    fname = '{}/mapping.json'.format(s_code)
    query = """
        query DistrictQuery(
          $condition: DistrictCondition!
        ) {
          data: allDistricts(orderBy: DTNAME_ASC, condition: $condition) {
            nodes {
              code: dtcode
              name: dtname
            }
          }
        }
    """
    variables = {
            "condition": {
                "stcode": str(s_code)
            }
    }
    return query, variables, fname


def get_all_blocks(s_code, d_code):
    fname = '{}/{}/mapping.json'.format(s_code, d_code)
    query = """
        query BlockQuery(
          $condition: BlockCondition!
        ) {
          data: allBlocks(orderBy: BPNAME_ASC, condition: $condition) {
            nodes {
              code: bpcode
              name: bpname
            }
          }
        }
    """
    variables = {
            "condition": {
                "stcode": str(s_code),
                "dtcode": str(d_code)
            }
    }
    return query, variables, fname


def get_all_panchayats(s_code, d_code, b_code):

    fname = '{}/{}/{}/mapping.json'.format(s_code, d_code, b_code)
    query = """
        query PanchayatQuery(
          $condition: PanchayatCondition!
        ) {
          data: allPanchayats(orderBy: GP_NAME_ASC, condition: $condition) {
            nodes {
              code: gpcode
              name: gpName
            }
          }
        }
    """
    variables = {
            "condition": {
                "stcode": str(s_code),
                "dtcode": str(d_code),
                "bpcode": str(b_code)
            }
    }
    return query, variables, fname


def get_all_block_villages(s_code, d_code, b_code):
    fname = '{}/{}/{}/village_mapping.json'.format(s_code, d_code, b_code)
    query = """
        query VillageQuery(
          $condition: VillageCondition!
        ) {
          data: allVillages(orderBy: VNAME_ASC, condition: $condition) {
            nodes {
              code: vcode11
              name: vname
            }
          }
        }
    """
    variables = {
            "condition": {
                "stcode": str(s_code),
                "dtcode": str(d_code),
                "bpcode": str(b_code)
            }
    }
    return query, variables, fname


def get_all_villages(s_code, d_code, b_code, g_code):
    fname = '{}/{}/{}/{}/mapping.json'.format(s_code, d_code, b_code, g_code)
    query = """
        query VillageQuery(
          $condition: VillageCondition!
        ) {
          data: allVillages(orderBy: VNAME_ASC, condition: $condition) {
            nodes {
              code: vcode11
              name: vname
            }
          }
        }
    """
    variables = {
            "condition": {
                "stcode": str(s_code),
                "dtcode": str(d_code),
                "bpcode": str(b_code),
                "gpcode": str(g_code)
            }
    }
    return query, variables, fname


def get_state_map(s_code):
    fname = '{}/boundary.geojson'.format(s_code)
    query = """
        query StateGeomQuery(
          $value: Int
          $value2: Int
        ) {
          geomvaluesbp(tablename: "bp.state", condition: "stcode", conditionvalue: $value, stcode: $value2) {
            geojson
          }
        }
    """
    variables = {
            "value": s_code,
            "value2": s_code,
    }
    return query, variables, fname


def get_dist_map(s_code, d_code):
    fname = '{}/{}/boundary.geojson'.format(s_code, d_code)
    query = """
        query DistrictGeomQuery(
          $value: Int
          $value2: Int
        ) {
          geomvaluesbp(tablename: "bp.district", condition: "dtcode", conditionvalue: $value, stcode: $value2) {
            geojson
          }
        }
    """
    variables = {
            "value": d_code,
            "value2": s_code,
    }
    return query, variables, fname


def get_block_map(s_code, d_code, b_code):
    fname = '{}/{}/{}/boundary.geojson'.format(s_code, d_code, b_code)
    query = """
        query BlockGeomQuery(
          $value: Int
          $value2: Int
        ) {
          geomvaluesbp(tablename: "bp.block", condition: "bpcode", conditionvalue: $value, stcode: $value2) {
            geojson
          }
        }
    """
    variables = {
            "value": b_code,
            "value2": s_code,
    }
    return query, variables, fname


def get_panchayat_map(s_code, d_code, b_code, g_code):
    fname = '{}/{}/{}/{}/boundary.geojson'.format(s_code, d_code, b_code, g_code)
    query = """
        query PanchayatGeomQuery(
          $value: Int
          $value2: Int
          $value3: Int!
          $value4: Int!
        ) {
          geomvaluesbp: geomvaluesbppanchayat(tablename: "bp.panchayat", condition: "gpcode", conditionvalue: $value, stcode: $value2, dtcode: $value3, bpcode: $value4) {
            geojson
          }
        }
    """
    variables = {
        "value": g_code,
        "value2": s_code,
        "value3": d_code,
        "value4": b_code
    }
    return query, variables, fname


def get_village_map(s_code, d_code, b_code, g_code, v_code):
    fname = '{}/{}/{}/{}/{}/boundary.geojson'.format(s_code, d_code, b_code, g_code, v_code)
    query = """
        query VillageGeomQuery(
          $value: Int
          $value2: Int
        ) {
          geomvaluesbp(tablename: "bp.village", condition: "vcode11", conditionvalue: $value, stcode: $value2) {
            geojson
          }
        }
    """
    variables = {
            "value": v_code,
            "value2": s_code
    }
    return query, variables, fname

def get_uncovered_village_map(s_code, d_code, b_code, v_code):
    fname = '{}/{}/{}/uncovered/{}/boundary.geojson'.format(s_code, d_code, b_code, v_code)
    query = """
        query VillageGeomQuery(
          $value: Int
          $value2: Int
        ) {
          geomvaluesbp(tablename: "bp.village", condition: "vcode11", conditionvalue: $value, stcode: $value2) {
            geojson
          }
        }
    """
    variables = {
            "value": v_code,
            "value2": s_code
    }
    return query, variables, fname



def listing_wrap(fn, *args):
    q_str, variables, fname = fn(*args)
    out_map = get_from_file(fname)
    if out_map is not None:
        return out_map

    data, retriable = make_graphql_req(q_str, variables)
    if data is None and retriable:
        return {}

    out_map = None
    if data is not None:
        out_map = {}
        for node in data['data']['nodes']:
            code = str(node['code'])
            name = node['name']
            out_map[code] = { 'name': name }

    dump_mapping(fname, out_map)
    if out_map is None:
        out_map = {}
    return out_map


def mapping_wrap(fn, *args):
    q_str, variables, fname = fn(*args)
    if os.path.exists(fname):
        return
    data, retriable = make_graphql_req(q_str, variables)
    if data is None and retriable:
        return

    if data is None:
        map_data = None
    else:
        map_data = json.loads(data['geomvaluesbp']['geojson'])
    dump_mapping(fname, map_data)


print('getting all states')
state_map = listing_wrap(get_all_states)
all_state_codes = state_map.keys()
if len(in_s_codes) == 0: 
    to_iter = all_state_codes
else:
    to_iter = in_s_codes

for s_code in to_iter:
    print('processing state: {}'.format(state_map[s_code]['name']))
    dist_map = listing_wrap(get_all_dists, s_code)
    state_map[s_code]['districts'] = dist_map
    mapping_wrap(get_state_map, s_code)
    d_code_list = list(dist_map.keys())
    random.shuffle(d_code_list)
    #for d_code in dist_map.keys():
    for d_code in d_code_list:
        print('processing district: {}'.format(dist_map[d_code]['name']))
        block_map = listing_wrap(get_all_blocks, s_code, d_code)
        dist_map[d_code]['blocks'] = block_map
        mapping_wrap(get_dist_map, s_code, d_code)
        b_code_list = list(block_map.keys())
        random.shuffle(b_code_list)
        for b_code in b_code_list:
            print('processing block: {}'.format(block_map[b_code]['name']))
            gp_map = listing_wrap(get_all_panchayats, s_code, d_code, b_code)
            village_block_map = listing_wrap(get_all_block_villages, s_code, d_code, b_code)
            all_villages_in_block = set(village_block_map.keys())
            block_map[b_code]['panchayats'] = gp_map
            mapping_wrap(get_block_map, s_code, d_code, b_code)
            villages_in_panchayats = set()
            g_code_list = list(gp_map.keys())
            random.shuffle(g_code_list)
            for g_code in g_code_list:
                print('processing panchayat: {}'.format(gp_map[g_code]['name']))
                mapping_wrap(get_panchayat_map, s_code, d_code, b_code, g_code)
                village_map = listing_wrap(get_all_villages, s_code, d_code, b_code, g_code)
                gp_map[g_code]['villages'] = village_map
                for v_code in village_map.keys():
                    villages_in_panchayats.add(v_code)
                    print('processing village: {}'.format(village_map[v_code]['name']))
                    mapping_wrap(get_village_map, s_code, d_code, b_code, g_code, v_code)
            #print('known {}\n, all {}'.format(villages_in_panchayats, all_villages_in_block))
            uncovered = all_villages_in_block - villages_in_panchayats
            uncovered_map = {}
            for v_code in uncovered:
                uncovered_map[v_code] = { 'name': village_block_map[v_code]['name'] }
                print('processing uncovered village: {}'.format(village_block_map[v_code]['name']))
                mapping_wrap(get_uncovered_village_map, s_code, d_code, b_code, v_code)
            block_map[b_code]['uncovered'] = uncovered_map
            

if len(in_s_codes) == 0:
    with open('full_mapping.json', 'w') as f:
        json.dump(state_map, f, indent=4)


