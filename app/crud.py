# from app.database import supabase_anon

# PDFs
def insert_pdf(supabase, user_id, filename):
    return supabase.table("pdfs").insert({
        "user_id": user_id, 
        "filename": filename
    }).execute()

def get_pdfs(supabase):
    return (
        supabase.table("pdfs") 
        .select("*") 
        .execute()
        .data
    )


# create new chat
def create_chat(supabase, user_id):
    res = supabase.table("chats").insert({
        "user_id": user_id
    }).execute()
    
    if not res.data:
        raise Exception("Chat creation failed")

    return res.data[0]


# update title (first question)
def set_chat_title(supabase, chat_id, title):
    return supabase.table("chats").update({
        "title": title
    }).eq("id", chat_id).execute()

# insert message
def insert_message(supabase, user_id, chat_id, role, content):
    if role not in ("user", "assistant"):
        raise ValueError("Invalid role. Must be 'user' or 'assistant'.")

    return supabase.table("messages").insert({
        "user_id": user_id,
        "chat_id": chat_id,
        "role": role,
        "content": content
    }).execute()

# get chats list (sidebar)
def get_user_chats(supabase):
    return (
        supabase.table("chats") 
        .select("id, title, created_at")
        .order("created_at", desc=True)
        .execute()
        .data
    )

# get messages of one chat
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
    supabase.table("messages") \
        .delete() \
        .eq("user_id", user_id) \
        .execute()

    supabase.table("chats") \
        .delete() \
        .eq("user_id", user_id) \
        .execute()