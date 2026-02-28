import os
import time
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from uuid import UUID
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.schemas import AuthRequest, QuestionRequest
from app.database import supabase_anon, get_supabase_user_client
from app.config import (
    UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K,
    MAX_FILE_SIZE_MB, MAX_CONTEXT_CHARS, SIMILARITY_THRESHOLD
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
# ---------------- BACKGROUND PDF PROCESS ----------------
# ---------------- BACKGROUND PDF PROCESS ----------------
def process_pdf_background(file_path, filename, user_id, access_token):

    from app.pdf_reader import load_pdf
    from app.text_splitter import split_text
    from app.config import CHUNK_SIZE, CHUNK_OVERLAP
    from app.faiss_db import create_or_update_faiss
    from app.database import get_supabase_user_client
    from app.crud import insert_pdf

    # 1️⃣ Load PDF pages
    pages = load_pdf(file_path)
    if not pages:
        print("No pages extracted")
        return

    chunks_with_meta = []

    # 2️⃣ Page-aware chunking
    for page in pages:

        text = page.get("text", "").strip()
        page_number = page.get("page")

        # ✅ safety fallback
        if page_number is None:
            page_number = 0   # PyPDFLoader gives 0-index

        if not text:
            continue

        page_chunks = split_text(
            text,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        for chunk in page_chunks:
            chunks_with_meta.append({
                "text": chunk,
                "metadata": {
                    "source": filename,
                    "page": page_number + 1,  # human readable
                    "user_id": user_id
                }
            })

    if not chunks_with_meta:
        print("No chunks created")
        return

    # 3️⃣ Create / update FAISS
    create_or_update_faiss(chunks_with_meta, user_id)

    # 4️⃣ Save PDF record
    supabase = get_supabase_user_client(access_token)
    insert_pdf(supabase, user_id, filename)

    print(f"✅ Indexed {len(chunks_with_meta)} chunks")
    
MAX_RETRIES = 3   #######
RETRY_DELAY = 2     ########

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:5500"
    ],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# ------------------- STATIC FILES -------------------
# frontend folder me HTML, CSS, JS
app.mount("/static", StaticFiles(directory="frontend"), name="static")

os.makedirs(UPLOAD_DIR, exist_ok=True)

CACHE = {}
CACHE_LIMIT = 500

# ------------------- FRONTEND ROUTE -------------------
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
# @app.post("/login")
# def login(data: AuthRequest):
#     res = supabase.auth.sign_in_with_password({
#         "email": data.email,
#         "password": data.password
#     })
#     if res.session is None:
#         raise HTTPException(status_code=401, detail="Login failed")
#     return {
#         "access_token": res.session.access_token,
#         "token_type": "bearer"
#     }


@app.post("/upload-multiple")
async def upload_multiple_pdfs(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user)
):

    total_chunks = 0
    uploaded_any_pdf = False

    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(400, "Only PDF files allowed")

        if not file.filename.lower().endswith(".pdf"):
            continue
        uploaded_any_pdf = True

        user_upload_dir = os.path.join(UPLOAD_DIR, f"user_{user['id']}")
        os.makedirs(user_upload_dir, exist_ok=True) 

        file_path = os.path.join(user_upload_dir, f"{int(time.time())}_{file.filename}")


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
            user["access_token"]
        )       

        # pages = load_pdf(file_path)
        # if not pages:
        #     continue

        # full_text = "\n\n".join(
        #     p["text"] for p in pages if p["text"].strip()
        # )

        # if not full_text.strip():
        #     continue

        # chunks = split_text(
        #     full_text,
        #     chunk_size=CHUNK_SIZE,
        #     chunk_overlap=CHUNK_OVERLAP
        # )
        # if not chunks:
        #     continue

        # chunks_with_meta = [
        #     {
        #         "text": c,
        #         "metadata": {
        #             "source": file.filename,
        #             "user_id": user.id,
        #             "chunk_id": i
        #         }
        #     }
        #     for i, c in enumerate(chunks)
        # ]

        # background_tasks.add_task(
        #     create_or_update_faiss,
        #     chunks_with_meta,
        #     user.id
        # )

        # total_chunks += len(chunks)
        # supabase = get_supabase_user_client(user.access_token)
        # insert_pdf(supabase, user.id, file.filename)

    if not uploaded_any_pdf:
        raise HTTPException(status_code=400, detail="No valid PDFs uploaded")


    return {
        "message": "PDFs uploaded and indexed",
        "total_chunks": total_chunks
    }

# New Chat
@app.post("/chats")
def new_chat(user=Depends(get_current_user)):

    supabase = get_supabase_user_client(user["access_token"])

    chat = create_chat(supabase, user["id"])

    return chat

# Sidebar chats
@app.get("/chats")
def list_chats(user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])
    chat = get_user_chats(supabase)
    return chat

# Open one chat
@app.get("/chats/{chat_id}")
def open_chat(chat_id: str, user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])
    return get_chat_messages(supabase, chat_id)

# @app.post("/ask")
# def ask_question(req: QuestionRequest, user=Depends(get_current_user)):
#     # if not req.chat_id:
#     #     raise HTTPException(status_code=400, detail="chat_id required")
#     try:
#         # check if valid UUID
#         chat_uuid = UUID(req.chat_id)
#     except Exception:
#         # ❗ If invalid or "string", create new chat
#         new_chat = create_chat(user.id)
#         req.chat_id = new_chat["id"]

#     insert_message(user.id, req.chat_id, "user", req.question)

#     memory.clear()

#     previous_messages = get_chat_messages(req.chat_id, user.id)

#     for msg in previous_messages:
#         if msg["role"] == "user":
#             memory.chat_memory.add_user_message(msg["content"])
#         elif msg["role"] == "assistant":
#             memory.chat_memory.add_ai_message(msg["content"])

