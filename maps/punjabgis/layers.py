import time
import json
import requests
import xmltodict
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pprint import pprint

geoserver_url = 'https://punjabgis.punjab.gov.in/geoserver'
base_url = 'https://punjabgis.punjab.gov.in/geoserver/web/wicket/bookmarkable/org.geoserver.web.demo.MapPreviewPage?1&filter=false'
def get_layer_names(soup):
    lnames = []
    table = soup.find('table')
    tbody = table.find('tbody')
    
    for tr in tbody.find_all('tr'):
        tds = tr.find_all('td')
        layer_name = tds[2].text.strip()
        lnames.append(layer_name)
    return lnames

def get_next_link(soup, curr_page):
    span = soup.find('span', { 'class': 'paginator' })
    next_page = str(curr_page + 1)
    all_links = span.find_all('a')
    next_link = None
    for link in all_links:
        if link.text.strip() == next_page:
            next_link = link
            break
    if next_link is None:
        return None, None
    next_url = urljoin(url, next_link.get('href'))
    next_url = next_url.replace('ILinkListener', 'IBehaviorListener')
    next_url = next_url.replace('?0','?1')
    return next_url, next_link.get('id')


def get_preview_url(resp_text):
    soup = BeautifulSoup(resp_text, 'lxml')
    links = soup.find_all('a')     
    preview_link = None
    for link in links:
        if link.text.strip() == 'Layer Preview':
            preview_link = link
    if preview_link is None:
        raise Exception('no preview link')

    href = preview_link.get('href')
    parts = href.split('?')
    sub_parts = parts[0].split(';')
    cookie_piece = sub_parts[1]
    cparts = cookie_piece.split('=')
    cookie_dict = { cparts[0]: cparts[1] }
    base_url = sub_parts[0] + '?' + parts[1]
    return base_url, cookie_dict

def get_next_link_new(soup):
    span = soup.find('span', { 'class': 'paginator' })
    all_links = span.find_all('a')
    next_link = None
    for link in all_links:
        if link.get('disabled') == 'disabled':
            continue
        if link.text.strip() == '>':
            next_link = link
            break
    if next_link is None:
        return None, None
    next_link_id = next_link.get('id')
    next_url = None
    lines = []
    scripts = soup.find_all('script')
    for script in scripts:
        lines.extend(script.text.split('\n'))
    wicket_prefix = 'Wicket.Ajax.ajax('
    for line in lines:
        if line.startswith(wicket_prefix):
            line = line[len(wicket_prefix):]
            line = line[:-len(');;')]
            data = json.loads(line)
            if data['c'] == next_link_id:
                next_url = data['u']
                break
    return next_url, next_link_id


def get_next_link_alt(soup, script):
    span = soup.find('span', { 'class': 'paginator' })
    all_links = span.find_all('a')
    next_link = None
    for link in all_links:
        if link.get('disabled') == 'disabled':
            continue
        if link.text.strip() == '>':
            next_link = link
            break
    if next_link is None:
        return None, None
    next_link_id = next_link.get('id')
    next_url = None
    lines = []
    lines.extend(script.split(';'))
    wicket_prefix = '(function(){Wicket.Ajax.ajax('
    for line in lines:
        if line.startswith(wicket_prefix):
            line = line[len(wicket_prefix):]
            line = line[:-len(')')]
            data = json.loads(line)
            if data['c'] == next_link_id:
                next_url = data['u']
                break
    return next_url, next_link_id



def parse_page(resp_text):
    soup = BeautifulSoup(resp_text, 'lxml')
    lnames = get_layer_names(soup)
    next_link, next_link_id = get_next_link_new(soup)
    return lnames, next_link, next_link_id

def parse_page_ajax(resp_text):
    data = xmltodict.parse(resp_text)
    all_text = '\n'.join([e['#text'] for e in data['ajax-response']['component']])
    soup = BeautifulSoup(all_text, 'lxml')
    lnames = get_layer_names(soup)
    next_link, next_link_id = get_next_link_alt(soup, data['ajax-response']['evaluate'])
    return lnames, next_link, next_link_id

if __name__ == '__main__':

    all_lnames = []
    session = requests.session()

    # start at main page ( for cookies?)
    print('getting main page')
    resp = session.get(geoserver_url)
    if not resp.ok:
        raise Exception(f'unable to access geoserver page')

    #  move to the web page ( why?)
    print('getting web page')
    new_url = urljoin(resp.url, 'web/')
    resp = session.get(new_url)
    if not resp.ok:
        raise Exception(f'unable to get web page')

    # extract preview url
    preview_url, cookies = get_preview_url(resp.text)
    preview_url = urljoin(new_url, preview_url)

    # go to preview page
    pno = 1
    print(f'getting preview page {pno}')
    resp = session.get(preview_url)
    if not resp.ok:
        raise Exception(f'unable to get preview page')
    curr_url = resp.url
    wicket_base_url = '/'.join(base_url.split('/')[5:])
    headers = {
        'Referer': curr_url,
        'Wicket-Ajax': 'true',
        'Wicket-Ajax-Baseurl': wicket_base_url,
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }

    # get layer list and next link
    lnames, next_url, next_link_id = parse_page(resp.text)
    with open('layers.txt', 'w') as f:
        for lname in lnames:
            f.write(lname)
            f.write('\n')
    pno += 1

    #pprint(lnames)
    #pprint(next_link_id)
    #pprint(next_url)

    while next_link_id is not None:

        next_url = urljoin(curr_url, next_url)
        new_headers = {}
        new_headers.update(headers)
        new_headers.update({ 'Wicket-Focusedelementid': next_link_id })
        pprint(new_headers)
        print(f'getting preview page {pno}')
        resp = session.get(next_url, headers=new_headers)
        if not resp.ok:
            raise Exception(f'unable to get next page {pno}')
        lnames, next_url, next_link_id = parse_page_ajax(resp.text)
        #pprint(lnames)
        #pprint(next_link_id)
        #pprint(next_url)
        with open('layers.txt', 'a') as f:
            for lname in lnames:
                f.write(lname)
                f.write('\n')
        pno += 1

