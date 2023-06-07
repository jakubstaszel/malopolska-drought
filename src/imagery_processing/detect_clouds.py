import os
from pathlib import Path

import rasterio
from rasterio.enums import Resampling
from rasterio.features import shapes

import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon


def detect_clouds(
    product: str, cloud_classif_dir: Path, cloud_prob_dir: Path, output_folder: Path
) -> Path:
    print("    Detecting clouds for", product)

    clouds_series = gpd.GeoSeries(dtype=object)

    if cloud_prob_dir:
        clouds_prob = rasterio.open(cloud_prob_dir).read(1).astype("int")
        # if probability of cloud > 5% then it is cloud
        clouds_prob[clouds_prob <= 5] = 0
        clouds_prob[clouds_prob > 5] = 1

        clouds = clouds_prob

    if cloud_classif_dir:
        with rasterio.open(cloud_classif_dir) as clouds_init:
            # resample data to target shape
            clouds_class = clouds_init.read(
                out_shape=(
                    clouds_init.count,
                    int(clouds_init.height * 3),
                    int(clouds_init.width * 3),
                ),
                resampling=Resampling.bilinear,
            ).astype("int")[0]

            clouds = clouds + clouds_class

    # possible values [0, 1, 2]
    # 1 or 2 - cloud on 1 or 2 products
    clouds[clouds < 1] = 0
    clouds[clouds >= 1] = 1

    clouds_prob_dir = rasterio.open(cloud_prob_dir)

    # from raster with values 0 or 1 create vectors
    clouds_shapes = (
        Polygon(s["coordinates"][0])
        for i, (s, v) in enumerate(
            shapes(clouds, mask=None, transform=clouds_prob_dir.transform)
        )
        if v == 1.0
    )

    # GeoSeries to append from each product
    clouds_shapes = gpd.GeoSeries(data=clouds_shapes, crs=clouds_prob_dir.crs).to_crs(
        "EPSG:3857"
    )
    clouds_series = pd.concat([clouds_series, clouds_shapes])
    clouds_prob_dir.close()

    # final GeoSeries to save as .shp
    gs = gpd.GeoSeries(data=clouds_series, crs="EPSG:3857")

    location = output_folder.joinpath(f"{product}_clouds_mask.shp")
    gs.to_file(location)

    return location
