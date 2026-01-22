const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const swaggerUi = require('swagger-ui-express');
const YAML = require('yamljs');
const path = require('path');
require('dotenv').config();

const logger = require('./config/logger');
const { initializeRedis, initializeMemcached, initializeElasticsearch } = require('./config/cache');
const { initializeGrpcClients } = require('./grpc/clients');
const menuRoutes = require('./routes/menu');
const dishesRoutes = require('./routes/dishes');
const healthRoutes = require('./routes/health');
const rateLimiter = require('./middleware/rateLimiter');

const app = express();
const PORT = process.env.PORT || 8080;

// Load OpenAPI specification
const swaggerDocument = YAML.load(path.join(__dirname, '../openapi.yaml'));

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));
app.use(rateLimiter);

// Logging middleware
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`, {
    ip: req.ip,
    userAgent: req.get('user-agent')
  });
  next();
});

// Swagger UI
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

// API Routes
app.use('/api/v1/health', healthRoutes);
app.use('/api/v1/menu', menuRoutes);
app.use('/api/v1/dishes', dishesRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'Menu Scanner API Gateway',
    version: '1.0.0',
    documentation: '/api-docs',
    endpoints: {
      health: '/api/v1/health',
      menu: '/api/v1/menu',
      dishes: '/api/v1/dishes'
    }
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  logger.error('Unhandled error:', err);
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error',
    code: err.code || 'INTERNAL_ERROR'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    code: 'NOT_FOUND'
  });
});

// Initialize services and start server
async function start() {
  try {
    logger.info('Initializing services...');
    
    // Initialize cache services
    await initializeRedis();
    await initializeMemcached();
    await initializeElasticsearch();
    
    // Initialize gRPC clients
    await initializeGrpcClients();
    
    // Start server
    app.listen(PORT, () => {
      logger.info(`API Gateway running on port ${PORT}`);
      logger.info(`API Documentation available at http://localhost:${PORT}/api-docs`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully...');
  process.exit(0);
});

start();

module.exports = app;
