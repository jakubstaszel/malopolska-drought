from pathlib import Path
from typing import Union

import numpy as np
import rasterio
from rasterio.mask import mask
from geopandas.geoseries import GeoSeries

from src.db_client.models.aois import AOI


def masking_aoi(
    layer: Path,
    masking_geom: AOI,
    epoch: str,
    output_folder: Path,
    invert: bool = False,
) -> Union[Path, None]:
    """
    Mask product with an AOI, by default take raster values that are inside shapes.
    """
    if invert == True:
        crop = False
    else:
        crop = True

    print("Masking " + layer.name + " for AOI " + str(masking_geom.order_id))

    with rasterio.open(layer) as src:
        out_image, out_transform = mask(
            src,
            [masking_geom.geometry],
            crop=crop,
            nodata=np.nan,
            all_touched=True,
            invert=invert,
        )
        out_meta = src.meta

    # if all values in array are NaN
    if np.isnan(out_image).all():
        return None
    else:
        out_meta.update(
            {
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
            }
        )

        output_file = output_folder.joinpath(
            f"{str(masking_geom.order_id)}_{str(masking_geom.geom_id)}_{layer.name}"
        )
        with rasterio.open(output_file, "w", **out_meta) as dest:
            dest.write(out_image)
        return output_file


def masking(
    layer: Path,
    mask_name: str,
    masking_geom: GeoSeries,
    output_folder: Path,
    invert: bool = False,
) -> Union[Path, None]:
    """
    Mask product with a GeoSeries, by default take raster values that are inside shapes.
    """
    if invert == True:
        crop = False
    else:
        crop = True

    print("Masking " + layer.name + " with " + mask_name)

    with rasterio.open(layer) as src:
        out_image, out_transform = mask(
            src,
            masking_geom,
            crop=crop,
            nodata=np.nan,
            all_touched=True,
            invert=invert,
        )
        out_meta = src.meta

    # if all values in array are NaN
    if np.isnan(out_image).all():
        return None
    else:
        out_meta.update(
            {
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
            }
        )

        output_file = output_folder.joinpath(f"{layer.stem}_{mask_name}Masked.tif")
        with rasterio.open(output_file, "w", **out_meta) as dest:
            dest.write(out_image)
        return output_file
