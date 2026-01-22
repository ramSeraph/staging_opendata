# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "esriscraper",
# ]
#
# [tool.uv.sources]
# esriscraper = { git = "https://github.com/ramSeraph/esriscraper" }
# ///

base_url = "https://gis.rajasthan.gov.in/rajasthan/rest/services"
base_params = {
    "max_page_size": 100,
    "pause_seconds": 2,
    "requests_to_pause": 100,
    "num_of_retry": 5,
    "timeout": 300,
    "proxy": "https://gis.rajasthan.gov.in/proxy/proxy.ashx?"
}
bucket_name = 'rajasthan_gis_data'

to_scrape = {
    #"GIS_Survey/Ward_Bndy_ULB/MapServer": {
    #},
    #"PHED_SMEK/PHED_SMEK/MapServer": {
    #    "whitelist": [
    #        "PHED/Ward Boundary_16"
    #    ]
    #},
    #"GIS_Survey/ULB/MapServer": {
    #    "whitelist": [
    #        "Municipal Boundary_1",
    #        "Building Footprint_5"
    #    ]
    #},
    "Settlement/SettlementData/MapServer": {
        "whitelist": [ "Khasra_0" ],
        "layer_params_map": {
            "Khasra_0": { "max_page_size": 1000 }
        }
    },
    #"Common/PoliceBndy/MapServer": {
    #    "whitelist": [ "Police Thana Boundary_0",
    #                   "New Police Thana Draft Boundary:03-11-2022 (26)_9",
    #                   "GRP Admin Boundary/GRP Thana Boundary_5" ]
    #},
    #"Citizen/SearchPOI_I/MapServer": {
    #}
}

black_list = {
    "Common/NetworkLocal/MapServer": [
        "Allroads_20"
    ],
    "Common/Network/MapServer": [
        "Allroads_20"
    ],
    "Health/Patient_Tracker_Display/MapServer": None,
    "RIICO/RIICOLANDBANK/MapServer": [
        "Zones_3"
    ],
    "Citizen/SearchPOI_R1/MapServer": [
        "Anganwadi_41"
    ],
    "GatiShakti/GatiShakti/MapServer": [
        "RAMS/Road Inventory/Road Type_114",
        "RAMS/Road Inventory/Shoulder Width_117",
        "RAMS/Road Inventory/Terrain Type_119",
        "RAMS/Road Furniture/Road Furniture_127",
    ],
    "GIS_Survey/GIS_Survey_Data1/MapServer": [
        "GIS Survey POI Data_0"
    ],
    "MJSA/MJSY/MapServer": [
        "Khasra_3",
        "Drainage/Drainage Line_5",
        "Land Use_7",
    ],
    "RRAMS/Environment/MapServer": [
        "Religious Places_0"
    ],
    "RRAMS/RoadCondition/MapServer": [
        "Roughness_0",
        "Rutting_6",
    ],
    "RRAMS/RoadFurniture/MapServer": [
        "Road Furniture_0",
    ],
    "RRAMS/RoadInventory/MapServer": [
        "Road Type_0",
        "Shoulder Width_3",
        "Terrain Type_5",
    ],
    "RRAMS/WorkProgramme/MapServer": None,
    "RIICO/RIICOInternalFacilities_from_SDO/MapServer": ["Internal Facilities/Roads_2"],
    "RoadAllocation/RoadAllocation/MapServer": [ "RAJ_STREETS_NONALLOCATED_3" ],
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
                                #post_processing_func=compress_and_push_to_gcs,
                                #post_processing_func_args={ 'bucket_name': bucket_name },
                                delay=15,
                                max_delay=900)
        exit(0)
