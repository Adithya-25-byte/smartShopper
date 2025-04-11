from transformers import AutoModelForSequenceClassification, AutoTokenizer
import os

MODEL_NAME = "Dmyadav2001/Sentimental-Analysis"
MODEL_DIR = "models/sentiment_model"

def download_model():
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Download and save tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.save_pretrained(MODEL_DIR)

    # Download and save model
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.save_pretrained(MODEL_DIR)

    print(f"Model and tokenizer saved to '{MODEL_DIR}'")

if __name__ == "__main__":
    download_model()
