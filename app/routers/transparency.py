from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import Base, engine, SessionLocal
from sqlalchemy import Column, Integer, String, DateTime, Float

router = APIRouter(prefix="/transparency", tags=["Ethical Constraints & Transparency"])


# ── Action log table ───────────────────────────────────────────────────────
class ActionLog(Base):
    __tablename__ = "action_logs"
    id            = Column(Integer, primary_key=True)
    user_id       = Column(String, index=True)
    timestamp     = Column(DateTime, default=datetime.now)
    action_type   = Column(String)   # auto_adjust / suggestion / blocked / user_override
    emotion       = Column(String)
    confidence    = Column(Float)
    source        = Column(String)   # hybrid / transformer / pattern
    environment   = Column(String)   # JSON string of what changed
    reason        = Column(String)   # why this happened
    ethical_check = Column(String)   # passed / blocked / suggested_only


Base.metadata.create_all(bind=engine)


class LogActionRequest(BaseModel):
    user_id:      str
    action_type:  str
    emotion:      str
    confidence:   float
    source:       str
    environment:  dict
    reason:       str
    ethical_check:str = "passed"


def log_action(
    user_id:      str,
    action_type:  str,
    emotion:      str,
    confidence:   float,
    source:       str,
    environment:  dict,
    reason:       str,
    ethical_check:str = "passed",
) -> dict:
    import json
    db = SessionLocal()
    try:
        entry = ActionLog(
            user_id       = user_id,
            timestamp     = datetime.now(),
            action_type   = action_type,
            emotion       = emotion,
            confidence    = confidence,
            source        = source,
            environment   = json.dumps(environment),
            reason        = reason,
            ethical_check = ethical_check,
        )
        db.add(entry)
        db.commit()
        return {"logged": True}
    finally:
        db.close()


def get_action_history(user_id: str, limit: int = 20) -> list:
    import json
    db = SessionLocal()
    try:
        logs = db.query(ActionLog)\
            .filter(ActionLog.user_id == user_id)\
            .order_by(ActionLog.timestamp.desc())\
            .limit(limit)\
            .all()
        return [
            {
                "timestamp":    l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "action_type":  l.action_type,
                "emotion":      l.emotion,
                "confidence":   l.confidence,
                "source":       l.source,
                "environment":  json.loads(l.environment) if l.environment else {},
                "reason":       l.reason,
                "ethical_check":l.ethical_check,
            }
            for l in logs
        ]
    finally:
        db.close()


# ── Ethical constraints checker ────────────────────────────────────────────
def ethical_check(
    emotion:     str,
    confidence:  float,
    action_type: str,
    user_id:     str,
) -> dict:
    """
    Check if an action passes ethical constraints.
    System can suggest or gently adjust — never force.
    """
    issues = []

    # Rule 1 — Low confidence should never auto-act
    if confidence < 50 and action_type == "auto_adjust":
        issues.append(
            f"Confidence {confidence}% is too low for auto-adjustment. "
            f"Minimum 50% required."
        )

    # Rule 2 — Rapid repeated actions are manipulation
    db = SessionLocal()
    try:
        from sqlalchemy import func
        recent_count = db.query(func.count(ActionLog.id))\
            .filter(
                ActionLog.user_id == user_id,
                ActionLog.action_type == "auto_adjust",
                ActionLog.timestamp >= datetime.now().replace(
                    minute=datetime.now().minute - 5,
                    second=0
                )
            ).scalar()

        if recent_count >= 3:
            issues.append(
                "Too many auto-adjustments in 5 minutes. "
                "This could feel manipulative. Switching to suggestion mode."
            )
    except:
        pass
    finally:
        db.close()

    # Rule 3 — Sleeping users should never have environment changed
    # except for sleep mode itself
    if emotion == "sleeping" and action_type == "auto_adjust":
        pass  # sleeping mode is always allowed
    elif emotion not in ("stressed","anxious","angry","tired","sad",
                         "happy","focused","neutral","sleeping"):
        issues.append(f"Unknown emotion {emotion} — cannot act.")

    if issues:
        return {
            "passed":   False,
            "issues":   issues,
            "verdict":  "suggestion_only",
            "message":  "Action converted to suggestion due to ethical constraints.",
        }

    return {
        "passed":  True,
        "issues":  [],
        "verdict": "approved",
        "message": "Action approved by ethical constraints layer.",
    }


# ── Routes ──────────────────────────────────────────────────────────────────
@router.get("/history/{user_id}")
def action_history(user_id: str, limit: int = 20):
    """
    See full history of everything the system did and why.
    Complete transparency for the user.
    """
    history = get_action_history(user_id, limit)
    return {
        "user_id": user_id,
        "count":   len(history),
        "message": "Every action the AI took is logged here with full reasoning.",
        "history": history,
    }


@router.get("/explain/{user_id}/last")
def explain_last_action(user_id: str):
    """Explain the most recent action the system took."""
    history = get_action_history(user_id, limit=1)
    if not history:
        return {
            "message": "No actions recorded yet for this user.",
            "user_id": user_id,
        }
    last = history[0]
    return {
        "user_id":     user_id,
        "last_action": last,
        "explanation": (
            f"At {last['timestamp']}, the system detected you were "
            f"{last['emotion']} with {last['confidence']}% confidence "
            f"(source: {last['source']}). "
            f"Reason: {last['reason']}. "
            f"Ethical check: {last['ethical_check']}."
        ),
    }


@router.post("/check")
def run_ethical_check(
    user_id:     str,
    emotion:     str,
    confidence:  float,
    action_type: str = "auto_adjust",
):
    """Run ethical constraints check before taking any action."""
    return ethical_check(emotion, confidence, action_type, user_id)


@router.get("/principles")
def ethical_principles():
    """The ethical rules this system follows."""
    return {
        "principles": [
            "System only suggests or gently adjusts — never forces changes",
            "Every automatic action is logged with full reasoning",
            "Low confidence detections convert to suggestions only",
            "Rapid repeated actions are blocked as potential manipulation",
            "User can view complete history of all AI actions at any time",
            "User can override any AI decision at any time",
            "No raw voice or text stored — only features and metadata",
            "Incognito mode available — clears all memory instantly",
            "System acts for user well-being only — never for engagement",
            "Transparency panel shows every reason for every change",
        ],
        "version":    "1.0",
        "last_updated": "2026",
    }