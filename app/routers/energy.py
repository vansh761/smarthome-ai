from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.ai.energy_model import predict_hourly_cost, train_model

router = APIRouter(prefix="/energy", tags=["Energy Optimizer AI"])


# ── Standard Indian home appliance wattages ────────────────────────────────
APPLIANCE_PRESETS = {
    # Cooling
    "ac_1ton":            {"watts": 1000, "label": "AC (1 Ton)",          "shiftable": False},
    "ac_1.5ton":          {"watts": 1500, "label": "AC (1.5 Ton)",        "shiftable": False},
    "ac_2ton":            {"watts": 2000, "label": "AC (2 Ton)",          "shiftable": False},
    "ceiling_fan":        {"watts": 75,   "label": "Ceiling Fan",         "shiftable": False},
    "table_fan":          {"watts": 50,   "label": "Table Fan",           "shiftable": False},
    "cooler":             {"watts": 200,  "label": "Air Cooler",          "shiftable": False},
    # Lighting
    "led_bulb_9w":        {"watts": 9,    "label": "LED Bulb (9W)",       "shiftable": False},
    "led_bulb_15w":       {"watts": 15,   "label": "LED Bulb (15W)",      "shiftable": False},
    "tube_light":         {"watts": 40,   "label": "Tube Light (40W)",    "shiftable": False},
    "cfl_bulb":           {"watts": 23,   "label": "CFL Bulb (23W)",      "shiftable": False},
    # Kitchen
    "refrigerator_small": {"watts": 100,  "label": "Refrigerator (Small)","shiftable": False},
    "refrigerator_large": {"watts": 150,  "label": "Refrigerator (Large)","shiftable": False},
    "microwave":          {"watts": 1200, "label": "Microwave",           "shiftable": True},
    "mixer_grinder":      {"watts": 750,  "label": "Mixer/Grinder",       "shiftable": False},
    "electric_kettle":    {"watts": 1500, "label": "Electric Kettle",     "shiftable": False},
    "induction_cooktop":  {"watts": 1800, "label": "Induction Cooktop",   "shiftable": False},
    "toaster":            {"watts": 800,  "label": "Toaster",             "shiftable": False},
    # Bathroom
    "geyser_instant":     {"watts": 3000, "label": "Geyser (Instant)",    "shiftable": True},
    "geyser_storage":     {"watts": 2000, "label": "Geyser (Storage)",    "shiftable": True},
    "exhaust_fan":        {"watts": 30,   "label": "Exhaust Fan",         "shiftable": False},
    # Entertainment
    "tv_32inch":          {"watts": 60,   "label": "TV (32 inch)",        "shiftable": False},
    "tv_43inch":          {"watts": 100,  "label": "TV (43 inch)",        "shiftable": False},
    "tv_55inch":          {"watts": 130,  "label": "TV (55 inch)",        "shiftable": False},
    # Laundry
    "washing_machine":    {"watts": 400,  "label": "Washing Machine",     "shiftable": True},
    "washing_machine_ha": {"watts": 800,  "label": "Washing Machine (HA)","shiftable": True},
    "iron":               {"watts": 1000, "label": "Electric Iron",       "shiftable": True},
    # Other
    "water_pump":         {"watts": 750,  "label": "Water Pump",          "shiftable": True},
    "laptop":             {"watts": 65,   "label": "Laptop",              "shiftable": False},
    "desktop_pc":         {"watts": 300,  "label": "Desktop PC",          "shiftable": False},
    "wifi_router":        {"watts": 10,   "label": "WiFi Router",         "shiftable": False},
    "set_top_box":        {"watts": 20,   "label": "Set Top Box",         "shiftable": False},
    "phone_charger":      {"watts": 20,   "label": "Phone Charger",       "shiftable": False},
    "mobile_charger":     {"watts": 20,   "label": "Mobile Charger",      "shiftable": False},
    "laptop_charger_65w": {"watts": 65,   "label": "Laptop Charger (65W)","shiftable": False},
    "laptop_charger_45w": {"watts": 45,   "label": "Laptop Charger (45W)","shiftable": False},
    "smartwatch_charger": {"watts": 5,    "label": "Smartwatch Charger",  "shiftable": False},
    "tablet_charger":     {"watts": 18,   "label": "Tablet Charger",      "shiftable": False},
    "electric_bike":      {"watts": 250,  "label": "Electric Bike Charger","shiftable": True},
    "ceiling_light_led":  {"watts": 12,   "label": "Ceiling Light (LED)", "shiftable": False},
    "standing_fan":       {"watts": 55,   "label": "Standing Fan",        "shiftable": False},
    "room_heater":        {"watts": 2000, "label": "Room Heater",         "shiftable": False},
    "aquarium_pump":      {"watts": 30,   "label": "Aquarium Pump",       "shiftable": False},
    "security_camera":    {"watts": 10,   "label": "Security Camera",     "shiftable": False},
    "music_system":       {"watts": 100,  "label": "Music System",        "shiftable": False},
    "printer":            {"watts": 400,  "label": "Printer",             "shiftable": True},
    "treadmill":          {"watts": 600,  "label": "Treadmill",           "shiftable": True},
    "dishwasher":         {"watts": 1200, "label": "Dishwasher",          "shiftable": True},
}


