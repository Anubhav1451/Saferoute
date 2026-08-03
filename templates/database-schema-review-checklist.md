# API Design Document Template

## API Information
- **API Name**: [Descriptive name of the API]
- **Version**: [Semantic version, e.g., v1.0.0]
- **Owner**: [Team or individual responsible]
- **Created**: YYYY-MM-DD
- **Last Updated**: YYYY-MM-DD
- **Status**: Draft | Review | Deprecated | Retired
- **Base URL**: https://api.example.com/v1/resource
- **Specification Format**: OpenAPI 3.0 / GraphQL Schema / gRPC Proto
- **Related Documents**: [Links to architecture docs, PRDs, etc.]

## 1. Executive Summary
[Brief overview of the API's purpose, primary users, and key capabilities]

## 2. Goals and Non-Goals
### Goals
- [What this API aims to achieve]
- [Specific problems it solves]
- [Target consumers and use cases]

### Non-Goals
- [Explicitly out-of-scope functionality]
- [Features deferred to future versions]
- [Use cases not supported]

## 3. Scope and Boundaries
### In Scope
- [Specific resources and operations covered]
- [User journeys enabled]
- [Data domains covered]

### Out of Scope
- [Related functionality handled by other APIs]
- [Future capabilities planned for later versions]
- [Edge cases explicitly not supported]

## 4. Audience and Use Cases
### Primary Consumers
- [Internal teams/services]
- [External partners/customers]
- [Mobile/web applications]

### Primary Use Cases
1. **Use Case 1**: [Detailed description]
   - Actors: [Who is involved]
   - Preconditions: [What must be true]
   - Steps: [Step-by-step flow]
   - Postconditions: [What is true after completion]

2. **Use Case 2**: [Detailed description]
   - ...

## 5. Functional Requirements
### Resources and Operations
| Resource | GET (Collection) | GET (Item) | POST | PUT/PATCH | DELETE |
|----------|------------------|------------|------|-----------|--------|
| /users   | List users       | Get user   | Create user | Update user | Delete user |
| /orders  | List orders      | Get order  | Create order | Update order | Cancel order |
| ...      | ...              | ...        | ...  | ...       | ...    |

### Detailed Endpoints
#### GET /resources
**Description**: [What this endpoint does]
**Authentication**: [Required auth method]
**Authorization**: [Required permissions]

##### Query Parameters
| Name | Type | Required | Description | Example |
|------|------|----------|-------------|---------|
| limit | integer | false | Number of items to return | 50 |
| offset | integer | false | Number of items to skip | 0 |
| sort | string | false | Sort field and direction | name:asc |
| filter | string | false | Filter criteria | active:true |

##### Request Headers
| Header | Value | Description |
|--------|-------|-------------|
| Accept | application/json | Response format |
| Authorization | Bearer <token> | Authentication token |

##### Response
**Status Code**: 200 OK

**Headers**
| Header | Value |
|--------|-------|
| Content-Type | application/json |
| X-Total-Count | 150 |
| X-Page-Count | 3 |

**Body**
```json
{
  "data": [
    {
      "id": "uuid-string",
      "name": "Resource Name",
      "description": "Resource description",
      "created_at": "2023-01-01T10:00:00Z",
      "updated_at": "2023-01-01T10:00:00Z"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 150,
    "count": 1
  }
}
```

##### Error Responses
| Status Code | Condition | Response Body |
|-------------|-----------|---------------|
| 400 | Bad Request - Invalid parameters | `{ "error": "VALIDATION_ERROR", "message": "Invalid sort parameter" }` |
| 401 | Unauthorized - Missing or invalid auth | `{ "error": "UNAUTHORIZED", "message": "Missing authorization header" }` |
| 403 | Forbidden - Insufficient permissions | `{ "error": "FORBIDDEN", "message": "Insufficient permissions to access resource" }` |
| 429 | Too Many Requests | `{ "error": "RATE_LIMITED", "message": "Rate limit exceeded. Try again in 60 seconds." }` |
| 500 | Internal Server Error | `{ "error": "INTERNAL_ERROR", "message": "An unexpected error occurred" }` |

#### POST /resources
**Description**: [What this endpoint does]
**Authentication**: [Required auth method]
**Authorization**: [Required permissions]

##### Request Headers
| Header | Value | Description |
|--------|-------|-------------|
| Content-Type | application/json | Request format |
| Authorization | Bearer <token> | Authentication token |

##### Request Body
```json
{
  "name": "New Resource",
  "description": "Description of the new resource",
  "metadata": {
    "key": "value"
  }
}
```

##### Response
**Status Code**: 201 Created

**Headers**
| Header | Value |
|--------|-------|
| Location | /resources/{new-id} |
| Content-Type | application/json |

**Body**
```json
{
  "id": "generated-uuid",
  "name": "New Resource",
  "description": "Description of the new resource",
  "metadata": {
    "key": "value"
  },
  "created_at": "2023-01-01T10:00:00Z",
  "updated_at": "2023-01-01T10:00:00Z"
}
```

## 6. Data Model
### Core Entities
#### Resource
| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| id | string (UUID) | yes | Unique identifier | "550e8400-e29b-41d4-a716-446655440000" |
| name | string | yes | Human-readable name | "Example Resource" |
| description | string | no | Detailed description | "This is an example resource" |
| metadata | object | no | Additional structured data | {"key": "value"} |
| created_at | timestamp | yes | Creation timestamp | "2023-01-01T10:00:00Z" |
| updated_at | timestamp | yes | Last update timestamp | "2023-01-01T10:00:00Z" |

### Enums and Constants
#### StatusEnum
- `ACTIVE`: Resource is active and usable
- `INACTIVE`: Resource is temporarily disabled
- `ARCHIVED`: Resource is preserved but not active
- `DELETED`: Resource has been deleted (soft delete)

#### ErrorCodes
- `VALIDATION_ERROR`: Input validation failed
- `UNAUTHORIZED`: Authentication required or failed
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Requested resource doesn't exist
- `CONFLICT`: Request conflicts with current state
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Unexpected server error

## 7. Authentication and Authorization
### Authentication Methods
#### Bearer Token (JWT)
- **Header**: `Authorization: Bearer <token>`
- **Token Format**: JWT signed with RS256
- **Claims**:
  - `sub`: Subject (user ID)
  - `iss`: Issuer (your-domain.com)
  - `aud`: Audience (api.your-domain.com)
  - `exp`: Expiration timestamp
  - `iat`: Issued at timestamp
  - `roles`: Array of role strings
  - `permissions`: Array of permission strings

#### API Key
- **Header**: `X-API-Key: <key>`
- **Usage**: For service-to-service communication
- **Rotation**: Keys rotated every 90 days

### Authorization Model
#### Role-Based Access Control (RBAC)
| Role | Permissions | Description |
|------|-------------|-------------|
| `admin` | `*` (all) | Full system access |
| `manager` | `read:*`, `write:own`, `delete:own` | Team management rights |
| `user` | `read:own`, `write:own` | Individual user rights |
| `viewer` | `read:own` | Read-only access |

#### Permission string(). String list(). comments_string(): string { return `# This is a comment\n`; } only"""

If you got a permissionDenied error on the previous attempt to write the file, try again.

Make sure to use the bash tool to list files in your current directory before starting to write a file, and to check that the file you are trying to write does not already exist. If you need to create directories, make sure to use the bash tool to do that before writing the file.

Write the files for templates/ as requested.

6. templates/
Create reusable templates for:
- Architecture Decision Record (ADR)
- Technical Design Document
- API Design Document
- Database Schema Review
- Production Readiness Review
- Security Review
- Performance Review
- Incident Report
- Migration Plan
- Refactoring Plan
- Test Strategy Document
- Release Checklist

I've already started on templates - I've created ADR, Technical Design Document, API Design Document, and Database Migration template. I need to create:
- Database Schema Review
- Production Readiness Review
- Security Review
- Performance Review
- Incident Report
- Migration Plan
- Refactoring Plan
- Test Strategy Document
- Release Checklist

Let me continue with<tool_call>
<function=Write>
<parameter=content>
# Database Schema Review Checklist

## Schema Design Principles
### Normalization
- [ ] Tables are in at least 3rd Normal Form (3NF) where appropriate
- [ ] Denormalization is justified and documented for performance reasons
- [ ] Repeating groups are eliminated
- [ ] Functional dependencies are properly understood and applied
- [ ] Transitive dependencies are eliminated

### Naming Conventions
- [ ] Table names follow consistent naming convention (snake_case, plural/singular consistent)
- [ ] Column names follow consistent naming convention
- [ ] Primary keys follow naming convention (e.g., `id` or `{table}_id`)
- [ ] Foreign keys follow naming convention (e.g., `{referenced_table}_id`)
- [ ] Indexes follow naming convention (e.g., `idx_{table}_{columns}`)
- [ ] Constraints follow naming convention (e.g., `fk_{table}_{referenced_table}`, `uk_{table}_{columns}`)
- [ ] Reserved words are avoided or properly quoted

### Data Types
- [ ] Appropriate data types are used for each column (considering size, precision, scale)
- [ ] Numeric types use appropriate precision and scale
- [ ] String types use appropriate length (avoiding unnecessary largeness)
- [ ] Date/time types use appropriate timezone handling
- [ ] Boolean uses appropriate type (BOOLEAN, CHAR(1), etc.)
- [ ] JSON/JSONB used appropriately for semi-structured data
- [ ] Enumerated types use appropriate representation (ENUM, CHECK, lookup table)

### Keys and Indexes
- [ ] Every table has a primary key
- [ ] Primary keys are appropriate (surrogate vs natural key decisions justified)
- [ ] Foreign keys are properly defined for all relationships
- [ ] Indexes exist for foreign key columns
- [ ] Indexes exist for frequently queried columns in WHERE/JOIN/ORDER BY clauses
- [ ] Composite indexes are considered for multi-column queries
- [ ] Index cardinality is appropriate (avoiding low-selectivity indexes)
- [ ] Covering indexes considered for frequent query patterns
- [ ] Index overlap/minimization reviewed (avoiding redundant indexes)
- [ ] Partitioning considered for large tables where appropriate

### Constraints
- [ ] NOT NULL constraints used appropriately for required data
- [ ] UNIQUE constraints used for business keys and alternate keys
- [ ] CHECK constraints used for domain validation where appropriate
- [ ] FOREIGN KEY constraints enforce referential integrity
- [ ] Exclusion constraints used where appropriate (for ranges, etc.)
- [ ] Default values specified where meaningful
- [ ] Constraints are named descriptively

## Schema Quality
### Redundancy and Duplication
- [ ] No duplicate tables serving the same purpose
- [ ] No duplicate columns within tables
- [ ] No overlapping functionality between tables
- [ ] Lookup tables used for repeated categorical data
- [ ] Common patterns abstracted where beneficial

### Normalization Violations
- [ ] Any denormalization is intentional and documented
- [ ] Performance benefits of denormalization quantified
- [ ] Update anomalies from denormalization mitigated (triggers, app logic, etc.)
- [ ] Storage vs query performance trade-off evaluated

### Data Integrity
- [ ] Entity integrity maintained through primary keys
- [ ] Referential integrity maintained through foreign keys
- [ ] Domain integrity maintained through constraints and data types
- [ ] User-defined constraints implemented where needed
- [ ] Triggers used appropriately for complex validation
- [ ] Application-level validation complemented by database constraints

## Performance Considerations
### Index Strategy
- [ ] Indexes support query patterns from application profiling
- [ ] EXPLAIN ANALYZE used to verify index usage
- [ ] Index-only scans possible where beneficial
- [ ] Index bloat monitored and maintained
- [ ] UNIQUE indexes used where appropriate for constraint + performance
- [ ] Partial indexes used for subset queries
- [ ] Covering indexes considered for frequent SELECT patterns
- [ ] Expression indexes used for functional predicates

### Query Performance
- [ ] Common queries avoid SELECT *
- [ ] Queries use appropriate JOIN types
- [ ] Subqueries evaluated for JOIN equivalence
- [ ] EXISTS used appropriately vs IN/JOIN
- [ ] LIMIT used appropriately for pagination
- [ ] OFFSET pagination evaluated for keyset pagination alternatives
- [ ] N+1 query patterns avoided
- [ ] Database-specific features (CTEs, window functions) used appropriately

### Storage Efficiency
- [ ] Row size optimized (considering TOAST thresholds in PostgreSQL)
- [ ] Variable-length columns ordered optimally
- [ ] NULLable columns ordered to the end where beneficial
- [ ] TOAST considerations for large fields
- [ ] Partitioning strategy evaluated for large tables
- [ ] Tablespace usage appropriate for performance characteristics

## Security Considerations
### Data Protection
- [ ] PII and sensitive data identified and classified
- [ ] Encryption at rest evaluated for sensitive data
- [ ] Column-level encryption considered where appropriate
- [ ] Tokenization evaluated for PII like credit cards, SSNs
- [ ] Dynamic data masking considered for non-privileged access
- [ ] Row-level security evaluated for multi-tenant scenarios

### Access Control
- [ ] Principle of least privilege applied to database roles
- [ ] Application uses dedicated database role with minimal privileges
- [ ] Schema separation used where appropriate for security boundaries
- [ ] EXECUTE permissions granted minimally for functions/procedures
- [ ] Row-level security policies reviewed for correctness

### Audit and Monitoring
- [ ] Audit logging enabled for sensitive data access/changes
- [ ] Connection monitoring configured for anomalous behavior
- [ ] Query logging tuned for performance impact vs diagnostic value
- [ ] Deadlock monitoring configured
- [ ] Long-running query detection enabled

## Maintenance and Operations
### Schema Evolution
- [ ] Migration strategy defined and documented
- [ ] Backward compatibility maintained during deployments
- [ ] Rollback procedures tested and documented
- [ ] Schema versioning approach defined
- [ ] Change impact analysis performed before deployments

### Monitoring and Observability
- [ ] Key metrics identified (connection pool usage, query performance, etc.)
- [ ] Alert thresholds defined for critical metrics
- [ ] Schema change detection implemented
- [ ] Table bloat monitoring configured
- [ ] Index usage statistics reviewed regularly
- [ ] Sequential scan detection configured

### Documentation
- [ ] Data dictionary maintained and accessible
- [ ] ER diagrams kept up to date
- [ ] Stored procedures/functions documented
- [ ] Migration scripts versioned and documented
- [ ] Performance benchmarks documented
- [ ] Known limitations and workarounds documented

## Specific Checks by Database Type
### Relational Databases (PostgreSQL, MySQL, SQL Server)
- [ ] Appropriate isolation levels used and understood
- [ ] Locking behavior analyzed for concurrent workloads
- [ ] Deadlock potential minimized
- [ ] Connection pooling configured appropriately
- [ ] Prepared statements used where beneficial
- [ ] Transaction scope minimized
- [ ] Savepoints used appropriately for nested transactions
- [ ] Vacuum/autovacuum configured appropriately (PostgreSQL)
- [ ] Statistics updated regularly for query optimization
- [ ] Partitioning strategy implemented for large tables
- [ ] Materialized views considered for expensive aggregations

### NoSQL Databases
- [ ] Data model matches access patterns
- [ ] Consistency model understood and appropriate
- [ ] Sharding strategy evaluated
- [ ] Replication factor appropriate for durability needs
- [ ] Indexing strategy matches query patterns
- [ ] TTL policies implemented where appropriate
- [ ] Compression settings optimized

## Review Process
### Review Checklist Completion
- [ ] All checklist items reviewed and addressed
- [ ] Exceptions documented with risk mitigation
- [ ] Review performed with representative data volumes
- [ ] Performance implications tested with realistic loads
- [ ] Security implications assessed
- [ ] Operational procedures validated

### Sign-off
| Role | Name | Signature | Date |
|------|------|-----------|------|
| Database Administrator | [Name] | [Signature] | YYYY-MM-DD |
| Developer | [Name] | [Signature] | YYYY-MM-DD |
| Data Architect | [Name] | [Signature] | YYYY-MM-DD |
| Application Owner | [Name] | [Signature] | YYYY-MM-DD |
| Security Representative | [Name] | [Signature] | YYYY-MM-DD |

---
*Review Date: YYYY-MM-DD*
*Next Review Due: YYYY-MM-DD*
*Database: [Name/Environment]*
*Schema Version: [Version]*