from pathlib import Path
import os


def bands_2A(folder: Path) -> dict:
    """
    Gets directories to different bands of the 2A product.
    Returns dictionary with directories to the bands.
    """
    # getting into exact imagery folder
    home = Path.cwd()
    os.chdir(folder)

    # finding directories for needed bands (only those needed for calculated indexes)
    bands = {
        "b02_10m": None,
        "b03_10m": None,
        "b04_10m": None,
        "b08_10m": None,
        "b8a_20m": None,
        "b11_20m": None,
        "b12_20m": None,
        "b01_60m": None,
        "b03_60m": None,
        "cloud_classif": None,
        "cloud_prob": None,
    }

    print("Getting bands directories for", folder.name)
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            # finding different bands and resolution
            if file.endswith("_B04_10m.jp2"):
                bands["b04_10m"] = Path(root).joinpath(file)
            if file.endswith("_B03_10m.jp2"):
                bands["b03_10m"] = Path(root).joinpath(file)
            if file.endswith("_B02_10m.jp2"):
                bands["b02_10m"] = Path(root).joinpath(file)
            if file.endswith("_B08_10m.jp2"):
                bands["b08_10m"] = Path(root).joinpath(file)
            if file.endswith("_B8A_20m.jp2"):
                bands["b8a_20m"] = Path(root).joinpath(file)
            if file.endswith("_B11_20m.jp2"):
                bands["b11_20m"] = Path(root).joinpath(file)
            if file.endswith("_B12_20m.jp2"):
                bands["b12_20m"] = Path(root).joinpath(file)
            if file.endswith("_B01_60m.jp2"):
                bands["b01_60m"] = Path(root).joinpath(file)
            if file.endswith("_B03_60m.jp2"):
                bands["b03_60m"] = Path(root).joinpath(file)

            # bands for cloud detection
            if file.endswith("MSK_CLASSI_B00.jp2"):
                bands["cloud_classif"] = Path(root).joinpath(file)
            if file.endswith("MSK_CLDPRB_20m.jp2"):
                bands["cloud_prob"] = Path(root).joinpath(file)
    os.chdir(home)
    return bands
