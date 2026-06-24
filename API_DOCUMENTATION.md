# SafeRoute AI - API Documentation

Complete API reference for SafeRoute AI backend services.

## Base URL

```
Development: http://localhost:8000
Production: https://api.saferoute.ai
```

## Authentication

Currently, the API does not require authentication for demo purposes. In production, JWT-based authentication will be implemented.

## API Endpoints

### Health Check

#### GET /health

Check the health status of the API and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "service": "saferoute-ai-api",
  "timestamp": 1234567890.123,
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    }
  }
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service is degraded or unhealthy

---

### Route Calculation

#### POST /api/v1/calculate

Calculate the safest and fastest routes between source and destination coordinates.

**Request Body:**
```json
{
  "source": {
    "latitude": 28.6315,
    "longitude": 77.2167
  },
  "destination": {
    "latitude": 28.6350,
    "longitude": 77.2200
  },
  "safety_weight": 0.7
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source.latitude` | float | Yes | Source latitude (-90 to 90) |
| `source.longitude` | float | Yes | Source longitude (-180 to 180) |
| `destination.latitude` | float | Yes | Destination latitude (-90 to 90) |
| `destination.longitude` | float | Yes | Destination longitude (-180 to 180) |
| `safety_weight` | float | No | Safety vs distance weight (0.0-1.0, default: 0.7) |

**Response:**
```json
{
  "success": true,
  "data": {
    "safest_route": [
      {"latitude": 28.6315, "longitude": 77.2167},
      {"latitude": 28.6320, "longitude": 77.2170},
      {"latitude": 28.6350, "longitude": 77.2200}
    ],
    "fastest_route": [
      {"latitude": 28.6315, "longitude": 77.2167},
      {"latitude": 28.6330, "longitude": 77.2185},
      {"latitude": 28.6350, "longitude": 77.2200}
    ],
    "safest_distance": 450.5,
    "fastest_distance": 380.2,
    "safest_safety_score": 0.87,
    "fastest_safety_score": 0.42,
    "route_segments": [
      {
        "from_coord": {"latitude": 28.6315, "longitude": 77.2167},
        "to_coord": {"latitude": 28.6320, "longitude": 77.2170},
        "distance": 50.5,
        "safety_score": 0.85,
        "penalty": 10.0
      }
    ]
  },
  "message": "Route calculation completed successfully"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `safest_route` | array | Array of coordinate objects for the safest route |
| `fastest_route` | array | Array of coordinate objects for the fastest route |
| `safest_distance` | float | Total distance of safest route in meters |
| `fastest_distance` | float | Total distance of fastest route in meters |
| `safest_safety_score` | float | Average safety score of safest route (0.0-1.0) |
| `fastest_safety_score` | float | Average safety score of fastest route (0.0-1.0) |
| `route_segments` | array | Detailed segment information (optional) |

**Status Codes:**
- `200 OK`: Route calculated successfully
- `400 Bad Request`: Invalid input data
- `500 Internal Server Error`: Route calculation failed

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid input data",
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid input data"
}
```

---

### AI Safety Score

#### GET /api/v1/ai/safety-score

Get AI-predicted safety score for a specific location and time.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `latitude` | float | Yes | Latitude coordinate (-90 to 90) |
| `longitude` | float | Yes | Longitude coordinate (-180 to 180) |
| `timestamp` | string | No | ISO format timestamp (defaults to now) |
| `radius` | integer | No | Radius in meters (100-50000, default: 1000) |

**Example Request:**
```
GET /api/v1/ai/safety-score?latitude=28.6315&longitude=77.2167&radius=1000
```

