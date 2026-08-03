# Database Review Guide

This checklist provides a comprehensive framework for reviewing database design, schema, queries, and related components to ensure data integrity, performance, security, and maintainability.

## How to Use This Guide

1. Review database schemas, ER diagrams, and migration scripts
2. Analyze SQL queries, stored procedures, and database access patterns
3. Consider data volume, growth projections, and access patterns
4. Evaluate both current state and future scalability needs
5. Check each item in the relevant categories below
6. Use database-specific tools (EXPLAIN, profiling, etc.) to validate assumptions
7. Prioritize issues based on impact on data integrity, performance, and security
8. Ensure compliance with organizational data standards and governance policies
9. Document findings and provide specific recommendations for improvement

## Review Categories

### 1. Data Modeling & Schema Design
- [ ] Is the data model properly normalized (to at least 3NF) unless denormalization is justified for performance?
- [ ] Are entities and relationships correctly identified and represented?
- [ ] Are primary keys chosen appropriately (surrogate vs natural, UUID vs sequential)?
- [ ] Are foreign key constraints used to enforce referential integrity?
- [ ] Are unique constraints applied where data uniqueness is required?
- [ ] Are check constraints used for domain validation where appropriate?
- [ ] Are nullable columns minimized and only used when truly optional?
- [ ] Are data types chosen appropriately for the data being stored (size, precision, type)?
- [ ] Are temporal data types used correctly for dates and times?
- [ ] Are enumerated values implemented properly (lookup tables, ENUM types, constraints)?
- [ ] Are JSON/XML or other semi-structured data types used appropriately?
- [ ] Are large objects (BLOBs/CLOBs) handled correctly or stored externally?
- [ ] Are access patterns considered in denormalization decisions?
- [ ] Are audit trails and historical data requirements addressed?
- [ ] Are multi-tenancy requirements considered in the schema design?
- [ ] Are partitioning strategies considered for large tables?

### 2. Naming Conventions & Standards
- [ ] Are table and column names clear, descriptive, and consistent?
- [ ] Is a naming convention followed consistently (snake_case, camelCase, PascalCase)?
- [ ] Are prefixes/suffixes used appropriately and consistently (tbl_, _id, _flag, etc.)?
- [ ] Are reserved words avoided in identifiers?
- [ ] Are abbreviations used sparingly and consistently?
- [ ] Are acronyms expanded in documentation where unclear?
- [ ] Are junction/association tables named clearly to indicate their purpose?
- [ ] Are views, stored procedures, and functions named consistently?
- [ ] Are constraints named meaningfully to aid in debugging?
- [ ] Are indexes named consistently and descriptively?

### 3. Data Integrity & Constraints
- [ ] Are primary keys defined on all tables?
- [ ] Are foreign key constraints used to maintain referential integrity?
- [ ] Are unique constraints applied where data uniqueness is business-critical?
- [ ] Are check constraints used for data validation (ranges, formats, etc.)?
- [ ] Are NOT NULL constraints used appropriately for required fields?
- [ ] Are default values specified where appropriate?
- [ ] Are triggers used judiciously for complex validation that constraints can't handle?
- [ ] Are cascading updates and deletes used carefully with understanding of implications?
- [ ] Are constraints validated against business rules and requirements?
- [ ] Are constraint names meaningful and helpful for error messages?
- [ ] Are deferrable constraints used only when necessary and understood?
- [ ] Are partial indexes used where appropriate for conditional uniqueness?

### 4. Indexing Strategy
- [ ] Are primary keys indexed automatically (as they should be)?
- [ ] Are foreign keys indexed to improve join performance?
- [ ] Are indexes created on columns used in WHERE, JOIN, ORDER BY, and GROUP BY clauses?
- [ ] Are composite indexes considered for multi-column queries?
- [ ] Are index column orders optimized for query patterns (selectivity, cardinality)?
- [ ] Are duplicate or redundant indexes avoided?
- [ ] Are index maintenance considerations evaluated (write performance vs read performance)?
- [ ] Are specialized indexes considered (full-text, spatial, GIN, GiST, etc.) when appropriate?
- [ ] Are filtered/partial indexes used for common query subsets?
- [ ] Are index statistics kept up-to-date for query planner effectiveness?
- [ ] Are index-only scans possible through covering indexes?
- [ ] Are index bloat and fragmentation monitored and managed?
- [ ] Are partitioning strategies considered for large tables with appropriate partition keys?
- [ ] Are indexing strategies reviewed regularly based on query performance data?

