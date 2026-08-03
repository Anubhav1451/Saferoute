# Good vs Bad API Design Examples

## Bad Example: Poorly Designed REST API

### Problems with This API
- Inconsistent naming conventions
- Mixing REST and RPC styles
- Poor error handling
- Lack of versioning
- Inconsistent response formats
- Missing documentation
- Security anti-patterns
- Inefficient querying
- No pagination or filtering
- Inappropriate HTTP methods
- Overloading of related resources

### Bad API Examples

#### Inconsistent Naming and Structure
```http
# Inconsistent resource naming
GET /getAllUsers          # Should be GET /users
GET /getUser/123         # Should be GET /users/123
POST /createUser         # Should be POST /users
PUT /updateUser/123      # Should be PUT /users/123
DELETE /deleteUser/123   # Should be DELETE /users/123

# Mixed naming conventions
GET /get-orders          # kebab-case
GET /get_orders          # snake_case
GET /getOrders           # camelCase

# RPC-style endpoints instead of resource-based
POST /calculateTotal     # Should be POST /orders/calculate
POST/sendEmail           # Should be POST /notifications/email
```

#### Poor Error Handling
```http
# Inconsistent error responses
GET /users/999
# Returns 200 OK with error in body when user not found
{
  "error": "User not found",
  "code": "USER_NOT_FOUND"
}

POST /orders
# Returns 500 Internal Server Error for validation errors
{
  "message": "Validation failed"
}

# No correlation IDs for tracing
# No helpful error messages
```

#### Missing or Inconsistent Versioning
```http
# No versioning at all
GET /users

# Inconsistent versioning approaches
GET /v1/users
GET /users/v2               # Different version placement
GET /users?version=3        # Query param versioning
```

#### Inconsistent Response Formats
```http
# Sometimes returns array directly
GET /users
[
  {"id": 1, "name": "John"},
  {"id": 2, "name": "Jane"}
]

# Sometimes wraps in object
GET /orders
{
  "data": [
    {"id": 101, "total": 100.00},
    {"id": 102, "total": 250.50}
  ]
}

# Sometimes wraps with metadata inconsistently
GET /products
{
  "items": [...],
  "count": 25,
  "page": 1
}
```

#### Security Anti-Patterns
```http
# Sensitive data in URLs (logged everywhere)
GET /users/123/password/secret123

# No authentication on sensitive endpoints
DELETE /users/456

# No rate limiting
POST /login  # Can be hammered without limits

# Sensitive data in query parameters
GET /search?ssn=123-45-6789&creditcard=4111-1111-1111-1111

# No HTTPS enforcement
# No security headers
```

#### Inefficient Data Fetching
```http
# N+1 query problem - no way to include related data
GET /orders/123
{
  "id": 123,
  "customerId": 456,
  "items": [
    {"productId": 789, "quantity": 2},
    {"productId": 101, "quantity": 1}
  ]
}
# Then need separate calls for each:
GET /customers/456   # For customer details
GET /products/789    # For each product
GET /products/101    # For each product

# No filtering, sorting, or pagination
GET /products  # Returns ALL products - could be millions!
GET /orders    # Returns ALL orders - no way to paginate
```

#### Inappropriate HTTP Methods
```http
# Using GET for state-changing operations
GET /users/123/delete    # Should be DELETE
GET /orders/456/cancel   # Should be DELETE or PUT

# Using POST for everything
POST /users/123          # Should be PUT or PATCH for updates
POST /orders/456/ship    # Should be PUT or PATCH

# Misusing HTTP methods
DELETE /search?q=old     # Should use POST with body for complex queries
```

### Good Example: Well-Designed REST API

#### Characteristics
- Consistent, resource-oriented URLs
- Proper use of HTTP methods
- Consistent error handling with problem details
- Semantic versioning
- Consistent response formats
- Comprehensive documentation
- Security best practices
- Efficient querying capabilities
- Proper HTTP status codes
- HATEOAS links for discoverability
- Rate limiting and throttling
- Caching headers
- Content negotiation

