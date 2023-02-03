#!/usr/bin/env python3

import sys
import argparse
import base64
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
import argparse
from pathlib import Path

opts = Options()
sleepTime1 = 4
sleepTime2 = 10

if '--headless' in sys.argv:
    opts.headless = True

url = "http://www.bhunaksha.cg.nic.in"
datadir = Path('CG')
datadir.mkdir(exist_ok=True, parents=True)

driver = webdriver.Firefox(options=opts)
driver.get(url)

def save_canvas(driver, canvas, outfile):
    canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
    # decode
    canvas_png = base64.b64decode(canvas_base64)
    # save to a file
    with open(outfile, 'wb') as f:
        f.write(canvas_png)
    

def process_district(driver, district, distDir):
    print(f"District {distname}", end=' ')
    elem = driver.find_element_by_xpath("//select[@id='level_2']")
    tehsils = elem.find_elements_by_tag_name("option")
    print(f" total tehsils {len(tehsils)}")
    for tehsil in tehsils:
        process_tehsil(driver, tehsil, distDir)

def process_tehsil(driver, tehsil, distDir):
    tname = tehsil.get_attribute('text')
    print(f" tehsil {tname}", end=' ')
    tehsil.click()
    time.sleep(sleepTime1)
    tdir = distDir / Path(tname)
    if tdir.exists():
        print(f"[WARN ] {tdir} exists. Ignoring...", file=sys.stderr)
        return
    tdir.mkdir(parents=True, exist_ok=True)
    elem = driver.find_element_by_xpath("//select[@id='level_3']")
    ris = elem.find_elements_by_tag_name("option")
    print(f"   total ris {len(ris)}")
    for ri in ris:
        process_ri(driver, ri, tdir)

def process_ri(driver, ri, tdir):
    riname = ri.get_attribute('text')
    ri.click()
    print(f"  RI {riname}", end=" ")
    time.sleep(sleepTime1)
    ridir = tdir / Path(riname)
    if ridir.exists():
        print(f"[WARN ] {ridir} exists. Ignoring...", file=sys.stderr)
        return
    ridir.mkdir(parents=True, exist_ok=True)

    # RI has villages
    elem = driver.find_element_by_xpath("//select[@id='level_4']")
    if not elem:
        print("[WARN ] No village found")
        return
    villages = elem.find_elements_by_tag_name("option")
    print(f"   total villages {len(villages)}")
    for village in villages:
        try:
            process_village(driver, village, ridir)
        except Exception as e:
            print(f' FAILED to process village {village}: {e}')

def process_village(driver, vill, halkadir):
    vname = vill.get_attribute('text')
    outfile = halkadir / f"{vname}.png"
    if outfile.exists():
        return
    vill.click()
    time.sleep(sleepTime2)
    print(f"     village {outfile}")
    canvas = driver.find_element_by_tag_name('canvas')
    save_canvas(driver, canvas, outfile)

# district
elem = driver.find_element_by_xpath("//select[@id='level_1']")
districts = elem.find_elements_by_tag_name("option")
for i, dist in enumerate(districts):
    dist.click()
    time.sleep(sleepTime1)
    distname = dist.get_attribute('text')
    distDir = datadir / Path(distname)
    distDir.mkdir(parents=True, exist_ok=True)
    try:
        process_district(driver, dist, distDir)
    except Exception as e:
        print(f"[INFO ] Failed {distname} {e}")
    print(f"Done {i} out of {len(districts)}")
driver.close()
