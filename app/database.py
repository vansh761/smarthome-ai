from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# SQLite database file will be created automatically
DATABASE_URL = "sqlite:///./smarthome.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── Table definition ──────────────────────────────────────────
class EnvironmentLog(Base):
    __tablename__ = "environment_logs"

    id              = Column(Integer, primary_key=True, index=True)
    timestamp       = Column(DateTime, default=datetime.now)
    room            = Column(String)

    # Climate
    temperature_c   = Column(Float)
    humidity_percent= Column(Float)

    # Lighting
    light_level     = Column(Integer)
    light_color     = Column(String)

    # Sound
    noise_db        = Column(Float)
    music_playing   = Column(Boolean)

    # Power
    power_watts     = Column(Float)
    ac_on           = Column(Boolean)
    fan_on          = Column(Boolean)

    # Comfort
    comfort_score   = Column(Float)


# ── Dependency for routes ─────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Create all tables ─────────────────────────────────────────
def init_db():
    Base.metadata.create_all(bind=engine)