from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import supabase_anon
from supabase_auth.errors import AuthApiError

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):

    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization token missing")

    token = credentials.credentials

    try:
        res = supabase_anon.auth.get_user(token)
    except AuthApiError:
        raise HTTPException(
            status_code=401,
            detail="Session expired. Please login again."
        )

    if not res or res.user is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "id": res.user.id,
        "email": res.user.email,
        "access_token": token
    }