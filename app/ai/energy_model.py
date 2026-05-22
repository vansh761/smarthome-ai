import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor
from app.ai.energy_trainer import generate_training_data

MODEL_PATH  = Path("models/energy_model.joblib")
SCALER_PATH = Path("models/energy_scaler.joblib")

FEATURES = [
    "hour", "day_of_week", "is_weekend", "month",
    "temperature_c", "ac_hours", "fan_hours",
    "washing_on", "tv_on", "lights_on", "price_per_kwh"
]

def train_model():
    print("🔄 Generating training data...")
    df = generate_training_data(days=90)

    X = df[FEATURES]
    y = df["cost_rupees"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        verbosity=0
    )
    model.fit(X_train_s, y_train)

    preds = model.predict(X_test_s)
    mae   = mean_absolute_error(y_test, preds)
    print(f"✅ Model trained. MAE: ₹{mae:.4f} per hour")

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model,  MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"✅ Saved to {MODEL_PATH}")
    return mae


def load_model():
    if not MODEL_PATH.exists():
        print("⚠️  No model found. Training now...")
        train_model()
    return joblib.load(MODEL_PATH), joblib.load(SCALER_PATH)


def predict_hourly_cost(hour, day_of_week, is_weekend, month,
                        temperature_c, ac_hours, fan_hours,
                        washing_on, tv_on, lights_on, price_per_kwh) -> dict:
    model, scaler = load_model()

    features = np.array([[
        hour, day_of_week, is_weekend, month,
        temperature_c, ac_hours, fan_hours,
        washing_on, tv_on, lights_on, price_per_kwh
    ]])
    cost = float(model.predict(scaler.transform(features))[0])

    # Same appliances but at 11 PM (cheaper rate, no AC needed)
    features_night = features.copy()
    features_night[0][0]  = 23    # hour = 11 PM
    features_night[0][4]  = 26.0  # cooler at night
    features_night[0][5]  = 0     # AC off at night
    features_night[0][6]  = 1     # fan instead
    features_night[0][10] = 6.0   # night rate
    cost_night = float(model.predict(scaler.transform(features_night))[0])

    saving = max(0.0, cost - cost_night)

    return {
        "predicted_cost_rupees": round(cost, 2),
        "cheaper_at_night":      round(cost_night, 2),
        "potential_saving":      round(saving, 2),
        "advice": (
            f"Shift this to 11 PM to save ₹{saving:.2f}"
            if saving > 0.1 else
            "This is already an efficient time"
        )
    }


def predict_monthly_bill(daily_pattern: dict) -> dict:
    model, scaler = load_model()
    from datetime import datetime
    month = datetime.now().month

    # Read user's actual schedule (with smart defaults)
    ac_start    = daily_pattern.get("ac_start_hour",     12)
    ac_end      = daily_pattern.get("ac_end_hour",       20)
    fan_start   = daily_pattern.get("fan_start_hour",     8)
    fan_end     = daily_pattern.get("fan_end_hour",      11)
    washing_hr  = daily_pattern.get("washing_hour",      14)
    tv_start    = daily_pattern.get("tv_start_hour",     18)
    tv_end      = daily_pattern.get("tv_end_hour",       23)
    lt_start    = daily_pattern.get("lights_start_hour", 18)
    lt_end      = daily_pattern.get("lights_end_hour",   23)

    total_normal = 0.0
    hourly_costs = {}

    for hour in range(24):
        is_night = hour >= 22 or hour <= 6
        price    = 6.0 if is_night else 10.0

        # Use user's schedule
        ac_on      = 1 if ac_start  <= hour <= ac_end  else 0
        fan_on     = 1 if fan_start <= hour <= fan_end else 0
        washing    = 1 if hour == washing_hr else 0
        tv_on      = 1 if tv_start  <= hour <= tv_end  else 0
        lights_on  = 1 if lt_start  <= hour <= lt_end  else 0

        row = [
            hour,
            daily_pattern.get("day_of_week",   1),
            daily_pattern.get("is_weekend",    0),
            month,
            daily_pattern.get("temperature_c", 28.0),
            ac_on, fan_on, washing, tv_on, lights_on,
            price
        ]
        cost = float(model.predict(scaler.transform([row]))[0])
        total_normal     += cost
        hourly_costs[hour] = cost

    # Calculate saving from shifting washing to night
    washing_watts  = 400
    current_price  = 6.0 if (washing_hr >= 22 or washing_hr <= 6) else 10.0
    night_price    = 6.0
    daily_saving   = round((washing_watts / 1000) * (current_price - night_price), 2)
    monthly_saving = round(daily_saving * 30, 2)

    # Extra saving: if AC runs past 8 PM suggest reducing by 1 hour
    ac_saving = 0
    if ac_end >= 21:
        ac_saving = round((1500 / 1000) * 10.0, 2)  # 1 hour AC at peak rate

    total_saving  = monthly_saving + (ac_saving * 30)
    daily_normal  = round(total_normal, 2)
    monthly_n     = round(total_normal * 30, 2)
    monthly_opt   = round(monthly_n - total_saving, 2)
    eff_score     = round((total_saving / monthly_n) * 100, 1) if monthly_n > 0 else 0

    advice = []
    if daily_saving > 0:
        advice.append(
            f"Shift washing machine to 11 PM → save ₹{monthly_saving}/month"
        )
    else:
        advice.append("Washing machine already running at off-peak hours ✓")
    if ac_saving > 0:
        advice.append(
            f"Reduce AC by 1 hour in evening → save ₹{ac_saving * 30}/month"
        )
    advice.append("Switch off lights by 11 PM if not needed")

    return {
        "your_schedule": {
            "ac":      f"{ac_start}:00 – {ac_end}:00",
            "fan":     f"{fan_start}:00 – {fan_end}:00",
            "washing": f"{washing_hr}:00",
            "tv":      f"{tv_start}:00 – {tv_end}:00",
            "lights":  f"{lt_start}:00 – {lt_end}:00",
        },
        "daily_cost_rupees":     daily_normal,
        "monthly_bill_rupees":   monthly_n,
        "optimized_bill_rupees": monthly_opt,
        "monthly_saving_rupees": round(total_saving, 2),
        "efficiency_score":      eff_score,
        "peak_hour":             max(hourly_costs, key=hourly_costs.get),
        "cheapest_hour":         min(hourly_costs, key=hourly_costs.get),
        "top_advice":            advice
    }