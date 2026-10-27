from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import LinkCreate, LinkOut
from app.services.links import CodeGenerationError, create_link

router = APIRouter(prefix="/api/links", tags=["links"])


def to_out(link) -> LinkOut:
    return LinkOut(
        short_code=link.short_code,
        short_url=f"{settings.base_url}/{link.short_code}",
        original_url=link.original_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
        is_active=link.is_active,
    )


@router.post("", response_model=LinkOut, status_code=201)
def create_short_link(payload: LinkCreate, db: Session = Depends(get_db)):
    try:
        link = create_link(db, str(payload.original_url), payload.expires_at)
    except CodeGenerationError:
        raise HTTPException(status_code=503, detail="Could not generate a short code, try again")
    return to_out(link)
