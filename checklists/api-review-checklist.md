# API Review Checklist

## API Design & Implementation
### RESTful Principles
- [ ] Do endpoints follow RESTful conventions and resource-oriented design?
- [ ] Are HTTP methods used correctly (GET for retrieval, POST for creation, PUT/PATCH for updates, DELETE for removal)?
- [ ] Are status codes appropriate for different outcomes (200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity, 500 Internal Server Error)?
- [ ] Is there consistent naming conventions for endpoints and resources (plural vs singular, hyphens vs underscores)?
- [ ] Are API versions handled appropriately in the URI or headers?
- [ ] Are error responses consistent and informative with standard error formats?

### Request/Response Design
- [ ] Are request/response payloads well-defined and documented?
- [ ] Is JSON used as the primary format for request/response bodies?
- [ ] Are request bodies validated against schemas (JSON Schema, OpenAPI, etc.)?
- [ ] Are response formats consistent across endpoints (envelope structure, paging, etc.)?
- [ ] Are date/time formats standardized (ISO 8601 UTC)?
- [ ] Are IDs consistently represented (strings vs integers, UUID format)?
- [ ] Are empty collections represented appropriately (empty array vs null)?
- [ ] Are boolean values represented as true/false (not 0/1 or "true"/"false")?

### Query Parameters & Filtering
- [ ] Are query parameters used appropriately for filtering, sorting, and pagination?
- [ ] Are standard parameter names used (limit, offset, sort, filter, q/search)?
- [ ] Is pagination implemented correctly with limit/offset or cursor-based approaches?
- [ ] Are sort parameters flexible (field:direction syntax)?
- [ ] Are filter parameters flexible and documented?
- [ ] Are range queries supported (gte, lte, gt, lt)?
- [ ] Is search functionality implemented for text fields?

### Error Handling
- [ ] Are errors returned with appropriate HTTP status codes?
- [ ] Is there a consistent error response structure?
- [ ] Do error messages provide actionable information without leaking sensitive details?
- [ ] Are validation errors clearly field-specific?
- [ ] Are error codes provided for programmatic handling?
- [ ] Is StackTrace or internal details excluded from error responses in production?

### Security
- [ ] Is authentication required for all endpoints that need it?
- [ ] Are authentication tokens validated properly (signature, expiration)?
- [ ] Are authorization checks performed at the endpoint level?
- [ ] Is sensitive data masked in responses (passwords, tokens, PII)?
- [ ] Are rate limiting and throttling implemented where appropriate?
- [ ] Are CORS policies properly configured for web clients?
- [ ] Are security headers present (X-Content-Type-Options, X-Frame-Options, etc.)?
- [ ] Is input validation performed to prevent injection attacks (SQL, NoSQL, Command)?
- [ ] Are parameters properly sanitized and validated?

### Performance & Scalability
- [ ] Are database queries optimized with proper indexing?
- [ ] Are N+1 query problems avoided through eager loading or batching?
- [ ] Is pagination implemented to prevent large response payloads?
- [ ] Are response payloads kept reasonable (field selection, compression)?
- [ ] Are caching headers set appropriately (Cache-Control, ETag, Last-Modified)?
- [ ] Are expensive operations asyncronized or queued when appropriate?
- [ ] Are timeouts configured for external service calls?
- [ ] Are connection pools properly sized and monitored?

### Documentation & Discoverability
- [ ] Is the API documented with OpenAPI/Swagger or similar?
- [ ] Are all endpoints, parameters, and response codes documented?
- [ ] Are examples provided for requests and responses?
- [ ] Is authentication clearly documented?
- [ ] Are error codes and messages documented?
- [ ] Is there a getting started guide or quick reference?
- [ ] Is the documentation versioned with the API?
- [ ] Are deprecated endpoints clearly marked?

### Backward Compatibility
- [ ] Are breaking changes avoided or properly versioned?
- [ ] When removing fields, are they deprecated first?
- [ ] When adding fields, are they made optional?
- [ ] Are changes to data types avoided or handled gracefully?
- [ ] Is there a deprecation policy in place?
- [ ] Are sunset timelines provided for deprecated endpoints?

### Testing & Quality
- [ ] Is there automated test coverage for the API (unit, integration, contract)?
- [ ] Are both positive and negative test cases covered?
- [ ] Are edge cases tested (boundary values, empty inputs, large payloads)?
- [ ] Is performance/load testing conducted for critical endpoints?
- [ ] Are security tests performed (authentication, authorization, injection)?
- [ ] Is API contract testing implemented to prevent breaking changes?
- [ ] Are mocks or stubs used effectively for external dependencies?
- [ ] Are tests included in CI/CD pipeline?