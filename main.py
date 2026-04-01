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

# ========== PROCESSING STATUS TRACKING ==========
from datetime import datetime
import threading

processing_status = {}
status_lock = threading.Lock()

app = FastAPI(title="PDF Chatbot")

def process_pdf_background(file_path, filename, user_id, access_token, chat_id):
    status_key = f"{user_id}:{chat_id}"
    
    try:
        # Initialize status
        with status_lock:
            processing_status[status_key] = {
                "status": "loading",
                "progress": 0,
                "message": "Loading PDF...",
                "start_time": datetime.now().isoformat(),
                "filename": filename
            }
        
        print("📄 Processing PDF:", filename)
        print("👤 User:", user_id)
        print("💬 Chat:", chat_id)
        from app.pdf_reader import load_pdf
        from app.text_splitter import split_text
        from app.config import CHUNK_SIZE, CHUNK_OVERLAP
        from app.faiss_db import create_or_update_faiss
        from app.database import get_supabase_user_client
        from app.crud import insert_pdf
        from app.config import get_chunk_settings


        print("📖 Loading PDF...")
        pages = load_pdf(file_path)
        if not pages:
            with status_lock:
                processing_status[status_key] = {
                    "status": "failed",
                    "message": "No pages extracted",
                    "error": "PDF has no readable text"
                }
            print("No pages extracted")
            return

        print(f"✅ Extracted {len(pages)} pages from PDF")
        
        total_pages = len(pages)

        chunk_size, chunk_overlap = get_chunk_settings(total_pages)
        print(f"📊 Using chunk_size={chunk_size}, overlap={chunk_overlap} for {total_pages} pages")
        with status_lock:
            processing_status[status_key]["total_pages"] = len(pages)
            processing_status[status_key]["message"] = f"Processing {len(pages)} pages..."
        
        # 🔥 DEBUG: Pehle page ka content print karo
        if pages and len(pages) > 0:
            print(f"First page preview: {pages[0]['text'][:200]}...")

        chunks_with_meta = []
        total_pages = len(pages)

        for page_idx, page in enumerate(pages):
            text = page.get("text", "").strip()
            page_number = page.get("page") or 0
            if not text:
                print(f"⚠️ Page {page_number + 1} has no text, skipping")
                continue
            print(f"✂️ Splitting page {page_number+1}")
            page_chunks = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

            for i, chunk in enumerate(page_chunks):
                chunks_with_meta.append({
                    "text": chunk,
                    "metadata": {
                        "source": filename,
                        "page": page_number + 1
                    }
                })
            print(f"   Created {len(page_chunks)} chunks from page {page_number + 1}")
            
            # Update progress
            progress = int((page_idx + 1) / total_pages * 40)  # 40% for splitting
            with status_lock:
                if status_key in processing_status:
                    processing_status[status_key]["progress"] = progress
                    processing_status[status_key]["message"] = f"Splitting pages... ({page_idx + 1}/{total_pages})"

        if not chunks_with_meta:
            with status_lock:
                processing_status[status_key] = {
                    "status": "failed",
                    "message": "No chunks created",
                    "error": "No text could be extracted"
                }
            print("No chunks created")
            return

        print(f"🧠 Total chunks: {len(chunks_with_meta)}")
        
        with status_lock:
            processing_status[status_key]["status"] = "embedding"
            processing_status[status_key]["message"] = f"Creating embeddings ({len(chunks_with_meta)} chunks)..."
            processing_status[status_key]["progress"] = 50
        
        print("🧠 Creating embeddings & updating FAISS...")
        create_or_update_faiss(chunks_with_meta, user_id, chat_id)

        with status_lock:
            processing_status[status_key]["progress"] = 90
            processing_status[status_key]["message"] = "Saving to database..."

        supabase = get_supabase_user_client(access_token)
        insert_pdf(supabase, user_id, filename)

        # Mark as complete
        with status_lock:
            processing_status[status_key] = {
                "status": "completed",
                "progress": 100,
                "message": "Ready to answer questions!",
                "completed_time": datetime.now().isoformat(),
                "filename": filename,
                "chunks": len(chunks_with_meta),
                "pages": len(pages)
            }

        print("✅ Indexing complete")
        print(f"✅ PDF processed successfully: {filename}")
    except Exception as e:
        print("❌ PDF processing failed:", str(e))
        import traceback
        traceback.print_exc()
        with status_lock:
            processing_status[status_key] = {
                "status": "failed",
                "message": "Processing failed",
                "error": str(e)
            }
    
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
    chat_id: str = None,
    user=Depends(get_current_user)
):

    supabase = get_supabase_user_client(user["access_token"])
    
    if chat_id:
        chat_check = supabase.table("chats") \
            .select("id") \
            .eq("id", chat_id) \
            .eq("user_id", user["id"]) \
            .execute()
        
        if chat_check.data:
            final_chat_id = chat_id
            print(f"📤 Uploading to existing chat: {final_chat_id}")
        else:
            new_chat = create_chat(supabase, user["id"])
            final_chat_id = new_chat["id"]
            print(f"📤 Chat not found, created new: {final_chat_id}")
    else:
        new_chat = create_chat(supabase, user["id"])
        final_chat_id = new_chat["id"]
        print(f"📤 No chat_id provided, created new: {final_chat_id}")
   
    print("===== UPLOAD DEBUG =====")
    print("UPLOAD USER ID:", user["id"])
    print("UPLOAD CHAT ID:", final_chat_id)
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
                final_chat_id
        )
       
    if uploaded_count == 0:
        raise HTTPException(status_code=400, detail="No valid PDFs uploaded")

    return {
        "message": "Uploading started",
        "uploaded_files": uploaded_count,
        "chat_id": final_chat_id,
        "status": "processing"
    }