#### Good API Examples

##### Consistent Resource-Oriented Design
```http
# Proper resource naming
GET     /users              # List users
POST    /users              # Create user
GET     /users/{id}         # Get specific user
PUT     /users/{id}         # Update user (replace)
PATCH   /users/{id}         # Partially update user
DELETE  /users/{id}         # Delete user

GET     /users/{userId}/orders          # Get user's orders
POST    /users/{userId}/orders          # Create order for user
GET     /orders/{orderId}               # Get specific order
PUT     /orders/{orderId}               # Update order
DELETE  /orders/{orderId}               # Delete order

GET     /products               # List products
POST    /products               # Create product
GET     /products/{id}          # Get specific product
PUT     /products/{id}          # Update product
DELETE  /products/{id}          # Delete product
```

##### Consistent Versioning
```http
# Version in URL path - clear and explicit
GET     /api/v1/users
POST    /api/v1/users
GET     /api/v1/users/{id}

# Alternative: Version in header (also acceptable)
GET     /users
Accept: application/vnd.myapi.v2+json
```

##### Proper Error Handling (RFC 7807 Problem Details)
```http
# Validation error
HTTP/1.1 400 Bad Request
Content-Type: application/problem+json
Content-Length: 287

{
  "type": "https://example.com/probs/out-of-credit",
  "title": "You do not have enough credit.",
  "detail": "Your current balance is 30, but that costs 50.",
  "instance": "/account/12345/msgs/abc",
  "balance": 30,
  "accounts": ["/account/12345", "/account/67890"],
  "errors": [
    {
      "field": "amount",
      "message": "must be greater than zero"
    },
    {
      "field": "currency",
      "message": "must be a valid currency code"
    }
  ]
}

# Resource not found
HTTP/1.1 404 Not Found
Content-Type: application/problem+json
Content-Length: 162

{
  "type": "https://example.com/probs/not-found",
  "title": "Resource not found",
  "detail": "The requested user could not be found.",
  "instance": "/users/999"
}

# Internal error with correlation ID
HTTP/1.1 500 Internal Server Error
Content-Type: application/problem+json
Content-Length: 201

{
  "type": "https://example.com/probs/internal-error",
  "title": "Internal server error",
  "detail": "An unexpected error occurred while processing your request.",
  "instance": "/orders",
  "traceId": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8"
}
```

##### Consistent Response Formats
```http
# Successful responses with metadata
GET /api/v1/users
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: max-age=60
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999

{
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "createdAt": "2023-01-15T10:30:00Z",
      "updatedAt": "2023-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "createdAt": "2023-01-16T14:22:00Z",
      "updatedAt": "2023-01-16T14:22:00Z"
    }
  ],
  "meta": {
    "count": 2,
    "limit": 100,
    "offset": 0,
    "total": 2
  },
  "links": {
    "self": "https://api.example.com/api/v1/users?limit=100&offset=0",
    "next": null,
    "prev": null
  }
}

# Single resource response
GET /api/v1/users/1
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "a1b2c3d4e5f6"

{
  "data": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "createdAt": "2023-01-15T10:30:00Z",
    "updatedAt": "2023-01-15T10:30:00Z"
  },
  "meta": {
    "version": 1
  },
  "links": {
    "self": "https://api.example.com/api/v1/users/1",
    "collection": "https://api.example.com/api/v1/users",
    "orders": "https://api.example.com/api/v1/users/1/orders"
  }
}
```

