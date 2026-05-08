# def insert_pdf(supabase, user_id, filename):
#     return supabase.table("pdfs").insert({
#         "user_id": user_id, 
#         "filename": filename
#     }).execute()

from datetime import datetime

def insert_pdf(supabase, user_id, filename, chat_id=None):
    """Insert PDF record into database"""
    try:
        data = {
            "user_id": user_id,
            "filename": filename,
            "upload_date": datetime.now().isoformat()
        }
        
        # chat_id bhi save karo agar diya gaya hai
        if chat_id:
            data["chat_id"] = chat_id
            
        print(f"📝 Saving PDF to DB: {data}")
        
        result = supabase.table("pdfs").insert(data).execute()
        
        print(f"✅ PDF saved: {result.data}")
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"❌ Failed to insert PDF: {e}")
        return None

def get_pdfs(supabase):
    return (
        supabase.table("pdfs") 
        .select("*") 
        .execute()
        .data
    )

def create_chat(supabase, user_id):
    import time
    from datetime import datetime, timedelta
    
    ten_seconds_ago = (datetime.now() - timedelta(seconds=10)).isoformat()
    
    recent_chats = supabase.table("chats") \
        .select("id, created_at") \
        .eq("user_id", user_id) \
        .gte("created_at", ten_seconds_ago) \
        .order("created_at", desc=True) \
        .execute()
    
    if recent_chats.data and len(recent_chats.data) > 0:
        print(f"⚠️ Returning existing chat {recent_chats.data[0]['id']} (created in last 10s)")
        return recent_chats.data[0]
    
    current_time = datetime.now().isoformat()
    res = supabase.table("chats").insert({
        "user_id": user_id,
        "created_at": current_time
    }).execute()
    
    if not res.data:
        raise Exception("Chat creation failed")
    
    print(f"✅ New chat created: {res.data[0]['id']}")
    return res.data[0]
  
def set_chat_title(supabase, chat_id, title):
    return supabase.table("chats").update({
        "title": title
    }).eq("id", chat_id).execute()

def insert_message(supabase, user_id, chat_id, role, content):
    if role not in ("user", "assistant"):
        raise ValueError("Invalid role. Must be 'user' or 'assistant'.")
    
    return supabase.table("messages").insert({
        "user_id": user_id,
        "chat_id": chat_id,
        "role": role,
        "content": content
    }).execute()

def get_user_chats(supabase):
    return (
        supabase.table("chats") 
        .select("id, title, created_at")
        .order("created_at", desc=True)
        .execute()
        .data
    )

def get_chat_messages(supabase, chat_id):
    return (
        supabase.table("messages") \
        .select("*") \
        .eq("chat_id", chat_id) \
        .order("created_at") \
        .execute()
        .data
    )

def delete_user_chats(supabase, user_id):
    """Delete all chats for a user"""
    chats = supabase.table("chats").select("id").eq("user_id", user_id).execute()
    
    for chat in chats.data:
        supabase.table("messages").delete().eq("chat_id", chat["id"]).execute()
    
    supabase.table("chats").delete().eq("user_id", user_id).execute()
    
    return {"message": "All chats deleted"}