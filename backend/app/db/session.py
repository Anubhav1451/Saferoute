from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database URL - can be overridden with environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./saferoute.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
