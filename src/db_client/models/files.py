from pydantic import BaseModel
from pathlib import Path
from typing import Optional

import datetime as dt


class File(BaseModel):
    file_id: Optional[int] = None
    order_id: int
    geom_id: int
    path: Path
    wq_index: str
    file_extension: str
    date: dt.datetime

    def make_path_relative(self):
        if not Path.cwd().name == "waterpix-backend":
            raise ValueError("Your working directory is not waterpix-backend folder")
        else:
            self.path = self.path.relative_to(Path.cwd())

        return self

    def make_path_absolute(self):
        if not Path.cwd().name == "waterpix-backend":
            raise ValueError("Your working directory is not waterpix-backend folder")
        else:
            self.path = Path.cwd().joinpath(self.path)

        return self
