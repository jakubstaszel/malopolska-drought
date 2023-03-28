import numpy as np
import os
from pathlib import Path

import rasterio
from rasterio.warp import calculate_default_transform


def cdom(product: str, B03: Path, B04: Path, output_folder: Path) -> Path:
    """
    Calculates CDOM index.
    Requires the title of the product, b03 and b04 bands.
    Saves the CDOM index in results directiory.
    """
    print("    Calculating CDOM for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype("f4")
    B04 = rasterio.open(B04).read().astype("f4")

    B03[B03 <= 0] = np.nan
    B04[B04 <= 0] = np.nan

    cdom = 537 * np.exp(-2.93 * B03 / B04)

    cdom[cdom <= 0] = np.nan

    dst_crs = "EPSG:3857"
    transform, wid, hei = calculate_default_transform(
        srcB03.crs, dst_crs, srcB03.width, srcB03.height, *srcB03.bounds
    )
    kwargs = srcB03.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "cdom_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(cdom.astype(rasterio.float32))

    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
