from auth.auth import login, register
from pdf_extract.pdf_extractor import handle_pdf_upload
from qgqa.generator import start_review
from models import Base
from database import engine

# Garante que as tabelas sejam criadas se não existirem
Base.metadata.create_all(bind=engine)

print("1. Login\n2. Registrar")
escolha = input("Escolha: ")
user = login() if escolha == "1" else register()
if not user:
    exit()

while True:
    print("\nMenu:\n1. Upload PDF\n2. Iniciar Revisão\n3. Sair")
    op = input("Opção: ")
    if op == "1":
        handle_pdf_upload(user)
    elif op == "2":
        start_review(user)
    elif op == "3":
        break
