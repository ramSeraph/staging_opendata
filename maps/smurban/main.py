import requests
import time
import json
import logging
#from playwright.sync_api import sync_playwright
import cfscrape

logger = logging.getLogger(__name__)

base_url = 'https://prodgis.sbmurban.org/server/rest/services'

#Cookie:
#AGS_ROLES="419jqfa+uOZgYod4xPOQ8Q=="; _ga=GA1.1.2121837532.1705041570; cf_clearance=dHSgiVW2u4gQitSCOEYzu_p8sXnZX9Gp5f1r4_yGXlg-1705041570-0-2-9a8e66e8.9472222d.cd8f3908-0.2.1705041570; _ga_MDVX6KVBHL=GS1.1.1705041569.1.1.1705041637.0.0.0

base_headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Referer': 'https://prodgis.sbmurban.org/ctpt-dashboard/',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36 ',
}


base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300
}
bucket_name = "smurban_data"

to_scrape = {
}

black_list = {
}

folder_blacklist = [
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
    scraper = cfscrape.create_scraper(delay=10)
    resp = scraper.get("https://sbmurban.org/swachh-bharat-mission-progess")
    print(resp.text)
    #session = requests.Session()
    #resp = session.get('https://sbmurban.org/swachh-bharat-mission-progess', verify=False)
    #if not resp.ok:
    #    logger.exception('unable to get main page')
    #    print(resp.text)
    #    exit(1)

    #print(session.cookies.get_dict())
    exit(0)

    base_params.update({
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
