from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.simulator import simulate_room, simulate_all_rooms, ROOMS
from app.services.logger import log_environment, get_room_history, get_all_history
from app.database import get_db

router = APIRouter(prefix="/environment", tags=["Environment Simulator"])


@router.get("/rooms")
def list_rooms():
    return {"rooms": ROOMS}


@router.get("/room/{room_name}")
def get_room(room_name: str, save: bool = True, db: Session = Depends(get_db)):
    """
    Get live sensor reading for a room.
    Automatically saves to database (save=false to skip).
    """
    if room_name not in ROOMS:
        return {"error": f"Room '{room_name}' not found. Choose from: {ROOMS}"}

    state = simulate_room(room_name)

    if save:
        log_environment(db, state)

    return state.dict()


@router.get("/snapshot")
def get_full_snapshot(save: bool = True, db: Session = Depends(get_db)):
    """Get readings for all rooms and save them."""
    data = simulate_all_rooms()
    results = {}
    for room, state in data.items():
        if save:
            log_environment(db, state)
        results[room] = state.dict()
    return results


@router.get("/history/{room_name}")
def room_history(room_name: str, limit: int = 20, db: Session = Depends(get_db)):
    """Get saved history for a room."""
    if room_name not in ROOMS:
        return {"error": f"Room not found. Choose from: {ROOMS}"}

    records = get_room_history(db, room_name, limit)
    return {
        "room": room_name,
        "count": len(records),
        "history": [
            {
                "timestamp":      r.timestamp,
                "temperature_c":  r.temperature_c,
                "noise_db":       r.noise_db,
                "light_level":    r.light_level,
                "power_watts":    r.power_watts,
                "comfort_score":  r.comfort_score,
                "ac_on":          r.ac_on,
            }
            for r in records
        ]
    }


@router.get("/history")
def all_history(limit: int = 50, db: Session = Depends(get_db)):
    """Get saved history across all rooms."""
    records = get_all_history(db, limit)
    return {"count": len(records), "records": [
        {
            "timestamp":     r.timestamp,
            "room":          r.room,
            "temperature_c": r.temperature_c,
            "comfort_score": r.comfort_score,
            "power_watts":   r.power_watts,
        }
        for r in records
    ]}