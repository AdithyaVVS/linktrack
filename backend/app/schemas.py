from datetime import date, datetime, timezone

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator


class LinkCreate(BaseModel):
    original_url: HttpUrl
    expires_at: datetime | None = None

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