### 5. Query Performance & Optimization
- [ ] Are queries using appropriate JOIN types (INNER, LEFT, RIGHT, FULL) for the data relationship?
- [ ] Are WHERE clauses selective enough to leverage indexes effectively?
- [ ] Are functions avoided on indexed columns in WHERE clauses (sargability)?
- [ ] Are SELECT clauses limited to needed columns rather than using SELECT *?
- [ ] Are ORDER BY clauses supported by appropriate indexes?
- [ ] Are GROUP BY operations optimized where possible?
- [ ] Are subqueries evaluated for potential rewriting as JOINs for better performance?
- [ ] Are UNION vs UNION ALL chosen appropriately based on duplicate handling needs?
- [ ] Are EXISTS/NOT EXISTS used appropriately for existence checks?
- [ ] Are LIMIT/OFFSET patterns used carefully for pagination (considering keyset pagination)?
- [ ] Are query hints used judiciously and only when necessary?
- [ ] Are query execution plans regularly reviewed for changes in data volume/distribution?
- [ ] Are parameter sniffing issues addressed where relevant?
- [ ] Are ORM-generated queries reviewed for efficiency?
- [ ] Are N+1 query problems identified and resolved?
- [ ] Are batch operations used where appropriate to reduce round-trips?
- [ ] Are transaction sizes kept reasonable to minimize locking duration?

### 6. Transaction Management & Concurrency
- [ ] Are transactions kept as short as possible to minimize locking?
- [ ] Are appropriate isolation levels chosen based on consistency requirements?
- [ ] Are dirty reads, non-repeatable reads, and phantom reads understood and acceptable?
- [ ] Are deadlock scenarios minimized through consistent lock ordering?
- [ ] Are deadlock detection and resolution mechanisms in place?
- [ ] Are savepoints used appropriately for complex transaction logic?
- [ ] Are autonomous transactions used judiciously with understanding of implications?
- [ ] Are distributed transactions avoided when possible due to complexity and performance cost?
- [ ] Are idempotency considerations built into transactional operations?
- [ ] Are retry mechanisms implemented for transient failures?
- [ ] Are transaction boundaries clearly defined in application code?
- [ ] Are read-only transactions declared as such for optimization?
- [ ] Are long-running transactions avoided or properly monitored?
- [ ] Are connection pooling configurations appropriate for transaction volume?

### 7. Security & Access Control
- [ ] Is the principle of least privilege applied to database users and roles?
- [ ] Are strong authentication mechanisms used (certificates, centralized auth)?
- [ ] Are passwords stored securely (hashed with salt) if password authentication is used?
- [ ] Are network connections encrypted (SSL/TLS) for database access?
- [ ] Are sensitive data fields encrypted at rest (PII, PHI, financial data)?
- [ ] Are column-level or row-level security implemented where needed?
- [ ] Are database accounts used by applications restricted to necessary privileges?
- [ ] Are schema ownership and object permissions reviewed regularly?
- [ ] Are SQL injection vulnerabilities prevented through parameterized queries/prepared statements?
- [ ] Are dynamic SQL constructions avoided or properly sanitized?
- [ ] Are audit logs enabled for access to sensitive data?
- [ ] Are database activity monitoring solutions considered for high-security environments?
- [ ] Are backups encrypted and secured appropriately?
- [ ] Are database ports restricted to necessary network segments?
- [ ] Are default accounts and passwords changed or disabled?
- [ ] Are vulnerability assessments performed regularly on database software?

