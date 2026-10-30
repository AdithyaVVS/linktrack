from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Click, Link


def list_links_with_counts(db: Session):
    """One query: every link plus its click count (0 if none)."""
    stmt = (
        select(Link, func.count(Click.id).label("click_count"))
        .outerjoin(Click, Click.link_id == Link.id)
        .group_by(Link.id)
        .order_by(Link.created_at.desc())
    )
    return db.execute(stmt).all()


def get_link_stats(db: Session, link: Link) -> dict:
    total, last_clicked = db.execute(
        select(func.count(Click.id), func.max(Click.clicked_at)).where(
            Click.link_id == link.id
        )
    ).one()

    day = func.date(Click.clicked_at)
    rows = db.execute(
        select(day.label("day"), func.count(Click.id).label("clicks"))
        .where(Click.link_id == link.id)
        .group_by(day)
        .order_by(day)
    ).all()

    return {
        "short_code": link.short_code,
        "original_url": link.original_url,
        "total_clicks": total,
        "last_clicked_at": last_clicked,
        "clicks_by_day": [{"day": r.day, "clicks": r.clicks} for r in rows],
    }
