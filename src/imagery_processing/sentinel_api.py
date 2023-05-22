import os
from typing import Union, List, Tuple
from settings import OAH_LOGIN, OAH_PASSWORD
import datetime as dt
from pathlib import Path
import pandas as pd

from shapely.geometry import Polygon
import geopandas

from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt, make_path_filter
from sentinelsat.exceptions import InvalidChecksumError, ServerError
from requests.exceptions import HTTPError
import zipfile


def _update_lastRefresh_file(datetime: dt.datetime) -> None:
    fileRefresh = open("lastRefresh.txt", "w")
    fileRefresh.write(str(datetime))
    fileRefresh.close()


def check_and_trigger_offline_retrieval(products_df) -> bool:
    api = SentinelAPI(
        OAH_LOGIN[0], OAH_PASSWORD[0], "https://scihub.copernicus.eu/dhus"
    )

    is_any_offline = False
    i = 0
    api_idx = 0
    login = OAH_LOGIN[1:]
    passw = OAH_PASSWORD[1:]

    switch_credentials_idx = []
    for cred in login:
        idx = 20
        switch_credentials_idx.append(idx)
        idx = idx + 20

    for product in products_df.iterrows():
        is_online = api.is_online(product[1]["uuid"])
        if not is_online:
            if i in switch_credentials_idx:
                api = SentinelAPI(
                    login[api_idx], passw[api_idx], "https://scihub.copernicus.eu/dhus"
                )
                api_idx = api_idx + 1
            i = i + 1
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
    identifier: str = "*",
    if_whole_polygon_inside_image: bool = False,
    clouds_coverage_percentage: Tuple = (0, 100),
    check_LTA: bool = False,
) -> pd.DataFrame:
    """
    Calls Sentinel API to find new 2A products.
    Return dataframe with products found.

    Parameters
    ----------
    identifier: str, optional, default to "*" meaning no filter on this field
        This parameter is used when you want to filter results by some kind of
        name pattern. As an example, if you want to download imagery for Sentinel 2,
        but only from 2B and for 2 locations you can use {"S2B*T34UDA*", "S2B*T34UEA*"}.

    if_whole_polygon_inside_image: bool, default to False, if you switch to True,
        only images which contains the whole polygon on the image will be returned.

    check_LTA: bool, default False, if True, it is checking if any product is in
        Long Term Archive, if yes, then it is triggering retrieval. You will
        have to wait a few hours for it to be ready to be downloaded.
    """
    home = Path.cwd()
    os.chdir(folder)

    api = SentinelAPI(
        OAH_LOGIN[0], OAH_PASSWORD[0], "https://scihub.copernicus.eu/dhus"
    )
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

    if if_whole_polygon_inside_image == True:
        area_relation = "Contains"
    else:
        area_relation = "Intersects"  # - it is by default

    products = api.query(
        footprint,
        date=date,
        platformname="Sentinel-2",
        processinglevel="Level-2A",
        identifier=identifier,
        cloudcoverpercentage=clouds_coverage_percentage,
        area_relation=area_relation,
    )

    products_df = api.to_dataframe(products)

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

        if check_LTA:
            if check_and_trigger_offline_retrieval(products_df):
                return None

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
    api = SentinelAPI(
        OAH_LOGIN[0], OAH_PASSWORD[0], "https://scihub.copernicus.eu/dhus"
    )

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

    except (InvalidChecksumError, HTTPError, ServerError) as e:
        print(e)
        os.chdir(home)
        print("Trying one more time: ")
        data_download_2A(folder, products_df)


def data_download_clouds_bands(folder: Path, products_df) -> List[Path]:
    home = Path.cwd()
    os.chdir(folder)
    api = SentinelAPI(
        OAH_LOGIN[0], OAH_PASSWORD[0], "https://scihub.copernicus.eu/dhus"
    )
    try:
        downloaded = []
        for product in products_df.iterrows():
            # product = products_df
            print(
                "Now downloading clouds bands: ", product[1]["filename"]
            )  # filename of the product
            path_filter = make_path_filter("*MSK_CL[DA][PS][RS][BI]_[2B]0[m0].jp2")
            api.download_all(
                [product[1]["uuid"]], nodefilter=path_filter
            )  # download the product using uuid

            downloaded.append(folder.joinpath(product[1]["filename"]))

        os.chdir(home)
        return downloaded

    except (InvalidChecksumError, HTTPError, ServerError) as e:
        print(e)
        os.chdir(home)
        print("Trying one more time: ")
        data_download_clouds_bands(folder, products_df)
