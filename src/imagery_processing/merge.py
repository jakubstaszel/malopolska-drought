from pathlib import Path
from typing import List
from datetime import datetime

import rasterio
from rasterio.merge import merge
import numpy as np


def merge_rasters(index_name: str, layers_to_merge: List[Path], output_folder):
    """ """
    layers_opened = []
    for layer in layers_to_merge:
        layers_opened.append(rasterio.open(layer))

    src = layers_opened[0]
    rasters = []
    print("Merging : " + index_name)
    rasters.extend(layers_opened)
    mosaic, out_trans = merge(rasters, nodata=np.nan)

    kwargs = src.meta.copy()
    kwargs.update(
        driver="GTiff",
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        transform=out_trans,
        dtype=rasterio.float32,
        count=1,
        compress="lzw",
    )

    output_file = output_folder.joinpath(index_name + ".tif")
    with rasterio.open(output_file, "w", **kwargs) as dest:
        dest.write(mosaic)

    src.close()

    for layer in layers_opened:
        layer.close()

    return output_file
