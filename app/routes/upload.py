from fastapi import APIRouter, HTTPException
from app.services.db import get_supabase
from app.models.schemas import UploadPayload
import base64
import uuid
from datetime import datetime, timezone

router = APIRouter(tags=["upload"])


def upload_to_storage(sb, bucket: str, base64_str: str | None, filename_prefix: str):
    """
    Upload optional base64 image to Supabase Storage.
    Returns public URL if uploaded, otherwise None.
    """
    if not base64_str:
        return None

    try:
        base64_str = base64_str.strip()
        if not base64_str:
            return None

        file_bytes = base64.b64decode(base64_str, validate=True)
        filename = f"{filename_prefix}_{uuid.uuid4()}.jpg"

        sb.storage.from_(bucket).upload(
            filename,
            file_bytes,
            {"content-type": "image/jpeg"}
        )

        return sb.storage.from_(bucket).get_public_url(filename)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {e}")


@router.post("/upload")
def upload_detection(payload: UploadPayload):
    try:
        sb = get_supabase()

        # -----------------------------
        # 1) Prepare mission
        # -----------------------------
        mission = payload.mission.model_dump(mode="json")
        detections = [d.model_dump(mode="json") for d in payload.detections]
        telemetry = payload.telemetry.model_dump(mode="json") if payload.telemetry else {}

        mission_id = mission["mission_id"]

        # Safety defaults for JSON geometry fields
        mission["flight_path"] = mission.get("flight_path") or []
        mission["field_boundary"] = mission.get("field_boundary") or []

        # -----------------------------
        # 1.1) Merge telemetry into mission row
        # since your missions table now stores live monitor fields
        # -----------------------------
        mission["latitude"] = telemetry.get("latitude")
        mission["longitude"] = telemetry.get("longitude")
        mission["altitude_m"] = telemetry.get("altitude_m")
        mission["relative_alt_m"] = telemetry.get("relative_alt_m")
        mission["speed_mps"] = telemetry.get("speed_mps")

        mission["armed"] = telemetry.get("armed")
        mission["mode"] = telemetry.get("mode")
        mission["connected"] = telemetry.get("connected")
        mission["source"] = telemetry.get("source")

        mission["voltage"] = telemetry.get("voltage")
        mission["battery_pct"] = telemetry.get("battery_pct")
        mission["link"] = telemetry.get("link")

        mission["updated_at"] = telemetry.get("updated_at") or datetime.now(timezone.utc).isoformat()

        # Optional: infer flight_status if not directly included
        # If later you add flight_status to telemetry schema, you can replace this
        mission["flight_status"] = (
            "in_progress" if telemetry.get("connected") else "planned"
        )

        # Upsert mission first
        sb.table("missions").upsert(
            mission,
            on_conflict="mission_id"
        ).execute()

        # -----------------------------
        # 2) Prepare detections
        # -----------------------------
        prepared_detections = []

        for idx, det in enumerate(detections, start=1):
            det["class_group"] = (det.get("class_group") or "").strip().lower()

            sev = (det.get("severity_level") or "").strip().lower()
            if sev == "medium":
                sev = "moderate"
            if sev == "high":
                sev = "severe"
            det["severity_level"] = sev or None

            image_url = upload_to_storage(
                sb,
                "missions",
                det.get("image_base64"),
                f"{mission_id}_image_{idx}"
            )

            heatmap_url = upload_to_storage(
                sb,
                "missions",
                det.get("heatmap_base64"),
                f"{mission_id}_heatmap_{idx}"
            )

            det["mission_id"] = mission_id

            if image_url:
                det["image_url"] = image_url
            if heatmap_url:
                det["heatmap_url"] = heatmap_url

            det.pop("image_base64", None)
            det.pop("heatmap_base64", None)

            prepared_detections.append(det)

        # -----------------------------
        # 3) Insert detections
        # -----------------------------
        inserted = []

        if prepared_detections:
            res = sb.table("detections").insert(prepared_detections).execute()
            inserted = res.data or []

        return {
            "ok": True,
            "mission_id": mission_id,
            "inserted_count": len(inserted),
            "inserted": inserted,
            "telemetry_saved": {
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
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")