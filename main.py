import os
import time
import shutil
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from uuid import UUID
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.schemas import AuthRequest, QuestionRequest
from app.database import supabase_anon, get_supabase_user_client
from app.config import (
    UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K,
    MAX_FILE_SIZE_MB, MAX_CONTEXT_CHARS, SIMILARITY_THRESHOLD, FAISS_PATH
)
from fastapi import BackgroundTasks
from app.auth import get_current_user
from app.crud import (
    insert_pdf,
    create_chat,
    set_chat_title,
    insert_message,
    get_user_chats,
    get_chat_messages,
    delete_user_chats
)
from app.pdf_reader import load_pdf
from app.text_splitter import split_text
from app.faiss_db import (
    create_or_update_faiss,
    load_faiss_index,

)
from app.llm import get_llm_response, build_memory
from app.formatter import format_text

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PDF Chatbot")

def process_pdf_background(file_path, filename, user_id, access_token, chat_id):
    try:
        print("📄 Processing PDF:", filename)
        print("👤 User:", user_id)
        print("💬 Chat:", chat_id)
        from app.pdf_reader import load_pdf
        from app.text_splitter import split_text
        from app.config import CHUNK_SIZE, CHUNK_OVERLAP
        from app.faiss_db import create_or_update_faiss
        from app.database import get_supabase_user_client
        from app.crud import insert_pdf


        print("📖 Loading PDF...")
        pages = load_pdf(file_path)
        if not pages:
            print("No pages extracted")
            return

        chunks_with_meta = []


        for page in pages:
            text = page.get("text", "").strip()
            page_number = page.get("page") or 0
            if not text:
                continue
            print(f"✂️ Splitting page {page_number+1}")
            page_chunks = split_text(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

            for chunk in page_chunks:
                chunks_with_meta.append({
                    "text": chunk,
                    "metadata": {
                        "source": filename,
                        "page": page_number + 1
                    }
                })

        if not chunks_with_meta:
            print("No chunks created")
            return


        print("🧠 Creating embeddings & updating FAISS...")
        create_or_update_faiss(chunks_with_meta, user_id, chat_id)

        supabase = get_supabase_user_client(access_token)
        insert_pdf(supabase, user_id, filename)

        print("✅ Indexing complete")
        print("Chunks:", len(chunks_with_meta))
        print("Chat:", chat_id)
    except Exception as e:
        print("❌ PDF processing failed:", str(e))
    
MAX_RETRIES = 3   
RETRY_DELAY = 2     

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://localhost:8000",  
        "http://127.0.0.1:8000",  
        "http://localhost",        
        "http://127.0.0.1", 
    ],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="frontend"), name="static")
os.makedirs(UPLOAD_DIR, exist_ok=True)

CACHE = {}
CACHE_LIMIT = 500


@app.get("/")
def get_frontend():
    return FileResponse("frontend/index.html")

@app.post("/signup")
def signup(data: AuthRequest):
    for attempt in range(MAX_RETRIES):
        try:
            res = supabase_anon.auth.sign_up({
                "email": data.email,
                "password": data.password
            })
            if res.user is None:
                raise HTTPException(status_code=400, detail="Signup failed")
            return {"message": "Signup successful. Please login."}
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise HTTPException(status_code=503, detail=f"Supabase not reachable: {e}")

@app.post("/login")
def login(data: AuthRequest):
    for attempt in range(MAX_RETRIES):
        try:
            res = supabase_anon.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password
            })
            return {
                "access_token": res.session.access_token,
                "user": res.user
            }
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise HTTPException(status_code=503, detail=f"Supabase not reachable: {e}")

@app.post("/upload-multiple")
async def upload_multiple_pdfs(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user)
):

    supabase = get_supabase_user_client(user["access_token"])
    new_chat = create_chat(supabase, user["id"])
    chat_id = new_chat["id"]
   

    print("===== UPLOAD DEBUG =====")
    print("UPLOAD USER ID:", user["id"])
    print("UPLOAD CHAT ID:", chat_id)
    print("========================")

    uploaded_count = 0

    for file in files:
        if file.content_type != "application/pdf":
            continue
        if not file.filename.lower().endswith(".pdf"):
            continue

        uploaded_count += 1

        user_upload_dir = os.path.join(UPLOAD_DIR, f"user_{user['id']}")
        os.makedirs(user_upload_dir, exist_ok=True)

        file_path = os.path.join(
            user_upload_dir,
            f"{int(time.time())}_{file.filename}"
        )

        with open(file_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)

        if os.path.getsize(file_path) / (1024 * 1024) > MAX_FILE_SIZE_MB:
            continue

        background_tasks.add_task(
            process_pdf_background,
                file_path,
                file.filename,
                user["id"],
                user["access_token"],
                chat_id
        )
       
    if uploaded_count == 0:
        raise HTTPException(status_code=400, detail="No valid PDFs uploaded")

    return {
        "message": "Uploading started",
        "uploaded_files": uploaded_count,
        "chat_id": chat_id,
        "status": "processing"
    }

