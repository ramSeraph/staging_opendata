base_url = "https://mapservice.gov.in/mapserviceserv176/rest/services"
base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300
}
bucket_name = 'bharatmaps_mapservice_data'

to_scrape = {
    #"India_Boundary/MapServer": {},
    #"CPC/CPC/MapServer": {},
    #"FSI/PlantationPolygon/MapServer": {},
    #"FSI/RFA/MapServer": {},
    #"dbt/bankNewCSC/MapServer": {
    #    "whitelist": [
    #        "CSC/CSC_1",
    #    ]
    #},
    #"RajasthanWaterBody/RajasthanWaterBody/MapServer": {},
    #"Matribhoomi/Matribhoomi/MapServer": {}
    "Panchayat/AdminGPHierarchy/MapServer": {
        "layer_params_map": {
            "District_1": {
                "max_page_size": 5
            },
            "Block_2": {
                "max_page_size": 100
            }
        }
    },
    "Panchayat/india_adminpoint/MapServer": {
        "whitelist": [
            "Internet Connectivity (Sources : BBNL 2023) _18"
        ]
    },
    "Panchayat/panchayat_admin/MapServer": {
        "whitelist": [
            "Census Villages_7"
        ]
    },
    "Street/StreetMap/MapServer": {
        "whitelist": [
            "Street4k/Mobile Towers_1056",
            "Street4k/NH_1076",
            "Street4k/sh_all_1077",
            "Street4k/road3_new_1078",
            "Street4k/10k_road/And_Road_1080",
            "Street4k/10k_road/AP_Road_1081",
            "Street4k/10k_road/arun_road_1082",
            "Street4k/10k_road/Assam_10k_1083",
            "Street4k/10k_road/Bih_Road_1084",
            "Street4k/10k_road/Chandi_Road_1085",
            "Street4k/10k_road/chh_road_1086",
            "Street4k/10k_road/Dadra_Road_1087",
            "Street4k/10k_road/Daman_Road_1088",
            "Street4k/10k_road/delhi_road1_1089",
            "Street4k/10k_road/Goa_Road_1090",
            "Street4k/10k_road/guj_Road_1091",
            "Street4k/10k_road/Har_road_1092",
            "Street4k/10k_road/HP_Road_1093",
            "Street4k/10k_road/Jha_Road_1094",
            "Street4k/10k_road/JK_Road_1095",
            "Street4k/10k_road/Kar_Road_1096",
            "Street4k/10k_road/Ker_Road_1097",
            "Street4k/10k_road/Laksh_Road_1098",
            "Street4k/10k_road/Mh_Road_1099",
            "Street4k/10k_road/mani_road_1100",
            "Street4k/10k_road/megh_road_1101",
            "Street4k/10k_road/mizo_road_1102",
            "Street4k/10k_road/MP_Road_1103",
            "Street4k/10k_road/Odisha_Road_1104",
            "Street4k/10k_road/pun_road_1105",
            "Street4k/10k_road/Puducherry_Road_1106",
            "Street4k/10k_road/raj_road_1107",
            "Street4k/10k_road/sik_road_1108",
            "Street4k/10k_road/Tel_Road_1109",
            "Street4k/10k_road/TN_Road_1110",
            "Street4k/10k_road/trip_road_1111",
            "Street4k/10k_road/Ukhand_Road_1112",
            "Street4k/10k_road/WB_Road_1113",
            "Street4k/10k_road/up_road_1114",
        ]
    }
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
