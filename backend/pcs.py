from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from scrapers import FlipkartScraper, AmazonScraper  # Import the scraper classes

# Machine Learning Libraries
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import tensorflow as tf

import logging

import os

# Suppress TensorFlow logs and warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow logs (0 = all logs, 3 = no logs)
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable DNN optimizations
tf.get_logger().setLevel(logging.ERROR)  # Suppress TensorFlow deprecation warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pcs")

# Initialize FastAPI
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sentiment Analysis Model Loading
try:
    MODEL_PATH = "./models/sentiment_model"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = TFAutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    logger.info(f"Sentiment model successfully loaded from {MODEL_PATH}")
except Exception as e:
    logger.error(f"Failed to load sentiment model: {e}")
    model = None
    tokenizer = None

class ProductQuery(BaseModel):
    query: str
    platform: str
    sort_by: str = "relevance"
    page: int = 1
    batch_size: int = 10

class ReviewItem(BaseModel):
    product: str
    review: str
    
class ReviewQuery(BaseModel):
    url: str
    platform: str    

@app.post("/scrape-products")
async def scrape_products(query: ProductQuery):
    """Fetch product data."""
    try:
        if query.platform == "flipkart":
            products = FlipkartScraper.fetch_products(
                query.query, 
                query.sort_by, 
                query.page, 
                query.batch_size
            )
        elif query.platform == "amazon":
            products = AmazonScraper.fetch_products(
                query.query, 
                query.sort_by, 
                query.page, 
                query.batch_size
            )
        elif query.platform == "both":
            flipkart_products = FlipkartScraper.fetch_products(
                query.query, 
                query.sort_by, 
                query.page, 
                query.batch_size
            )
            amazon_products = AmazonScraper.fetch_products(
                query.query, 
                query.sort_by, 
                query.page, 
                query.batch_size
            )
            products = flipkart_products + amazon_products
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform")
        
        return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")
    
def clean_review(review):
    """Clean individual review text for consistency."""
    cleaned = review.lstrip("0123456789")
    cleaned = cleaned.split("READ MORE")[0]
    cleaned = cleaned.replace("Perfect product!", "").replace("Awesome", "").replace("Decent product", "")
    return cleaned.strip()


@app.post("/scrape-reviews")
async def scrape_reviews(query: ReviewQuery):
    """Fetch and clean reviews for a product."""
    try:
        if query.platform == "flipkart":
            reviews = FlipkartScraper.fetch_reviews(query.url)
        elif query.platform == "amazon":
            reviews = AmazonScraper.fetch_reviews(query.url)
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform")

        cleaned_reviews = [clean_review(review) for review in reviews if isinstance(review, str) and review.strip()]
        return {"reviews": cleaned_reviews}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reviews: {str(e)}")


@app.post("/analyze-reviews")
async def analyze_reviews(reviews: List[ReviewItem]):
    """Analyze sentiments of reviews."""
    try:
        results = []
        for item in reviews:
            
            inputs = tokenizer(item.review, return_tensors="tf", padding=True, truncation=True)
            outputs = model(**inputs)
            logits = outputs.logits
            predicted_class = tf.argmax(logits, axis=1).numpy()[0]

            sentiment_labels = ["Negative", "Positive", "Neutral"]
            sentiment = sentiment_labels[predicted_class]
    
            confidence = tf.nn.softmax(logits)[0][predicted_class].numpy().item()

            results.append({
                "product": item.product,
                "sentiment_summary": {
                    "overall_sentiment": sentiment,
                    "confidence": round(confidence * 100, 2),
                },
            })

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing reviews: {str(e)}")