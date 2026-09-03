import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import OperationalError
from app.config import settings

logger = logging.getLogger("worker_risk_engine.database")

Base = declarative_base()

# Primary database URL
_db_url = settings.effective_db_url
_engine_kwargs = {"echo": False}

if _db_url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20

engine = create_engine(_db_url, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per request.
    Ensures the session is cleanly closed upon completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables defined in SQLAlchemy models.
    If cloud PostgreSQL is blocked by local network firewall,
    falls back gracefully to SQLite so the server never crashes.
    """
    global engine, SessionLocal
    import app.models.risk_score  # Ensure models are imported

    try:
        # Test connection
        with engine.connect() as conn:
            pass
        Base.metadata.create_all(bind=engine)
        logger.info("Connected to database successfully (%s)", engine.url.drivername)
    except OperationalError as exc:
        if not str(engine.url).startswith("sqlite"):
            logger.warning(
                "Network firewall or DNS blocked direct connection to Supabase (%s). "
                "Switching automatically to local SQLite fallback so your server stays online!",
                exc.orig if hasattr(exc, "orig") else exc
            )
            # Rebind to local SQLite fallback
            fallback_url = "sqlite:///./risk_scores.db"
            engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            Base.metadata.create_all(bind=engine)
            logger.info("Local SQLite database initialized at ./risk_scores.db")
        else:
            raise exc
