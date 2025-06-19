import uuid
from pydantic import BaseModel, EmailStr, Field, ValidationError, model_validator, ConfigDict

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserDAO(BaseModel):
    username: str
    email: EmailStr

class UserLogin(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="Optional when e-mail is supplied",
    )
    email: EmailStr | None = Field(
        default=None,
        description="Optional when username is supplied",
    )
    password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def at_least_one_identifier(cls, values):
        if not (values.username or values.email):
            raise ValueError("Provide either username or e-mail.")
        return values


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)   
