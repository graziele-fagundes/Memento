from models import User
from database import SessionLocal
from getpass import getpass

from getpass import getpass
from models import User
from database import SessionLocal
import bcrypt

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode(), salt).decode()

def register():
    db = SessionLocal()
    name = input("Nome: ")
    email = input("Email: ")
    password = getpass("Senha: ")

    if db.query(User).filter_by(email=email).first():
        print("Email já registrado.")
        return None

    hashed = hash_password(password)
    user = User(name=name, email=email, password=hashed)
    db.add(user)
    db.commit()
    print("Usuário registrado com sucesso!")
    user = db.query(User).filter_by(email=email).first()
    return user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def login():
    db = SessionLocal()
    email = input("Email: ")
    password = getpass("Senha: ")

    user = db.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.password):
        print("Credenciais inválidas.")
        return None

    print(f"Bem-vindo, {user.name}!")
    return user

