from pathlib import Path
import numpy as np
import os

import rasterio


def doc(product: str, B03: Path, B04: Path, output_folder: Path) -> Path:
    """
    Dissolved Organic Carbon
    """
    print("    Calculating DOC for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype("f4")
    B04 = rasterio.open(B04).read().astype("f4")

    B03[B03 <= 0] = np.nan
    B04[B04 <= 0] = np.nan

    doc = 432 * np.exp(-2.24 * B03 / B04)

    doc[doc <= 0] = np.nan

    kwargs = srcB03.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "doc_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(doc.astype(rasterio.float32))
    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
