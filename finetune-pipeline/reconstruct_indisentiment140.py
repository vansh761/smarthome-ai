"""
IndiSentiment140 Reconstruction Pipeline
==========================================
Purpose: Rebuild a dataset equivalent to Kumar, Sanasam Ranbir Singh & Nandi (NAACL 2024)
"IndiSentiment140" since no public download of their translated artifact was found.

Method (matches the published paper's methodology):
  1. Load Sentiment140 (kazanova/sentiment140, Kaggle) - 1.6M English tweets, binary labels
  2. Stratified sample down to a workable size per language (full 1.6M x 22 langs is not
     necessary or affordable for a fine-tuning experiment of this scale)
  3. Machine-translate sampled English text into each of the 22 official Indian languages
  4. Preserve original Sentiment140 polarity label (0=negative, 4=positive) through translation
  5. Save per-language CSVs with train/test split, mirroring Table 2 structure of the paper

Honest scope note for the report:
  This is a RECONSTRUCTION using the same published method, not the authors' original
  artifact. If the authors respond with their actual dataset, swap it in directly --
  this script's output format is designed to be a drop-in replacement either way.

Translation backend: deep-translator (free, wraps Google Translate web endpoint).
For production scale, swap to the official Google Cloud Translate API (paid, but stable
and won't get rate-limited) -- swap point is clearly marked below.
"""

import os
import time
import random
import pandas as pd
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────

SENTIMENT140_CSV = "sentiment140.csv"   # download from kaggle.com/datasets/kazanova/sentiment140
OUTPUT_DIR       = Path("indisentiment140_reconstructed")
SAMPLES_PER_LANG = 1000                 # paper used ~1K per language for low-resource langs (Table 2)
TRAIN_TEST_SPLIT = 0.8
RANDOM_SEED      = 42

# All 22 official Indian languages (Eighth Schedule, Indian Constitution)
# ISO 639-1 / Google Translate language codes
INDIAN_LANGUAGES = {
    "Hindi":      "hi",
    "Bengali":    "bn",
    "Telugu":     "te",
    "Marathi":    "mr",
    "Tamil":      "ta",
    "Gujarati":   "gu",
    "Kannada":    "kn",
    "Odia":       "or",
    "Malayalam":  "ml",
    "Punjabi":    "pa",
    "Assamese":   "as",
    "Maithili":   "mai",
    "Sanskrit":   "sa",
    "Urdu":       "ur",
    "Kashmiri":   "ks",
    "Konkani":    "gom",
    "Sindhi":     "sd",
    "Dogri":      "doi",     # may not be supported by Google Translate -- see fallback note
    "Manipuri":   "mni-Mtei", # Meitei script -- may need fallback
    "Bodo":       "brx",      # likely unsupported -- see fallback note
    "Santali":    "sat",      # likely unsupported -- see fallback note
    "Nepali":     "ne",
}

# Languages Google Translate does NOT reliably support as of this writing.
# The paper itself flags this kind of gap (their "% English remaining" column
# exists precisely because some low-resource languages translate poorly).
#
# FALLBACK CHAIN for these languages (tried in order, first success wins):
#   1. AI4Bharat IndicTrans2  -- purpose-built for Indian languages, best quality
#   2. Bhashini API (gov't)   -- covers some gaps IndicTrans2 doesn't (esp. Santali, Bodo)
#   3. Manual curation flag    -- if both fail, don't fake it; flag for human phrase-bank
LOW_RESOURCE_LANGUAGES = {"Dogri", "Bodo", "Santali", "Manipuri", "Maithili", "Kashmiri", "Konkani", "Sindhi"}

