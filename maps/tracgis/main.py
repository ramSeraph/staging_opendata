base_url = "http://tracgis.telangana.gov.in/arcgis/rest/services"
base_params = {
    "max_page_size": 1000,
    "pause_seconds": 2,
    "requests_to_pause": 10,
    "num_of_retry": 5,
    "timeout": 300
}
bucket_name = "tracgis_data"

to_scrape = {
    "2bhk/2bhk/MapServer": {
        "whitelist": [
            "Plot Locations_0",
            "30_TENDER_PARCELS_7",
        ]
    },
    "Bhunaksha/Bhunaksha_Cadastral/MapServer": {
        "layer_params_map": {
            "Village_1": {
                "max_page_size": 100
            },
            "Mandals_2": {
                "max_page_size": 5
            },
            "District_3": {
                "max_page_size": 1
            }
        }
    },
    "Bhunaksha/Bhunaksha_query/MapServer": {
        "whitelist": [
            "ULB cadastral_1",
            "ULB Villages_2",
            "ULB_3",
            "Cadastral_7"
        ],
        "layer_params_map": {
            "ULB_3": {
                "max_page_size": 10
            }
        }
    },
    "CAD/Cadastral_Updation/MapServer": {
        "whitelist": [
            "Cadastral_OS_2273_Villages_0",
            "Administrative Layers/Mandal_Boundary_4",
            "Administrative Layers/Village_Boundary_5"
        ],
        "layer_params_map": {
            "Administrative Layers/Village_Boundary_5": {
                "max_page_size": 100
            },
            "Administrative Layers/Mandal_Boundary_4": {
                "max_page_size": 5
            }
        }
    },
    "CadastralAgricultureLULC/CadastralAgricultureLULC/MapServer": {
        "whitelist": [
            "FieldWork_Points_0",
            "CADASTRAL_AGRICULTURE_LULC_LAYER_1"
        ]
    },
    "CAM/I_CAD/MapServer": {
        "layer_params_map": {
            "District_9": {
                "max_page_size": 1
            },
            "Mandal_10": {
                "max_page_size": 5
            },
            "Village_12": {
                "max_page_size": 100
            }
        }
    },
    "CCLA/CadastralBasemap/MapServer": {},
    "CCLA/CadastralLayers/MapServer": {},
    "DistrictFormation/TS_NEW_DISTRICTS/MapServer": {
        "whitelist": [
            "Admin Boundaries/Assembly_Boundary_14",
            "Admin Boundaries/Revenue_Divisions_15"
        ],
        "layer_params_map": {
            "Admin Boundaries/Assembly_Boundary_14": {
                "max_page_size": 5
            },
            "Admin Boundaries/Revenue_Divisions_15": {
                "max_page_size": 1
            }
        }

    },
    "EducationWelfare/EducationWelfare_Query/MapServer": {
        "whitelist": [
            "TS_Residential_Dept_2409_updated_0"
        ]
    },
    "Endowment_Lands/Endowment_Lands_Query/MapServer": {
        "whitelist": [
            "Endowment Lands TS_3",
            "Hyderabad_Temples_Data_5",
            "Temples_Endowment_Data_Single_Polygon_6",
            "Temples_Endowment_Data_Transpose_Web_Final_withunique_7",
            "Temples_Endowment_Data_Web_Final_withunique_8",
            "Temples_Endowment_With_UniqueCode_9",
            "Temples_Endowment_With_UniqueCode_Transpose_10",
        ]
    },
    "Endowment_Lands/Endowment_Lands_Temples_Layer/MapServer": {
        "whitelist": [
            "Parcel Level View/TS_Habitations_1",
            "Parcel Level View/Parcel_Level_2",
            "Parcel Level View/Laltitudes_Longitudes_4",
        ]   
    },
    "Excise/Excise_Department/MapServer": {},
    "flood/vul/MapServer": {},
    "GHMC/cmtyhall/MapServer": {},
    "GHMC/sport/MapServer": {},
    "GHMC2/GHMC2/MapServer": {},
    "GHMCDockets/Dockets/MapServer": {},
    "GHMCHealth/Health_Facilities/MapServer": {},
    "Gov_Assets/Government_Assets/MapServer": {},
    "GroundWater/GroundWaterWells/MapServer": {},
    "HMDA/HMDA/MapServer": {},
    "Mapping/Huzurabad_Admin/MapServer": {},
    "ISMS_Agriculture/ISMS_Agriculture/MapServer": {
         "whitelist": [
             "isms_collected_points_0",
             "Cadastral Layer/Medak_2"
         ]
    },
    "MancherialMuncipality/Mancherial/MapServer": {},
    "MancherialMuncipality/MnclGVT/MapServer": {},
    "Mines/TS_Mines_Geology_Layer/MapServer": {},
    "Minor_Irrigation_Sensus/Minor_Irrigation_Sensus/MapServer": {},
    "Minor_Irrigation_Sensus/SixthMICensus/MapServer": {
         "whitelist": [
             "MICensusWholeData_0"
         ]
    },
    "Miscellaneous/KMM/MapServer": {},
    #"Plantation/Plantation_All": {}
    "PanchayatRaj/PR_Data/MapServer": {},
    "ResidentialSchools/EducationWelfare/MapServer": {},
    "RIS_NEW/RIS_AdminLayers/MapServer": {
         "whitelist": [
             "PWD Circles_6",
             "PWD Divisions_7"
         ]
    },
    "RIS_NEW/RIS_PRRoads/MapServer": {},
    "RIS_NEW/RIS_RBRoads/MapServer": {},
    "RIS_NEW/RIS_Symbology/MapServer": {
        "whitelist": [
            "Mandal Level View/Gram Panchayat Head Quarters Location (Point)_46",
            "Mandal Level View/Gram Panchayat Head Quarters Location (Poly)_59",
            "Mandal Level View/Existing R & B Roads/National Highway (Proposed)_61",
            "Mandal Level View/Existing R & B Roads/National Highway (NH)_62",
            "Mandal Level View/Existing R & B Roads/State Highway (SH)_63",
            "Mandal Level View/Existing R & B Roads/District Major Road (DMR)_64",
            "Mandal Level View/Existing R & B Roads/Other District Road (ODR)_65",
            "Mandal Level View/Other Road_66",
            "Mandal Level View/Existing P R Roads/BT Road_68",
            "Mandal Level View/Existing P R Roads/CC Road_69",
            "Mandal Level View/Existing P R Roads/WBM Road_70",
            "Mandal Level View/Existing P R Roads/Gravel Road_71",
            "Mandal Level View/Existing P R Roads/Earthen Road_72",
            "Mandal Level View/Proposed PR Road Connectivity/Ongoing Road_74",
            "Mandal Level View/Proposed PR Road Connectivity/Proposed Road_75"
        ]
    },
    "SchoolGIS/Schools/MapServer": {
        "whitelist": [
            "Management_1",
            "Anganwadi_Locations_Dept_2"
            "Management_3",
            "School Building Compound Wall_4",
            "Administrative Layers/Settlement Boundary_10",
            "Administrative Layers/Settlements Locations_11",
        ]
    },
    "SKS/SKS_Figures/MapServer": {},
    "TIS_Update/TIS_UPDATE/MapServer": {},
    "TSIIC/BaseLayers/MapServer": {},
    "TSIIC/Industrial_Infrastructure_Layers/MapServer": {},
    "TSTIS/MBasin/MapServer": {},
    "TSTIS/Jurisdiction/MapServer": {},
    "TSTIS/Tanks/MapServer": {},
    "TSTIS/Streams/MapServer": {},
}


black_list = {
    "Excise/Excise_Department/MapServer": [
        "Excise Admin /TS_Districts_1",
        "Excise Admin /TS_Villages_5",
        "Excise Admin /Excise_Mandals_4",
    ],
    "GHMC/sport/MapServer": [
        "GHMC_CIRCLES_0"
    ],
    "GHMCHealth/Health_Facilities_Admin_Layers/MapServer": [
        "Administrative Layers/Hyderabad_2"
    ],
    "Mines/TS_Mines_Geology_Layer/MapServer": [
        "Geo-Morphology_0",
        "Lithology_1",
        "Weathering_Morophology_4"
    ],
    "Plantation/Plantation_All/MapServer": [
        "Administrative Units Hyderabad Town/State Boundary_20",
        "Administrative Units Hyderabad Town/District Boundary_21",
    ],
    "TIS_Update/TIS_UPDATE/MapServer": [
        "District_0",
        "Mandal_1"
    ]
}

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
        from esriscraper.explore import get_all_info
        full_list, full_list_map = get_all_info(base_url, base_params, analysis_folder)
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
