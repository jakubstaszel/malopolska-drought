from pathlib import Path
import numpy as np
import os

from rasterio.warp import calculate_default_transform
import rasterio


def ndwi1(product: str, B8A: Path, B12: Path, output_folder: Path) -> Path:
    """
    Calculates Normalized Difference Water Index.

    https://edo.jrc.ec.europa.eu/documents/factsheets/factsheet_ndwi.pdf

    """
    print("    Calculating NDWI v1 for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB8A = rasterio.open(B8A)
    B8A = srcB8A.read().astype("f4")
    B12 = rasterio.open(B12).read().astype("f4")

    B8A[B8A <= 0] = np.nan
    B12[B12 <= 0] = np.nan

    ndwi = np.divide((B8A - B12), (B8A + B12))
    ndwi[(ndwi == np.inf) | (ndwi == -np.inf)] = np.nan

    ndwi[ndwi < -1] = np.nan
    ndwi[ndwi > 1] = np.nan

    dst_crs = "EPSG:3857"
    transform, wid, hei = calculate_default_transform(
        srcB8A.crs, dst_crs, srcB8A.width, srcB8A.height, *srcB8A.bounds
    )

    kwargs = srcB8A.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "ndwi1_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(ndwi.astype(rasterio.float32))

    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
