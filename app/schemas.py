from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserPublic(BaseModel):
    id: int
    username: str
    email: str | None = None


class MeRead(BaseModel):
    id: int
    username: str | None = None
    name: str
    email: str
    picture: str | None = None
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)


class UsernameUpdate(BaseModel):
    username: str = Field(min_length=3, max_length=15)

    @field_validator("username")
    @classmethod
    def strip_and_validate_username(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Username is required.")

        if not re.fullmatch(r"[A-Za-z0-9_]+", cleaned):
            raise ValueError("Username can only contain letters, numbers, and underscores.")

        return cleaned


class ProfessorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    photo_url: str | None = Field(default=None, max_length=1024)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Professor name cannot be empty.")
        return cleaned

    @field_validator("department")
    @classmethod
    def strip_department(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("photo_url")
    @classmethod
    def strip_and_validate_photo_url(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        if not cleaned:
            return None

        if not (
            cleaned.startswith("http://")
            or cleaned.startswith("https://")
            or cleaned.startswith("/")
        ):
            raise ValueError("Photo URL must start with http://, https://, or /.")

        return cleaned


class ProfessorRead(BaseModel):
    id: int
    name: str
    department: str | None = None
    photo_url: str | None = None
    average_rating: float | None = None
    review_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    review_text: str | None = Field(default=None, max_length=1500)

    @field_validator("review_text")
    @classmethod
    def strip_review_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ReviewRead(BaseModel):
    id: int
    rating: int
    review_text: str | None = None
    created_at: datetime
    is_deleted: bool = False
    can_delete: bool = False
    reviewer: UserPublic

    model_config = ConfigDict(from_attributes=True)


class ProfessorDetails(ProfessorRead):
    reviews: list[ReviewRead] = []
