from pydantic import BaseModel
from typing import Optional


class ModuleOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    order_index: int
    lessons_count: int


class LessonOut(BaseModel):
    id: str
    module_id: str
    title: str
    description: Optional[str]
    order_index: int


class LessonContentOut(BaseModel):
    lesson_id: str
    title: str
    content: str
