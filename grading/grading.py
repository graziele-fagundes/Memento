from sentence_transformers import SentenceTransformer, util
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "graziele-fagundes/BERTimbau-Grading"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, device_map="cuda")

def predict_grade(question, reference_answer, student_answer, conf_threshold=0.6):
    question = question.strip()
    reference_answer = reference_answer.strip()
    student_answer = student_answer.strip()
    question_ref = f"{question} {reference_answer}"

    # Classificação com BERTimbau
    inputs = tokenizer(question_ref, student_answer,
                       return_tensors="pt",
                       padding="max_length",
                       truncation=True,
                       max_length=512).to("cuda")
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1).squeeze()
        predicted_class = torch.argmax(probs).item()
        confidence = probs[predicted_class].item()

    final_grade = int(round(predicted_class))

    print(f"Nota: {predicted_class} (confiança {confidence:.2f})")
    
    return final_grade
