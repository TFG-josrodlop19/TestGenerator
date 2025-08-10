from enum import Enum

from pydantic import BaseModel, Field, validator

from .validators import validate_password

EMAIL_PATTERN = r"^[\w\-.]+@([\w-]+\.)+[\w-]{2,4}$"

class User(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)
    password: str = Field(...)

    @validator("password")
    def validate_password(cls, value):
        return validate_password(value)


class LoginRequest(BaseModel):
    email: str = Field(
        pattern=EMAIL_PATTERN
    )
    password: str = Field(...)

    @validator("password")
    def validate_password(cls, value):
        return validate_password(value)


class AccountExistsRequest(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)


class VerifyAccessTokenRequest(BaseModel):
    access_token: str | None


class ChangePasswordRequest(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)
    old_password: str = Field(...)
    new_password: str = Field(...)

    @validator("new_password", "old_password")
    def validate_password(cls, value):
        return validate_password(value)


class StatementsGroup(str, Enum):
    no_grouping = "no_grouping"
    supplier = "supplier"
    cwe_type = "cwe_type"
    attack_vector_av = "attack_vector_av"
    attack_vector_ac = "attack_vector_ac"
    attack_vector_au = "attack_vector_au"
    attack_vector_c = "attack_vector_c"
    attack_vector_i = "attack_vector_i"
    attack_vector_a = "attack_vector_a"
    reachable_code = "reachable_code"


class GenerateVEXRequest(BaseModel):
    owner: str = Field(min_lengt=1)
    name: str = Field(min_lengt=1)
    sbom_path: str = Field(min_lengt=1)
    statements_group: StatementsGroup
    user_id: str
