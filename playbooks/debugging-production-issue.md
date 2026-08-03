# Debugging Production Issue Playbook

## Purpose
This playbook provides a systematic approach for diagnosing and resolving issues in production environments, minimizing downtime and impact on users.

## Scope
Applies to all production incidents across services, applications, and infrastructure components.

## Prerequisites
- Monitoring and alerting systems are configured and operational
- Runbooks and troubleshooting guides are accessible
- Team members have appropriate access to systems and logs
- Communication channels are established for incident response

## Roles & Responsibilities
- **Incident Commander**: Owns the overall incident response process and communication
- **Subject Matter Experts (SMEs)**: Provide deep knowledge of specific systems or components
- **On-Call Engineer**: First responder who initiates diagnosis
- **Communication Lead**: Manages internal and external stakeholder communication
- **SRE/Operations Team**: Manages infrastructure and provides environmental context
- **Development Team**: Provides application-specific knowledge and code changes
- **Database Administrator**: Assists with database-related issues
- **Network Engineer**: Helps with network connectivity and performance issues

## Procedure

### Phase 1: Initial Detection and Triage

#### Step 1: Alert Reception and Validation
- [ ] Receive alert from monitoring system
- [ ] Verify alert is legitimate (not a false positive)
- [ ] Check if similar alerts are firing (indicating broader issue)
- [ ] Assess severity and impact based on alert details
- [ ] Determine if this requires immediate escalation
- **Owner:** On-Call Engineer
- **Duration:** 2-5 minutes

#### Step 2: Initial Assessment and Notification
- [ ] Gather basic information: what service is affected, error messages, timeline
- [ ] Check dashboards for visible anomalies or trends
- [ ] Determine initial impact scope (users affected, functionality impacted)
- [ ] Notify Incident Commander and relevant stakeholders
- [ ] Create incident ticket or chat channel for tracking
- [ ] Assign initial severity level based on impact
- **Owner:** On-Call Engineer
- **Duration:** 5-10 minutes

#### Step 3: Preliminary Diagnosis
- [ ] Check recent deployments or changes (last 24-48 hours)
- [ ] Review change management system for planned activities
- [ ] Look for correlated alerts in other systems
- [ ] Form initial hypothesis about root cause
- [ ] Determine if immediate mitigation is possible (rollback, feature flag, etc.)
- **Owner:** Subject Matter Experts
- **Duration:** 10-15 minutes

### Phase 2: Investigation and Diagnosis

#### Step 4: Data Collection
[Collect relevant data based on symptoms]

##### Infrastructure Metrics
- [ ] CPU, memory, disk, and network utilization
- [ ] Load averages and process counts
- [ ] Disk I/O and latency metrics
- [ ] Network connection counts and error rates
- [ ] Container/pod restart rates (if applicable)
- [ ] Virtual machine or host-level metrics

##### Application Metrics
- [ ] Request rates, error rates, and latency (RED metrics)
- [ ] Queue depths and processing times
- [ ] Cache hit/miss ratios
- [ ] Database connection pool usage
- [ ] Thread pool and worker statistics
- [ ] Garbage collection and memory usage (for JVM/CLR/etc.)

##### Logs and Traces
- [ ] Application logs around the time of incident
- [ ] System logs (syslog, journalctl, event logs)
- [ ] Web server/access logs
- [ ] Database slow query logs
- [ ] Distributed tracing spans (if available)
- [ ] Audit logs for security-related incidents
- [ ] Debug logs if verbosity can be safely increased

##### Business Metrics
- [ ] User impact metrics (conversion rates, error rates)
- [ ] Revenue or transaction impact
- [ ] SLA/SLI compliance metrics
- [ ] Customer-facing error messages or feedback

#### Step 5: Hypothesis Testing
[Based on collected data, test potential root causes]