#     faiss_index = load_faiss_index(user.id)
#     # context_text = ""

#          # ---------------- NO INDEX ----------------
#     if not faiss_index:
#         answer = "Sorry, the requested information is not available in the provided PDF."

#         insert_message(user.id, req.chat_id, "assistant", answer)

#         return {
#             "answer": answer,
#             "used_pdf_context": False
#         }

#     # ---------------- RETRIEVE ----------------
#     results = faiss_index.similarity_search_with_score(
#         req.question,
#         k=TOP_K,
#     )

#     # Always take top K (no threshold)
#     filtered_results = [doc for doc, score in results]

#     print("---- Retrieved Chunks ----")
#     for doc in filtered_results:
#         print(doc.page_content[:300])
# #################################################  
#     if not filtered_results:
#         answer = "Sorry, the requested information is not available in the provided PDF."
    
#         insert_message(user.id, req.chat_id, "assistant", answer)

#         return {
#             "answer": answer,
#             "used_pdf_context": False
#         }  
#         # if filtered_results:  # use filtered_results instead of results
#         context_text = "\n\n".join([doc.page_content for doc in filtered_results])
#         context_text = context_text[:MAX_CONTEXT_CHARS]

#             # 🔹 debug
#         print("---- Context sent to LLM ----")
#         print(context_text[:500])  # first 500 chars only

#     # if not context_text.strip():
#     #     answer = "Sorry, the requested information is not available in the provided PDF."
#     # else:
#         answer_raw = get_llm_response(
#             question=req.question,
#             context=context_text
#         )

#         answer = format_text(answer_raw)

#     insert_message(user.id, req.chat_id, "assistant", answer)

#     # Set title if first message
#     chats = get_user_chats(user.id)
#     chat = next((c for c in chats if c["id"] == req.chat_id), None)
#     if chat and not chat.get("title"):
#         set_chat_title(req.chat_id, req.question[:40])

@app.post("/ask")
def ask_question(req: QuestionRequest, user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])


    # ---------------- HANDLE CHAT ID ----------------
    if not req.chat_id:
        new_chat = create_chat(supabase, user["id"])
        req.chat_id = new_chat["id"]
    else:
        try:
            UUID(req.chat_id)
        except:
            supabase = get_supabase_user_client(user["access_token"])
            new_chat = create_chat(supabase, user["id"])
            req.chat_id = new_chat["id"]

    insert_message(supabase, user["id"], req.chat_id, "user", req.question)

    # ---------------- MEMORY ----------------
    previous_messages = get_chat_messages(supabase, req.chat_id)
    memory = build_memory()
    for msg in previous_messages:
        if msg.get("role") == "user":
            memory.chat_memory.add_user_message(msg.get("content", ""))

        elif msg.get("role") == "assistant":
            memory.chat_memory.add_ai_message(msg.get("content", ""))
    # ---------------- LOAD INDEX ----------------
    faiss_index = load_faiss_index(user["id"])

    if not faiss_index:
        answer = "PDF is still processing. Please try again in a few seconds."

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
            "processing": True
        }
    # ---------------- RETRIEVE ----------------
    results = faiss_index.similarity_search_with_score(
        req.question,
        k=TOP_K,
    )

    # filtered_results = [
    #     doc for doc, score in results
    #     if score < SIMILARITY_THRESHOLD
    # ]
    filtered_results = [
        doc for doc, score in results
        if score < SIMILARITY_THRESHOLD
]

    print("---- Retrieved Chunks ----")
    for doc in filtered_results:
        print(doc.page_content[:300])

    if not filtered_results:
        answer = "Sorry, the requested information is not available in the provided PDF."
        insert_message(supabase, user["id"], req.chat_id, "assistant", answer)

        return {
            "answer": answer,
            "used_pdf_context": False
        }

    # ---------------- BUILD CONTEXT ----------------
    best_docs = filtered_results[:TOP_K]

# -------- CONTEXT --------
    context_text = "\n\n".join(
        doc.page_content for doc in best_docs
    )

# -------- SOURCES (ONLY USED DOCS) --------
    sources = list({
        f"{doc.metadata.get('source','Unknown')} "
        f"(Page {doc.metadata.get('page','?')})"
        for doc in best_docs
    })
    context_text = context_text[:MAX_CONTEXT_CHARS]

    print("---- Context sent to LLM ----")
    print(context_text[:500])

    
    # ---------------- LLM CALL ----------------
    
    cache_key = f"{user['id']}:{req.question.strip().lower()}"

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
            answer = "Service temporarily unavailable."

    insert_message(supabase, user["id"], req.chat_id, "assistant", answer)

    # ---------------- TITLE ----------------
    chats = get_user_chats(supabase)
    chat = next((c for c in chats if c["id"] == req.chat_id), None)

    if chat and not chat.get("title"):
        set_chat_title(supabase, req.chat_id, req.question[:40])

    # return {
    #     "answer": answer,
    #     "used_pdf_context": True
    # }
    used_pdf = True
 
    if "sorry" in answer.lower():
        used_pdf = False
    else:
        used_pdf = bool(context_text.strip())

    # return {
    #     "answer": answer,
    #     "used_pdf_context": used_pdf
    # }
    return {
    "answer": answer,
    "used_pdf_context": used_pdf,
    "sources": sources,
    "chat_id": req.chat_id
    }


@app.delete("/delete-chat-history")
def delete_chat_history(user=Depends(get_current_user)):

    supabase = get_supabase_user_client(user["access_token"])

    delete_user_chats(supabase, user["id"])

    return {"message": "All chats deleted"}

@app.get("/health")
def health():
    return {"status": "ok"}


