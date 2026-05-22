import json
import threading
from datetime import datetime
from typing import Optional, Callable

_mqtt_client    = None
_connected      = False
_message_log    = []
_subscribers    = {}
BROKER_HOST     = "localhost"
BROKER_PORT     = 1883


def get_client():
    global _mqtt_client, _connected
    if _mqtt_client is not None:
        return _mqtt_client, _connected
    try:
        import paho.mqtt.client as mqtt

        client = mqtt.Client(client_id="smarthome-ai")

        def on_connect(client, userdata, flags, rc):
            global _connected
            if rc == 0:
                _connected = True
                print("MQTT broker connected")
                client.subscribe("smarthome/#")
            else:
                _connected = False
                print(f"MQTT connection failed: rc={rc}")

        def on_message(client, userdata, msg):
            entry = {
                "timestamp": datetime.now().isoformat(),
                "topic":     msg.topic,
                "payload":   msg.payload.decode("utf-8"),
            }
            _message_log.append(entry)
            if len(_message_log) > 100:
                _message_log.pop(0)

            # Call any registered subscribers
            for pattern, callback in _subscribers.items():
                if msg.topic.startswith(pattern.replace("#", "")):
                    try:
                        callback(msg.topic, msg.payload.decode("utf-8"))
                    except Exception as e:
                        print(f"Subscriber error: {e}")

        def on_disconnect(client, userdata, rc):
            global _connected
            _connected = False

        client.on_connect    = on_connect
        client.on_message    = on_message
        client.on_disconnect = on_disconnect

        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

        # Start in background thread
        thread = threading.Thread(target=client.loop_forever, daemon=True)
        thread.start()

        _mqtt_client = client
        return client, _connected

    except Exception as e:
        return None, False


def publish(topic: str, payload: dict) -> dict:
    """Publish a command to any MQTT topic."""
    client, connected = get_client()

    message = json.dumps(payload)

    if client and connected:
        result = client.publish(topic, message)
        status = "sent" if result.rc == 0 else "failed"
    else:
        # Broker not available — simulate
        status = "simulated"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "topic":     topic,
        "payload":   payload,
        "status":    status,
    }
    _message_log.append(entry)

    return {
        "topic":   topic,
        "payload": payload,
        "status":  status,
        "broker":  f"{BROKER_HOST}:{BROKER_PORT}",
    }


def control_device_mqtt(
    room:       str,
    device_id:  str,
    command:    dict,
) -> dict:
    """
    Send control command to a real device via MQTT.
    Topic format: smarthome/{room}/{device_id}/set
    """
    topic = f"smarthome/{room}/{device_id}/set"
    return publish(topic, command)


def apply_room_environment_mqtt(room: str, environment: dict) -> dict:
    """
    Send full environment change to all devices in a room via MQTT.
    This is what gets called when emotion engine changes the room.
    """
    commands = []

    light_level = environment.get("light_level", 60)
    light_color = environment.get("light_color", "neutral")
    temp        = environment.get("temperature_c", 23)
    music       = environment.get("music", "none")

    # Light command
    light_cmd = {
        "power":      "on" if light_level > 0 else "off",
        "brightness": light_level,
        "color":      light_color,
        "transition": 2,
    }
    commands.append(publish(f"smarthome/{room}/lights/set", light_cmd))

    # AC command
    ac_cmd = {
        "power":       "on" if temp < 26 else "off",
        "temperature": temp,
        "mode":        "cool" if temp < 23 else "fan_only",
    }
    commands.append(publish(f"smarthome/{room}/ac/set", ac_cmd))

    # Music command
    if music and music != "none":
        music_cmd = {"play": True, "genre": music, "volume": 30}
        commands.append(publish(f"smarthome/{room}/speaker/set", music_cmd))

    return {
        "room":        room,
        "environment": environment,
        "commands_sent": len(commands),
        "commands":    commands,
        "note": (
            "Commands published to MQTT broker. "
            "Real devices will respond if connected. "
            "Simulated if no broker running."
        ),
    }


def get_message_log(limit: int = 20) -> list:
    """Get recent MQTT messages."""
    return _message_log[-limit:]


def get_status() -> dict:
    """Get MQTT broker connection status."""
    client, connected = get_client()
    return {
        "connected":    connected,
        "broker":       f"{BROKER_HOST}:{BROKER_PORT}",
        "client_id":    "smarthome-ai",
        "messages_logged": len(_message_log),
        "note": (
            "Connected to real broker" if connected
            else "Broker not running — commands simulated locally"
        ),
    }