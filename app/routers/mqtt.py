from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.hardware.mqtt_bridge import (
    publish,
    control_device_mqtt,
    apply_room_environment_mqtt,
    get_message_log,
    get_status,
)

router = APIRouter(prefix="/mqtt", tags=["MQTT Hardware Bridge"])


class PublishRequest(BaseModel):
    topic:   str
    payload: dict


class DeviceControlRequest(BaseModel):
    room:      str
    device_id: str
    command:   dict


class RoomEnvironmentRequest(BaseModel):
    room:        str
    environment: dict


@router.get("/status")
def mqtt_status():
    """Check MQTT broker connection status."""
    return get_status()


@router.post("/publish")
def mqtt_publish(req: PublishRequest):
    """Publish any message to any MQTT topic."""
    return publish(req.topic, req.payload)


@router.post("/device/control")
def device_control(req: DeviceControlRequest):
    """
    Control a real device via MQTT.
    Works with Philips Hue, Tasmota, Shelly, Zigbee2MQTT devices.
    """
    return control_device_mqtt(req.room, req.device_id, req.command)


@router.post("/room/environment")
def room_environment(req: RoomEnvironmentRequest):
    """
    Apply full environment to a room via MQTT.
    Sends commands to lights, AC, and speaker simultaneously.
    """
    return apply_room_environment_mqtt(req.room, req.environment)


@router.get("/log")
def message_log(limit: int = 20):
    """Get recent MQTT message history."""
    return {
        "count":    min(limit, 20),
        "messages": get_message_log(limit),
    }


@router.get("/topics")
def mqtt_topics():
    """Standard MQTT topic structure used by this system."""
    return {
        "format":   "smarthome/{room}/{device}/set",
        "examples": [
            "smarthome/bedroom/lights/set",
            "smarthome/living_room/ac/set",
            "smarthome/kitchen/plug/set",
            "smarthome/office/speaker/set",
        ],
        "compatible_devices": [
            "Philips Hue (via Hue Bridge)",
            "Tasmota flashed devices",
            "Shelly smart plugs",
            "Zigbee2MQTT devices",
            "Home Assistant MQTT integration",
            "ESPHome devices",
            "Any MQTT-compatible smart device",
        ],
        "broker_setup": (
            "Install Mosquitto MQTT broker: "
            "sudo apt install mosquitto mosquitto-clients"
        ),
    }