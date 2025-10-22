from sentence_transformers import SentenceTransformer, util
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Modelo de classificação
model_name = "graziele-fagundes/BERTimbau-Grading"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, device_map="cuda")

# Modelo de embeddings
embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

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

    # Penalização por baixa confiança
    if confidence < conf_threshold:
        # Similaridade de cosseno
        embeddings = embed_model.encode([reference_answer, student_answer], convert_to_tensor=True, show_progress_bar=False)
        cosine_sim = util.cos_sim(embeddings[0], embeddings[1]).item()
        
        # Combinação entre modelo, confiança e similaridade
        score = (predicted_class * confidence) + (cosine_sim * (1 - confidence))
        
    else:
        score = predicted_class

    # Converter para inteiro 0-3
    final_grade = int(round(score))
    final_grade = max(0, min(3, final_grade))

    print(f"Modelo: {predicted_class} (confiança {confidence:.2f})")
    if confidence < conf_threshold:
        print(f"Similaridade: {cosine_sim:.2f} → Score combinado: {score:.2f}")
    
    return final_grade
