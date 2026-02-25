import os
import time
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.schemas import AuthRequest, QuestionRequest
from app.database import supabase_anon
from app.config import (
    UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K,
    MAX_FILE_SIZE_MB, MAX_CONTEXT_CHARS, SIMILARITY_THRESHOLD
)
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
from app.llm import get_llm_response, memory
from app.formatter import format_text

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PDF Chatbot")
MAX_RETRIES = 3   #######
RETRY_DELAY = 2     ########

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# ------------------- STATIC FILES -------------------
# frontend folder me HTML, CSS, JS
app.mount("/static", StaticFiles(directory="frontend"), name="static")

os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user)
):

    total_chunks = 0
    uploaded_any_pdf = False

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        uploaded_any_pdf = True

        user_upload_dir = os.path.join(UPLOAD_DIR, f"user_{user.id}")
        os.makedirs(user_upload_dir, exist_ok=True) 

        file_path = os.path.join(user_upload_dir, f"{int(time.time())}_{file.filename}")


        with open(file_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)

        if os.path.getsize(file_path) / (1024 * 1024) > MAX_FILE_SIZE_MB:
            continue

        pages = load_pdf(file_path)
        if not pages:
            continue

        full_text = "\n\n".join(
            p["text"] for p in pages if p["text"].strip()
        )

        if not full_text.strip():
            continue

        chunks = split_text(
            full_text,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        if not chunks:
            continue

        chunks_with_meta = [
            {
                "text": c,
                "metadata": {
                    "source": file.filename,
                    "user_id": user.id,
                    "chunk_id": i
                }
            }
            for i, c in enumerate(chunks)
        ]

        create_or_update_faiss(
            chunks_with_meta,
            user.id
        )

        total_chunks += len(chunks)
        insert_pdf(user.id, file.filename)

    if not uploaded_any_pdf or total_chunks == 0:
        raise HTTPException(status_code=400, detail="No valid PDFs uploaded")


    return {
        "message": "PDFs uploaded and indexed",
        "total_chunks": total_chunks
    }

# New Chat
@app.post("/chats")
def new_chat(user=Depends(get_current_user)):
    chat = create_chat(user.id)
    if not chat:
        raise HTTPException(status_code=500, detail="Chat creation failed")
    return chat

# Sidebar chats
@app.get("/chats")
def list_chats(user=Depends(get_current_user)):
    return get_user_chats(user.id)

# Open one chat
@app.get("/chats/{chat_id}")
def open_chat(chat_id: str, user=Depends(get_current_user)):
    return get_chat_messages(chat_id, user.id)

@app.post("/ask")
def ask_question(req: QuestionRequest, user=Depends(get_current_user)):
    if not req.chat_id:
        raise HTTPException(status_code=400, detail="chat_id required")
    insert_message(user.id, req.chat_id, "user", req.question)

    memory.clear()

    previous_messages = get_chat_messages(req.chat_id, user.id)

    for msg in previous_messages:
        if msg["role"] == "user":
            memory.chat_memory.add_user_message(msg["content"])
        elif msg["role"] == "assistant":
            memory.chat_memory.add_ai_message(msg["content"])

    faiss_index = load_faiss_index(user.id)
    context_text = ""

    if faiss_index:
        results = faiss_index.similarity_search_with_score(
            req.question,
            k=TOP_K,
        )
        filtered_results = []

        for doc, score in results:
            if score >= SIMILARITY_THRESHOLD:  # smaller score = better match
                filtered_results.append(doc)

        results = filtered_results
# #################################
        print("---- Retrieved Chunks ----")
        for doc in results:
            print(doc.page_content[:300])
#################################################    
        if filtered_results:  # use filtered_results instead of results
            context_text = "\n\n".join([doc.page_content for doc in filtered_results])
            context_text = context_text[:MAX_CONTEXT_CHARS]

            # 🔹 debug
            print("---- Context sent to LLM ----")
            print(context_text[:500])  # first 500 chars only

    if not context_text.strip():
        answer = "Sorry, the requested information is not available in the provided PDF."
    else:
        answer_raw = get_llm_response(
            question=req.question,
            context=context_text
        )

        answer = format_text(answer_raw)

    insert_message(user.id, req.chat_id, "assistant", answer)

    # Set title if first message
    chats = get_user_chats(user.id)
    chat = next((c for c in chats if c["id"] == req.chat_id), None)
    if chat and not chat.get("title"):
        set_chat_title(req.chat_id, req.question[:40])

    if "sorry" in answer.lower():
        used_pdf = False
    else:
        used_pdf = bool(context_text.strip())

    return {
        "answer": answer,
        "used_pdf_context": used_pdf
    }

@app.delete("/delete-chat-history")
def delete_chat_history(user=Depends(get_current_user)):
    from app.crud import delete_user_chats
    delete_user_chats(user.id)
    return {"message": "All chats deleted"}


@app.get("/health")
def health():
    return {"status": "ok"}


