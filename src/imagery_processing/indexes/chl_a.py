from pathlib import Path
import numpy as np
import os

import rasterio


def chl_a(product: str, B03: Path, B01: Path, output_folder: Path):
    """
    Concentration of Chlorophyll a
    """
    print("    Calculating Chl a for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype("f4")
    B01 = rasterio.open(B01).read().astype("f4")

    B03[B03 <= 0] = np.nan
    B01[B01 <= 0] = np.nan

    chla = 4.26 * np.float_power(B03 / B01, 3.94)

    chla[chla <= 0] = np.nan

    kwargs = srcB03.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "chla_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(chla.astype(rasterio.float32))
    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
