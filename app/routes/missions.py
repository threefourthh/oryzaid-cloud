from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.db import get_supabase

router = APIRouter(tags=["missions"])

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

@router.get("/missions")
def list_missions(limit: int = 20):
    try:
        sb = get_supabase()
        res = sb.table("missions").select("*").order("capture_time", desc=True).limit(limit).execute()
        missions = res.data or []
        return {"ok": True, "count": len(missions), "missions": missions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list missions: {e}")

@router.get("/missions/{mission_id}")
def get_mission(mission_id: str):
    try:
        sb = get_supabase()
        mission_res = sb.table("missions").select("*").eq("mission_id", mission_id).limit(1).execute()
        mission_rows = mission_res.data or []
        mission = mission_rows[0] if mission_rows else None

        if not mission:
            return {"ok": True, "mission": None, "count": 0, "detections": []}

        detections_res = sb.table("detections").select("*").eq("mission_id", mission_id).order("detected_at", desc=False).execute()
        detections = detections_res.data or []

        return {"ok": True, "mission": mission, "count": len(detections), "detections": detections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mission: {e}")

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
            "flight_path": [p.model_dump() for p in (payload.flight or [])],
            "field_boundary": [p.model_dump() for p in (payload.polygon or [])],
            "capture_time": payload.updated_at or payload.created_at,
            "mission_status": "planned",
            "notes": "Created from web planner sync",
        }

        sb.table("missions").upsert(mission_data, on_conflict="mission_id").execute()
        return {"ok": True, "mission_id": mission_id, "message": "Mission synced successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync mission: {e}")