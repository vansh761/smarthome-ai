print("Attempting to load IndicTrans2 tokenizer...")
try:
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indictrans2-en-indic-1B", trust_remote_code=True)
    print("Tokenizer loaded successfully!")
except Exception as e:
    print(f"FAILED to load tokenizer: {type(e).__name__}: {e}")