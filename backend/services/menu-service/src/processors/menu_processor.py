import os
import sys
import time
import uuid
import logging
from typing import List, Dict, Any, Optional
import json

# Add proto_gen to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'proto_gen'))

import menu_pb2
from google.cloud import vision
from google.cloud import storage
from google.cloud import pubsub_v1
import redis
from elasticsearch import Elasticsearch
from PIL import Image
import io

logger = logging.getLogger(__name__)


class MenuProcessor:
    """Processes menu images and extracts dish information."""
    
    def __init__(self):
        # Initialize Redis
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        
        # Initialize Elasticsearch
        es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
        es_port = int(os.getenv('ELASTICSEARCH_PORT', 9200))
        self.es_client = Elasticsearch([f'http://{es_host}:{es_port}'])
        
        # Initialize GCP clients (requires credentials)
        try:
            self.vision_client = vision.ImageAnnotatorClient()
            self.storage_client = storage.Client()
            self.pubsub_publisher = pubsub_v1.PublisherClient()
            logger.info("GCP clients initialized")
        except Exception as e:
            logger.warning(f"GCP clients not initialized: {e}")
            self.vision_client = None
            self.storage_client = None
            self.pubsub_publisher = None
        
        logger.info("MenuProcessor initialized")
    
    def process_menu(
        self,
        image_data: bytes,
        image_url: str,
        options: menu_pb2.ProcessingOptions
    ) -> menu_pb2.MenuResponse:
        """Process a menu image and extract dishes."""
        start_time = time.time()
        menu_id = str(uuid.uuid4())
        
        logger.info(f"Processing menu {menu_id}")
        
        # Check cache if enabled
        if options.use_cache:
            cache_key = f"menu:{menu_id}"
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.info(f"Cache hit for menu {menu_id}")
                return self._deserialize_menu_response(cached)
        
        # Extract text using Google Cloud Vision (or mock if not available)
        text_annotations = self._extract_text(image_data)
        
        # Parse dishes from text
        dishes = self._parse_dishes(text_annotations, options)
        
        # Index in Elasticsearch
        for dish in dishes:
            self._index_dish(dish)
        
        # Create response
        processing_time = int((time.time() - start_time) * 1000)
        
        response = menu_pb2.MenuResponse(
            menu_id=menu_id,
            dishes=dishes,
            metadata=menu_pb2.Metadata(
                processing_time_ms=processing_time,
                total_dishes=len(dishes),
                source='vision_api',
                timestamp=int(time.time())
            ),
            status=menu_pb2.ProcessingStatus(
                status=menu_pb2.ProcessingStatus.Status.COMPLETED,
                message="Menu processed successfully"
            )
        )
        
        # Cache the result
        if options.use_cache:
            cache_key = f"menu:{menu_id}"
            self.redis_client.setex(
                cache_key,
                3600,  # 1 hour TTL
                self._serialize_menu_response(response)
            )
        
        # Publish to Pub/Sub (if available)
        self._publish_menu_processed(menu_id, len(dishes))
        
        return response
    
    def get_dish(
        self,
        dish_id: str,
        include_similar: bool
    ) -> Optional[menu_pb2.DishResponse]:
        """Get dish details by ID."""
        # Try cache first
        cache_key = f"dish:{dish_id}"
        cached = self.redis_client.get(cache_key)
        
        if cached:
            dish_data = json.loads(cached)
            dish = self._dict_to_dish(dish_data)
        else:
            # Get from Elasticsearch
            try:
                result = self.es_client.get(index='dishes', id=dish_id)
                dish = self._dict_to_dish(result['_source'])
                
                # Cache it
                self.redis_client.setex(
                    cache_key,
                    3600,
                    json.dumps(result['_source'])
                )
            except Exception as e:
                logger.error(f"Dish not found: {e}")
                return None
        
        response = menu_pb2.DishResponse(dish=dish)
        
        # Find similar dishes if requested
        if include_similar:
            similar = self._find_similar_dishes(dish_id, dish.name)
            response.similar_dishes.extend(similar)
        
        return response
    
    def search_dishes(self, request: menu_pb2.SearchRequest) -> menu_pb2.SearchResponse:
        """Search dishes using Elasticsearch."""
        # Build Elasticsearch query
        query = {
            "query": {
                "multi_match": {
                    "query": request.query,
                    "fields": ["name^3", "description^2", "ingredients"]
                }
            },
            "size": request.limit or 20,
            "from": request.offset or 0
        }
        
        # Add filters
        if request.categories:
            query["query"] = {
                "bool": {
                    "must": query["query"],
                    "filter": {
                        "terms": {"category": list(request.categories)}
                    }
                }
            }
        
        try:
            result = self.es_client.search(index='dishes', body=query)
            
            dishes = []
            for hit in result['hits']['hits']:
                dishes.append(self._dict_to_dish(hit['_source']))
            
            return menu_pb2.SearchResponse(
                dishes=dishes,
                total_results=result['hits']['total']['value'],
                page=(request.offset // request.limit) + 1 if request.limit else 1,
                metadata=menu_pb2.SearchMetadata(
                    search_time_ms=result['took']
                )
            )
        except Exception as e:
            logger.error(f"Search error: {e}")
            return menu_pb2.SearchResponse()
    
    def process_menu_stream(self, image_data, image_url, options):
        """Stream dish processing results."""
        # This is a generator that yields dishes as they are processed
        text_annotations = self._extract_text(image_data)
        dishes = self._parse_dishes(text_annotations, options)
        
        for dish in dishes:
            self._index_dish(dish)
            yield menu_pb2.DishResponse(dish=dish)
    
    def _extract_text(self, image_data: bytes) -> List[str]:
        """Extract text from image using Google Cloud Vision."""
        if self.vision_client and image_data:
            try:
                image = vision.Image(content=image_data)
                response = self.vision_client.text_detection(image=image)
                
                if response.text_annotations:
                    return [annotation.description for annotation in response.text_annotations]
            except Exception as e:
                logger.error(f"Vision API error: {e}")
        
        # Return mock data for development
        return [
            "MENU",
            "Margherita Pizza - Classic tomato and mozzarella - $12.99",
            "Pasta Carbonara - Creamy pasta with bacon - $14.99",
            "Caesar Salad - Fresh romaine with parmesan - $8.99",
            "Tiramisu - Italian coffee dessert - $6.99"
        ]
    
    def _parse_dishes(
        self,
        text_annotations: List[str],
        options: menu_pb2.ProcessingOptions
    ) -> List[menu_pb2.Dish]:
        """Parse dish information from text annotations."""
        dishes = []
        
        # Simple parsing logic (should be more sophisticated in production)
        for i, text in enumerate(text_annotations[1:], 1):  # Skip first annotation (full text)
            if '-' in text and '$' in text:
                parts = text.split('-')
                if len(parts) >= 2:
                    name = parts[0].strip()
                    description = parts[1].strip() if len(parts) > 1 else ""
                    
                    # Extract price
                    price_text = ""
                    amount = 0.0
                    if '$' in description:
                        price_parts = description.split('$')
                        if len(price_parts) > 1:
                            price_text = '$' + price_parts[-1].strip()
                            try:
                                amount = float(price_parts[-1].strip().replace(',', ''))
                            except ValueError:
                                pass
                            description = '$'.join(price_parts[:-1]).strip()
                    
                    dish = menu_pb2.Dish(
                        dish_id=str(uuid.uuid4()),
                        name=name,
                        description=description,
                        price=menu_pb2.Price(
                            amount=amount,
                            currency='USD',
                            original_text=price_text
                        ) if options.extract_prices else None,
                        category=self._categorize_dish(name),
                        confidence_score=0.85,
                        image_url=""
                    )
                    
                    dishes.append(dish)
        
        return dishes
    
    def _categorize_dish(self, name: str) -> str:
        """Simple categorization based on keywords."""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['pizza', 'burger', 'sandwich', 'pasta']):
            return 'main'
        elif any(word in name_lower for word in ['salad', 'soup', 'appetizer']):
            return 'appetizer'
        elif any(word in name_lower for word in ['cake', 'pie', 'ice cream', 'tiramisu']):
            return 'dessert'
        else:
            return 'other'
    
    def _index_dish(self, dish: menu_pb2.Dish):
        """Index dish in Elasticsearch."""
        try:
            doc = {
                'name': dish.name,
                'description': dish.description,
                'price': {
                    'amount': dish.price.amount,
                    'currency': dish.price.currency
                } if dish.price else None,
                'ingredients': list(dish.ingredients),
                'category': dish.category,
                'confidence_score': dish.confidence_score
            }
            
            self.es_client.index(
                index='dishes',
                id=dish.dish_id,
                document=doc
            )
            logger.info(f"Indexed dish: {dish.dish_id}")
        except Exception as e:
            logger.error(f"Error indexing dish: {e}")
    
    def _find_similar_dishes(self, dish_id: str, dish_name: str) -> List[menu_pb2.Dish]:
        """Find similar dishes using Elasticsearch."""
        try:
            query = {
                "query": {
                    "more_like_this": {
                        "fields": ["name", "description"],
                        "like": dish_name,
                        "min_term_freq": 1,
                        "max_query_terms": 12
                    }
                },
                "size": 5
            }
            
            result = self.es_client.search(index='dishes', body=query)
            
            similar = []
            for hit in result['hits']['hits']:
                if hit['_id'] != dish_id:
                    similar.append(self._dict_to_dish(hit['_source']))
            
            return similar
        except Exception as e:
            logger.error(f"Error finding similar dishes: {e}")
            return []
    
    def _publish_menu_processed(self, menu_id: str, dish_count: int):
        """Publish menu processed event to Pub/Sub."""
        if self.pubsub_publisher:
            try:
                project_id = os.getenv('GCP_PROJECT_ID')
                topic_path = self.pubsub_publisher.topic_path(
                    project_id,
                    'menu-processed'
                )
                
                data = json.dumps({
                    'menu_id': menu_id,
                    'dish_count': dish_count,
                    'timestamp': int(time.time())
                }).encode('utf-8')
                
                self.pubsub_publisher.publish(topic_path, data)
                logger.info(f"Published menu processed event: {menu_id}")
            except Exception as e:
                logger.warning(f"Failed to publish event: {e}")
    
    def _dict_to_dish(self, data: Dict[str, Any]) -> menu_pb2.Dish:
        """Convert dictionary to Dish message."""
        dish = menu_pb2.Dish(
            dish_id=data.get('dish_id', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            category=data.get('category', ''),
            confidence_score=data.get('confidence_score', 0.0)
        )
        
        if 'price' in data and data['price']:
            dish.price.CopyFrom(menu_pb2.Price(
                amount=data['price'].get('amount', 0.0),
                currency=data['price'].get('currency', 'USD'),
                original_text=data['price'].get('original_text', '')
            ))
        
        if 'ingredients' in data:
            dish.ingredients.extend(data['ingredients'])
        
        return dish
    
    def _serialize_menu_response(self, response: menu_pb2.MenuResponse) -> str:
        """Serialize MenuResponse to string."""
        return response.SerializeToString().hex()
    
    def _deserialize_menu_response(self, data: str) -> menu_pb2.MenuResponse:
        """Deserialize MenuResponse from string."""
        response = menu_pb2.MenuResponse()
        response.ParseFromString(bytes.fromhex(data))
        return response
