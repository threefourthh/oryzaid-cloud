# app/services/storage.py

import base64
import uuid
from fastapi import HTTPException
from app.services.db import get_supabase


def upload_base64_image(bucket: str, base64_str: str, prefix: str):
    """
    Upload base64 image to Supabase storage and return public URL
    """

    if not base64_str:
        return None

    try:
        sb = get_supabase()

        file_bytes = base64.b64decode(base64_str)

        filename = f"{prefix}_{uuid.uuid4()}.jpg"

        sb.storage.from_(bucket).upload(
            filename,
            file_bytes,
            {"content-type": "image/jpeg"}
        )

        public_url = sb.storage.from_(bucket).get_public_url(filename)

        return public_url

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {e}")