### 8. Backup, Recovery & Disaster Recovery
- [ ] Are regular backups scheduled and tested (full, differential, transaction log)?
- [ ] Are backup retention policies aligned with business and regulatory requirements?
- [ ] Are backups stored off-site or in geographically separate locations?
- [ ] Are restore procedures documented and regularly tested?
- [ ] Are point-in-time recovery capabilities configured and tested?
- [ ] Are recovery time objectives (RTO) and recovery point objectives (RPO) defined and met?
- [ ] Are backup integrity checks performed regularly (checksums, test restores)?
- [ ] Are transaction logs properly managed and archived?
- [ ] Are standby replicas or log shipping configured for high availability?
- [ ] Are failover procedures documented and tested?
- [ ] Are regional disaster recovery plans in place for catastrophic failures?
- [ ] Are backup windows scheduled to minimize impact on production performance?
- [ ] Are backup compression and encryption enabled where appropriate?
- [ ] Are cloud backup and snapshot features leveraged where available?
- [ ] Are legal hold and e-discovery capabilities considered for compliance?

### 9. Maintenance & Administration
- [ ] Are regular maintenance windows scheduled for index rebuilds and statistics updates?
- [ ] Are fragmentation and bloat monitored and addressed regularly?
- [ ] Are database statistics kept up-to-date for optimal query planning?
- [ ] Are log files monitored and rotated appropriately to prevent disk exhaustion?
- [ ] Are temporary tablespaces managed and monitored?
- [ ] Are database parameters tuned for the specific workload and hardware?
- [ ] Are connection limits configured appropriately to prevent resource exhaustion?
- [ ] Are maximum connections, memory allocation, and cache sizes tuned?
- [ ] Are error logs monitored for recurring issues?
- [ ] Are version upgrade procedures tested and documented?
- [ ] Are patch management processes in place for security updates?
- [ ] Are database size and growth trends monitored and planned for?
- [ ] Are archive and purging strategies implemented for historical data?
- [ ] Are data masking and obfuscation techniques used for non-production environments?
- [ ] Are database change management processes followed (version control, migrations)?

### 10. Documentation & Metadata
- [ ] Is the database schema documented with descriptions for tables and columns?
- [ ] Are data dictionaries maintained and kept up-to-date?
- [ ] Are ER diagrams generated and available for reference?
- [ ] Are stored procedures, functions, and triggers documented with parameters and return values?
- [ ] Are indexing strategies documented with rationale?
- [ ] Are partitioning schemes explained and documented?
- [ ] Are data retention and archiving policies documented?
- [ ] Are backup and recovery procedures documented?
- [ ] Are security configurations and access controls documented?
- [ ] Are known issues and workarounds documented?
- [ ] Are database dependencies on external systems documented?
- [ ] Are connection strings and configuration parameters documented?
- [ ] Are database aliases and linkage information documented?
- [ ] Are data lineage and provenance tracked where important?
- [ ] Are glossaries of business terms and data definitions maintained?

### 11. Performance Monitoring & Optimization
- [ ] Are slow query logs enabled and reviewed regularly?
- [ ] Are database metrics monitored (connections, cache hit ratios, lock waits, etc.)?
- [ ] Are query execution plans analyzed for inefficient patterns?
- [ ] Are index usage statistics reviewed to identify unused or inefficient indexes?
- [ ] Are table and index bloat monitored and addressed?
- [ ] Are disk I/O patterns analyzed for hotspots and bottlenecks?
- [ ] Are memory utilization patterns examined for buffer pool efficiency?
- [ ] Are transaction log generation rates monitored for capacity planning?
- [ ] Are replication lag and synchronization monitored in clustered environments?
- [ ] Are deadlock and timeout incidents analyzed and addressed?
- [ ] Are connection pool usage and exhaustion monitored?
- [ ] Are CPU and memory utilization tracked for the database server?
- [ ] Are network latency and bandwidth monitored for distributed databases?
- [ ] Are custom metrics and alerts defined for application-specific performance concerns?
- [ ] Are benchmark tests performed regularly to establish baselines?
- [ ] Are load testing results used to inform capacity planning?

