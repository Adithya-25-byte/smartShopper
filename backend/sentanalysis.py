from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import tensorflow as tf

# Specify the local directory where the model and tokenizer are saved
local_directory = "./models/sentiment_model"

# Load the tokenizer from the local directory
tokenizer = AutoTokenizer.from_pretrained(local_directory)

# Load the TensorFlow model from the local directory
model = TFAutoModelForSequenceClassification.from_pretrained(local_directory)

# Test the model
text = "I love this product🙂!"
inputs = tokenizer(text, return_tensors="tf")
outputs = model(**inputs)
logits = outputs.logits
probabilities = tf.nn.softmax(logits, axis=-1)
predicted_class = tf.argmax(probabilities, axis=-1).numpy()[0]
print(f"Predicted class: {model.config.id2label[predicted_class]}")
print(model.config.id2label)