class Device(BaseModel):
    preset:      Optional[str]  = None   # use a preset key from above
    name:        Optional[str]  = None   # or enter custom name
    watts:       Optional[float]= None   # required only if no preset
    quantity:    int   = 1
    start_hour:  int   = 0
    end_hour:    int   = 23
    weekend_start_hour: Optional[int] = None
    weekend_end_hour:   Optional[int] = None


class UserSettings(BaseModel):
    """
    Optional user settings.
    If not provided, defaults are used.
    """
    electricity_rate_per_unit: float = 6.0    # ₹ per kWh — user can change
    custom_wattages: dict = {}                 # e.g. {"ceiling_fan": 60} overrides preset


class HomeProfile(BaseModel):
    devices:       List[Device]
    temperature_c: float = 28.0
    is_weekend:    int   = 0
    day_of_week:   int   = 1
    settings:      UserSettings = UserSettings()  # optional, has defaults


class HourlyRequest(BaseModel):
    hour:          int   = None
    day_of_week:   int   = None
    is_weekend:    int   = 0
    temperature_c: float = 28.0
    ac_hours:      int   = 1
    fan_hours:     int   = 0
    washing_on:    int   = 0
    tv_on:         int   = 1
    lights_on:     int   = 1
    price_per_kwh: float = 10.0


@router.get("/presets")
def get_presets():
    """List all available appliance presets with their standard wattages."""
    grouped = {
        "cooling":       {},
        "lighting":      {},
        "kitchen":       {},
        "bathroom":      {},
        "entertainment": {},
        "laundry":       {},
        "other":         {},
    }
    cooling_keys       = ["ac_1ton","ac_1.5ton","ac_2ton","ceiling_fan","table_fan","cooler"]
    lighting_keys      = ["led_bulb_9w","led_bulb_15w","tube_light","cfl_bulb"]
    kitchen_keys       = ["refrigerator_small","refrigerator_large","microwave",
                          "mixer_grinder","electric_kettle","induction_cooktop","toaster"]
    bathroom_keys      = ["geyser_instant","geyser_storage","exhaust_fan"]
    entertainment_keys = ["tv_32inch","tv_43inch","tv_55inch"]
    laundry_keys       = ["washing_machine","washing_machine_ha","iron"]
    other_keys         = ["water_pump","laptop","desktop_pc","wifi_router",
                          "set_top_box","phone_charger"]

    for k in cooling_keys:       grouped["cooling"][k]       = APPLIANCE_PRESETS[k]
    for k in lighting_keys:      grouped["lighting"][k]      = APPLIANCE_PRESETS[k]
    for k in kitchen_keys:       grouped["kitchen"][k]       = APPLIANCE_PRESETS[k]
    for k in bathroom_keys:      grouped["bathroom"][k]      = APPLIANCE_PRESETS[k]
    for k in entertainment_keys: grouped["entertainment"][k] = APPLIANCE_PRESETS[k]
    for k in laundry_keys:       grouped["laundry"][k]       = APPLIANCE_PRESETS[k]
    for k in other_keys:         grouped["other"][k]         = APPLIANCE_PRESETS[k]

    return grouped


@router.post("/predict/monthly")
def predict_monthly(profile: HomeProfile):
    return calculate_bill(profile)


@router.post("/predict/hourly")
def predict_hourly(req: HourlyRequest):
    now = datetime.now()
    return predict_hourly_cost(
        hour          = req.hour or now.hour,
        day_of_week   = req.day_of_week or now.weekday(),
        is_weekend    = req.is_weekend,
        month         = now.month,
        temperature_c = req.temperature_c,
        ac_hours      = req.ac_hours,
        fan_hours     = req.fan_hours,
        washing_on    = req.washing_on,
        tv_on         = req.tv_on,
        lights_on     = req.lights_on,
        price_per_kwh = req.price_per_kwh
    )


@router.post("/train")
def retrain_model():
    mae = train_model()
    return {"status": "Model retrained", "mae_rupees": round(mae, 2)}


@router.get("/status")
def model_status():
    from pathlib import Path
    trained = Path("models/energy_model.joblib").exists()
    return {
        "model_ready": trained,
        "model_type":  "XGBoost Regressor",
        "status":      "trained" if trained else "not trained"
    }

@router.get("/presets/search")
def search_preset(name: str):
    """
    Search for a device by name.
    If not found, returns custom device template to fill in manually.
    """
    name_lower = name.lower()
    matches = {
        k: v for k, v in APPLIANCE_PRESETS.items()
        if name_lower in k.lower() or name_lower in v["label"].lower()
    }
    if matches:
        return {"found": True, "matches": matches}
    return {
        "found": False,
        "message": f"'{name}' not in presets. Use custom device format below.",
        "custom_device_template": {
            "name":       name,
            "watts":      "FILL THIS IN (check label on device or manual)",
            "quantity":   1,
            "start_hour": 0,
            "end_hour":   23
        },
        "tip": "Watts is usually printed on the device label, plug, or manual."
    }


