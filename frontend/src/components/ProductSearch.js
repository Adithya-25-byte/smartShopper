import React, { useState, useCallback, useEffect } from "react";
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  CardMedia,
  Alert,
  Container,
  Skeleton,
  Chip,
  CircularProgress,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Grid,
  Paper,
  Divider,
  Avatar,
  Badge,
  IconButton,
  FormGroup,
  FormControlLabel,
  Switch,
} from "@mui/material";
import {
  Search,
  OpenInNew,
  Star,
  ShoppingCart,
  MoreHoriz,
  TrendingUp,
  SortOutlined,
  MonetizationOn,
} from "@mui/icons-material";
import { styled, alpha } from "@mui/material/styles";
import { useTheme } from "@mui/material/styles";

// Logo URLs
const PLATFORM_LOGOS = {
  flipkart:
    "https://static-assets-web.flixcart.com/batman-returns/batman-returns/p/images/flipkart-logo-dbabcbe86c.svg",
  amazon:
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/1024px-Amazon_logo.svg.png",
};

// Custom styled components
const SearchBar = styled("div")(({ theme }) => ({
  position: "relative",
  borderRadius: theme.shape.borderRadius,
  backgroundColor: alpha(theme.palette.common.white, 0.15),
  "&:hover": {
    backgroundColor: alpha(theme.palette.common.white, 0.25),
  },
  marginRight: theme.spacing(2),
  marginLeft: 0,
  width: "100%",
  [theme.breakpoints.up("sm")]: {
    width: "auto",
    flexGrow: 1,
  },
  display: "flex",
  border: `1px solid ${theme.palette.divider}`,
  boxShadow: theme.shadows[1],
}));

const ScrollContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  gap: theme.spacing(2),
  padding: theme.spacing(2),
  scrollBehavior: "smooth",
}));

const ProductGrid = styled(Grid)(({ theme }) => ({
  gap: theme.spacing(2),
  "& > *": {
    margin: 0, // Reset Grid item margin
  },
}));

const ProductCard = styled(Card)(({ theme }) => ({
  height: "100%",
  display: "flex",
  flexDirection: "column",
  transition: "all 0.2s ease-in-out",
  "&:hover": {
    transform: "translateY(-4px)",
    boxShadow: theme.shadows[8],
  },
  position: "relative",
  overflow: "visible", // Allow badge to overflow
}));

const PlatformBadge = styled(Avatar)(({ theme }) => ({
  width: 28,
  height: 28,
  position: "absolute",
  top: 8,
  right: 8,
  border: `2px solid ${theme.palette.background.paper}`,
  boxShadow: theme.shadows[2],
}));

const DiscountBadge = styled(Chip)(({ theme }) => ({
  position: "absolute",
  top: 8,
  left: 8,
  backgroundColor: theme.palette.error.main,
  color: theme.palette.error.contrastText,
  fontWeight: "bold",
}));

const SortingBar = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(1, 2),
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  marginBottom: theme.spacing(2),
  backgroundColor: theme.palette.background.default,
  borderRadius: theme.shape.borderRadius,
}));

const LoadMoreButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(3, "auto"),
  display: "block",
  minWidth: 180,
}));

