from pathlib import Path
import numpy as np
import os

from rasterio.warp import calculate_default_transform, Resampling
import rasterio


def ndmi(product: str, B08: Path, B11: Path, output_folder: Path) -> Path:
    """
    Calculates Normalized Difference Moisture Index.

    """
    print("    Calculating NDMI for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB11 = rasterio.open(B11)
    B11 = srcB11.read().astype("f4")

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

    ndmi = np.divide((B08 - B11), (B08 + B11))

    ndmi[ndmi < 0] = np.nan
    ndmi[ndmi > 1] = np.nan

    dst_crs = "EPSG:3857"
    transform, wid, hei = calculate_default_transform(
        srcB11.crs, dst_crs, srcB11.width, srcB11.height, *srcB11.bounds
    )
    kwargs = srcB11.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "ndmi_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(ndmi.astype(rasterio.float32))

    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
