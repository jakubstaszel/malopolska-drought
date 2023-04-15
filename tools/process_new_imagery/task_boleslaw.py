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

WATER_INDEXES: Final = {"cdom": [], "turb": [], "doc": [], "chla": [], "cya": []}
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
    # find new products
    products_df = data_check_2A(
        check_folder(Path.cwd().joinpath("data", "download")),
        Polygon(POLYGON),
        sen_from,
        sen_to,
        if_polygon_inside_image=True,
    )

    timestamp = products_df["generationdate"].mean()

    # # download new satellite imagery
    if not products_df.empty:
        downloaded = data_download_2A(
            check_folder(Path.cwd().joinpath("data", "download")), products_df
        )

        indexes = deepcopy(ALL_INDEXES)

        output_folder = check_folder(Path.cwd().joinpath("data", "indexes_per_imagery"))
        output_folder_for_clouds = check_folder(
            Path.cwd().joinpath("data", "clouds_masks_per_imagery")
        )
        for folder in downloaded:
            bands = bands_2A(folder)

            # calculate indexes
            indexes["cdom"].append(
                cdom(folder.name, bands["b03_10m"], bands["b04_10m"], output_folder)
            )
            indexes["turb"].append(
                turbidity(
                    folder.name, bands["b03_60m"], bands["b01_60m"], output_folder
                )
            )
            indexes["doc"].append(
                doc(folder.name, bands["b03_10m"], bands["b04_10m"], output_folder)
            )
            indexes["chla"].append(
                chl_a(folder.name, bands["b03_60m"], bands["b01_60m"], output_folder)
            )
            indexes["cya"].append(
                cya(
                    folder.name,
                    bands["b03_10m"],
                    bands["b04_10m"],
                    bands["b02_10m"],
                    output_folder,
                )
            )

            indexes["ndwi"].append(
                ndwi(
                    folder.name,
                    bands["b03_10m"],
                    bands["b08_10m"],
                    output_folder,
                )
            )

            indexes["nmdi"].append(
                nmdi(
                    folder.name,
                    bands["b08_10m"],
                    bands["b11_20m"],
                    bands["b12_20m"],
                    output_folder,
                )
            )

            indexes["ndmi"].append(
                ndmi(
                    folder.name,
                    bands["b08_10m"],
                    bands["b11_20m"],
                    output_folder,
                )
            )

            indexes["ndvi"].append(
                ndvi(
                    folder.name,
                    bands["b04_10m"],
                    bands["b08_10m"],
                    output_folder,
                )
            )

            indexes["wdrvi"].append(
                wdrvi(
                    folder.name,
                    bands["b04_10m"],
                    bands["b08_10m"],
                    output_folder,
                )
            )

            indexes["evi"].append(
                evi(
                    folder.name,
                    bands["b02_10m"],
                    bands["b04_10m"],
                    bands["b08_10m"],
                    output_folder,
                )
            )

            # detect clouds
            detected_clouds = []
            detected_clouds.append(
                detect_clouds(
                    folder.name,
                    bands["cloud_classif"],
                    bands["cloud_prob"],
                    output_folder_for_clouds,
                )
            )

        # reproject to web mercator: EPSG 3857
        indexes_reproj = deepcopy(ALL_INDEXES)

        output_folder = check_folder(
            Path.cwd().joinpath("data", "indexes_per_imagery_reprojected")
        )

        for key in indexes.keys():
            for layer in indexes[key]:
                indexes_reproj[key].append(epsg3857(layer, output_folder))
        delete_folder_with_all_files(Path.cwd().joinpath("data", "indexes_per_imagery"))

        # merge all products for each index
        indexes_merged = deepcopy(ALL_INDEXES)
        output_folder = check_folder(Path.cwd().joinpath("data", "merged"))
        for key in indexes_merged.keys():
            indexes_merged[key].append(
                merge_rasters(key, indexes_reproj[key], output_folder)
            )
        delete_folder_with_all_files(
            Path.cwd().joinpath("data", "indexes_per_imagery_reprojected")
        )

        # drought indexes need additional masking with water bodies
        drought_indexes = deepcopy(DROUGHT_INDEXES)
        output_folder = check_folder(
            Path.cwd().joinpath("data", "merged_waterBodiesMasked")
        )
        water_bodies = geopandas.read_file(
            Path.cwd().joinpath(
                "src",
                "imagery_processing",
                "geoms_for_merging",
                "waterBodies_malopolska.shp",
            )
        )
        for key in drought_indexes.keys():
            indexes_merged[key] = [
                masking(
                    layer=indexes_merged[key][0],
                    mask_name="waterBodies",
                    masking_geom=water_bodies.geometry,
                    output_folder=output_folder,
                    invert=True,
                )
            ]

        # mask rasters with AOIs
        db = DBClient()
        for aoi in db.get_all_aois():
            for key in indexes_merged.keys():
                output_folder = check_folder(
                    Path.cwd().joinpath(
                        "data",
                        "final",
                        str(aoi.order_id),
                        str(aoi.geom_id),
                        str(int(timestamp.timestamp())),
                    )
                )
                layer_file = masking_aoi(
                    layer=indexes_merged[key][0],
                    masking_geom=aoi,
                    epoch=str(int(timestamp.timestamp())),
                    output_folder=output_folder,
                )

                # add produced TIF files to DB
                if layer_file:
                    db.insert_file(
                        File(
                            order_id=aoi.order_id,
                            geom_id=aoi.geom_id,
                            path=layer_file,
                            wq_index=key,
                            file_extension="TIF",
                            date=timestamp,
                        )
                    )
