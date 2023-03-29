from pathlib import Path
import numpy as np
import os

from rasterio.warp import calculate_default_transform
import rasterio


def ndwi(product: str, B03: Path, B08: Path, output_folder: Path) -> Path:
    """
    Calculates Normalized Difference Water Index.
    """
    print("    Calculating NDWI for", product)
    # opening one of bands in separated to retrieve metadata to later save the raster
    srcB03 = rasterio.open(B03)
    B03 = srcB03.read().astype("f4")
    B08 = rasterio.open(B08).read().astype("f4")

    B03[B03 <= 0] = np.nan
    B08[B08 <= 0] = np.nan

    ndwi = np.divide((B03 - B08), (B03 + B08))

    ndwi[ndwi < -1] = np.nan
    ndwi[ndwi > 1] = np.nan

    dst_crs = "EPSG:3857"
    transform, wid, hei = calculate_default_transform(
        srcB03.crs, dst_crs, srcB03.width, srcB03.height, *srcB03.bounds
    )

    kwargs = srcB03.meta.copy()
    kwargs.update(driver="GTiff", dtype=rasterio.float32, count=1, compress="lzw")

    home = Path.cwd()
    os.chdir(output_folder)
    name = "ndwi_"
    with rasterio.open(name + product + ".tif", "w", **kwargs) as dst:
        dst.write(ndwi.astype(rasterio.float32))

    os.chdir(home)

    return output_folder.joinpath(name + product + ".tif")