# ── Core calculation ───────────────────────────────────────────────────────
def calculate_bill(profile: HomeProfile) -> dict:
    RATE = profile.settings.electricity_rate_per_unit
    DAY_RATE   = RATE
    NIGHT_RATE = RATE

    device_breakdown  = []
    total_daily_cost  = 0.0
    total_daily_kwh   = 0.0
    optimization_tips = []

    for device in profile.devices:
        # Skip devices with 0 quantity
        if device.quantity <= 0:
            continue
        # Skip devices where start and end are both 0 (not configured)
        if device.start_hour == 0 and device.end_hour == 0:
            continue
        # Resolve watts and name from preset or manual entry
        if device.preset and device.preset in APPLIANCE_PRESETS:
            preset    = APPLIANCE_PRESETS[device.preset]
            # Check if user has overridden wattage for this preset
            custom_w  = profile.settings.custom_wattages.get(device.preset)
            watts     = custom_w if custom_w else preset["watts"]
            name      = preset["label"]
            shiftable = preset["shiftable"]
        else:
            watts     = device.watts or 100
            name      = device.name  or "Custom Device"
            shiftable = True

        # Weekend schedule override
        is_weekend = bool(profile.is_weekend)
        start = device.weekend_start_hour if (is_weekend and device.weekend_start_hour is not None) else device.start_hour
        end   = device.weekend_end_hour   if (is_weekend and device.weekend_end_hour   is not None) else device.end_hour

        # Hours per day
        hours_per_day = (end - start) if end > start else (24 - start + end)
        total_watts   = watts * device.quantity
        kwh_per_day   = (total_watts * hours_per_day) / 1000

        # Split cost into day vs night hours
        day_hrs = night_hrs = 0
        for h in range(24):
            if end > start:
                running = start <= h < end
            else:
                running = h >= start or h < end
            if running:
                if h >= 22 or h < 6:
                    night_hrs += 1
                else:
                    day_hrs   += 1

        daily_cost = (
            (total_watts * day_hrs   / 1000) * DAY_RATE +
            (total_watts * night_hrs / 1000) * NIGHT_RATE
        )

        # Only suggest shifting if device is shiftable AND runs mostly in day
        if shiftable and day_hrs > 0:
            full_night_cost = kwh_per_day * NIGHT_RATE
            saving = round(daily_cost - full_night_cost, 2)
            if saving >= 1.0:
                opt_start = 22
                opt_end   = (opt_start + hours_per_day) % 24
                optimization_tips.append({
                    "device":           f"{device.quantity}× {name}",
                    "current_schedule": f"{start}:00–{end}:00",
                    "suggestion":       f"Run at {opt_start}:00–{opt_end}:00 (off-peak)",
                    "daily_saving":     saving,
                    "monthly_saving":   round(saving * 30, 2),
                    "reason":           f"Night rate ₹{NIGHT_RATE}/unit vs day rate ₹{DAY_RATE}/unit"
                })

        device_breakdown.append({
            "device":       f"{device.quantity}× {name} ({watts}W each)",
            "hours_per_day": hours_per_day,
            "kwh_per_day":   round(kwh_per_day, 3),
            "daily_cost":    round(daily_cost, 2),
            "monthly_cost":  round(daily_cost * 30, 2),
            "schedule":      f"{start}:00 – {end}:00",
        })

        total_daily_cost += daily_cost
        total_daily_kwh  += kwh_per_day

    # Sort breakdown by highest cost
    device_breakdown.sort(key=lambda x: x["monthly_cost"], reverse=True)
    optimization_tips.sort(key=lambda x: x["monthly_saving"], reverse=True)

    total_monthly_saving = sum(t["monthly_saving"] for t in optimization_tips)
    monthly_cost         = round(total_daily_cost * 30, 2)
    optimized_cost       = round(monthly_cost - total_monthly_saving, 2)

    return {
        "settings_used": {
            "electricity_rate": f"₹{RATE}/unit",
            "custom_wattages":  profile.settings.custom_wattages or "none (using presets)"
        },
        "summary": {
            "total_devices":         sum(d.quantity for d in profile.devices if d.quantity > 0),
            "daily_kwh":             round(total_daily_kwh, 2),
            "daily_cost_rupees":     round(total_daily_cost, 2),
            "monthly_bill_rupees":   monthly_cost,
            "optimized_bill_rupees": optimized_cost,
            "monthly_saving_rupees": round(total_monthly_saving, 2),
            "efficiency_score":      round((total_monthly_saving / monthly_cost) * 100, 1) if monthly_cost > 0 else 0,
        },
        "device_breakdown":  device_breakdown,
        "optimization_tips": optimization_tips,
    }