@app.post("/chats")
def new_chat(user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])
    
    import traceback
    print("="*50)
    print("🔴 NEW CHAT CREATION ATTEMPTED")
    print(f"User: {user['id']}")
    print("Stack trace:")
    traceback.print_stack()
    print("="*50)
    
    chat = create_chat(supabase, user["id"])
    return chat

@app.get("/chats")
def list_chats(user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])
    chats = get_user_chats(supabase)
    
    chats.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return chats


@app.get("/chats/{chat_id}")
def open_chat(chat_id: str, user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])
    return get_chat_messages(supabase, chat_id)

@app.get("/processing-status/{chat_id}")
def get_processing_status(chat_id: str, user=Depends(get_current_user)):
    """Get real-time processing status for a chat"""
    status_key = f"{user['id']}:{chat_id}"
    
    with status_lock:
        if status_key in processing_status:
            status = processing_status[status_key]
            
            # Clean up old status entries (older than 5 minutes)
            if status.get("status") in ["completed", "failed"]:
                try:
                    completed_time = datetime.fromisoformat(status.get("completed_time", "2000-01-01"))
                    if (datetime.now() - completed_time).seconds > 300:  # 5 minutes
                        del processing_status[status_key]
                except:
                    pass
            
            return status
    
    # Check if PDF exists in database
    supabase = get_supabase_user_client(user["access_token"])
    pdf_check = supabase.table("pdfs") \
        .select("filename") \
        .eq("user_id", user["id"]) \
        .eq("chat_id", chat_id) \
        .execute()
    
    if pdf_check.data and len(pdf_check.data) > 0:
        return {"status": "completed", "message": "PDF already processed"}
    
    return {"status": "unknown", "message": "No PDF found"}

