from database import SessionLocal
from models import QA, PDFBlock, UserHistory
from datetime import datetime, timezone
from fsrs import Scheduler, Card, Rating, State

rating_map = {
    1: Rating.Again,
    2: Rating.Hard,
    3: Rating.Good,
    4: Rating.Easy,
}
state_map = {
    1: State.Learning,
    2: State.Review,
    3: State.Relearning,
}

scheduler = Scheduler()

from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import BitsAndBytesConfig
import torch

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

model_qag = AutoModelForCausalLM.from_pretrained("graziele-fagundes/Sabia7B-QAG", device_map="cuda", quantization_config=bnb_config)
tokenizer_qag = AutoTokenizer.from_pretrained("graziele-fagundes/Sabia7B-QAG", use_fast=True)   

def generate_qa(block_text):
    inputs = tokenizer_qag(block_text, return_tensors="pt")
    outputs = model_qag.generate(**inputs)
    print(tokenizer_qag.decode(outputs[0], skip_special_tokens=True))
    return "pergunta", "resposta"

def create_card_from_history(history: UserHistory | None) -> Card:
    card = Card()
    if history:
        card.state = state_map.get(history.state)
        card.step = history.step
        card.difficulty = history.difficulty
        card.stability = history.stability

        if history.review is not None:
            card.last_review = history.review.replace(tzinfo=timezone.utc)
        else:
            card.last_review = history.review

    return card

def get_latest_history(db, qa_id):
    return db.query(UserHistory).filter_by(qa_id=qa_id).order_by(UserHistory.review.desc()).first()

def start_review(user):
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    qas = db.query(QA, PDFBlock).join(
        PDFBlock, QA.pdf_block_id == PDFBlock.id
    ).filter(QA.user_id == user.id).all()

    revisables = []
    for qa, b in qas:
        history = get_latest_history(db, qa.id)
        due = history.due if history else None
        if due is not None:
            due = due.replace(tzinfo=timezone.utc)
        if due is None or due <= now:
            revisables.append((qa, b, history))

    if not revisables:
        print("Nenhum QA para revisar.")
        return

    print(f"📒 Você tem {len(revisables)} QAs para revisar.")

    for qa, b, history in revisables:
        print("\n------------------------------")
        print("ID:", qa.id)
        print("Bloco: ", b.text_content)
        if history:
            print("Ultima nota:", history.grade)
        print("Q:", qa.question)
        user_answer = input("Sua resposta: ")
        print("A:", qa.answer)

        try:
            print("Nota: 1=Again, 2=Hard, 3=Good, 4=Easy")
            grade = int(input("Nota: "))
            rating = rating_map.get(grade)
            if not rating:
                print("Nota inválida. Pulando.")
                continue
        except Exception as e:
            print("Erro:", e)
            continue

        card = create_card_from_history(history)
        
        updated_card, review_log = scheduler.review_card(card,rating)

        new_history = UserHistory(
            qa_id=qa.id,
            user_answer=user_answer,
            state=updated_card.state.value,
            step=updated_card.step,
            difficulty=updated_card.difficulty,
            stability=updated_card.stability,
            grade=grade,
            review=now,
            due=updated_card.due.replace(tzinfo=timezone.utc) if updated_card.due else None
        )
        db.add(new_history)

        print(f"📅 Próxima revisão: {updated_card.due.astimezone().strftime('%Y-%m-%d %H:%M:%S')}")
        db.commit()

    print("✅ Revisão concluída.")