from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import LinkCreate, LinkListItem, LinkOut, LinkStats
from app.services.links import CodeGenerationError, create_link, get_link_by_code
from app.services.stats import get_link_stats, list_links_with_counts

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


@router.get("", response_model=list[LinkListItem])
def list_links(db: Session = Depends(get_db)):
    rows = list_links_with_counts(db)
    return [
        LinkListItem(**to_out(link).model_dump(), click_count=count)
        for link, count in rows
    ]


@router.get("/{short_code}/stats", response_model=LinkStats)
def link_stats(short_code: str, db: Session = Depends(get_db)):
    link = get_link_by_code(db, short_code)
    if link is None:
        raise HTTPException(status_code=404, detail="Short link not found")
    return get_link_stats(db, link)


@router.delete("/{short_code}", status_code=204)
def delete_link(short_code: str, db: Session = Depends(get_db)):
    link = get_link_by_code(db, short_code)
    if link is None:
        raise HTTPException(status_code=404, detail="Short link not found")
    db.delete(link)  # its clicks are deleted too (cascade)
    db.commit()
    return Response(status_code=204)
