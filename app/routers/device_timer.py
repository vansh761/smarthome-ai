from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/device-timer", tags=["Device Timer & Bill Simulator"])


class TimerDevice(BaseModel):
    name:        str
    watts:       float
    quantity:    int   = 1
    hours:       float        # how many hours to simulate
    is_on:       bool  = True


class TimerRequest(BaseModel):
    devices:           List[TimerDevice]
    electricity_rate:  float = 6.0
    apply_suggestions: bool  = False


@router.post("/simulate")
def simulate_usage(req: TimerRequest):
    """
    Simulate device usage for any number of hours.
    Shows bill before and after applying AI suggestions.
    No need to wait — calculates instantly.
    """
    total_cost    = 0.0
    total_kwh     = 0.0
    device_details= []
    suggestions   = []

    for device in req.devices:
        if not device.is_on:
            continue

        kwh      = (device.watts * device.quantity * device.hours) / 1000
        cost     = kwh * req.electricity_rate
        total_cost += cost
        total_kwh  += kwh

        # Generate suggestion
        suggestion = None
        if device.hours > 8 and device.name.lower() in ["fan", "ceiling fan"]:
            optimal_hours = 8
            saving        = ((device.hours - optimal_hours) * device.watts * device.quantity / 1000) * req.electricity_rate
            suggestion    = {
                "device":          f"{device.quantity}× {device.name}",
                "issue":           f"Running for {device.hours}h is excessive",
                "recommendation":  f"Reduce to {optimal_hours}h",
                "saving_rupees":   round(saving, 2),
                "severity":        "medium",
            }
        elif device.hours > 12 and device.name.lower() in ["ac", "air conditioner", "ac 1.5ton", "ac 1ton"]:
            optimal_hours = 8
            saving        = ((device.hours - optimal_hours) * device.watts * device.quantity / 1000) * req.electricity_rate
            suggestion    = {
                "device":          f"{device.quantity}× {device.name}",
                "issue":           f"AC running {device.hours}h continuously is very costly",
                "recommendation":  f"Use timer — limit to {optimal_hours}h, use fan for remaining hours",
                "saving_rupees":   round(saving, 2),
                "severity":        "high",
            }
        elif device.hours > 16 and device.watts > 100:
            optimal_hours = device.hours * 0.6
            saving        = ((device.hours - optimal_hours) * device.watts * device.quantity / 1000) * req.electricity_rate
            suggestion    = {
                "device":          f"{device.quantity}× {device.name}",
                "issue":           f"High wattage device running {device.hours}h",
                "recommendation":  f"Reduce usage to {round(optimal_hours)}h",
                "saving_rupees":   round(saving, 2),
                "severity":        "medium",
            }

        if suggestion:
            suggestions.append(suggestion)

        device_details.append({
            "device":     f"{device.quantity}× {device.name} ({device.watts}W)",
            "hours":      device.hours,
            "kwh":        round(kwh, 3),
            "cost":       round(cost, 2),
            "is_on":      device.is_on,
        })

    # Optimized cost
    total_saving   = sum(s["saving_rupees"] for s in suggestions)
    optimized_cost = round(total_cost - total_saving, 2)

    # Scale to monthly
    monthly_cost      = round(total_cost * 30, 2)
    monthly_optimized = round(optimized_cost * 30, 2)
    monthly_saving    = round(total_saving * 30, 2)

    return {
        "simulation": {
            "total_hours":        max(d.hours for d in req.devices if d.is_on) if req.devices else 0,
            "total_kwh":          round(total_kwh, 3),
            "current_cost":       round(total_cost, 2),
            "optimized_cost":     optimized_cost,
            "saving":             round(total_saving, 2),
            "electricity_rate":   req.electricity_rate,
        },
        "monthly_projection": {
            "current_bill":       monthly_cost,
            "optimized_bill":     monthly_optimized,
            "monthly_saving":     monthly_saving,
            "efficiency_pct":     round((monthly_saving / monthly_cost * 100), 1) if monthly_cost > 0 else 0,
        },
        "device_breakdown": sorted(device_details, key=lambda x: x["cost"], reverse=True),
        "ai_suggestions":   suggestions,
        "verdict": (
            f"Running these devices for the simulated period costs ₹{round(total_cost,2)}. "
            f"With AI suggestions you save ₹{round(total_saving,2)} "
            f"(₹{monthly_saving}/month)."
        ),
    }


@router.get("/presets")
def timer_presets():
    """Common device usage scenarios for quick testing."""
    return {
        "scenarios": [
            {
                "name":    "Fan running 20 hours",
                "devices": [{"name": "Ceiling Fan", "watts": 75, "quantity": 1, "hours": 20, "is_on": True}],
                "note":    "Tests excessive fan usage suggestion",
            },
            {
                "name":    "AC all day",
                "devices": [{"name": "AC 1.5ton", "watts": 1500, "quantity": 1, "hours": 14, "is_on": True}],
                "note":    "Tests AC overuse suggestion",
            },
            {
                "name":    "Full home overnight",
                "devices": [
                    {"name": "Fan",          "watts": 75,  "quantity": 3, "hours": 8,  "is_on": True},
                    {"name": "AC",           "watts": 1500,"quantity": 1, "hours": 8,  "is_on": True},
                    {"name": "Refrigerator", "watts": 150, "quantity": 1, "hours": 8,  "is_on": True},
                    {"name": "LED Bulb",     "watts": 9,   "quantity": 4, "hours": 6,  "is_on": True},
                ],
                "note": "Typical overnight usage",
            },
        ]
    }
