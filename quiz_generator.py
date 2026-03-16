import json
import random
import re
import os
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_with_gemini(text: str, chunk_id: str) -> List[Dict[str, Any]]:
    """Generates quiz questions using Gemini 2.5 Flash."""
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    You are an educational assistant. Based on the following text, generate 3 quiz questions:
    1. One Multiple Choice Question (MCQ) with 4 options.
    2. One True/False (TF) question.
    3. One Fill-in-the-blank (FIB) question.

    For each question, assign a difficulty level: 'easy', 'medium', or 'hard'.
    
    Format the output as a JSON list of objects with these fields:
    - question: the question text
    - type: 'MCQ', 'TF', or 'FIB'
    - options: list of 4 strings for MCQ, ['True', 'False'] for TF, null for FIB
    - answer: the correct answer string
    - difficulty: 'easy', 'medium', or 'hard'
    - source_chunk_id: "{chunk_id}"

    Text:
    {text}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        questions = json.loads(response.text)
        # Ensure source_chunk_id is correct
        for q in questions:
            q['source_chunk_id'] = chunk_id
        return questions
    except Exception as e:
        print(f"Gemini generation failed: {e}")
        return []

def extract_questions_from_text(text: str, chunk_id: str) -> List[Dict[str, Any]]:
    """Attempts to extract structured questions already present in the text."""
    questions = []
    
    # 1. Extract MCQs: "1. MCQ ... A. ... B. ... C. ... D. ... Answer ..."
    mcq_pattern = r"(\d+)\.\s+MCQ\s+(.*?)\s+A\.\s+(.*?)\s+B\.\s+(.*?)\s+C\.\s+(.*?)\s+D\.\s+(.*?)\s+Answer\s+(.*?)(?=\s+\d+\.|$)"
    mcq_matches = re.finditer(mcq_pattern, text, re.DOTALL)
    for match in mcq_matches:
        q_num, question, a, b, c, d, answer = match.groups()
        questions.append({
            "question": question.strip(),
            "type": "MCQ",
            "options": [a.strip(), b.strip(), c.strip(), d.strip()],
            "answer": answer.strip(),
            "difficulty": "medium",
            "source_chunk_id": chunk_id
        })
        
    # 2. Extract True/False: "2. TrueFalse ... Answer ..."
    tf_pattern = r"(\d+)\.\s+TrueFalse\s+(.*?)\s+Answer\s+(True|False)(?=\s+\d+\.|$)"
    tf_matches = re.finditer(tf_pattern, text, re.DOTALL)
    for match in tf_matches:
        q_num, question, answer = match.groups()
        questions.append({
            "question": question.strip(),
            "type": "TF",
            "options": ["True", "False"],
            "answer": answer.strip(),
            "difficulty": "easy",
            "source_chunk_id": chunk_id
        })
        
    # 3. Extract Fill-in-the-blank: "3. Fill ... Answer ..."
    fib_pattern = r"(\d+)\.\s+Fill\s+(.*?)\s+Answer\s+(.*?)(?=\s+\d+\.|$)"
    fib_matches = re.finditer(fib_pattern, text, re.DOTALL)
    for match in fib_matches:
        q_num, question, answer = match.groups()
        questions.append({
            "question": question.strip(),
            "type": "FIB",
            "options": None,
            "answer": answer.strip(),
            "difficulty": "hard",
            "source_chunk_id": chunk_id
        })
        
    return questions

def generate_mock_questions(chunk_text: str, chunk_id: str) -> List[Dict[str, Any]]:
    """Simulates an LLM generating questions from a chunk of text."""
    # First, try to extract existing questions
    extracted = extract_questions_from_text(chunk_text, chunk_id)
    if extracted:
        return extracted
        
    # If no structured questions found, fallback to basic mock
    questions = []
    
    # MCQ
    questions.append({
        "question": f"Based on the content: '{chunk_text[:50]}...', what is the primary topic?",
        "type": "MCQ",
        "options": ["Topic A", "Topic B", "Topic C", "Topic D"],
        "answer": "Topic A",
        "difficulty": random.choice(["easy", "medium", "hard"]),
        "source_chunk_id": chunk_id
    })
    
    # TF
    questions.append({
        "question": f"Does the text mention: '{chunk_text[:20]}...'?",
        "type": "TF",
        "options": ["True", "False"],
        "answer": "True",
        "difficulty": random.choice(["easy", "medium", "hard"]),
        "source_chunk_id": chunk_id
    })
    
    return questions

def generate_quiz_questions(chunk_text: str, chunk_id: str, api_key: str = None) -> List[Dict[str, Any]]:
    """Generates quiz questions from chunk text using Gemini 2.5 Flash, Parser, or Mock."""
    # 1. Try Gemini if configured
    if GEMINI_API_KEY:
        gemini_questions = generate_with_gemini(chunk_text, chunk_id)
        if gemini_questions:
            return gemini_questions
            
    # 2. Fallback to extracting existing questions
    extracted = extract_questions_from_text(chunk_text, chunk_id)
    if extracted:
        return extracted
        
    # 3. Final fallback to mock questions
    return generate_mock_questions(chunk_text, chunk_id)