### 12. Application Integration & Data Access
- [ ] Are connection pools properly sized and configured for application needs?
- [ ] Are database connections properly closed or returned to the pool?
- [ ] Are connection leaks prevented through proper resource management?
- [ ] Are database access layers abstracted (DAO, Repository, ORM) for maintainability?
- [ ] AreObject-Relational Mapping (ORM) tools used appropriately with understanding of generated SQL?
- [ ] Are lazy loading and eager loading strategies chosen appropriately for access patterns?
- [ ] Are query caching mechanisms used where beneficial and safe?
- [ ] Are second-level caches configured and invalidated appropriately?
- [ ] Are batch operations used for bulk data processing?
- [ ] Are streaming APIs used for large result sets to avoid memory exhaustion?
- [ ] Are database timeouts configured appropriately for query execution?
- [ ] Are retry logic and exponential backoff implemented for transient failures?
- [ ] Are circuit breaker patterns used to prevent cascading failures?
- [ ] Are database version compatibility matrices maintained?
- [ ] Are database driver/jar versions kept up-to-date and compatible?
- [ ] Are connection string parameters secure (not hard-coded, not logged)?
- [ ] Are read-only replicas used for reporting and analytics workloads?
- [ ] Are write-heavy operations routed to primary instances appropriately?

### 13. Data Lifecycle Management
- [ ] Are data retention policies defined and implemented for different data types?
- [ ] Are archiving strategies employed for historical data that must be retained?
- [ ] Are purging strategies implemented for temporary or obsolete data?
- [ ] Are data anonymization or masking techniques used for non-production environments?
- [ ] Are legal hold capabilities implemented for e-discovery requirements?
- [ ] Are data migration strategies planned and tested for schema changes?
- [ ] Are data quality metrics monitored and reported?
- [ ] Are master data management practices implemented where appropriate?
- [ ] Are data lineage and provenance tracked for regulatory compliance?
- [ ] Are data obfuscation techniques used for development and testing datasets?
- [ ] Are data archiving and retrieval performance tested regularly?
- [ ] Are data drainage and aggregation strategies implemented for analytics workloads?
- [ ] Are data dignity and respect principles applied to personal information?
- [ ] Are data minimization principles followed to collect only what is necessary?

### 14. Scalability & Growth Planning
- [ ] Are horizontal scaling strategies considered (sharding, partitioning, federation)?
- [ ] Are vertical scaling limits understood and planned for?
- [ ] Are read replicas considered for scaling read-heavy workloads?
- [ ] Are caching layers evaluated to reduce database load?
- [ ] Are database upgrade procedures tested and documented?
- [ ] Are schema evolution strategies planned for minimal downtime?
- [ ] Are blue/green or canary deployment strategies considered for database changes?
- [ ] Are data migration tools and processes evaluated for large-scale changes?
- [ ] Are multi-region or geo-distributed database architectures considered?
- [ ] Are conflict resolution strategies planned for eventually consistent systems?
- [ ] Are database connection limits planned for concurrent user growth?
- [ ] Are storage capacity forecasts performed regularly?
- [ ] Are performance baselines established for scaling decisions?
- [ ] Are elasticity features of cloud databases leveraged where appropriate?
- [ ] Are hybrid cloud architectures considered for burst capacity?
- [ ] Are data locality and access patterns considered for distributed designs?
- [ ] Are regulatory restrictions on data location understood and planned for?

## Database-Specific Considerations

