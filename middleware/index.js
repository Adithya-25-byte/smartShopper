const express = require("express");
const axios = require("axios");
const bodyParser = require("body-parser");
const cors = require("cors");
const winston = require("winston");

// Configure logging
const logger = winston.createLogger({
  level: "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: "error.log", level: "error" }),
    new winston.transports.File({ filename: "combined.log" }),
    new winston.transports.Console({
      format: winston.format.simple(),
    }),
  ],
});

// Create Express app
const app = express();

// Middleware configuration
app.use(
  cors({
    origin: process.env.FRONTEND_URL || "http://localhost:3000",
    methods: ["POST", "GET", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);
app.use(bodyParser.json());

// Configuration
const PYTHON_BACKEND =
  process.env.PYTHON_BACKEND_URL || "http://localhost:8000";
const TIMEOUT = 100000;

// Utility functions
function cleanReview(review) {
  // Remove the rating number at the start
  let cleaned = review.replace(/^\d+/, "");

  // Remove 'READ MORE' and anything following it
  cleaned = cleaned.split("READ MORE")[0];

  // Remove common artifacts
  cleaned = cleaned.replace(/Perfect product!|Awesome|Decent product/, "");

  // Trim whitespace and return
  return cleaned.trim();
}

// Updated endpoint to handle "Load more" functionality
app.post("/search-products", async (req, res) => {
  const { productName, platform, sortBy = "relevance", page = 1 } = req.body;

  try {
    if (!productName) {
      return res.status(400).json({ error: "Product name is required" });
    }

    const encodedProductName = productName.trim().replace(/\s+/g, "+");
    console.log(
      `Searching for ${encodedProductName} on ${platform} (sort: ${sortBy}, page: ${page})...`
    );

    const productsResponse = await axios.post(
      `${PYTHON_BACKEND}/scrape-products`,
      {
        query: encodedProductName,
        platform,
        sort_by: sortBy,
        page,
        batch_size: 10, // Default batch size
      }
    );

    console.log(`${platform} products response:`, productsResponse.data);

    // Make sure we're sending the products array
    const products = productsResponse.data.products || [];
    res.json({ products });
  } catch (error) {
    console.error(`Error in /search-products:`, error);
    res.status(500).json({ error: error.message });
  }
});

app.post("/analyze-product-reviews", async (req, res) => {
  const { product, platform } = req.body;

  try {
    // Get reviews
    const reviewsResponse = await axios.post(
      `${PYTHON_BACKEND}/scrape-reviews`,
      {
        url: product.url,
        platform,
      }
    );

    const reviews = reviewsResponse.data.reviews || [];

    if (reviews.length === 0) {
      return res.json({
        sentimentSummary: {
          overall_sentiment: "No reviews",
          confidence: 0,
        },
      });
    }

    // Analyze reviews
    const reviewsToAnalyze = reviews.map((review) => ({
      product: product.name,
      review: cleanReview(review),
    }));

    const sentimentResponse = await axios.post(
      `${PYTHON_BACKEND}/analyze-reviews`,
      reviewsToAnalyze
    );

    res.json({ sentimentSummary: sentimentResponse.data[0].sentiment_summary });
  } catch (error) {
    logger.error("Review analysis error", {
      product: product.name,
      error: error.message,
    });
    res.status(500).json({ error: error.message });
  }
});

// Start the server
const PORT = process.env.PORT || 5000;
const server = app.listen(PORT, () => {
  logger.info(`Node.js server running on http://localhost:${PORT}`);
});

module.exports = app;
