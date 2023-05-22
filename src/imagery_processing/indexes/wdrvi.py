from pathlib import Path
import numpy as np
import os

from rasterio.warp import calculate_default_transform
import rasterio


def wdrvi(product: str, B04: Path, B08: Path, output_folder: Path) -> Path:
    """
    Calculates Wide Dynamic Range Vegetation Index.

    https://calmit.unl.edu/people/agitelson2/pdf/JPP-04.pdf

    """
    print("    Calculating WDRVI for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB04 = rasterio.open(B04)
    B04 = srcB04.read().astype("f4")
    B08 = rasterio.open(B08).read().astype("f4")

    B08[B08 <= 0] = np.nan
    B04[B04 <= 0] = np.nan

    wdrvi = np.divide(((0.1 * B08) - B04), ((0.1 * B08) + B04))
    wdrvi[(wdrvi == np.inf) | (wdrvi == -np.inf)] = np.nan

    wdrvi[wdrvi < -1] = np.nan
    wdrvi[wdrvi > 1] = np.nan

    dst_crs = "EPSG:3857"
    transform, wid, hei = calculate_default_transform(
        srcB04.crs, dst_crs, srcB04.width, srcB04.height, *srcB04.bounds
    )
    kwargs = srcB04.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "wdrvi_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(wdrvi.astype(rasterio.float32))

    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
