from pathlib import Path
import numpy as np
import os

from rasterio.warp import calculate_default_transform
import rasterio


def msavi2(product: str, B04: Path, B08: Path, output_folder: Path) -> Path:
    """
    Calculates Modified Soil Adjusted Vegetation Index.

    https://www.usgs.gov/landsat-missions/landsat-modified-soil-adjusted-vegetation-index

    """
    print("    Calculating MSAVI2 for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB04 = rasterio.open(B04)
    B04 = srcB04.read().astype("f4")
    B08 = rasterio.open(B08).read().astype("f4")

    B04[B04 <= 0] = np.nan
    B08[B08 <= 0] = np.nan

    msavi2 = np.divide(
        2 * B08 + 1 - np.sqrt(np.power(2 * B08 + 1, 2) - 8 * (B08 - B04)), 2
    )

    msavi2[(msavi2 == np.inf) | (msavi2 == -np.inf)] = np.nan

    msavi2[msavi2 < -1] = np.nan
    msavi2[msavi2 > 1] = np.nan

    dst_crs = "EPSG:3857"
    transform, wid, hei = calculate_default_transform(
        srcB04.crs, dst_crs, srcB04.width, srcB04.height, *srcB04.bounds
    )

    kwargs = srcB04.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "msavi2_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(msavi2.astype(rasterio.float32))

    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
