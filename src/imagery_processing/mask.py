from pathlib import Path
from typing import Union

import numpy as np
import rasterio
from rasterio.mask import mask

from src.db_client.models.aois import AOI


def _check_folder(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def masking(
    layer: Path, maskingGeom: AOI, output_folder: Path, invert: bool = False
) -> Union[Path, None]:
    """
    Mask product with a shapefile, take raster values that are
    inside shapes.
    """
    if invert == True:
        crop = False
    else:
        crop = True

    print("Masking " + layer.name + " for AOI " + str(maskingGeom.order_id))

    with rasterio.open(layer) as src:
        out_image, out_transform = mask(
            src,
            [maskingGeom.geom],
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

        output_file = _check_folder(output_folder).joinpath(
            f"{str(maskingGeom.order_id)}_{str(maskingGeom.geom_id)}_{layer.name}"
        )
        with rasterio.open(output_file, "w", **out_meta) as dest:
            dest.write(out_image)
        return output_file
