from sqlalchemy.orm import Session
import models
import schemas
import uuid

def create_document(db: Session, doc: schemas.DocumentCreate) -> models.Document:
    db_doc = models.Document(**doc.dict())
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def create_chunk(db: Session, chunk_data: dict, doc_id: int) -> models.Chunk:
    db_chunk = models.Chunk(
        chunk_id=chunk_data["chunk_id"],
        text=chunk_data["text"],
        document_id=doc_id
    )
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk

def create_question(db: Session, question_data: dict, chunk_id: int) -> models.Question:
    db_question = models.Question(
        text=question_data["question"],
        type=question_data["type"],
        options=question_data["options"],
        answer=question_data["answer"],
        difficulty=question_data["difficulty"],
        chunk_id=chunk_id
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def get_questions_by_topic_and_difficulty(db: Session, topic: str, difficulty: str, limit: int = 10):
    return db.query(models.Question).join(models.Chunk).join(models.Document).filter(
        models.Document.topic == topic,
        models.Question.difficulty == difficulty
    ).limit(limit).all()

def get_student_progress(db: Session, student_id: str, topic: str):
    progress = db.query(models.StudentProgress).filter(
        models.StudentProgress.student_id == student_id,
        models.StudentProgress.topic == topic
    ).first()
    if not progress:
        progress = models.StudentProgress(student_id=student_id, topic=topic)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress

def update_student_difficulty(db: Session, progress: models.StudentProgress, is_correct: bool):
    difficulties = ["easy", "medium", "hard"]
    current_idx = difficulties.index(progress.current_difficulty)
    
    if is_correct:
        if current_idx < 2:
            progress.current_difficulty = difficulties[current_idx + 1]
    else:
        if current_idx > 0:
            progress.current_difficulty = difficulties[current_idx - 1]
    
    db.commit()
    db.refresh(progress)
    return progress

def record_answer(db: Session, submission: schemas.AnswerSubmission, is_correct: bool):
    db_answer = models.StudentAnswer(
        student_id=submission.student_id,
        question_id=submission.question_id,
        selected_answer=submission.selected_answer,
        is_correct=1 if is_correct else 0
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

def get_question_by_id(db: Session, question_id: int):
    return db.query(models.Question).filter(models.Question.id == question_id).first()
