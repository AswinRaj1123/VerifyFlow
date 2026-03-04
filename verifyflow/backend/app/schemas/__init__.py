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