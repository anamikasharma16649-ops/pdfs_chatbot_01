from app.database import supabase_anon

# PDFs
def insert_pdf(user_id, filename):
    return supabase_anon.table("pdfs").insert({
        "user_id": user_id, 
        "filename": filename
    }).execute()

def get_pdfs(user_id):
    return supabase_anon.table("pdfs") \
    .select("*") \
    .eq("user_id", user_id) \
    .execute().data

# create new chat
def create_chat(user_id):
    res = supabase_anon.table("chats").insert({
        "user_id": user_id
    }).execute()
    
    return res.data[0] if res.data else None

# update title (first question)
def set_chat_title(chat_id, title):
    return supabase_anon.table("chats").update({
        "title": title
    }).eq("id", chat_id).execute()

# insert message
def insert_message(user_id, chat_id, role, content):
    if role not in ("user", "assistant"):
        raise ValueError("Invalid role. Must be 'user' or 'assistant'.")

    return supabase_anon.table("messages").insert({
        "user_id": user_id,
        "chat_id": chat_id,
        "role": role,
        "content": content
    }).execute()

# get chats list (sidebar)
def get_user_chats(user_id):
    return supabase_anon.table("chats") \
        .select("id, title, created_at") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute().data

# get messages of one chat
def get_chat_messages(chat_id, user_id):
    return supabase_anon.table("messages") \
        .select("*") \
        .eq("chat_id", chat_id) \
        .eq("user_id", user_id) \
        .order("created_at") \
        .execute().data

def delete_user_chats(user_id):
    supabase_anon.table("messages").delete().eq("user_id", user_id).execute()
    supabase_anon.table("chats").delete().eq("user_id", user_id).execute()