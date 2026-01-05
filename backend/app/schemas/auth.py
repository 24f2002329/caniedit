from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, constr


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: constr(min_length=8)  # type: ignore[valid-type]


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OTPRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class OTPVerify(BaseModel):
    email: EmailStr
    code: constr(min_length=4, max_length=8)  # type: ignore[valid-type]
    full_name: Optional[str] = None


class UsageRead(BaseModel):
    scope: str
    limit: int
    used: int


class UserRead(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: constr(strip_whitespace=True, min_length=1, max_length=120)  # type: ignore[valid-type]

    class Config:
        extra = "forbid"
