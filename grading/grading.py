from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

model_name = "graziele-fagundes/bertimbau-grading"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, device_map="cuda")

def predict_grade(question, reference_answer, student_answer):
    question_ref = f"{question} {reference_answer}"

    # Tokenização e predição
    inputs = tokenizer(question_ref, student_answer,
                       return_tensors="pt",
                       padding="max_length",
                       truncation=True,
                       max_length=512).to("cuda")
    with torch.no_grad():
        outputs = model(**inputs)
        predicted_class = torch.argmax(outputs.logits, dim=1).item()

    return int(predicted_class)