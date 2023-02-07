import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

base_url = 'https://mtcbus.tn.gov.in/Home/routewiseinfo'

session = requests.session()

data_dir = Path('data')
data_dir.mkdir(exist_ok=True, parents=True)


def get_route_lists():
    #route_list_file = data_dir / 'route_list.txt'
    #if route_list_file.exists():
    #    route_ids = route_list_file.read_text().split('\n')
    #    route_ids = [ r.strip() for r in route_ids if r.strip() != '' ]
    #    return set(route_ids)



    resp = session.get(base_url)
    
    if not resp.ok:
        raise Exception(f'unable to get data from {base_url}')
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    form = soup.find('form', { 'id': 'rwsearchform' })
    csrf_token = form.find('input', { 'name': 'csrf_test_name' }).attrs['value']
    
    sel = form.find('select', { 'id': 'selroute' })
    options = sel.find_all('option')
    route_ids = [ o.attrs['value'] for o in options ]
    return set(route_ids), csrf_token


route_ids, csrf_token = get_route_lists()

route_data_file = data_dir / 'route_data.jsonl'

route_data_file.touch()

known_routes = {}
with open(route_data_file, 'r') as f:
    lines = f.read().split('\n')
    lines = [ l.strip() for l in lines if l.strip() != '' ]
    routes = [ json.loads(l) for l in lines ]
    known_routes = { r['id']:r['stops'] for r in routes }



with open(route_data_file, 'a') as f:
    for route_id in route_ids:
        if route_id in known_routes:
            continue
        resp = session.get(base_url,
                           params={ 'submit': '',
                                    'selroute': route_id,
                                    'csrf_test_name': csrf_token })
        if not resp.ok:
            raise Exception(f'unable to get data for route {route_id}')

        soup = BeautifulSoup(resp.text, 'html.parser')
        ul = soup.find('ul', {'class': 'route'})
        stops = []
        lis = ul.find_all('li')
        for li in lis:
            s_id = li.find('span').text
            s_full = li.text
            s_name = s_full.removeprefix(s_id).strip()
            print(f'{s_id=} {s_full=} {s_name=}')
            stop = { 'stop_id': s_id, 'stop_name': s_name }
            stops.append(stop)
        
        line = json.dumps({ 'id': route_id, 'stops': stops })
        f.write(line)
        f.write('\n')

        
    



