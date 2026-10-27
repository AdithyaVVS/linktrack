from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.clicks import record_click
from app.services.links import get_link_by_code, is_link_usable

router = APIRouter(tags=["redirect"])


@router.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    link = get_link_by_code(db, short_code)
    if link is None:
        raise HTTPException(status_code=404, detail="Short link not found")
    if not is_link_usable(link):
        raise HTTPException(status_code=410, detail="This link has expired or been deactivated")

    background_tasks.add_task(
        record_click,
        link.id,
        request.headers.get("referer"),
        request.headers.get("user-agent"),
    )
    return RedirectResponse(url=link.original_url, status_code=302)