##### Common Issue Categories
- [ ] Resource exhaustion (CPU, memory, disk, network)
- [ ] Dependency failures (database, external services, APIs)
- [ ] Configuration issues (incorrect values, missing files)
- [ ] Code defects (recent deployments, logic errors)
- [ ] Infrastructure problems (hardware failures, network partitions)
- [ ] Scaling limits (connection limits, file descriptors, ports)
- [ ] Security issues (rate limiting, blocking, authentication failures)
- [ ] Data corruption or inconsistency
- [ ] Environmental differences (dev/stage/prod mismatch)

##### Investigation Techniques
- [ ] Correlate timing of events across systems
- [ ] Look for error patterns in logs (stack traces, exception types)
- [ ] Check for recent changes that coincide with issue onset
- [ ] Verify configuration matches expected values
- [ ] Test connectivity and responsiveness of dependencies
- [ ] Examine resource usage trends leading up to incident
- [ ] Check for cyclic or periodic patterns in metrics
- [ ] Compare current state to known good baselines

#### Step 6: Deep Dive Analysis
[If initial investigation doesn't reveal cause]

##### Advanced Techniques
- [ ] Enable debug logging or tracing temporarily (if safe)
- [ ] Use profiling tools to identify performance bottlenecks
- [ ] Analyze heap dumps or core dumps for memory issues
- [ ] Use network packet capture for communication issues
- [ ] Apply statistical analysis to identify anomalies
- [ ] Correlate with business events or user activities
- [ ] Check for race conditions or timing-dependent issues
- [ ] Examine system limits and uconfigurations
- [ ] Review garbage collection logs for JVM applications
- [ ] Check for integer overflow or wraparound conditions
- [ ] Validate assumptions about system behavior

### Phase 3: Resolution and Recovery

#### Step 7: Implement Fix or Mitigation
[Based on confirmed root cause]

##### Immediate Mitigations (if applicable)
- [ ] Roll back recent deployment
- [ ] Toggle feature flag to disable problematic functionality
- [ ] Scale up resources to relieve pressure
- [ ] Restart affected services or containers
- [ ] Failover to backup or secondary systems
- [ ] Implement rate limiting or load shedding
- [ ] Bypass problematic component via circuit breaker
- [ ] Apply temporary workaround or patch
- [ ] Redirect traffic to healthy instances

##### Permanent Fixes (follow standard change process)
- [ ] Develop and test fix in isolated environment
- [ ] Submit change through normal change management
- [ ] Schedule deployment during appropriate window
- [ ] Prepare rollback plan in case of issues
- [ ] Communicate planned fix to stakeholders

#### Step 8: Verify Resolution
- [ ] Confirm symptoms have disappeared
- [ ] Validate key metrics return to normal ranges
- [ ] Test critical user journeys and functionality
- [ ] Check for any regression or side effects
- [ ] Monitor for recurrence over observation period
- [ ] Validate dependent systems are functioning correctly
- [ ] Confirm no new alerts are firing

#### Step 9: Communication and Handoff
- [ ] Update stakeholders on resolution status
- [ ] Provide summary of actions taken and outcomes
- [ ] Confirm with business owners that service is restored
- [ ] Transition from incident response to normal operations
- [ ] Schedule post-mortem meeting
- [ ] Update incident ticket with resolution details

### Phase 4: Post-Incident Activities

#### Step 10: Post-Mortem Preparation
- [ ] Collect all relevant logs, metrics, and artifacts
- [ ] Preserve evidence for later analysis (if needed)
- [ ] Create timeline of events from detection to resolution
- [ ] Document all hypotheses tested and outcomes
- [ ] Gather metrics on impact (duration, users affected, etc.)
- [ ] Identify any contributing factors or aggravating circumstances
- [ ] Note what worked well in the response process
- [ ] Identify gaps or issues in the response process

#### Step 11: Root Cause Analysis
- [ ] Use 5 Whys or fishbone diagram to identify root cause
- [ ] Distinguish between triggering events and underlying conditions
- [ ] Identify systemic issues that enabled the incident
- [ ] Determine if this is an isolated incident or part of a pattern
- [ ] Evaluate effectiveness of monitoring and alerting
- [ ] Assess adequacy of runbooks and training
- [ ] Review communication effectiveness during incident
- [ ] Consider preventive measures for future similar incidents

#### Step 12: Action Items and Follow-up
- [ ] Create specific, actionable improvement items
- [ ] Assign owners and due dates for each action
- [ ] Prioritize actions based on impact and feasibility
- [ ] Schedule follow-up to verify completion
- [ ] Update runbooks, playbooks, or documentation as needed
- [ ] Improve monitoring, alerting, or logging based on lessons learned
- [ ] Consider architectural or process changes to prevent recurrence
- [ ] Share learnings with broader organization through tech talks or documentation

### Phase 5: Closure

#### Step 13: Incident Closure
- [ ] Confirm all action items are tracked and scheduled
- [ ] Ensure communication to stakeholders is complete
- [ ] Update incident ticket with final resolution and summary
- [ ] Close incident in tracking system
- [ ] Release any reserved resources or override conditions
- [ ] Return to normal monitoring and operations posture

## Decision Trees and Troubleshooting Guides

### Common Symptom-Based Investigation Paths

#### High Latency / Slow Response Times
```
High Latency
├── Check: Application metrics (response times, throughput)
│   ├── If high across all services → Likely infrastructure or network issue
│   │   ├── Check: Network latency, packet loss, bandwidth utilization
│   │   ├── Check: DNS resolution times
│   │   └── Check: Load balancer or reverse proxy performance
│   └── If specific service/system → Likely application or dependency issue
│       ├── Check: Database query performance and connection pools
│       ├── Check: External API call latency and reliability
│       ├── Check: Thread pool exhaustion or blocking operations
│       ├── Check: Garbage collection pauses (JVM/.NET)
│       ├── Check: Lock contention or deadlocks
│       └── Check: Inefficient algorithms or data structures
```

#### High Error Rates
```
High Error Rates
├── Check: Error types and messages in logs
│   ├── If authentication/authorization errors → Security or config issue
│   │   ├── Check: Identity provider availability
│   │   ├── Check: Certificate expiration or trust issues
│   │   └── Check: Role-based access control configurations
│   ├── If database connection errors → Connectivity or resource issue
│   │   ├── Check: Database availability and responsiveness
│   │   ├── Check: Connection pool exhaustion
│   │   └── Check: Network connectivity to database
│   ├── If timeout errors → Performance or dependency issue
│   │   ├── Check: Downstream service performance
│   │   ├── Check: Network latency or packet loss
│   │   └── Check: Circuit breaker or bulkhead configurations
│   ├── If validation errors → Data quality or input issue
│   │   ├── Check: Upstream data sources or producers
│   │   ├── Check: Input sanitization or transformation logic
│   │   └── Check: Schema or format mismatches
│   └── If 5xx server errors → Application or infrastructure issue
│       ├── Check: Application exceptions and stack traces
│       ├── Check: Resource exhaustion (memory, file descriptors)
│       └── Check: Container crashes or restarts
```

#### Service Unavailability / Downtime
```
Service Unavailability
├── Check: Infrastructure accessibility
│   ├── If cannot reach at all → Network or infrastructure issue
│   │   ├── Check: DNS resolution for service endpoints
│   │   ├── Check: Load balancer or ingress controller status
│   │   ├── Check: Firewall or security group rules
│   │   └── Check: Routing or VPC configuration
│   └── If can reach but service not responding → Application issue
│       ├── Check: Process status and resource utilization
│       │   ├── Check: Application crashed or exited
│       │   ├── Check: Out of memory or CPU starvation
│       │   └── Check: File descriptor or process limits
│       ├── Check: Logs for startup or initialization errors
│       │   ├── Check: Missing dependencies or configuration
│       │   ├── Check: Port binding conflicts
│       │   └── Check: Database connection failures on startup
│       └── Check: Health check or readiness probe failures
│           ├── Check: Application logic in health check endpoints
│           │   ├── Check: Dependency health checks failing
│           │   └── Check: Self-diagnostic logic errors
│           └── Check: Infrastructure health check misconfiguration
```

### Specific Issue Resolution Guides

#### Database Connection Issues
1. Verify database service is running and accessible
2. Check network connectivity (ping, traceroute, telnet to port)
3. Validate connection pool configuration (max connections, timeouts)
4. Look for connection leaks in application code
5. Examine database logs for connection refusals or errors
6. Check for long-running queries consuming connections
7. Verify authentication credentials and permissions
8. Assess database resource utilization (CPU, memory, disk I/O)
9. Check for replication lag or failover events
10. Consider increasing connection pool size or optimizing usage

#### Memory Leak Symptoms
1. Observe steadily increasing memory usage over time
2. Check for regular garbage collection that doesn't reclaim memory
3. Look for OutOfMemoryError in logs
4. Monitor heap usage patterns (sawtooth vs. steady climb)
5. Identify objects that are accumulating in memory
6. Common causes: static collections, unclosed resources, thread locals
7. Use heap dump analysis tools (MAT, VisualVM) to identify leaking objects
8. Check for caches without proper eviction policies
9. Verify proper closure of streams, connections, and file handles
10. Review use of ThreadLocal or similar context storage

#### Performance Degradation
1. Establish baseline performance metrics from known good period
2. Identify specific operations or endpoints that are slower
3. Check for recent code deployments or configuration changes
4. Look for increases in data volume or complexity
5. Monitor resource utilization for bottlenecks (CPU, memory, I/O, network)
6. Check for lock contention or thread starvation
7. Examine query execution plans for database performance
8. Review caching effectiveness and hit ratios
9. Look for retry storms or cascading failures
10. Consider impact of data growth on indexing or partitioning strategies

## Communication Templates

### Initial Alert Notification
**Subject:** [SEVERITY] INCIDENT: [Service Name] - [Brief Description] - [TIME] [TIMEZONE]

**Body:**
```
Incident Description: [Brief 1-2 sentence summary of what's happening]
Impact: [Number of users affected, percentage of traffic, revenue impact if known]
Severity: [SEVERITY LEVEL: SEV 1 (Critical) to SEV 4 (Minor)]
Detected: [TIME] [TIMEZONE] by [Monitoring System/Alert Name]
Current Status: [INVESTIGATING/MITIGATING/RESOLVING]
Assigned To: [On-Call Engineer Name]
Incident Channel: [Slack Channel/Conference Bridge Link]
Next Update: [TIME] or [When significant change occurs]

Known Symptoms:
- [Symptom 1]
- [Symptom 2]
- [Symptom 3]

Initial Actions Taken:
- [Action 1]
- [Action 2]

Please join [Channel] to assist with investigation.
```

### Status Update
**Subject:** [UPDATE] INCIDENT: [Service Name] - [STATUS] - [TIME] [TIMEZONE]

**Body:**
```
Time: [CURRENT TIME] [TIMEZONE]
Status: [UPDATE STATUS: e.g., STILL INVESTIGATING, IDENTIFIED ROOT CAUSE, APPLYING FIX]
Impact: [UPDATED IMPACT ASSESSMENT]
Root Cause (if known): [Brief description or "Still under investigation"]
Actions Taken:
- [Action 1 with timestamp]
- [Action 2 with timestamp]
- [Action 3 with timestamp]

Current Hypothesis:
- [What team believes is causing the issue]

Next Steps:
- [Step 1]
- [Step 2]
- [Step 3]

Estimated Time to Resolution: [If known]
Next Update: [TIME] or [When significant change occurs]
```

### Resolution Notification
**Subject:** [RESOLVED] INCIDENT: [Service Name] - [Brief Summary] - [DURATION]

**Body:**
```
Incident: [Service Name] experienced [brief description of problem]
Duration: [START TIME] to [END TIME] [TIMEZONE] ([TOTAL DURATION])
Impact: [Final impact assessment: users affected, error rates, etc.]
Root Cause: [Clear statement of what caused the issue]
Resolution: [How the issue was fixed or mitigated]
Timeline:
- [TIME] [TIMEZONE] - Alert triggered: [Description]
- [TIME] [TIMEZONE] - Initial assessment: [Description]
- [TIME] [TIMEZONE] - Hypothesis formed: [Description]
- [TIME] [TIMEZONE] - Action taken: [Description]
- [TIME] [TIMEZONE] - Service restored: [Description]
- [TIME] [TIMEZONE] - post-incident monitoring began

Lessons Learned (Initial):
- [Lesson 1]
- [Lesson 2]
- [Lesson 3]

Action Items Created:
- [Action item 1] - Owner: [Name] - Due: [Date]
- [Action item 2] - Owner: [Name] - Due: [Date]

Post-Mortem Scheduled: [Date] [Time] [TIMEZONE]
Full report will be shared within [timeframe].
```

## Escalation Criteria

### Escalate to Next Level When:
- [ ] Impact exceeds predefined thresholds (users affected, revenue impact, etc.)
- [ ] No root cause identified after [TIME] minutes of investigation
- [ ] Standard mitigation procedures have been attempted without success
- [ ] Incident threatens to violate SLA or compliance requirements
- [ ] Specialized expertise is required that is not currently available
- [ ] Multiple related incidents suggest broader systemic problem
- [ ] Customer or executive communication is required
- [ ] Regulatory reporting may be necessary
- [ ] Incident duration exceeds maximum allowable time for severity level

### Escalation Path:
1. On-Call Engineer → Team Lead → Department Director → VP/CTO → Executive Leadership
2. Functional escalation: Database → DBA Team Lead, Network → Network Engineering Lead, etc.
3. External partners/vendors as appropriate per contracts and SLAs
4. Regulatory or legal teams if compliance or data breach implications exist

## Tools and Resources

### Monitoring and Observability
- [List monitoring systems: Datadog, New Relic, Prometheus/Grafana, etc.]
- [Log aggregation: ELK Stack, Splunk, Sumo Logic, CloudWatch Logs]
- [Tracing: Jaeger, Zipkin, AWS X-Ray, Azure Monitor]
- [Infrastructure: Cloud provider consoles, VMware vCenter, etc.]

### Diagnostic Tools
- [System: top, htop, iostat, netstat, ss, lsof, ps, df, du]
- [Network: ping, traceroute, tcpdump, Wireshark, mtr, nslookup, dig]
- [Application: jstack, jmap, VisualVM, YourKit, dotTrace, perf]
- [Database: EXPLAIN ANALYZE, slow query logs, database-specific tools]
- [Language-specific: Python cProfile, Ruby stackprof, Go pprof, etc.]

### Communication and Collaboration
- [Incident tracking: Jira Service Desk, ServiceNow, PagerDuty]
- [Chat: Slack, Microsoft Teams, Discord]
- [Video/Voice: Zoom, Google Meet, Microsoft Teams]
- [Status pages: Statuspage.io, Atlassian Status, custom internal]
- [Conference bridges: Phone numbers, Zoom meeting IDs, etc.]

### Documentation and Knowledge Base
- [Runbooks and playbooks location]
- [Architecture diagrams and documentation]
- [Post-mortem repository]
- [Knowledge base: Confluence, Notion, internal wiki]
- [API documentation: Swagger/OpenAPI, Postman collections]
- [Troubleshooting guides and FAQs]

## References
- [Company Incident Response Policy]
- [Site Reliability Engineering (SRE) Books and Practices]
- [ITIL Incident Management Process]
- [NIST Incident Response Guide]
- [AWS Well-Architected Framework - Reliability Pillar]
- [Google SRE Workbook]
- [The Phoenix Project - DevOps Novel]
- [Accelerate: Building and Scaling High Performing Technology Organizations]
- [Chaos Engineering Principles]
- [BLAMLESS Postmortem Culture]
- [Observability Engineering (Charity Majors et al.)]
- [Site Reliability Workbook (Google SRE Team)]
- [Incident Metrics: MTTR, MTTD, MTBF]
- [Error Budgets and SLOs]