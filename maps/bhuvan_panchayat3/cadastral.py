import os
#os.environ['SPATIALINDEX_C_LIBRARY'] = '/opt/homebrew/lib/'

import json
import os.path
import copy
import sys

import requests
from rtree import index
from shapely import wkb
from shapely.geometry import shape, mapping
from shapely.prepared import prep
import glob
import csv


import argparse
parser = argparse.ArgumentParser(description='cadastral processing')
parser.add_argument('--download', '-d', action='store_true')
parser.add_argument('--chunk', '-n', type=int)
parser.add_argument('--cursor', '-c', default='')
parser.add_argument('--collect-cadastrals', '-g', action='store_true')
parser.add_argument('--starting-gid', '-s', type=int, default=-1)
args = parser.parse_args()



graphql_url = 'https://bhuvan-panchayat3.nrsc.gov.in/graphql'


def make_graphql_req(q_str, variables):
    req_dict = {
        'query': q_str,
        'variables': variables
    }
    headers = { 'Content-Type': 'application/json' }
    data = None
    retriable = True
    try:
        web_data = session.post(graphql_url, data=json.dumps(req_dict), headers=headers, timeout=120)
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


def get_n_paged(n, cursor):
    print('getting {} after cursor : {}'.format(n, cursor))
    chunk_file = 'cadastrals/{}.json'.format('start' if cursor == '' else cursor)
    if os.path.exists(chunk_file):
        with open(chunk_file) as f:
            data = json.load(f)
    else:
        query = """
        query MyQuery {
        """ + (\
        """
            allCadastrals(orderBy: PRIMARY_KEY_ASC, first: {}, after: "{}") {{
        """.format(n, cursor) if cursor != '' else """
            allCadastrals(orderBy: PRIMARY_KEY_ASC, first: {}) {{
        """.format(n)) +\
        """
            pageInfo {
              endCursor
              hasNextPage
            }
            edges {
              node {
                gid
                geom
                parNum
                state
              }
              cursor
            }
          }
        }
        """
        print(query)
        full_data, retriable = make_graphql_req(query, {})
        data = full_data['allCadastrals']
        print('writing {}'.format(chunk_file))
        with open(chunk_file, 'w') as f:
            json.dump(data, f, indent=4)

    return data['pageInfo'], len(data['edges'])



if args.download:
    session = requests.Session()
    n = args.chunk
    cursor = args.cursor

    count = 0
    hasnext = True
    while hasnext:
        page_info, num = get_n_paged(n, cursor) 
        cursor = page_info['endCursor']
        hasnext = page_info['hasNextPage']
        count = count + num
        print('Done: {}'.format(count))
    print('All Done: {}'.format(count))
    exit()



def getdictwriter(filename):
    fields = ['gid', 'par_num', 'share', 'ambiguous', 'share', 'geom']

    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    
    file_exists = os.path.exists(filename)
    f = open(filename, 'a')
    writer = csv.DictWriter(f, fields)
    if not file_exists:
        writer.writeheader()
    return writer



prepared_map = {}

def idx_gen():
    i = 0
    geojson_files = ['../osm/composite/subdistricts.geojson']
    #geojson_files = glob.glob('composite/*/districts.geojson')
    for geojson_file in geojson_files:
        print('processing {} for building subdistrict index'.format(geojson_file))
        with open(geojson_file) as f:
            data = json.load(f)

        for feature in data['features']:
            s = shape(feature['geometry'])
            if not s.is_valid:
                print('invalid geometry for {}, fixing with buffer(0)'.format(feature['properties']))
                s = s.buffer(0)
                if not s.is_valid:
                    print('invalid geometry even after buffer for {}'.format(feature['properties']))
            g = prep(s)
            feature['geometry'] = s
            prepared_map[i] = g
            feature['id'] = i
            print('sending {}, {}, {}'.format(i, s.bounds, feature['properties']))
            yield (i, s.bounds, feature)
            i += 1


if args.collect_cadastrals:
    #done_till = 4507423
    done_till = args.starting_gid
    state_name_key = 'state_name'
    dist_name_key = 'dist_name'
    #state_name_key = 's_name'

    uncovered = getdictwriter('cadastrals/composite/uncovered.csv')
    invalid = getdictwriter('cadastrals/composite/invalid.csv')
    print('building subdistrict index')
    idx = index.Index(idx_gen())
    

    filename = 'cadastrals/start.json'
    out = {}
    has_next = True
    count = 0
    while has_next:
        print('processing file: {}'.format(filename))
        with open(filename) as f:
            data = json.load(f)
        edges = data['edges']
        for edge in edges:
            node = edge['node']
            geom = node['geom']
            gid = node['gid']
            par_num = node['parNum']
            count += 1
            if gid <= done_till:
                continue
            feature = {
                'geom': geom,
                'gid': gid,
                'par_num': par_num,
                'ambiguous': True,
                'share': 1.0
            }

            if geom is None:
                print('{}: {} got invalid entry'.format(count, gid))
                invalid.writerow(feature)
                continue

            #print(Geometry(geom, 4326).geojson)
            try:
                cadastral_shape = wkb.loads(geom, hex=True)
            except Exception as e:
                print('{}: {} got exception {} while reading geometry'.format(count, gid, e))
                invalid.writerow(feature)
                continue

            if not cadastral_shape.is_valid:
                print('{}: {} got invalid geometry'.format(count, gid))
                invalid.writerow(feature)
                continue

            cadastral_box = cadastral_shape.bounds

            idx_features = [n.object for n in idx.intersection(cadastral_box, objects=True)]
            infos = []
            shares = []
            idx_features_filtered = []
            for idx_feature in idx_features:
                pg = prepared_map[idx_feature['id']]
                if pg.intersects(cadastral_shape):
                    infos.append(idx_feature['properties'])
                    idx_features_filtered.append(idx_feature)

            ambiguous = False
            if len(idx_features_filtered) > 1:
                ambiguous = True

            for idx_feature in idx_features_filtered:
                if ambiguous:
                    g = idx_feature['geometry']
                    share = ( cadastral_shape.intersection(g).area / cadastral_shape.area )
                else:
                    share = 1.0
                shares.append(share)

            feature['ambiguous'] = ambiguous
            if len(infos) == 0:
                print('{}: {} {}'.format(count, gid, cadastral_shape.bounds))
                feature_copy = copy.deepcopy(feature)
                feature_copy['share'] = 0.0
                uncovered.writerow(feature_copy)
                continue

            print(count, gid, infos, shares)
            for i, info in enumerate(infos):
                subdist_name = info['name']
                state_name = info[state_name_key]
                dist_name = info[dist_name_key]

                if state_name not in out:
                    out[state_name] = {}
                if dist_name not in out[state_name]:
                    out[state_name][dist_name] = {}
                if subdist_name not in out[state_name][dist_name]:
                    out[state_name][dist_name][subdist_name] = getdictwriter('cadastrals/composite/{}/{}/{}.csv'.format(state_name, dist_name, subdist_name))
                writer = out[state_name][dist_name][subdist_name]
                feature_copy = copy.deepcopy(feature)
                feature_copy['share'] = shares[i]
                writer.writerow(feature_copy)

        page_info = data['pageInfo']
        has_next = page_info['hasNextPage']
        cursor = page_info['endCursor']
        filename = 'cadastrals/{}.json'.format(cursor)

