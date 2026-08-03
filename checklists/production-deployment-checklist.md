# Production Deployment Checklist

## Pre-Deployment Preparation
### Code & Artifacts
- [ ] Code is merged into the main/release branch
- [ ] All required code reviews have been completed and approved
- [ ] Version number has been updated according to semantic versioning
- [ ] Build artifacts have been successfully generated and stored
- [ ] Docker images (if applicable) have been built and pushed to registry
- [ ] Database migration scripts are ready and tested
- [ ] Configuration files are environment-specific and validated
- [ ] Feature flags are set appropriately for the release
- [ ] Dependencies are locked and verified (package-lock.json, requirements.txt, etc.)
- [ ] Security scans have passed (SAST, DAST, dependency scanning)
- [ ] License compliance check has been completed

### Testing & Quality Gates
- [ ] All unit tests pass (>= 80% coverage threshold)
- [ ] Integration tests pass for critical user journeys
- [ ] Contract tests pass for API compatibility
- [ ] Performance tests meet baseline requirements
- [ ] Security scans show no critical or high vulnerabilities
- [ ] Smoke tests pass in staging environment
- [ ] Chaos engineering experiments have been run (if applicable)
- [ ] Accessibility tests pass (WCAG 2.1 AA)
- [ ] Cross-browser/device testing completed
- [ ] Load testing results are within acceptable thresholds
- [ ] User acceptance testing (UAT) sign-off obtained (if required)

### Environment & Infrastructure
- [ ] Target environment is provisioned and ready
- [ ] Infrastructure as Code (IaC) changes are applied and tested
- [ ] Database schema is backed up and ready for migration
- [ ] Cache layers are warmed or prepared for flush
- [ ] CDN cache invalidation rules are prepared
- [ ] Load balancer configurations are updated and tested
- [ ] DNS changes are prepared and TTL adjusted
- [ ] SSL/TLS certificates are valid and renewed if needed
- [ ] Monitoring dashboards are updated for new metrics
- [ ] Alerting rules are reviewed and adjusted if needed
- [ ] Log retention policies are verified
- [ ] Backup systems are operational and tested
- [ ] Disaster recovery site is synchronized (if applicable)

### Communication & Coordination
- [ ] Deployment schedule is communicated to stakeholders
- [ ] Maintenance window is booked and confirmed
- [ ] Release notes are prepared and reviewed
- [ ] Rollback communication plan is established
- [ ] Support team is briefed and on standby
- [ ] Customer-facing status page is ready for updates
- [ ] Executive stakeholders are notified (if high-impact release)
- [ ] Regulatory/compliance teams are informed (if applicable)
- [ ] Third-party service providers are notified (if integrations affected)
- [ ] War room/Virtual bridge is set up for the deployment
- [ ] Post-deployment validation meeting is scheduled

## Deployment Execution
### Pre-Deployment Checks
- [ ] Environment health checks pass (CPU, memory, disk, network)
- [ ] Dependencies and services are healthy (database, cache, queues, etc.)
- [ ] No conflicting deployments are in progress
- [ ] Rollback plan is reviewed and ready
- [ ] Deployment scripts/tools are tested and versioned
- [ ] Feature flags are set to desired initial state
- [ ] Circuit breakers are configured appropriately
- [ ] Monitoring and alerting systems are active
- [ ] Logging systems are ready to capture deployment events
- [ ] Backup of current state is completed and verified
- [ ] Maintenance mode is enabled (if applicable)

### Deployment Process
- [ ] Deployment follows the approved procedure/runbook
- [ ] Database migrations are executed and validated
- [ ] Application containers/services are restarted/updated
- [ ] Health checks pass after deployment
- [ ] Smoke tests are executed in production
- [ ] Synthetic transactions are run to validate critical paths
- [ ] Load balancer health checks show all instances healthy
- [ ] Service discovery is updated (if applicable)
- [ ] Caching layers are warmed or flushed as needed
- [ ] CDN edge caches are purged or updated
- [ ] Version information is updated in application/system
- [ ] Deployment metadata is logged (who, what, when, version)

