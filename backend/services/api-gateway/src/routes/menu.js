const express = require('express');
const multer = require('multer');
const router = express.Router();
const { getMenuServiceClient } = require('../grpc/clients');
const { getRedisClient } = require('../config/cache');
const logger = require('../config/logger');

// Configure multer for file upload
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image files are allowed'), false);
    }
  }
});

// Upload and process menu image
router.post('/upload', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        error: 'No image file provided',
        code: 'MISSING_IMAGE'
      });
    }

    const options = req.body.options ? JSON.parse(req.body.options) : {};
    const menuServiceClient = getMenuServiceClient();

    // Prepare gRPC request
    const grpcRequest = {
      image_data: req.file.buffer,
      format: req.file.mimetype.split('/')[1],
      options: {
        extract_prices: options.extract_prices !== false,
        extract_descriptions: options.extract_descriptions !== false,
        extract_ingredients: options.extract_ingredients || false,
        language: options.language || 'en',
        use_cache: options.use_cache !== false
      }
    };

    // Call gRPC service
    menuServiceClient.ProcessMenuImage(grpcRequest, (error, response) => {
      if (error) {
        logger.error('gRPC error:', error);
        return res.status(500).json({
          error: 'Failed to process menu image',
          code: 'PROCESSING_ERROR',
          details: error.message
        });
      }

      res.json(response);
    });
  } catch (error) {
    logger.error('Upload error:', error);
    res.status(500).json({
      error: error.message,
      code: 'INTERNAL_ERROR'
    });
  }
});

// Get menu by ID
router.get('/:menuId', async (req, res) => {
  try {
    const { menuId } = req.params;
    const redisClient = getRedisClient();

    // Try to get from cache first
    const cached = await redisClient.get(`menu:${menuId}`);
    if (cached) {
      logger.info(`Cache hit for menu: ${menuId}`);
      return res.json(JSON.parse(cached));
    }

    // If not in cache, retrieve from service
    // This is a placeholder - implement actual retrieval logic
    res.status(404).json({
      error: 'Menu not found',
      code: 'NOT_FOUND'
    });
  } catch (error) {
    logger.error('Get menu error:', error);
    res.status(500).json({
      error: error.message,
      code: 'INTERNAL_ERROR'
    });
  }
});

module.exports = router;
