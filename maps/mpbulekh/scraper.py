#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
#     "pyproj",
#     "xmltodict",
#     "beautifulsoup4",
# ]
# ///
"""
MP Bhulekh WebGIS Scraper
Extracts API configuration from the Angular application
"""

import json
import re
from pathlib import Path

import requests
import xmltodict
from bs4 import BeautifulSoup
from pyproj import Transformer

BASE_URL = "https://webgis2.mpbhulekh.gov.in"
DATA_DIR = Path(__file__).parent / "data"

def sanitize_name(name: str) -> str:
    """Sanitize name for use in folder paths by replacing / with _"""
    return name.replace("/", "_")

# Coordinate transformer from WGS84 to UTM zone 43N
transformer_4326_to_32643 = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)


class TokenExpiredError(Exception):
    """Raised when access token expires (401 Unauthorized)."""
    pass


# --- GeoRSS to GeoJSON conversion (from pywmsdump) ---

def get_props_from_html(content):
    soup = BeautifulSoup(content, 'html.parser')
    lis = soup.find_all('li')
    props = {}
    for li in lis:
        txt = li.text.strip()
        parts = txt.split(':', 1)
        if len(parts) != 2:
            return {'unparsed': content}
        props[parts[0]] = parts[1].strip()
    return props


def get_points(vals):
    points = []
    curr_p = []
    for c in vals.split(' '):
        if len(curr_p) == 2:
            curr_p.reverse()
            points.append(curr_p)
            curr_p = []
        curr_p.append(float(c))
    if len(curr_p) == 2:
        curr_p.reverse()
        points.append(curr_p)
    return points


def extract_feature(entry):
    title = entry.get('title', None)
    content = entry.get('content', {}).get('#text', '')
    props = get_props_from_html(content)

    where = entry['georss:where']
    if 'georss:polygon' in where:
        points = get_points(where['georss:polygon'])
        geom = {'type': 'Polygon', 'coordinates': [points]}
    elif 'georss:line' in where:
        points = get_points(where['georss:line'])
        geom = {'type': 'LineString', 'coordinates': points}
    elif 'georss:point' in where:
        points = get_points(where['georss:point'])
        geom = {'type': 'Point', 'coordinates': points[0]}
    else:
        raise Exception(f'unexpected content in {where}')

    return {'type': 'Feature', 'id': title, 'geometry': geom, 'properties': props}


def combine_geoms(geoms):
    g_types = set()
    for g in geoms:
        g_types.add(g['type'])
    if len(g_types) > 1:
        return {'type': 'GeometryCollection', 'geometries': geoms}

    g_type = g_types.pop()
    if g_type not in ['Point', 'LineString', 'Polygon']:
        raise Exception(f'Unexpected geom type: {g_type}')
    out_type = 'Multi' + g_type
    coords = [g['coordinates'] for g in geoms]
    return {'type': out_type, 'coordinates': coords}


def combine_features(feats):
    by_fid = {}
    for feat in feats:
        fid = feat.get('id', None)
        if fid not in by_fid:
            by_fid[fid] = []
        by_fid[fid].append(feat)

    new_feats = []
    for fid, f_feats in by_fid.items():
        if fid is None:
            new_feats.extend(f_feats)
            continue
        if len(f_feats) == 1:
            new_feats.extend(f_feats)
            continue
        non_empty_props = [f['properties'] for f in f_feats if f['properties'] != {}]
        if len(non_empty_props) > 1:
            new_feats.extend(f_feats)
            continue
        props = non_empty_props[0] if len(non_empty_props) > 0 else {}
        new_geom = combine_geoms([f['geometry'] for f in f_feats])
        new_feat = {'type': 'Feature', 'id': fid, 'properties': props, 'geometry': new_geom}
        new_feats.append(new_feat)
    return new_feats


