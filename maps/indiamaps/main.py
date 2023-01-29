import requests
import time
import json
import logging

logger = logging.getLogger(__name__)

base_url = "https://indiamaps.gov.in/server/rest/services"

base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300
}
bucket_name = "indiamaps_data"

#TODO: add layer ids to layers
to_scrape = {
    "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer": {
        "layer_params_map": {
            "50K_Data/50K_Poly1/DISTRICT_336": {
                "max_page_size": 1
            },
            "50K_Data/50K_Poly1/SUBDISTRICT_339": {
                "max_page_size": 5
            },
            "50K_Data/50K_Poly1/State_340": {
                "max_page_size": 1
            }
        }
    },
    "G2G_SOI/G2G_Portal/MapServer": {
        "whitelist": [
            "NUIS_Data/NUIS_Data/Water Bodies/TANK_D_115",
            "50K_Data/50K_Point/TEMPLE_206",
            "50K_Data/50K_Point/MOSQUE_219",
            "50K_Data/50K_Poly1/tracks_313",
            "50K_Data/50K_Poly1/STATE_343",
            "IndiaBoundary_344"
        ],
        "layer_params_map": {
            "50K_Data/50K_Poly1/STATE_343": {
                "max_page_size": 1
            },
            "IndiaBoundary_344": {
                "max_page_size": 1
            }
        }
    },
    "G2G_SOI/POI/MapServer": {
    },
    "G2G_SOI/G2G_IndiaBoundary/MapServer": {
        "layer_params_map": {
            "STATE_6": {
                "max_page_size": 1
            },
            "DISTRICT_1": {
                "max_page_size": 2
            },
            "SUBDISTRICT_0": {
                "max_page_size": 5
            }
        }
    },
    "G2G_SOI/G2G_Admin/MapServer": {
        "layer_params_map": {
            "INDIA_0": {
                "max_page_size": 1
            }
        }
    },
    "G2G_SOI/VillageBoundaryData/MapServer": {
    },
    "G2G_SOI/DDA_Data/MapServer": {
    },
    "SOI/Name_Places/MapServer": {
    },
    "SOI/G2C_Portal_BaseMap/MapServer": {
        "whitelist": [
            "50K_Data/50K_Poly1/MTOWNS_255",
            "50K_Data/50K_Poly1/roads_1_265",
            "50K_Data/50K_Poly1/roads_2_266",
            "50K_Data/50K_Poly1/SDHQ_257",
            "50K_Data/50K_Poly1/DISTRICT_246",
            "NUIS_Data/NUIS_Data/PUBLIC_SEMI_PUBLIC/WATER_TREATMENT_PLANT_74"
        ],
        "layer_params_map": {
            "50K_Data/50K_Poly1/DISTRICT_246": {
                "max_page_size": 1
            }
        }
    },
    "SOI/G2C_StateLanguageOtherthanEnglish/MapServer": {
        "layer_params_map": {
            "50K_Data/DISTRICT_0": {
                "max_page_size": 1
            },
            "50K_Data/STATE_1": {
                "max_page_size": 1
            }
        }
    },
    "SOI/SOI_Public_Portal/MapServer": {
        "whitelist": [
            "Public Portal/50K_Data/50K_Poly1/DISTRICT_BOUNDARY_265",
            "Public Portal/50K_Data/50K_Poly1/state_251",
            "Public Portal/50K_Data/50K_Point/TEMPLE_182",
            "Public Portal/50K_Data/50K_Point/GRAVE_188",
            "Public Portal/50K_Data/50K_Point/IDGAH_192"
        ],
        "layer_params_map": {
            "Public Portal/50K_Data/50K_Poly1/DISTRICT_BOUNDARY_265": {
                "max_page_size": 2
            },
            "Public Portal/50K_Data/50k_Poly1/state_251": {
                "max_page_size": 1
            }
        }
    },
    "SOI/FinalRoad_App/MapServer": {
    },
    "SOI/NH_App/MapServer": {
    },
    "SOI/SH_App/MapServer": {
    },
    "SOI/RailwayLine_App/MapServer": {
    },
    "SOI/SOISearch/MapServer": {
    },
    "SOI/SOIThemes/MapServer": {
         "whitelist": [
             "Religious_0"
         ]
    },
    "SOI/VillageBoundary/MapServer": {
    }
}

black_list = {
}

folder_blacklist = [
    "Swamitva"
]


match_ignore = {
   "G2G_SOI/G2G_PlanningTool/MapServer": None,
   "SOI/G2C_Portal_BaseMap/MapServer": [
      "50K_Data/50k_Point_1/New Group Layer_163"
   ],

   "Hosted/Scene_WSL1/MapServer": None,
}

known_matches = {
    "G2G_SOI/G2G_Portal/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_INFRASTRUCTURE/PO_8": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_INFRASTRUCTURE/PO_1_7",
    "G2G_SOI/G2G_Portal/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE_14": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE_1_13",
    "G2G_SOI/G2G_Portal/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH_15": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH_1_14",
    "G2G_SOI/G2G_Portal/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE_16": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE_1_15",
    "G2G_SOI/G2G_Portal/MapServer/50K_Data/50k_Point_1/jetty_202": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50k_Point_1/jetty_1_198",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/CHURCH_12": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/CHURCH_1_12",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE_13": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE_1_13",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH_14":  "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH_1_14",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE_15": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE_1_15",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/OTHER_LAND_USES/QUARRY_100": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/OTHER_LAND_USES/QUARRY_new_108",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/Water Bodies/POND_1_103": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/Water Bodies/POND_112",
    "SOI/G2C_Portal_BaseMap/MapServer/DSSDI_Data/RoadCenterLine_1_157": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/DSSDI_Data/RoadCenterLine_148",
    "SOI/G2C_Portal_BaseMap/MapServer/DSSDI_Data/RoadCenterLine_2_158": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/DSSDI_Data/RoadCenterLine_1_149",
    "SOI/G2C_Portal_BaseMap/MapServer/50K_Data/50K_Point/TEMPLE_1_183": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Point/TEMPLE_202",
    "SOI/G2C_Portal_BaseMap/MapServer/50K_Data/50K_Point/GRAVE_1_189": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Point/GRAVE_209",
    "SOI/G2C_Portal_BaseMap/MapServer/50K_Data/50K_Point/IDGAH_1_193": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Point/IDGAH_213",
    "SOI/G2C_Portal_BaseMap/MapServer/50K_Data/50K_Point/CHURCH_1_204": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Point/CHURCH_225",
    "SOI/G2C_Portal_BaseMap/MapServer/50K_Data/50K_Poly1/Railway Lines_267": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Poly1/railways_323",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/NUIS_Data/LANDMARKS_RELIGIOUS/CHURCH_12": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/CHURCH_1_12",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE_13": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE_1_13",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH_14": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH_1_14",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE_15": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE_1_15",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/50K_Data/50k_Point_1/ROCK_PINNACLE_CELL_172": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50k_Point_1/ROCKY_KNOB_CELL_175",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/50K_Data/50K_Poly1/tracks_248": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Poly1/tracks_1_309",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/DSSDI_Data/RoadCenterLine_156": [
        "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/DSSDI_Data/RoadCenterLine_148",
        "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/DSSDI_Data/RoadCenterLine_149"
    ],
    "SOI/SOIThemes/MapServer/Hospital_1": "SOI/SOISearch/MapServer/Hospital_App_0"
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
        from esriscraper.explore import get_all_info
        full_list, full_list_map = get_all_info(base_url, base_params, analysis_folder,
                                                folder_blacklist=folder_blacklist,
                                                interested_server_types=['MapServer'])
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
