FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.docker.txt .

RUN pip install --no-cache-dir --timeout=120 \
    fastapi uvicorn sqlalchemy aiosqlite databases \
    scikit-learn xgboost pandas numpy joblib \
    textblob chromadb pydantic python-multipart \
    requests paho-mqtt groq google-generativeai
    
RUN pip install --no-cache-dir --timeout=300 \
    torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir --timeout=300 --retries=5 \
    sentence-transformers transformers

COPY . .

RUN mkdir -p models memory_db

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
