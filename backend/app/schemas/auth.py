from pydantic import BaseModel, Field
from typing import Optional

class LoginRequest(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="password")

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
