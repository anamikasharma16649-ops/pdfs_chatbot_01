from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 100):
    if not text:
        return []
        
    splitter = RecursiveCharacterTextSplitter(
       chunk_size=CHUNK_SIZE,
       chunk_overlap=CHUNK_OVERLAP 
    )
    chunks = splitter.split_text(text)
    return chunks