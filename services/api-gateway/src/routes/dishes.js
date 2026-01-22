const express = require('express');
const router = express.Router();
const { getMenuServiceClient } = require('../grpc/clients');
const { getElasticsearchClient, getRedisClient } = require('../config/cache');
const logger = require('../config/logger');

// Get dish by ID
router.get('/:dishId', async (req, res) => {
  try {
    const { dishId } = req.params;
    const includeSimilar = req.query.include_similar === 'true';
    const redisClient = getRedisClient();

    // Try cache first
    const cacheKey = `dish:${dishId}`;
    const cached = await redisClient.get(cacheKey);
    
    if (cached) {
      logger.info(`Cache hit for dish: ${dishId}`);
      return res.json(JSON.parse(cached));
    }

    const menuServiceClient = getMenuServiceClient();
    
    // Call gRPC service
    menuServiceClient.GetDish(
      { dish_id: dishId, include_similar: includeSimilar },
      async (error, response) => {
        if (error) {
          logger.error('gRPC error:', error);
          return res.status(404).json({
            error: 'Dish not found',
            code: 'NOT_FOUND'
          });
        }

        // Cache the result
        await redisClient.setEx(cacheKey, 3600, JSON.stringify(response));
        
        res.json(response);
      }
    );
  } catch (error) {
    logger.error('Get dish error:', error);
    res.status(500).json({
      error: error.message,
      code: 'INTERNAL_ERROR'
    });
  }
});

// Search dishes
router.get('/search', async (req, res) => {
  try {
    const {
      q: query,
      category,
      min_price,
      max_price,
      limit = 20,
      offset = 0
    } = req.query;

    if (!query) {
      return res.status(400).json({
        error: 'Query parameter is required',
        code: 'MISSING_QUERY'
      });
    }

    const esClient = getElasticsearchClient();
    
    // Build Elasticsearch query
    const esQuery = {
      index: 'dishes',
      body: {
        from: parseInt(offset),
        size: parseInt(limit),
        query: {
          bool: {
            must: [
              {
                multi_match: {
                  query: query,
                  fields: ['name^3', 'description^2', 'ingredients'],
                  fuzziness: 'AUTO'
                }
              }
            ],
            filter: []
          }
        },
        highlight: {
          fields: {
            name: {},
            description: {}
          }
        }
      }
    };

    // Add category filter
    if (category) {
      const categories = Array.isArray(category) ? category : [category];
      esQuery.body.query.bool.filter.push({
        terms: { category: categories }
      });
    }

    // Add price range filter
    if (min_price || max_price) {
      const priceFilter = { range: { 'price.amount': {} } };
      if (min_price) priceFilter.range['price.amount'].gte = parseFloat(min_price);
      if (max_price) priceFilter.range['price.amount'].lte = parseFloat(max_price);
      esQuery.body.query.bool.filter.push(priceFilter);
    }

    const startTime = Date.now();
    const result = await esClient.search(esQuery);
    const searchTime = Date.now() - startTime;

    const response = {
      dishes: result.hits.hits.map(hit => ({
        ...hit._source,
        dish_id: hit._id,
        _score: hit._score
      })),
      total_results: result.hits.total.value,
      page: Math.floor(offset / limit) + 1,
      metadata: {
        search_time_ms: searchTime,
        suggested_queries: [],
        category_counts: {}
      }
    };

    res.json(response);
  } catch (error) {
    logger.error('Search error:', error);
    res.status(500).json({
      error: error.message,
      code: 'SEARCH_ERROR'
    });
  }
});

module.exports = router;
