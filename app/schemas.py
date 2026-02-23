from pydantic import BaseModel, EmailStr

# Auth
class AuthRequest(BaseModel):
    email: EmailStr
    password: str

# PDF Upload metadata
class PDFUpload(BaseModel):
    filename: str

# Ask question
class QuestionRequest(BaseModel):
    question: str
    chat_id: str 