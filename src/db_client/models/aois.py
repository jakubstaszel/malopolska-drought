from pydantic import BaseModel
from typing import Optional

from shapely.geometry import Polygon
from shapely import wkt
import geopandas as gpd


class AOI(BaseModel):
    geom_id: Optional[int]
    order_id: int
    geometry: Polygon
    epsg: int

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, geom_id: int, order_id: int, geometry: str, epsg: int):
        super().__init__(
            geom_id=geom_id, order_id=order_id, geometry=wkt.loads(geometry), epsg=epsg
        )
