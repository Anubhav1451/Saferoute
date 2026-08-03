# Database Review Checklist

## Schema Design
- [ ] Are tables properly normalized (3NF or BCNF where appropriate)?
- [ ] Are primary keys appropriately chosen (surrogate vs natural keys)?
- [ ] Are foreign key relationships properly defined with appropriate constraints?
- [ ] Are indexes created for frequently queried columns?
- [ ] Are composite indexes considered for multi-column queries?
- [ ] Are JSON/document types used appropriately for semi-structured data?
- [ ] Are enum/lookup tables used for categorical data?
- [ ] Are partitioning/sharding strategies considered for large tables?

## Data Types & Constraints
- [ ] Are appropriate data types used for each column (size, precision)?
- [ ] Are constraints used appropriately (NOT NULL, UNIQUE, CHECK)?
- [ ] Are default values specified where meaningful?
- [ ] Are character sets and collations appropriate for the data?
- [ ] Are temporal data types used correctly (TIMESTAMP vs DATETIME)?
- [ ] Are monetary values stored using appropriate decimal types?
- [ ] Are IP addresses, emails, URLs stored with appropriate types/validation?

## Performance Considerations
- [ ] Are queries using indexes effectively (EXPLAIN plans reviewed)?
- [ ] Are N+1 query problems avoided?
- [ ] Are JOINs optimized and necessary?
- [ ] Are subqueries used appropriately or replaced with JOINs?
- [ ] Are wildcard searches (%) avoided on leading edges when possible?
- [ ] Are aggregate functions used with appropriate GROUP BY clauses?
- [ ] Are LIMIT/OFFSET used appropriately for pagination?
- [ ] Are materialized views considered for complex aggregations?

## Security
- [ ] Is sensitive data encrypted at rest (PII, passwords, financial data)?
- [ ] Are database connections using secure protocols (SSL/TLS)?
- [ ] Are database credentials stored securely (secrets management)?
- [ ] Is the principle of least privilege applied to database users?
- [ ] Are SQL injection vulnerabilities prevented through parameterized queries?
- [ ] Are audit logs enabled for sensitive data access/modification?
- [ ] Are database firewalls/restrictions configured appropriately?

## Backup & Recovery
- [ ] Are regular backups scheduled and tested?
- [ ] Are point-in-time recovery capabilities available?
- [ ] Are backup retention policies defined and followed?
- [ ] Are cross-region/geographic backups configured for disaster recovery?
- [ ] Are backup integrity checks performed regularly?
- [ ] Are recovery time objectives (RTO) and recovery point objectives (RPO) defined?

## Maintenance & Operations
- [ ] Are database statistics updated regularly for query optimization?
- [ ] Is index fragmentation/monitoring procedures in place?
- [ ] Are archive/purge strategies implemented for historical data?
- [ ] Are schema changes backward compatible where possible?
- [ ] Are database connection pools properly sized?
- [ ] Are long-running queries monitored and prevented?
- [ ] Are deadlocks monitored and resolved?
- [ ] Is replication lag monitored for replica setups?

## Testing & Validation
- [ ] Are schema changes tested in staging environments?
- [ ] Are data migration scripts tested for correctness and rollback?
- [ ] Are test datasets representative of production data characteristics?
- [ ] Are performance tests conducted with realistic data volumes?
- [ ] Are data validation scripts run after migrations?
- [ ] Are referential integrity constraints validated after data loads?

## Documentation
- [ ] Is the database schema documented (ERD, table descriptions)?
- [ ] Are data dictionaries maintained for important tables/columns?
- [ ] Are stored procedures/functions documented with parameters and return values?
- [ ] Are migration scripts versioned and documented?
- [ ] Are backup and recovery procedures documented?
- [ ] Are performance tuning guidelines documented?