from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.services.db import get_supabase

router = APIRouter(tags=["missions"])


# =========================
# Pydantic models for sync
# =========================

class Point(BaseModel):
    lat: float
    lng: float


class MissionSync(BaseModel):
    plan_id: str
    cloud_mission_id: Optional[str] = ""
    mission_name: Optional[str] = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    area_ha: Optional[float] = 0
    location_label: Optional[str] = ""
    settings: Optional[Dict[str, Any]] = {}
    polygon: Optional[List[Point]] = []
    flight: Optional[List[Point]] = []
    home: Optional[Dict[str, Any]] = None

    # real field center
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None


class MissionStatusUpdate(BaseModel):
    mission_id: str
    mission_name: Optional[str] = None
    flight_status: str

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # GPS/global altitude
    altitude_m: Optional[float] = None

    # height above takeoff
    relative_alt_m: Optional[float] = None

    # live speed
    speed_mps: Optional[float] = None

    armed: Optional[bool] = None
    mode: Optional[str] = None
    connected: Optional[bool] = None
    source: Optional[str] = None

    voltage: Optional[float] = None
    battery_pct: Optional[float] = None
    link: Optional[str] = None

    updated_at: Optional[str] = None


# =========================
# Existing routes
# =========================

@router.get("/missions")
def list_missions(limit: int = 20):
    try:
        sb = get_supabase()

        res = (
            sb.table("missions")
            .select("*")
            .order("capture_time", desc=True)
            .limit(limit)
            .execute()
        )

        missions = res.data or []

        return {
            "ok": True,
            "count": len(missions),
            "missions": missions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list missions: {e}")


@router.get("/missions/{mission_id}")
def get_mission(mission_id: str):
    try:
        sb = get_supabase()

        mission_res = (
            sb.table("missions")
            .select("*")
            .eq("mission_id", mission_id)
            .limit(1)
            .execute()
        )

        mission_rows = mission_res.data or []
        mission = mission_rows[0] if mission_rows else None

        if not mission:
            return {
                "ok": True,
                "mission": None,
                "telemetry": None,
                "count": 0,
                "detections": []
            }

        detections_res = (
            sb.table("detections")
            .select("*")
            .eq("mission_id", mission_id)
            .order("detected_at", desc=False)
            .execute()
        )

        detections = detections_res.data or []

        telemetry = {
            "lat": mission.get("latitude"),
            "lng": mission.get("longitude"),
            "altitude_m": mission.get("altitude_m"),
            "relative_alt_m": mission.get("relative_alt_m"),
            "speed_mps": mission.get("speed_mps"),
            "armed": mission.get("armed"),
            "mode": mission.get("mode"),
            "connected": mission.get("connected"),
            "source": mission.get("source"),
            "voltage": mission.get("voltage"),
            "battery_pct": mission.get("battery_pct"),
            "link": mission.get("link"),
            "updated_at": mission.get("updated_at"),
            "status": mission.get("flight_status"),
        }

        return {
            "ok": True,
            "mission": mission,
            "telemetry": telemetry,
            "count": len(detections),
            "detections": detections
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mission: {e}")


# =========================
# Delete mission
# =========================

@router.delete("/missions/{mission_id}")
def delete_mission(mission_id: str):
    try:
        sb = get_supabase()

        sb.table("detections").delete().eq("mission_id", mission_id).execute()
        sb.table("missions").delete().eq("mission_id", mission_id).execute()

        return {
            "ok": True,
            "mission_id": mission_id,
            "message": "Mission deleted successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete mission: {e}")


# =========================
# Sync local web plan to cloud
# =========================

@router.post("/missions/sync")
def sync_mission(payload: MissionSync):
    try:
        sb = get_supabase()

        mission_id = (payload.cloud_mission_id or "").strip() or payload.plan_id.strip()

        mission_data = {
            "mission_id": mission_id,
            "mission_name": (payload.mission_name or "").strip() or mission_id,
            "field_location": payload.location_label or "",
            "area_covered_ha": float(payload.area_ha or 0),

            # real field center
            "center_lat": payload.center_lat,
            "center_lng": payload.center_lng,

            "flight_path": [p.model_dump() for p in (payload.flight or [])],
            "field_boundary": [p.model_dump() for p in (payload.polygon or [])],

            "capture_time": payload.updated_at or payload.created_at,
            "updated_at": payload.updated_at or payload.created_at,
            "flight_status": "planned",
        }

        (
            sb.table("missions")
            .upsert(mission_data, on_conflict="mission_id")
            .execute()
        )

        return {
            "ok": True,
            "mission_id": mission_id,
            "message": "Mission synced successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync mission: {e}")


# =========================
# Live flight status routes
# =========================

@router.post("/missions/status")
def update_mission_status(payload: MissionStatusUpdate):
    try:
        sb = get_supabase()

        mission_id = (payload.mission_id or "").strip()
        if not mission_id:
            raise HTTPException(status_code=400, detail="mission_id is required")

        status_time = payload.updated_at or datetime.now(timezone.utc).isoformat()

        update_data = {
            "mission_id": mission_id,
            "mission_name": (payload.mission_name or "").strip() or mission_id,

            # live status
            "flight_status": payload.flight_status,

            # live drone position
            "latitude": payload.latitude,
            "longitude": payload.longitude,

            # live altitude / height / speed
            "altitude_m": payload.altitude_m,
            "relative_alt_m": payload.relative_alt_m,
            "speed_mps": payload.speed_mps,

            # live drone state
            "armed": payload.armed,
            "mode": payload.mode,
            "connected": payload.connected,
            "source": payload.source,

            # live battery/link
            "voltage": payload.voltage,
            "battery_pct": payload.battery_pct,
            "link": payload.link,

            "updated_at": status_time,
            "capture_time": status_time,
        }

        (
            sb.table("missions")
            .upsert(update_data, on_conflict="mission_id")
            .execute()
        )

        return {
            "ok": True,
            "mission_id": mission_id,
            "flight_status": payload.flight_status,
            "message": "Mission status updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update mission status: {e}")


@router.get("/missions/status")
def get_mission_status(mission_id: str):
    try:
        sb = get_supabase()

        res = (
            sb.table("missions")
            .select("*")
            .eq("mission_id", mission_id)
            .limit(1)
            .execute()
        )

        rows = res.data or []
        mission = rows[0] if rows else None

        if not mission:
            raise HTTPException(status_code=404, detail="Mission status not found")

        return {
            "ok": True,
            "mission_id": mission_id,
            "flight_status": mission.get("flight_status"),
            "latitude": mission.get("latitude"),
            "longitude": mission.get("longitude"),
            "altitude_m": mission.get("altitude_m"),
            "relative_alt_m": mission.get("relative_alt_m"),
            "speed_mps": mission.get("speed_mps"),
            "armed": mission.get("armed"),
            "mode": mission.get("mode"),
            "connected": mission.get("connected"),
            "source": mission.get("source"),
            "voltage": mission.get("voltage"),
            "battery_pct": mission.get("battery_pct"),
            "link": mission.get("link"),
            "updated_at": mission.get("updated_at"),
            "mission": mission,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mission status: {e}")