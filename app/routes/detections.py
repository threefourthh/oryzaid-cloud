from fastapi import APIRouter
from app.services.db import get_supabase
from app.models.schemas import DetectionsResponse

router = APIRouter(tags=["detections"])


@router.get("/missions/{mission_id}/detections", response_model=DetectionsResponse)
def get_mission_detections(mission_id: str):

    supabase = get_supabase()

    result = (
        supabase.table("detections")
        .select("*")
        .eq("mission_id", mission_id)
        .execute()
    )

    return {"detections": result.data or []}