from database import SessionLocal
from models import Flashcard, PDFBlock
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

def generate_flashcard(block_text):
    return "Pergunta placeholder?", "Resposta placeholder."

def create_card_from_db(flashcard: Flashcard) -> Card:
    card = Card()

    if flashcard.difficulty is not None:
        card.state = state_map.get(flashcard.state)
        card.step = flashcard.step
        card.difficulty = flashcard.difficulty
        card.stability = flashcard.stability

        if flashcard.last_review is not None:
            card.last_review = flashcard.last_review.replace(tzinfo=timezone.utc)
        else:
            card.last_review = flashcard.last_review

        card.due = flashcard.due

    return card

def start_review(user):
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    flashcards = db.query(Flashcard, PDFBlock).join(PDFBlock, Flashcard.pdf_block_id == PDFBlock.id).filter(Flashcard.user_id == user.id).all()

    revisables = []
    for f,b in flashcards:
        due = f.due
        if due is not None:
            due = due.replace(tzinfo=timezone.utc)
        if due is None or due <= now:
            revisables.append((f, b))

    if not revisables:
        print("Nenhum flashcard para revisar.")
        return

    print(f"📒 Você tem {len(revisables)} flashcards para revisar.")
    
    # Order by due date (none first, then by due date)
    revisables.sort(key=lambda x: (x[0].due is not None, x[0].due))

    for f,b in revisables:
        print("\n------------------------------")
        print("ID:", f.id)
        print("Bloco: ", b.text_content)
        print("Q:", f.question)
        input("Sua resposta: ")
        print("A:", f.answer)

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

        card = create_card_from_db(f)
        
        updated_card, review_log = scheduler.review_card(card, rating)

        f.state = updated_card.state.value
        f.step = updated_card.step
        f.difficulty = updated_card.difficulty
        f.stability = updated_card.stability
        f.last_grade = review_log.rating.value
        f.last_review = review_log.review_datetime
        f.due = updated_card.due

        print(f"📅 Próxima revisão: {f.due.astimezone().strftime('%Y-%m-%d %H:%M:%S')}")

        db.commit()
    print("✅ Revisão concluída.")

