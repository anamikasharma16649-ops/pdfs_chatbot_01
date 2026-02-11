from langchain_community.document_loaders import PyPDFLoader

def load_pdf(file_path: str):
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        if not docs:
            return None

        pages = []
        for doc in docs:
            if doc.page_content:
                pages.append({
                    "text": doc.page_content.strip(),
                    "page": doc.metadata.get("page", None)
                })
        return pages