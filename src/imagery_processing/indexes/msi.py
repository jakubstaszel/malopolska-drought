from pathlib import Path
import numpy as np
import os

from rasterio.warp import calculate_default_transform
import rasterio


def msi(product: str, B8A: Path, B11: Path, output_folder: Path) -> Path:
    """
    Calculates Moisture Stress Index.

    https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/msi/

    """
    print("    Calculating MSI for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB8A = rasterio.open(B8A)
    B8A = srcB8A.read().astype("f4")
    B11 = rasterio.open(B11).read().astype("f4")

    B8A[B8A <= 0] = np.nan
    B11[B11 <= 0] = np.nan

    msi = np.divide(B11, B8A)
    msi[(msi == np.inf) | (msi == -np.inf)] = np.nan

    msi[msi < 0] = np.nan
    msi[msi > 5] = np.nan

    dst_crs = "EPSG:3857"
    transform, wid, hei = calculate_default_transform(
        srcB8A.crs, dst_crs, srcB8A.width, srcB8A.height, *srcB8A.bounds
    )

    kwargs = srcB8A.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "msi_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(msi.astype(rasterio.float32))

    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