### For Relational Databases (PostgreSQL, MySQL, SQL Server, Oracle):
- [ ] Are appropriate storage engines selected (InnoDB vs MyISAM, etc.)?
- [ ] Are transaction isolation levels understood and chosen appropriately?
- [ ] Are locking behaviors (row-level, page-level, table-level) considered?
- [ ] Are MVCC (Multi-Version Concurrency Control) implications understood?
- [ ] Are vacuum/autovacuum settings configured appropriately for write-heavy workloads?
- [ ] Are transaction log management and retention policies configured?
- [ ] Are partitioning strategies implemented effectively (range, list, hash)?
- [ ] Are columnstore indexes considered for analytical workloads?
- [ ] Are in-memory tables explored for high-performance requirements?
- [ ] Are JSON/XML capabilities evaluated for semi-structured data needs?
- [ ] Are temporal tables used for automatic historical tracking?
- [ ] Are change data capture mechanisms implemented for integration needs?
- [ ] Are compression features evaluated for storage savings?
- [ ] Are advanced indexing options considered (BRIN, GIN, GiST, SP-GiST, etc.)?
- [ ] Are materialized views used for complex, frequently accessed aggregations?
- [ ] Are indexed views considered where supported and beneficial?
- [ ] Are query store or equivalent features used for performance tracking?
- [ ] Are resource governor or similar features used for workload management?

### For NoSQL Databases (MongoDB, Cassandra, Redis, etc.):
- [ ] Is the data model appropriate for the chosen NoSQL paradigm (document, key-value, column-family, graph)?
- [ ] Are consistency models understood and appropriate for the use case (strong, eventual, causal)?
- [ ] Are partition keys chosen effectively for distribution and query performance?
- [ ] Are replication strategies configured for availability and durability?
- [ ] Are sharding strategies planned for horizontal scaling?
- [ ] Are consistency levels tuned appropriately for read and write operations?
- [ ] Are tombstone and garbage collection policies understood and managed?
- [ ] Are read and write path optimizations considered?
- [ ] Are secondary indexes used judiciously understanding their trade-offs?
- [ ] Are TTL (time-to-live) policies implemented for automatic expiration?
- [ ] Are atomic operations and transactions supported as needed?
- [ ] Are bulk load and import/export processes optimized?
- [ ] Are compatibility and version upgrade paths understood?
- [ ] Are driver and client library best practices followed?
- [ ] Are monitoring and alerting adapted to NoSQL-specific metrics?
- [ ] Are backup and restore strategies appropriate for the data model?
- [ ] Are consistency and availability trade-offs evaluated per CAP theorem?

### For Data Warehouses & Analytics Platforms:
- [ ] Are star and snowflake schemas used appropriately for dimensional modeling?
- [ ] Are fact tables designed with appropriate granularity?
- [ ] Are slowly changing dimensions (SCD) handled correctly?
- [ ] Are columnar storage formats leveraged for analytical queries?
- [ ] Are compression techniques optimized for analytical workloads?
- [ ] Are partition strategies effective for large fact tables?
- [ ] Are materialized views and aggregations used effectively?
- [ ] Are workload management and resource isolation configured?
- [ ] Are workload priorities set appropriately for different user groups?
- [ ] Are result set caching implemented where beneficial?
- [ ] Are query optimization and rewrite features utilized?
- [ ] Are concurrency and scaling features understood and configured?
- [ ] Are data loading and ETL processes optimized for performance?
- [ ] Are data validation and quality checks implemented in the pipeline?
- [ ] Are aggregate awareness features used where available?
- [ ] Are workload balancing and queuing implemented?
- [ ] Are cost-based optimizations trusted and verified?
- [ ] Are workload segmentation strategies implemented?

## Review Process

### Preparation
- [ ] Obtain current schema diagrams (ERD, DDL scripts)
- [ ] Gather recent query performance reports and slow query logs
- [ ] Collect database configuration and parameter settings
- [ ] Review change management and migration history
- [ ] Understand application access patterns and data flow
- [ ] Identify peak usage times and seasonal variations
- [ ] Establish baseline performance metrics
- [ ] Identify compliance and regulatory requirements

