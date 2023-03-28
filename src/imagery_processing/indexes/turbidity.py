from pathlib import Path
import numpy as np
import os

import rasterio


def turbidity(product: str, B03: Path, B01: Path, output_folder: Path) -> Path:
    """
    Calculates turbidity.
    Requires the title of the product, b03 and b04 bands.
    Saves the turbidity raster in results directiory.
    """
    print("    Calculating turbidity for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype("f4")
    B01 = rasterio.open(B01).read().astype("f4")

    B03[B03 <= 0] = np.nan
    B01[B01 <= 0] = np.nan

    turb = 8.93 * (B03 / B01) - 6.39

    # turb[turb <= 0] = np.nan

    kwargs = srcB03.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "turb_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(turb.astype(rasterio.float32))
    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
