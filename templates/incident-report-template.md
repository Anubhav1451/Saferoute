# Incident Report Template

## Incident Metadata
- **Incident ID**: [Unique identifier, e.g., INC-2023-00123]
- **Title**: [Brief, descriptive title of the incident]
- **Date/Time Detected**: YYYY-MM-DD HH:MM:SS [Timezone]
- **Date/Time Resolved**: YYYY-MM-DD HH:MM:SS [Timezone] (if resolved)
- **Duration**: [HH:MM:SS or "Ongoing"]
- **Reporter**: [Name/Team who detected/reported]
- **Incident Commander**: [Name/Role leading response]
- **Severity Level**: [P0/P1/P2/P3 or Critical/High/Medium/Low]
- **Impact Level**: [P0/P1/P2/P3 or Critical/High/Medium/Low]
- **Status**: [Detected | Investigating | Mitigating | Resolved | Postmortem | Closed]
- **Incident Type**: [Outage | Degraded Performance | Security Breach | Data Loss | Configuration Error | Dependency Failure | Capacity Exhaustion | Other: _______]
- **Affected Services**: [List of services/systems impacted]
- **User Impact**: [Description of user experience impact]
- **Business Impact**: [Revenue impact, SLA violations, regulatory concerns, etc.]

## Timeline of Events
[Chronological sequence of key events with timestamps]

| Time (UTC) | Event | Description | Owner |
|------------|-------|-------------|-------|
| HH:MM:SS | Incident Detected | [How it was detected: alert, user report, monitoring] | [Team/Person] |
| HH:MM:SS | Response Initiated | [Initial response actions] | [Team/Person] |
| HH:MM:SS | Preliminary Assessment | [Initial understanding of scope/cause] | [Team/Person] |
| HH:MM:SS | Mitigation Began | [First mitigation actions] | [Team/Person] |
| HH:MM:SS | Update Shared | [Status update communicated] | [Team/Person] |
| HH:MM:SS | Root Cause Identified | [Underlying cause determined] | [Team/Person] |
| HH:MM:SS | Fix Implemented | [Solution deployed/applied] | [Team/Person] |
| HH:MM:SS | Service Restored | [Confirmation of service recovery] | [Team/Person] |
| HH:MM:SS | Post-Incident Monitoring Began | [Enhanced monitoring started] | [Team/Person] |
| HH:MM:SS | Incident Closed | [Formal closure declared] | [Team/Person] |

*Note: All times should be in UTC or clearly specify timezone*

