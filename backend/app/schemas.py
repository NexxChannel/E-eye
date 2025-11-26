from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserOut(UserBase):
    id: int
    isActive: bool
    subscriptionLevel: str

    model_config = ConfigDict(from_attributes=True)


class UserLogin(UserBase):
    password: str = Field(min_length=8)
    # role: str

class Token(BaseModel):
    accessToken: str
    tokenType: str

class ProjectBase(BaseModel):
    name: str

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int
    createdAt: datetime
    ownerId: int

    model_config = ConfigDict(from_attributes=True)