def estimate_remaining_time(status):
    """Estimate remaining processing time"""
    if status.get("progress", 0) < 30:
        return "15-20 seconds"
    elif status.get("progress", 0) < 60:
        return "10-15 seconds"
    elif status.get("progress", 0) < 90:
        return "5-10 seconds"
    else:
        return "a few seconds"

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
        # Check processing status first
        status_key = f"{user['id']}:{req.chat_id}"
        with status_lock:
            if status_key in processing_status:
                status = processing_status[status_key]
                if status["status"] == "processing":
                    # Still processing - give user info
                    answer = f"""⏳ **Your PDF is being processed...**

{status.get('message', 'Processing')}  
📊 **Progress:** {status.get('progress', 0)}% complete

Estimated time remaining: {estimate_remaining_time(status)}

_You'll be notified when ready. Please wait..._"""
                    
                    insert_message(supabase, user["id"], req.chat_id, "assistant", answer)
                    return {"answer": answer, "used_pdf_context": False}
                
                elif status["status"] == "failed":
                    answer = f"""❌ **PDF processing failed**

{status.get('error', 'Unknown error')}

Please try uploading again."""
                    insert_message(supabase, user["id"], req.chat_id, "assistant", answer)
                    return {"answer": answer, "used_pdf_context": False}
        
        # Check if PDF was uploaded but status unknown
        pdf_check = supabase.table("pdfs") \
            .select("filename, created_at") \
            .eq("user_id", user["id"]) \
            .eq("chat_id", req.chat_id) \
            .execute()
        
        if pdf_check.data and len(pdf_check.data) > 0:
            answer = """⏳ **Your PDF was uploaded but is still being processed...**

This may take 15-30 seconds for large documents.
Please wait a moment and try again."""
        else:
            answer = "No PDF found for this chat. Please upload a PDF first"
        
        insert_message(supabase, user["id"], req.chat_id, "assistant", answer)
        return {"answer": answer, "used_pdf_context": False}

        # 🔥 IMPROVED RETRIEVAL - Zyada chunks lo
    results = faiss_index.similarity_search_with_score(
        req.question,
        k=TOP_K * 3,  # 24 chunks retrieve karo
    )

    # Better filtering - strict mat raho
    filtered_docs = []
    for doc, score in results:
        # Thoda lenient threshold
        if score <= SIMILARITY_THRESHOLD * 1.5:
            filtered_docs.append(doc)

    # Agar kuch nahi mila to top results le lo
    if len(filtered_docs) < 3:
        print("⚠️ Taking top results regardless of score")
        filtered_docs = [doc for doc, score in results[:TOP_K]]

    # Remove duplicates
    from difflib import SequenceMatcher

    def is_similar(text1, text2, threshold=0.7):
        """Check if two texts are similar (not just exact match)"""
        # Short strings ko alag treat karo
        if len(text1) < 50 or len(text2) < 50:
            return text1 == text2
    
        # SequenceMatcher se similarity check
        similarity = SequenceMatcher(None, text1[:200], text2[:200]).ratio()
        return similarity > threshold

    unique_docs = []
    for doc in filtered_docs:
        is_duplicate = False
        current_text = doc.page_content[:200]  # Pehle 200 chars se compare
    
        for existing in unique_docs:
            existing_text = existing.page_content[:200]
            if is_similar(current_text, existing_text, threshold=0.7):
                is_duplicate = True
                break
    
        if not is_duplicate:
            unique_docs.append(doc)

    filtered_docs = unique_docs
    print(f"📊 Similarity deduplication: {len(filtered_docs)} unique chunks")

    print(f"📚 Retrieved {len(filtered_docs)} unique chunks")

    # filtered_docs = [doc for doc, score in results]

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

    # Sort by relevance score if available
    if hasattr(results[0], 'score'):
        best_docs = [doc for doc, score in sorted(results, key=lambda x: x[1])[:TOP_K]]

    # Build context
    context_parts = []
    for doc in best_docs:
        if len(doc.page_content.strip()) > 40:
            context_parts.append(doc.page_content.strip())

    context_text = "\n\n".join(context_parts)

    # If context too short, get more chunks
    if len(context_text) < 500 and len(filtered_docs) > TOP_K:
        print("⚠️ Context too short, getting more chunks...")
        best_docs = filtered_docs[:TOP_K + 2]  # 2 extra chunks
        context_parts = []
        for doc in best_docs:
            if len(doc.page_content.strip()) > 40:
                context_parts.append(doc.page_content.strip())
        context_text = "\n\n".join(context_parts)

    # Clean up whitespace
    import re
    context_text = re.sub(r'\s+', ' ', context_text)

    # Limit context size
    context_text = context_text[:MAX_CONTEXT_CHARS]

        # 🔥 FINAL CHECK: Ensure we have enough context
    if len(context_text) < 200:
        print("⚠️ Very little context found, expanding search...")
        # Get more chunks
        more_results = faiss_index.similarity_search_with_score(
            req.question,
            k=TOP_K * 5,  # 40 chunks
        )
        for doc, score in more_results:
            if len(context_text) < 1000 and doc.page_content not in context_text:
                context_text += "\n\n" + doc.page_content.strip()

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
            

            if "rate limit" in error_str or "429" in error_str or "rate_limit_exceeded" in error_str:
               
                import re
                wait_time = re.search(r"in (\d+)m(\d+\.?\d*)s", str(e))
                if wait_time:
                    minutes = wait_time.group(1)
                    seconds = wait_time.group(2)
                    answer = f"⏳ **Rate limit reached.** Please try again in **{minutes} minutes {seconds} seconds**."
                else:
                    answer = "⏳ **Rate limit reached.** Please wait a few minutes and try again."
            
    
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

    import re

    def fix_numbering_generic(answer_text):
        """
        Fix numbering in ANY answer without hardcoding topics
        """
        lines = answer_text.split('\n')
        fixed_lines = []
    
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
        
            # Check if line starts with a number like "1.", "4.", etc.
            number_match = re.match(r'^(\d+)\.\s+(.*)', line)
        
            if number_match:
                current_num = int(number_match.group(1))
                content = number_match.group(2)
            
                fixed_lines.append(line)
            
                # Look ahead to find next numbered line
                next_num = None
                next_num_line = None
                j = i + 1
                while j < len(lines):
                    next_match = re.match(r'^(\d+)\.\s+', lines[j])
                    if next_match:
                        next_num = int(next_match.group(1))
                        next_num_line = j
                        break
                    j += 1
            
                # Agar next number mila aur skip hai (1 ke baad 4)
                if next_num and next_num > current_num + 1:
                
                    # Missing numbers ke liye generic names
                    for missing in range(current_num + 1, next_num):
                    
                        # Check karo kahin missing number already to nahi aaya bina number ke?
                        found_unumbered = False
                        for k in range(i + 1, next_num_line):
                            if lines[k].strip() and not re.match(r'^\d+\.', lines[k]):
                                unnumbered_content = lines[k].strip()
                                fixed_lines.append(f"{missing}. {unnumbered_content}")
                                found_unumbered = True
                                lines[k] = ""  # Mark as used
                                break
                    
                        if not found_unumbered:
                            fixed_lines.append(f"{missing}. **Item {missing}**")
                
                    i = next_num_line
                    continue
            
            elif line.strip() and not re.match(r'^\d+\.', line):
                # Yeh unnumbered line hai
                last_number = None
                for l in reversed(fixed_lines):
                    last_match = re.match(r'^(\d+)\.', l)
                    if last_match:
                        last_number = int(last_match.group(1))
                        break
            
                if last_number:
                    next_expected = last_number + 1
                    fixed_lines.append(f"{next_expected}. {line}")
                else:
                    fixed_lines.append(line)
            else:
                if line.strip():
                    fixed_lines.append(line)
        
            i += 1
    
        result_lines = [l for l in fixed_lines if l.strip()]
        return '\n'.join(result_lines)

