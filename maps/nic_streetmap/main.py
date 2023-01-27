import requests
import time
import json
import logging

logger = logging.getLogger(__name__)

base_url = 'https://mapservice.gov.in/mapserviceserv176/rest/services'

token = "VjLMTxgZzbtEIXsnQTi6v-1-JTraH9KEJUIY-2sfNbrO6Nq9FuKAVRHj65Z0H2SbHgRS5VEyXqvemEoHZaRRHQ.."

base_headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Origin': 'https://postalgis.nic.in',
    'Referer': 'https://postalgis.nic.in/',
    'Pragma': 'no-cache',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36 ',
}


base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300
}
bucket_name = "nic_streetmap_data"

to_scrape = {
    "misc/postal_admin/MapServer": {
        "layer_params_map": {
            "District_1": {
                "max_page_size": 10
            },
            "Block_2": {
                "max_page_size": 100
            },
        },
    },
    "misc/post/MapServer": {},
    #"cidco/cidco_environment/MapServer": {
    #    "whitelist": [
    #        "CRZ Limits_3"
    #    ]
    #},
    #"gatishakti/mh_forest/MapServer": {
    #    "layer_params_map": {
    #        "Territorial Circle/Forest_Admin_Range_Boundary_3": {
    #            "max_page_size": 10
    #        },
    #        "Territorial Circle/Forest_Admin_Round_Boundary_4": {
    #            "max_page_size": 100
    #        }
    #    }
    #},
}

black_list = {
    #"cidco/cidco_admin/MapServer": [
    #    "CIDCO Grid-1Million_0",
    #    "CIDCO Grid-250000_1",
    #    "CIDCO Grid-50000_2",
    #    "CIDCO Grid-10000_3",
    #],
}

folder_blacklist = [
    #"bharatmaps",
    #"panchayat",
    #"svamitva",
    #"Utilities"
]


match_ignore = {
}

known_matches = {
}



if __name__ == '__main__':
    import os
    import sys
    import logging
    from pathlib import Path

    log_level = ( logging.DEBUG if os.environ.get('DEBUG', '0') == '1' else logging.INFO )
    logging.basicConfig(level=log_level)


    base_params.update({
        'extra_query_args': { 'token': token },
        'extra_headers': base_headers,
    })
    data_folder = Path('data')
    analysis_folder = data_folder / 'analysis'
    if sys.argv[1] == 'explore':
        from esriscraper.explore import get_all_info
        full_list, full_list_map = get_all_info(base_url, base_params, analysis_folder, folder_blacklist=folder_blacklist)
        exit(0)

    if sys.argv[1] == 'check':
        from esriscraper.check import run_checks
        run_checks(data_folder, analysis_folder, match_ignore, known_matches)
        exit(0)

    if sys.argv[1] == 'scrape':
        from esriscraper.utils import compress_and_push_to_gcs
        from esriscraper.scrape import scrape_map_servers_wrap
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
