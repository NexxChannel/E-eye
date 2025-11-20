from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    isActive: bool
    subscriptionLevel: str

    model_config = ConfigDict(from_attributes=True)


class UserLogin(UserBase):
    password: str
    # role: str

class Token(BaseModel):
    accessToken: str
    tokenType: str