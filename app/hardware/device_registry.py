from datetime import datetime
from typing import Optional

# ── Device type definitions ────────────────────────────────────────────────
DEVICE_TYPES = {
    "light":       "Controls brightness and color of lights",
    "ac":          "Controls air conditioning temperature and mode",
    "fan":         "Controls fan speed",
    "tv":          "Controls television power and volume",
    "plug":        "Controls smart plug power state",
    "thermostat":  "Controls room temperature",
    "sensor_temp": "Reads room temperature",
    "sensor_noise":"Reads ambient noise level",
    "sensor_power":"Reads power consumption",
}

# ── In-memory device registry ─────────────────────────────────────────────
# This is the Device Abstraction Layer
# Virtual devices and real devices both register here
# Rest of system only talks to this registry — never to devices directly

_devices = {}


def register_device(
    device_id:   str,
    device_type: str,
    name:        str,
    room:        str,
    is_virtual:  bool = True,
    brand:       Optional[str] = None,
    protocol:    Optional[str] = None,
) -> dict:
    """Register a device (virtual or real) in the registry."""
    device = {
        "device_id":   device_id,
        "device_type": device_type,
        "name":        name,
        "room":        room,
        "is_virtual":  is_virtual,
        "brand":       brand or "virtual",
        "protocol":    protocol or "virtual",
        "state":       get_default_state(device_type),
        "registered":  datetime.now().isoformat(),
        "last_updated":datetime.now().isoformat(),
        "online":      True,
    }
    _devices[device_id] = device
    return device


def get_default_state(device_type: str) -> dict:
    defaults = {
        "light":       {"power": "off", "brightness": 0,   "color": "neutral"},
        "ac":          {"power": "off", "temperature": 24, "mode": "cool"},
        "fan":         {"power": "off", "speed": 0},
        "tv":          {"power": "off", "volume": 0},
        "plug":        {"power": "off", "watts": 0},
        "thermostat":  {"power": "off", "target_temp": 23},
        "sensor_temp": {"value": 25.0, "unit": "celsius"},
        "sensor_noise":{"value": 40.0, "unit": "db"},
        "sensor_power":{"value": 0.0,  "unit": "watts"},
    }
    return defaults.get(device_type, {"power": "off"})


def control_device(device_id: str, command: dict) -> dict:
    """
    Send a command to any device.
    Virtual devices update state immediately.
    Real devices will send command via MQTT (Phase 5b).
    """
    if device_id not in _devices:
        return {"error": f"Device {device_id} not found"}

    device = _devices[device_id]

    # Update state
    device["state"].update(command)
    device["last_updated"] = datetime.now().isoformat()

    if device["is_virtual"]:
        return {
            "success":   True,
            "device_id": device_id,
            "name":      device["name"],
            "type":      device["device_type"],
            "virtual":   True,
            "new_state": device["state"],
            "message":   f"Virtual {device['name']} updated",
        }
    else:
        # Real device — send via MQTT (implemented in Phase 5b)
        return send_mqtt_command(device, command)


def send_mqtt_command(device: dict, command: dict) -> dict:
    """
    Send command to real hardware via MQTT.
    Currently returns simulation — real MQTT in Phase 5b.
    """
    try:
        import paho.mqtt.publish as publish
        topic   = f"smarthome/{device['room']}/{device['device_id']}/set"
        payload = str(command)
        publish.single(topic, payload, hostname="localhost")
        return {
            "success":   True,
            "device_id": device["device_id"],
            "protocol":  "mqtt",
            "topic":     topic,
            "command":   command,
        }
    except ImportError:
        return {
            "success":  True,
            "device_id":device["device_id"],
            "protocol": "mqtt_simulated",
            "command":  command,
            "note":     "paho-mqtt not installed — simulating MQTT",
        }
    except Exception as e:
        return {
            "success":  False,
            "error":    str(e),
            "device_id":device["device_id"],
        }


def get_device(device_id: str) -> dict:
    return _devices.get(device_id, {"error": "not found"})


def get_all_devices() -> dict:
    return _devices


def get_room_devices(room: str) -> list:
    return [d for d in _devices.values() if d["room"] == room]


def apply_environment_to_room(room: str, environment: dict) -> dict:
    """
    Apply an emotion-based environment to all devices in a room.
    This is what gets called when emotion engine triggers a change.
    """
    devices    = get_room_devices(room)
    results    = []
    light_level= environment.get("light_level", 60)
    light_color= environment.get("light_color", "neutral")
    temp       = environment.get("temperature_c", 23)
    music      = environment.get("music", "none")

    for device in devices:
        dtype = device["device_type"]
        cmd   = {}

        if dtype == "light":
            cmd = {
                "power":      "on" if light_level > 0 else "off",
                "brightness": light_level,
                "color":      light_color,
            }
        elif dtype == "ac":
            cmd = {
                "power":       "on" if temp < 25 else "off",
                "temperature": temp,
                "mode":        "cool" if temp < 23 else "fan",
            }
        elif dtype == "fan":
            speed = 1 if temp > 26 else (2 if temp > 28 else 0)
            cmd   = {"power": "on" if speed > 0 else "off", "speed": speed}
        elif dtype == "thermostat":
            cmd = {"power": "on", "target_temp": temp}

        if cmd:
            result = control_device(device["device_id"], cmd)
            results.append(result)

    return {
        "room":          room,
        "devices_updated": len(results),
        "environment":   environment,
        "results":       results,
    }


def setup_virtual_home():
    """
    Create a complete virtual home with all rooms and devices.
    Called on startup — provides a working simulation immediately.
    """
    rooms = {
        "bedroom":     ["light", "ac", "fan"],
        "living_room": ["light", "ac", "fan", "tv"],
        "kitchen":     ["light", "plug"],
        "office":      ["light", "ac", "fan"],
    }

    for room, device_types in rooms.items():
        for i, dtype in enumerate(device_types):
            device_id = f"{room}_{dtype}_{i+1}"
            register_device(
                device_id   = device_id,
                device_type = dtype,
                name        = f"{room.replace('_',' ').title()} {dtype.title()} {i+1}",
                room        = room,
                is_virtual  = True,
            )

    return {"setup": "complete", "total_devices": len(_devices)}