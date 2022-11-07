import requests
import time
import json
import logging

logger = logging.getLogger(__name__)

base_url = 'https://portal.mrsac.org.in/webadpgis8/rest/services'

base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300
}
bucket_name = "mrsac_data"

to_scrape = {
    "admin2011/admin_grampanchayat_2011/MapServer": {},
    "admin2011/admin_village_16/MapServer": {},
    "admin2011/admin_state_2011/MapServer": {},
    "agriculture/agriculture_admin_bnd/MapServer": {},
    "baselayers/cadastral/MapServer": {},
    "cidco/cidco_admin/MapServer": {},
    "cidco/cidco_basemap/MapServer": {},
    "cidco/cidco_chaturseema/MapServer": {},
    "cidco/cidco_communication/MapServer": {},
    "cidco/cidco_engineering/MapServer": {},
    "cidco/cidco_environment/MapServer": {
        "whitelist": [
            "CRZ Limits_3"
        ]
    },
    "cidco/cidco_hollow/MapServer": {},
    "cidco/cidco_lands/MapServer": {},
    "cidco/cidco_socialfacility/MapServer": {},
    "cidco/cidco_transport/MapServer": {},
    "cidco/cidco_utility/MapServer": {},
    "cidco/cidco/MapServer": {},
    "gatishakti/Eco_Senitive_zones/MapServer": {},
    "gatishakti/mh_forest/MapServer": {
        "layer_params_map": {
            "Territorial Circle/Forest_Admin_Range_Boundary_3": {
                "max_page_size": 10
            },
            "Territorial Circle/Forest_Admin_Round_Boundary_4": {
                "max_page_size": 100
            }
        }
    },
    "gatishakti/mh_roads/MapServer": {},
    #"gatishakti/MSEDCL_new/MapServer": {},
    "gatishakti/waterresources/MapServer": {},
    "geomin/geomin_master_plan/MapServer": {},
    "geomin/geomin_prospect_mineral/MapServer": {},
    "healthGIS/healthGIS_phc_service_area/MapServer": {},
    "healthGIS/healthGIS_pts/MapServer": {},
    "igr/igr_mumbai/MapServer": {},
    "jalyukt/jalyukt_combined/MapServer": {},
    "jalyukt/jalyukt_villages/MapServer": {},
    "jnpt/jnpt_admin/MapServer": {},
    "jnpt/jnpt_ELUPLU/MapServer": {},
    "jnpt/jnpt_Luse2000_2014/MapServer": {},
    "jnpt/jnpt_portlimit/MapServer": {},
    "jnpt/jnpt_property/MapServer": {
        "whitelist": [
            "BPCL Gas Pipe Line_19",
            "T1 Oil Line_20",
            "JNPT Asset Property_21",
            "JNPT Other Lands_22",
            "JNPT SEZ_23",
            "JNPT TankFarm_24",
            "JNPT Existing LandUse_25"
        ]
    },
    "jnpt/jnpt_Satellitedata/MapServer": {
        "whitelist": [
            "JNPT Administrative Boundary_0",
        ]
    },
    "jnpt/jnpt_seachannels/MapServer": {},
    "jnpt/jnpt_transport/MapServer": {},
    "jnpt/jnpt_zone_sector/MapServer": {},
    "nit/nit_admin/MapServer": {},
    "nit/nit_infrastructure/MapServer": {},
    "nit/nit_landuse/MapServer": {},
    "nit/nit_transportation/MapServer": {},
    "ris/ebm_roads/MapServer": {},
    "sandghat/sandghat/MapServer": {},
    "smartvillage/waterresources/MapServer": {}
}

black_list = {
    "cidco/cidco_admin/MapServer": [
        "CIDCO Grid-1Million_0",
        "CIDCO Grid-250000_1",
        "CIDCO Grid-50000_2",
        "CIDCO Grid-10000_3",
    ],
    "jnpt/jnpt_property/MapServer": [
        "JNPT Annotations/TEXT_2",
    ],
    "jnpt/jnpt_seachannels/MapServer": [
        "Channel Annotation/TEXT_3"
    ],
    "nit/nit_transportation/MapServer": [
        "Satellite Data/High Resolution Satellite Data_21"
    ]
}

match_ignore = {
}

known_matches = {
}

def get_token():
    token_url = 'https://portal.mrsac.org.in/webadpgis8/tokens/'
    post_data = {
        'request': 'getToken',
        'username': 'mrsac_viewer',
        'password': '@gsvieWer#2018',
        'expiration': '60',
        'f': 'json'
    }
    base_headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Host': 'portal.mrsac.org.in',
        'Origin': 'http://mrsac.maharashtra.gov.in',
        'Pragma': 'no-cache',
        'Referer': 'http://mrsac.maharashtra.gov.in/',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36 ',
    }

    headers = base_headers
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    resp = requests.post(token_url, data=post_data, headers=headers)
    if not resp.ok:
        logger.error(f'{resp.text=}')
        raise Exception('Unable to get token')
    tok_data = json.loads(resp.text)
    return tok_data['token']
 

def scrape_map_servers_wrap(**kwargs):
    from esridump.errors import EsriDownloadError
    attempt = 0

    max_delay = kwargs.pop('max_delay')
    delay = kwargs.pop('delay')

    need_new_token = True
    while True:
        if need_new_token:
            base_params = kwargs['base_params']
            token = get_token()
            base_params.update({ 'extra_query_args': { 'token': token } })
            need_new_token = False
        else:
            to_delay = delay * attempt
            if to_delay > max_delay:
                to_delay = max_delay
            logger.info(f'sleeping for {to_delay} secs before next attempt')
            time.sleep(to_delay)
            attempt += 1
        try:
            done = scrape_map_servers(**kwargs)
            if done:
                logger.info('All Done')
                return
        except EsriDownloadError as ex:
            if str(ex).find('Invalid Token') != -1:
                need_new_token = True
                logger.warning('Token expired..')
            else:
                logger.exception(f'{attempt=} to scrape failed')
        except Exception:
            logger.exception(f'{attempt=} to scrape failed')

if __name__ == '__main__':
    import os
    import sys
    import logging
    from pathlib import Path

    log_level = ( logging.DEBUG if os.environ.get('DEBUG', '0') == '1' else logging.INFO )
    logging.basicConfig(level=log_level)


    data_folder = Path('data')
    analysis_folder = data_folder / 'analysis'
    if sys.argv[1] == 'explore':
        from esriscraper.explore import get_all_info
        token = get_token()
        base_params.update({ 'extra_query_args': { 'token': token } })
        full_list, full_list_map = get_all_info(base_url, base_params, analysis_folder)
        exit(0)

    if sys.argv[1] == 'check':
        from esriscraper.check import run_checks
        run_checks(data_folder, analysis_folder, match_ignore, known_matches)
        exit(0)

    if sys.argv[1] == 'scrape':
        from esriscraper.utils import compress_and_push_to_gcs
        from esriscraper.scrape import scrape_map_servers
        scrape_map_servers_wrap(base_url=base_url,
                                base_params=base_params,
                                data_folder=data_folder,
                                to_scrape=to_scrape,
                                blacklist=black_list,
                                post_processing_func=compress_and_push_to_gcs,
                                post_processing_func_args={ 'bucket_name': bucket_name },
                                delay=15,
                                max_delay=900)
        exit(0)
