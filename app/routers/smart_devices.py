from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/smart-devices", tags=["Smart Device Input"])

# ── User-friendly device categories ───────────────────────────────────────
DEVICE_CATEGORIES = {
    "cooling": {
        "label": "Cooling & Fans",
        "devices": {
            "ceiling_fan":  {"label": "Ceiling Fan",        "watts": 75,   "ask": None},
            "table_fan":    {"label": "Table Fan",           "watts": 50,   "ask": None},
            "cooler_small": {"label": "Air Cooler (Small)",  "watts": 150,  "ask": None},
            "cooler_large": {"label": "Air Cooler (Large)",  "watts": 250,  "ask": None},
            "ac_1ton":      {"label": "AC",                  "watts": None, "ask": "tons",
                            "options": {"0.75 ton": 750, "1 ton": 1000, "1.5 ton": 1500, "2 ton": 2000}},
        }
    },
    "refrigeration": {
        "label": "Kitchen — Cold Storage",
        "devices": {
            "fridge_small": {"label": "Refrigerator (Small — under 250 litres)",  "watts": 100, "ask": None},
            "fridge_medium":{"label": "Refrigerator (Medium — 250-400 litres)",   "watts": 150, "ask": None},
            "fridge_large": {"label": "Refrigerator (Large — above 400 litres)",  "watts": 200, "ask": None},
            "freezer":      {"label": "Deep Freezer",                              "watts": 300, "ask": None},
        }
    },
    "lighting": {
        "label": "Lights & Bulbs",
        "devices": {
            "led_bulb":     {"label": "LED Bulb",            "watts": None, "ask": "wattage",
                            "options": {"5W": 5, "7W": 7, "9W": 9, "12W": 12, "15W": 15, "18W": 18}},
            "tube_light":   {"label": "Tube Light / Batten", "watts": 40,   "ask": None},
            "cfl":          {"label": "CFL Bulb",             "watts": 23,   "ask": None},
            "ceiling_light":{"label": "Ceiling Light (LED Panel)", "watts": 18, "ask": None},
            "bulb_old":     {"label": "Old Filament Bulb",   "watts": 60,   "ask": None},
        }
    },
    "kitchen": {
        "label": "Kitchen Appliances",
        "devices": {
            "mixer":        {"label": "Mixer / Grinder",     "watts": 750,  "ask": None},
            "microwave":    {"label": "Microwave Oven",       "watts": 1200, "ask": None},
            "induction":    {"label": "Induction Cooktop",    "watts": 1800, "ask": None},
            "toaster":      {"label": "Toaster / Sandwich Maker", "watts": 800, "ask": None},
            "kettle":       {"label": "Electric Kettle",     "watts": 1500, "ask": None},
            "rice_cooker":  {"label": "Rice Cooker",          "watts": 700,  "ask": None},
            "oven":         {"label": "OTG / Oven",           "watts": 1500, "ask": None},
        }
    },
    "water": {
        "label": "Water Heating & Pumps",
        "devices": {
            "geyser_instant":{"label": "Geyser (Instant/Instant Gyser)", "watts": 3000, "ask": None},
            "geyser_storage":{"label": "Geyser (Storage — 15-25 litres)","watts": 2000, "ask": None},
            "water_pump":    {"label": "Water Pump / Motor",              "watts": 750,  "ask": None},
        }
    },
    "entertainment": {
        "label": "TV & Entertainment",
        "devices": {
            "tv_32":        {"label": "TV (32 inch)",         "watts": 60,   "ask": None},
            "tv_43":        {"label": "TV (43 inch)",         "watts": 100,  "ask": None},
            "tv_55":        {"label": "TV (55 inch or above)","watts": 150,  "ask": None},
            "set_top_box":  {"label": "Set Top Box / DTH",   "watts": 20,   "ask": None},
            "music_system": {"label": "Music System / Speaker", "watts": 50, "ask": None},
        }
    },
    "computers": {
        "label": "Computers & Charging",
        "devices": {
            "laptop":       {"label": "Laptop",               "watts": 65,   "ask": None},
            "desktop":      {"label": "Desktop PC",           "watts": 300,  "ask": None},
            "monitor":      {"label": "Computer Monitor",     "watts": 25,   "ask": None},
            "mobile_charge":{"label": "Mobile Phone Charger", "watts": 20,   "ask": None},
            "wifi_router":  {"label": "WiFi Router",          "watts": 10,   "ask": None},
            "printer":      {"label": "Printer",              "watts": 400,  "ask": None},
        }
    },
    "washing": {
        "label": "Washing & Ironing",
        "devices": {
            "washing_fa":   {"label": "Washing Machine (Front Load)", "watts": 800,  "ask": None},
            "washing_ta":   {"label": "Washing Machine (Top Load)",   "watts": 400,  "ask": None},
            "iron":         {"label": "Electric Iron",                 "watts": 1000, "ask": None},
            "dryer":        {"label": "Clothes Dryer",                 "watts": 2000, "ask": None},
        }
    },
    "other": {
        "label": "Other Devices",
        "devices": {
            "treadmill":    {"label": "Treadmill",            "watts": 600,  "ask": None},
            "room_heater":  {"label": "Room Heater",          "watts": 2000, "ask": None},
            "exhaust_fan":  {"label": "Exhaust Fan",          "watts": 30,   "ask": None},
            "security_cam": {"label": "Security Camera",      "watts": 10,   "ask": None},
            "custom":       {"label": "Other Device (I know the watts)", "watts": None, "ask": "watts"},
        }
    },
}


