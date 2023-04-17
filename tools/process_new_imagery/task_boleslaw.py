from typing import Final, Union, List
from pathlib import Path
from datetime import datetime
from shutil import rmtree
from copy import deepcopy

from shapely.geometry import Polygon
import geopandas

from src.imagery_processing.get_bands import bands_2A
from src.imagery_processing.sentinel_api import data_check_2A, data_download_2A

# water indexes
from src.imagery_processing.indexes.cdom import cdom
from src.imagery_processing.indexes.turbidity import turbidity
from src.imagery_processing.indexes.doc import doc
from src.imagery_processing.indexes.chl_a import chl_a
from src.imagery_processing.indexes.cya import cya

# drought indexes
from src.imagery_processing.indexes.ndwi import ndwi
from src.imagery_processing.indexes.nmdi import nmdi
from src.imagery_processing.indexes.ndmi import ndmi
from src.imagery_processing.indexes.ndvi import ndvi
from src.imagery_processing.indexes.wdrvi import wdrvi
from src.imagery_processing.indexes.evi import evi

# clouds
from src.imagery_processing.detect_clouds import detect_clouds

# reproject
from src.imagery_processing.reproject import epsg3857

# merge
from src.imagery_processing.merge import merge_rasters

# DB
from src.db_client.db_client import DBClient

# mask
from src.imagery_processing.mask import masking, masking_aoi

from src.db_client.models.files import File

# around Boleslaw mining sites
POLYGON: Final = [
    [19.700705772907838, 50.412751801438958],
    [19.272261488161291, 50.514547586387039],
    [19.113125039541046, 50.303868968171855],
    [19.687175953389556, 50.145376796670575],
    [19.700705772907838, 50.412751801438958],
]

WATER_INDEXES: Final = {}
DROUGHT_INDEXES: Final = {
    "ndwi": [],
    "nmdi": [],
    "ndmi": [],
    "ndvi": [],
    "wdrvi": [],
    "evi": [],
}
ALL_INDEXES: Final = {**WATER_INDEXES, **DROUGHT_INDEXES}


