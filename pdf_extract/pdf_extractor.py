import os
from database import SessionLocal
from models import PDFDocument, PDFBlock
from qag.generator import generate_qa
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

logging.getLogger("docling").setLevel(logging.ERROR)

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

def extract_blocks_with_docling(path, max_tokens=1024, use_tokenizer_limit=True):
    """
    Extrai blocos do PDF.
    - Se use_tokenizer_limit=True: Usa o tokenizer do Sabiá-7b e respeita max_tokens.
    - Se use_tokenizer_limit=False: Usa chunking padrão por estrutura (sem contagem precisa de tokens).
    """
    doc = DocumentConverter().convert(source=path).document
    
    if use_tokenizer_limit:
        chunker = HybridChunker(
            tokenizer="maritaca-ai/sabia-7b", 
            max_tokens=max_tokens,
            merge_peers=True
        )
    else:
        chunker = HybridChunker()
    
    blocks = []
    for i, chunk in enumerate(chunker.chunk(dl_doc=doc)):
        enriched_text = chunker.contextualize(chunk=chunk)
        blocks.append(enriched_text.strip())
    
    return blocks

def handle_pdf_upload(user):
    path = input("Caminho do PDF: ")

    if not path.lower().endswith(".pdf"):
        print("❌ Arquivo inválido. Por favor, selecione um PDF.")
        return

    with open(path, "rb") as f:
        file_bytes = f.read()

    print("⏳ Processando PDF...")
    saved_path = save_pdf(user.id, path, file_bytes)
    
    token_limit = 1024
    use_tokenizer = True
    blocks = extract_blocks_with_docling(
        saved_path, 
        max_tokens=token_limit, 
        use_tokenizer_limit=use_tokenizer
    )

    db = SessionLocal()
    pdf_doc = PDFDocument(file_path=saved_path, uploader_id=user.id)
    db.add(pdf_doc)
    db.commit()
    db.refresh(pdf_doc)
 
    for i, block_text in enumerate(blocks):
        block = PDFBlock(pdf_id=pdf_doc.id, text_content=block_text)
        db.add(block)
        db.commit()
        db.refresh(block)

        generate_qa(block, user.id)

    print(f"✅ PDF processado e salvo com {len(blocks)} blocos.")