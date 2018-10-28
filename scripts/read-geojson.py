import glob
import json
import os
import sys
import time

import fiona
import shapely.geometry


def main(args=None):
    args = args if args is not None else sys.argv[1:]
    geojson_path = args[1] if len(args) >= 2 else "output"

    t1 = time.clock()
    regions, features = process_regions(geojson_path)
    t2 = time.clock()

    print(json.dumps(regions, indent=2))
    print(f"{len(features)} features processed in {t2 - t1} seconds.")

    find_bbox_features(features, (17, 40, 18, 41))
    find_bbox_features(features, (10, 53, 12, 54))
    find_bbox_features(features, (16, 58, 18, 60))


def find_bbox_features(features, bbox):
    query_geometry = shapely.geometry.box(*bbox)
    t1 = time.clock()
    matching_features = find_features(features, query_geometry)
    t2 = time.clock()
    print(f"{len(matching_features)} features found in {t2 - t1} seconds for bbox {bbox}.")
    for feature_id, feature in matching_features.items():
        properties = feature["properties"]
        print(properties["Region_Name"], properties["Sub_Region_Name"], feature_id)


def find_features(features, query_geometry):
    matching_features = dict()
    for feature_id, feature in features.items():
        geometry = shapely.geometry.shape(feature["geometry"])
        if geometry.intersects(query_geometry):
            matching_features[feature_id] = feature
    return matching_features


def process_regions(geojson_path):
    regions = dict()
    features = dict()

    files = glob.glob(os.path.join(geojson_path, "*.geojson"))
    for file in files:
        with fiona.open(file, "r") as fc:
            for feature in fc:
                properties = feature["properties"]
                # See https://github.com/Toblerity/Fiona/issues/660: Property named "ID" renamed to "id"
                id_ = properties.get("ID") or properties.get("id")
                if id_ is None:
                    print(json.dumps(feature, indent=2))
                    raise ValueError("'ID' not found in property")

                region_name = properties.get("Region_Name")
                sub_region_name = properties.get("Sub_Region_Name")
                if region_name and sub_region_name:
                    if region_name not in regions:
                        regions[region_name] = dict()
                    sub_regions = regions[region_name]
                    if sub_region_name not in sub_regions:
                        sub_regions[sub_region_name] = list()
                    sub_region_list = sub_regions[sub_region_name]
                    sub_region_list.append(id_)
                features[id_] = feature

    return regions, features


if __name__ == "__main__":
    main()
