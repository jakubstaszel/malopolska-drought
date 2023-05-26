from typing import Final, Union, List
from pathlib import Path
from datetime import datetime
from shutil import rmtree
from copy import deepcopy

from shapely.geometry import Polygon
import geopandas as gpd
import pandas as pd

from src.imagery_processing.get_bands import bands_2A
from src.imagery_processing.sentinel_api import data_check, data_download

# water indexes
from src.imagery_processing.indexes.cdom import cdom
from src.imagery_processing.indexes.turbidity import turbidity
from src.imagery_processing.indexes.doc import doc
from src.imagery_processing.indexes.chl_a import chl_a
from src.imagery_processing.indexes.cya import cya

# drought indexes
from src.imagery_processing.indexes.ndwi_v1 import ndwi1
from src.imagery_processing.indexes.ndwi_v2 import ndwi2
from src.imagery_processing.indexes.nmdi import nmdi
from src.imagery_processing.indexes.ndmi import ndmi
from src.imagery_processing.indexes.ndvi import ndvi
from src.imagery_processing.indexes.wdrvi import wdrvi
from src.imagery_processing.indexes.evi import evi
from src.imagery_processing.indexes.msavi2 import msavi2
from src.imagery_processing.indexes.msi import msi

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

# Roznowskie lake in Małopolska
POLYGON: Final = [
    [19.091504869414848, 49.971660199797157],
    [19.661907963059775, 49.402238702643217],
    [19.790343096728236, 49.195316426684997],
    [20.08121089944791, 49.182972223535046],
    [20.300306127470606, 49.370271832411788],
    [20.708276552064262, 49.385028356961811],
    [20.950036803675232, 49.29149552756877],
    [21.274902141777716, 49.429271349061253],
    [21.422224795103205, 49.436641305065848],
    [21.206907071012097, 50.354001512810328],
    [20.776271622829938, 50.291294753773286],
    [20.655391497024198, 50.192242879005676],
    [20.417408749344588, 50.201915538359515],
    [20.23986606456765, 50.495990864248427],
    [19.975440789368065, 50.508004295927549],
    [19.507030301871396, 50.406996472399328],
    [19.091504869414848, 49.971660199797157],
]

WATER_INDEXES: Final = {}
DROUGHT_INDEXES: Final = {
    "ndwi1": [],
    "ndwi2": [],
    "nmdi": [],
    "ndmi": [],
    "ndvi": [],
    "wdrvi": [],
    "evi": [],
    "msavi2": [],
    "msi": [],
}
ALL_INDEXES: Final = {**WATER_INDEXES, **DROUGHT_INDEXES}


def check_folder(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def delete_folder_with_all_files(folder: Path):
    rmtree(folder)


def run_malopolska(
    sen_from: Union[datetime, None], sen_to: Union[datetime, None]
) -> None:
    """
    This task supports only AOIs that are inside one imagery.
    """
    # ------------------------------------------------------------------------------------ find new products
    sate = "S2A"
    identifier = {
        sate + "*T34UCV*",
        sate + "*T34UCA*",
        sate + "*T34UEA*",
        sate + "*T34UDV*",
        sate + "*T34UDA*",
        sate + "*T34UEV*",
    }
    # identifier = "*34UDA*"
    products_df = data_check(
        check_folder(Path.cwd().joinpath("data", "download")),
        Polygon(POLYGON),
        sen_from,
        sen_to,
        identifier=identifier,
        check_LTA=True,
        processing_level="Level-1C"
    )

    if len(products_df) != 6:
        raise ValueError("Time range is too wide or too narrow")
    print(len(products_df))

    # ------------------------------------------------------------------------------------ download new satellite imagery
    if not products_df is None:
        # imagery before 2021 have no generationdate field
        if "generationdate" not in products_df:
            products_df["generationdate"] = products_df["filename"].apply(
                lambda x: datetime.strptime(
                    x.split("_")[-1].split(".")[0], "%Y%m%dT%H%M%S"
                )
            )
        timestamp = products_df["generationdate"].mean()

        downloaded = data_download(
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
            if "cdom" in indexes.keys():
                indexes["cdom"].append(
                    cdom(folder.name, bands["b03_10m"], bands["b04_10m"], output_folder)
                )

            if "turb" in indexes.keys():
                indexes["turb"].append(
                    turbidity(
                        folder.name, bands["b03_60m"], bands["b01_60m"], output_folder
                    )
                )

            if "doc" in indexes.keys():
                indexes["doc"].append(
                    doc(folder.name, bands["b03_10m"], bands["b04_10m"], output_folder)
                )

            if "chla" in indexes.keys():
                indexes["chla"].append(
                    chl_a(
                        folder.name, bands["b03_60m"], bands["b01_60m"], output_folder
                    )
                )

            if "cya" in indexes.keys():
                indexes["cya"].append(
                    cya(
                        folder.name,
                        bands["b03_10m"],
                        bands["b04_10m"],
                        bands["b02_10m"],
                        output_folder,
                    )
                )

            if "ndwi1" in indexes.keys():
                indexes["ndwi1"].append(
                    ndwi1(
                        folder.name, bands["b8a_20m"], bands["b12_20m"], output_folder
                    )
                )

            if "ndwi2" in indexes.keys():
                indexes["ndwi2"].append(
                    ndwi2(
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

            if "msavi2" in indexes.keys():
                indexes["msavi2"].append(
                    msavi2(
                        folder.name,
                        bands["b04_10m"],
                        bands["b08_10m"],
                        output_folder,
                    )
                )

            if "msi" in indexes.keys():
                indexes["msi"].append(
                    msi(
                        folder.name,
                        bands["b8a_20m"],
                        bands["b11_20m"],
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
        clouds = []
        for file in detected_clouds:
            clouds.append(gpd.read_file(file))
        clouds = pd.concat(clouds, ignore_index=True)
        clouds = clouds.dissolve().explode(ignore_index=True)

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
        aoi = gpd.read_file(
            Path.cwd().joinpath(
                "src",
                "imagery_processing",
                "geoms_for_merging",
                "malopolska.shp",
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