# IndicTrans2 language codes (FLORES-200 style codes used by AI4Bharat models)
# Reference: https://github.com/AI4Bharat/IndicTrans2
INDICTRANS2_CODES = {
    "Dogri":     "doi_Deva",
    "Bodo":      "brx_Deva",
    "Santali":   "sat_Olck",
    "Manipuri":  "mni_Mtei",
    "Maithili":  "mai_Deva",
    "Kashmiri":  "kas_Deva",   # also has kas_Arab variant -- using Devanagari here
    "Konkani":   "gom_Deva",
    "Sindhi":    "snd_Arab",
}

# Bhashini language codes (ISO 639 based, per bhashini.gov.in API docs)
BHASHINI_CODES = {
    "Dogri":     "doi",
    "Bodo":      "brx",
    "Santali":   "sat",
    "Manipuri":  "mni",
    "Maithili":  "mai",
    "Kashmiri":  "ks",
    "Konkani":   "gom",
    "Sindhi":    "sd",
}

# Kept for backward compatibility with rest of script
UNSUPPORTED_OR_UNRELIABLE = LOW_RESOURCE_LANGUAGES


def load_sentiment140(path: str) -> pd.DataFrame:
    """
    Sentiment140 columns: polarity, id, date, query, user, text
    polarity: 0 = negative, 2 = neutral (rare/absent in practice), 4 = positive
    """
    cols = ["polarity", "id", "date", "query", "user", "text"]
    df = pd.read_csv(path, encoding="latin-1", names=cols)
    df = df[["polarity", "text"]]
    df = df[df["text"].str.len() > 10]          # drop too-short/garbage tweets
    df = df[~df["text"].str.contains(r"http|www", regex=True, na=False)]  # drop link-only noise
    return df.reset_index(drop=True)


def stratified_sample(df: pd.DataFrame, n_per_class: int, seed: int) -> pd.DataFrame:
    """Equal samples per polarity class so the reconstructed set isn't skewed."""
    classes = df["polarity"].unique()
    parts = []
    for c in classes:
        subset = df[df["polarity"] == c]
        take   = min(n_per_class, len(subset))
        parts.append(subset.sample(n=take, random_state=seed))
    return pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)


def translate_batch(texts: list[str], target_lang: str, batch_size: int = 25) -> list[str]:
    """
    Translate a list of English strings to target_lang via Google Translate.
    Used for the 14 languages Google supports reliably.

    SWAP POINT for production: replace this function body with a call to
    google.cloud.translate_v2 (paid, much higher throughput, no rate-limit guessing).
    """
    from deep_translator import GoogleTranslator
    translator = GoogleTranslator(source="en", target=target_lang)
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for t in batch:
            try:
                results.append(translator.translate(t))
            except Exception as e:
                print(f"  [warn] translate failed for one item ({target_lang}): {e}")
                results.append(None)
            time.sleep(0.3)  # be polite to the free endpoint
        print(f"  ...{min(i+batch_size, len(texts))}/{len(texts)} translated ({target_lang})")
    return results


_indictrans2_model_cache = {}

