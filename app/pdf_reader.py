from langchain_community.document_loaders import PyPDFLoader
import re

def clean_pdf_text(text: str):
    text = re.sub(r'(\d+)\.\s*\n\s*([A-Za-z])', r'\1. \2', text)
    text = re.sub(r'\n\s*:\s*', ': ', text)
    text = re.sub(r'([A-Za-z])\n([a-z])', r'\1 \2', text)
    text = re.sub(r'\n([A-Z][a-zA-Z ]+)\n', r' \1 ', text)
    text = re.sub(r'([a-z])\n([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'(?<!\n)\n(?!\n)(?!\d+\.)', ' ', text)
    text = re.sub(r'\s(\d+\.\s)', r'\n\1', text)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'^(\d+)\.\s*\n\s*([A-Z][A-Za-z ]+)', r'\1. \2', text, flags=re.MULTILINE)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    return text.strip()

def load_pdf(file_path: str):
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        if not docs:
            return None

        pages = []
        for doc in docs:
            if doc.page_content:
                clean_text = clean_pdf_text(doc.page_content)

                page_num = doc.metadata.get("page")
                if page_num is None:
                    page_num = 0
            
                print(f"📄 Page {page_num + 1} extracted, length: {len(clean_text)} chars")
                pages.append({
                    "text": clean_text,
                    "page": page_num
                })
        return pages