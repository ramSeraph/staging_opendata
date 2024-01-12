import requests
import time
import json
import logging

logger = logging.getLogger(__name__)

base_url = 'https://mapservice.gov.in/gismapservice/rest/services'

base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300
}
bucket_name = "bharatmaps_gismapservice_data"

to_scrape = {
    "BharatMapService/Block_Boundary/MapServer": {
        "layer_params_map": {
            "Block_0": {
                "max_page_size": 100
            }
        }
    },
    "BharatMapService/Village_Boundary/MapServer": {},
    "BharatMapService/Admin_Boundary_Village/MapServer": {
        "whitelist": [
            "SubDistrict_2"
        ]
    },
    "BharatMapService/Population_Density/MapServer": {
        "whitelist": [
            "District 2011_0",
            "Sub Distrcit 2011_1",
        ],
        "layer_params_map": {
            "District 2011_0": {
                "max_page_size": 10
            },
            "Sub Distrcit 2011_1": {
                "max_page_size": 100
            }
        }
    },
    "BharatMapService/GramPanchayat_Boundary/MapServer": {
    },
    "BharatMapService/Admin_Boundary_GramPanchayat/MapServer": {
        "whitelist": [
            "Block_2",
            "State_0",
        ],
        "layer_params_map": {
            "Block_2": {
                "max_page_size": 100
            },
            "State_0": {
                "max_page_size": 10
            },
        }
    },
    "BharatMapService/Admin_Boundary_Village/MapServer": {
        "whitelist": [
            "District_1",
        ],
        "layer_params_map": {
            "District_1": {
                "max_page_size": 10
            },
        }
    },
    "BharatMapService/AC_PC/MapServer": {
        "whitelist": [
            "Parliamentary Constituency_1",
            "Assembly Constituency_2",
        ],
        "layer_params_map": {
            "Parliamentary Constituency_1": {
                "max_page_size": 10
            },
            "Assembly Constituency_2": {
                "max_page_size": 100
            },
        }
    }

}

black_list = {
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
 

def get_token_simple():
    return 'AYoPi0yUpPCJsWAW5QDg0Lg71hhWxZntWPABr4NojcN-JQp9E8GzuHdANwja1Axpwx0mSSChEgQDKI4UHs9kXQ..'

def get_headers():
    return {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Host': 'mapservice.gov.in',
        'Pragma': 'no-cache',
        'Referer': 'https://lgdirectory.gov.in/',
        'Sec-Fetch-Dest': 'script',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }


def scrape_map_servers_wrap(**kwargs):
    from esridump.errors import EsriDownloadError
    attempt = 0

    max_delay = kwargs.pop('max_delay')
    delay = kwargs.pop('delay')

    need_new_token = True
    while True:
        if need_new_token:
            base_params = kwargs['base_params']
            token = get_token_simple()
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
        token = get_token_simple()
        base_params.update({ 'extra_query_args': { 'token': token } })
        base_params.update({ 'extra_headers': get_headers() })
        full_list, full_list_map = get_all_info(base_url, base_params, analysis_folder)
        exit(0)

    if sys.argv[1] == 'check':
        from esriscraper.check import run_checks
        run_checks(data_folder, analysis_folder, match_ignore, known_matches)
        exit(0)

    if sys.argv[1] == 'scrape':
        from esriscraper.utils import compress_and_push_to_gcs
        from esriscraper.scrape import scrape_map_servers
        token = get_token_simple()
        base_params.update({ 'extra_query_args': { 'token': token } })
        base_params.update({ 'extra_headers': get_headers() })
        scrape_map_servers_wrap(base_url=base_url,
                                base_params=base_params,
                                data_folder=data_folder,
                                to_scrape=to_scrape,
                                blacklist=black_list,
                                #post_processing_func=compress_and_push_to_gcs,
                                #post_processing_func_args={ 'bucket_name': bucket_name },
                                delay=15,
                                max_delay=900)
        exit(0)
