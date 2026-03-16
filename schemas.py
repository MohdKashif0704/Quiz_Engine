from pydantic import BaseModel
from typing import List, Optional, Union

class ChunkBase(BaseModel):
    chunk_id: str
    text: str

class ChunkCreate(ChunkBase):
    pass

class Chunk(ChunkBase):
    id: int
    document_id: int

    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    source_id: str
    filename: str
    grade: Optional[int] = None
    subject: Optional[str] = None
    topic: str

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    chunks: List[Chunk] = []

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    text: str
    type: str  # MCQ, TF, FIB
    options: Optional[List[str]] = None
    answer: str
    difficulty: str
    chunk_id: int

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int

    class Config:
        from_attributes = True

class AnswerSubmission(BaseModel):
    student_id: str
    question_id: int
    selected_answer: str

class QuizResponse(BaseModel):
    id: int
    text: str
    type: str
    options: Optional[List[str]] = None
    difficulty: str

class StudentProgress(BaseModel):
    student_id: str
    topic: str
    current_difficulty: str
    score: float

    class Config:
        from_attributes = True
