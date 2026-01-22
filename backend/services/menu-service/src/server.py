import os
import sys
import logging
from concurrent import futures
import grpc

# Add proto_gen to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto_gen'))

import menu_pb2
import menu_pb2_grpc
from processors.menu_processor import MenuProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MenuServiceServicer(menu_pb2_grpc.MenuServiceServicer):
    """Implements the MenuService gRPC service."""
    
    def __init__(self):
        self.processor = MenuProcessor()
        logger.info("MenuService initialized")
    
    def ProcessMenuImage(self, request, context):
        """Process a menu image and extract dishes."""
        try:
            logger.info(f"Processing menu image, format: {request.format}")
            
            # Process the image
            result = self.processor.process_menu(
                image_data=request.image_data,
                image_url=request.image_url,
                options=request.options
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing menu image: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return menu_pb2.MenuResponse()
    
    def GetDish(self, request, context):
        """Get dish details by ID."""
        try:
            logger.info(f"Getting dish: {request.dish_id}")
            
            result = self.processor.get_dish(
                dish_id=request.dish_id,
                include_similar=request.include_similar
            )
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Dish {request.dish_id} not found")
                return menu_pb2.DishResponse()
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting dish: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return menu_pb2.DishResponse()
    
    def SearchDishes(self, request, context):
        """Search dishes."""
        try:
            logger.info(f"Searching dishes: {request.query}")
            
            result = self.processor.search_dishes(request)
            return result
            
        except Exception as e:
            logger.error(f"Error searching dishes: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return menu_pb2.SearchResponse()
    
    def StreamDishProcessing(self, request, context):
        """Stream dish processing results."""
        try:
            logger.info("Starting streaming dish processing")
            
            for dish in self.processor.process_menu_stream(
                image_data=request.image_data,
                image_url=request.image_url,
                options=request.options
            ):
                yield dish
                
        except Exception as e:
            logger.error(f"Error in streaming processing: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))


def serve():
    """Start the gRPC server."""
    port = os.getenv('GRPC_PORT', '50051')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    menu_pb2_grpc.add_MenuServiceServicer_to_server(
        MenuServiceServicer(), server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    logger.info(f"Menu Service started on port {port}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.stop(0)


if __name__ == '__main__':
    serve()
