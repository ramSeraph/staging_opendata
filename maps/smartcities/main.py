import requests
import time
import json
import logging

logger = logging.getLogger(__name__)

base_url = 'https://gmis.smartcities.gov.in/server/rest/services'

base_headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
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
bucket_name = "smartcities_data"

to_scrape = {
    "CityData/MajorIndianCities/MapServer": {},
    "sbm/All_Indicator/MapServer": {},
    "GMIS/Central_Allocation/MapServer": {},
    "GMIS/GMIS/FeatureServer": {},
    "GMIS/gmislayers/MapServer": {},
    "UrbanObservatory/CityWiseData/MapServer": {},
    "UrbanObservatory/PMAYAHPProjectDetails/MapServer": {
        "whitelist": [
            "AHP Projects_0"
        ]
    },
    "UrbanObservatory/UrbanStatistic_PMAY/MapServer": {},
    "UrbanObservatory/UrbanStatistics/MapServer": {},
}

black_list = {
    "sbm/All_Indicator/MapServer": [
        'StateBoundary_0',
        'District_layer_1'
    ],
    "GMIS/gmislayers/MapServer": [
        'smartcity_gmisdb.sde.StateBoundary_2'
    ]
}

folder_blacklist = [
    "KmlConversion",
    "UrbanExpansion"
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
        #'extra_query_args': { 'token': token },
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
