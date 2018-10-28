import csv
import glob
import json
import os
import sys
import time
import uuid

import fiona
import fiona.transform
import shapely.geometry
import shapely.wkt


def main(args=None):
    args = args if args is not None else sys.argv[1:]
    regions_path = args[0] if len(args) >= 1 else "input"
    output_path = args[1] if len(args) >= 2 else "output"

    os.makedirs(output_path, exist_ok=True)

    region_count = 0

    def write_feature_collection(region_name, sub_region_name, features):
        nonlocal region_count, output_path
        region_count += 1
        file = os.path.join(output_path, f"{region_name}-{sub_region_name}.geojson")
        print("--> Writing", file, f"with {len(features)} features", "...")
        with open(file, "w") as fp:
            json.dump(dict(type="FeatureCollection", features=features), fp, indent=2)

    t1 = time.clock()
    process_regions(regions_path, write_feature_collection)
    t2 = time.clock()
    print(f"{region_count} regions processed in {t2 - t1} seconds.")


def process_regions(regions_path, on_features):
    region_names = os.listdir(regions_path)
    for region_name in region_names:
        sub_regions_path = os.path.join(regions_path, region_name)
        if os.path.isdir(sub_regions_path):
            if region_name.startswith("L2_"):
                region_name = region_name[3:]
            process_sub_regions(region_name, sub_regions_path, on_features)


def process_sub_regions(region_name, sub_regions_path, on_features):
    sub_region_names = os.listdir(sub_regions_path)
    for sub_region_name in sub_region_names:
        sub_region_path = os.path.join(sub_regions_path, sub_region_name)
        if os.path.isdir(sub_region_path):
            if sub_region_name.startswith("L2C_"):
                sub_region_name = sub_region_name[4:]
            process_sub_region(region_name, sub_region_name, sub_region_path, on_features)


def process_sub_region(region_name, sub_region_name, sub_region_path, on_features):
    features = []
    paths = glob.glob(os.path.join(sub_region_path, '*.shp'))
    for path in paths:
        features += read_shapefile(path)
    paths = glob.glob(os.path.join(sub_region_path, '*.wkt'))
    for path in paths:
        features += read_wkt(path)
    paths = glob.glob(os.path.join(sub_region_path, '*_wkt.txt'))
    for path in paths:
        features += read_wkt(path)
    paths = glob.glob(os.path.join(sub_region_path, '*_pins.txt'))
    for path in paths:
        features += read_pins(path)
    emit_features(features, region_name, sub_region_name, on_features)


def read_shapefile(file):
    print("<-- Reading", file, "...")
    with fiona.open(file, 'r') as features:
        return list(features)


def read_wkt(file):
    print("<-- Reading", file, "...")
    with open(file) as fp:
        geometry = shapely.wkt.load(fp)
    feature = dict(type="Feature", geometry=geometry.__geo_interface__, properties={})
    return [feature]


def read_pins(file):
    print("<-- Reading", file, "...")
    features = []
    with open(file, newline='') as fp:
        reader = csv.DictReader(fp, delimiter='\t')
        for row in reader:
            lon = float(row.pop('Longitude'))
            lat = float(row.pop('Latitude'))
            geometry = dict(type="Point", coordinates=[lon, lat])
            feature = dict(type="Feature", geometry=geometry, properties=row)
            features.append(feature)
    return features


def emit_features(features, region_name, sub_region_name, on_features):
    dst_crs = dict(init='epsg:4326')
    src_crs = features.crs if hasattr(features, "crs") else dst_crs
    transformed_features = []
    for feature in features:
        geometry = feature["geometry"]
        if src_crs != dst_crs:
            geometry = fiona.transform.transform_geom(src_crs, dst_crs, geometry)
        shape = shapely.geometry.shape(geometry)
        if shape.has_z:
            # "tidy" geometry, remove z coordinate
            shape = shape.buffer(1).buffer(-1)
            geometry = shape.__geo_interface__
        feature["geometry"] = geometry
        feature["properties"]["ID"] = uuid.uuid4().hex
        feature["properties"]["Sub_Region_Name"] = sub_region_name
        feature["properties"]["Region_Name"] = region_name
        transformed_features.append(feature)
    on_features(region_name, sub_region_name, transformed_features)


if __name__ == "__main__":
    main()
