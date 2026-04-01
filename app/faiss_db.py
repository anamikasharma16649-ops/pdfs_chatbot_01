


import os
from langchain_community.vectorstores import FAISS
from app.embeddings import embeddings_model
from app.config import FAISS_PATH
from difflib import SequenceMatcher

def get_user_faiss_path(user_id: str, chat_id: str):
    return os.path.join(
        FAISS_PATH,
        f"user_{user_id}",
        f"chat_{chat_id}"
    )

def load_faiss_index(user_id: str, chat_id: str):
    path = get_user_faiss_path(user_id, chat_id)
    
    print("---- DEBUG LOAD ----")
    print("User:", user_id)
    print("Chat:", chat_id)
    print("Path:", path)
    print("Folder exists:", os.path.exists(path))
    
    if not os.path.exists(path):
        print("❌ FAISS folder does not exist")
        return None
    
    index_file = os.path.join(path, "index.faiss")
    pkl_file = os.path.join(path, "index.pkl")
    
    print("Index file exists:", os.path.exists(index_file))
    print("PKL file exists:", os.path.exists(pkl_file))
    
    if not os.path.exists(index_file):
        print("❌ FAISS index file missing")
        return None
    
    try:
        index = FAISS.load_local(
            path, 
            embeddings_model, 
            allow_dangerous_deserialization=True 
        )
        print("✅ FAISS index loaded successfully")
        return index
    except Exception as e:
        print(f"❌ Error loading FAISS: {str(e)}")
        return None

def save_faiss_index(index, user_id: str, chat_id: str):
    path = get_user_faiss_path(user_id, chat_id)
    os.makedirs(path, exist_ok=True)
    index.save_local(path)
    print(f"✅ FAISS index saved to {path}")

def is_duplicate(text1, text2, threshold=0.6):
    """Check if two texts are too similar"""
    if len(text1) < 50 or len(text2) < 50:
        return text1.strip() == text2.strip()
    
    t1 = text1[:200].strip()
    t2 = text2[:200].strip()
    
    similarity = SequenceMatcher(None, t1, t2).ratio()
    return similarity > threshold

def create_or_update_faiss(chunks_with_meta, user_id: str, chat_id: str):
    try:
        print(f"📊 Creating FAISS with {len(chunks_with_meta)} chunks")
        
        # 🔥 AGGRESSIVE DEDUPLICATION
        unique_chunks = []
        seen_texts = []
        
        for chunk in chunks_with_meta:
            text = chunk["text"]
            is_dup = False
            
            for seen in seen_texts:
                if is_duplicate(text, seen):
                    is_dup = True
                    break
            
            if not is_dup:
                unique_chunks.append(chunk)
                seen_texts.append(text)
        
        print(f"📊 After deduplication: {len(unique_chunks)} unique chunks")
        
        if unique_chunks and len(unique_chunks) > 0:
            print(f"Sample chunk: {unique_chunks[0]['text'][:100]}...")
            print(f"Metadata: {unique_chunks[0]['metadata']}")
        
        texts = [c["text"] for c in unique_chunks]
        metas = [c["metadata"] for c in unique_chunks]
        
        # 🔥 FIX: Pehle check karo index exist karta hai ya nahi
        existing_index = load_faiss_index(user_id, chat_id)
        
        if existing_index:
            print("📝 Updating existing FAISS index with new chunks...")
            existing_index.add_texts(texts, metadatas=metas)
            save_faiss_index(existing_index, user_id, chat_id)
            print("✅ FAISS index updated with new PDF")
        else:
            print("📝 Creating new FAISS index...")
            index = FAISS.from_texts(
                texts=texts, 
                embedding=embeddings_model, 
                metadatas=metas 
            )
            save_faiss_index(index, user_id, chat_id)
            print("✅ New FAISS index created")

        # Verify
        saved_index = load_faiss_index(user_id, chat_id)
        if saved_index:
            print(f"✅ Verification: FAISS index loaded successfully")
            # Count unique sources
            all_docs = saved_index.similarity_search("", k=1000)
            sources = set([doc.metadata.get("source") for doc in all_docs if doc.metadata])
            print(f"📚 Total PDFs in index: {len(sources)}")
            print(f"📄 PDFs: {', '.join(sources)}")
        else:
            print(f"❌ Verification: FAISS index could not be loaded!")
            
    except Exception as e:
        print(f"❌ FAISS creation failed: {str(e)}")
        import traceback
        traceback.print_exc()