def georss_extract_features(xml_text):
    # deal with some xml/unicode messups
    xml_text = re.sub(r'&#([a-zA-Z0-9]+);?', r'[#\1;]', xml_text)
    data = xmltodict.parse(xml_text)

    if 'feed' not in data:
        raise Exception('no feed in data')

    feed = data['feed']
    if 'entry' not in feed:
        return []

    entries = feed['entry']
    if type(entries) is not list:
        entries = [entries]

    feats = []
    for entry in entries:
        feat = extract_feature(entry)
        feats.append(feat)

    feats = combine_features(feats)
    return feats


# --- End GeoRSS conversion ---

COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Content-Type": "application/json",
    "Origin": BASE_URL,
    "Pragma": "no-cache",
    "Referer": f"{BASE_URL}/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
}


def get_headers(request_id: str, access_token: str | None = None, lang: str = "en") -> dict:
    """Build headers with optional auth token"""
    headers = {
        **COMMON_HEADERS,
        "qp-language-code": lang,
        "qp-tc-request-id": request_id,
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def fetch_html():
    """Fetch the main HTML page"""
    response = requests.get(BASE_URL)
    response.raise_for_status()
    return response.text


def extract_main_js_path(html: str) -> str:
    """Extract the main.*.js script path from HTML"""
    pattern = r'src="(main\.[a-f0-9]+\.js)"'
    match = re.search(pattern, html)
    if not match:
        raise ValueError("Could not find main.*.js in HTML")
    return match.group(1)


def fetch_js(js_path: str) -> str:
    """Fetch the JavaScript file"""
    url = f"{BASE_URL}/{js_path}"
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def extract_request_id(js_content: str) -> str:
    """Extract qp-tc-request-id from customAPIHeaders"""
    # Pattern: customAPIHeaders:[{key:"qp-tc-request-id",value:"..."}]
    pattern = r'customAPIHeaders:\s*\[\s*\{\s*key:\s*["\']qp-tc-request-id["\']\s*,\s*value:\s*["\']([^"\']+)["\']'
    match = re.search(pattern, js_content)
    if not match:
        raise ValueError("Could not find qp-tc-request-id in JS")
    return match.group(1)


def extract_captcha_key(js_content: str) -> str:
    """Extract captcha key from captcha config"""
    # Pattern: captcha:{key:"...",enable:...}
    pattern = r'captcha:\s*\{\s*key:\s*["\']([^"\']+)["\']'
    match = re.search(pattern, js_content)
    if not match:
        raise ValueError("Could not find captcha key in JS")
    return match.group(1)


def guest_login(request_id: str) -> dict:
    """Perform guest login and get session token"""
    url = f"{BASE_URL}/user/guest/public/login"
    headers = get_headers(request_id)
    payload = {"tenant_id": "gov.in"}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def get_locations(request_id: str, access_token: str, **level_ids) -> list:
    """Fetch locations. Pass level_1_id=0 for districts, level_3_id=district_id for tehsils"""
    url = f"{BASE_URL}/user/master/v1/public/location"
    headers = get_headers(request_id, access_token, lang="hi")
    payload = {"tenant_id": "gov.in", **level_ids}
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 401:
        raise TokenExpiredError("Access token expired")
    response.raise_for_status()
    return response.json()["data"]


def get_village_extent(request_id: str, access_token: str, loc_id: int) -> dict:
    """Fetch village extent/bounds"""
    url = f"{BASE_URL}/tcgis/parcel_map_editing/map_editing/v1/gis/village/extent"
    headers = get_headers(request_id, access_token)
    payload = {
        "loc_id": loc_id,
        "parcel_type": "",
        "parcel_no": "",
        "tenant_id": "gov.in",
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 401:
        raise TokenExpiredError("Access token expired")
    response.raise_for_status()
    return response.json()["data"]


def get_village_georss(request_id: str, loc_id: int, extent: dict, parcel_type: str = "S") -> bytes:
    """Fetch village plot boundaries as GeoRSS.
    
    Args:
        parcel_type: 'S' for survey-based, 'P' for plot-based cadastrals
    """
    # Convert extent from EPSG:4326 to EPSG:32643
    minx, miny = transformer_4326_to_32643.transform(extent['minx'], extent['miny'])
    maxx, maxy = transformer_4326_to_32643.transform(extent['maxx'], extent['maxy'])
    bbox = f"{minx},{miny},{maxx},{maxy}"
    
    params = {
        "service": "wms",
        "layers": "tcgis:vp_villagemap_bnd",
        "srs": "EPSG:32643",
        "serviceType": "wms",
        "work_space": "tcgis",
        "VIEWPARAMS": f"loc_id:{loc_id};parcel_type:{parcel_type}",
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "FORMAT": "application/atom xml",
        "TRANSPARENT": "true",
        "tiled": "true",
        "CRS": "EPSG:32643",
        "STYLES": "",
        "WIDTH": "1024",
        "HEIGHT": "1024",
        "BBOX": bbox,
    }
    url = f"{BASE_URL}/gis/v1/public/proxy"
    headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Referer": f"{BASE_URL}/",
        "qp-tc-request-id": request_id,
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.content


def get_tokens():
    """Get request_id and access_token."""
    print(f"Fetching HTML from {BASE_URL}...")
    html = fetch_html()
    
    print("Extracting main.js path...")
    js_path = extract_main_js_path(html)
    print(f"  Found: {js_path}")
    
    print(f"Fetching {js_path}...")
    js_content = fetch_js(js_path)
    print(f"  Downloaded {len(js_content)} bytes")
    
    print("Extracting API configuration...")
    request_id = extract_request_id(js_content)
    print(f"  qp-tc-request-id: {request_id}")
    
    captcha_key = extract_captcha_key(js_content)
    print(f"  captcha key: {captcha_key}")
    
    print("Performing guest login...")
    login_response = guest_login(request_id)
    access_token = login_response["data"]["access_token"]
    print(f"  Got access token (expires in {login_response['data']['expires_in']}s)")
    
    return request_id, access_token, captcha_key


def scrape_data(request_id, access_token):
    """Scrape all data - districts, tehsils, villages, and parcels."""
    # Fetch or load districts
    DATA_DIR.mkdir(exist_ok=True)
    districts_file = DATA_DIR / "districts.json"
    if districts_file.exists():
        print("Loading districts from cache...")
        with open(districts_file, encoding="utf-8") as f:
            districts = json.load(f)
        print(f"  Loaded {len(districts)} districts")
    else:
        print("Fetching districts...")
        districts = get_locations(request_id, access_token, level_1_id=0)
        print(f"  Found {len(districts)} districts:")
        for loc in districts:
            print(f"    {loc.get('district_id')}: {loc.get('district')}")
        with open(districts_file, "w", encoding="utf-8") as f:
            json.dump(districts, f, ensure_ascii=False, indent=2)
        print(f"  Saved to {districts_file}")
    
    # Fetch tehsils for each district
    print("Fetching tehsils...")
    for district in districts:
        district_id = district["district_id"]
        district_name = district["district"]
        
        # Create district subdirectory
        district_dir = DATA_DIR / f"{district_id}_{sanitize_name(district_name)}"
        district_dir.mkdir(exist_ok=True)
        
        tehsils_file = district_dir / "tehsils.json"
        if tehsils_file.exists():
            print(f"  {district_name}: cached")
        else:
            tehsils = get_locations(request_id, access_token, level_3_id=district_id)
            print(f"  {district_name}: {len(tehsils)} tehsils")
            with open(tehsils_file, "w", encoding="utf-8") as f:
                json.dump(tehsils, f, ensure_ascii=False, indent=2)
    
    # Fetch villages for each tehsil
    print("Fetching villages...")
    for district in districts:
        district_id = district["district_id"]
        district_name = district["district"]
        district_dir = DATA_DIR / f"{district_id}_{sanitize_name(district_name)}"
        
        # Load tehsils for this district
        tehsils_file = district_dir / "tehsils.json"
        with open(tehsils_file, encoding="utf-8") as f:
            tehsils = json.load(f)
        
        for tehsil in tehsils:
            tehsil_id = tehsil["tehsil_id"]
            tehsil_name = tehsil["tehsil"]
            
            # Create tehsil subdirectory
            tehsil_dir = district_dir / f"{tehsil_id}_{sanitize_name(tehsil_name)}"
            tehsil_dir.mkdir(exist_ok=True)
            
            villages_file = tehsil_dir / "villages.json"
            if villages_file.exists():
                continue
            
            villages = get_locations(request_id, access_token, level_6_id=tehsil_id)
            print(f"  {district_name}/{tehsil_name}: {len(villages)} villages")
            
            with open(villages_file, "w", encoding="utf-8") as f:
                json.dump(villages, f, ensure_ascii=False, indent=2)
    
    # Fetch extent for each village
    print("Fetching village extents...")
    for district in districts:
        district_id = district["district_id"]
        district_name = district["district"]
        district_dir = DATA_DIR / f"{district_id}_{sanitize_name(district_name)}"
        
        tehsils_file = district_dir / "tehsils.json"
        with open(tehsils_file, encoding="utf-8") as f:
            tehsils = json.load(f)
        
        for tehsil in tehsils:
            tehsil_id = tehsil["tehsil_id"]
            tehsil_name = tehsil["tehsil"]
            tehsil_dir = district_dir / f"{tehsil_id}_{sanitize_name(tehsil_name)}"
            
            villages_file = tehsil_dir / "villages.json"
            with open(villages_file, encoding="utf-8") as f:
                villages = json.load(f)
            
            for village in villages:
                village_id = village["village_id"]
                village_name = village["village"]
                
                # Create village subdirectory
                village_dir = tehsil_dir / f"{village_id}_{sanitize_name(village_name)}"
                village_dir.mkdir(exist_ok=True)
                
                survey_geojsonl_file = village_dir / "survey_parcels.geojsonl"
                plot_geojsonl_file = village_dir / "plot_parcels.geojsonl"
                skip_file = village_dir / ".skip"
                
                # Skip if already processed
                if survey_geojsonl_file.exists() and plot_geojsonl_file.exists():
                    print(f"  {district_name}/{tehsil_name}/{village_name}: already scraped")
                    continue
                if skip_file.exists():
                    print(f"  {district_name}/{tehsil_name}/{village_name}: skipped (not georeferenced)")
                    continue
                
                # Fetch extent once (same for both types)
                print(f"  {district_name}/{tehsil_name}/{village_name}: fetching extent...")
                extent = get_village_extent(request_id, access_token, village_id)
                if not extent.get("isgeoref"):
                    # Mark as not georeferenced to skip in future
                    skip_file.touch()
                    continue
                
                # Fetch survey-based cadastrals (S flag)
                if not survey_geojsonl_file.exists():
                    georss_data = get_village_georss(request_id, village_id, extent, "S")
                    features = georss_extract_features(georss_data.decode("utf-8"))
                    with open(survey_geojsonl_file, "w", encoding="utf-8") as f:
                        for feat in features:
                            f.write(json.dumps(feat, ensure_ascii=False) + "\n")
                    print(f"  {district_name}/{tehsil_name}/{village_name}: {len(features)} survey parcels")
                
                # Fetch plot-based cadastrals (P flag)
                if not plot_geojsonl_file.exists():
                    georss_data = get_village_georss(request_id, village_id, extent, "P")
                    features = georss_extract_features(georss_data.decode("utf-8"))
                    with open(plot_geojsonl_file, "w", encoding="utf-8") as f:
                        for feat in features:
                            f.write(json.dumps(feat, ensure_ascii=False) + "\n")
                    print(f"  {district_name}/{tehsil_name}/{village_name}: {len(features)} plot parcels")


def main():
    request_id, access_token, captcha_key = get_tokens()
    
    while True:
        try:
            scrape_data(request_id, access_token)
            break
        except TokenExpiredError:
            request_id, access_token, _ = get_tokens()


if __name__ == "__main__":
    main()
