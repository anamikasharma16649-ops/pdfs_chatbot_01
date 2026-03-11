from pydantic import BaseModel, EmailStr
from typing import Optional

class AuthRequest(BaseModel):
    email: EmailStr
    password: str

class PDFUpload(BaseModel):
    filename: str


class QuestionRequest(BaseModel):
    question: str
    chat_id: str