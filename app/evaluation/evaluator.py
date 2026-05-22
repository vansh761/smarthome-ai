import json
from collections import defaultdict
from app.ai.emotion_model import analyze_emotion
from app.evaluation.test_dataset import TEST_DATASET


def run_evaluation() -> dict:
    """
    Run full evaluation on 200-sentence test dataset.
    Returns accuracy, F1, precision, recall, confusion matrix.
    """
    print(f"Running evaluation on {len(TEST_DATASET)} sentences...")

    y_true = []
    y_pred = []
    results = []
    language_results = defaultdict(lambda: {"correct": 0, "total": 0})

    EMOTIONS = [
        "stressed", "tired", "happy", "sad",
        "angry", "anxious", "focused", "neutral"
    ]

    for i, item in enumerate(TEST_DATASET):
        result = analyze_emotion(text=item["text"])
        predicted = result["detected_emotion"]
        expected  = item["expected"]
        correct   = predicted == expected

        y_true.append(expected)
        y_pred.append(predicted)

        lang = item["language"]
        language_results[lang]["total"]   += 1
        language_results[lang]["correct"] += int(correct)

        results.append({
            "id":         i + 1,
            "text":       item["text"][:50] + "...",
            "language":   lang,
            "expected":   expected,
            "predicted":  predicted,
            "correct":    correct,
            "confidence": result["confidence"],
        })

        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(TEST_DATASET)}...")

    # ── Overall accuracy ──────────────────────────────────────────────
    total   = len(y_true)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = round((correct / total) * 100, 2)

    # ── Per-emotion metrics ───────────────────────────────────────────
    emotion_metrics = {}
    for emotion in EMOTIONS:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == emotion and p == emotion)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != emotion and p == emotion)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == emotion and p != emotion)
        tn = sum(1 for t, p in zip(y_true, y_pred) if t != emotion and p != emotion)

        precision = round(tp / (tp + fp) * 100, 1) if (tp + fp) > 0 else 0.0
        recall    = round(tp / (tp + fn) * 100, 1) if (tp + fn) > 0 else 0.0
        f1        = round(
            2 * precision * recall / (precision + recall), 1
        ) if (precision + recall) > 0 else 0.0
        support   = sum(1 for t in y_true if t == emotion)

        emotion_metrics[emotion] = {
            "precision": precision,
            "recall":    recall,
            "f1_score":  f1,
            "support":   support,
            "tp": tp, "fp": fp, "fn": fn,
        }

    # ── Macro averages ────────────────────────────────────────────────
    active = [m for m in emotion_metrics.values() if m["support"] > 0]
    macro_precision = round(sum(m["precision"] for m in active) / len(active), 1)
    macro_recall    = round(sum(m["recall"]    for m in active) / len(active), 1)
    macro_f1        = round(sum(m["f1_score"]  for m in active) / len(active), 1)

    # ── Confusion matrix ──────────────────────────────────────────────
    confusion = {}
    for true_em in EMOTIONS:
        confusion[true_em] = {}
        for pred_em in EMOTIONS:
            confusion[true_em][pred_em] = sum(
                1 for t, p in zip(y_true, y_pred)
                if t == true_em and p == pred_em
            )

    # ── Language accuracy ─────────────────────────────────────────────
    lang_accuracy = {}
    for lang, counts in language_results.items():
        lang_accuracy[lang] = {
            "accuracy": round(counts["correct"] / counts["total"] * 100, 1),
            "correct":  counts["correct"],
            "total":    counts["total"],
        }

    # ── Confidence stats ──────────────────────────────────────────────
    confidences = [r["confidence"] for r in results]
    avg_conf    = round(sum(confidences) / len(confidences), 1)
    high_conf   = sum(1 for c in confidences if c >= 80)

    # ── Wrong predictions ─────────────────────────────────────────────
    wrong = [r for r in results if not r["correct"]]

    print(f"\n✅ Evaluation complete!")
    print(f"   Accuracy:  {accuracy}%")
    print(f"   Macro F1:  {macro_f1}%")
    print(f"   Avg Conf:  {avg_conf}%")

    return {
        "summary": {
            "total_sentences":    total,
            "correct":            correct,
            "incorrect":          total - correct,
            "overall_accuracy":   accuracy,
            "macro_precision":    macro_precision,
            "macro_recall":       macro_recall,
            "macro_f1":           macro_f1,
            "avg_confidence":     avg_conf,
            "high_conf_pct":      round(high_conf / total * 100, 1),
        },
        "emotion_metrics":    emotion_metrics,
        "confusion_matrix":   confusion,
        "language_accuracy":  dict(
            sorted(lang_accuracy.items(),
                   key=lambda x: x[1]["accuracy"], reverse=True)
        ),
        "wrong_predictions":  wrong[:20],  # top 20 mistakes
        "grade": (
            "Excellent" if accuracy >= 90 else
            "Good"      if accuracy >= 80 else
            "Fair"      if accuracy >= 70 else
            "Needs work"
        ),
    }