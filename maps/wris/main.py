base_url = "https://arc.indiawris.gov.in/server/rest/services"

base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300
}
bucket_name = 'wris_data'

to_scrape = {
    "NWIC/JalDharohar_MI/MapServer": {
        "whitelist": [
            "First  Waterbody Census (MI)_11",
        ]
    },
    "SubInfoSysLCC/River_StreamOrder/MapServer": {
        "layer_params_map": {
            "Hydrological Boundary/Sub Basin_2": {
                "max_page_size": 10
            },
            "Hydrological Boundary/Watershed_3": {
                "max_page_size": 100
            },
            "River/Major Rivers/River Name_15": {
                "max_page_size": 10
            },
            "River/Major Rivers/River Name_16": {
                "max_page_size": 10
            },
            "River/River Polygon_17": {
                "max_page_size": 100
            },
        },
    },
    "SubInfoSysLCC/WaterBodies/MapServer": {
    },
    "SubInfoSysLCC/WaterResourceProject/MapServer": {
    },
    "SubInfoSysLCC/InlandNavigation/MapServer": {},
    "NWIC/Glacial_Lakes/MapServer": {},
    "NWIC/GroundwaterLevel_Stations/MapServer": {
        "whitelist": [
            "Ground Water Level_0"
        ]
    },
    "SubInfoSysLCC/InterBasinTransferLink/MapServer": {
        "whitelist": [
            "Inter Basin Transfer Links/Links_1",
            "Inter Basin Transfer Links/Structure on Links_2",
            "Inter Basin Transfer Links/IBTL Component_3",
            "Inter Basin Transfer Links/Waterbodies_4",
            "Inter Basin Transfer Links/Peninsular Links_5"
        ]
    }
}

black_list = {
   "NWIC/MIFirst_WBC/MapServer": [
       'First  WB Census (MI) - ≥ 1000 Ha_6',
       'First  WB Census (MI) - >100 to  ≥ 1000 Ha_7',
       'First  WB Census (MI) - >50 to  ≥ 100 Ha_8',
       'First  WB Census (MI) - >10 to  ≥ 50 Ha_9',
       'First  WB Census (MI) - >5 to  ≥ 10 Ha_10',
       'First  WB Census (MI) - >1 to  ≥ 5 Ha_11',
       'First  WB Census (MI) - >0.5 to  ≥ 1 Ha_12',
   ],
   'SubInfoSysLCC/WaterBodies_202212221251/MapServer': [
       'Waterbodies_0',
       'Surface Water Bodies/Reservoir <= 500 Ha _5',
       'Surface Water Bodies/Lake / Pond_6',
       'Surface Water Bodies/Others_7',
   ],
   "SubInfoSysLCC/River_StreamOrder/MapServer": [
       "River/Waterbody_5",
   ],
   "SubInfoSysLCC/WaterBodies/MapServer": [
       "Surface Water Bodies/River/River Polygon_9",
       "Surface Water Bodies/River/Major Rivers_10",
       "Surface Water Bodies/River/River Name_11",
   ],
    "SubInfoSysLCC/InlandNavigation/MapServer": [
        "Inland Navigation Waterways/International Boundary_1",
        "Inland Navigation Waterways/State Boundary_2",
        "Inland Navigation Waterways/District Boundary_3",
        "Inland Navigation Waterways/Settlement Location_5",
   ],
}

folder_blacklist = [
    #"EnchroachmentMP"
    "FeatureService",
    "Hosted",
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
                                post_processing_func=compress_and_push_to_gcs,
                                post_processing_func_args={ 'bucket_name': bucket_name },
                                delay=15,
                                max_delay=900)
        exit(0)
