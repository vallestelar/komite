from typing import List, Optional

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class CompanyLoginResponse(BaseModel):
    id: str
    name: str


class CondominiumLoginResponse(BaseModel):
    id: str
    name: str
    role: str
    role_name: str
    unit_id: Optional[str] = None
    unit_identifier: Optional[str] = None


class UserLoginResponse(BaseModel):
    id: str
    email: str
    full_name: str
    company_profile: Optional[str] = None
    organization_position: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserLoginResponse
    company: Optional[CompanyLoginResponse] = None
    condominiums: List[CondominiumLoginResponse]


class MeResponse(TokenResponse):
    pass
