import os
from typing import Union, List
from settings import OAH_LOGIN, OAH_PASSWORD
import datetime as dt
from pathlib import Path
import pandas as pd

from shapely.geometry import Polygon
import geopandas

from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt, make_path_filter
from sentinelsat.exceptions import InvalidChecksumError
from requests.exceptions import HTTPError
import zipfile


def _update_lastRefresh_file(datetime: dt.datetime) -> None:
    fileRefresh = open("lastRefresh.txt", "w")
    fileRefresh.write(str(datetime))
    fileRefresh.close()


def _any_product_offline(api, products_df) -> bool:
    is_any_offline = False
    for product in products_df.iterrows():
        is_online = api.is_online(product[1]["uuid"])
        if not is_online:
            is_any_offline = True
            api.trigger_offline_retrieval(product[1]["uuid"])
            print(
                f"    {product[1]['filename']} is offline, triggered retrieval from LTA"
            )

    if is_any_offline:
        return True
    else:
        return False


def data_check_2A(
    folder: Path,
    polygon: Polygon,
    sen_from: Union[dt.datetime, None],
    sen_to: Union[dt.datetime, None],
    if_polygon_inside_image: bool = False,
) -> pd.DataFrame:
    """
    Calls Sentinel API to find new 2A products.
    Return dataframe with products found.
    """
    home = Path.cwd()
    os.chdir(folder)

    api = SentinelAPI(OAH_LOGIN, OAH_PASSWORD, "https://scihub.copernicus.eu/dhus")
    footprint = geopandas.GeoSeries([polygon]).to_wkt()[0]

    if sen_from and sen_to:
        sen_to = sen_to + dt.timedelta(hours=23, minutes=59, seconds=59)
        date = (sen_from, sen_to)
        print(f"Searching for satellite imagery from {sen_from} to {sen_to}")
    elif Path.cwd().joinpath("lastRefresh.txt").is_file():
        lastRefresh = dt.datetime.strptime(
            open("lastRefresh.txt", "r").read(), "%Y-%m-%d %H:%M:%S.%f"
        )
        date = (lastRefresh, dt.datetime.now())
        print(
            f"Searching for satellite imagery from {lastRefresh} to {dt.datetime.now()}"
        )
    else:
        date = (dt.datetime.now() - dt.timedelta(days=4), dt.datetime.now())
        print(
            f"Searching for satellite imagery from {dt.datetime.now() - dt.timedelta(days=4)} to {dt.datetime.now()}"
        )

    if if_polygon_inside_image == True:
        area_relation = "Contains"
    else:
        area_relation = "Intersects"  # - it is by default

    products = api.query(
        footprint,
        date=date,
        platformname="Sentinel-2",
        processinglevel="Level-2A",
        cloudcoverpercentage=(0, 100),
        area_relation=area_relation,
    )

    products_df = api.to_dataframe(products)

    if _any_product_offline(api, products_df):
        return None

    if products_df.empty:
        print("    No new products found")
        # update the datetime of last refresh
        _update_lastRefresh_file(dt.datetime.now())
        return None
    else:
        print("Products found: ")
        avgClouds = 0.0
        for product in products_df.iterrows():
            print(
                "Found: ",
                product[1]["filename"],
                "   clouds:",
                product[1]["cloudcoverpercentage"],
            )
            avgClouds += product[1]["cloudcoverpercentage"]
        avgClouds = avgClouds / len(products_df)
        print("Avg clouds coverage: ", avgClouds)

    os.chdir(home)
    return products_df


def data_download_2A(folder: Path, products_df) -> List[Path]:
    """
    Downloads and unzips products found.
    Reguires data returned from dataCheck() function and lastRefresh.txt file in HOMEdir.
    Returns nothing.
    """
    home = Path.cwd()
    os.chdir(folder)
    api = SentinelAPI(OAH_LOGIN, OAH_PASSWORD, "https://scihub.copernicus.eu/dhus")

    try:
        downloaded = []
        for product in products_df.iterrows():
            # product = products_df
            print(
                "Now downloading: ", product[1]["filename"]
            )  # filename of the product
            api.download(product[1]["uuid"])  # download the product using uuid
            odata = api.get_product_odata(product[1]["uuid"], full=True)
            with zipfile.ZipFile(odata["title"] + ".zip", "r") as zip_ref:
                zip_ref.extractall()
                print("    Zipped file extracted to", product[1]["filename"], "folder")

            downloaded.append(folder.joinpath(product[1]["filename"]))

        os.chdir(home)
        return downloaded

    except (InvalidChecksumError, HTTPError) as e:
        print(e)
        os.chdir(home)
        print("Trying one more time: ")
        data_download_2A(folder, products_df)


def data_download_clouds_bands(folder: Path, products_df) -> List[Path]:
    home = Path.cwd()
    os.chdir(folder)
    api = SentinelAPI(OAH_LOGIN, OAH_PASSWORD, "https://scihub.copernicus.eu/dhus")
    try:
        downloaded = []
        for product in products_df.iterrows():
            # product = products_df
            print(
                "Now downloading clouds bands: ", product[1]["filename"]
            )  # filename of the product
            path_filter = make_path_filter("*MSK_CLASSI_B00.jp2")
            api.download(
                product[1]["uuid"], nodefilter=path_filter
            )  # download the product using uuid
            path_filter = make_path_filter("*MSK_CLDPRB_20m.jp2")
            api.download(
                product[1]["uuid"], nodefilter=path_filter
            )  # download the product using uuid

            downloaded.append(folder.joinpath(product[1]["filename"]))

        os.chdir(home)
        return downloaded

    except (InvalidChecksumError, HTTPError) as e:
        print(e)
        os.chdir(home)
        print("Trying one more time: ")
        data_download_clouds_bands(folder, products_df)
