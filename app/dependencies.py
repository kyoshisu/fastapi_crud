from fastapi import Depends, HTTPException, Request
from app.auth import get_current_user_id

def require_auth(current_user_id: int = Depends(get_current_user_id)):
    return current_user_id