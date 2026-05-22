from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from app.ai.emotion_model import analyze_emotion
from app.routers.automation import can_auto_act, record_action
from app.routers.transparency import log_action, ethical_check

router = APIRouter(prefix="/emotion", tags=["Emotion Engine"])


class EmotionRequest(BaseModel):
    text:        str
    time_of_day: Optional[str]  = None
    user_id:     Optional[str]  = "default"
    is_sleeping: Optional[bool] = False


class MultiUserRequest(BaseModel):
    users: List[dict]


@router.post("/analyze")
def analyze(req: EmotionRequest):
    result = analyze_emotion(
        text        = req.text,
        time_of_day = req.time_of_day,
        user_id     = req.user_id,
        is_sleeping = req.is_sleeping,
    )

    act_check = can_auto_act(req.user_id)

    if not act_check["allowed"]:
        result["auto_act"]  = False
        result["mode"]      = act_check.get("reason", "auto-act disabled")
        result["suggestion"] = (
            "Suggestion: " + result["environment_suggestion"]["message"]
            if act_check.get("suggestion_only") else None
        )
    else:
        # Run ethical check before acting
        eth = ethical_check(
            emotion     = result["detected_emotion"],
            confidence  = result["confidence"],
            action_type = "auto_adjust",
            user_id     = req.user_id,
        )

        if not eth["passed"]:
            # Ethical check failed — convert to suggestion
            result["auto_act"]        = False
            result["mode"]            = "suggestion_only"
            result["ethical_issues"]  = eth["issues"]
            result["suggestion"]      = (
                "Suggestion: " + result["environment_suggestion"]["message"]
            )
            ethical_status = "blocked"
        else:
            ethical_status = "passed"

        # Log the action with full reasoning
        log_action(
            user_id      = req.user_id,
            action_type  = "auto_adjust" if eth["passed"] else "suggestion",
            emotion      = result["detected_emotion"],
            confidence   = result["confidence"],
            source       = result.get("detection_source", "hybrid"),
            environment  = result["environment_suggestion"],
            reason       = result["explanation"],
            ethical_check= ethical_status,
        )

        record_action(
            req.user_id,
            f"{result['detected_emotion']} environment activated"
        )

    result["automation_status"] = act_check
    return result


@router.post("/analyze/multi-user")
def analyze_multi_user(req: MultiUserRequest):
    from app.ai.emotion_model import resolve_multi_user
    results = []
    for user in req.users:
        result = analyze_emotion(
            text        = user.get("text", ""),
            time_of_day = user.get("time_of_day"),
            user_id     = user.get("user_id", "default"),
            is_sleeping = user.get("is_sleeping", False),
        )
        results.append(result)
    resolution = resolve_multi_user(results)
    return {
        "individual_results":    results,
        "multi_user_resolution": resolution,
    }


@router.get("/emotions")
def list_emotions():
    from app.ai.emotion_model import EMOTION_ENVIRONMENT, EMOTION_PRIORITY
    return {
        emotion: {
            "priority": EMOTION_PRIORITY.get(emotion, 99),
            "light":    f"{env['light_level']}% {env['light_color']}",
            "temp":     f"{env['temperature_c']}°C",
            "music":    env["music"],
            "message":  env["message"],
        }
        for emotion, env in EMOTION_ENVIRONMENT.items()
    }

@router.post("/analyze/distribution")
def analyze_with_distribution(req: EmotionRequest):
    """
    Returns full probability distribution across all emotions.
    More honest representation than single forced label.
    Example: stressed 45%, anxious 35%, tired 20%
    """
    result = analyze_emotion(
        text        = req.text,
        time_of_day = req.time_of_day,
        user_id     = req.user_id,
        is_sleeping = req.is_sleeping,
    )

    all_scores = result.get("all_scores", {})
    total      = sum(all_scores.values())

    if total > 0:
        distribution = {
            emotion: round(score / total * 100, 1)
            for emotion, score in sorted(
                all_scores.items(), key=lambda x: x[1], reverse=True
            )
        }
    else:
        distribution = {result["detected_emotion"]: 100.0}

    top_3 = list(distribution.items())[:3]

    return {
        "primary_emotion":    result["detected_emotion"],
        "confidence":         result["confidence"],
        "distribution":       distribution,
        "top_3": [
            {"emotion": e, "probability": p}
            for e, p in top_3
        ],
        "interpretation": (
            f"Most likely {top_3[0][0]} ({top_3[0][1]}%)"
            + (f", possibly {top_3[1][0]} ({top_3[1][1]}%)" if len(top_3) > 1 and top_3[1][1] > 15 else "")
        ),
        "detection_source":   result.get("detection_source", "hybrid"),
        "environment":        result["environment_suggestion"],
        "honest_note":        "Distribution based on keyword scores + semantic similarity. Not calibrated probabilities.",
    }