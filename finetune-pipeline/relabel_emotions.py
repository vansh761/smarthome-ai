"""
Sentiment -> 8-Class Emotion Relabeling Pipeline
===================================================
Purpose: IndiSentiment140 (real or reconstructed) gives binary sentiment labels
(negative/positive). Our system needs 8 emotion classes:
  stressed, anxious, tired, sad, angry, happy, focused, neutral

This script uses an LLM (Groq, free tier, already wired into the project) to
relabel sentiment -> emotion, with an explicit, fixed prompt and temperature=0
for reproducibility, followed by a MANDATORY human spot-check stage before
anything is used for fine-tuning.

This directly answers the reviewer's critique: "you have not trained or
fine-tuned a model on real labeled data... no amount of report polish fixes
this." This pipeline is the fix -- not by claiming perfect labels, but by
being transparent about exactly how labels were derived and verified.

Pipeline stages:
  1. AUTO-RELABEL   - Groq assigns one of 8 emotion classes per sample,
                       with a confidence flag for ambiguous cases
  2. SAMPLE FOR REVIEW - randomly draw N samples per language for human check
  3. HUMAN SPOT-CHECK  - YOU verify the sampled subset (CSV-based, no special
                       tooling needed -- just open in Excel/Sheets)
  4. AGREEMENT REPORT  - compute LLM-vs-human agreement rate, report honestly
  5. FINAL DATASET     - only samples above a confidence threshold (or all,
                       with the disagreement rate disclosed) go into training

Honest framing for the report:
  "Emotion labels were derived via LLM-assisted relabeling of sentiment data,
   with manual verification on a stratified N-sample-per-language subset.
   Human-LLM agreement was X%. This is a semi-automated labeling methodology,
   not human-annotated ground truth at full scale -- a documented limitation
   common in low-resource multilingual NLP."
"""

import os
import json
import time
import random
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from collections import Counter

# ── Config ──────────────────────────────────────────────────────────────────

INPUT_DIR           = Path("indisentiment140_reconstructed")  # output of previous script
OUTPUT_DIR           = Path("relabeled_emotions")
SPOTCHECK_DIR        = Path("spotcheck_for_human_review")
SAMPLES_PER_LANG_FOR_RELABEL = 60    # reduced from 200 for faster turnaround -- still enough
                                      # for a proof-of-concept fine-tuning experiment
SPOTCHECK_SAMPLE_SIZE        = 30    # per language, drawn from the relabeled set
RANDOM_SEED          = 42

EMOTION_CLASSES = ["stressed", "anxious", "tired", "sad", "angry", "happy", "focused", "neutral"]

RELABEL_SYSTEM_PROMPT = f"""You are a careful emotion-labeling assistant for a research dataset.
You will be given a short piece of text (translated from English, may have translation artifacts)
and its original sentiment polarity (negative or positive).

Classify the text into EXACTLY ONE of these 8 emotion categories:
{", ".join(EMOTION_CLASSES)}

Rules:
- Use the sentiment polarity as a weak prior only -- judge primarily from the text content.
- Negative sentiment usually maps to: stressed, anxious, tired, sad, or angry (pick the best fit, not just "sad" by default).
- Positive sentiment usually maps to: happy or focused.
- If the text is ambiguous, generic, or doesn't clearly express any of the 8, label it "neutral".
- If translation artifacts make the text incomprehensible, label it "neutral" and set confidence to "low".

Respond with ONLY a JSON object, no other text:
{{"emotion": "<one of the 8 classes>", "confidence": "high|medium|low", "reason": "<one short phrase>"}}
"""


def get_groq_client():
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set. export GROQ_API_KEY=your_key_here")
    return Groq(api_key=api_key)


