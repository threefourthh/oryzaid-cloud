from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.services.db import get_supabase

router = APIRouter(tags=["files"])


@router.get("/files/{bucket}/{file_path:path}")
def get_file(bucket: str, file_path: str):
    try:
        sb = get_supabase()

        # Get public URL from Supabase storage
        public_url = sb.storage.from_(bucket).get_public_url(file_path)

        if not public_url:
            raise HTTPException(status_code=404, detail="File not found")

        # Redirect to the actual file
        return RedirectResponse(public_url)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File retrieval failed: {e}")