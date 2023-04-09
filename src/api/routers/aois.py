from typing import List

from fastapi import APIRouter, Depends
import geopandas as gpd

from ...db_client.models.users import UserNoPassword
from ...db_client.db_client import DBClient
from ..models.authentication import get_current_active_user

router = APIRouter()


@router.get("/aois/mine/", tags=["aois"])
async def read_mine_aois(
    current_user: UserNoPassword = Depends(get_current_active_user),
):
    # credentials_exception = HTTPException(
    #     status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    # )
    db = DBClient()
    aois = db.get_all_aois_for_user(current_user.user_id)

    if len(aois) > 0:
        aois = [aoi.dict() for aoi in aois]
        aois = gpd.GeoDataFrame(aois)
        print(aois.to_json())

    return aois.to_json()
