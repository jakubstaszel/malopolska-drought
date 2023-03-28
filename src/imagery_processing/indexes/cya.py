from pathlib import Path
import numpy as np
import os

import rasterio


def cya(product: str, B03: Path, B04: Path, B02: Path, output_folder: Path):
    """
    Density of Cyanobacteria
    """
    print("    Calculating Cya for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype("f4")
    B04 = rasterio.open(B04).read().astype("f4")
    B02 = rasterio.open(B02).read().astype("f4")

    B03[B03 <= 0] = np.nan
    B04[B04 <= 0] = np.nan
    B02[B02 <= 0] = np.nan

    cyaTemp = 115530.31 * np.float_power(B03 * B04 / B02, 2.38)
    cya = np.divide(cyaTemp, 10**12)

    cya[cya <= 0] = np.nan

    kwargs = srcB03.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "cya_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(cya.astype(rasterio.float32))
    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