##### Efficient Querying Capabilities
```http
# Filtering
GET /api/v1/users?status=active&role=admin
GET /api/v1/products?price_min=10&price_max=100&category=electronics
GET /api/v1/orders?created_after=2023-01-01&created_before=2023-01-31

# Sorting
GET /api/v1/users?sort=name
GET /api/v1/products?sort=-price,name  # Descending price, then ascending name
GET /api/v1/orders?sort=-createdAt    # Newest first

# Pagination
GET /api/v1/users?limit=25&offset=50
GET /api/v1/products?page=3&size=20
GET /api/v1/orders?limit=100&after=2023-01-15T00:00:00Z

# Field selection (for bandwidth optimization)
GET /api/v1/users?fields=id,name,email
GET /api/v1/products?fields=id,name,price,category

# Expanding related resources (instead of N+1 problem)
GET /api/v1/orders/123?expand=customer,items.product
GET /api/v1/users/456?expand=orders,orders.items,orders.items.product
```

##### Proper HTTP Methods and Status Codes
```http
# Correct usage of HTTP methods
POST   /api/v1/users          # 201 Created + Location header
GET    /api/v1/users/123      # 200 OK
PUT    /api/v1/users/123      # 200 OK or 204 No Content
PATCH  /api/v1/users/123      # 200 OK or 204 No Content
DELETE /api/v1/users/123      # 204 No Content

# Proper status codes
POST   /api/v1/users          # 409 Conflict if user already exists
GET    /api/v1/users/999      # 404 Not Found
PUT    /api/v1/users/123      # 409 Conflict if version mismatch
DELETE /api/v1/users/123      # 409 Conflict if has dependent records
GET    /api/v1/orders         # 429 Too Many Requests (rate limited)
POST   /api/v1/orders         # 402 Payment Required (if payment needed)
```

##### Security Best Practices
```http
# All endpoints require HTTPS
# No sensitive data in URLs or logs
# Proper authentication
GET    /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Proper authorization
DELETE /api/v1/users/123
# 403 Forbidden if user doesn't have permission to delete user 123

# Rate limiting
# 429 Too Many Requests with retry-after header

# Input validation and sanitization
# Protection against injection attacks
# Proper CORS headers
# Security headers: CSP, HSTS, X-Frame-Options, etc.

# No SQL/NoSQL injection vulnerabilities
# No XML External Entity (XXE) processing
# No deserialization of untrusted data
```

#### Complete Example: User Management API

##### Endpoints
```
GET    /api/v1/users                          # List users with filtering, pagination
POST   /api/v1/users                          # Create new user
GET    /api/v1/users/{userId}                 # Get specific user
PUT    /api/v1/users/{userId}                 # Update user (full replacement)
PATCH  /api/v1/users/{userId}                 # Partially update user
DELETE /api/v1/users/{userId}                 # Delete user
GET    /api/v1/users/{userId}/orders          # Get user's orders
POST   /api/v1/users/{userId}/orders          # Create order for user
```

##### Request/Response Examples

**Create User**
```http
POST /api/v1/users
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "password": "securePassword123!",
  "role": "user"
}

HTTP/1.1 201 Created
Location: /api/v1/users/123
Content-Type: application/json

{
  "data": {
    "id": 123,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "role": "user",
    "createdAt": "2023-06-15T10:30:00Z",
    "updatedAt": "2023-06-15T10:30:00Z"
  },
  "links": {
    "self": "https://api.example.com/api/v1/users/123",
    "collection": "https://api.example.com/api/v1/users"
  }
}
```

**Get User with Expanded Relationships**
```http
GET /api/v1/users/123?expand=orders,orders.items,orders.items.product
Accept: application/json

HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "id": 123,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "role": "user",
    "createdAt": "2023-06-15T10:30:00Z",
    "updatedAt": "2023-06-15T10:30:00Z",
    "orders": [
      {
        "id": 1001,
        "status": "completed",
        "totalAmount": 89.99,
        "createdAt": "2023-06-14T15:22:00Z",
        "items": [
          {
            "id": 5001,
            "quantity": 2,
            "unitPrice": 25.00,
            "product": {
              "id": 201,
              "name": "Wireless Headphones",
              "description": "Bluetooth noise-cancelling headphones",
              "price": 25.00,
              "category": "electronics"
            }
          },
          {
            "id": 5002,
            "quantity": 1,
            "unitPrice": 39.99,
            "product": {
              "id": 202,
              "name": "Smartphone Case",
              "description": "Protective case for iPhone 14",
              "price": 39.99,
              "category": "accessories"
            }
          }
        ]
      }
    ]
  },
  "meta": {
    "version": 1
  },
  "links": {
    "self": "https://api.example.com/api/v1/users/123",
    "collection": "https://api.example.com/api/v1/users",
    "orders": "https://api.example.com/api/v1/users/123/orders"
  }
}
```

