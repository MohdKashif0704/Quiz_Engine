from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from database import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, unique=True, index=True)
    filename = Column(String)
    grade = Column(Integer, nullable=True)
    subject = Column(String, nullable=True)
    topic = Column(String, index=True)
    chunks = relationship("Chunk", back_populates="document")

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String, unique=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    text = Column(Text)
    document = relationship("Document", back_populates="chunks")
    questions = relationship("Question", back_populates="chunk")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    type = Column(String)  # MCQ, TF, FIB
    options = Column(JSON, nullable=True)  # Store list for MCQ
    answer = Column(String)
    difficulty = Column(String)  # easy, medium, hard
    chunk_id = Column(Integer, ForeignKey("chunks.id"))
    chunk = relationship("Chunk", back_populates="questions")

class StudentProgress(Base):
    __tablename__ = "student_progress"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    topic = Column(String, index=True)
    current_difficulty = Column(String, default="easy")
    score = Column(Float, default=0.0)

class StudentAnswer(Base):
    __tablename__ = "student_answers"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_answer = Column(String)
    is_correct = Column(Integer)  # 1 or 0
