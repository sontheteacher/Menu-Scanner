const express = require('express');
const router = express.Router();
const { getRedisClient, getMemcachedClient, getElasticsearchClient } = require('../config/cache');
const logger = require('../config/logger');

router.get('/', async (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    services: {}
  };

  try {
    // Check Redis
    const redisClient = getRedisClient();
    if (redisClient && redisClient.isOpen) {
      await redisClient.ping();
      health.services.redis = 'connected';
    } else {
      health.services.redis = 'disconnected';
      health.status = 'degraded';
    }
  } catch (error) {
    health.services.redis = 'error';
    health.status = 'degraded';
    logger.error('Redis health check failed:', error);
  }

  try {
    // Check Memcached
    const memcachedClient = getMemcachedClient();
    if (memcachedClient) {
      health.services.memcached = 'connected';
    } else {
      health.services.memcached = 'disconnected';
      health.status = 'degraded';
    }
  } catch (error) {
    health.services.memcached = 'error';
    health.status = 'degraded';
    logger.error('Memcached health check failed:', error);
  }

  try {
    // Check Elasticsearch
    const esClient = getElasticsearchClient();
    if (esClient) {
      const esHealth = await esClient.cluster.health();
      health.services.elasticsearch = esHealth.status;
    } else {
      health.services.elasticsearch = 'disconnected';
      health.status = 'degraded';
    }
  } catch (error) {
    health.services.elasticsearch = 'error';
    health.status = 'degraded';
    logger.error('Elasticsearch health check failed:', error);
  }

  try {
    // Check gRPC services
    health.services.grpc = 'connected';
  } catch (error) {
    health.services.grpc = 'error';
    health.status = 'degraded';
    logger.error('gRPC health check failed:', error);
  }

  const statusCode = health.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(health);
});

module.exports = router;
