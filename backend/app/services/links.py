from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Link
from app.services.shortcode import generate_short_code

MAX_RETRIES = 5


class CodeGenerationError(Exception):
    """Raised when a unique short code could not be generated."""


def create_link(
    db: Session, original_url: str, expires_at: datetime | None = None
) -> Link:
    for _ in range(MAX_RETRIES):
        link = Link(
            short_code=generate_short_code(),
            original_url=original_url,
            expires_at=expires_at,
        )
        db.add(link)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()  # code collided with an existing one; try again
            continue
        db.refresh(link)
        return link
    raise CodeGenerationError("Could not generate a unique short code")
