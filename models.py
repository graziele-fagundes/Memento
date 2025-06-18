from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

class PDFDocument(Base):
    __tablename__ = "pdf_documents"
    id = Column(Integer, primary_key=True)
    file_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class PDFBlock(Base):
    __tablename__ = "pdf_blocks"
    id = Column(Integer, primary_key=True)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id"), nullable=False)
    block_order = Column(Integer)
    text_content = Column(Text, nullable=False)

class Flashcard(Base):
    __tablename__ = "flashcards"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pdf_block_id = Column(Integer, ForeignKey("pdf_blocks.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    state = Column(Integer) 
    step = Column(Integer)
    difficulty = Column(Integer)
    stability = Column(Integer)
    last_grade = Column(Integer)
    last_review = Column(DateTime)
    due = Column(DateTime)
