from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/state", tags=["Shared State"])

# In-memory state store — simple dict per user
_state: dict = {}


class StateUpdate(BaseModel):
    user_id:          str = "default"
    weather_temp:     Optional[float] = None
    weather_place:    Optional[str]   = None
    weather_humidity: Optional[float] = None
    mic_db:           Optional[float] = None
    light_level:      Optional[int]   = None
    power_watts:      Optional[float] = None
    ac_on:            Optional[bool]  = None
    music_playing:    Optional[str]   = None


@router.post("/update")
def update_state(req: StateUpdate):
    uid = req.user_id
    if uid not in _state:
        _state[uid] = {}
    data = req.dict(exclude_none=True)
    data.pop("user_id", None)
    _state[uid].update(data)
    return {"updated": True, "state": _state[uid]}


@router.get("/get/{user_id}")
def get_state(user_id: str):
    return _state.get(user_id, {})
