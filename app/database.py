from supabase import create_client
from app.config import (
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    SUPABASE_SERVICE_KEY
)

def get_supabase_user_client(access_token: str):
    client = create_client(
        SUPABASE_URL,
        SUPABASE_ANON_KEY
    )
    client.postgrest.auth(access_token)
    return client

supabase_anon = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY,   
)

supabase_admin = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)
