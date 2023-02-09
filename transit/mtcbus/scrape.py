import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

base_route_url = 'https://mtcbus.tn.gov.in/Home/routewiseinfo'
base_timing_url = 'https://mtcbus.tn.gov.in/Home/bustimingsearch'
base_origin_by_route_url = 'https://mtcbus.tn.gov.in/Home/getoriginbyroute'

def get_route_lists(session, url, form_name):
    resp = session.get(base_route_url)
    if not resp.ok:
        raise Exception(f'unable to get data from {base_url}')
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    form = soup.find('form', { 'id': 'rwsearchform' })
    csrf_token = form.find('input', { 'name': 'csrf_test_name' }).attrs['value']
    
    sel = form.find('select', { 'id': 'selroute' })
    options = sel.find_all('option')
    route_ids = [ o.attrs['value'] for o in options ]
    return set(route_ids), csrf_token


def get_route_stops(session, route_id, csrf_token):
    resp = session.get(base_route_url,
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

    return stops
 

def get_all_route_stops(known_routes, csrf_token):

    route_data_file = data_dir / 'route_data.jsonl'
    route_data_file.touch()
    
    # this is to make it resumable, in case scraping breaks midway
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
            stops = get_route_stops(session, route_id, csrf_token)
            line = json.dumps({ 'id': route_id, 'stops': stops })
            f.write(line)
            f.write('\n')


def get_route_stops_data(data_dir, session):    
    route_ids, csrf_token = get_route_lists(session, base_route_url, 'rwsearchform')
    get_all_route_stops(route_ids, csrf_token)


def get_route_timings(session, route_id, csrf_token):
    resp = session.get(base_origin_by_route_url,
                       params={ 'selfrom': '',
                                'selto': '',
                                'selroute': route_id,
                                'csrf_test_name': csrf_token })
    if not resp.ok:
        raise Exception(f'unable to get data for route {route_id}')
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    stop_divs = soup.find_all('div', recursive=False)
    stop_timings = []
    for stop_div in stop_divs:
        stop_name = stop_div.find('h6').text.strip()
        time_divs = stop_div.find_all('div')  
        timings = [ t.text.strip() for t in time_divs ]
        stop_timings.append({ 'stop': stop_name, 'timings': timings })
    return stop_timings


def get_all_route_timings(route_ids, csrf_token):

    route_timing_data_file = data_dir / 'route_timing_data.jsonl'
    route_timing_data_file.touch()
    
    # this is to make it resumable, in case scraping breaks midway
    known_routes = {}
    with open(route_timing_data_file, 'r') as f:
        lines = f.read().split('\n')
        lines = [ l.strip() for l in lines if l.strip() != '' ]
        routes = [ json.loads(l) for l in lines ]
        known_routes = { r['id']:r['stop_timings'] for r in routes }

    with open(route_timing_data_file, 'a') as f:
        for route_id in route_ids:
            if route_id in known_routes:
                continue
            stop_timings = get_route_timings(session, route_id, csrf_token)
            line = json.dumps({ 'id': route_id, 'stop_timings': stop_timings })
            f.write(line)
            f.write('\n')


def get_route_timing_data(data_dir, session):
    route_ids, csrf_token = get_route_lists(session, base_timing_url, 'timingsearchform')
    get_all_route_timings(route_ids, csrf_token)



if __name__ == '__main__':

    session = requests.session()

    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True, parents=True)
    get_route_stops_data(data_dir, session)
    get_route_timing_data(data_dir, session)


