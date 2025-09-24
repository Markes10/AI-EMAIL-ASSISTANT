from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import config

# SQLAlchemy base class for models
Base = declarative_base()

# Create engine based on DB URI
engine = create_engine(config.DB_URI, echo=config.DEBUG, future=True)

# Create session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Dependency for route-level DB access
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Optional: initialize DB tables
def init_db():
    import models.email
    import models.user
    import models.resume
    Base.metadata.create_all(bind=engine)