**Response:**
```json
{
  "success": true,
  "data": {
    "latitude": 28.6315,
    "longitude": 77.2167,
    "timestamp": "2024-06-24T10:30:00",
    "safety_score": 0.87,
    "radius_meters": 1000,
    "method": "ai_prediction"
  },
  "message": "Safety score retrieved successfully"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `latitude` | float | Requested latitude |
| `longitude` | float | Requested longitude |
| `timestamp` | string | Timestamp of prediction |
| `safety_score` | float | Safety score (0.0 = unsafe, 1.0 = safe) |
| `radius_meters` | integer | Radius used for feature calculation |
| `method` | string | Method used for prediction |

**Status Codes:**
- `200 OK`: Safety score calculated successfully
- `400 Bad Request`: Invalid timestamp format or parameters
- `500 Internal Server Error`: Safety score calculation failed

**Error Response:**
```json
{
  "detail": "Failed to calculate safety score: error message"
}
```

---

### SOS Emergency Alert

#### POST /api/v1/sos/trigger

Trigger an emergency SOS alert with user's location and safety context.

**Request Body:**
```json
{
  "latitude": 28.6315,
  "longitude": 77.2167,
  "timestamp": "2024-06-24T10:30:00Z"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `latitude` | float | Yes | User's current latitude |
| `longitude` | float | Yes | User's current longitude |
| `timestamp` | string | Yes | ISO format timestamp |

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "success",
    "message": "Emergency SOS alert sent successfully",
    "timestamp": "2024-06-24T10:30:00Z",
    "location": {
      "latitude": 28.6315,
      "longitude": 77.2167
    },
    "dispatch_details": {
      "police_patrol": "Vehicle #04 redirected to location",
      "guardians_notified": "+91 XXXXXXX890",
      "emergency_contacts": ["100", "1091", "112"]
    },
    "alerts_sent": [
      "SMS to emergency contact",
      "Email to emergency services",
      "Police Control Room",
      "Women's Helpline",
      "Emergency Services",
      "Guardians notified"
    ]
  },
  "message": "Emergency SOS alert sent successfully"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Alert status |
| `timestamp` | string | Alert timestamp |
| `location` | object | User's location coordinates |
| `dispatch_details` | object | Emergency response dispatch information |
| `alerts_sent` | array | List of services notified |

**Status Codes:**
- `200 OK`: SOS alert sent successfully
- `400 Bad Request`: Invalid input data
- `500 Internal Server Error`: SOS processing failed

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid input data for SOS request",
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid input data for SOS request"
}
```

---

### Routing Service Health

#### GET /api/v1/routing/health

Health check for the routing service.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy"
  },
  "message": "Routing service is operational"
}
```

---

## Data Models

### Coordinate
```json
{
  "latitude": 28.6315,
  "longitude": 77.2167
}
```

### Route Segment
```json
{
  "from_coord": {
    "latitude": 28.6315,
    "longitude": 77.2167
  },
  "to_coord": {
    "latitude": 28.6320,
    "longitude": 77.2170
  },
  "distance": 50.5,
  "safety_score": 0.85,
  "penalty": 10.0
}
```

## Error Handling

All API endpoints follow a consistent error response format:

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "message": "User-friendly message"
}
```

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Invalid input data or parameters |
| `INTERNAL_ERROR` | Internal server error |
| `DATABASE_ERROR` | Database operation failed |
| `AI_MODEL_ERROR` | AI model prediction failed |

## Rate Limiting

Currently, rate limiting is not implemented for demo purposes. In production, the following rate limits will be applied:

- Route calculation: 60 requests per minute
- AI safety score: 100 requests per minute
- SOS alerts: 10 requests per minute

## Interactive API Documentation

When the backend is running, interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to test API endpoints directly from your browser.

## Example Usage

### Using cURL

#### Calculate Route
```bash
curl -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "source": {"latitude": 28.6315, "longitude": 77.2167},
    "destination": {"latitude": 28.6350, "longitude": 77.2200},
    "safety_weight": 0.7
  }'
```

#### Get Safety Score
```bash
curl "http://localhost:8000/api/v1/ai/safety-score?latitude=28.6315&longitude=77.2167&radius=1000"
```

#### Trigger SOS
```bash
curl -X POST http://localhost:8000/api/v1/sos/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 28.6315,
    "longitude": 77.2167,
    "timestamp": "2024-06-24T10:30:00Z"
  }'
```

### Using JavaScript/Fetch

```javascript
// Calculate Route
const response = await fetch('http://localhost:8000/api/v1/calculate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    source: { latitude: 28.6315, longitude: 77.2167 },
    destination: { latitude: 28.6350, longitude: 77.2200 },
    safety_weight: 0.7
  })
});

const data = await response.json();
console.log(data);
```

### Using Python/Requests

```python
import requests

# Calculate Route
response = requests.post(
    'http://localhost:8000/api/v1/calculate',
    json={
        'source': {'latitude': 28.6315, 'longitude': 77.2167},
        'destination': {'latitude': 28.6350, 'longitude': 77.2200},
        'safety_weight': 0.7
    }
)

data = response.json()
print(data)
```

## Versioning

The API uses semantic versioning. Current version: `v1`

Future versions will maintain backward compatibility where possible. Breaking changes will be indicated by a major version increment.

## Support

For API-related issues:
- Check the interactive documentation at `/docs`
- Review the troubleshooting section in README
- Open an issue on GitHub

---

**Note**: This API documentation is for the current demo version. Production deployment will include additional security features, authentication, and enhanced rate limiting.
