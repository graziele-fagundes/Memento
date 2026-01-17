import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "graziele-fagundes/BERTimbau-Grading"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, device_map="cuda")
model.eval()

def predict_grade(question, reference_answer, student_answer):
    question = question.strip()
    reference_answer = reference_answer.strip()
    student_answer = student_answer.strip()
    question_ref = f"{question} {reference_answer}"

    inputs = tokenizer(question_ref, student_answer,
                       return_tensors="pt",
                       padding="max_length",
                       truncation=True,
                       max_length=512).to("cuda")
    with torch.no_grad():
        # Cálculo da predição
        outputs = model(**inputs)
        predicted_class = torch.argmax(outputs.logits, dim=1).item()

        # Cálculo da confiança
        probabilities = torch.softmax(outputs.logits, dim=1)
        confidence = probabilities[0][predicted_class].item()

    final_grade = int(round(predicted_class))
    
    return final_grade, confidence