### Post-Deployment Validation
- [ ] Application health endpoints return healthy status
- [ ] Key metrics are within normal ranges (latency, error rate, throughput)
- [ ] Business KPIs are tracked and showing expected behavior
- [ ] User-facing functionality is verified (smoke tests)
- [ ] API endpoints return correct responses (spot checks)
- [ ] Database connections are healthy and pooled properly
- [ ] External service integrations are functioning
- [ ] Error rates are at or below baseline
- [ ] Resource utilization is within expected ranges
- [ ] No new critical errors in logs
- [ ] Security monitoring shows no anomalies
- [ ] Performance metrics are within SLAs/SLOs
- [ ] Rollback readiness is confirmed (can still rollback if needed)

## Post-Deployment Activities
### Monitoring & Observation
- [ ] Enhanced monitoring is enabled for first 15-30 minutes
- [ ] Key dashboards are monitored for anomalies
- [ ] Alert silences are managed appropriately
- [ ] Log aggregation is reviewed for new patterns
- [ ] User session metrics are tracked
- [ ] Conversion/business metrics are observed
- [ ] Error tracking systems are monitored for new issues
- [ ] Performance profiling is conducted if needed
- [ ] Resource usage trends are observed
- [ ] Dependency health is verified

### Validation & Sign-off
- [ ] Stakeholder demo/walkthrough is conducted (if significant changes)
- [ ] Product owner validates functionality meets acceptance criteria
- [ ] Quality assurance team signs off on release
- [ ] Operations team confirms system stability
- [ ] Security team verifies no new vulnerabilities introduced
- [ ] Compliance team validates regulatory requirements (if applicable)
- [ ] Customer support team is briefed on any known issues
- [ ] Release notes are published to customers/users
- [ ] Post-deployment retrospective meeting is scheduled

### Cleanup & Documentation
- [ ] Temporary feature flags are removed or updated
- [ ] Deployment logs are archived and indexed
- [ ] Rollback artifacts are cleaned up (if successful deployment)
- [ ] Version control tags are created and pushed
- [ ] Changelog is updated with release details
- [ ] Documentation is updated if needed (API, user guides, etc.)
- [ ] Backup schedules are verified/resumed
- [ ] Normal monitoring alerts are restored
- [ ] Capacity utilization is reviewed for planning
- [ ] Lessons learned are documented and shared
- [ ] Deployment metrics are recorded (duration, success rate, etc.)

## Rollback Procedure (If Needed)
### Decision Criteria
- [ ] Critical functionality is broken
- [ ] Error rates exceed acceptable thresholds
- [ ] Performance degradation beyond SLA limits
- [ ] Data corruption or loss is detected
- [ ] Security vulnerabilities are introduced
- [ ] Health checks fail consistently
- [ ] User impact exceeds acceptable levels
- [ ] Business metrics show significant negative impact
- [ ] Monitoring shows cascading failures
- [ ] Manual intervention is required repeatedly

### Execution Steps
- [ ] Deployment is halted immediately
- [ ] War room/NOC is notified of rollback initiation
- [ ] Traffic is diverted away from affected instances
- [ ] Previous version is redeployed from known good artifacts
- [ ] Database rollback is executed (if migrations were applied)
- [ ] Caches are flushed or warmed as needed
- [ ] Configuration is reverted to previous state
- [ ] Feature flags are restored to previous values
- [ ] Health checks are validated after rollback
- [ ] Smoke tests are executed to confirm stability
- [ ] Metrics are monitored to verify recovery
- [ ] Stakeholders are notified of rollback completion
- [ ] Post-rollback validation is performed
- [ ] Root cause analysis is initiated
- [ ] Follow-up fix is planned and scheduled