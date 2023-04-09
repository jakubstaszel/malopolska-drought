from fastapi import APIRouter, Depends

from ...db_client.models.users import UserNoPassword
from ..models.authentication import get_current_active_user

router = APIRouter()


@router.get("/users/me/", response_model=UserNoPassword, tags=["users"])
async def read_users_me(
    current_user: UserNoPassword = Depends(get_current_active_user),
):
    return current_user