def relabel_one(client, text: str, polarity: int) -> dict:
    polarity_label = "negative" if polarity == 0 else "positive" if polarity == 4 else "neutral"
    user_prompt = f'Sentiment polarity: {polarity_label}\nText: "{text}"'

    try:
        response = client.chat.completions.create(
            model       = "llama-3.1-8b-instant",
            messages    = [
                {"role": "system", "content": RELABEL_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens  = 80,
            temperature = 0,   # deterministic -- same input always gives same label
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        if parsed.get("emotion") not in EMOTION_CLASSES:
            parsed["emotion"] = "neutral"
            parsed["confidence"] = "low"
        return parsed
    except Exception as e:
        return {"emotion": "neutral", "confidence": "low", "reason": f"error: {e}"}


def relabel_language(client, lang_name: str, max_workers: int = 6) -> pd.DataFrame:
    train_path = INPUT_DIR / lang_name / "train.csv"
    if not train_path.exists():
        print(f"  [skip] No data for {lang_name}")
        return pd.DataFrame()

    df = pd.read_csv(train_path)
    if "text_translated" not in df.columns or df["text_translated"].isna().all():
        print(f"  [skip] {lang_name} has no machine-translated text (needs manual curation).")
        return pd.DataFrame()

    df = df[df["text_translated"].notna()].reset_index(drop=True)
    df = df.sample(n=min(SAMPLES_PER_LANG_FOR_RELABEL, len(df)), random_state=RANDOM_SEED)
    df = df.reset_index(drop=True)

    print(f"\n=== Relabeling {lang_name}: {len(df)} samples ({max_workers} concurrent workers) ===")

    results = [None] * len(df)
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(relabel_one, client, row["text_translated"], row["polarity"]): i
            for i, row in df.iterrows()
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                results[idx] = {"emotion": "neutral", "confidence": "low", "reason": f"error: {e}"}
            completed += 1
            if completed % 20 == 0 or completed == len(df):
                print(f"  ...{completed}/{len(df)}")

    df["emotion"]        = [r["emotion"] for r in results]
    df["llm_confidence"] = [r["confidence"] for r in results]
    df["llm_reason"]     = [r.get("reason","") for r in results]
    df["language"]       = lang_name
    return df


def make_spotcheck_file(df: pd.DataFrame, lang_name: str):
    """
    Produces a plain CSV for YOU to manually review -- no special tools needed.
    Columns: text, llm_emotion, [blank column for your verdict]
    """
    n = min(SPOTCHECK_SAMPLE_SIZE, len(df))
    sample = df.sample(n=n, random_state=RANDOM_SEED)[
        ["text_translated", "polarity", "emotion", "llm_confidence", "llm_reason"]
    ].copy()
    sample = sample.rename(columns={"emotion": "llm_predicted_emotion"})
    sample["human_verdict_CORRECT_or_actual_emotion"] = ""  # you fill this in
    sample["notes"] = ""

    SPOTCHECK_DIR.mkdir(exist_ok=True)
    out_path = SPOTCHECK_DIR / f"{lang_name}_spotcheck.csv"
    sample.to_csv(out_path, index=False)
    print(f"  Spot-check file: {out_path}  ({n} rows -- open in Excel/Sheets and fill the verdict column)")


def compute_agreement_report(spotcheck_dir: Path) -> pd.DataFrame:
    """
    Run this AFTER you've manually filled in the verdict columns.
    Computes LLM-vs-human agreement rate per language -- this is the number
    that goes in the report, not a guessed accuracy figure.
    """
    rows = []
    for f in sorted(spotcheck_dir.glob("*_spotcheck.csv")):
        df = pd.read_csv(f)
        verdict_col = "human_verdict_CORRECT_or_actual_emotion"
        filled = df[df[verdict_col].notna() & (df[verdict_col].astype(str).str.strip() != "")]
        if len(filled) == 0:
            print(f"  [skip] {f.name}: no human verdicts filled in yet")
            continue

        agree = 0
        for _, row in filled.iterrows():
            verdict = str(row[verdict_col]).strip().lower()
            if verdict in ("correct", "yes", "y", "ok", row["llm_predicted_emotion"].lower()):
                agree += 1
        agreement_rate = round(agree / len(filled) * 100, 1)
        lang = f.stem.replace("_spotcheck", "")
        rows.append({"language": lang, "reviewed": len(filled), "agreement_pct": agreement_rate})
        print(f"  {lang}: {agreement_rate}% agreement on {len(filled)} reviewed samples")

    report = pd.DataFrame(rows)
    if len(report):
        report.to_csv("agreement_report.csv", index=False)
        print(f"\nOverall mean agreement: {report['agreement_pct'].mean():.1f}%")
        print("Saved: agreement_report.csv  <- cite this number in the report, not a guess")
    return report


def main():
    import sys
    OUTPUT_DIR.mkdir(exist_ok=True)

    if len(sys.argv) > 1 and sys.argv[1] == "--agreement-report":
        compute_agreement_report(SPOTCHECK_DIR)
        return

    client = get_groq_client()
    languages = [d.name for d in INPUT_DIR.iterdir() if d.is_dir()]

    all_results = []
    for lang in languages:
        df = relabel_language(client, lang)
        if len(df):
            df.to_csv(OUTPUT_DIR / f"{lang}_relabeled.csv", index=False)
            make_spotcheck_file(df, lang)
            all_results.append(df)

    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        combined.to_csv(OUTPUT_DIR / "_all_languages_combined.csv", index=False)

        print("\n=== RELABELING SUMMARY ===")
        print(combined.groupby("language")["emotion"].value_counts())
        print(f"\nLow-confidence relabels: {(combined['llm_confidence']=='low').sum()} "
              f"/ {len(combined)} ({(combined['llm_confidence']=='low').mean()*100:.1f}%)")

    print(f"\n{'='*60}")
    print("NEXT STEPS (do not skip these):")
    print(f"{'='*60}")
    print(f"1. Open each file in {SPOTCHECK_DIR}/ and fill the verdict column")
    print(f"   for all {SPOTCHECK_SAMPLE_SIZE} rows per language.")
    print(f"2. Re-run: python relabel_emotions.py --agreement-report")
    print(f"3. Report the resulting agreement_report.csv numbers honestly in your")
    print(f"   technical writeup -- this IS your dataset quality metric.")
    print(f"4. Only proceed to fine-tuning once you've reviewed at least 2-3")
    print(f"   languages manually -- this is the human-verification step the")
    print(f"   reviewer specifically asked for.")


if __name__ == "__main__":
    main()
