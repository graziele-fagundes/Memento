import os
from database import SessionLocal
from models import PDFDocument, PDFBlock
from qag.generator import generate_qa
from prompt_toolkit import prompt
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # pasta do arquivo atual
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

    if not path.lower().endswith(".pdf"):
        print("❌ Arquivo inválido. Por favor, selecione um PDF.")
        return

    with open(path, "rb") as f:
        file_bytes = f.read()

    print("⏳ Extraindo texto do PDF...")
    saved_path = save_pdf(user.id, path, file_bytes)
    blocks = extract_blocks_with_docling(saved_path)

    # Cálculo de mínimos e máximos
    block_sizes = [len(b) for b in blocks]

    # Máximo = número de chunks originais
    max_q = len(blocks)

    # Mínimo: agrupar apenas blocos adjacentes sem ultrapassar 1000
    min_groups = []
    current = []
    current_len = 0
    for size, text in zip(block_sizes, blocks):
        if current_len + size <= 1000:
            current.append(text)
            current_len += size
        else:
            min_groups.append("\n".join(current))
            current = [text]
            current_len = size
    if current:
        min_groups.append("\n".join(current))
    min_q = len(min_groups)

    print(f"📊 Número de perguntas possíveis: mínimo = {min_q}, máximo = {max_q}")
    qtd = int(input("Quantas perguntas você deseja gerar? "))

    if not (min_q <= qtd <= max_q):
        print("❌ Valor inválido. Encerrando.")
        return

    # ========================
    # Montagem dos grupos finais (adjacentes)
    # ========================
    if qtd == max_q:
        final_groups = blocks
    elif qtd == min_q:
        final_groups = min_groups
    else:
        # Distribuição intermediária: junta blocos adjacentes sem ultrapassar 1000
        final_groups = []
        current = []
        current_len = 0
        groups_remaining = qtd
        for size, text in zip(block_sizes, blocks):
            if current_len + size <= 1000:
                current.append(text)
                current_len += size
            else:
                final_groups.append("\n".join(current))
                current = [text]
                current_len = size
                groups_remaining -= 1

        if current:
            final_groups.append("\n".join(current))

        # Ajuste final: se ainda faltar grupos, separa alguns blocos isolados
        while len(final_groups) < qtd:
            # pega o último grupo e separa o primeiro bloco dele
            last_group = final_groups.pop()
            split_blocks = last_group.split("\n")
            final_groups.append(split_blocks[0])
            if len(split_blocks) > 1:
                final_groups.append("\n".join(split_blocks[1:]))

    # ========================
    # Persistência no banco + geração de QA
    # ========================
    db = SessionLocal()
    pdf_doc = PDFDocument(file_path=saved_path, uploader_id=user.id)
    db.add(pdf_doc)
    db.commit()
    db.refresh(pdf_doc)

    print(f"TAMANHO FINAL GROUPS: {len(final_groups)}")
    for i, block_text in enumerate(final_groups):
        block = PDFBlock(pdf_id=pdf_doc.id, block_order=i, text_content=block_text)
        db.add(block)
        db.commit()
        db.refresh(block)

        generate_qa(block, user.id)

    print(f"✅ {len(final_groups)} blocos (agrupados) e QAs salvos.")