## Impact Assessment
### User Impact
- [ ] Total users affected: [Number or percentage]
- [ ] Geographic regions affected: [List regions]
- [ ] User actions blocked: [List specific actions users couldn't perform]
- [ ] Error messages seen by users: [What users encountered]
- [ ] Workarounds available: [What users could do instead]
- [ ] Support tickets received: [Number and categorization]
- [ ] Social media mentions: [Volume and sentiment]
- [ ] NPS/CSAT impact: [Measured change in satisfaction metrics]

### Business Impact
- [ ] Estimated revenue loss: [Amount and currency]
- [ ] SLA violations: [Which SLAs and by how much]
- [ ] Contract penalties: [Amount if applicable]
- [ ] Regulatory implications: [Any compliance concerns]
- [ ] Brand reputation impact: [Qualitative assessment]
- [ ] Internal productivity loss: [Estimated person-hours]
- [ ] Data loss or corruption: [Description if any]
- [ ] Long-term effects: [Anticipated ongoing impacts]

### Technical Impact
- [ ] Services completely down: [List services]
- [ ] Services degraded performance: [List services and degradation level]
- [ ] Data inconsistency: [Description if any]
- [ ] Lost transactions: [Estimated number and type]
- [ ] Failed jobs/batch processes: [List and impact]
- [ ] Cache warming required: [Services needing cache rebuild]
- [ ] Connection pool exhaustion: [Details if applicable]
- [ ] Resource leaks: [Memory, file descriptors, etc.]
- [ ] Security implications: [Any potential exposure]
- [ ] Dependency impact: [Effects on upstream/downstream services]

## Root Cause Analysis
### Immediate Cause
[What directly triggered the incident - e.g., "Null pointer exception in UserService.verifyPermission()"]

### Root Cause(s)
[The underlying reason why the immediate cause was able to happen - e.g., "Missing null check introduced during refactoring two weeks ago"]

### Contributing Factors
[Factors that made the incident more likely or severe - e.g., "Insufficient test coverage for the modified code path", "Alerting threshold too high for this failure mode", "No circuit breaker on external dependency"]

### Failure Modes
[What specific failure mechanisms were involved - e.g., "Unhandled exception", "Infinite loop", "Deadlock", "Resource exhaustion", "Configuration drift"]

## Response and Mitigation
### Detection
- [ ] How incident was detected: [Alert type, user report, synthetic transaction, etc.]
- [ ] Time to detect: [From onset to detection]
- [ ] Alert accuracy: [Was it a true positive, false positive, or noise?]
- [ ] Alert routing: [Did alert go to correct team/person?]
- [ ] Alert noise: [How many related alerts were generated?]
- [ ] Alert suppression: [Were any related alerts suppressed?]

### Initial Response
- [ ] Time to initial response: [From detection to first responder engagement]
- [ ] Initial actions taken: [What was done first]
- [ ] Escalation triggered: [When and how was escalation initiated]
- [ ] Incident commander appointed: [When and who]
- [ ] War room/virtual bridge established: [When and how]
- [ ] Stakeholder notification: [When were key stakeholders informed?]
- [ ] Public status page updated: [When and what was communicated]

### Investigation
- [ ] Investigation methods used: [Logs, tracing, monitoring, code review, etc.]
- [ ] Evidence collected: [What data was gathered]
- [ ] Investigation challenges: [What made diagnosis difficult]
- [ ] False leads investigated: [What dead ends were pursued]
- [ ] Key breakthrough: [What evidence led to root cause identification]

### Mitigation and Resolution
- [ ] Mitigation strategies attempted: [What was tried to reduce impact]
- [ ] Temporary workarounds implemented: [What stop-gap measures were put in place]
- [ ] Permanent fix implemented: [What change resolved the issue]
- [ ] Fix deployment method: [How was the fix deployed]
- [ ] Rollback considered/used: [Was rollback an option/back attempted or used]
- [ ] Verification of fix: [How was the fix confirmed to work]
- [ ] Reintroduction of traffic: [How was traffic restored]
- [ ] Monitoring during recovery: [What was watched during restoration]

### Communication
- [ ] Internal communication channels used: [Slack, email, phone, bridge line]
- [ ] Communication frequency: [How often were updates provided]
- [ ] Stakeholder Groups Notified: [Engineering, Product, Leadership, Support, Legal, PR, Customers]
- [ ] Status page updates: [Timing and content of updates]
- [ ] Customer notifications: [How and what was communicated to customers]
- [ ] Executive briefings: [When and what was shared with leadership]
- [ ] Post-incident summary: [When and how was final summary shared]
- [ ] Lessons learned shared: [How were insights distributed]

## Corrective and Preventive Actions (CAPA)
### Short-term Actions (Completed or In Progress)
| Action Item | Owner | Due Date | Status | Notes |
|-------------|-------|----------|--------|-------|
| [e.g., Add null check in UserService.verifyPermission()] | [Team/Person] | [Date] | [Done/In Progress] | [Any additional context] |
| [e.g., Deploy patch to all affected instances] | [Team/Person] | [Date] | [Done/In Progress] |  |
| [e.g., Increase alert sensitivity for similar metrics] | [Team/Person] | [Date] | [Done/In Progress] |  |
| [e.g., Add synthetic transaction for critical user path] | [Team/Person] | [Date] | [Done/In Progress] |  |

### Long-term Actions (Planned)
| Action Item | Owner | Target Date | Status | Notes |
|-------------|-------|-------------|--------|-------|
| [e.g., Refactor permission service to improve testability] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Implement circuit breaker for external auth service] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Improve alerting for similar failure modes] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Add chaos engineering experiment for this scenario] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Enhance on-call runbook for authentication services] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Add unit and integration tests for null pointer scenarios] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Review and update authentication service SLOs] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Implement feature flag for new permission logic] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Conduct security review of auth service changes] | [Team/Person] | [Date] | [Planned] |  |

