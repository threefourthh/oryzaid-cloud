from fastapi import APIRouter, HTTPException
from app.services.db import get_supabase
from app.models.schemas import UploadPayload
import base64
import uuid

router = APIRouter(tags=["upload"])

def upload_to_storage(sb, bucket: str, base64_str: str | None, filename_prefix: str):
    if not base64_str:
        return None
    try:
        base64_str = base64_str.strip()
        if not base64_str:
            return None

        file_bytes = base64.b64decode(base64_str, validate=True)
        filename = f"{filename_prefix}_{uuid.uuid4()}.jpg"

        sb.storage.from_(bucket).upload(filename, file_bytes, {"content-type": "image/jpeg"})
        return sb.storage.from_(bucket).get_public_url(filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {e}")

@router.post("/upload")
def upload_detection(payload: UploadPayload):
    try:
        sb = get_supabase()
        mission = payload.mission.model_dump(mode="json")
        detections = [d.model_dump(mode="json") for d in payload.detections]
        mission_id = mission["mission_id"]

        mission["flight_path"] = mission.get("flight_path") or []
        mission["field_boundary"] = mission.get("field_boundary") or []

        sb.table("missions").upsert(mission, on_conflict="mission_id").execute()

        prepared_detections = []
        for idx, det in enumerate(detections, start=1):
            det["class_group"] = (det.get("class_group") or "").strip().lower()
            sev = (det.get("severity_level") or "").strip().lower()
            det["severity_level"] = "moderate" if sev == "medium" else "severe" if sev == "high" else sev or None

            image_url = upload_to_storage(sb, "oryzaid-storage", det.get("image_base64"), f"{mission_id}_image_{idx}")
            heatmap_url = upload_to_storage(sb, "oryzaid-storage", det.get("heatmap_base64"), f"{mission_id}_heatmap_{idx}")

            det["mission_id"] = mission_id
            if image_url: det["image_url"] = image_url
            if heatmap_url: det["heatmap_url"] = heatmap_url
            det.pop("image_base64", None)
            det.pop("heatmap_base64", None)

            prepared_detections.append(det)

        inserted = []
        if prepared_detections:
            res = sb.table("detections").insert(prepared_detections).execute()
            inserted = res.data or []

        return {"ok": True, "mission_id": mission_id, "inserted_count": len(inserted), "inserted": inserted}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")