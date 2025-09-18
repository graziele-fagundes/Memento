import os
from database import SessionLocal
from models import PDFDocument, PDFBlock
from qag.generator import generate_qa
from prompt_toolkit import prompt
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_pdf(user_id, original_path, file_bytes):
    user_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    filename = os.path.basename(original_path)
    save_path = os.path.join(user_dir, filename)
    if os.path.exists(save_path):
        print(f"Arquivo {filename} já existe. Substituindo...")
    with open(save_path, "wb") as f:
        f.write(file_bytes)
    return save_path

def extract_blocks_with_docling(path):
    """Extrai blocos do PDF usando Docling + HybridChunker."""
    doc = DocumentConverter().convert(source=path).document
    chunker = HybridChunker()
    
    blocks = []
    for i, chunk in enumerate(chunker.chunk(dl_doc=doc)):
        enriched_text = chunker.contextualize(chunk=chunk)
        blocks.append(enriched_text.strip())
    return blocks


def handle_pdf_upload(user):
    path = input("Caminho do PDF: ")
    with open(path, "rb") as f:
        file_bytes = f.read()

    saved_path = save_pdf(user.id, path, file_bytes)
    blocks = extract_blocks_with_docling(saved_path)

    db = SessionLocal()
    pdf_doc = PDFDocument(file_path=saved_path, uploader_id=user.id)
    db.add(pdf_doc)
    db.commit()
    db.refresh(pdf_doc)

    for i, block_text in enumerate(blocks):
        block = PDFBlock(pdf_id=pdf_doc.id, block_order=i, text_content=block_text)
        db.add(block)
        db.commit()
        db.refresh(block)

        generate_qa(block, user.id)

    print(f"✅ {len(blocks)} blocos e QAs salvos.")
