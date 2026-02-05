import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in environment")

# ✅ Production-grade pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # base connections
    max_overflow=40,       # burst capacity
    pool_timeout=30,       # wait before timeout
    pool_pre_ping=True,    # avoid stale connections
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