### Process Improvements
| Improvement | Owner | Target Date | Status | Notes |
|-------------|-------|-------------|--------|-------|
| [e.g., Update definition of done to require security review] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Add performance test for permission verification under load] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Implement canary analysis for auth service deploys] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Increase test coverage for auth service to 90%] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Add dependency vulnerability scanning to CI pipeline] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Implement feature flagging framework for risky changes] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Improve runbook clarity and add decision trees] | [Team/Person] | [Date] | [Planned] |  |
| [e.g., Conduct tabletop exercise for similar incident scenarios] | [Team/Person] | [Date] | [Planned] |  |

## Lessons Learned
### What Went Well
- [Effective detection methods]
- [Quick initial response]
- [Good communication and coordination]
- [Effective mitigation strategies]
- [Successful fix implementation]
- [Clear documentation during incident]
- [Effective stakeholder management]
- [Good use of available tools and data]
- [Appropriate escalation]
- [Successful knowledge sharing]

### What Could Be Improved
- [Detection time too long]
- [Alert noise made diagnosis difficult]
- [Initial response actions not optimal]
- [Communication gaps or delays]
- [Mitigation efforts ineffective or caused additional issues]
- [Root cause took too long to identify]
- [Fix introduced new risks or issues]
- [Verification of fix insufficient]
- [Communication unclear or inconsistent]
- [Documentation lacking during incident]
- [Escalation delayed or misdirected]
- [Post-incident follow-up insufficient]

### System Weaknesses Revealed
- [Single point of failure]
- [Insufficient redundancy]
- [Inadequate monitoring/alerting]
- [Poor error handling]
- [Insufficient logging/tracing]
- [Lack of circuit breakers]
- [Inadequate retry logic]
- [Poor degradation handling]
- [Insufficient capacity planning]
- [Inadequate testing coverage]
- [Deployment process weaknesses]
- [Configuration management issues]
- [Dependency management problems]
- [Knowledge silos]
- [Runbook inaccuracies or gaps]
- [Tooling limitations]
- [Skill or knowledge gaps]
- [Process adherence issues]
- [Tool or technology limitations]

## Evidence and Artifacts
### Logs and Traces
- [ ] Application logs collected: [Time range, log levels, sources]
- [ ] System logs collected: [Time range, sources]
- [ ] Network logs collected: [Time range, sources]
- [ ] Security logs collected: [Time range, sources]
- [ ] Audit logs collected: [Time range, sources]
- [ ] Distributed tracing data: [Time range, services]
- [ ] Database query logs: [Time range, sources]
- [ ] Cache logs: [Time range, sources]
- [ ] Message queue logs: [Time range, sources]
- [ ] Load balancer logs: [Time range, sources]
- [ ] Proxy logs: [Time range, sources]
- [ ] Firewall logs: [Time range, sources]
- [ ] IDS/IPS logs: [Time range, sources]
- [ ] Antivirus/EDR logs: [Time range, sources]
- [ ] Cloud provider logs: [Time range, services]
- [ ] Custom application logs: [Time range, sources]

