from models import User
from database import SessionLocal
from getpass import getpass

def register():
    db = SessionLocal()
    name = input("Nome: ")
    email = input("Email: ")
    password = getpass("Senha: ")
    if db.query(User).filter_by(email=email).first():
        print("Email já registrado.")
        return None
    user = User(name=name, email=email, password=password)
    db.add(user)
    db.commit()
    print("Usuário registrado com sucesso!")
    
    user = db.query(User).filter_by(email=email, password=password).first()
    return user

def login():
    db = SessionLocal()
    email = input("Email: ")
    password = getpass("Senha: ")
    user = db.query(User).filter_by(email=email, password=password).first()
    if not user:
        print("Credenciais inválidas.")
        return None
    print(f"Bem-vindo, {user.name}!")
    return user