# 🔥 YEH LINE ADD KARO - numbering fix apply karo
    answer_clean = fix_numbering_generic(answer_clean)

    is_sorry = (
        "not available in the provided pdf" in answer_clean.lower()
        or "not available in the provided context" in answer_clean.lower()
        or "i'm sorry" in answer_clean.lower()
        or "sorry" in answer_clean.lower()  
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
                if len(pdf_pages) > 6:
                    pdf_pages = pdf_pages[:6] + ["..."]  # Sirf 6 pages dikhao, baaki "..."

                source_texts.append(f"{pdf} — Pages {', '.join(pdf_pages)}")

            if len(source_texts) > 4:
                source_texts = source_texts[:4] + ["...and more PDFs"]
    
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

@app.delete("/chats/{chat_id}")
def delete_single_chat(chat_id: str, user=Depends(get_current_user)):
    """
    Delete a single chat and its associated FAISS index
    """
    supabase = get_supabase_user_client(user["access_token"])
    
    try:
        result = supabase.table("chats").delete().eq("id", chat_id).eq("user_id", user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        faiss_chat_path = os.path.join(FAISS_PATH, f"user_{user['id']}", chat_id)
        if os.path.exists(faiss_chat_path):
            shutil.rmtree(faiss_chat_path)
            print(f"✅ Deleted FAISS index for chat {chat_id}")
        
        supabase.table("messages").delete().eq("chat_id", chat_id).execute()
        
        supabase.table("pdfs").delete().eq("chat_id", chat_id).execute()
        
        return {"message": "Chat deleted successfully"}
        
    except Exception as e:
        print(f"❌ Error deleting chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {str(e)}")
 
@app.delete("/delete-chat-history")
def delete_chat_history(user=Depends(get_current_user)):
    supabase = get_supabase_user_client(user["access_token"])
    
    chats = supabase.table("chats").select("id").eq("user_id", user["id"]).execute()
    
    user_faiss_path = os.path.join(FAISS_PATH, f"user_{user['id']}")
    if os.path.exists(user_faiss_path):
        shutil.rmtree(user_faiss_path)
        print(f"✅ Deleted all FAISS indexes for user {user['id']}")
    
    supabase.table("messages").delete().eq("user_id", user["id"]).execute()
    
    supabase.table("pdfs").delete().eq("user_id", user["id"]).execute()
    
    delete_user_chats(supabase, user["id"])
    
    return {"message": "All chats deleted"}

@app.get("/health")
def health():
    return {"status": "ok"}