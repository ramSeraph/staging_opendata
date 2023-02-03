import json
import sys
import os
import os.path

s_code = sys.argv[1]

known_problems = [
        # file empty and id repeated at 28//545/4887, mapping file also empty
        '28/545/4887/285450699/boundary.geojson',
        # file empty, mapping file also empty
        '28/545/4887/285450670/boundary.geojson',
        # dir non existent, gp with id 229643 and similar name exists
        '33/602/6359/9990229643/boundary.geojson',
]


with open('mapping.json') as f:
    state_map = json.load(f)

s_name = state_map[s_code]['name']
s_name_o = s_name.replace(' ', '_')

dist_list_file = '{}/mapping.json'.format(s_code)
with open(dist_list_file) as f:
    dist_map = json.load(f)

dist_map_data = {
        "type": "FeatureCollection",
        "features" : []
}
subdist_map_data = {
        "type": "FeatureCollection",
        "features" : []
}
gp_map_data = {
        "type": "FeatureCollection",
        "features" : []
}
village_map_data = {
        "type": "FeatureCollection",
        "features" : []
}

for d_code in dist_map.keys():
    d_name = dist_map[d_code]['name']
    map_file_name = '{}/{}/boundary.geojson'.format(s_code, d_code)
    print('handling file: {}'.format(map_file_name))
    with open(map_file_name) as f:
        map_data = json.load(f)

    feature = {
        'type': 'Feature',
        'geometry': map_data,
        'properties': {
            's_name': s_name,
            's_code': s_code,
            'name': d_name,
            'code': d_code
        }
    }
    dist_map_data['features'].append(feature)
    subdist_list_file = '{}/{}/mapping.json'.format(s_code, d_code)
    with open(subdist_list_file) as f:
        subdist_map = json.load(f)
    for sd_code in subdist_map.keys():
        sd_name = subdist_map[sd_code]['name']
        map_file_name = '{}/{}/{}/boundary.geojson'.format(s_code, d_code, sd_code)
        print('handling file: {}'.format(map_file_name))
        with open(map_file_name) as f:
            map_data = json.load(f)

        feature = {
            'type': 'Feature',
            'geometry': map_data,
            'properties': {
                's_name': s_name,
                's_code': s_code,
                'd_name': d_name,
                'd_code': d_code,
                'name': sd_name,
                'code': sd_code
            }
        }
        subdist_map_data['features'].append(feature)
        block_village_list_file = '{}/{}/{}/village_mapping.json'.format(s_code, d_code, sd_code)
        with open(block_village_list_file) as f:
            block_village_map = json.load(f)


        gp_list_file = '{}/{}/{}/mapping.json'.format(s_code, d_code, sd_code)
        with open(gp_list_file) as f:
            gp_map = json.load(f)
        #print("gp list: {}".format(gp_map.keys()))
        covered = set()
        for gp_code in gp_map.keys():
            gp_name = gp_map[gp_code]['name']
            map_file_name = '{}/{}/{}/{}/boundary.geojson'.format(s_code, d_code, sd_code, gp_code)
            print('handling file: {}'.format(map_file_name))
            if map_file_name in known_problems:
                continue
            with open(map_file_name) as f:
                map_data = json.load(f)

            feature = {
                'type': 'Feature',
                'geometry': map_data,
                'properties': {
                    's_name': s_name,
                    's_code': s_code,
                    'd_name': d_name,
                    'd_code': d_code,
                    'sd_name': sd_name,
                    'sd_code': sd_code,
                    'name': gp_name,
                    'code': gp_code
                }
            }
            gp_map_data['features'].append(feature)


            village_list_file = '{}/{}/{}/{}/mapping.json'.format(s_code, d_code, sd_code, gp_code)
            with open(village_list_file) as f:
                village_map = json.load(f)
            #print("villages covered in gp {}: {}".format(gp_code, village_map.keys()))
            for v_code in village_map.keys():
                covered.add(v_code)
                v_name = village_map[v_code]['name']
                map_file_name = '{}/{}/{}/{}/{}/boundary.geojson'.format(s_code, d_code, sd_code, gp_code, v_code)
                if map_file_name in known_problems:
                    continue
                print('handling file: {}'.format(map_file_name))
                with open(map_file_name) as f:
                    map_data = json.load(f)
                feature = map_data

                feature = {
                    'type': 'Feature',
                    'geometry': map_data,
                    'properties': {
                        's_name': s_name,
                        's_code': s_code,
                        'd_name': d_name,
                        'd_code': d_code,
                        'sd_name': sd_name,
                        'sd_code': sd_code,
                        'gp_name': gp_name,
                        'gp_code': gp_code,
                        'name': v_name,
                        'code': v_code
                    }
                }
                village_map_data['features'].append(feature)
        
        #print("covered: {}".format(covered))
        #print("all: {}".format(set(block_village_map.keys())))
        uncovered_villages = set(block_village_map.keys()) - covered
        for v_code in uncovered_villages:
            v_name = block_village_map[v_code]['name']
            map_file_name = '{}/{}/{}/uncovered/{}/boundary.geojson'.format(s_code, d_code, sd_code, v_code)
            print('handling file: {}'.format(map_file_name))
            with open(map_file_name) as f:
                map_data = json.load(f)
            feature = map_data

            feature = {
                'type': 'Feature',
                'geometry': map_data,
                'properties': {
                    's_name': s_name,
                    's_code': s_code,
                    'd_name': d_name,
                    'd_code': d_code,
                    'sd_name': sd_name,
                    'sd_code': sd_code,
                    'gp_name': 'uncovered',
                    'gp_code': '0',
                    'name': v_name,
                    'code': v_code
                }
            }
            village_map_data['features'].append(feature)
 

dist_map_file = 'composite/{}/districts.geojson'.format(s_name_o)
os.makedirs(os.path.dirname(dist_map_file), exist_ok=True)
with open(dist_map_file, 'w') as f:
    json.dump(dist_map_data, f, indent=4)


subdist_map_file = 'composite/{}/subdistricts.geojson'.format(s_name_o)
os.makedirs(os.path.dirname(subdist_map_file), exist_ok=True)
with open(subdist_map_file, 'w') as f:
    json.dump(subdist_map_data, f, indent=4)


panchayats_map_file = 'composite/{}/panchayats.geojson'.format(s_name_o)
os.makedirs(os.path.dirname(panchayats_map_file), exist_ok=True)
with open(panchayats_map_file, 'w') as f:
    json.dump(gp_map_data, f, indent=4)


villages_map_file = 'composite/{}/villages.geojson'.format(s_name_o)
os.makedirs(os.path.dirname(villages_map_file), exist_ok=True)
with open(villages_map_file, 'w') as f:
    json.dump(village_map_data, f, indent=4)