def check_folder(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def delete_folder_with_all_files(folder: Path):
    rmtree(folder)


def run_boleslaw(
    sen_from: Union[datetime, None], sen_to: Union[datetime, None]
) -> None:
    # ------------------------------------------------------------------------------------ find new products
    products_df = data_check_2A(
        check_folder(Path.cwd().joinpath("data", "download")),
        Polygon(POLYGON),
        sen_from,
        sen_to,
        if_polygon_inside_image=True,
    )

    timestamp = products_df["generationdate"].mean()

    # ------------------------------------------------------------------------------------ download new satellite imagery
    if not products_df.empty:
        downloaded = data_download_2A(
            check_folder(Path.cwd().joinpath("data", "download")), products_df
        )

        indexes = deepcopy(ALL_INDEXES)

        output_folder = check_folder(Path.cwd().joinpath("data", "indexes_per_imagery"))
        detected_clouds = []
        output_folder_for_clouds = check_folder(
            Path.cwd().joinpath("data", "clouds_masks_per_imagery")
        )
        for folder in downloaded:
            bands = bands_2A(folder)

            # ------------------------------------------------------------------------------------ calculate indexes
            if "ndwi" in indexes.keys():
                indexes["ndwi"].append(
                    ndwi(
                        folder.name,
                        bands["b03_10m"],
                        bands["b08_10m"],
                        output_folder,
                    )
                )

            if "nmdi" in indexes.keys():
                indexes["nmdi"].append(
                    nmdi(
                        folder.name,
                        bands["b08_10m"],
                        bands["b11_20m"],
                        bands["b12_20m"],
                        output_folder,
                    )
                )

            if "ndmi" in indexes.keys():
                indexes["ndmi"].append(
                    ndmi(
                        folder.name,
                        bands["b08_10m"],
                        bands["b11_20m"],
                        output_folder,
                    )
                )

            if "ndvi" in indexes.keys():
                indexes["ndvi"].append(
                    ndvi(
                        folder.name,
                        bands["b04_10m"],
                        bands["b08_10m"],
                        output_folder,
                    )
                )

            if "wdrvi" in indexes.keys():
                indexes["wdrvi"].append(
                    wdrvi(
                        folder.name,
                        bands["b04_10m"],
                        bands["b08_10m"],
                        output_folder,
                    )
                )

            if "evi" in indexes.keys():
                indexes["evi"].append(
                    evi(
                        folder.name,
                        bands["b02_10m"],
                        bands["b04_10m"],
                        bands["b08_10m"],
                        output_folder,
                    )
                )

            # ------------------------------------------------------------------------------------ detect clouds
            detected_clouds.append(
                detect_clouds(
                    folder.name,
                    bands["cloud_classif"],
                    bands["cloud_prob"],
                    output_folder_for_clouds,
                )
            )

        # ------------------------------------------------------------------------------------ reproject to web mercator: EPSG 3857
        indexes_reproj = deepcopy(ALL_INDEXES)

        output_folder = check_folder(
            Path.cwd().joinpath("data", "indexes_per_imagery_reprojected")
        )

        for key in indexes.keys():
            for layer in indexes[key]:
                indexes_reproj[key].append(epsg3857(layer, output_folder))
        delete_folder_with_all_files(Path.cwd().joinpath("data", "indexes_per_imagery"))

        # ------------------------------------------------------------------------------------ merge all products for each index
        indexes_merged = deepcopy(ALL_INDEXES)
        output_folder = check_folder(Path.cwd().joinpath("data", "merged"))
        for key in indexes_merged.keys():
            indexes_merged[key].append(
                merge_rasters(
                    key
                    + f"_epoch{int(timestamp.timestamp())}_date{timestamp.strftime('%Y%m%d')}",
                    indexes_reproj[key],
                    output_folder,
                )
            )
        delete_folder_with_all_files(
            Path.cwd().joinpath("data", "indexes_per_imagery_reprojected")
        )

        # ------------------------------------------------------------------------------------ mask rasters with clouds
        masked_clouds = deepcopy(ALL_INDEXES)
        clouds = geopandas.read_file(detected_clouds[0])
        output_folder = check_folder(Path.cwd().joinpath("data", "merged_cloudsMasked"))

        for key in indexes_merged.keys():
            masked_clouds[key].append(
                masking(
                    layer=indexes_merged[key][0],
                    mask_name="clouds",
                    masking_geom=clouds.geometry,
                    output_folder=output_folder,
                    invert=True,
                )
            )
        delete_folder_with_all_files(Path.cwd().joinpath("data", "merged"))

        # ------------------------------------------------------------------------------------ mask rasters with AOI
        masked_aoi = deepcopy(ALL_INDEXES)
        aoi = geopandas.read_file(
            Path.cwd().joinpath(
                "src",
                "imagery_processing",
                "geoms_for_merging",
                "boleslaw.shp",
            )
        )
        output_folder = check_folder(
            Path.cwd().joinpath(
                "data",
                "final",
                f"epoch{int(timestamp.timestamp())}_date{timestamp.strftime('%Y%m%d')}",
            )
        )
        for key in masked_clouds.keys():
            masked_aoi[key].append(
                masking(
                    layer=masked_clouds[key][0],
                    mask_name="aoi",
                    masking_geom=aoi.geometry,
                    output_folder=output_folder,
                )
            )
        delete_folder_with_all_files(Path.cwd().joinpath("data", "merged_cloudsMasked"))

        # ------------------------------------------------------------------------------------ create SHP with clouds
        clouds_aoiClipped = clouds.clip(aoi)
        clouds_aoiClipped.to_file(
            output_folder.joinpath(
                f"clouds_epoch{int(timestamp.timestamp())}_date{timestamp.strftime('%Y%m%d')}"
            )
        )
