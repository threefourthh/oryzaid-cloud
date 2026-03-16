from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal
from datetime import datetime

class LatLngPoint(BaseModel):
    lat: float
    lng: float

class DetectionIn(BaseModel):
    class_name: str
    class_group: Literal["disease", "pest"]
    normalized_label: Optional[str] = None
    confidence: Optional[float] = None
    severity_level: Optional[Literal["low", "moderate", "severe"]] = None
    affected_area_percent: Optional[float] = None
    latitude: float
    longitude: float
    altitude_m: Optional[float] = None
    image_url: Optional[str] = None
    heatmap_url: Optional[str] = None
    image_base64: Optional[str] = None
    heatmap_base64: Optional[str] = None
    detected_at: Optional[datetime] = None

class MissionIn(BaseModel):
    mission_id: str
    mission_name: Optional[str] = None
    field_location: Optional[str] = None
    area_covered_ha: Optional[float] = None
    flight_altitude_m: Optional[float] = None
    drone_id: Optional[str] = None
    operator_name: Optional[str] = None
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    capture_time: Optional[datetime] = None
    started_at: Optional[datetime] = None
    flight_path: List[LatLngPoint] = Field(default_factory=list)
    field_boundary: List[LatLngPoint] = Field(default_factory=list)

class UploadPayload(BaseModel):
    mission: MissionIn
    detections: List[DetectionIn]
