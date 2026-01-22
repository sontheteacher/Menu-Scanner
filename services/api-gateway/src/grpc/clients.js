const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');
const logger = require('../config/logger');

let menuServiceClient;
let imageServiceClient;

async function initializeGrpcClients() {
  // Load proto files
  const PROTO_PATH = path.join(__dirname, '../../../proto');
  
  const menuProtoPath = path.join(PROTO_PATH, 'menu.proto');
  const imageProtoPath = path.join(PROTO_PATH, 'image.proto');

  const packageDefinition1 = protoLoader.loadSync(menuProtoPath, {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
  });

  const packageDefinition2 = protoLoader.loadSync(imageProtoPath, {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
  });

  const menuProto = grpc.loadPackageDefinition(packageDefinition1).menu;
  const imageProto = grpc.loadPackageDefinition(packageDefinition2).image;

  // Initialize Menu Service client
  const menuServiceHost = process.env.GRPC_MENU_SERVICE_HOST || 'localhost';
  const menuServicePort = process.env.GRPC_MENU_SERVICE_PORT || 50051;
  
  menuServiceClient = new menuProto.MenuService(
    `${menuServiceHost}:${menuServicePort}`,
    grpc.credentials.createInsecure()
  );

  logger.info(`Menu Service gRPC client initialized at ${menuServiceHost}:${menuServicePort}`);

  // Initialize Image Service client
  const imageServiceHost = process.env.GRPC_IMAGE_SERVICE_HOST || 'localhost';
  const imageServicePort = process.env.GRPC_IMAGE_SERVICE_PORT || 50052;
  
  imageServiceClient = new imageProto.ImageService(
    `${imageServiceHost}:${imageServicePort}`,
    grpc.credentials.createInsecure()
  );

  logger.info(`Image Service gRPC client initialized at ${imageServiceHost}:${imageServicePort}`);
}

function getMenuServiceClient() {
  return menuServiceClient;
}

function getImageServiceClient() {
  return imageServiceClient;
}

module.exports = {
  initializeGrpcClients,
  getMenuServiceClient,
  getImageServiceClient
};
