from typing import Final, Union, List
from pathlib import Path
from datetime import datetime
from shutil import rmtree

from shapely.geometry import Polygon

from src.imagery_processing.get_bands import bands_2A
from src.imagery_processing.sentinel_api import data_check_2A, data_download_2A

# indexes
from src.imagery_processing.indexes.cdom import cdom
from src.imagery_processing.indexes.turbidity import turbidity
from src.imagery_processing.indexes.doc import doc
from src.imagery_processing.indexes.chl_a import chl_a
from src.imagery_processing.indexes.cya import cya

# clouds
from src.imagery_processing.detect_clouds import detect_clouds

# reproject
from src.imagery_processing.reproject import epsg3857

# merge
from src.imagery_processing.merge import merge_rasters

# DB
from src.db_client.db_client import DBClient

# mask
from src.imagery_processing.mask import masking

from src.db_client.models.files import File

# around Malopolska Region in Poland
POLYGON: Final = [
    [19.422527512826534, 50.530129894672505],
    [18.968967183751467, 50.004954776796112],
    [19.955659829458632, 48.988422635755057],
    [21.511292186198563, 49.432036466385497],
    [21.276554822905325, 50.480397402449363],
    [20.532556739247099, 50.293403231690341],
    [20.170504195862613, 50.635562778185566],
    [20.170504195862613, 50.635562778185566],
    [19.422527512826534, 50.530129894672505],
]


def check_folder(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def delete_folder_with_all_files(folder: Path):
    rmtree(folder)


def run(sen_from: Union[datetime, None], sen_to: Union[datetime, None]) -> None:
    # find new products
    products_df = data_check_2A(
        check_folder(Path.cwd().joinpath("data", "download")),
        Polygon(POLYGON),
        sen_from,
        sen_to,
    )

    # download new satellite imagery
    if not products_df.empty:
        downloaded = data_download_2A(
            check_folder(Path.cwd().joinpath("data", "download")), products_df
        )

        indexes = {"cdom": [], "turb": [], "doc": [], "chla": [], "cya": []}

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
        indexes_reproj = {"cdom": [], "turb": [], "doc": [], "chla": [], "cya": []}

        output_folder = check_folder(
            Path.cwd().joinpath("data", "indexes_per_imagery_reprojected")
        )
        for key in indexes.keys():
            for layer in indexes[key]:
                indexes_reproj[key].append(epsg3857(layer, output_folder))
        delete_folder_with_all_files(Path.cwd().joinpath("data", "indexes_per_imagery"))

        # merge all products for each index
        indexes_merged = {"cdom": [], "turb": [], "doc": [], "chla": [], "cya": []}
        output_folder = check_folder(Path.cwd().joinpath("data", "merged"))
        for key in indexes_merged.keys():
            indexes_merged[key].append(
                merge_rasters(key, indexes_reproj[key], output_folder)
            )
        delete_folder_with_all_files(
            Path.cwd().joinpath("data", "indexes_per_imagery_reprojected")
        )

        # mask rasters with AOIs
        db = DBClient()
        for aoi in db.get_all_aois():
            for key in indexes_merged.keys():
                layer_file = masking(
                    layer=indexes_merged[key][0],
                    maskingGeom=aoi,
                    output_folder=Path.cwd().joinpath(
                        "data", "final", str(aoi.order_id), str(aoi.geom_id)
                    ),
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
                            date=datetime.now(),
                        )
                    )