### Metrics and Monitoring Data
- [ ] Application metrics: [Time range, metrics]
- [ ] System metrics: [Time range, metrics]
- [ ] Network metrics: [Time range, metrics]
- [ ] Database metrics: [Time range, metrics]
- [ ] Cache metrics: [Time range, metrics]
- [ ] Business metrics: [Time range, metrics]
- [ ] Custom metrics: [Time range, metrics]
- [ ] SLO/SLI metrics: [Time range, metrics]
- [ ] Infrastructure metrics: [Time range, metrics]
- [ ] Container metrics: [Time range, metrics]
- [ ] Orchestrator metrics: [Time range, metrics]
- [ ] Load balancer metrics: [Time range, metrics]
- [ ] CDN metrics: [Time range, metrics]
- [ ] Third-party service metrics: [Time range, metrics]

### Configuration and Deployment Artifacts
- [ ] Configuration files: [Versions and sources]
- [ ] Deployment manifests: [Versions and sources]
- [ ] Infrastructure as Code: [Versions and sources]
- [ ] Database schema: [Version at time of incident]
- [ ] API specifications: [Version at time of incident]
- [ ] Feature flag states: [States at time of incident]
- [ ] Release versions: [Versions deployed at time of incident]
- [ ] Rollback artifacts: [If rollback was performed]
- [ ] Hotfix/patch files: [If hotfix was applied]
- [ ] Configuration change records: [If configuration change caused incident]
- [ ] Dependency versions: [Versions of key dependencies]
- [ ] Container images: [Images used at time of incident]
- [ ] Build artifacts: [If build issue contributed]
- [ ] Test results: [If test failure missed in CI]
- [ ] Security scan results: [If security issue]
- [ ] Performance test results: [If performance issue]
- [ ] Load test results: [If load testing missed issue]
- [ ] Chaos engineering results: [If relevant experiment]

### Communications and Documentation
- [ ] Chat logs: [Relevant Slack/Teams channels]
- [ ] Email correspondence: [Relevant email threads]
- [ ] Incident bridge recordings: [Audio/video if recorded]
- [ ] Status page snapshots: [Screenshots of status updates]
- [ ] Customer notifications: [Copies of customer communications]
- [ ] Executive briefings: [Materials shared with leadership]
- [ ] Runbooks consulted: [Which runbooks were used]
- [ ] Documentation referenced: [Which docs were consulted]
- [ ] Code reviewed: [Which code was examined]
- [ ] Design documents: [Which architectural docs referenced]
- [ ] Test cases: [Which tests were examined/re-run]
- [ ] Monitoring alerts: [Which alerts fired]
- [ ] Dashboard snapshots: [Screenshots of monitoring dashboards]
- [ ] Post-incident summary: [Final summary document]
- [ ] Lessons learned document: [Documented insights]
- [ ] Action item tracker: [Where CAPA items are tracked]
- [ ] Meeting notes: [From incident review meetings]
- [ ] Retrospective notes: [From blameless postmortem]

## Approvals and Sign-off
| Role | Name | Signature | Date |
|------|------|-----------|------|
| Incident Commander | [Name] | [Signature] | YYYY-MM-DD |
| Service Owner | [Name] | [Signature] | YYYY-MM-DD |
| Engineering Manager | [Name] | [Signature] | YYYY-MM-DD |
| Product Owner | [Name] | [Signature] | YYYY-MM-DD |
| SRE/Operations Lead | [Name] | [Signature] | YYYY-MM-DD |
| Security Representative (if applicable) | [Name] | [Signature] | YYYY-MM-DD |
| Customer Support Lead (if user-impacting) | [Name] | [Signature] | YYYY-MM-DD |
| Communications/PR Lead (if public-facing) | [Name] | [Signature] | YYYY-MM-DD |

---
*Report Completed:* YYYY-MM-DD HH:MM:SS
*Next Review Due:* YYYY-MM-DD (typically 30-90 days after incident for effectiveness check)
*Related Incidents:* [Links to similar past incidents]
*References:* [Links to relevant runbooks, architecture docs, code commits]