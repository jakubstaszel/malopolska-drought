from .task import run
import argparse
from datetime import datetime


def cli() -> None:
    parser = argparse.ArgumentParser(description="Process new satellite imagery.")
    parser.add_argument(
        "--from",
        "-f",
        action="store",
        required=False,
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        dest="sentinel_from",
    )
    parser.add_argument(
        "--to",
        "-t",
        action="store",
        required=False,
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        dest="sentinel_to",
    )

    args = parser.parse_args()

    run(args.sentinel_from, args.sentinel_to)
