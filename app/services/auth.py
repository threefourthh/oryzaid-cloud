# app/services/auth.py

import os
from fastapi import Header, HTTPException

API_KEY = os.getenv("ORYZAID_API_KEY")


def verify_api_key(x_api_key: str = Header(None)):

    if not API_KEY:
        # If not configured, skip auth
        return True

    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return True