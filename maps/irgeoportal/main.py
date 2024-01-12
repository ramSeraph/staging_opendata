base_url = "https://irgeoportal.gov.in/arcgis/rest/services"
base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300
}
bucket_name = 'irgeoportal_data'

to_scrape = {
    #"Civil_Engineering_Assets/FeatureServer": {},
    #"station_1_joined/FeatureServer": {},
    #"railway_track_cris_somya/MapServer": {},
    "UMP/Rail_Assets_Map/MapServer": {},
}

black_list = {
    #"MTC_TPZ/FeatureServer": None, 
    #"MTC_TPZ/MapServer": None, 
    #"offtrack_editing_v2/FeatureServer": None,
    #"offtrack_editing_v2/MapServer": None,
}

folder_blacklist = [
    "26032019esri",
    "ArcGISData",
    "Certificates",
    "Delete",
    "Demo",
    "Editing_Services",
    "GIS",
    "Hosted",
    "IR_Asset",
    "Orthophotos",
    "POC",
    "Test",
    "Utilities",
]

match_ignore = {
   "Hosted/MapServer": None,
   "SampleWorldCities/MapServer": None,
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
