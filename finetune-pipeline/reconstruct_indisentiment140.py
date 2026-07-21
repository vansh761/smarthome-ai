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

CHECKPOINT/RESUME:
  Progress is saved to indisentiment140_reconstructed/_checkpoint_done_langs.txt
  If interrupted, just re-run the same command:
      python reconstruct_indisentiment140.py
  Already-completed languages will be skipped automatically.
"""

import os
import time
import random
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Config ──────────────────────────────────────────────────────────────────

SENTIMENT140_CSV = "sentiment140.csv"   # download from kaggle.com/datasets/kazanova/sentiment140
OUTPUT_DIR       = Path("indisentiment140_reconstructed")
CHECKPOINT_FILE  = OUTPUT_DIR / "_checkpoint_done_langs.txt"   # ← NEW: tracks completed languages
SAMPLES_PER_LANG = 300                  # reduced from 1000 for faster turnaround on a proof-of-concept
                                         # scale experiment -- still defensible for this report's scope
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
LOW_RESOURCE_LANGUAGES = {"Dogri", "Bodo", "Santali", "Manipuri", "Maithili", "Kashmiri", "Konkani", "Sindhi"}

# IndicTrans2 language codes (FLORES-200 style codes used by AI4Bharat models)
INDICTRANS2_CODES = {
    "Dogri":     "doi_Deva",
    "Bodo":      "brx_Deva",
    "Santali":   "sat_Olck",
    "Manipuri":  "mni_Mtei",
    "Maithili":  "mai_Deva",
    "Kashmiri":  "kas_Deva",
    "Konkani":   "gom_Deva",
    "Sindhi":    "snd_Arab",
}

# Bhashini language codes
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

UNSUPPORTED_OR_UNRELIABLE = LOW_RESOURCE_LANGUAGES


# ── Checkpoint helpers ───────────────────────────────────────────────────────

def load_checkpoint() -> set:
    """Load the set of languages already completed in a previous run."""
    if CHECKPOINT_FILE.exists():
        done = set(CHECKPOINT_FILE.read_text().splitlines())
        done = {lang.strip() for lang in done if lang.strip()}  # clean up any blank lines
        return done
    return set()


def mark_done(lang_name: str):
    """Append a language name to the checkpoint file once it is fully saved."""
    with open(CHECKPOINT_FILE, "a") as f:
        f.write(lang_name + "\n")


# ── Data helpers ─────────────────────────────────────────────────────────────

def load_sentiment140(path: str) -> pd.DataFrame:
    cols = ["polarity", "id", "date", "query", "user", "text"]
    df = pd.read_csv(path, encoding="latin-1", names=cols)
    df = df[["polarity", "text"]]
    df = df[df["text"].str.len() > 10]
    df = df[~df["text"].str.contains(r"http|www", regex=True, na=False)]
    return df.reset_index(drop=True)


def stratified_sample(df: pd.DataFrame, n_per_class: int, seed: int) -> pd.DataFrame:
    classes = df["polarity"].unique()
    parts = []
    for c in classes:
        subset = df[df["polarity"] == c]
        take   = min(n_per_class, len(subset))
        parts.append(subset.sample(n=take, random_state=seed))
    return pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)


# ── Translation backends ─────────────────────────────────────────────────────

def translate_batch(texts: list[str], target_lang: str, batch_size: int = 25) -> list[str]:
    """Google Translate via deep-translator (free endpoint)."""
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
            time.sleep(0.3)
        print(f"  ...{min(i+batch_size, len(texts))}/{len(texts)} translated ({target_lang})")
    return results


_indictrans2_model_cache = {}

def translate_batch_indictrans2(texts: list[str], lang_name: str) -> list[str] | None:
    """Translate using AI4Bharat IndicTrans2."""
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
        batch_size = 8
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
    """Translate using Bhashini (Government of India NLP mission) API."""
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
    """IndicTrans2 → Bhashini → manual curation flag."""
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


# ── Core pipeline ────────────────────────────────────────────────────────────

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

    print(f"  Saved {lang_name}: {len(train)} train / {len(test)} test -> {lang_dir}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    random.seed(RANDOM_SEED)
    OUTPUT_DIR.mkdir(exist_ok=True)

    if not Path(SENTIMENT140_CSV).exists():
        print(f"ERROR: {SENTIMENT140_CSV} not found.")
        print("Download from: https://www.kaggle.com/datasets/kazanova/sentiment140")
        print("Place the extracted CSV in this directory and re-run.")
        return

    # ── Load checkpoint ──────────────────────────────────────────────────────
    done_langs = load_checkpoint()
    if done_langs:
        print(f"\n[RESUME MODE] Skipping {len(done_langs)} already-completed language(s): {sorted(done_langs)}")
        print(f"[RESUME MODE] Delete {CHECKPOINT_FILE} to start completely fresh.\n")
    else:
        print("\n[FRESH START] No checkpoint found -- starting from the beginning.\n")

    # ── Load & sample data ───────────────────────────────────────────────────
    print("Loading Sentiment140...")
    df_full = load_sentiment140(SENTIMENT140_CSV)
    print(f"Loaded {len(df_full)} usable tweets after cleaning.")

    df_sample = stratified_sample(df_full, n_per_class=SAMPLES_PER_LANG // 2, seed=RANDOM_SEED)
    print(f"Sampled {len(df_sample)} tweets (stratified by polarity) for per-language translation.")

    # ── Split languages into two groups ─────────────────────────────────────
    google_langs       = {k: v for k, v in INDIAN_LANGUAGES.items() if k not in LOW_RESOURCE_LANGUAGES}
    low_resource_langs = {k: v for k, v in INDIAN_LANGUAGES.items() if k in LOW_RESOURCE_LANGUAGES}

    # Filter out already-done languages from both groups
    google_langs_todo       = {k: v for k, v in google_langs.items()       if k not in done_langs}
    low_resource_langs_todo = {k: v for k, v in low_resource_langs.items() if k not in done_langs}

    summary_rows = []

    # ── Google Translate languages (concurrent) ──────────────────────────────
    if google_langs_todo:
        print(f"\n=== Translating {len(google_langs_todo)} language(s) concurrently (4 workers) ===")
        print(f"    Remaining: {sorted(google_langs_todo.keys())}")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(build_language_dataset, df_sample, name, code): name
                for name, code in google_langs_todo.items()
            }
            for future in as_completed(futures):
                lang_name = futures[future]
                try:
                    lang_df = future.result()
                except Exception as e:
                    print(f"  [error] {lang_name} failed entirely: {e}")
                    continue
                save_with_split(lang_df, lang_name)
                mark_done(lang_name)   # ← save progress immediately after each language
                summary_rows.append({
                    "language": lang_name,
                    "code": google_langs[lang_name],
                    "samples": len(lang_df),
                    "status": lang_df["translation_status"].iloc[0] if len(lang_df) else "empty",
                })
                print(f"  [done] {lang_name} finished ({len(lang_df)} samples) -- checkpoint saved.")
    else:
        print(f"\n[skip] All Google Translate languages already done.")

    # ── Low-resource languages (sequential) ─────────────────────────────────
    if low_resource_langs_todo:
        print(f"\n=== Processing {len(low_resource_langs_todo)} low-resource language(s) sequentially ===")
        print(f"    Remaining: {sorted(low_resource_langs_todo.keys())}")
        for lang_name, lang_code in low_resource_langs_todo.items():
            lang_df = build_language_dataset(df_sample, lang_name, lang_code)
            save_with_split(lang_df, lang_name)
            mark_done(lang_name)       # ← save progress immediately after each language
            summary_rows.append({
                "language": lang_name,
                "code": lang_code,
                "samples": len(lang_df),
                "status": lang_df["translation_status"].iloc[0] if len(lang_df) else "empty",
            })
            print(f"  [done] {lang_name} finished ({len(lang_df)} samples) -- checkpoint saved.")
    else:
        print(f"\n[skip] All low-resource languages already done.")

    # ── Summary ──────────────────────────────────────────────────────────────
    if summary_rows:
        summary = pd.DataFrame(summary_rows)
        # Append to summary CSV (don't overwrite previously written rows)
        summary_path = OUTPUT_DIR / "_summary.csv"
        if summary_path.exists():
            existing = pd.read_csv(summary_path)
            summary = pd.concat([existing, summary]).drop_duplicates(subset="language").reset_index(drop=True)
        summary.to_csv(summary_path, index=False)
        print("\n=== THIS RUN'S RESULTS ===")
        print(summary.to_string(index=False))

    print("\n=== ALL DONE ===")
    print(f"Languages needing manual curation: {sorted(LOW_RESOURCE_LANGUAGES)}")
    print(f"Next step: run the relabeling pipeline (relabel_emotions.py) on this output.")


if __name__ == "__main__":
    main()