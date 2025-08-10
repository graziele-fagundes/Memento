import os
import re
import fitz
from collections import Counter
from database import SessionLocal
from models import PDFDocument, PDFBlock, QA
from qag.generator import generate_qa
from langchain.text_splitter import RecursiveCharacterTextSplitter
from prompt_toolkit import prompt

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================
# Funções de limpeza de PDF
# ==========================
def detectar_repeticoes(paginas, pos='top', n_linhas=2, repeticao_min=0.8):
    """Detecta cabeçalhos ou rodapés repetidos entre páginas."""
    if pos == 'top':
        candidatos = ["\n".join(p[:n_linhas]) for p in paginas]
    else:
        candidatos = ["\n".join(p[-n_linhas:]) for p in paginas]

    contagem = Counter(candidatos)
    limite = int(len(paginas) * repeticao_min)
    return {texto for texto, freq in contagem.items() if freq >= limite}

def limpar_texto(texto):
    """Remove URLs e caracteres estranhos."""
    texto = re.sub(r'https?://\S+|www\.\S+', '', texto)
    texto = re.sub(r'[^\w\sá-úÁ-Ú.,!?;:\-–()"/]', '', texto)
    return texto.strip()

def limpar_pdf_paginas(texto_extraido):
    """Limpa cabeçalhos, rodapés, números de página e ruídos comuns."""
    bruto_paginas = texto_extraido.split("<<<PAGE_BREAK>>>")
    paginas = [p.split("\n") for p in bruto_paginas]

    headers = detectar_repeticoes(paginas, pos='top')
    footers = detectar_repeticoes(paginas, pos='bottom')

    texto_limpo_paginas = []
    for linhas in paginas:
        novas_linhas = []
        for linha in linhas:
            linha_strip = linha.strip()

            if linha_strip in headers or linha_strip in footers:
                continue
            if re.match(r'^\d{1,3}$', linha_strip):  # número de página
                continue
            if not linha_strip:
                continue

            novas_linhas.append(linha_strip)

        # Junta linhas quebradas sem pontuação final
        pagina_texto = ""
        for linha in novas_linhas:
            if pagina_texto and not pagina_texto.endswith(('.', '?', '!', ':')):
                pagina_texto += " " + linha
            else:
                pagina_texto += "\n" + linha

        # Remove hifenização
        pagina_texto = re.sub(r'(\w+)-\n(\w+)', r'\1\2', pagina_texto)

        # Limpeza final
        pagina_texto = limpar_texto(pagina_texto)
        texto_limpo_paginas.append(pagina_texto.strip())

    return "\n\n".join(texto_limpo_paginas)

# ==========================
# Fluxo principal
# ==========================
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

def load_pdf_text(path):
    """Extrai texto do PDF e aplica limpeza automática."""
    doc = fitz.open(path)
    paginas = []
    for page in doc:
        paginas.append(page.get_text("text"))
    doc.close()

    texto_completo = "<<<PAGE_BREAK>>>".join(paginas)
    texto_limpo = limpar_pdf_paginas(texto_completo)
    return texto_limpo

def split_text(text, chunk_size=800, chunk_overlap=150):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_text(text)
    chunks = [chunk.replace("\n", " ").strip() for chunk in chunks if chunk.strip()]
    return chunks

def extract_blocks(path, chunk_size=1500, chunk_overlap=200):
    text = load_pdf_text(path)
    blocks = split_text(text, chunk_size, chunk_overlap)
    return blocks

def handle_pdf_upload(user):
    path = input("Caminho do PDF: ")
    with open(path, "rb") as f:
        file_bytes = f.read()

    saved_path = save_pdf(user.id, path, file_bytes)
    blocks = extract_blocks(saved_path)

    # Curadoria
    curated_blocks = []
    print("\n--- Curadoria dos Blocos ---")
    for i, block in enumerate(blocks):
        print(f"\n🔹 Bloco {i+1}:\n{block}\n")
        action = input("[Enter = manter | e = editar | x = excluir] > ").strip().lower()
        
        if action == "x":
            print("❌ Bloco excluído.")
            continue
        elif action == "e":
            print("✏️ Editando bloco:")
            new_block = prompt("Edite o bloco: ", default=block)
            new_block = new_block.strip()
            if new_block:
                curated_blocks.append(new_block)
            else:
                print("⚠️ Bloco vazio após edição. Ignorado.")
        else:
            curated_blocks.append(block)

    if not curated_blocks:
        print("⚠️ Nenhum bloco aprovado. Upload cancelado.")
        return

    db = SessionLocal()
    pdf_doc = PDFDocument(file_path=saved_path, uploader_id=user.id)
    db.add(pdf_doc)
    db.commit()
    db.refresh(pdf_doc)

    for i, block_text in enumerate(curated_blocks):
        block = PDFBlock(pdf_id=pdf_doc.id, block_order=i, text_content=block_text)
        db.add(block)
        db.commit()
        db.refresh(block)

        question, answer = generate_qa(block_text)
        qa = QA(
            user_id=user.id,
            pdf_block_id=block.id,
            question=question,
            answer=answer
        )
        db.add(qa)

    db.commit()
    print(f"✅ {len(curated_blocks)} blocos e QAs salvos.")
