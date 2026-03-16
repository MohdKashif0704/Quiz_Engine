from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import models, schemas, crud, database, pdf_processor, quiz_generator
from typing import List, Optional
import uuid

# Initialize database
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Quiz Engine API")

@app.post("/ingest", response_model=schemas.Document)
async def ingest_pdf(
    file: UploadFile = File(...),
    grade: Optional[int] = Form(None),
    subject: Optional[str] = Form(None),
    topic: str = Form(...),
    db: Session = Depends(database.get_db)
):
    """Ingest a PDF file, extract text, clean it, and chunk it."""
    try:
        content = await file.read()
        source_id = f"SRC_{uuid.uuid4().hex[:8].upper()}"
        
        # 1. Process PDF
        processed_chunks = pdf_processor.process_pdf(content, source_id)
        
        # 2. Store Document
        doc_create = schemas.DocumentCreate(
            source_id=source_id,
            filename=file.filename,
            grade=grade,
            subject=subject,
            topic=topic
        )
        db_doc = crud.create_document(db, doc_create)
        
        # 3. Store Chunks
        for chunk_data in processed_chunks:
            crud.create_chunk(db, chunk_data, db_doc.id)
            
        db.refresh(db_doc)
        return db_doc
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@app.post("/generate-quiz/{doc_id}", response_model=List[schemas.Question])
async def generate_quiz(doc_id: int, db: Session = Depends(database.get_db)):
    """Generate quiz questions for all chunks in a document using an LLM."""
    db_doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    all_questions = []
    for chunk in db_doc.chunks:
        # Simulate LLM question generation
        questions_data = quiz_generator.generate_quiz_questions(chunk.text, chunk.chunk_id)
        for q_data in questions_data:
            db_q = crud.create_question(db, q_data, chunk.id)
            all_questions.append(db_q)
            
    return all_questions

@app.get("/quiz", response_model=List[schemas.QuizResponse])
def get_quiz(
    student_id: str,
    topic: str,
    difficulty: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Retrieve quiz questions based on topic and student's current difficulty."""
    # 1. Determine student's difficulty for this topic
    progress = crud.get_student_progress(db, student_id, topic)
    current_diff = difficulty or progress.current_difficulty
    
    # 2. Fetch questions matching topic and difficulty
    questions = crud.get_questions_by_topic_and_difficulty(db, topic, current_diff)
    
    if not questions:
        # Fallback to any difficulty if no questions found
        questions = db.query(models.Question).join(models.Chunk).join(models.Document).filter(
            models.Document.topic == topic
        ).limit(10).all()
        
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this topic.")
        
    return questions

@app.post("/submit-answer")
def submit_answer(submission: schemas.AnswerSubmission, db: Session = Depends(database.get_db)):
    """Submit student answer and update difficulty based on performance."""
    # 1. Fetch question and check correctness
    db_q = crud.get_question_by_id(db, submission.question_id)
    if not db_q:
        raise HTTPException(status_code=404, detail="Question not found")
        
    is_correct = (submission.selected_answer.strip().lower() == db_q.answer.strip().lower())
    
    # 2. Record answer
    crud.record_answer(db, submission, is_correct)
    
    # 3. Update student difficulty for the topic
    topic = db_q.chunk.document.topic
    progress = crud.get_student_progress(db, submission.student_id, topic)
    updated_progress = crud.update_student_difficulty(db, progress, is_correct)
    
    return {
        "is_correct": is_correct,
        "correct_answer": db_q.answer,
        "new_difficulty": updated_progress.current_difficulty
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