def translate_batch_indictrans2(texts: list[str], lang_name: str) -> list[str] | None:
    """
    Translate using AI4Bharat IndicTrans2 -- purpose-built for Indian languages,
    significantly better quality than Google Translate for low-resource languages.

    Returns None entirely if the model/library isn't available or the language
    isn't in IndicTrans2's coverage, so the caller can fall through to Bhashini.

    Requires: pip install IndicTransToolkit torch transformers
    Model: ai4bharat/indictrans2-en-indic-1B (downloads ~2-4GB on first use)
    """
    target_code = INDICTRANS2_CODES.get(lang_name)
    if not target_code:
        return None

    try:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        from IndicTransToolkit.processor import IndicProcessor

        cache_key = "indictrans2_en_indic"
        if cache_key not in _indictrans2_model_cache:
            print(f"  [setup] Loading IndicTrans2 model (first call only, may take a minute)...")
            model_name = "ai4bharat/indictrans2-en-indic-1B"
            tokenizer  = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            model      = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)
            device     = "cuda" if torch.cuda.is_available() else "cpu"
            model      = model.to(device).eval()
            _indictrans2_model_cache[cache_key] = (tokenizer, model, IndicProcessor(inference=True), device)

        tokenizer, model, ip, device = _indictrans2_model_cache[cache_key]

        results = []
        batch_size = 8  # smaller batches -- this is a local model, not an API
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_processed = ip.preprocess_batch(batch, src_lang="eng_Latn", tgt_lang=target_code)
            inputs = tokenizer(batch_processed, truncation=True, padding="longest",
                                return_tensors="pt", max_length=256).to(device)
            with torch.no_grad():
                generated = model.generate(**inputs, max_length=256, num_beams=5)
            decoded = tokenizer.batch_decode(generated, skip_special_tokens=True)
            decoded = ip.postprocess_batch(decoded, lang=target_code)
            results.extend(decoded)
            print(f"  ...{min(i+batch_size,len(texts))}/{len(texts)} translated via IndicTrans2 ({lang_name})")

        return results

    except ImportError:
        print(f"  [skip] IndicTransToolkit not installed -- pip install IndicTransToolkit torch transformers")
        return None
    except Exception as e:
        print(f"  [warn] IndicTrans2 failed for {lang_name}: {e}")
        return None


