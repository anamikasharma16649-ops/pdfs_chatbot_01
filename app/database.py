# from supabase import create_client
# from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

# supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)



from supabase import create_client
from app.config import (
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    SUPABASE_SERVICE_KEY
)


supabase_anon = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    
)


supabase_admin = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)
