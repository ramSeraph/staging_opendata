base_url = "https://gis.rajasthan.gov.in/rajasthan/rest/services"
base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300,
    "proxy": "https://gis.rajasthan.gov.in/proxy/proxy.ashx?"
}
bucket_name = 'rajasthan_gis_data'

to_scrape = {
}

black_list = {
    "Common/NetworkLocal/MapServer": [
        "Allroads_20"
    ],
    "Common/Network/MapServer": [
        "Allroads_20"
    ],
    "GIS_Survey/Basemap_GISSurvey/MapServer": None,
}

folder_blacklist = [
]

match_ignore = {
   #"Hosted/MapServer": None,
   #"SampleWorldCities/MapServer": None,
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

    data_folder = Path('data')
    analysis_folder = data_folder / 'analysis'
    if sys.argv[1] == 'explore':
        analysis_folder.mkdir(exist_ok=True, parents=True)
        from esriscraper.explore import get_all_info
        full_list, full_list_map = get_all_info(base_url, base_params, analysis_folder,
                                                blacklist=black_list,
                                                folder_blacklist=folder_blacklist)
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
                                ignore_layer_types=['Raster Layer'],
                                post_processing_func=compress_and_push_to_gcs,
                                post_processing_func_args={ 'bucket_name': bucket_name },
                                delay=15,
                                max_delay=900)
        exit(0)
