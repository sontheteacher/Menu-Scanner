# API Examples

Complete examples for using the Menu Scanner API.

## Authentication (Future)

Currently, the API is open for development. In production, use API keys:

```bash
curl -H "X-API-Key: your-api-key" http://api.example.com/api/v1/menu/upload
```

## Upload Menu Image

### Basic Upload

```bash
curl -X POST http://localhost:8080/api/v1/menu/upload \
  -F "image=@menu.jpg" \
  | jq .
```

### Upload with Options

```bash
curl -X POST http://localhost:8080/api/v1/menu/upload \
  -F "image=@menu.jpg" \
  -F 'options={
    "extract_prices": true,
    "extract_descriptions": true,
    "extract_ingredients": true,
    "language": "en",
    "use_cache": true
  }' \
  | jq .
```

### Response

```json
{
  "menu_id": "550e8400-e29b-41d4-a716-446655440000",
  "dishes": [
    {
      "dish_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "name": "Margherita Pizza",
      "description": "Classic tomato and mozzarella",
      "price": {
        "amount": 12.99,
        "currency": "USD",
        "original_text": "$12.99"
      },
      "ingredients": [],
      "category": "main",
      "thumbnail": "",
      "image_url": "",
      "confidence_score": 0.85
    }
  ],
  "metadata": {
    "processing_time_ms": 1234,
    "restaurant_name": "",
    "cuisine_type": "",
    "total_dishes": 4,
    "source": "vision_api",
    "timestamp": 1640000000
  },
  "status": {
    "status": "COMPLETED",
    "message": "Menu processed successfully",
    "errors": []
  }
}
```

## Get Menu by ID

```bash
curl http://localhost:8080/api/v1/menu/550e8400-e29b-41d4-a716-446655440000 \
  | jq .
```

## Search Dishes

### Basic Search

```bash
curl "http://localhost:8080/api/v1/dishes/search?q=pasta" \
  | jq .
```

### Advanced Search

```bash
curl -G "http://localhost:8080/api/v1/dishes/search" \
  --data-urlencode "q=pasta" \
  --data-urlencode "category=main" \
  --data-urlencode "category=appetizer" \
  --data-urlencode "min_price=10" \
  --data-urlencode "max_price=20" \
  --data-urlencode "limit=20" \
  --data-urlencode "offset=0" \
  | jq .
```

### Response

```json
{
  "dishes": [
    {
      "dish_id": "abc123",
      "name": "Pasta Carbonara",
      "description": "Creamy pasta with bacon",
      "price": {
        "amount": 14.99,
        "currency": "USD"
      },
      "category": "main",
      "_score": 2.5
    }
  ],
  "total_results": 15,
  "page": 1,
  "metadata": {
    "search_time_ms": 45,
    "suggested_queries": [],
    "category_counts": {
      "main": 10,
      "appetizer": 5
    }
  }
}
```

## Get Dish Details

### Basic Dish Info

```bash
curl http://localhost:8080/api/v1/dishes/abc123 \
  | jq .
```

### With Similar Dishes

```bash
curl "http://localhost:8080/api/v1/dishes/abc123?include_similar=true" \
  | jq .
```

### Response

```json
{
  "dish": {
    "dish_id": "abc123",
    "name": "Pasta Carbonara",
    "description": "Creamy pasta with bacon",
    "price": {
      "amount": 14.99,
      "currency": "USD"
    },
    "ingredients": ["pasta", "bacon", "eggs", "parmesan"],
    "category": "main"
  },
  "similar_dishes": [
    {
      "dish_id": "def456",
      "name": "Pasta Alfredo",
      "description": "Creamy white sauce pasta"
    }
  ]
}
```

## Health Check

```bash
curl http://localhost:8080/api/v1/health | jq .
```

### Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "services": {
    "redis": "connected",
    "memcached": "connected",
    "elasticsearch": "green",
    "grpc": "connected"
  }
}
```

## Using JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function uploadMenu(imagePath) {
  const form = new FormData();
  form.append('image', fs.createReadStream(imagePath));
  form.append('options', JSON.stringify({
    extract_prices: true,
    extract_descriptions: true,
    language: 'en'
  }));

  const response = await axios.post(
    'http://localhost:8080/api/v1/menu/upload',
    form,
    { headers: form.getHeaders() }
  );

  return response.data;
}

async function searchDishes(query) {
  const response = await axios.get(
    'http://localhost:8080/api/v1/dishes/search',
    { params: { q: query } }
  );

  return response.data;
}

// Usage
uploadMenu('./menu.jpg')
  .then(result => console.log('Menu processed:', result))
  .catch(err => console.error('Error:', err));

searchDishes('pizza')
  .then(results => console.log('Found dishes:', results))
  .catch(err => console.error('Error:', err));
```

