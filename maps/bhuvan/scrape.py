#from PIL import Image
import json
from io import StringIO
#import requests
from owslib.wms import WebMapService
import pickle
from pprint import pprint

more_urls = [
    "https://bhuvan-vec1.nrsc.gov.in/bhuvan/parks/wms?"
]

urls = [
#    "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms?",
    "https://bhuvan-vec1.nrsc.gov.in/bhuvan/wms?",
#    "https://bhuvan-vec3.nrsc.gov.in/bhuvan/wms?",
]

#urls = [
#    "https://bhuvan-gp1.nrsc.gov.in/bhuvan/wms?",
#]

layers = {}
for url in urls:
    print(f'handling {url}')
    wms = WebMapService(url, version='1.1.1')
    groups = {}
    for k, v in wms.items():
        print(k)
        if k.find(':') != -1:
            gname = k.split(':')[0]
            rest = ':'.join(k.split(':')[1:])
        else:
            gname = k
            rest = k
    
        if gname not in groups:
            groups[gname] = []
        groups[gname].append(rest)
    layers[url] = groups

with open('data/layers_1.json', 'w') as f:
    json.dump(layers, f)