@app.post("/chats")
def new_chat(user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])
    chat = create_chat(supabase, user["id"])
    return chat

@app.get("/chats")
def list_chats(user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])
    chat = get_user_chats(supabase)
    return chat


@app.get("/chats/{chat_id}")
def open_chat(chat_id: str, user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])
    return get_chat_messages(supabase, chat_id)

@app.post("/ask")
def ask_question(req: QuestionRequest, user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])

    print("===== ASK DEBUG =====")
    print("ASK USER ID:", user["id"])
    print("ASK CHAT ID:", req.chat_id)
    print("=====================")

    try:
        UUID(req.chat_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid chat_id")

    import re

    history_pattern = r"what is my \d+(st|nd|rd|th) question"

    if re.search(history_pattern, req.question.lower()):

        previous_messages = get_chat_messages(supabase, req.chat_id)

        questions = [
            m["content"]
            for m in previous_messages
            if m["role"] == "user"
        ]

        try:
            number = int(re.findall(r"\d+", req.question)[0])

            if number <= len(questions):
                answer = f"Your {number} question is: {questions[number-1]}"
            else:
                answer = "That question number does not exist."

        except:
            answer = "Could not determine the question number."

        insert_message(supabase, user["id"], req.chat_id, "assistant", answer)

        return {
            "answer": answer,
            "used_pdf_context": False,
            "chat_id": req.chat_id
        }
    insert_message(supabase, user["id"], req.chat_id, "user", req.question)


    follow_up_patterns = [
        "what about",
        "its",
        "their",
        "those",
        "these",
    ]   

    question_lower = req.question.lower()

    if any(p in question_lower for p in follow_up_patterns):

        previous_messages = get_chat_messages(supabase, req.chat_id)

        last_user_questions = [
            m["content"]
            for m in previous_messages
            if m["role"] == "user"
        ]

        base_question = None

        for q in reversed(last_user_questions):
            q_lower = q.lower()

            if not any(p in q_lower for p in follow_up_patterns):
                base_question = q
                break

        if base_question:
            req.question = base_question + " " + req.question
            print("🔁 Rewritten Question:", req.question)

    previous_messages = sorted(
        get_chat_messages(supabase, req.chat_id),
        key=lambda x: x.get("created_at")
    )
    memory = build_memory()
    for msg in previous_messages:
        if msg.get("role") == "user":
            memory.chat_memory.add_user_message(msg.get("content", ""))

        elif msg.get("role") == "assistant":
            memory.chat_memory.add_ai_message(msg.get("content", ""))

    user_folder = os.path.join(FAISS_PATH, f"user_{user['id']}")

    if os.path.exists(user_folder):
        print("Available chat folders:", os.listdir(user_folder))
    else:
        print("User FAISS folder does not exist yet")

    faiss_index = load_faiss_index(user["id"], req.chat_id)

    if not faiss_index:
        answer = "No PDF found for this chat. Please upload a PDF first"

        insert_message(
            supabase,
            user["id"],
            req.chat_id,
            "assistant",
            answer
        )

        return {
            "answer": answer,
            "used_pdf_context": False,
        }

    results = faiss_index.similarity_search_with_score(
        req.question,
        k=TOP_K,
    )

    filtered_docs = [doc for doc, score in results]

    seen = set()
    unique_docs = []

    for doc in filtered_docs:
        if doc.page_content not in seen:
            unique_docs.append(doc)
            seen.add(doc.page_content)

    filtered_docs = unique_docs

    print("---- Retrieved Chunks ----")
    for doc in filtered_docs:
        print(doc.page_content[:300])

    MIN_RELEVANT_CHUNKS = 1

    if len(filtered_docs) == 0:
        answer = "Sorry, the requested information is not available in the provided PDF."
        insert_message(
            supabase, 
            user["id"], 
            req.chat_id, 
            "assistant", 
            answer
        )

        return {
            "answer": answer,
            "used_pdf_context": False,
            "chat_id": req.chat_id
        }


    best_docs = filtered_docs[:TOP_K]

    context_text = "\n\n".join(
        doc.page_content.strip()
        for doc in best_docs
        if len(doc.page_content.strip()) > 40
    )

    import re
    context_text = re.sub(r'\s+', ' ', context_text)

    context_text = context_text[:MAX_CONTEXT_CHARS]

    print("---- Context sent to LLM ----")
    print(context_text[:500])
    
    cache_key = f"{user['id']}:{req.chat_id}:{req.question.strip().lower()}"

    if cache_key in CACHE:
        answer = CACHE[cache_key]

    else:
        try:
            answer_raw = get_llm_response(
                question=req.question,
                context=context_text,
                memory=memory
            )

            answer = format_text(answer_raw)

            CACHE[cache_key] = answer

            if len(CACHE) > CACHE_LIMIT:
                CACHE.pop(next(iter(CACHE)))

        except Exception as e:
            print("LLM ERROR:", e)
            error_str = str(e).lower()
            
            # 🔥 RATE LIMIT CHECK - SIRF YAHI USER KO DIKHEGA
            if "rate limit" in error_str or "429" in error_str or "rate_limit_exceeded" in error_str:
                # Extract wait time if available
                import re
                wait_time = re.search(r"in (\d+)m(\d+\.?\d*)s", str(e))
                if wait_time:
                    minutes = wait_time.group(1)
                    seconds = wait_time.group(2)
                    answer = f"⏳ **Rate limit reached.** Please try again in **{minutes} minutes {seconds} seconds**."
                else:
                    answer = "⏳ **Rate limit reached.** Please wait a few minutes and try again."
            
            # 🔥 ALL OTHER ERRORS - SIRF GENERIC MESSAGE
            else:
                answer = "⚠️ **Service temporarily unavailable.** Please try again in a few moments."

    insert_message(supabase, user["id"], req.chat_id, "assistant", answer)

    chats = get_user_chats(supabase)
    chat = next((c for c in chats if c["id"] == req.chat_id), None)

    if chat and not chat.get("title"):
        set_chat_title(supabase, req.chat_id, req.question[:40])

    
    used_pdf = bool(filtered_docs)

    import re

    is_history = "[HISTORY_ANSWER]" in answer
    answer_clean = re.sub(r"\[.*?\]", "", answer).strip()
    answer_clean = format_text(answer_clean)

    is_sorry = (
        "not available in the provided pdf" in answer_clean.lower()
        or "not available in the provided context" in answer_clean.lower()
        or "i'm sorry" in answer_clean.lower()
        or "sorry" in answer_clean.lower()  # 👈 ADD THIS
    )

    if is_history:
        answer_final = answer
        used_pdf = False

    elif is_sorry:
        answer_final = "Sorry, the requested information is not available in the provided PDF."
        used_pdf = False

    else:
        if filtered_docs:

            pdf_names = {
                doc.metadata.get("source", "Unknown")
                for doc in best_docs
            }

            source_texts = []

            for pdf in sorted(pdf_names):
                pdf_pages = sorted({
                    str(doc.metadata.get("page", "?"))
                    for doc in best_docs
                    if doc.metadata.get("source") == pdf
                })

                source_texts.append(f"{pdf} — Pages {', '.join(pdf_pages)}")

            sources_display = "Sources:<br>" + "<br>".join(source_texts)

            answer_final = f"{answer_clean}<br><br>{sources_display}"
            used_pdf = True

        else:
            answer_final = answer_clean
            used_pdf = False


    return {
        "answer": answer_final,
        "used_pdf_context": used_pdf,
        "chat_id": req.chat_id
    }

# ========== INDIVIDUAL CHAT DELETE ==========
@app.delete("/chats/{chat_id}")
def delete_single_chat(chat_id: str, user=Depends(get_current_user)):
    """
    Delete a single chat and its associated FAISS index
    """
    supabase = get_supabase_user_client(user["access_token"])
    
    try:
        # 1. Delete chat from database
        result = supabase.table("chats").delete().eq("id", chat_id).eq("user_id", user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        # 2. Delete FAISS index for this chat
        faiss_chat_path = os.path.join(FAISS_PATH, f"user_{user['id']}", chat_id)
        if os.path.exists(faiss_chat_path):
            shutil.rmtree(faiss_chat_path)
            print(f"✅ Deleted FAISS index for chat {chat_id}")
        
        # 3. Delete associated messages from database
        supabase.table("messages").delete().eq("chat_id", chat_id).execute()
        
        # 4. Delete associated PDF records from database
        supabase.table("pdfs").delete().eq("chat_id", chat_id).execute()
        
        return {"message": "Chat deleted successfully"}
        
    except Exception as e:
        print(f"❌ Error deleting chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {str(e)}")
 
@app.delete("/delete-chat-history")
def delete_chat_history(user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])
    
    # Get all chats for this user
    chats = supabase.table("chats").select("id").eq("user_id", user["id"]).execute()
    
    # Delete all FAISS indexes
    user_faiss_path = os.path.join(FAISS_PATH, f"user_{user['id']}")
    if os.path.exists(user_faiss_path):
        shutil.rmtree(user_faiss_path)
        print(f"✅ Deleted all FAISS indexes for user {user['id']}")
    
    # Delete all messages
    supabase.table("messages").delete().eq("user_id", user["id"]).execute()
    
    # Delete all PDFs
    supabase.table("pdfs").delete().eq("user_id", user["id"]).execute()
    
    # Delete all chats
    delete_user_chats(supabase, user["id"])
    
    return {"message": "All chats deleted"}
@app.get("/health")
def health():
    return {"status": "ok"}


