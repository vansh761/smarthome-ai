import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_training_data(days: int = 90) -> pd.DataFrame:
    records = []
    base_date = datetime.now() - timedelta(days=days)

    for day in range(days):
        current = base_date + timedelta(days=day)
        is_weekend = current.weekday() >= 5

        for hour in range(24):
            ac_on      = 1 if 12 <= hour <= 20 else 0
            fan_on     = 1 if 8  <= hour <= 11 else 0
            washing_on = 1 if hour == 22 and not is_weekend else 0
            tv_on      = 1 if 18 <= hour <= 23 else 0
            lights_on  = 1 if (6 <= hour <= 8) or (18 <= hour <= 23) else 0

            # Night rate cheaper (₹6/unit), day rate normal (₹10/unit)
            price_per_kwh = 6.0 if (hour >= 22 or hour <= 6) else 10.0

            # Realistic power in WATTS
            power_w = 200  # base (fridge, router, standby)
            power_w += 1500 * ac_on
            power_w += 75   * fan_on
            power_w += 400  * washing_on
            power_w += 120  * tv_on
            power_w += 50   * lights_on
            power_w += random.uniform(-30, 30)

            # Convert to units (kWh) for 1 hour then multiply by price
            kwh  = power_w / 1000
            cost = kwh * price_per_kwh  # rupees per hour — realistic

            records.append({
                "hour":          hour,
                "day_of_week":   current.weekday(),
                "is_weekend":    int(is_weekend),
                "month":         current.month,
                "temperature_c": 28 + random.uniform(-3, 5),
                "ac_hours":      ac_on,
                "fan_hours":     fan_on,
                "washing_on":    washing_on,
                "tv_on":         tv_on,
                "lights_on":     lights_on,
                "price_per_kwh": price_per_kwh,
                "power_watts":   round(power_w, 1),
                "cost_rupees":   round(cost, 4),
            })

    return pd.DataFrame(records)