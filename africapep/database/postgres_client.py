from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import structlog

from africapep.config import settings

log = structlog.get_logger()

engine = create_engine(
    settings.postgres_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def verify_connectivity() -> bool:
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        log.error("postgres_connectivity_failed", error=str(e))
        return False


def apply_schema(sql_file: str):
    with open(sql_file) as f:
        sql = f.read()
    with get_db() as db:
        db.execute(text(sql))
    log.info("postgres_schema_applied", file=sql_file)
