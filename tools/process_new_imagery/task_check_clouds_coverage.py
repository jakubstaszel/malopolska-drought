from typing import Final, Union
from pathlib import Path
from datetime import datetime
from shutil import rmtree

from shapely.geometry import Polygon
import geopandas

from src.imagery_processing.get_bands import bands_2A
from src.imagery_processing.sentinel_api import (
    data_check_2A,
    data_download_clouds_bands,
)

# clouds
from src.imagery_processing.detect_clouds import detect_clouds

# Roznowskie lake in Małopolska
POLYGON: Final = [
    [20.639198280192943, 49.689258119589113],
    [20.749934447137491,49.689258119589113],
    [20.749934447137491,49.768078665670942],
    [20.639198280192943,49.768078665670942],
    [20.639198280192943,49.689258119589113],
]


def check_folder(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def delete_folder_with_all_files(folder: Path):
    rmtree(folder)


def run_check_clouds_coverage(
    sen_from: Union[datetime, None], sen_to: Union[datetime, None]
) -> None:
    """
    This task supports only AOIs that are inside one imagery.
    """
    # -------------------------------------- find new products
    products_df = data_check_2A(
        check_folder(Path.cwd().joinpath("data", "download")),
        Polygon(POLYGON),
        sen_from,
        sen_to,
        if_polygon_inside_image=True,
    )

    # -------------------------------------- download bands for clouds
    if not products_df is None:
        downloaded = data_download_clouds_bands(
            check_folder(Path.cwd().joinpath("data", "clouds_coverage_data")),
            products_df,
        )

        output_folder_clouds = check_folder(
            Path.cwd().joinpath("data", "clouds_coverage_data", "clouds_shp")
        )
        statistics = []
        for folder in downloaded:
            bands = bands_2A(folder)

            # -------------------------------------- detect clouds
            clouds_file = detect_clouds(
                folder.name,
                bands["cloud_classif"],
                bands["cloud_prob"],
                output_folder_clouds,
            )

            # -------------------------------------- clip clouds to AOI
            aoi = geopandas.read_file(
                Path.cwd().joinpath(
                    "src",
                    "imagery_processing",
                    "geoms_for_merging",
                    "jezioro_roznowskie.shp",
                )
            )
            clouds = geopandas.read_file(clouds_file)
            clouds_aoiClipped = clouds.clip(aoi)

            statistics.append(
                {
                    "folder": folder.stem,
                    "clouds": sum(clouds_aoiClipped.area) / sum(aoi.area),
                }
            )

        for product in statistics:
            print(
                f"Clouds coverage in AOI: {(product['clouds']*100):.2f}% - {product['folder']}"
            )
