import os
from pathlib import Path

import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling


def epsg3857(layer: Path, output_folder: Path):
    """
    Saves reprojected to EPSG 3857 (Web Mercator) .tif file.
    Can delete provided product in the specified directory after reprojection.
    """
    name = layer.name.split(".tif")[0]
    print("Reprojecting: " + name)
    dst_crs = "EPSG:3857"
    with rasterio.open(layer) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update(
            {"crs": dst_crs, "transform": transform, "width": width, "height": height}
        )

        output_layer = output_folder.joinpath(name + "_epsg3857.tif")
        with rasterio.open(output_layer, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest,
                )

    return output_layer
