#!/usr/bin/env -S uv run --with "wmsdump[punch-holes]"
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "wmsdump[punch-holes]",
# ]
# ///
"""
Collects all geojsonl files from data folders into single files with metadata.
Adds l1-l6 IDs, district/tehsil/village names (Hindi + English), and LGD codes.
Uses punch-holes from wmsdump to remove overlaps.
"""

import json
import sys
import tempfile
from pathlib import Path

from wmsdump.hole_puncher import punch_holes

DATA_DIR = Path(__file__).parent / "data"
COORD_PRECISION = 7


def truncate_coords(coords, precision: int = COORD_PRECISION):
    """Recursively truncate coordinates to specified decimal places."""
    if isinstance(coords, (int, float)):
        return round(coords, precision)
    return [truncate_coords(c, precision) for c in coords]


def truncate_geometry(geometry: dict, precision: int = COORD_PRECISION) -> dict:
    """Truncate all coordinates in a geometry to specified precision."""
    if geometry is None:
        return None
    geom = geometry.copy()
    if "coordinates" in geom:
        geom["coordinates"] = truncate_coords(geom["coordinates"], precision)
    elif "geometries" in geom:
        geom["geometries"] = [truncate_geometry(g, precision) for g in geom["geometries"]]
    return geom


def load_json(path: Path) -> list | dict:
    """Load JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_lookup_maps():
    """Build lookup maps for districts, tehsils, and villages."""
    districts_file = DATA_DIR / "districts.json"
    if not districts_file.exists():
        print(f"Error: {districts_file} not found")
        sys.exit(1)
    
    districts = load_json(districts_file)
    
    # district_id -> district info
    district_map = {d["district_id"]: d for d in districts}
    
    # tehsil_id -> tehsil info
    tehsil_map = {}
    
    # village_id -> village info
    village_map = {}
    
    for district in districts:
        district_id = district["district_id"]
        district_name = district["district"].replace("/", "_")
        district_dir = DATA_DIR / f"{district_id}_{district_name}"
        
        tehsils_file = district_dir / "tehsils.json"
        if not tehsils_file.exists():
            continue
        
        tehsils = load_json(tehsils_file)
        for tehsil in tehsils:
            tehsil_map[tehsil["tehsil_id"]] = tehsil
            tehsil_id = tehsil["tehsil_id"]
            tehsil_name = tehsil["tehsil"].replace("/", "_")
            tehsil_dir = district_dir / f"{tehsil_id}_{tehsil_name}"
            
            villages_file = tehsil_dir / "villages.json"
            if not villages_file.exists():
                continue
            
            villages = load_json(villages_file)
            for village in villages:
                village_map[village["village_id"]] = village
    
    return district_map, tehsil_map, village_map


def enrich_feature(feature: dict, village_info: dict, tehsil_info: dict, district_info: dict) -> dict:
    """Add metadata from hierarchy to feature properties and truncate coordinates."""
    props = feature.get("properties", {})
    
    # Drop loc_id and lgd_code from existing properties
    props.pop("loc_id", None)
    props.pop("lgd_code", None)
    
    # Add l1-l6 IDs from village info
    for key in ["l1_id", "l2_id", "l3_id", "l4_id", "l5_id", "l6_id"]:
        if key in village_info:
            props[key] = village_info[key]
    
    # Add district info
    props["district_name_en"] = district_info.get("district")
    props["district_name_hi"] = district_info.get("district_ll")
    props["district_lgd_code"] = district_info.get("lgd_code")
    
    # Add tehsil info
    props["tehsil_name_en"] = tehsil_info.get("tehsil")
    props["tehsil_name_hi"] = tehsil_info.get("tehsil_ll")
    props["tehsil_lgd_code"] = tehsil_info.get("lgd_code")
    
    # Add village info
    props["village_name_en"] = village_info.get("village")
    props["village_name_hi"] = village_info.get("village_ll")
    props["village_lgd_code"] = village_info.get("lgd_code")
    
    feature["properties"] = props
    
    # Truncate geometry coordinates
    if "geometry" in feature:
        feature["geometry"] = truncate_geometry(feature["geometry"])
    
    return feature


def collect_geojsonl(output_dir: Path, apply_punch_holes: bool = True):
    """
    Collect all geojsonl files into separate files for surveys and plots.
    
    Args:
        output_dir: Output directory path
        apply_punch_holes: Whether to apply punch-holes to remove overlaps
    """
    print(f"Building lookup maps...")
    district_map, tehsil_map, village_map = build_lookup_maps()
    
    # Count total districts for progress
    district_dirs = [d for d in sorted(DATA_DIR.iterdir()) 
                     if d.is_dir() and d.name != "__pycache__" and d.name.split("_")[0].isdigit()]
    total_districts = len(district_dirs)
    
    print(f"Collecting parcels from {total_districts} districts...")
    
    survey_count = 0
    plot_count = 0
    village_file_count = 0
    
    survey_file = output_dir / "all_survey_parcels.geojsonl"
    plot_file = output_dir / "all_plot_parcels.geojsonl"
    
    with open(survey_file, "w", encoding="utf-8") as survey_f, \
         open(plot_file, "w", encoding="utf-8") as plot_f:
        # Iterate through all district folders
        for district_idx, district_dir in enumerate(district_dirs, 1):
            # Parse district_id from folder name
            try:
                district_id = int(district_dir.name.split("_")[0])
            except ValueError:
                continue
            
            district_info = district_map.get(district_id, {})
            district_name = district_info.get("district", district_dir.name)
            
            # Count tehsils in this district
            tehsil_dirs = [t for t in sorted(district_dir.iterdir()) 
                          if t.is_dir() and t.name.split("_")[0].isdigit()]
            
            print(f"[{district_idx}/{total_districts}] {district_name} ({len(tehsil_dirs)} tehsils)")
            
            district_features = 0
            
            # Iterate through tehsil folders
            for tehsil_idx, tehsil_dir in enumerate(tehsil_dirs, 1):
                try:
                    tehsil_id = int(tehsil_dir.name.split("_")[0])
                except ValueError:
                    continue
                
                tehsil_info = tehsil_map.get(tehsil_id, {})
                tehsil_name = tehsil_info.get("tehsil", tehsil_dir.name)
                
                print(f"    [{tehsil_idx}/{len(tehsil_dirs)}] Processing tehsil: {tehsil_name}")
                
                tehsil_features = 0
                
                # Iterate through village folders
                for village_dir in sorted(tehsil_dir.iterdir()):
                    if not village_dir.is_dir():
                        continue
                    
                    try:
                        village_id = int(village_dir.name.split("_")[0])
                    except ValueError:
                        continue
                    
                    village_info = village_map.get(village_id, {})
                    village_name = village_info.get("village", village_dir.name)
                    
                    # Process both survey and plot parcels
                    for filename in ["survey_parcels.geojsonl", "plot_parcels.geojsonl"]:
                        geojsonl_file = village_dir / filename
                        if not geojsonl_file.exists():
                            continue
                        
                        # Check if file has content
                        if geojsonl_file.stat().st_size == 0:
                            continue
                        
                        village_file_count += 1
                        parcel_type = "survey" if "survey" in filename else "plot"
                        
                        # Apply punch-holes to this file first
                        if apply_punch_holes:
                            temp_fixed = Path(tempfile.mktemp(suffix=".geojsonl"))
                            try:
                                punch_holes(str(geojsonl_file), str(temp_fixed), use_offset=False, keep_map_file=False)
                                source_file = temp_fixed
                            except Exception as e:
                                # Fall back to original file if punch-holes fails
                                source_file = geojsonl_file
                                temp_fixed = None
                        else:
                            source_file = geojsonl_file
                            temp_fixed = None
                        
                        file_features = 0
                        out_f = survey_f if parcel_type == "survey" else plot_f
                        # Read and enrich features
                        with open(source_file, encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                
                                try:
                                    feature = json.loads(line)
                                    feature = enrich_feature(feature, village_info, tehsil_info, district_info)
                                    out_f.write(json.dumps(feature, ensure_ascii=False) + "\n")
                                    if parcel_type == "survey":
                                        survey_count += 1
                                    else:
                                        plot_count += 1
                                    tehsil_features += 1
                                    file_features += 1
                                except json.JSONDecodeError as e:
                                    print(f"      Warning: Invalid JSON in {geojsonl_file}: {e}")
                        
                        print(f"      {village_name} ({parcel_type}): {file_features} features")
                        
                        # Clean up temp file
                        if temp_fixed is not None and temp_fixed.exists():
                            temp_fixed.unlink()
                
                district_features += tehsil_features
                print(f"    [{tehsil_idx}/{len(tehsil_dirs)}] {tehsil_name} done: {tehsil_features} features")
            
            print(f"  District total: {district_features} features")
    
    print(f"\nCollected {survey_count} survey features and {plot_count} plot features from {village_file_count} village files")
    print(f"Output: {survey_file}, {plot_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect geojsonl files with metadata")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DATA_DIR,
        help="Output directory (default: data/)"
    )
    parser.add_argument(
        "--no-punch-holes",
        action="store_true",
        help="Skip punch-holes processing"
    )
    
    args = parser.parse_args()
    
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    apply_punch_holes = not args.no_punch_holes
    
    collect_geojsonl(output_dir, apply_punch_holes)
    
    print("Done!")


if __name__ == "__main__":
    main()
