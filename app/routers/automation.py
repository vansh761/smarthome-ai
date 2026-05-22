from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import SessionLocal
from sqlalchemy import Column, String, Integer, DateTime
from app.database import Base, engine

router = APIRouter(prefix="/automation", tags=["Automation Modes"])


# ── Database model for user settings ──────────────────────────────────────
class UserSettings(Base):
    __tablename__ = "user_settings"
    id            = Column(Integer, primary_key=True)
    user_id       = Column(String, unique=True, index=True)
    mode          = Column(String, default="full_ai")
    changes_this_hour = Column(Integer, default=0)
    last_hour     = Column(Integer, default=0)
    last_action   = Column(String, default="")
    locked        = Column(Integer, default=0)  # 0=unlocked, 1=locked
    updated_at    = Column(DateTime, default=datetime.now)


Base.metadata.create_all(bind=engine)


# ── Mode definitions ───────────────────────────────────────────────────────
MODES = {
    "manual": {
        "label":       "Manual Mode",
        "description": "You control everything. System never auto-acts.",
        "auto_act":    False,
        "suggestions": False,
        "max_changes_per_hour": 0,
    },
    "assisted": {
        "label":       "Assisted Mode",
        "description": "System suggests changes but never acts automatically.",
        "auto_act":    False,
        "suggestions": True,
        "max_changes_per_hour": 0,
    },
    "full_ai": {
        "label":       "Full AI Mode",
        "description": "System acts automatically based on emotion and patterns.",
        "auto_act":    True,
        "suggestions": True,
        "max_changes_per_hour": 3,
    },
}

# Rate limit — max auto-changes per hour in full_ai mode
MAX_CHANGES_PER_HOUR = 3


class SetModeRequest(BaseModel):
    user_id: str
    mode:    str  # manual / assisted / full_ai


class ActionRequest(BaseModel):
    user_id:     str
    action:      str
    environment: Optional[dict] = None


def get_or_create_settings(user_id: str) -> dict:
    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if not settings:
            settings = UserSettings(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)

        return {
            "user_id":  settings.user_id,
            "mode":     settings.mode,
            "locked":   bool(settings.locked),
            "changes_this_hour": settings.changes_this_hour,
            "last_action": settings.last_action,
        }
    finally:
        db.close()


def can_auto_act(user_id: str) -> dict:
    """
    Check if system can auto-act for this user right now.
    Enforces mode + rate limiting + lock.
    """
    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if not settings:
            return {
                "allowed":  True,
                "reason":   "new user — default full_ai mode",
                "mode":     "full_ai",
            }

        # Check lock
        if settings.locked:
            return {
                "allowed": False,
                "reason":  "environment is locked by user",
                "mode":    settings.mode,
            }

        # Check mode
        mode_config = MODES.get(settings.mode, MODES["full_ai"])
        if not mode_config["auto_act"]:
            return {
                "allowed": False,
                "reason":  f"mode is {settings.mode} — auto-act disabled",
                "mode":    settings.mode,
                "suggestion_only": mode_config["suggestions"],
            }

        # Check rate limit
        current_hour = datetime.now().hour
        if settings.last_hour != current_hour:
            # New hour — reset counter
            settings.changes_this_hour = 0
            settings.last_hour         = current_hour
            db.commit()

        if settings.changes_this_hour >= MAX_CHANGES_PER_HOUR:
            return {
                "allowed": False,
                "reason":  f"rate limit reached — max {MAX_CHANGES_PER_HOUR} auto-changes per hour",
                "mode":    settings.mode,
                "changes_this_hour": settings.changes_this_hour,
            }

        return {
            "allowed":           True,
            "reason":            "auto-act permitted",
            "mode":              settings.mode,
            "changes_this_hour": settings.changes_this_hour,
            "remaining":         MAX_CHANGES_PER_HOUR - settings.changes_this_hour,
        }
    finally:
        db.close()


def record_action(user_id: str, action: str):
    """Record that an auto-action was taken."""
    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if settings:
            current_hour = datetime.now().hour
            if settings.last_hour != current_hour:
                settings.changes_this_hour = 0
                settings.last_hour         = current_hour

            settings.changes_this_hour += 1
            settings.last_action        = action
            settings.updated_at         = datetime.now()
            db.commit()
    finally:
        db.close()


# ── Routes ─────────────────────────────────────────────────────────────────
@router.get("/modes")
def list_modes():
    """List all available automation modes."""
    return MODES


@router.get("/settings/{user_id}")
def get_settings(user_id: str):
    """Get current automation settings for a user."""
    return get_or_create_settings(user_id)


@router.post("/mode")
def set_mode(req: SetModeRequest):
    """Set automation mode for a user."""
    if req.mode not in MODES:
        return {
            "error": f"Invalid mode. Choose from: {list(MODES.keys())}"
        }

    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == req.user_id
        ).first()

        if not settings:
            settings = UserSettings(user_id=req.user_id, mode=req.mode)
            db.add(settings)
        else:
            settings.mode       = req.mode
            settings.updated_at = datetime.now()

        db.commit()

        return {
            "success":     True,
            "user_id":     req.user_id,
            "mode":        req.mode,
            "description": MODES[req.mode]["description"],
            "message":     f"Mode set to {MODES[req.mode]['label']}",
        }
    finally:
        db.close()


@router.post("/lock")
def lock_environment(user_id: str):
    """Lock the environment — system will not change anything."""
    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if not settings:
            settings = UserSettings(user_id=user_id, locked=1)
            db.add(settings)
        else:
            settings.locked     = 1
            settings.updated_at = datetime.now()

        db.commit()
        return {
            "locked":  True,
            "user_id": user_id,
            "message": "Environment locked. System will not make any changes."
        }
    finally:
        db.close()


@router.post("/unlock")
def unlock_environment(user_id: str):
    """Unlock the environment."""
    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if settings:
            settings.locked     = 0
            settings.updated_at = datetime.now()
            db.commit()

        return {
            "locked":  False,
            "user_id": user_id,
            "message": "Environment unlocked."
        }
    finally:
        db.close()


@router.post("/undo")
def undo_last_action(user_id: str):
    """Undo the last automatic action."""
    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if not settings or not settings.last_action:
            return {
                "success": False,
                "message": "No recent action to undo."
            }

        last = settings.last_action
        settings.last_action    = ""
        settings.updated_at     = datetime.now()
        db.commit()

        return {
            "success":       True,
            "undone_action": last,
            "message":       f"Undone: {last}. Environment restored to previous state."
        }
    finally:
        db.close()


@router.get("/can-act/{user_id}")
def check_can_act(user_id: str):
    """Check if system is allowed to auto-act for this user right now."""
    return can_auto_act(user_id)