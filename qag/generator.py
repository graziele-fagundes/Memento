from database import SessionLocal
from models import QA, UserHistory, PDFBlock
from datetime import datetime, timezone
from fsrs import Scheduler, Card, Rating, State
from grading.grading import predict_grade
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import BitsAndBytesConfig
import torch

# FSRS
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

# Modelo QAG
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)
model_qag = AutoModelForCausalLM.from_pretrained("graziele-fagundes/Sabia7B-QAG", device_map="cuda", quantization_config=bnb_config)
tokenizer_qag = AutoTokenizer.from_pretrained("graziele-fagundes/Sabia7B-QAG", use_fast=True)   


def generate_qa(block, user_id):
    prompt = (
        "Dado o contexto, gere uma pergunta e uma resposta. "
        "A resposta de cada pergunta é um segmento do contexto correspondente. "
        "A resposta deve ser curta e direta.\n"
        f"### Contexto: {block.text_content}\n### Pergunta:"
    )
    inputs = tokenizer_qag(prompt, return_tensors="pt").input_ids.to("cuda")

    db = SessionLocal()
    seen_qas = set()

    print("\n" + "=" * 100)
    print(f"📘 Texto usado como contexto (tamanho {len(block.text_content)}):\n{block.text_content}\n")

    # ==========================
    # Etapa 1: Greedy
    # ==========================
    while True:
        output = model_qag.generate(
            input_ids=inputs,
            max_length=2048,
            return_dict_in_generate=True,
            output_scores=True,
            do_sample=False
        )
        decoded = tokenizer_qag.decode(output.sequences[0], skip_special_tokens=True)

        if "### Pergunta:" in decoded and "### Resposta:" in decoded:
            question = decoded.split("### Pergunta:")[1].split("### Resposta:")[0].strip()
            answer = decoded.split("### Resposta:")[1].strip()
        else:
            question = decoded.strip()
            answer = ""

        if (question, answer) in seen_qas:
            return []
        seen_qas.add((question, answer))

        # Deixa pergunta e resposta bem formuladas (? e . no final) (primeira letra maiúscula)
        if not question.endswith("?"):
            question += "?"
        if not answer.endswith("."):
            answer += "."
        question = question[0].upper() + question[1:]
        answer = answer[0].upper() + answer[1:]

        print("=" * 60)
        print("✨ Estratégia: Greedy Search")
        print(f"\nPergunta:\n{question}")
        print(f"Resposta:\n{answer}\n")
        print("=" * 60)

        user_input = input("👉 Digite [a = aprovar | r = reprovar | g = gerar de novo] > ").lower()

        if user_input == 'a':
            qa = QA(user_id=user_id, pdf_block_id=block.id, question=question, answer=answer)
            db.add(qa)
            db.commit()
            db.refresh(qa)
            print("✅ QA aprovada e salva!")
            return [(question, answer)]

        elif user_input == 'r':
            print("❌ QA rejeitada. Passando para o próximo bloco.")
            return []

        elif user_input == 'g':
            print("🔄 Mudando para Top-p Sampling...\n")
            break

        else:
            print("⚠️ Opção inválida.")
            continue

    # ==========================
    # Etapa 2: Top-p (loop até decidir)
    # ==========================
    while True:
        output = model_qag.generate(
            input_ids=inputs,
            max_length=2048,
            return_dict_in_generate=True,
            output_scores=True,
            do_sample=True,
            top_p=0.9
        )
        decoded = tokenizer_qag.decode(output.sequences[0], skip_special_tokens=True)

        if "### Pergunta:" in decoded and "### Resposta:" in decoded:
            question = decoded.split("### Pergunta:")[1].split("### Resposta:")[0].strip()
            answer = decoded.split("### Resposta:")[1].strip()
        else:
            question = decoded.strip()
            answer = ""

        if (question, answer) in seen_qas:
            print("⚠️ QA duplicada encontrada, gerando de novo...")
            continue
        seen_qas.add((question, answer))

        # Deixa pergunta e resposta bem formuladas (? e . no final) (primeira letra maiúscula)
        if not question.endswith("?"):
            question += "?"
        if not answer.endswith("."):
            answer += "."
        question = question[0].upper() + question[1:]
        answer = answer[0].upper() + answer[1:]

        print("=" * 60)
        print("✨ Estratégia: Top-p Sampling")
        print(f"\nPergunta:\n{question}")
        print(f"Resposta:\n{answer}\n")
        print("=" * 60)

        user_input = input("👉 Digite [a = aprovar | r = reprovar | g = gerar de novo] > ").lower()

        if user_input == 'a':
            qa = QA(user_id=user_id, pdf_block_id=block.id, question=question, answer=answer)
            db.add(qa)
            db.commit()
            db.refresh(qa)
            print("✅ QA aprovada e salva!")
            return [(question, answer)]

        elif user_input == 'r':
            print("❌ QA rejeitada. Passando para o próximo bloco.")
            return []

        elif user_input == 'g':
            print("🔄 Gerando novamente (Top-p)...\n")
            continue

        else:
            print("⚠️ Opção inválida.")
            continue


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
        if history:
            print("Ultima nota:", history.grade)
        print("Pergunta:", qa.question)
        print("Gabarito:", qa.answer)
        user_answer = input("\nSua resposta: ")
        
        try:
            grade = predict_grade(qa.question, qa.answer, user_answer) + 1 
            print(f"Nota: {grade} (1-4)")
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
            user_id=user.id,
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

        print(f"📅 Próxima revisão: {updated_card.due.astimezone().strftime('%d/%m/%Y %H:%M')}")
        db.commit()

    print("✅ Revisão concluída.")