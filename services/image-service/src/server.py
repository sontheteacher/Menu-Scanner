import os
import sys
import logging
from concurrent import futures
import grpc

# Add proto_gen to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto_gen'))

import image_pb2
import image_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageServiceServicer(image_pb2_grpc.ImageServiceServicer):
    """Implements the ImageService gRPC service."""
    
    def __init__(self):
        logger.info("ImageService initialized")
    
    def AnalyzeImage(self, request, context):
        """Analyze an image."""
        try:
            logger.info("Analyzing image")
            
            # Placeholder implementation
            response = image_pb2.ImageAnalysisResponse(
                image_id="img_" + os.urandom(8).hex(),
                metadata=image_pb2.ImageMetadata(
                    width=800,
                    height=600,
                    format="jpeg",
                    size_bytes=len(request.image_data) if request.image_data else 0,
                    processing_time_ms=100
                )
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return image_pb2.ImageAnalysisResponse()
    
    def ExtractText(self, request, context):
        """Extract text from image."""
        try:
            logger.info("Extracting text from image")
            
            # Placeholder implementation
            response = image_pb2.TextExtractionResponse(
                full_text="Sample extracted text",
                metadata=image_pb2.ImageMetadata(
                    processing_time_ms=150
                )
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return image_pb2.TextExtractionResponse()
    
    def DetectObjects(self, request, context):
        """Detect objects in image."""
        try:
            logger.info("Detecting objects in image")
            
            # Placeholder implementation
            response = image_pb2.ObjectDetectionResponse(
                total_objects=0,
                metadata=image_pb2.ImageMetadata(
                    processing_time_ms=200
                )
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error detecting objects: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return image_pb2.ObjectDetectionResponse()
    
    def StreamImageUpload(self, request_iterator, context):
        """Handle streaming image upload."""
        try:
            logger.info("Starting streaming image upload")
            
            chunks = []
            upload_id = None
            
            for chunk in request_iterator:
                upload_id = chunk.upload_id
                chunks.append(chunk.chunk)
                logger.info(f"Received chunk {chunk.chunk_number}")
            
            # Combine chunks
            full_data = b''.join(chunks)
            
            response = image_pb2.UploadResponse(
                image_id="img_" + os.urandom(8).hex(),
                storage_url=f"gs://menu-scanner-images/{upload_id}",
                success=True,
                message=f"Uploaded {len(full_data)} bytes successfully"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in streaming upload: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return image_pb2.UploadResponse(success=False, message=str(e))


def serve():
    """Start the gRPC server."""
    port = os.getenv('GRPC_PORT', '50052')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    image_pb2_grpc.add_ImageServiceServicer_to_server(
        ImageServiceServicer(), server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    logger.info(f"Image Service started on port {port}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.stop(0)


if __name__ == '__main__':
    serve()
