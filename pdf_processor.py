import io
from PyPDF2 import PdfReader
import re

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extracts text from a PDF file byte stream."""
    pdf_file = io.BytesIO(file_content)
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def clean_text(text: str) -> str:
    """Cleans extracted text by removing extra whitespace and special characters."""
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    # Basic cleaning - keeping only alphanumeric and basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text.strip()

def chunk_text(text: str, chunk_size: int = 500) -> list:
    """Splits cleaned text into chunks of approximately chunk_size characters."""
    # Split by sentences to avoid cutting in the middle of a sentence
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def process_pdf(file_content: bytes, source_id: str) -> list:
    """Full pipeline to extract, clean, and chunk PDF content."""
    raw_text = extract_text_from_pdf(file_content)
    cleaned_text = clean_text(raw_text)
    chunks = chunk_text(cleaned_text)
    
    processed_chunks = []
    for i, text in enumerate(chunks):
        processed_chunks.append({
            "source_id": source_id,
            "chunk_id": f"{source_id}_CH_{i+1:02d}",
            "text": text
        })
    return processed_chunks
