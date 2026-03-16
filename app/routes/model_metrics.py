from fastapi import APIRouter

router = APIRouter(tags=["model"])

@router.get("/model/metrics")
def get_model_metrics():
    return {
        "precision": 0.89,
        "recall": 0.86,
        "map50": 0.91,
        "map50_95": 0.74,
        "model_version": "best.pt",
        "last_trained": "2026-03-01"
    }