class UserDeviceInput(BaseModel):
    category:    str
    device_key:  str
    quantity:    int   = 1
    hours:       float = 8.0
    option:      Optional[str] = None  # for devices that ask tons/wattage
    custom_watts:Optional[float] = None  # for custom devices
    is_on:       bool  = True


class UserHomeRequest(BaseModel):
    devices:          List[UserDeviceInput]
    electricity_rate: Optional[float] = 6.0


@router.get("/categories")
def get_categories():
    """Get all device categories in user-friendly format."""
    return {
        cat_key: {
            "label":   cat_data["label"],
            "devices": {
                dev_key: {
                    "label":   dev["label"],
                    "watts":   dev["watts"],
                    "ask":     dev["ask"],
                    "options": dev.get("options"),
                }
                for dev_key, dev in cat_data["devices"].items()
            }
        }
        for cat_key, cat_data in DEVICE_CATEGORIES.items()
    }


@router.post("/calculate-bill")
def calculate_user_bill(req: UserHomeRequest):
    """
    Calculate bill from user-friendly device selection.
    User only picks device type — no need to know watts.
    """
    total_cost   = 0.0
    total_kwh    = 0.0
    breakdown    = []
    suggestions  = []

    for item in req.devices:
        if not item.is_on:
            continue

        cat = DEVICE_CATEGORIES.get(item.category)
        if not cat:
            continue
        dev = cat["devices"].get(item.device_key)
        if not dev:
            continue

        # Resolve watts
        if dev["ask"] == "tons" and item.option and dev.get("options"):
            watts = dev["options"].get(item.option, 1500)
            label = f"{item.option} AC"
        elif dev["ask"] == "wattage" and item.option and dev.get("options"):
            watts = dev["options"].get(item.option, 9)
            label = f"{item.option} {dev['label']}"
        elif dev["ask"] == "watts" and item.custom_watts:
            watts = item.custom_watts
            label = "Custom Device"
        elif dev["watts"]:
            watts = dev["watts"]
            label = dev["label"]
        else:
            watts = 100
            label = dev["label"]

        total_watts = watts * item.quantity
        kwh         = (total_watts * item.hours) / 1000
        cost        = kwh * (req.electricity_rate or 6.0)
        total_cost += cost
        total_kwh  += kwh

        # Smart suggestion
        if item.hours > 8 and "fan" in item.device_key:
            saving = ((item.hours - 8) * total_watts / 1000) * (req.electricity_rate or 6.0)
            suggestions.append({
                "device":      f"{item.quantity}× {label}",
                "suggestion":  "Reduce to 8 hours — fan running 24h wastes energy",
                "saving":      round(saving, 2),
            })
        elif item.hours >= 12 and "ac" in item.device_key:
            saving = ((item.hours - 8) * total_watts / 1000) * (req.electricity_rate or 6.0)
            suggestions.append({
                "device":      f"{item.quantity}× {label}",
                "suggestion":  "Use timer — limit AC to 8h, switch to fan for rest",
                "saving":      round(saving, 2),
            })

        breakdown.append({
            "device":   f"{item.quantity}× {label}",
            "watts":    total_watts,
            "hours":    item.hours,
            "kwh":      round(kwh, 3),
            "cost":     round(cost, 2),
            "monthly":  round(cost * 30, 2),
        })

    breakdown.sort(key=lambda x: x["cost"], reverse=True)
    total_saving   = sum(s["saving"] for s in suggestions)
    monthly        = round(total_cost * 30, 2)
    monthly_opt    = round((total_cost - total_saving) * 30, 2)

    return {
        "daily_cost":       round(total_cost, 2),
        "monthly_bill":     monthly,
        "optimized_bill":   monthly_opt,
        "monthly_saving":   round(total_saving * 30, 2),
        "total_kwh":        round(total_kwh, 3),
        "breakdown":        breakdown,
        "suggestions":      suggestions,
        "rate_used":        req.electricity_rate,
    }
