from app.database import SessionLocal
from app.models import Click


def record_click(link_id: int, referrer: str | None, user_agent: str | None) -> None:
    """Runs in the background after the redirect is sent, with its own session."""
    db = SessionLocal()
    try:
        db.add(Click(link_id=link_id, referrer=referrer, user_agent=user_agent))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
