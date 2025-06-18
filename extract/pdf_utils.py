import os
import fitz 
from database import SessionLocal
from models import PDFDocument, PDFBlock, Flashcard
from qa.generator import generate_flashcard
import fitz
from langchain.text_splitter import RecursiveCharacterTextSplitter

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_pdf(user_id, original_path, file_bytes):
    user_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    filename = os.path.basename(original_path)
    save_path = os.path.join(user_dir, filename)

    # If the file already exists, show a message
    if os.path.exists(save_path):
        print(f"Arquivo {filename} já existe. Substituindo...")
        
    with open(save_path, "wb") as f:
        f.write(file_bytes)
    return save_path


def load_pdf_text(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text

def split_text(text, chunk_size=800, chunk_overlap=150):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_text(text)

    # Remove empty chunks
    chunks = [chunk for chunk in chunks if chunk.strip()]
    # Remoe line breaks
    chunks = [chunk.replace("\n", " ").strip() for chunk in chunks]
    return chunks

def extract_blocks(path, chunk_size=800, chunk_overlap=150):
    text = load_pdf_text(path)
    blocks = split_text(text, chunk_size, chunk_overlap)
    return blocks

def handle_pdf_upload(user):
    path = input("Caminho do PDF: ")
    with open(path, "rb") as f:
        file_bytes = f.read()

    saved_path = save_pdf(user.id, path, file_bytes)

    db = SessionLocal()
    pdf_doc = PDFDocument(file_path=saved_path, uploader_id=user.id)
    db.add(pdf_doc)
    db.commit()
    db.refresh(pdf_doc)

    blocks = extract_blocks(saved_path)
    for i, block_text in enumerate(blocks):
        block = PDFBlock(pdf_id=pdf_doc.id, block_order=i, text_content=block_text)
        db.add(block)
        db.commit()
        db.refresh(block)

        question, answer = generate_flashcard(block_text)
        flashcard = Flashcard(
            user_id=user.id,
            pdf_block_id=block.id,
            question=question,
            answer=answer
        )
        db.add(flashcard)
    db.commit()
    print(f"{len(blocks)} blocos e flashcards salvos.")
