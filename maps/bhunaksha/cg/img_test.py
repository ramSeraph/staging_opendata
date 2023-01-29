import json
import time
import subprocess
from pyproj import Transformer

import cv2

def run_external(cmd):
    print(f'running cmd - {cmd}')
    start = time.time()
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end = time.time()
    print(f'STDOUT: {res.stdout}')
    print(f'STDERR: {res.stderr}')
    print(f'command took {end - start} secs to run')
    if res.returncode != 0:
        raise Exception(f'command {cmd} failed')


img_fname = 'data/raw/22/57/01/01/329/vill.png'

cv_img = cv2.imread(img_fname)
h, w = cv_img.shape[:2]
h, w = h-1, w-1
print(h,w)
z = 0

bbox_fname = img_fname + '.bbox.json'
with open(bbox_fname, 'r') as f:
    b = json.load(f)

print(b)

epsg_44n = 'EPSG:32644'
epsg_ch_area = 'EPSG:4398'
epsg_ch_nsf_tm  = 'EPSG:7745'
epsg_ch_wgs84  = 'EPSG:7778'
#t = Transformer.from_crs(epsg_44n, 'EPSG:3857', always_xy=True)
#min_p = t.transform(float(b[0]), float(b[1]))
#max_p = t.transform(float(b[2]), float(b[3]))
#b = [ min_p[0], min_p[1], max_p[0], max_p[1] ]

a_ullr_str = f'{b[2]} {b[1]} {b[0]} {b[3]}'
print(a_ullr_str)

gtif_fname = img_fname.replace('.png', '.tif')
cmd = f'gdal_translate -of GTiff -a_srs {epsg_ch_wgs84} -a_ullr {a_ullr_str} {img_fname} {gtif_fname}'
run_external(cmd)
exit(0)

gcp_strs = []
gcp_strs.append(f'-gcp {z} {z} {b[0]} {b[3]}')
gcp_strs.append(f'-gcp {z} {h} {b[0]} {b[1]}')
gcp_strs.append(f'-gcp {w} {h} {b[2]} {b[1]}')
gcp_strs.append(f'-gcp {w} {z} {b[2]} {b[3]}')
gcp_str = ' '.join(gcp_strs)
print(gcp_str)

gtif_gcp_fname = img_fname.replace('.png', '.gcp.tif')
cmd = f'gdal_translate -of GTiff {gcp_str} {img_fname} {gtif_gcp_fname}'
run_external(cmd)

cmd = f'gdalwarp -t_srs EPSG:3857 {gtif_gcp_fname} {gtif_fname}'
run_external(cmd)



