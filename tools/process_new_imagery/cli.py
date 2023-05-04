from .task import run
from .task_boleslaw import run_boleslaw
from .task_check_clouds_coverage import run_check_clouds_coverage
import argparse
from datetime import datetime


def cli() -> None:
    parser = argparse.ArgumentParser(description="Process new satellite imagery.")

    parser.add_argument(
        "--task-name",
        "-tn",
        action="store",
        choices=["task", "boleslaw", "clouds"],
        required=True,
        type=str,
        dest="task_name",
    )
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

    if args.task_name == "task":
        run(args.sentinel_from, args.sentinel_to)
    elif args.task_name == "boleslaw":
        run_boleslaw(args.sentinel_from, args.sentinel_to)
    elif args.task_name == "clouds":
        run_check_clouds_coverage(args.sentinel_from, args.sentinel_to)
