import os
from langchain_community.vectorstores import FAISS
from app.embeddings import embeddings_model

FAISS_PATH = "data/faiss_index"

def get_user_faiss_path(user_id: str): 
    return os.path.join(FAISS_PATH, f"user_{user_id}")

def load_faiss_index(user_id:str):
    path = get_user_faiss_path(user_id)

    if not os.path.exists(path): 
        return None

    return FAISS.load_local(
        path, 
        embeddings_model, 
        allow_dangerous_deserialization=True 
    )
def save_faiss_index(index, user_id: str):
    path = get_user_faiss_path(user_id)
    os.makedirs(path, exist_ok=True)
    index.save_local(path)

def create_or_update_faiss(chunks_with_meta, user_id: str):
    index = load_faiss_index(user_id)

    texts = [c["text"] for c in chunks_with_meta]
    metas = [c["metadata"] for c in chunks_with_meta]

    if index:
        index.add_texts(texts, metadatas=metas)
    else:
        index = FAISS.from_texts(
            texts=texts, 
            embedding=embeddings_model, 
            metadatas=metas 
        )

    
    save_faiss_index(index, user_id) 
    return index