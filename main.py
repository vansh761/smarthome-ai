from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import environment
from app.routers import energy
from app.routers import sleep
from app.routers import emotion
from app.routers import memory
from app.routers import automation
from app.routers import transparency
from app.routers import hardware
from app.routers import weather
from app.routers import evaluation
from app.routers import mqtt
from app.routers import demo
from app.routers import device_timer
from app.routers import smart_devices


app = FastAPI(
    title        = "AI Smart Home Intelligence System",
    version      = "1.0.0",
    description  = (
        "Privacy-first predictive well-being platform for Indian homes. "
        "Supports 23 Indian languages, 20 health conditions, "
        "emotional memory, energy optimization, and real weather data."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = False,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

import os

@app.on_event("startup")
def startup():
    init_db()
    print("Database initialized")

    try:
        from app.memory.emotion_store import get_collection
        get_collection()
        print("Memory store ready")
    except Exception as e:
        print(f"Memory store failed: {e}")

    if not os.getenv("DISABLE_HEAVY_MODELS"):
        try:
            from app.ai.semantic_emotion import get_reference_embeddings
            get_reference_embeddings()
            print("Semantic model ready")
        except Exception as e:
            print(f"Semantic model failed: {e}")

        try:
            from app.ai.zero_shot_fallback import get_classifier
            get_classifier()
            print("Zero-shot fallback model ready")
        except Exception as e:
            print(f"Zero-shot model failed: {e}")
    else:
        print("Heavy models disabled for deployment")

    try:
        from app.hardware.device_registry import setup_virtual_home
        result = setup_virtual_home()
        print(f"Virtual home ready — {result['total_devices']} devices")
    except Exception as e:
        print(f"Hardware setup failed: {e}")


app.include_router(environment.router)
app.include_router(energy.router)
app.include_router(sleep.router)
app.include_router(emotion.router)
app.include_router(memory.router)
app.include_router(automation.router)
app.include_router(transparency.router)
app.include_router(hardware.router)
app.include_router(weather.router)
app.include_router(evaluation.router)
app.include_router(mqtt.router)
app.include_router(demo.router)
app.include_router(device_timer.router)
app.include_router(smart_devices.router)

@app.get("/")
def root():
    return {
        "status":   "AI Smart Home Intelligence System is running",
        "version":  "1.0.0",
        "modules":  [
            "environment", "energy", "sleep", "emotion",
            "memory", "automation", "transparency",
            "hardware", "weather", "evaluation",
        ],
        "docs":     "http://localhost:8000/docs",
        "health":   "http://localhost:8000/health",
    }


@app.get("/health")
def health():
    return {
        "status":  "ok",
        "version": "1.0.0",
        "phase":   "Phase 5 - Hardware + Deployment",
    }
