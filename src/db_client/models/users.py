from pydantic import BaseModel


class UserNoPassword(BaseModel):
    user_id: int
    username: str
    email: str
    phone: str
    disabled: bool


class User(UserNoPassword):
    password: str