const ProductSearch = () => {
  const theme = useTheme();
  const [productName, setProductName] = useState("");
  const [allProducts, setAllProducts] = useState([]);
  const [sortBy, setSortBy] = useState("relevance");
  const [sortedProducts, setSortedProducts] = useState([]);
  const [productSort, setProductSort] = useState("price_low_to_high");
  const [currentPage, setCurrentPage] = useState({ flipkart: 1, amazon: 1 });
  const [loading, setLoading] = useState({
    products: false,
    sentiment: false,
    more: false,
  });
  const [analyzingProducts, setAnalyzingProducts] = useState(new Set());
  const [error, setError] = useState(null);
  const [hasMoreProducts, setHasMoreProducts] = useState(true);

  // Fetch products from both platforms
  const fetchProducts = async (isLoadMore = false) => {
    const loadingKey = isLoadMore ? "more" : "products";
    setLoading((prev) => ({ ...prev, [loadingKey]: true }));

    try {
      const platforms = ["flipkart", "amazon"];
      const fetchPromises = platforms.map((platform) =>
        fetch("http://localhost:5000/search-products", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            productName,
            platform,
            sortBy,
            page: isLoadMore ? currentPage[platform] : 1,
          }),
        }).then((res) => res.json())
      );

      const results = await Promise.all(fetchPromises);
      const newFlipkartProducts = results[0].products || [];
      const newAmazonProducts = results[1].products || [];

      // Update pagination state
      if (isLoadMore) {
        setCurrentPage({
          flipkart:
            newFlipkartProducts.length > 0
              ? currentPage.flipkart + 1
              : currentPage.flipkart,
          amazon:
            newAmazonProducts.length > 0
              ? currentPage.amazon + 1
              : currentPage.amazon,
        });

        setAllProducts((prev) => [
          ...prev,
          ...newFlipkartProducts,
          ...newAmazonProducts,
        ]);
      } else {
        setCurrentPage({ flipkart: 2, amazon: 2 });
        setAllProducts([...newFlipkartProducts, ...newAmazonProducts]);
      }

      // Check if we have more products
      setHasMoreProducts(
        newFlipkartProducts.length > 0 || newAmazonProducts.length > 0
      );

      return {
        flipkart: newFlipkartProducts,
        amazon: newAmazonProducts,
      };
    } catch (error) {
      console.error("Error fetching products:", error);
      setError(`Error fetching products: ${error.message}`);
      return { flipkart: [], amazon: [] };
    } finally {
      setLoading((prev) => ({ ...prev, [loadingKey]: false }));
    }
  };

  // Analyze sentiments in batches
  const analyzeSentiments = async (newProducts) => {
    setLoading((prev) => ({ ...prev, sentiment: true }));
    const batchSize = 4; // Analyze 4 products at a time

    const allNewProducts = [
      ...(newProducts.flipkart || []),
      ...(newProducts.amazon || []),
    ];

    // Process products in batches
    for (let i = 0; i < allNewProducts.length; i += batchSize) {
      const batch = allNewProducts.slice(i, i + batchSize);
      const analyzePromises = batch.map(async (product) => {
        setAnalyzingProducts((prev) => new Set([...prev, product.name]));

        try {
          const response = await fetch(
            "http://localhost:5000/analyze-product-reviews",
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ product, platform: product.platform }),
            }
          );

          const result = await response.json();

          setAllProducts((prev) =>
            prev.map((p) =>
              p.name === product.name && p.platform === product.platform
                ? { ...p, sentimentSummary: result.sentimentSummary }
                : p
            )
          );
        } catch (error) {
          console.error(`Error analyzing ${product.name}:`, error);
        } finally {
          setAnalyzingProducts((prev) => {
            const newSet = new Set(prev);
            newSet.delete(product.name);
            return newSet;
          });
        }
      });

      await Promise.all(analyzePromises);
    }

    setLoading((prev) => ({ ...prev, sentiment: false }));
  };

  const handleSearch = useCallback(async () => {
    if (!productName.trim()) {
      setError("Please enter a product name");
      return;
    }

    setAllProducts([]);
    setError(null);
    setAnalyzingProducts(new Set());
    setHasMoreProducts(true);

    const newProducts = await fetchProducts(false);
    analyzeSentiments(newProducts);
  }, [productName, sortBy]);

  const handleLoadMore = async () => {
    if (loading.more || !hasMoreProducts) return;

    const newProducts = await fetchProducts(true);
    analyzeSentiments(newProducts);
  };

  // Sort products based on user selection
  useEffect(() => {
    if (allProducts.length === 0) {
      setSortedProducts([]);
      return;
    }

    const productsWithPrice = allProducts.map((product) => {
      // Extract numeric price value for sorting
      const priceValue = parseFloat(product.price.replace(/[^0-9.]/g, "")) || 0;
      return { ...product, priceValue };
    });

    let sorted = [...productsWithPrice];

    switch (productSort) {
      case "price_low_to_high":
        sorted.sort((a, b) => a.priceValue - b.priceValue);
        break;
      case "price_high_to_low":
        sorted.sort((a, b) => b.priceValue - a.priceValue);
        break;
      case "sentiment_high":
        sorted.sort((a, b) => {
          const sentimentA =
            a.sentimentSummary?.overall_sentiment === "Positive"
              ? 1
              : a.sentimentSummary?.overall_sentiment === "Neutral"
              ? 0
              : -1;
          const sentimentB =
            b.sentimentSummary?.overall_sentiment === "Positive"
              ? 1
              : b.sentimentSummary?.overall_sentiment === "Neutral"
              ? 0
              : -1;
          return sentimentB - sentimentA;
        });
        break;
      case "sentiment_low":
        sorted.sort((a, b) => {
          const sentimentA =
            a.sentimentSummary?.overall_sentiment === "Negative"
              ? 1
              : a.sentimentSummary?.overall_sentiment === "Neutral"
              ? 0
              : -1;
          const sentimentB =
            b.sentimentSummary?.overall_sentiment === "Negative"
              ? 1
              : b.sentimentSummary?.overall_sentiment === "Neutral"
              ? 0
              : -1;
          return sentimentB - sentimentA;
        });
        break;
      default:
        break;
    }

    setSortedProducts(sorted);
  }, [allProducts, productSort]);

  // Get recommended products (lowest price first)
  const getRecommendedProducts = () => {
    if (allProducts.length === 0) return [];

    // Create a deep copy and sort by price
    const productsWithPrice = allProducts.map((product) => {
      const priceValue = parseFloat(product.price.replace(/[^0-9.]/g, "")) || 0;
      return { ...product, priceValue };
    });

    return productsWithPrice
      .sort((a, b) => a.priceValue - b.priceValue)
      .slice(0, 3); // Show top 3 cheapest products
  };

  const recommendedProducts = getRecommendedProducts();

  // Extract discount value as a number for display purposes
  const getDiscountValue = (discountText) => {
    if (!discountText) return 0;
    const matches = discountText.match(/(\d+)/);
    return matches ? parseInt(matches[0]) : 0;
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography
        variant="h4"
        component="h1"
        sx={{ mb: 4, fontWeight: "bold", color: theme.palette.primary.main }}
      >
        Smart Shopper - The Only Product Recommender You Need
      </Typography>

      {/* Search Section */}
      <Paper
        elevation={3}
        sx={{
          p: 3,
          mb: 4,
          background: `linear-gradient(to right, ${theme.palette.primary.light}, ${theme.palette.primary.main})`,
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ mb: 2, color: "white" }}>
              Find the best products at the best prices
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <SearchBar>
              <TextField
                fullWidth
                placeholder="Search for products..."
                variant="outlined"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    borderRadius: 0,
                    "& fieldset": { border: "none" },
                  },
                }}
                onKeyPress={(e) => {
                  if (e.key === "Enter") handleSearch();
                }}
              />
              <Button
                variant="contained"
                color="primary"
                onClick={handleSearch}
                disabled={loading.products || !productName.trim()}
                sx={{ borderRadius: "0 4px 4px 0", px: 3 }}
              >
                {loading.products ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  <Search />
                )}
              </Button>
            </SearchBar>
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl
              fullWidth
              variant="outlined"
              sx={{
                backgroundColor: "white",
                borderRadius: theme.shape.borderRadius,
              }}
            >
              <InputLabel id="sort-by-label">Sort By</InputLabel>
              <Select
                labelId="sort-by-label"
                id="sort-by"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                label="Sort By"
                startAdornment={
                  <SortOutlined
                    sx={{ mr: 1, color: theme.palette.text.secondary }}
                  />
                }
              >
                <MenuItem value="relevance">Relevance</MenuItem>
                <MenuItem value="popularity">Popularity</MenuItem>
                <MenuItem value="price_low_to_high">
                  Price: Low to High
                </MenuItem>
                <MenuItem value="price_high_to_low">
                  Price: High to Low
                </MenuItem>
                <MenuItem value="newest">Newest First</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      {/* Recommended Products Section */}
      {recommendedProducts.length > 0 && (
        <Box sx={{ mb: 6 }}>
          <Paper
            elevation={3}
            sx={{
              p: 2,
              mb: 3,
              background: `linear-gradient(to right, ${theme.palette.success.light}, ${theme.palette.success.main})`,
              color: "white",
              borderRadius: "8px 8px 0 0",
            }}
          >
            <Typography
              variant="h6"
              sx={{ fontWeight: "bold", display: "flex", alignItems: "center" }}
            >
              <MonetizationOn sx={{ mr: 1 }} /> Best Price Recommendations
            </Typography>
          </Paper>

          <Grid container spacing={2}>
            {recommendedProducts.map((product, index) => (
              <Grid item xs={12} sm={6} md={4} key={`recommended-${index}`}>
                <ProductCard elevation={3}>
                  {getDiscountValue(product.discount) > 0 && (
                    <DiscountBadge
                      size="small"
                      label={product.discount}
                      icon={<TrendingUp fontSize="small" />}
                    />
                  )}

                  <PlatformBadge
                    src={PLATFORM_LOGOS[product.platform]}
                    alt={product.platform}
                    title={
                      product.platform === "flipkart" ? "Flipkart" : "Amazon"
                    }
                  />

                  <CardMedia
                    component="img"
                    height="180"
                    image={product.img || "/api/placeholder/280/140"}
                    alt={product.name}
                    sx={{ objectFit: "contain", p: 2 }}
                  />

                  <CardContent
                    sx={{
                      flexGrow: 1,
                      display: "flex",
                      flexDirection: "column",
                    }}
                  >
                    <Typography
                      variant="subtitle1"
                      component="h3"
                      sx={{
                        fontWeight: "medium",
                        mb: 1,
                        height: "3em",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {product.name}
                    </Typography>

                    <Typography
                      variant="h6"
                      color="primary"
                      sx={{ mb: 2, fontWeight: "bold" }}
                    >
                      {product.price}
                    </Typography>

                    {product.sentimentSummary && (
                      <Chip
                        icon={<Star sx={{ color: "gold" }} />}
                        label={`${product.sentimentSummary.overall_sentiment} (${product.sentimentSummary.confidence}%)`}
                        color={
                          product.sentimentSummary.overall_sentiment ===
                          "Positive"
                            ? "success"
                            : product.sentimentSummary.overall_sentiment ===
                              "Negative"
                            ? "error"
                            : "default"
                        }
                        variant="outlined"
                        size="small"
                        sx={{ alignSelf: "flex-start", mb: 2 }}
                      />
                    )}

                    <Button
                      variant="contained"
                      color="primary"
                      endIcon={<OpenInNew />}
                      href={product.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{ mt: "auto" }}
                    >
                      View Details
                    </Button>
                  </CardContent>
                </ProductCard>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* All Products Section */}
      {sortedProducts.length > 0 && (
        <Box>
          <SortingBar elevation={1}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: "medium",
                display: "flex",
                alignItems: "center",
              }}
            >
              <ShoppingCart sx={{ mr: 1 }} /> All Products (
              {sortedProducts.length})
            </Typography>

            <FormControl variant="outlined" size="small" sx={{ minWidth: 200 }}>
              <InputLabel id="product-sort-label">Sort Products</InputLabel>
              <Select
                labelId="product-sort-label"
                id="product-sort"
                value={productSort}
                onChange={(e) => setProductSort(e.target.value)}
                label="Sort Products"
              >
                <MenuItem value="price_low_to_high">
                  Price: Low to High
                </MenuItem>
                <MenuItem value="price_high_to_low">
                  Price: High to Low
                </MenuItem>
                <MenuItem value="sentiment_high">
                  Sentiment: Most Positive
                </MenuItem>
                <MenuItem value="sentiment_low">
                  Sentiment: Most Negative
                </MenuItem>
              </Select>
            </FormControl>
          </SortingBar>

          <ScrollContainer>
            <ProductGrid container>
              {sortedProducts.map((product, index) => (
                <Grid
                  item
                  xs={12}
                  sm={6}
                  md={4}
                  lg={3}
                  key={`product-${index}`}
                >
                  <ProductCard elevation={2}>
                    {getDiscountValue(product.discount) > 0 && (
                      <DiscountBadge
                        size="small"
                        label={product.discount}
                        icon={<TrendingUp fontSize="small" />}
                      />
                    )}

                    <PlatformBadge
                      src={PLATFORM_LOGOS[product.platform]}
                      alt={product.platform}
                    />

                    <CardMedia
                      component="img"
                      height="160"
                      image={product.img || "/api/placeholder/280/140"}
                      alt={product.name}
                      sx={{ objectFit: "contain", p: 2 }}
                    />

                    <CardContent
                      sx={{
                        flexGrow: 1,
                        display: "flex",
                        flexDirection: "column",
                      }}
                    >
                      <Typography
                        variant="subtitle1"
                        component="h3"
                        sx={{
                          fontWeight: "medium",
                          mb: 1,
                          height: "3em",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          display: "-webkit-box",
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: "vertical",
                        }}
                      >
                        {product.name}
                      </Typography>

                      <Typography
                        variant="h6"
                        color="primary"
                        sx={{ mb: 1, fontWeight: "bold" }}
                      >
                        {product.price}
                      </Typography>

                      {analyzingProducts.has(product.name) ? (
                        <Box
                          sx={{ display: "flex", alignItems: "center", mb: 2 }}
                        >
                          <CircularProgress size={16} sx={{ mr: 1 }} />
                          <Typography variant="caption">
                            Analyzing reviews...
                          </Typography>
                        </Box>
                      ) : product.sentimentSummary ? (
                        <Chip
                          icon={<Star sx={{ color: "gold" }} />}
                          label={`${product.sentimentSummary.overall_sentiment} (${product.sentimentSummary.confidence}%)`}
                          color={
                            product.sentimentSummary.overall_sentiment ===
                            "Positive"
                              ? "success"
                              : product.sentimentSummary.overall_sentiment ===
                                "Negative"
                              ? "error"
                              : "default"
                          }
                          variant="outlined"
                          size="small"
                          sx={{ alignSelf: "flex-start", mb: 2 }}
                        />
                      ) : null}

                      <Button
                        variant="contained"
                        color="primary"
                        endIcon={<OpenInNew />}
                        href={product.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{ mt: "auto" }}
                        size="small"
                      >
                        View Details
                      </Button>
                    </CardContent>
                  </ProductCard>
                </Grid>
              ))}
            </ProductGrid>

            {hasMoreProducts && (
              <LoadMoreButton
                variant="outlined"
                color="primary"
                onClick={handleLoadMore}
                disabled={loading.more}
                startIcon={
                  loading.more ? <CircularProgress size={20} /> : <MoreHoriz />
                }
              >
                {loading.more ? "Loading more..." : "Load More Products"}
              </LoadMoreButton>
            )}
          </ScrollContainer>
        </Box>
      )}

      {/* Loading State */}
      {loading.products && !loading.more && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Searching for products...
          </Typography>
          <Grid container spacing={2}>
            {Array(8)
              .fill(0)
              .map((_, idx) => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={idx}>
                  <Skeleton
                    variant="rectangular"
                    height={300}
                    sx={{ borderRadius: 2 }}
                  />
                </Grid>
              ))}
          </Grid>
        </Box>
      )}
    </Container>
  );
};

export default ProductSearch;
