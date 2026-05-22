from sqlalchemy.orm import Session
from app.database import EnvironmentLog
from app.models.environment import EnvironmentState

def log_environment(db: Session, state: EnvironmentState) -> EnvironmentLog:
    """Save one environment snapshot to the database."""
    record = EnvironmentLog(
        timestamp        = state.timestamp,
        room             = state.room,
        temperature_c    = state.temperature_c,
        humidity_percent = state.humidity_percent,
        light_level      = state.light_level,
        light_color      = state.light_color,
        noise_db         = state.noise_db,
        music_playing    = state.music_playing,
        power_watts      = state.power_watts,
        ac_on            = state.ac_on,
        fan_on           = state.fan_on,
        comfort_score    = state.comfort_score
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_room_history(db: Session, room: str, limit: int = 50):
    """Fetch last N readings for a room."""
    return (
        db.query(EnvironmentLog)
        .filter(EnvironmentLog.room == room)
        .order_by(EnvironmentLog.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_all_history(db: Session, limit: int = 100):
    """Fetch last N readings across all rooms."""
    return (
        db.query(EnvironmentLog)
        .order_by(EnvironmentLog.timestamp.desc())
        .limit(limit)
        .all()
    )