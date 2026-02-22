from pydantic import BaseModel, Field
from typing import Optional


class LectureRequest(BaseModel):
    lesson_id: str
    session_id: Optional[str] = None
    message: str = Field(max_length=2000)
    message_id: str


class ExamStartRequest(BaseModel):
    lesson_id: str


class ConsultantRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(max_length=2000)
    message_id: str


class SessionOut(BaseModel):
    session_id: str
    mode: str