### Execution
- [ ] Review schema against normalization principles
- [ ] Analyze index usage and effectiveness
- [ ] Examine query patterns and execution plans
- [ ] Evaluate transaction handling and locking behavior
- [ ] Assess backup, recovery, and disaster readiness
- [ ] Review security configurations and access controls
- [ ] Check maintenance procedures and automation
- [ ] Validate monitoring and alerting configurations
- [ ] Assess documentation completeness and accuracy
- [ ] Review change control and versioning practices
- [ ] Examine capacity planning and growth projections
- [ ] Evaluate compliance with data governance policies

### Reporting
- [ ] Document findings with specific examples and locations
- [ ] Quantify impact where possible (performance, storage, risk)
- [ ] Prioritize recommendations by severity and effort
- [ ] Provide clear remediation steps for each finding
- [ ] Reference relevant best practices and standards
- [ ] Include visual aids (diagrams, charts, excerpts) where helpful
- [ ] Summarize overall database health and readiness
- [ ] Outline short-term, medium-term, and long-term recommendations
- [ ] Suggest metrics for tracking improvement over time
- [ ] Plan follow-up reviews and reassessment timelines

## Severity Guidelines

**Critical**: 
- Risk of data loss or corruption
- Severe security vulnerabilities (SQL injection, excessive privileges)
- Complete inability to meet business requirements
- Blocking issues for production deployment

**High**: 
- Significant performance degradation under load
- Data integrity risks that could lead to incorrect results
- Security weaknesses that could lead to unauthorized access
- Major scalability limitations that will require near-term rework

**Medium**: 
- Moderate performance impact that affects user experience
- Maintenance difficulties that increase operational overhead
- Minor security issues that should be addressed
- Design imperfections that lead to suboptimal but workable solutions

**Low**: 
- Minor style or naming inconsistencies
- Documentation improvements
- Theoretical concerns unlikely to manifest in practice
- Opportunities for optimization that are not currently needed

## Review Checklist Summary

**Database System**: ________________________ (PostgreSQL/MySQL/SQL Server/Oracle/MongoDB/etc.)
**Version**: _______________________________
**Environment**: ____________________________ (Development/Test/Staging/Production)
**Schema Size**: _________________ tables, ___________ GB data
**Review Date**: _________________________
**Reviewer**: _____________________________
**Application/Service**: ____________________

### Overall Database Health Assessment
- [ ] Excellent (production-ready, minor optimizations possible)
- [ ] Good (suitable for production with monitoring)
- [ ] Satisfactory (needs improvements before production)
- [ ] Needs Work (significant issues requiring resolution)
- [ ] Unsatisfactory (major redesign required)

### Evaluation Categories Scores (1-5 scale, 5=best)

**Data Modeling & Design**: __/5
**Indexing Strategy**: __/5
**Query Performance**: __/5
**Data Integrity**: __/5
**Security & Compliance**: __/5
**Backup & Recovery**: __/5
**Performance & Scaling**: __/5
**Maintenance & Operations**: __/5
**Documentation**: __/5
**Overall Assessment**: __/5

### Detailed Findings

**Schema & Design Issues:**
1. ________________________________________
   Impact: ________________  Severity: ________
   Location: _______________  Table/Column: ________
   Recommendation: ____________________________

2. ________________________________________
   Impact: ________________  Severity: ________
   Location: _______________  Table/Column: ________
   Recommendation: ____________________________

**Indexing Issues:**
1. ________________________________________
   Impact: ________________  Severity: ________
   Table: _______________   Columns: ___________
   Recommendation: ____________________________

2. ________________________________________
   Impact: ________________  Severity: ________
   Table: _______________   Columns: ___________
   Recommendation: ____________________________

**Query Performance Issues:**
1. ________________________________________
   Impact: ________________  Severity: ________
   Query Type: ____________  Frequency: ________
   Recommendation: ____________________________

2. ________________________________________
   Impact: ________________  Severity: ________
   Query Type: ____________  Frequency: ________
   Recommendation: ____________________________

**Security & Access Control Issues:**
1. ________________________________________
   Impact: ________________  Severity: ________
   Issue Type: _____________  Object: ___________
   Recommendation: ____________________________