## Using Python

```python
import requests

def upload_menu(image_path):
    """Upload a menu image for processing."""
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {
            'options': '{"extract_prices": true, "extract_descriptions": true}'
        }
        response = requests.post(
            'http://localhost:8080/api/v1/menu/upload',
            files=files,
            data=data
        )
    return response.json()

def search_dishes(query, category=None, min_price=None, max_price=None):
    """Search for dishes."""
    params = {'q': query}
    if category:
        params['category'] = category
    if min_price:
        params['min_price'] = min_price
    if max_price:
        params['max_price'] = max_price
    
    response = requests.get(
        'http://localhost:8080/api/v1/dishes/search',
        params=params
    )
    return response.json()

def get_dish(dish_id, include_similar=False):
    """Get dish details."""
    params = {'include_similar': include_similar}
    response = requests.get(
        f'http://localhost:8080/api/v1/dishes/{dish_id}',
        params=params
    )
    return response.json()

# Usage
if __name__ == '__main__':
    # Upload menu
    result = upload_menu('menu.jpg')
    print(f"Processed menu: {result['menu_id']}")
    print(f"Found {len(result['dishes'])} dishes")
    
    # Search dishes
    results = search_dishes('pasta', category='main')
    print(f"Found {results['total_results']} pasta dishes")
    
    # Get dish details
    if results['dishes']:
        dish = get_dish(results['dishes'][0]['dish_id'], include_similar=True)
        print(f"Dish: {dish['dish']['name']}")
```

## Using cURL Scripts

Save as `test-api.sh`:

```bash
#!/bin/bash

API_URL="http://localhost:8080/api/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test health
echo -e "${GREEN}Testing health endpoint...${NC}"
curl -s "$API_URL/health" | jq .

# Upload menu
echo -e "\n${GREEN}Uploading menu...${NC}"
MENU_RESPONSE=$(curl -s -X POST "$API_URL/menu/upload" \
  -F "image=@menu.jpg" \
  -F 'options={"extract_prices": true}')

echo "$MENU_RESPONSE" | jq .

MENU_ID=$(echo "$MENU_RESPONSE" | jq -r '.menu_id')
echo -e "\n${GREEN}Menu ID: $MENU_ID${NC}"

# Search dishes
echo -e "\n${GREEN}Searching for pasta dishes...${NC}"
curl -s "$API_URL/dishes/search?q=pasta" | jq .

# Get specific dish
if [ ! -z "$MENU_RESPONSE" ]; then
  DISH_ID=$(echo "$MENU_RESPONSE" | jq -r '.dishes[0].dish_id')
  if [ "$DISH_ID" != "null" ]; then
    echo -e "\n${GREEN}Getting dish details...${NC}"
    curl -s "$API_URL/dishes/$DISH_ID?include_similar=true" | jq .
  fi
fi
```

## Rate Limiting

The API enforces rate limits:
- 100 requests per 15 minutes per IP

When rate limited, you'll receive:

```json
{
  "error": "Too many requests from this IP, please try again later.",
  "code": "RATE_LIMIT_EXCEEDED"
}
```

## Error Handling

### Common Error Responses

**400 Bad Request**
```json
{
  "error": "No image file provided",
  "code": "MISSING_IMAGE"
}
```

**404 Not Found**
```json
{
  "error": "Menu not found",
  "code": "NOT_FOUND"
}
```

**500 Internal Server Error**
```json
{
  "error": "Failed to process menu image",
  "code": "PROCESSING_ERROR",
  "details": "..."
}
```

## WebSocket Support (Future)

Real-time updates for menu processing:

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/menu/process');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Processing update:', update);
};

ws.send(JSON.stringify({
  action: 'upload',
  image: base64Image
}));
```

## Best Practices

1. **Always check health** before making requests
2. **Use caching** by setting `use_cache: true` in options
3. **Handle rate limits** with exponential backoff
4. **Validate images** client-side before uploading
5. **Use appropriate image sizes** (max 10MB)
6. **Include error handling** for all API calls
7. **Cache dish IDs** to avoid repeated searches
8. **Use pagination** for large search results

## Production URLs

When deploying to production with Cloudflare:

```bash
# Replace localhost with your domain
API_URL="https://api.menuscanner.example.com/api/v1"
```

All endpoints remain the same, just update the base URL.
