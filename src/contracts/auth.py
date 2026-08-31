from __future__ import annotations

from pydantic import BaseModel


class Credentials(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
