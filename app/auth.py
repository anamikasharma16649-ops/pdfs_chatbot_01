from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import supabase_anon

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization token missing")

    token = credentials.credentials

    try:
        res = supabase_anon.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not res or res.user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return res.user
# bearer_scheme = HTTPBearer()

# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
#     token = credentials.credentials
#     res = supabase_anon.auth.get_user(token)
#     if res.user is None:
#         raise HTTPException(status_code=401, detail="Invalid token")
#     return res.user
