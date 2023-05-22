from pathlib import Path
import numpy as np
import os

from rasterio.warp import calculate_default_transform
import rasterio


def evi(product: str, B02: Path, B04: Path, B08: Path, output_folder: Path) -> Path:
    """
    Calculates Enhanced Vegetation Index.

    https://www.usgs.gov/landsat-missions/landsat-enhanced-vegetation-index

    """
    print("    Calculating EVI for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB04 = rasterio.open(B04)
    B04 = srcB04.read().astype("f4")
    B08 = rasterio.open(B08).read().astype("f4")
    B02 = rasterio.open(B02).read().astype("f4")

    B04[B04 <= 0] = np.nan
    B08[B08 <= 0] = np.nan
    B02[B02 <= 0] = np.nan

    evi_nominator = np.subtract(B08, B04)
    evi_denominator = B08 + np.multiply(B04, 6) - np.multiply(B02, 7.5) + 1
    evi = np.multiply(
        np.divide(evi_nominator, evi_denominator),
        2.5,
    )

    evi[(evi == np.inf) | (evi == -np.inf)] = np.nan

    evi[evi < -10] = np.nan
    evi[evi > 10] = np.nan

    dst_crs = "EPSG:3857"
    transform, wid, hei = calculate_default_transform(
        srcB04.crs, dst_crs, srcB04.width, srcB04.height, *srcB04.bounds
    )
    kwargs = srcB04.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "evi_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(evi.astype(rasterio.float32))

    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