2. ________________________________________
   Impact: ________________  Severity: ________
   Issue Type: _____________  Object: ___________
   Recommendation: ____________________________

**Backup & Recovery Issues:**
1. ________________________________________
   Impact: ________________  Severity: ________
   Issue Type: _____________  Frequency: ________
   Recommendation: ____________________________

**Maintenance & Operations Issues:**
1. ________________________________________
   Impact: ________________  Severity: ________
   Issue Type: _____________  Frequency: ________
   Recommendation: ____________________________

### Positive Aspects / Strengths
1. ________________________________________
2. ________________________________________
3. ________________________________________
4. ________________________________________

### Recommendations & Action Plan

**Immediate Actions (0-30 days):**
1. ________________________________________
   Effort: _______   Impact: _______   Owner: _______

2. ________________________________________
   Effort: _______   Impact: _______   Owner: _______

**Short-term Actions (1-3 months):**
1. ________________________________________
   Effort: _______   Impact: _______   Owner: _______

2. ________________________________________
   Effort: _______   Impact: _______   Owner: _______

**Medium-term Actions (3-6 months):**
1. ________________________________________
   Effort: _______   Impact: _______   Owner: _______

2. ________________________________________
   Effort: _______   Impact: _______   Owner: _______

**Long-term Considerations (6+ months):**
1. ________________________________________
2. ________________________________________

### Metrics for Monitoring Improvement

**Performance Metrics to Track:**
- Average query response time: _______ ms (target: _______ ms)
- 95th percentile query response time: _______ ms (target: _______ ms)
- Transactions per second: _______ (target: _______)
- Connection pool utilization: _______% (target: <_____%)
- Cache hit ratio: _______% (target: >_____%)
- Index usage efficiency: _______% (target: >_____%)
- Disk I/O per second: _______ (target: <_______)
- Memory utilization: _______% (target: <_____%)
- Log growth rate: _______ MB/hour (target: <_______)
- Backup duration: _______ minutes (target: <_______)
- Restore time objective: _______ minutes (actual: _______)

**Data Quality Metrics:**
- Null percentage in required fields: _______% (target: <_____%)
- Duplicate key violations: _______/day (target: 0)
- Constraint violation errors: _______/day (target: 0)
- Data completeness score: _______% (target: >_____%)
- Referential integrity violations: _______/day (target: 0)

**Operations Metrics:**
- Backup success rate: _______% (target: 100%)
- Restore test frequency: _______ (target: monthly)
- Patch compliance: _______% (target: 100%)
- Monitoring coverage: _______% (target: 100%)
- Alert false positive rate: _______% (target: <_____%)
- Mean time to detect issues: _______ minutes (target: <_____)
- Mean time to resolve issues: _______ hours (target: <_____)

### Reviewer Comments & Observations
________________________________________________________________________
________________________________________________________________________
________________________________________________________________________
________________________________________________________________________

### References & Standards Consulted
☐ Database Vendor Documentation (official manuals and guides)
☐ SQL Standards (ANSI/ISO SQL:2016, etc.)
☐ Normalization Theory (Codd's Normal Forms)
☐ Data Modeling Principles (IDEF1X, IE, Barker's Notation)
☐ Performance Tuning Guides (vendor-specific)
☐ Security Standards (CIS Benchmarks, DISA STIGs)
☐ Backup & Recovery Best Practices
☐ High Availability & Disaster Recovery Guides
☐ Data Governance Frameworks (DAMA-DMBOK)
☐ Industry Regulations (GDPR, HIPAA, PCI-DSS, SOX)
☐ Books: "SQL Antipatterns", "Database Design for Mere Mortals", "The Art of PostgreSQL"
☐ Blogs: Use The Index, Luke!, Database Journal, Percona, MariaDB, etc.
☐ Other: __________________________________

### Sign-off
**Database Administrator**: ________________   Date: _________
**Data Architect**: ________________________   Date: _________
**Application Owner**: _____________________   Date: _________
**Security Officer**: ______________________   Date: _________
**Data Steward**: _________________________   Date: _________