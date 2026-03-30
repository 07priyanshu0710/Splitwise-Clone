
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Since we are using standard (sync) SQLAlchemy for repository pattern in this iterate
# (BaseRepository uses Session, not AsyncSession), we need a sync engine too.
# settings.SQLALCHEMY_DATABASE_URI is Async.
# We will create a SYNC URL from settings.

SYNC_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI).replace("postgresql+asyncpg", "postgresql")

engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
