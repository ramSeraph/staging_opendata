base_url = "https://gisportal.ncscm.res.in/server/rest/services"
base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300
}
bucket_name = 'ncscm_data'

to_scrape = {
}

black_list = {
    "Hosted/survey123_13b5d88adc7a40728fe0c2a6834b61c7_form/FeatureServer": [ "survey_0" ],
    "Hosted/survey123_1a4ee73970234c18ada87000140d1bf3_form/FeatureServer": [ "survey_0" ],
    "Hosted/survey123_310effc0dfc24283bf8e17cb24b25504_form/FeatureServer": [ "survey_0" ],
}

folder_blacklist = [
    "Case",
    "CoralIndex",
    "Geoevent",
    "HTL",
    "KAGeotagged",
    "Mangrove_Cart",
    "Utilities",
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
                                delay=15,
                                max_delay=900)
        exit(0)
