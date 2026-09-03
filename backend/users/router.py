from fastapi import APIRouter, Depends
import schemas
import models
from auth.dependencies import require_worker

router = APIRouter()

@router.get("/me", response_model=schemas.UserProfileResponse)
def read_users_me(current_user: models.User = Depends(require_worker)):
    return current_user
