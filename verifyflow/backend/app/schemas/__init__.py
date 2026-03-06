from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class QuestionnaireSessionCreate(BaseModel):
    title: str | None = None

class QuestionnaireSessionOut(BaseModel):
    id: int
    user_id: int
    title: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReferenceDocumentOut(BaseModel):
    id: int
    session_id: int
    filename: str
    # parsed_text: str   ← usually don't return full text in list view

    class Config:
        from_attributes = True

class QuestionOut(BaseModel):
    id: int
    session_id: int
    original_text: str
    answer: str | None = None
    citations: list = []
    confidence: int = 0
    is_edited: bool = False

    class Config:
        from_attributes = True

class QuestionnaireUploadResponse(BaseModel):
    session_id: int
    questions_created: int
    questions: list[QuestionOut]

class GenerateAnswersResponse(BaseModel):
    session_id: int
    questions_processed: int
    results: list[QuestionOut]

class PartialRegenerateRequest(BaseModel):
    question_ids: list[int]
    force: bool = False