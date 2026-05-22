from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.hardware.device_registry import (
    register_device,
    control_device,
    get_device,
    get_all_devices,
    get_room_devices,
    apply_environment_to_room,
    setup_virtual_home,
    DEVICE_TYPES,
)

router = APIRouter(prefix="/hardware", tags=["Hardware Control"])


class RegisterDeviceRequest(BaseModel):
    device_id:   str
    device_type: str
    name:        str
    room:        str
    is_virtual:  bool           = True
    brand:       Optional[str]  = None
    protocol:    Optional[str]  = None


class ControlRequest(BaseModel):
    device_id: str
    command:   dict


class ApplyEnvironmentRequest(BaseModel):
    room:        str
    environment: dict


@router.post("/setup/virtual-home")
def create_virtual_home():
    """Create a complete virtual home with all rooms and devices."""
    return setup_virtual_home()


@router.get("/devices")
def list_all_devices():
    """List all registered devices."""
    devices = get_all_devices()
    return {
        "total":   len(devices),
        "devices": list(devices.values()),
    }


@router.get("/devices/room/{room}")
def list_room_devices(room: str):
    """List all devices in a specific room."""
    devices = get_room_devices(room)
    return {
        "room":    room,
        "total":   len(devices),
        "devices": devices,
    }


@router.get("/devices/{device_id}")
def get_device_info(device_id: str):
    """Get current state of a specific device."""
    return get_device(device_id)


@router.post("/devices/register")
def register_new_device(req: RegisterDeviceRequest):
    """Register a new device — virtual or real."""
    return register_device(
        device_id   = req.device_id,
        device_type = req.device_type,
        name        = req.name,
        room        = req.room,
        is_virtual  = req.is_virtual,
        brand       = req.brand,
        protocol    = req.protocol,
    )


@router.post("/devices/control")
def control(req: ControlRequest):
    """Send a command to any device."""
    return control_device(req.device_id, req.command)


@router.post("/environment/apply")
def apply_environment(req: ApplyEnvironmentRequest):
    """Apply an emotion-based environment to all devices in a room."""
    return apply_environment_to_room(req.room, req.environment)


@router.get("/device-types")
def device_types():
    """List all supported device types."""
    return DEVICE_TYPES