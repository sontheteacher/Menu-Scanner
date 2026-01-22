const redis = require('redis');
const Memcached = require('memcached');
const { Client } = require('@elastic/elasticsearch');
const logger = require('./logger');

let redisClient;
let memcachedClient;
let elasticsearchClient;

async function initializeRedis() {
  const redisHost = process.env.REDIS_HOST || 'localhost';
  const redisPort = process.env.REDIS_PORT || 6379;
  
  redisClient = redis.createClient({
    socket: {
      host: redisHost,
      port: redisPort
    }
  });

  redisClient.on('error', (err) => {
    logger.error('Redis error:', err);
  });

  redisClient.on('connect', () => {
    logger.info('Connected to Redis');
  });

  await redisClient.connect();
  return redisClient;
}

function initializeMemcached() {
  const memcachedHost = process.env.MEMCACHED_HOST || 'localhost';
  const memcachedPort = process.env.MEMCACHED_PORT || 11211;
  
  memcachedClient = new Memcached(`${memcachedHost}:${memcachedPort}`);
  
  logger.info('Memcached client initialized');
  return memcachedClient;
}

async function initializeElasticsearch() {
  const esHost = process.env.ELASTICSEARCH_HOST || 'localhost';
  const esPort = process.env.ELASTICSEARCH_PORT || 9200;
  
  elasticsearchClient = new Client({
    node: `http://${esHost}:${esPort}`
  });

  try {
    const health = await elasticsearchClient.cluster.health();
    logger.info('Connected to Elasticsearch:', health.cluster_name);
  } catch (error) {
    logger.error('Elasticsearch connection error:', error.message);
  }

  return elasticsearchClient;
}

function getRedisClient() {
  return redisClient;
}

function getMemcachedClient() {
  return memcachedClient;
}

function getElasticsearchClient() {
  return elasticsearchClient;
}

module.exports = {
  initializeRedis,
  initializeMemcached,
  initializeElasticsearch,
  getRedisClient,
  getMemcachedClient,
  getElasticsearchClient
};