## Migration Path from Bad to Good API

### Phase 1: Assessment and Planning
1. **Inventory existing endpoints** - Document all current APIs
2. **Identify pain points** - Gather feedback from API consumers
3. **Define API principles** - Establish design guidelines
4. **Create migration plan** - Prioritize changes by impact and effort

### Phase 2: Foundational Improvements
1. **Implement consistent error handling** - Adopt RFC 7807 Problem Details
2. **Add proper versioning** - Choose strategy (URL or header-based)
3. **Enforce HTTPS everywhere** - Redirect HTTP to HTTPS
4. **Add security headers** - CSP, HSTS, X-Frame-Options, etc.
5. **Implement request/response logging** - With correlation IDs
6. **Add rate limiting** - Protect against abuse

### Phase 3: API Design Improvements
1. **Standardize resource naming** - Use nouns, plural, kebab-case
2. **Consistent HTTP methods** - Follow REST conventions
3. **Uniform response formats** - Consistent structure for success/error
4. **Add proper status codes** - Use full range of HTTP status codes
5. **Implement pagination** - For all list endpoints
6. **Add filtering and sorting** - Standard query parameters
7. **Implement field selection** - For bandwidth optimization

### Phase 4: Advanced Features
1. **Add HATEOAS links** - For discoverability
2. **Implement caching headers** - ETag, Last-Modified, Cache-Control
3. **Add content negotiation** - Support JSON, XML, etc.
4. **Create comprehensive documentation** - OpenAPI/Swagger specs
5. **Implement API analytics** - Usage monitoring and alerting
6. **Add API versioning strategy** - Deprecation and sunset policies
7. **Implement webhook support** - For asynchronous notifications

### Phase 5: Documentation and Governance
1. **Create API style guide** - Documentation standards
2. **Implement API governance** - Review process for changes
3. **Developer portal** - Documentation, SDKs, code samples, interactive console
4. **API monitoring** - Performance, error rates, usage analytics
5. **Deprecation policy** - How and when to retire old versions
6. **Backward compatibility** - Guidelines for breaking changes

## Key Takeaways

### Avoid These Anti-Patterns
1. **Inconsistent Naming** - Confuses API consumers
2. **Poor Error Handling** - Makes debugging difficult
3. **Missing Versioning** - Creates breaking change nightmares
4. **Inconsistent Responses** - Increases client complexity
5. **Security Negligence** - Leads to data breaches
6. **Inefficient Data Fetching** - Causes performance problems
7. **Wrong HTTP Methods** - Violates REST principles
8. **Lack of Documentation** - Increases integration time

### Embrace These Practices
1. **Resource-Oriented Design** - Think nouns, not verbs
2. **Consistent Error Responses** - Use RFC 7807 Problem Details
3. **Semantic Versioning** - Clear communication of changes
4. **Uniform Response Formats** - Predictable structure for clients
5. **Security First** - Authentication, authorization, encryption
6. **Query Capabilities** - Filter, sort, paginate, select fields
7. **Proper HTTP Methods** - GET, POST, PUT, PATCH, DELETE semantics
8. **Comprehensive Documentation** - Reduce integration friction
9. **Observability** - Logging, monitoring, tracing
10. **Backward Compatibility** - Respect existing consumers