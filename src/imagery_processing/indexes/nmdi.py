from pathlib import Path
import numpy as np
import os

from rasterio.warp import calculate_default_transform, Resampling
import rasterio


def nmdi(product: str, B08: Path, B11: Path, B12: Path, output_folder: Path) -> Path:
    """
    Calculates Normalized Multi-Band Drought Index.

    https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007gl031021
    """
    print("    Calculating NMDI for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB11 = rasterio.open(B11)
    B11 = srcB11.read().astype("f4")
    B12 = rasterio.open(B12).read().astype("f4")

    # band 8 is not available in 20m, using 10m and resampling
    upscale_factor = 1 / 2
    with rasterio.open(B08) as B08init:
        # resample data to target shape
        B08 = B08init.read(
            out_shape=(
                B08init.count,
                int(B08init.height * upscale_factor),
                int(B08init.width * upscale_factor),
            ),
            resampling=Resampling.bilinear,
        ).astype("f4")

    B08[B08 <= 0] = np.nan
    B11[B11 <= 0] = np.nan
    B12[B12 <= 0] = np.nan

    B11B12 = B11 - B12

    nmdi = np.divide(B08 - B11B12, B08 + B11B12)
    nmdi[(nmdi == np.inf) | (nmdi == -np.inf)] = np.nan

    # normalized, values from 0 to 1 are the only reasonable
    nmdi[nmdi < 0] = np.nan
    nmdi[nmdi > 1] = np.nan

    dst_crs = "EPSG:3857"
    transform, wid, hei = calculate_default_transform(
        srcB11.crs, dst_crs, srcB11.width, srcB11.height, *srcB11.bounds
    )
    kwargs = srcB11.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "nmdi_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(nmdi.astype(rasterio.float32))

    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
