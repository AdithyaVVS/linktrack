from datetime import date, datetime, timezone
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator

from app.config import settings

MAX_URL_LENGTH = 2048


class LinkCreate(BaseModel):
    original_url: HttpUrl
    expires_at: datetime | None = None

    @field_validator("original_url")
    @classmethod
    def url_must_be_reasonable(cls, value):
        text = str(value)
        if len(text) > MAX_URL_LENGTH:
            raise ValueError(f"URL must be at most {MAX_URL_LENGTH} characters")
        own_host = urlparse(settings.base_url).hostname
        if own_host and (value.host or "").lower() == own_host.lower():
            raise ValueError("Cannot shorten a link that points to LinkTrack itself")
        return value

    @field_validator("expires_at")
    @classmethod
    def expiry_must_be_future(cls, value):
        if value is None:
            return value
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)  # assume UTC if no timezone given
        if value <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")
        return value


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    short_code: str
    short_url: str
    original_url: str
    created_at: datetime
    expires_at: datetime | None
    is_active: bool


class LinkListItem(LinkOut):
    click_count: int


class DailyClicks(BaseModel):
    day: date
    clicks: int


class LinkStats(BaseModel):
    short_code: str
    original_url: str
    total_clicks: int
    last_clicked_at: datetime | None
    clicks_by_day: list[DailyClicks]
