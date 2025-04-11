from transformers import AutoModelForSequenceClassification
import os

MODEL_NAME = "Dmyadav2001/Sentimental-Analysis"
MODEL_DIR = "models/sentiment_model"

def download_model():
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Download and save model only
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.save_pretrained(MODEL_DIR)

    print(f"Model saved to '{MODEL_DIR}'")

if __name__ == "__main__":
    download_model()
