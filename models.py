from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    # Relações
    histories = relationship("UserHistory", back_populates="user")

class PDFDocument(Base):
    __tablename__ = "pdf_documents"
    id = Column(Integer, primary_key=True)
    file_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relações
    blocks = relationship("PDFBlock", back_populates="pdf_document")

class PDFBlock(Base):
    __tablename__ = "pdf_blocks"
    id = Column(Integer, primary_key=True)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id"), nullable=False)
    text_content = Column(Text, nullable=False)
    
    # Relações
    pdf_document = relationship("PDFDocument", back_populates="blocks")
    qas = relationship("QA", back_populates="pdf_block")

class QA(Base):
    __tablename__ = "questions_answers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pdf_block_id = Column(Integer, ForeignKey("pdf_blocks.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    
    # Relações
    pdf_block = relationship("PDFBlock", back_populates="qas")
    user_history = relationship("UserHistory", back_populates="qa")

class UserHistory(Base):
    __tablename__ = "users_history"
    id = Column(Integer, primary_key=True)
    qa_id = Column(Integer, ForeignKey("questions_answers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_answer = Column(Text)
    grade = Column(Integer)
    state = Column(Integer)
    step = Column(Integer)
    difficulty = Column(Float)
    stability = Column(Float)
    review = Column(DateTime)
    due = Column(DateTime)
    
    # Relações
    qa = relationship("QA", back_populates="user_history")
    user = relationship("User", back_populates="histories")