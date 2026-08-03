# Database Migration Template

## Migration Metadata
- **Migration ID**: [Timestamp or UUID]
- **Title**: [Brief description of what this migration accomplishes]
- **Author**: [Your Name/Team]
- **Created**: YYYY-MM-DD HH:MM:SS
- **Database**: [Database name/alias]
- **Type**: [Schema | Data | Reference | Rollback]
- **Dependencies**: [List of migration IDs this depends on]
- **Tags**: [feature-name, breaking-change, performance, etc.]

## Summary
[Brief 2-3 sentence description of what this migration does and why it's needed]

## Changes
### Schema Changes
#### Tables
**Created:**
- `table_name`: [Description of purpose]
  - Columns:
    - `id` SERIAL PRIMARY KEY
    - `column_name` DATA_TYPE CONSTRAINTS -- [Description]
    - `...`

**Modified:**
- `table_name`: 
  - Added columns: [list]
  - Dropped columns: [list]
  - Modified columns: [list with old → new definitions]
  - Added indexes: [list]
  - Dropped indexes: [list]
  - Added constraints: [list]
  - Dropped constraints: [list]

**Dropped:** [List of tables if any]

#### Views
**Created:**
- `view_name`: [Description]
  - Definition: [SQL or description]

**Modified:**
- `view_name`: [Description of changes]

**Dropped:** [List of views if any]

#### Functions/Procedures
**Created:**
- `function_name`([params]) RETURNS return_type
  - Language: SQL/PLpgSQL/etc.
  - Volatility: volatile/stable/immutable
  - Description: [What it does]

**Modified:** [List changes]

**Dropped:** [List if any]

### Data Changes
#### Data Inserts
- Table: `table_name`
  - Records: [Number] records inserted
  - Sample data: [Example rows or description]

#### Data Updates
- Table: `table_name`
  - Records affected: [Number or criteria]
  - Changes: [Description of what changed]

#### Data Deletes
- Table: `table_name`
  - Records affected: [Number or criteria]
  - Reason: [Why data is being removed]

## Rationale
[Why these changes are necessary]
- Problem being solved
- Business requirement or technical debt being addressed
- Alternatives considered and rejected

## Risks and Considerations
### Performance Impact
- Lock duration: [Estimated time locks will be held]
- Table size impact: [Current size and growth implications]
- Index maintenance: [Impact on write performance]
- Replication lag: [Expected impact on replicas]

### Data Integrity
- Constraints being added: [What new validation is added]
- Data loss risks: [What data might be affected and how]
- Migration reversibility: [How easy is it to rollback]
- Data validation needed: [Checks to perform after migration]

### Backward Compatibility
- Breaking changes: [What existing code might break]
- Deprecation period: [How long old behavior will be supported]
- Migration strategy: [How to handle existing deployments]

## Implementation
### Upgrade SQL
```sql
-- Begin transaction if your migration system supports it
BEGIN;

-- Your migration statements here
CREATE TABLE IF NOT EXISTS example_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index if needed
CREATE INDEX IF NOT EXISTS idx_example_table_name ON example_table(name);

COMMIT;
```

### Downgrade SQL (Rollback)
```sql
-- Begin transaction if your migration system supports it
BEGIN;

-- Your rollback statements here
DROP INDEX IF EXISTS idx_example_table_name;
DROP TABLE IF EXISTS example_table;

COMMIT;
```

### Execution Notes
- [Any special instructions for running this migration]
- [Maintenance window requirements if any]
- [Dependencies on other systems or services]
- [Validation steps to run after migration]

## Testing
### Local Testing
```bash
# Steps to test locally
# 1. Create test database
# 2. Apply migration
# 3. Verify schema changes
# 4. Verify data changes (if applicable)
# 5. Test rollback
```

### Test Cases
- [ ] Schema changes applied correctly
- [ ] Indexes created as expected
- [ ] Constraints enforced properly
- [ ] Data migrated accurately (if data migration)
- [ ] Rollback works correctly
- [ ] Performance impact measured
- [ ] Application compatibility verified

## Deployment
### Environment Checklist
- [ ] Backup verified (if production)
- [ ] Maintenance window scheduled (if required)
- [ ] Dependencies verified
- [ ] Rollback plan reviewed
- [ ] Monitoring alerts reviewed

### Rollback Plan
1. [Step 1: How to detect failure]
2. [Step 2: How to stop rollout]
3. [Step 3: How to execute rollback]
4. [Step 4: How to verify rollback]
5. [Step 5: How to notify stakeholders]

## Verification
### Post-Migration Checks
- [ ] Application health checks pass
- [ ] Database connectivity verified
- [ ] Critical queries tested
- [ ] Replication lag monitored
- [ ] Error rates checked
- [ ] Performance metrics reviewed

### Validation Queries
```sql
-- Check table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'your_table'
);

-- Check row count (for data migrations)
SELECT COUNT(*) FROM your_table;

-- Check constraints
SELECT conname, contype 
FROM pg_constraint 
WHERE conrelid = 'your_table'::regclass;

-- Check indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'your_table';
```

## Approvals
| Role | Name | Signature | Date |
|------|------|-----------|------|
| Database Administrator | [Name] | [Signature] | YYYY-MM-DD |
| Developer | [Name] | [Signature] | YYYY-MM-DD |
| Tech Lead | [Name] | [Signature] | YYYY-MM-DD |
| Release Manager | [Name] | [Signature] | YYYY-MM-DD |

---
*Generated by: [Your Name/Tool]*
*Migration System: [e.g., Flyway, Liquibase, Alembic, Django Migrations, etc.]*