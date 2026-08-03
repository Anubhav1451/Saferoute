# Backend Review Checklist

## API Design & Implementation
- [ ] Are API endpoints RESTful and follow consistent naming conventions?
- [ ] Are HTTP methods used correctly (GET, POST, PUT, DELETE, PATCH)?
- [ ] Are status codes appropriate for different outcomes?
- [ ] Are request/response payloads well-defined and validated?
- [ ] Are API versions handled appropriately?
- [ ] Are error responses consistent and informative?

## Data Access & Storage
- [ ] Are database queries optimized (indexes, joins, N+1 problems)?
- [ ] Are database connections properly managed (pooled, closed)?
- [ ] Are ORM usages correct and efficient?
- [ ] Are transactions used appropriately for data consistency?
- [ ] Are database migrations backward compatible?
- [ ] Are sensitive data fields encrypted at rest?

## Business Logic
- [ ] Is business logic correctly implemented according to requirements?
- [ ] Are complex calculations validated for correctness?
- [ ] Are state transitions valid and well-defined?
- [ ] Are race conditions handled appropriately?
- [ ] Are external service integrations robust (timeouts, retries, fallbacks)?

## Security
- [ ] Is authentication properly implemented and enforced?
- [ ] Are authorization checks performed at appropriate levels?
- [ ] Are SQL/NoSQL injection vulnerabilities prevented?
- [ ] Are sensitive data exposures prevented in logs/responses?
- [ ] Are rate limiting and throttling implemented where needed?
- [ ] Are CORS policies properly configured?
- [ ] Are secrets managed securely (not hardcoded)?

## Performance & Scalability
- [ ] Are asynchronous operations used where beneficial?
- [ ] Are caching strategies implemented appropriately?
- [ ] Are database queries optimized for scale?
- [ ] Are external API calls optimized (batching, caching)?
- [ ] Are resources properly released under load?
- [ ] Is pagination implemented for large datasets?

## Reliability & Observability
- [ ] Is proper logging implemented (structured, appropriate levels)?
- [ ] Are key metrics and KPIs instrumented?
- [ ] Are health checks implemented for services?
- [ ] Are circuit breakers used for external dependencies?
- [ ] Are timeouts configured appropriately?
- [ ] Are retry mechanisms implemented with exponential backoff?
- [ ] Are dead letter queues used for failed message processing?

## Testing & Quality
- [ ] Are unit tests written for business logic?
- [ ] Are integration tests covering critical paths?
- [ ] Are contract tests in place for APIs?
- [ ] Are load/performance tests conducted for critical paths?
- [ ] Are chaos engineering principles considered?
- [ ] Is test coverage adequate for critical components?

## Deployment & Operations
- [ ] Are configuration changes backward compatible?
- [ ] Are database migrations safe for zero-downtime deployment?
- [ ] Are feature flags used appropriately for risky changes?
- [ ] Are rollback procedures documented and tested?
- [ ] Are resource requirements properly defined (CPU, memory, storage)?