def translate_batch_bhashini(texts: list[str], lang_name: str) -> list[str] | None:
    """
    Translate using Bhashini (Government of India NLP mission) API.
    Covers some gaps IndicTrans2 doesn't fully handle (esp. Santali, Bodo, Manipuri).

    Returns None if API key isn't configured or the call fails, so caller
    can fall through to manual curation flag.

    Requires: BHASHINI_API_KEY and BHASHINI_USER_ID env vars
    (register free at https://bhashini.gov.in -> API access)

    NOTE: Bhashini's API structure changes periodically -- verify the current
    pipeline/endpoint format at https://bhashini.gov.in/ulca/apis before relying
    on this in production. The function below uses their documented compute
    pipeline pattern as of this writing.
    """
    target_code = BHASHINI_CODES.get(lang_name)
    if not target_code:
        return None

    api_key = os.getenv("BHASHINI_API_KEY")
    user_id = os.getenv("BHASHINI_USER_ID")
    if not api_key or not user_id:
        print(f"  [skip] BHASHINI_API_KEY / BHASHINI_USER_ID not set -- skipping Bhashini for {lang_name}")
        return None

    import requests
    results = []
    try:
        for text in texts:
            payload = {
                "pipelineTasks": [{
                    "taskType": "translation",
                    "config": {
                        "language": {"sourceLanguage": "en", "targetLanguage": target_code}
                    }
                }],
                "inputData": {"input": [{"source": text}]}
            }
            headers = {
                "Authorization": api_key,
                "userID": user_id,
                "Content-Type": "application/json",
            }
            resp = requests.post(
                "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/compute",
                json=payload, headers=headers, timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            translated = data.get("pipelineResponse", [{}])[0].get("output", [{}])[0].get("target", None)
            results.append(translated)
            time.sleep(0.2)
        print(f"  ...{len(texts)} translated via Bhashini ({lang_name})")
        return results
    except Exception as e:
        print(f"  [warn] Bhashini failed for {lang_name}: {e}")
        return None


def translate_with_fallback_chain(texts: list[str], lang_name: str) -> tuple[list[str] | None, str]:
    """
    For low-resource languages: try IndicTrans2 first (best quality for Indian
    languages), then Bhashini (gov't API, covers some IndicTrans2 gaps),
    then give up cleanly so the caller flags for manual curation.

    Returns (translated_texts_or_None, method_used_string) -- the method string
    gets recorded in the output CSV so the report can honestly state which
    tool produced which language's data.
    """
    print(f"  [fallback-chain] Trying IndicTrans2 for {lang_name}...")
    result = translate_batch_indictrans2(texts, lang_name)
    if result is not None:
        return result, "indictrans2"

    print(f"  [fallback-chain] IndicTrans2 unavailable/failed, trying Bhashini for {lang_name}...")
    result = translate_batch_bhashini(texts, lang_name)
    if result is not None:
        return result, "bhashini"

    print(f"  [fallback-chain] Both tools failed/unavailable for {lang_name} -- flagging for manual curation.")
    return None, "manual_curation_needed"


def build_language_dataset(df_sample: pd.DataFrame, lang_name: str, lang_code: str) -> pd.DataFrame:
    print(f"\n=== Building {lang_name} ({lang_code}) ===")

    if lang_name in LOW_RESOURCE_LANGUAGES:
        texts = df_sample["text"].tolist()
        translated, method = translate_with_fallback_chain(texts, lang_name)

        out = df_sample.copy()
        if translated is None:
            out["text_translated"]    = None
            out["translation_status"] = "needs_manual_curation"
            out["translation_method"] = "none"
            print(f"  [result] {lang_name}: 0 samples -- needs native-speaker phrase bank")
        else:
            out["text_translated"]    = translated
            out["translation_status"] = "machine_translated"
            out["translation_method"] = method
            out = out[out["text_translated"].notna()].reset_index(drop=True)
            print(f"  [result] {lang_name}: {len(out)} samples via {method}")
        return out

    translated = translate_batch(df_sample["text"].tolist(), lang_code)
    out = df_sample.copy()
    out["text_translated"]    = translated
    out["translation_status"] = "machine_translated"
    out["translation_method"] = "google_translate"
    out = out[out["text_translated"].notna()].reset_index(drop=True)
    return out


def save_with_split(df: pd.DataFrame, lang_name: str):
    df = df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    split_idx = int(len(df) * TRAIN_TEST_SPLIT)
    train, test = df.iloc[:split_idx], df.iloc[split_idx:]

    lang_dir = OUTPUT_DIR / lang_name
    lang_dir.mkdir(parents=True, exist_ok=True)
    train.to_csv(lang_dir / "train.csv", index=False)
    test.to_csv(lang_dir / "test.csv", index=False)

    print(f"  Saved {lang_name}: {len(train)} train / {len(test)} test "
          f"-> {lang_dir}")


def main():
    random.seed(RANDOM_SEED)
    OUTPUT_DIR.mkdir(exist_ok=True)

    if not Path(SENTIMENT140_CSV).exists():
        print(f"ERROR: {SENTIMENT140_CSV} not found.")
        print("Download from: https://www.kaggle.com/datasets/kazanova/sentiment140")
        print("Place the extracted CSV in this directory and re-run.")
        return

    print("Loading Sentiment140...")
    df_full = load_sentiment140(SENTIMENT140_CSV)
    print(f"Loaded {len(df_full)} usable tweets after cleaning.")

    df_sample = stratified_sample(df_full, n_per_class=SAMPLES_PER_LANG // 2, seed=RANDOM_SEED)
    print(f"Sampled {len(df_sample)} tweets (stratified by polarity) "
          f"for per-language translation.")

    summary_rows = []
    for lang_name, lang_code in INDIAN_LANGUAGES.items():
        lang_df = build_language_dataset(df_sample, lang_name, lang_code)
        save_with_split(lang_df, lang_name)
        summary_rows.append({
            "language": lang_name,
            "code": lang_code,
            "samples": len(lang_df),
            "status": lang_df["translation_status"].iloc[0] if len(lang_df) else "empty",
        })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUTPUT_DIR / "_summary.csv", index=False)
    print("\n=== DONE ===")
    print(summary.to_string(index=False))
    print(f"\nLanguages needing manual curation (no reliable MT support):")
    print(f"  {sorted(UNSUPPORTED_OR_UNRELIABLE)}")
    print(f"\nNext step: run the relabeling pipeline (relabel_emotions.py) on this output.")


if __name__ == "__main__":
    main()
