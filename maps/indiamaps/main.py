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

to_scrape = {
    "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer": {
        "layer_params_map": {
            "50K_Data/50K_Poly1/DISTRICT": {
                "max_page_size": 1
            },
            "50K_Data/50K_Poly1/SUBDISTRICT": {
                "max_page_size": 5
            },
            "50K_Data/50K_Poly1/State": {
                "max_page_size": 1
            }
        }
    },
    "G2G_SOI/G2G_Portal/MapServer": {
        "whitelist": [
            "NUIS_Data/NUIS_Data/Water Bodies/TANK_D",
            "50K_Data/50K_Point/TEMPLE",
            "50K_Data/50K_Point/MOSQUE",
            "50K_Data/50K_Poly1/tracks",
            "50K_Data/50K_Poly1/STATE",
            "IndiaBoundary"
        ],
        "layer_params_map": {
            "50K_Data/50K_Poly1/State": {
                "max_page_size": 1
            },
            "IndiaBoundary": {
                "max_page_size": 1
            }
        }
    },
    "G2G_SOI/POI/MapServer": {
    },
    "G2G_SOI/G2G_IndiaBoundary/MapServer": {
        "layer_params_map": {
            "STATE": {
                "max_page_size": 1
            },
            "DISTRICT": {
                "max_page_size": 2
            },
            "SUBDISTRICT": {
                "max_page_size": 5
            }
        }
    },
    "G2G_SOI/G2G_Admin/MapServer": {
        "layer_params_map": {
            "INDIA": {
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
            "50K_Data/50K_Poly1/MTOWNS",
            "50K_Data/50K_Poly1/roads_1",
            "50K_Data/50K_Poly1/roads_2",
            "50K_Data/50K_Poly1/SDHQ",
            "50K_Data/50K_Poly1/DISTRICT",
            "NUIS_Data/NUIS_Data/PUBLIC_SEMI_PUBLIC/WATER_TREATMENT_PLANT"
        ],
        "layer_params_map": {
            "50K_Data/50K_Poly1/DISTRICT": {
                "max_page_size": 1
            }
        }
    },
    "SOI/G2C_StateLanguageOtherthanEnglish/MapServer": {
        "layer_params_map": {
            "50K_Data/DISTRICT": {
                "max_page_size": 1
            },
            "50K_Data/STATE": {
                "max_page_size": 1
            }
        }
    },
    "SOI/SOI_Public_Portal/MapServer": {
        "whitelist": [
            "Public Portal/50K_Data/50K_Poly1/DISTRICT_BOUNDARY",
            "Public Portal/50K_Data/50K_Poly1/state",
            "Public Portal/50K_Data/50K_Point/TEMPLE",
            "Public Portal/50K_Data/50K_Point/GRAVE",
            "Public Portal/50K_Data/50K_Point/IDGAH"
        ],
        "layer_params_map": {
            "Public Portal/50K_Data/50K_Poly1/DISTRICT_BOUNDARY": {
                "max_page_size": 2
            },
            "Public Portal/50K_Data/STATE": {
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
             "Religious"
         ]
    },
    "SOI/VillageBoundary/MapServer": {
    }
}

black_list = {
}

folder_blacklist = [
]


match_ignore = {
   "G2G_SOI/G2G_PlanningTool/MapServer": None,
   "SOI/G2C_Portal_BaseMap/MapServer": [
      "50K_Data/50k_Point_1/New Group Layer_163"
   ],
   "Swamitva/Swamitra_Yojana/MapServer": [
      "gisdb.sde.JOJKHERA",
      "gisdb.sde.SARKADI_MUNDI",
      "gisdb.sde.ASAWAR",
      "gisdb.sde.NAGLA_ANDHIYIRI",
      "gisdb.sde.AILCHINAGAR",
      "gisdb.sde.MALIKPUR",
      "gisdb.sde.MISRIPUR",
      "gisdb.sde.PURA_BHADAURIA",
      "gisdb.sde.UJJAINEY",
      "gisdb.sde.VIMATA_MAU",
      "gisdb.sde.TULSIPURA_MAJRA",
      "gisdb.sde.Jainpur",
      "gisdb.sde.Chandanpur",
      "gisdb.sde.Amawa",
      "SDE.Chatesar",
      "SDE.Sultanpur",
      "SDE.Nizampur"
   ],
   "Swamitva/Swamitra_Yojana_Feature_Editing/MapServer": None,
   "Hosted/Scene_WSL1/MapServer": None,
}

known_matches = {
    "G2G_SOI/G2G_Portal/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_INFRASTRUCTURE/PO": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_INFRASTRUCTURE/PO_1",
    "G2G_SOI/G2G_Portal/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE_1",
    "G2G_SOI/G2G_Portal/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH_1",
    "G2G_SOI/G2G_Portal/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE_1",
    "G2G_SOI/G2G_Portal/MapServer/50K_Data/50k_Point_1/jetty": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50k_Point_1/jetty_1",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/CHURCH": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/CHURCH_1",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE_1",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH":  "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH_1",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE_1",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/OTHER_LAND_USES/QUARRY": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/OTHER_LAND_USES/QUARRY_new",
    "SOI/G2C_Portal_BaseMap/MapServer/NUIS_Data/NUIS_Data/Water Bodies/POND_1": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/Water Bodies/POND",
    "SOI/G2C_Portal_BaseMap/MapServer/DSSDI_Data/RoadCenterLine_1": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/DSSDI_Data/RoadCenterLine",
    "SOI/G2C_Portal_BaseMap/MapServer/DSSDI_Data/RoadCenterLine_2": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/DSSDI_Data/RoadCenterLine_1",
    "SOI/G2C_Portal_BaseMap/MapServer/50K_Data/50K_Point/TEMPLE_1": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Point/TEMPLE",
    "SOI/G2C_Portal_BaseMap/MapServer/50K_Data/50K_Point/GRAVE_1": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Point/GRAVE",
    "SOI/G2C_Portal_BaseMap/MapServer/50K_Data/50K_Point/IDGAH_1": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Point/IDGAH",
    "SOI/G2C_Portal_BaseMap/MapServer/50K_Data/50K_Point/CHURCH_1": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Point/CHURCH",
    "SOI/G2C_Portal_BaseMap/MapServer/50K_Data/50K_Poly1/Railway Lines": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Poly1/railways",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/NUIS_Data/LANDMARKS_RELIGIOUS/CHURCH": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/CHURCH_1",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/GRAVE_1",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/IDGAH_1",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/NUIS_Data/LANDMARKS_RELIGIOUS/TEMPLE_1",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/50K_Data/50k_Point_1/ROCK_PINNACLE_CELL": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50k_Point_1/ROCKY_KNOB_CELL",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/50K_Data/50K_Poly1/tracks": "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/50K_Data/50K_Poly1/tracks_1",
    "SOI/SOI_Public_Portal/MapServer/Public Portal/DSSDI_Data/RoadCenterLine": [
        "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/DSSDI_Data/RoadCenterLine",
        "G2G_Basemap_Portal/G2G_Basemap_Portal/MapServer/DSSDI_Data/RoadCenterLine_1"
    ],
    "SOI/SOIThemes/MapServer/Hospital": "SOI/SOISearch/MapServer/Hospital_App"
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
