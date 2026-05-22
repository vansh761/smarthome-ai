from transformers import pipeline
import torch

_classifier = None

EMOTION_LABELS = [
    "feeling stressed and overwhelmed with too much work or pressure",
    "feeling tired exhausted sleepy and needing rest",
    "feeling happy joyful excited and in a good mood",
    "feeling sad depressed lonely unhappy and low",
    "feeling angry furious irritated and frustrated",
    "feeling anxious nervous worried scared and panicked",
    "feeling focused concentrated productive and working",
    "feeling neutral okay normal nothing special",
]

LABEL_TO_EMOTION = {
    "feeling stressed and overwhelmed with too much work or pressure": "stressed",
    "feeling tired exhausted sleepy and needing rest":                 "tired",
    "feeling happy joyful excited and in a good mood":                 "happy",
    "feeling sad depressed lonely unhappy and low":                    "sad",
    "feeling angry furious irritated and frustrated":                  "angry",
    "feeling anxious nervous worried scared and panicked":             "anxious",
    "feeling focused concentrated productive and working":             "focused",
    "feeling neutral okay normal nothing special":                     "neutral",
}


def get_classifier():
    global _classifier
    if _classifier is None:
        print("Loading zero-shot fallback model...")
        try:
            _classifier = pipeline(
                "zero-shot-classification",
                model = "cross-encoder/nli-MiniLM2-L6-H768",
                device    = -1,   # CPU only
                framework = "pt",
            )
            print("Zero-shot fallback model loaded")
        except Exception as e:
            print(f"Zero-shot model failed to load: {e}")
            _classifier = None
    return _classifier


def zero_shot_classify(text: str) -> dict:
    """
    Classify emotion using zero-shot transformer.
    Called only when hybrid confidence is below threshold.
    Returns emotion + confidence score.
    """
    classifier = get_classifier()

    if classifier is None:
        return {
            "emotion":     "neutral",
            "confidence":  50.0,
            "source":      "fallback_failed",
            "all_scores":  {},
        }

    try:
        result = classifier(
            text,
            candidate_labels = EMOTION_LABELS,
            multi_label      = False,
        )

        # Map labels back to emotion names
        scores = {}
        for label, score in zip(result["labels"], result["scores"]):
            emotion = LABEL_TO_EMOTION.get(label, "neutral")
            scores[emotion] = round(score * 100, 1)

        sorted_scores  = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_emotion    = sorted_scores[0][0]
        top_score      = sorted_scores[0][1]
        second_score   = sorted_scores[1][1]

        # Scale confidence based on gap between top and second
        # Large gap = high confidence, small gap = low confidence
        gap = top_score - second_score

        if gap >= 40:
            scaled_confidence = 92.0
        elif gap >= 30:
            scaled_confidence = 85.0
        elif gap >= 20:
            scaled_confidence = 78.0
        elif gap >= 10:
            scaled_confidence = 70.0
        else:
            scaled_confidence = 60.0

        return {
            "emotion":    top_emotion,
            "confidence": round(scaled_confidence, 1),
            "source":     "zero_shot_transformer",
            "all_scores": scores,
        }

    except Exception as e:
        print(f"Zero-shot classification failed: {e}")
        return {
            "emotion":    "neutral",
            "confidence": 50.0,
            "source":     "fallback_error",
            "all_scores": {},
        }