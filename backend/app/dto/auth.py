from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    status: str = "ok"


class MeResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
