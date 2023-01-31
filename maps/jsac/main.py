base_url = "https://gis1.jharkhand.gov.in/gisserver/rest/services"
base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300
}
bucket_name = 'jsac_data'

to_scrape = {
    "Gati_Shakti/Aadhar_Center/MapServer": {},
    "Gati_Shakti/Gati_Shakti/MapServer": {},
    "Large_Scale_2k/Large_Scale_Chaibasa/MapServer": {},
    "Large_Scale_2k/Large_Scale_chas/MapServer": {},
    "Large_Scale_2k/Large_Scale_deoghar/MapServer": {},
    "Large_Scale_2k/Large_Scale_dhanbad/MapServer": {},
    "Large_Scale_2k/Large_Scale_Dumka/MapServer": {},
    "Large_Scale_2k/Large_Scale_Giridih/MapServer": {},
    "Large_Scale_2k/Large_Scale_Hazaribagh/MapServer": {},
    "Large_Scale_2k/Large_Scale_palamu/MapServer": {},
    "Large_Scale_2k/Large_Scale_ranchi/MapServer": {},
    "District/Chatra_Forest_Plot/MapServer": {},
    "District/Chatra_M_Tower_OFC/MapServer": {},
    "District/Chatra_Portal/MapServer": {},
    "District/Chatra_Rural_road_network/MapServer": {},
    "District/Deoghar_Portal/MapServer": {},
    "District/Dhanbad_Portal/MapServer": {},
    "District/Dumka_Portal/MapServer": {},
    "District/East_Singhbhum_Portal/MapServer": {},
    "District/Garhwa_Portal/MapServer": {},
    "District/Giridih_Portal/MapServer": {},
    "District/Godda_Portal/MapServer": {},
    "District/Gumla_Portal/MapServer": {},
    "District/Hazaribag_Portal/MapServer": {},
    "District/Jamtara_Portal/MapServer": {},
    "District/Khunti_Portal/MapServer": {},
    "District/Koderma_Portal/MapServer": {},
    "District/Latehar_Portal/MapServer": {},
    "District/Lohardaga_Portal/MapServer": {},
    "District/Pakur_Portal/MapServer": {},
    "District/Palamu_Portal/MapServer": {},
    "District/Ramgarh_Portal/MapServer": {},
    "District/Ranchi_Portal/MapServer": {},
    "District/Ranchi_Scheme_Layer/MapServer": {},
    "District/Ranchi_waterbodies/MapServer": {},
    "District/Sahibganj_Portal/MapServer": {},
    "District/Sahibganj_mines/MapServer": {},
    "District/Saraikela_Portal/MapServer": {},
    "District/Simdega_Portal/MapServer": {},
    "District/West_Saranda_forest_boundary/MapServer": {},
    "District/West_Singhbhum_Portal/MapServer": {},
    "District/West_singhbhum_pds/MapServer": {},
    "landrecord/GM_Land/MapServer": {},
    "Census/Census_jharkhand/MapServer": {},
    "Registration/Registration_Data_Chatra/MapServer": {},
    "CUJ/Cuj_boundary/MapServer": {}
}

black_list = {
}

folder_blacklist = [
]

match_ignore = {
   "Hosted/MapServer": None,
   "SampleWorldCities/MapServer": None,
   "WMS_WFS/Sahibganj_Cadastral_Map/MapServer": None,
   "WMS_WFS/Simdega_WMS/MapServer": None,
   "JSAC/Cadastral_Map_webiste/MapServer": None
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
