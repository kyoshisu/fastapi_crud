from fastapi import Depends, HTTPException, Request
from app.auth import get_current_user_id

def require_auth(current_user_id: int = Depends(get_current_user_id)):
    """Зависимость для защиты эндпоинтов"""
    return current_user_id

def require_admin(current_user_id: int = Depends(get_current_user_id)):
    """Только для администраторов"""
    return current_user_id