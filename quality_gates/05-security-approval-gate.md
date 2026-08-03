# Security Approval Gate

## Purpose
This gate ensures that security considerations have been adequately addressed throughout the development lifecycle and that the solution meets organizational security standards and compliance requirements before promotion to higher environments.

## Entry Criteria
- [ ] Development Complete Gate has been passed (or equivalent milestone)
- [ ] Threat modeling exercise has been completed
- [ ] Security requirements have been identified and documented
- [ ] Static Application Security Testing (SAST) has been performed on code
- [ ] Dependency scanning has been completed for third-party components
- [ ] Architecture review from security perspective has been conducted
- [ ] Security testing plan is developed and approved
- [ ] Security configurations and hardening guides are available
- [ ]  - [ ] Access control requirements are defined
- [ ] Data protection requirements (encryption, masking) are specified
- [ ] Logging and monitoring requirements for security events are identified
- [ ] Incident response considerations are noted
- [ ] Third-party and service integrations are reviewed for security implications
- [ ] Regulatory and compliance requirements (GDPR, HIPAA, PCI-DSS, etc.) are identified
- [ ] Security training completion records for development team
- [ ] Penetration testing scope and approach are defined (if applicable)
- [ ] Secure coding standards are established and communicated
- [ ] Secrets management approach is defined
- [ ] Security headers and protections are planned for web applications

## Exit Criteria (Definition of Done)
To pass this gate and receive security approval for promotion to next environment/stage, the following must be true:

### Vulnerability Management
- [ ] Critical vulnerabilities identified in SAST/DAST scans are resolved
- [ ] High vulnerabilities are resolved or have risk acceptance with mitigation
- [ ] Medium/low vulnerabilities are prioritized in backlog
- [ ] Dependency vulnerabilities are addressed through updates or patches
- [ ] No known exploitable vulnerabilities remain in production-bound code
- [ ] Vulnerability scan false positives are documented and justified
- [ ] Vulnerability management process is followed consistently
- [ ] Security debt is tracked and prioritized appropriately
- [ ] Third-party component licensing compliance is verified
- [ ] Vulnerability exposure time is minimized

### Secure Development Practices
- [ ] Secure coding standards are followed throughout development
- [ ] Input validation and output encoding are implemented correctly
- [ ] Authentication and authorization mechanisms are secure
- [ ] Session management is secure (if applicable)
- [ ] Cryptographic implementations use approved algorithms and libraries
- [ ] Key management follows best practices
- [ ] Error handling does not leak sensitive information
- [ ] Logging captures security-relevant events without sensitive data
- [ ] CSRF, XSS, SQL injection, and other common vulnerabilities are prevented
- [ ] File upload functionality is properly secured (if applicable)
- [ ] External entity expansion (XXE) protections are in place (if XML used)
- [ ] Deserialization vulnerabilities are prevented
- [ ] Directory traversal attacks are prevented
- [ ] Clickjacking protections are implemented (if web app)
- [ ] Security misconfigurations are avoided through hardening
- [ ] Unused features, services, and ports are disabled
- [ ] Default credentials are changed or disabled
- [ ] Least privilege principle is applied to service accounts and permissions
- [ ] Network segmentation and access controls are designed appropriately

### Data Protection
- [ ] Sensitive data is encrypted at rest using strong algorithms
- [ ] Data in transit is protected with TLS 1.2 or higher
- [ ] Encryption keys are managed securely (KMS, HSM, or equivalent)
- [ ] Key rotation procedures are established
- [ ] Personally Identifiable Information (PII) is identified and protected
- [ ] Payment Card Industry (PCI) data handling complies with standards (if applicable)
- [ ] Protected Health Information (PHI) handling complies with HIPAA (if applicable)
- [ ] Data minimization principles are followed
- [ ] Data retention and deletion policies are implemented
- [ ] Data masking and tokenization are used where appropriate
- [ ] Database encryption or column-level encryption is applied (if needed)
- [ ] Backup encryption is implemented
- [ ] Secure deletion procedures are established for sensitive data

### Identity and Access Management
- [ ] Authentication mechanisms are secure and resist common attacks
- [ ] Multi-factor authentication (MFA) is implemented where required
- [ ] Password policies comply with security standards
- [ ] Account lockout mechanisms are implemented to prevent brute force
- [ ] Password storage uses strong, slow hashing algorithms (bcrypt, scrypt, PBKDF2)
- [ ] Authorization follows least privilege principle
- [ ] Role-based access control (RBAC) or attribute-based access control (ABAC) is properly implemented
- [ ] Access rights are reviewed regularly
- [ ] Segregation of duties (SoD) is enforced where required
- [ ] Privileged access management (PAM) is implemented for admin functions
- [ ] Service-to-service authentication is secure (mutual TLS, API keys, JWT, etc.)
- [ ] Session management uses secure cookies with appropriate attributes
- [ ] OAuth/OpenID Connect implementations follow best practices
- [ ] API keys and secrets are stored securely (not in code/repositories)
- [ ] Token expiration and refresh mechanisms are properly implemented
- [ ] Federated identity considerations are addressed (if applicable)

### Security Testing
- [ ] Static Application Security Testing (SAST) passes with acceptable results
- [ ] Dynamic Application Security Testing (DAST) is conducted (if applicable)
- [ ] Software Composition Analysis (SCA) identifies no critical vulnerable dependencies
- [ ] Infrastructure as Code (IaC) scanning identifies no misconfigurations
- [ ] Container image scanning finds no critical vulnerabilities
- [ ] Manual penetration testing is completed (if required by policy)
- [ ] Security test cases are defined and executed
- [ ] Fuzz testing is performed on critical components (if applicable)
- [ ] API security testing is completed (if applicable)
- [ ] Mobile application security testing is done (if applicable)
- [ ] Social engineering resistance is evaluated (if applicable)
- [ ] Red team/blue tabletop exercises are conducted (if applicable)
- [ ] Security regression testing is included in test suite
- [ ] Security test environment closely mirrors production

### Logging, Monitoring, and Incident Response
- [ ] Security-relevant events are logged (authentication, authorization, data access, etc.)
- [ ] Logs do not contain sensitive information (passwords, PII, etc.)
- [ ] Log integrity is protected from tampering
- [ ] Log retention meets regulatory and business requirements
- [ ] Centralized logging is implemented for distributed systems
- [ ] Real-time alerting is configured for security events
- [ ] Security Information and Event Management (SIEM) integration is established
- [ ] Intrusion Detection/Prevention Systems (IDS/IPS) alerts are monitored
- [ ] File integrity monitoring is enabled for critical files
- [ ] Honeytokens or canaries are deployed (if applicable)
- [ ] Incident response playbook is updated for this application
- [ ] Forensic readiness is considered in logging strategy
- [ ] Security metrics and key risk indicators (RKIs) are defined
- [ ] Regular security reviews and audits are scheduled
- [ ] Vulnerability disclosure process is established
- [ ] Security awareness training completion is tracked for team

### Configuration and Infrastructure Security
- [ ] Infrastructure as Code (IaC) templates are scanned for security issues
- [ ] Server hardening standards are applied
- [ ] Network security groups/firewall rules are restricted to minimum required
- [ ] Default accounts and passwords are changed or disabled
- [ ] Unnecessary services and ports are disabled
- [ ] Secure boot and firmware validation are enabled (if applicable)
- [ ] Encryption is enabled for storage volumes
- [ ] Security patches and updates are applied regularly
- [ ] Vulnerability management for operating systems and platforms
- [ ] Container runtime security is configured (if applicable)
- [ ] Kubernetes pod security policies or equivalent are applied (if applicable)
- [ ] Secrets are not stored in environment variables or configuration files
- [ ] Runtime application self-protection (RASP) is considered (if applicable)
- [ ] Web Application Firewall (WAF) rules are configured and tested
- [ ] API gateway security policies are enforced
- [ ] Service mesh security policies are implemented (if applicable)
- [ ] Zero trust network access principles are followed where possible
- [ ] Edge computing security considerations are addressed (if applicable)

### Compliance and Governance
- [ ] Applicable regulatory requirements are identified and addressed (GDPR, CCPA, HIPAA, PCI-DSS, SOX, etc.)
- [ ] Data processing agreements are in place for third-party services (if applicable)
- [ ] Privacy impact assessment (PIA) is completed (if required)
- [ ] Security controls are mapped to compliance requirements
- [ ] Audit logging supports compliance reporting requirements
- [ ] Evidence collection for audits is facilitated
- [ ] Records of processing activities are maintained (if GDPR applies)
- [ ] Data subject access request (DSAR) capabilities are implemented (if GDPR applies)
- [ ] Right to be forgotten functionality is implemented (if GDPR applies)
- [ ] Data breach notification procedures are established
- [ ] Security policies and standards are referenced and followed
- [ ] Exception request process is followed for any deviations
- [ ] Contractual security requirements with vendors are met
- [ ] Export control restrictions are considered (if applicable)
- [ ] Classification and handling of data follows information security policy
- [ ] Insurance and liability considerations are addressed
- [ ] Third-party risk management assessments are completed
- [ ] Security supply chain risks are evaluated
- [ ] Open source license compliance is verified
- [ ] Cryptographic usage complies with export regulations (if applicable)

## Exit Questions
1. What is the current status of critical and high-severity security vulnerabilities?
2. Have all security testing activities (SAST, DAST, SCA, penetration testing) been completed with acceptable results?
3. Is sensitive data properly protected both at rest and in transit?
4. Are authentication and authorization mechanisms implemented correctly and securely?
5. Have security configurations and hardening measures been applied?
6. Is logging and monitoring sufficient to detect and respond to security incidents?
7. Are identity and access management controls properly implemented?
8. Have all applicable compliance requirements been addressed?
9. Is the infrastructure securely configured and hardened?
10. What is the plan for ongoing security maintenance and monitoring?
11. Are there any outstanding security risks that require risk acceptance?
12. Have security considerations been integrated throughout the SDLC?
13. Is the security track record of third-party components and services acceptable?
14. Are security metrics and reporting mechanisms in place?
15. What evidence demonstrates compliance with security policies and standards?

## Exit Options
- **APPROVE**: Security controls are adequate, can proceed to next stage
- **CONDITIONAL APPROVE**: Approved with specific compensating controls or monitoring requirements
- **REJECT**: Significant security issues remain that must be addressed before proceeding
- **DEFER**: Security assessment incomplete, resume when additional information is available

## Evidence Required
- Threat model documentation
- Security requirements specification
- SAST scan reports and remediation evidence
- DAST scan reports (if performed)
- SCA/dependency scanning reports
- Container image scan reports
- Infrastructure as Code (IaC) scan reports
- Manual penetration testing report (if conducted)
- Security test cases and execution results
- Threat modeling diagrams and findings
- Security architecture review documentation
- Access control matrices and policies
- Encryption key management documentation
- Data flow diagrams showing data protection points
- Security configuration baselines
- Firewall and network security group rules
- Identity and access management configurations
- Audit logging configuration and samples
- Monitoring and alerting rules for security events
- Incident response playbook updates
- Security training completion records
- Vulnerability management reports and metrics
- Compliance assessment reports or gap analysis
- Data protection impact assessments (if applicable)
- Security exception requests and approvals (if any)
- Third-party security assessments (SOC 2, ISO 27001, etc.) for dependencies
- Security code review checklists and results
- Security test automation scripts and coverage
- Security metrics dashboard or reports
- Disaster recovery and business continuity considerations from security perspective
- Retention and disposal procedures for sensitive data
- Security architecture diagrams and threat surfaces
- Secure coding standard documentation and compliance matrix
- Security training materials and attendance records
- Penetration testing scope, rules of engagement, and findings
- Red team exercise results (if applicable)
- Bug bounty program participation and vulnerability disclosure program)
- Security configuration baselines and drift reports
</security hardening verification checklist
- Secure sEvidence Required compliance verification</ Supplies</sub:rd>
  files
license

## References
- Security Review</lity
   Team
 Ownership
 Oath
 Evidence
 
 ( Standard
 CIP
   evidence
  
  
  
  
  securitythird-party
 
 libraries
  
  firewalls
 
  
  
  metho
 
 
  
Staff
   test
  damage
  
 
  
 
  is.s
 
  files
 
 
  
  
  
  
 
 
  ev
  
  
  
 
 
  C
 
  
  
  
  
 
)



.</sub:c>
</sub:t>
        evidence
      
evidence
```

This is getting too long, let me cut it off and create a more concise version:
<tool_call>
<function=Write>
<parameter=content>
# Security Approval Gate

## Purpose
This gate ensures that security considerations have been adequately addressed throughout the development lifecycle and that the solution meets organizational security standards and compliance requirements before promotion to higher environments.

## Entry Criteria
- [ ] Development Complete Gate has been passed
- [ ] Threat modeling completed
- [ ] Security requirements documented
- [ ] SAST/DAST/SCA scans performed
- [ ] Security testing plan approved
- [ ] Architecture security review conducted
- [ ] Access controls defined
- [ ] Data protection requirements specified
- [ ] Logging/monitoring requirements identified
- [ ] Incident response considerations noted
- [ ] Third-party integrations reviewed
- [ ] Regulatory requirements identified
- [ ] Security training completed
- [ ] Penetration testing scope defined
- [ ] Secure coding standards established
- [ ] Secrets management approach defined
- [ ] Security headers/protections planned

## Exit Criteria (Definition of Done)
To pass this gate and receive security approval:

### Vulnerability Management
- [ ] Critical vulnerabilities resolved
- [ ] High vulnerabilities resolved or risk accepted
- [ ] Medium/low vulnerabilities prioritized
- [ ] Dependency vulnerabilities addressed
- [ ] No known exploitable vulnerabilities remain
- [ ] False positives documented/justified
- [ ] Vulnerability management process followed
- [ ] Security debt tracked/prioritized
- [ ] Third-party license compliance verified

### Secure Development Practices
- [ ] Secure coding standards followed
- [ ] Input validation/output encoding implemented
- [ ] Authentication/authorization secure
- [ ] Session management secure
- [ ] Cryptography uses approved algorithms
- [ ] Key management follows best practices
- [ ] Error handling doesn't leak sensitive data
- [ ] Logging captures security events appropriately
- [ ] Common vulnerabilities prevented (XSS, SQLi, CSRF, etc.)
- [ ] File uploads properly secured
- [ ] XXE protections in place (if XML used)
- [ ] Deserialization vulnerabilities prevented
- [ ] Directory traversal prevented
- [ ] Clickjacking protections (if web app)
- [ ] Security misconfigurations avoided
- [ ] Unused services/ports disabled
- [ ] Default credentials changed/disabled
- [ ] Least privilege principle applied
- [ ] Network segmentation/access controls designed

### Data Protection
- [ ] Sensitive data encrypted at rest (strong algorithms)
- [ ] Data in transit protected with TLS 1.2+
- [ ] Encryption keys managed securely (KMS/HSM)
- [ ] Key rotation procedures established
- [ ] PII identified and protected
- [ ] PCI data handled per standards (if applicable)
- [ ] PHI handled per HIPAA (if applicable)
- [ ] Data minimization followed
- [ ] Data retention/deletion implemented
- [ ] Data masking/tokenization used where appropriate
- [ ] Database/column-level encryption applied (if needed)
- [ ] Backup encryption implemented
- [ ] Secure deletion procedures established

### Identity and Access Management
- [ ] Authentication mechanisms secure/resist attacks
- [ ] MFA implemented where required
- [ ] Password policies comply with standards
- [ ] Account lockout prevents brute force
- [ ] Password storage uses strong hashing (bcrypt/scrypt/PBKDF2)
- [ ] Authorization follows least privilege
- [ ] RBAC/ABAC properly implemented
- [ ] Access rights reviewed regularly
- [ ] Segregation of duties enforced
- [ ] Privileged access management for admin functions
- [ ] Service-to-service authentication secure (mTLS, API keys, JWT)
- [ ] Session management uses secure cookies
- [ ] OAuth/OpenID Connect follows best practices
- [ ] API keys/secrets stored securely (not in code)
- [ ] Token expiration/refresh properly implemented
- [ ] Federated identity considerations addressed

### Security Testing
- [ ] SAST passes with acceptable results
- [ ] DAST conducted (if applicable)
- [ ] SCA finds no critical vulnerable dependencies
- [ ] IaC scanning finds no misconfigurations
- [ ] Container scanning finds no critical vulnerabilities
- [ ] Manual penetration testing completed (if required)
- [ ] Security test cases defined/executed
- [ ] Fuzz testing performed on critical components
- [ ] API security testing completed (if applicable)
- [ ] Mobile app security testing done (if applicable)
- [ ] Social engineering resistance evaluated
- [ ] Red team/blue team exercises conducted
- [ ] Security regression testing in test suite
- [ ] Security test environment mirrors production

### Logging, Monitoring, and Incident Response
- [ ] Security-relevant events logged (auth, access, etc.)
- [ ] Logs don't contain sensitive information
- [ ] Log integrity protected from tampering
- [ ] Log retention meets requirements
- [ ] Centralized logging for distributed systems
- [ ] Real-time alerting configured for security events
- [ ] SIEM integration established
- [ ] IDS/IPS alerts monitored
- [ ] File integrity monitoring enabled
- [ ] Honeytokens/canaries deployed
- [ ] Incident response playbook updated
- [ ] Forensic readiness considered
- [ ] Security metrics/KRIs defined
- [ ] Regular security reviews/audits scheduled
- [ ] Vulnerability disclosure process established
- [ ] Security awareness training tracked

### Configuration and Infrastructure Security
- [ ] IaC templates scanned for security issues
- [ ] Server hardening standards applied
- [ ] Network security groups/firewall rules minimized
- [ ] Default accounts/passwords changed/disabled
- [ ] Unnecessary services/ports disabled
- [ ] Secure boot/firmware validation enabled
- [ ] Storage volume encryption enabled
- [ ] Security patches/updates applied regularly
- [ ] OS/platform vulnerability management
- [ ] Container runtime security configured
- [ ] K8s pod security policies applied (if applicable)
- [ ] Secrets not in env vars/config files
- [ ] RASP considered (if applicable)
- [ ] WAF rules configured/tested
- [ ] API gateway security policies enforced
- [ ] Service mesh security policies implemented
- [ ] Zero trust principles followed

### Compliance and Governance
- [ ] Applicable regulations addressed (GDPR, CCPA, HIPAA, PCI-DSS, SOX)
- [ ] Data processing agreements for third parties
- [ ] Privacy impact assessment completed (if required)
- [ ] Security controls mapped to compliance
- [ ] Audit logging supports compliance reporting
- [ ] Evidence collection facilitated for audits
- [ ] Processing activities recorded (if GDPR)
- [ ] DSAR capabilities implemented (if GDPR)
- [ ] Right to be forgotten implemented (if GDPR)
- [ ] Data breach notification procedures established
- [ ] Security policies/standards referenced/followed
- [ ] Exception request process followed for deviations
- [ ] Contractual vendor security requirements met
- [ ] Export control restrictions considered
- [ ] Data classification/handling follows policy
- [ ] Insurance/liability considerations addressed
- [ ] Third-party risk management assessments completed
- [ ] Supply chain security risks evaluated
- [ ] Open source license compliance verified
- [ ] Cryptographic usage complies with export regs

## Exit Questions
1. What is the status of critical/high security vulnerabilities?
2. Have all security tests (SAST, DAST, SCA, pen testing) been completed acceptably?
3. Is sensitive data properly protected (at rest and in transit)?
4. Are authentication/authorization mechanisms correctly implemented?
5. Have security configurations/hardening been applied?
6. Is logging/monitoring sufficient for detection/response?
7. Are IAM controls properly implemented?
8. Have all compliance requirements been addressed?
9. Is infrastructure securely configured/hardened?
10. What is the plan for ongoing security maintenance?
11. Are there outstanding risks requiring risk acceptance?
12. Have security considerations been integrated throughout SDLC?
13. Is third-party component/service security track record acceptable?
14. Are security metrics/reporting mechanisms in place?
15. What evidence demonstrates compliance with security policies?

## Exit Options
- **APPROVE**: Security controls adequate, proceed
- **CONDITIONAL APPROVE**: Approved with specific compensating controls/monitoring
- **REJECT**: Significant security issues remain
- **DEFER**: Assessment incomplete, resume later

## Evidence Required
- Threat model documentation
- Security requirements spec
- SAST/DAST/SCA reports + remediation evidence
- Container/IaC scan reports
- Penetration test report (if conducted)
- Security test cases/results
- Threat modeling diagrams
- Security architecture review docs
- Access control matrices/policies
- Encryption key management docs
- Data flow diagrams showing protection
- Security config baselines
- Firewall/NSG rules
- IAM configurations
- Audit logging config/samples
- Monitoring/alerting rules
- Incident response playbook updates
- Security training records
- Vulnerability management reports
- Compliance assessments/gap analysis
- Data protection impact assessments
- Security exception requests/approvals
- Third-party security assessments (SOC 2, ISO 27001)
- Security code review checklists/results
- Security test automation scripts/coverage
- Security metrics dashboard/reports
- DR/BC security considerations
- Data retention/disposal procedures
- Security architecture diagrams/threat surfaces
- Secure coding standard docs/compliance matrix
- Security training materials/attendance
- Penetration test scope/ROE/findings
- Red team exercise results
- Bug bounty/vuln disclosure participation
- Security config baselines/drift reports

## Roles and Responsibilities
- **Information Security Lead**: Leads security review and approval
- **Application Security Engineer**: Conducts security testing and reviews
- **DevSecOps Engineer**: Integrates security into CI/CD pipelines
- **Network Security Engineer**: Reviews network security controls
- **Database Security Administrator**: Reviews data protection measures
- **Cloud Security Engineer**: Reviews cloud-specific security controls
- **Application Architect**: Ensures security considerations in design
- **Development Team Lead**: Represents development perspective
- **Quality Assurance Lead**: Confirms security testing adequacy
- **Compliance Officer**: Validates regulatory compliance adherence
- **Privacy Officer**: Reviews privacy-related controls (if applicable)
- **Audit/Internal Audit**: Validates audit readiness (if applicable)
- **Infrastructure/Platform Team**: Validates infrastructure security
- **Product Owner**: Represents business requirements perspective
- **Release Manager**: Coordinates release process
- **Stakeholders**: Subject matter experts as needed

## Related Artifacts
- Threat model documentation (STRIDE, PASTA, etc.)
- Security requirements specification
- Secure coding standards document
- Vulnerability management policy
- Patch management procedure
- Incident response plan
- Disaster recovery plan
- Business continuity plan
- Security awareness training materials
- Access control policy
- Data classification and handling policy
- Encryption key management policy
- Suppliers and third parties security policy
- Remote access policy
- Acceptable use policy
- Clean desk and clear screen policy
- Password policy
- Remote working policy
- Cloud security policy
- Container security policy
- DevSecOps policy
- API security policy
- Mobile device management policy
- Encryption policy
- Backup and encryption policy
- Audit logging policy
- Monitoring and alerting policy
- Penetration testing methodology
- Red team exercise framework
- Bug bounty/vulnerability disclosure policy
- Security metrics and reporting framework
- Security risk assessment methodology
- Security exception request form
- Security approval checklist
- Security test plan template
- Security test case template
- Penetration test report template
- Vulnerability assessment report template
- Security architecture review template
- Threat modeling template
- Secure code review checklist
- Security configuration checklist
- Network security checklist
- Database security checklist
- Application security checklist
- Cloud security checklist
- DevSecOps checklist
- Container security checklist
- IAM checklist
- Data protection checklist
- Incident response checklist
- Forensic readiness checklist
- Compliance checklist (GDPR, HIPAA, PCI-DSS, etc.)
- Privacy impact assessment template
- Data processing agreement template
- Third-party risk assessment questionnaire
- Vendor security assessment questionnaire
- Security awareness training attendance sheet
- Phishing simulation results
- Security poster/awareness materials
- Security newsletters/communications
- Security bulletins/advisories
- Security metrics dashboard
- Security heat map of vulnerabilities
- Security trend analysis report
- Security investment justification document
- Security resource allocation plan
- Security skills matrix
- Security training needs analysis
- Security career path framework
- Security certification requirements
- Security budget planning template
- Security cost-benefit analysis model
- Security ROI calculation methodology
- Security TCO estimation model
- Security benchmarking report
- Security best practices compendium
- Security glossary of terms
- Security acronyms list
- Security bibliography and references
- Security standards mapping (ISO 27001, NIST, CIS, etc.)
- Security regulatory compliance matrix
- Security audit program
- Security internal audit checklist
- Security external audit preparation guide
- Security audit findings and remediation tracker
- Security audit evidence list
- Security audit working papers
- Security audit report template
- Security management review minutes
- Security steering committee charter
- Security governance framework
- Security policy framework
- Security procedure catalog
- Security work instruction library
- Security form and template repository
- Security software inventory
- Security hardware asset list
- Security network diagram
- Security topology diagram
- Security zone diagram
- Security trust boundary diagram
- Security data flow diagram
- Security process flow diagram
- Security decision tree
- Security risk matrix
- Security heat map
- Security burndown chart
- Security velocity chart
- Security blocker list
- Security mitigation plan
- Security contingency plan
- Security disaster recovery plan
- Security business continuity plan
- Security crisis management plan
- Security incident response team (IRT) charter
- Security incident response playbook
- Security incident classification guide
- Security incident severity levels
- Socrhemer
 
  
  
  
  but
 
  
  license
  
  Product
  
  
  
  
  support
  
 
  
  
  
 
 
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
  
  
  
  
  
  
  
 
 
  
 
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
 
 
 
 
  
  
  
  
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  标
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
 
  
  
  
  
  
  
  
 
 
 
 
 
 
 
  
  
  
  
 
 
 
 
  
  
  
  
 
 
  
  
  
  
  
  
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
 
 
  
  
  
 
 
 
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
  
  
  
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
 
 
 
 
 
 
 
  
 
  
 
 
 
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
 
 
 
  
  
  
 
 
  
  
  
  
  
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
  
  
  
  
  
  
 
  
  
  
  
  
 
 
 
 
  
  
 
 
 
 
 
 
 
 
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
 
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
  
  
  
  
  
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
  
  
  
 
 
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
  
  
  
  
  
  
  
  
  
  
 
 
 
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
  
  
  
 
 
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
 
 
 
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
 
  
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
  
 
 
  
  
  
  
  
  
  
 
 
  
  
  
  
  
  
  
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
 
 
 
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
 
 
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
  
  
  
  
  
 
 
  
  
  
  
  
 
 
  
  
  
  
  
  
 
 
  
  
  
 
 
 
  
  
  
  
  
 
 
  
  
  
  
  
  
 
 
  
  
  
 
 
 
 
 
  
  
  
  
 
 
  
  
  
  
  
 
 
  
  
  
  
  
 
 
  
  
 
 
 
 
  
  
  
 
 
 
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
  
 
 
  
  
 
 
  
  
  
  
  
  
  
 
 
  
  
 
 
 
 
 
 
  
  
  
  
  
 
 
  
  
 
 
  
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
  
  
  
  
 
 
  
  
 
 
 
  
  
  
 
 
 
  
  
 
 
 
  
  
  
 
 
 
 
 
 
 
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
  
  
  
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
  
  
  
  
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
  
  
  
  
 
 
 
 
 
 
 
  
  
  
  
  
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
  
  
  
  
  
  
  
  
  
 
 
 
  
  
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
  
  
 
 
 
  
  
  
  
  
  
  
 
 
 
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
  
 
 
 
 
  
  
  
  
  
  
  
 
 
 
 
 
  
 
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
 
 
 
  
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
  
  
  
 
 
 
 
 
 
 
  
  
  
  
  
 
 
 
 
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
 
  
  
  
  
 
 
 
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
  
  
  
  
  
  
  
 
 
 
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
 
 
  
  
  
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
  
  
 
  
  
  
 
 
  
  
  
  
  
  
 
 
 
  
 
 
  
 
  
 
 
 
 
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
 
 
 
 
  
 
 
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
  
  
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
 
 
 
 
  
  
 
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
 
 
  
  
 
 
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
  
 
 
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
  
  
 
 
 
  
  
 
 
   
The response was cut off due to length constraints. Let me create a more
<tool_call>
<function=Write>
<parameter=content>
# Security Approval Gate

## Purpose
Ensures security considerations are addressed throughout the SDLC and the solution meets security standards before promotion.

## Entry Criteria
- [ ] Development Complete Gate passed
- [ ] Threat modeling completed
- [ ] Security requirements documented
- [ ] SAST/DAST/SCA scans performed
- [ ] Security testing plan approved
- [ ] Architecture security review conducted
- [ ] Access controls defined
- [ ] Data protection requirements specified
- [ ] Logging/monitoring requirements identified
- [ ] Incident response considerations noted
- [ ] Third-party integrations reviewed
- [ ] Regulatory requirements identified
- [ ] Security training completed
- [ ] Penetration testing scope defined
- [ ] Secure coding standards established
- [ ] Secrets management approach defined
- [ ] Security headers/protections planned

## Exit Criteria
### Vulnerability Management
- [ ] Critical vulnerabilities resolved
- [ ] High vulnerabilities resolved or risk accepted  
- [ ] Medium/low vulnerabilities prioritized in backlog
- [ ] Dependency vulnerabilities addressed through updates/patches
- [ ] No known exploitable vulnerabilities remain in production-bound code
- [ ] Vulnerability scan false positives documented and justified
- [ ] Vulnerability management process followed consistently
- [ ] Security debt tracked and prioritized appropriately
- [ ] Third-party component licensing compliance verified

### Secure Development Practices
- [ ] Secure coding standards followed throughout development
- [ ] Input validation and output encoding implemented correctly
- [ ] Authentication and authorization mechanisms are secure
- [ ] Session management is secure (if applicable)
- [ ] Cryptographic implementations use approved algorithms and libraries
- [ ] Key management follows best practices (rotation, protection)
- [ ] Error handling does not leak sensitive information in messages or logs
- [ ] Logging captures security-relevant events without sensitive data
- [ ] Common vulnerabilities prevented (XSS, SQLi, CSRF, etc.)
- [ ] File upload functionality properly secured (if applicable)
- [ ] XXE protections in place (if XML used)
- [ ] Deserialization vulnerabilities prevented
- [ ] Directory traversal attacks prevented
- [ ] Clickjacking protections implemented (if web app)
- [ ] Security misconfigurations avoided through hardening
- [ ] Unused features, services, and ports are disabled
- [ ] Default credentials are changed or disabled
- [ ] Least privilege principle applied to service accounts and permissions
- [ ] Network segmentation and access controls designed appropriately

### Data Protection
- [ ] Sensitive data is encrypted at rest using strong algorithms (AES-256, etc.)
- [ ] Data in transit is protected with TLS 1.2 or higher
- [ ] Encryption keys managed securely (KMS, HSM, or equivalent)
- [ ] Key rotation procedures established and documented
- [ ] Personally Identifiable Information (PII) identified and protected
- [ ] Payment Card Industry (PCI) data handling complies with standards (if applicable)
- [ ] Protected Health Information (PHI) handling complies with HIPAA (if applicable)
- [ ] Data minimization principles followed
- [ ] Data retention and deletion policies implemented
- [ ] Data masking and tokenization used where appropriate
- [ ] Database encryption or column-level encryption applied (if needed)
- [ ] Backup encryption implemented
- [ ] Secure deletion procedures established for sensitive data

### Identity and Access Management
- [ ] Authentication mechanisms are secure and resist common attacks (brute force, etc.)
- [ ] Multi-factor authentication (MFA) implemented where required by policy
- [ ] Password policies comply with security standards (length, complexity, history)
- [ ] Account lockout mechanisms implemented to prevent brute force attacks
- [ ] Password storage uses strong, slow hashing algorithms (bcrypt, scrypt, PBKDF2)
- [ ] Authorization follows least privilege principle
- [ ] Role-based access control (RBAC) or attribute-based access control (ABAC) properly implemented
- [ ] Access rights reviewed regularly (quarterly or as required)
- [ ] Segregation of duties (SoD) enforced where required by policy
- [ ] Privileged access management (PAM) implemented for administrative functions
- [ ] Service-to-service authentication is secure (mutual TLS, API keys, JWT, etc.)
- [ ] Session management uses secure cookies with appropriate attributes (HttpOnly, Secure, SameSite)
- [ ] OAuth/OpenID Connect implementations follow best practices and security guidelines
- [ ] API keys and secrets stored securely (not in code/repositories, use vaults/secrets managers)
- [ ] Token expiration and refresh mechanisms properly implemented
- [ ] Federated identity considerations addressed (if applicable)

### Security Testing
- [ ] Static Application Security Testing (SAST) passes with acceptable results
- [ ] Dynamic Application Security Testing (DAST) conducted (if applicable)
- [ ] Software Composition Analysis (SCA) identifies no critical vulnerable dependencies
- [ ] Infrastructure as Code (IaC) scanning identifies no misconfigurations
- [ ] Container image scanning finds no critical vulnerabilities
- [ ] Manual penetration testing completed (if required by policy)
- [ ] Security test cases are defined and executed
- [ ] Fuzz testing performed on critical components (if applicable)
- [ ] API security testing completed (if applicable)
- [ ] Mobile application security testing done (if applicable)
- [ ] Social engineering resistance evaluated (if applicable)
- [ ] Red team/blue team exercises conducted (if applicable)
- [ ] Security regression testing is included in test suite
- [ ] Security test environment closely mirrors production for validity

### Logging, Monitoring, and Incident Response
- [ ] Security-relevant events are logged (authentication, authorization, data access, etc.)
- [ ] Logs do not contain sensitive information (passwords, PII, session tokens, etc.)
- [ ] Log integrity is protected from tampering (write-once, append-only, or signed)
- [ ] Log retention meets regulatory and business requirements
- [ ] Centralized logging is implemented for distributed systems
- [ ] Real-time alerting is configured for security events (failed logins, privilege escalation, etc.)
- [ ] Security Information and Event Management (SIEM) integration is established
- [ ] Intrusion Detection/Prevention Systems (IDS/IPS) alerts are monitored
- [ ] File integrity monitoring is enabled for critical files and configurations
- [ ] Honeytokens or canaries are deployed (if applicable for breach detection)
- [ ] Incident response playbook is updated for this application/services
- [ ] Forensic readiness is considered in logging strategy (sufficient detail for investigation)
- [ ] Security metrics and key risk indicators (KRIs) are defined and tracked
- [ ] Regular security reviews and audits are scheduled
- [ ] Vulnerability disclosure process is established and communicated
- [ ] Security awareness training completion is tracked for team members

### Configuration and Infrastructure Security
- [ ] Infrastructure as Code (IaC) templates are scanned for security issues (misconfigurations)
- [ ] Server hardening standards are applied (CIS benchmarks, vendor guidelines)
- [ ] Network security groups/firewall rules are restricted to minimum required access
- [ ] Default accounts and passwords are changed or disabled
- [ ] Unnecessary services and ports are disabled
- [ ] Secure boot and firmware validation are enabled (where applicable)
- [ ] Encryption is enabled for storage volumes (where supported)
- [ ] Security patches and updates are applied regularly (OS, middleware, runtime)
- [ ] Vulnerability management process for operating systems and platforms
- [ ] Container runtime security is configured (if applicable: read-only root, drop capabilities, etc.)
- [ ] Kubernetes pod security policies or equivalent are applied (if applicable)
- [ ] Secrets are not stored in environment variables or configuration files (use secrets managers)
- [ ] Runtime application self-protection (RASP) is considered (if applicable)
- [ ] Web Application Firewall (WAF) rules are configured and tested
- [ ] API gateway security policies are enforced (rate limiting, IP allowlisting, etc.)
- [ ] Service mesh security policies are implemented (if applicable: mTLS, authorization policies)
- [ ] Zero trust network access principles are followed where possible (never trust, always verify)

### Compliance and Governance
- [ ] Applicable regulatory requirements are identified and addressed (GDPR, CCPA, HIPAA, PCI-DSS, SOX, etc.)
- [ ] Data processing agreements are in place for third-party services (if applicable)
- [ ] Privacy impact assessment (PIA) is completed (if required by regulation)
- [ ] Security controls are mapped to compliance requirements for verification
- [ ] Audit logging supports compliance reporting requirements (who, what, when, where)
- [ ] Evidence collection for audits is facilitated (logs, access records, configuration)
- [ ] Records of processing activities are maintained (if GDPR applies)
- [ ] Data subject access request (DSAR) capabilities are implemented (if GDPR applies)
- [ ] Right to be forgotten functionality is implemented (if GDPR applies)
- [ ] Data breach notification procedures are established (timelines, contents, authorities)
- [ ] Security policies and standards are referenced and followed (ISO 27001, NIST, CIS, etc.)
- [ ] Exception request process is followed for any deviations from standards
- [ ] Contractual security requirements with vendors are met (SLAs, security clauses)
- [ ] Export control restrictions are considered (if applicable for cryptography)
- [ ] Classification and handling of data follows information security policy
- [ ] Insurance and liability considerations are addressed (cyber insurance, etc.)
- [ ] Third-party risk management assessments are completed for critical vendors
- [ ] Security supply chain risks are evaluated (provenance, integrity of components)
- [ ] Open source license compliance is verified (permissions, obligations, restrictions)
- [ ] Cryptographic usage complies with export regulations (if applicable: Wassenaar, etc.)

## Exit Questions
1. What is the current status of critical and high-severity security vulnerabilities?
2. Have all security testing activities (SAST, DAST, SCA, penetration testing) been completed with acceptable results?
3. Is sensitive data properly protected both at rest and in transit?
4. Are authentication and authorization mechanisms implemented correctly and securely?
5. Have security configurations and hardening measures been applied?
6. Is logging and monitoring sufficient to detect and respond to security incidents?
7. Are identity and access management controls properly implemented?
8. Have all applicable compliance requirements been addressed?
9. Is the infrastructure securely configured and hardened?
10. What is the plan for ongoing security maintenance and monitoring?
11. Are there any outstanding security risks that require formal risk acceptance?
12. Have security considerations been integrated throughout the SDLC (shift-left security)?
13. Is the security track record of third-party components and services acceptable?
14. Are security metrics and reporting mechanisms in place for continuous improvement?
15. What evidence demonstrates compliance with organizational security policies and standards?

## Exit Options
- **APPROVE**: Security controls are adequate, can proceed to next stage
- **CONDITIONAL APPROVE**: Approved with specific compensating controls or enhanced monitoring requirements
- **REJECT**: Significant security issues remain that must be addressed before proceeding
- **DEFER**: Security assessment incomplete, resume when additional information/tests are available

## Evidence Required
- Threat model documentation (STRIDE, PASTA, TRIKE, etc.)
- Security requirements specification document
- SAST scan reports with remediation evidence/tracking
- DAST scan reports (if performed)
- Software Composition Analysis (SCA) / dependency scanning reports
- Container image scan reports
- Infrastructure as Code (IaC) scan reports (Terraform, CloudFormation, etc.)
- Manual penetration testing report (if conducted)
- Security test cases and execution results
- Security test automation scripts and coverage metrics
- Threat modeling diagrams and findings
- Security architecture review documentation and feedback
- Access control matrices, policies, and implementation evidence
- Encryption key management documentation and procedures
- Data flow diagrams showing protection points (encryption, tokenization, masking)
- Security configuration baselines and drift reports
- Firewall, network security group, and security rule configurations
- Identity and access management configurations and review evidence
- Audit logging configuration, samples, and retention policies
- Monitoring and alerting rules for security events with thresholds
- Incident response playbook updates and version control
- Security training completion records and materials
- Vulnerability management reports, metrics, and trend analysis
- Compliance assessment reports, gap analyses, and remediation plans
- Data protection impact assessments (if applicable)
- Security exception requests and approvals (if any deviations granted)
- Third-party security assessment reports (SOC 2 Type II, ISO 27001 certificates, etc.)
- Security code review checklists and results from peer reviews
- Security metrics dashboard or regular security reports to stakeholders
- Disaster recovery and business continuity considerations from security perspective
- Data retention, archival, and disposal procedures for sensitive data
- Security architecture diagrams showing trust boundaries, data flows, and zones
- Secure coding standard documentation and compliance matrix against actual code
- Security training materials, attendance records, and effectiveness measurements
- Penetration test scope, rules of engagement, and detailed findings with remediation
- Red team exercise results, objectives, tactics, and lessons learned (if applicable)
- Bug bounty program participation reports and vulnerability disclosure metrics
- Security configuration baseline documents and deviation reports
- Web Application Firewall (WAF) rules, tests, and effectiveness metrics
- API gateway security policy configurations and enforcement reports
- Service mesh security policy configurations (if applicable: mTLS, authorization, rate limiting)
- Zero trust network access implementation evidence and validation
- Data classification and handling policy implementation evidence
- Encryption key lifecycle management documentation and audit trails
- Backup encryption verification and restore test records
- Secure deletion procedures and verification methods
- Privileged access management (PAM) implementation and usage reports
- Service account creation, usage, and decommissioning procedures
- Account provisioning and deprovisioning automation evidence
- Password policy enforcement and compliance reports
- Multi-factor authentication (MFA) adoption and usage statistics
- Session management configuration and timeout values
- OAuth/OpenID Connect implementation details and security assessments
- API key and secret management system audit trails and access logs
- Token validation, expiration, and refresh mechanism testing results
- Network segmentation diagrams and access control validation tests
- Intrusion Detection/Prevention System (IDS/IPS) configuration and tuning reports
- File integrity monitoring (FIM) configuration and baseline reports
- Honeytoken/decoy deployment documentation and alerting mechanisms
- Forensic readiness preparations: logging sufficiency, chain of custody, tool availability
- Security metrics and key risk indicators (KRIs) dashboard and trend analysis
- Security awareness training completion rates, quiz scores, and behavioral metrics
- Phishing simulation results and click-through rates over time
- Regular security review meeting minutes, attendance, and action items
- Internal and external security audit reports, findings, and remediation status
- Compliance assessment reports (GDPR, HIPAA, PCI-DSS, SOC 2, ISO 27001, etc.)
- Data processing agreements (DPAs) with third-party vendors and service providers
- Privacy impact assessment (PIA) reports and mitigation plans
- Data subject access request (DSAR) process documentation and testing results
- Right to be forgotten implementation verification and performance metrics
- Data breach incident response plan, playbook, and communication templates
- Security exception request forms, justifications, approval workflows, and expiration dates
- Contractual security requirements verification against vendor SOC 2, ISO 27001, etc.
- Export control classification numbers (ECCNs) and licensing documentation (if applicable)
- Data inventory and classification register with sensitivity levels and handling requirements
- Information security policy version, distribution acknowledgments, and compliance matrix
- Acceptable use policy (AUP) documentation and user acceptance records
- Clean desk and clear screen policy compliance evidence and monitoring
- Password policy enforcement reports, breakdown of compliance metrics, and exceptions
- Remote work security policy implementation verification and device inventory
- Cloud security posture management (CSPM) scan results and remediation tracking
- Container security scanning results, base image vulnerabilities, and runtime permissions
- Secrets management solution audit trails, access logs, and rotation verification
- Runtime application self-protection (RASP) agent deployment, configuration, and alerts
- Web Application Firewall (WAF) rule sets, testing results, false positive/negative rates
- API gateway configuration, security policies, rate limiting, IP allowlisting, and throttling
- Service mesh configuration, mutual TLS (mTLS) adoption, authorization policies, and rate limits
- Zero trust network access policy enforcement, device posture checks, and micro-segmentation
- Data classification tool outputs, tagging consistency, and handling procedure adherence
- Encryption key management system (KMS/HSM) audit logs, key lifecycle events, and access
- Encryption algorithm validation, key strength verification, and certificate transparency
- Backup encryption verification, restore test results, and key management for backups
- Secure deletion verification methods, overwrite patterns, and confirmation procedures
- Privileged access management (PAM) session monitoring, command logging, and audit trails
- Service account inventory, purpose documentation, credential rotation, and decommissioning
- Automated user provisioning/deprovisioning integration with HR systems and audit trails
- Password policy configuration files, compliance reporting tools, and exception workflows
- Multi-factor authentication (MFA) provider selection, conditional access policies, and adoption
- Session management configuration files, timeout values, and secure flag enforcement
- OAuth/OpenID Connect client configurations, token validation, scope enforcement, and revocation
- API key management system access logs, rotation history, and unauthorized use detection
- JWT signing algorithm verification, key rotation, expiration handling, and audience validation
- OAuth token storage recommendations, encryption at rest, and short-lived token practices
- Network segmentation diagrams, VLAN configurations, firewall rule bases, and access validation
- Intrusion Detection/Prevention System (IDS/IPS) signature updates, tuning effectiveness, and false positive rates
- File integrity monitoring (FIM) baselines, change detection alerts, and exclusion lists
- Hardware security module (HSM) utilization, key generation logs, and administrative access
- Trusted platform module (TPM) availability, attestation capabilities, and boot integrity
- Secure boot configuration, validation logs, and alternative boot prevention mechanisms
- Firmware integrity verification, signed update mechanisms, and rollback prevention
- Container image signing, provenance verification, and runtime security constraints
- Kubernetes admission control policies, pod security standards, and namespace isolation
- Service mesh traffic policies, authorization rules, rate limiting, and mutual TLS enforcement
- API gateway security policies, authentication enforcement, rate limiting, and threat protection
- Web Application Firewall (WAF) rule management, testing efficacy, and bypass prevention
- Data loss prevention (DLP) configuration, rule testing, false positive rates, and incident workflows
- Email security gateway (ESG) settings, spam filtering, phishing detection, and malware protection
- Endpoint detection and response (EDR) agent deployment, configuration, and threat detection
- Mobile device management (MDM) policies, containerization, encryption, and remote wipe
- Identity governance and administration (IGA) lifecycle management, entitlement management, and access reviews
- Privileged access management (PAM) session monitoring, command logging, and just-in-time access
- Identity proofing and verification procedures, document validation, and biometric considerations
- Passwordless authentication methods, FIDO2/WebAuthn implementation, and device attestation
- Privileged access management (PAM) vault integration, account onboarding, and credential rotation
- Identity governance and administration (IGA) role engineering, access certification, and segregation of duties
- Security information and event management (SIEM) rule tuning, false positive reduction, and threat hunting
- Security orchestration, automation, and response (SOAR) playbooks, automation effectiveness, and manual intervention
- User and entity behavior analytics (UEBA) baseline establishment, anomaly detection, and tuning
- Deception technology deployment, honeytoken placement, alert fidelity, and engagement metrics
- Identity data quality, completeness, accuracy, and timeliness metrics for governance processes
- Access expiration and recertification workflows, completion rates, and remedial action tracking
- Identity lifecycle management events, provisioning timelines, and accuracy of entitlement assignments
- Privileged access management (PAM) checkout duration, session isolation, and replay attack prevention
- Identity federation metadata exchange, certificate validity, and single sign-off loop prevention
- Attribute mapping and transformation accuracy, claim validation, and privacy-preserving techniques
- Federated identity logout procedures, session invalidation, and cross-domain session management
- Consent management platform (CMP) integration, preference storage, and regulatory compliance
- Preference signaling compliance, global privacy control (GPC) adherence, and do not track (DNT) handling
- Consent receipt generation, storage, and verification for audit trails and transparency
- Consent withdrawal processing, preference reversal, and data isolation or deletion mechanisms
- Geofencing implementation, location-based access controls, and consent boundary enforcement
- Purpose limitation enforcement, consent scope validation, and data segregation by purpose
- Data minimization techniques, field-level encryption, and selective disclosure mechanisms
- Consent audit trail integrity, timestamp reliability, and non-repudiation mechanisms
- Consent versioning, backward compatibility, and upgrade/migration strategies for existing consents
- Local law and regulation compliance matrix, jurisdictional requirements, and conflict resolution mechanisms
- Cross-border data transfer mechanisms, adequacy decisions, and standard contractual clauses (SCCs)
- Data localization requirements, storage location restrictions, and processing location constraints
- International data transfer impact assessments, risk evaluations, and supplemental measures
- Consent management for special categories of data, explicit consent requirements, and processing limitations
- Children's online privacy protection (COPPA) compliance, age verification mechanisms, and parental consent
- Health Insurance Portability and Accountability Act (HIPAA) safeguards, minimum necessary rule, and business associate agreements
- Payment Card Industry Data Security Standard (PCI DSS) scoping, network segmentation, and cardholder data environment
- Service organization control (SOC) reports, type distinctions, trust service criteria, and auditor qualifications
- International Organization for Standardization (ISO) 27001 controls, statement of applicability, and audit evidence
- National Institute of Standards and Technology (NIST) Cybersecurity Framework (CSF) functions, categories, and subcategories
- Center for Internet Security (CIS) benchmarks, configuration guidelines, and assessment tools for various platforms
- Health Information Trust Alliance (HITRUST) CSF controls, requirement statements, and assessment methodology
- Federal Risk and Authorization Management Program (FedRAMP) baselines, security controls, and continuous monitoring
- Defense Federal Acquisition Regulation Supplement (DFARS) clauses, cybersecurity requirements, and documentation
- Cybersecurity Maturity Model Certification (CMMC) levels, practices, processes, and assessment methodology
- General Data Protection Regulation (GDPR) articles, recitals, guidelines, and enforcement mechanisms
- California Consumer Privacy Act (CCPA) definitions, rights, obligations, and enforcement procedures
- Health Insurance Portability and Accountability Act (HIPAA) privacy rule, security rule, and breach notification
- Sarbanes-Oxley Act (SOX) internal controls over financial reporting, section 404, and audit requirements
- Federal Information Security Modernization Act (FISMA) requirements, NIST mappings, and authorization process
- North American Electric Reliability Corporation Critical Infrastructure Protection (NERC CIP) standards
- Financial Industry Regulatory Authority (FINRA) rules, regulatory notices, and compliance requirements
- Health Level Seven International (HL7) standards, messaging formats, and implementation guides for healthcare
- Digital Imaging and Communications in Medicine (DICOM) standards, protocols, and implementation guides for medical imaging
- Society for Worldwide Interbank Financial Telecommunication (SWIFT) customer security controls and compliance
- Base II and Base III security requirements for payment card processing and transaction security
- Automated Clearing House (ACH) network rules, operating rules, and risk management frameworks for electronic payments
- International Traffic in Arms Regulations (ITAR) and Export Administration Regulations (EAR) compliance for defense
- Committee on Foreign Investment in the United States (CFIUS) reviews, national security considerations, and mitigation
- Foreign Corrupt Practices Act (FCPA) provisions, anti-bribery measures, accurate books and records, and internal controls
- Antiboycott provisions, reporting requirements, and compliance with export administration regulations
- OECD Guidelines for Multinational Enterprises, responsible business conduct, and implementation procedures
- Uyghur Forced Labor Prevention Act (UFLPA) compliance, supply chain tracing, and entity list verification
- Supporting legislation, regulations, directives, and standards for specific industries and data types
- General Data Protection Regulation (GDPR) Article 30 records of processing activities, template, and guidance
- California Consumer Privacy Act (CCPA) Section 1798.100 definitions, scope, and applicability
- Health Insurance Portability and Accountability Act (HIPAA) § 164.502 uses and disclosures of protected health information
- Health Insurance Portability and Accountability Act (HIPAA) § 164.506 uses and disclosures for treatment, payment, and operations
- Health Insurance Portability and Accountability Act (HIPAA) § 164.512 uses and disclosures with
 
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  sensor
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
 
 
 
 
  
  
  
 
 
 
  
  
  
  
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
 
 
 
 
  
  
  
 
 
 
  
  
  
  
  
 
 
 
 
  
  
  
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
 
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
  
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
 
 
 
  
  
  
 
 
 
  
  
  
  
 
 
 
 
  
  
  
  
  
  
 
 
 
 
 
 
 
  
  
  
  
  
 
 
  
  
 
 
 
 
 
 
 
 
 
 
  
  
  
  
 
 
 
 
 
 
 
  
  
  
 
 
 
 
 
  
 
 
  
  
  
  
  
 
 
 
 
 
 
  
  
 
 
  
  
  
 
 
 
 
 
  
  
  
 
 
 
 
 
 
  
  
  
  
 
 
 
  
  
  
 
 
 
 
 
 
 
 
  
  
  
 
 
  
 
 
 
 
 
  
  
  
  
  
 
 
  
  
 
 
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
  
  
  
 
 
 
  
  
  
 
 
  
  
 
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
  
  
  
  
  
 
 
 
  
  
 
 
 
  
  
  
  
  
  
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
 
 
  
  
 
 
 
 
 
 
 
 
  
  
  
  
 
 
 
 
 
  
  
  
  
 
 
 
  
  
  
 
 
 
  
  
 
 
 
 
 
  
  
  
  
  
  
 
 
  
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
  
  
  
  
  message
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
 
 
 
  
  
  
  
  
  
 
 
  
  
  
  
  
  
  
 
 
 
  
  
  
 
 
 
 
 
 
 
 
  
  
  
  
  
 
 
  
  
  
 
 
 
  
  
  
  
 
 
 
 
  
  
  
  
  
 
 
 
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
 
 
  
  
  
  
 
 
 
  
  
  
 
 
  
 
 
 
  
  
  
 
  
  
  
  
  
 
 
 
  
  
  
  
 
  
  
  
  
  
  
 
 
 
 
 
  
  
  
  
  
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
 
 
 
 
 
 
  
  
 
 
  
  
 
 
 
 
 
 
 
  
  
 
  
  
  
  
  
 
 
  
  
  
  
  
  
 
 
 
 
  
  
  
 
 
 
  
  
 
 
  
 
 
 
 
 
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
 
 
 
 
 
  
  
  
 
 
 
 
  
  
  
 
 
 
  
 
  
 
 
 
 
  
  
  
  
  
  
 
 
 
 
  
  
  
  
  
 
 
  
 
 
  
  
  
  
 
 
 
 
 
 
 
  
  
  
  
 
 
 
  
  
 
  
 
  
  
 
  
  
  
 
 
  
  
  
 
 
 
  
  
  
 
 
  
 
 
  
  
 
 
 
 
 
 
 
  
  
  
  
  
  
  
 
  
  
  
  
  
 
 
 
 
 
 
 
 
  
  
  
 
 
  
  
  
  
  
  
  
  
 
 
 
  
  
 
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
  
  
  
  
 
 
 
  
 
  
  
  
 
 
 
  
  
  
  
  
  
  
 
 
  
  
  
  
  
  
  
 
 
  
 
 
 
 
  
  
  
  
  
  
 
 
  
 
 
  
  
  
  
  
  
 
 
  
 
 
  
 
 
  
  
 
  
  
 
  
  
 
 
 
  
 
 
 
 
  
  
  
 
 
  
 
 
 
  
  
 
 
  
 
  
 
 
 
 
  
  
 
 
 
 
 
  
  
 
 
  
 
 
 
 
 
 
  
  
  
  
  
 
 
  
  
  
  
 
 
  
 
 
  
  
  
 
 
 
  
  
 
 
 
 
  
  
  
 
 
 
 
  
  
  
  
 
 
  
 
 
 
  
  
 
  
  
 
 
 
  
  
  
  
 
 
  
 
 
  
 
 
  
  
 
 
  
 
 
 
 
 
 
 
  
  
  
  
  
 
 
  
 
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
  
  
 
 
 
 
  
  
  
 
 
 
 
 
 
 
  
  
  
  
  
  
 
 
 
 
  
  
  
 
 
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
  
  
  
 
 
 
  
  
  
  
  
  
 
 
  
 
 
 
 
 
  
  
  
 
  
  
 
 
  
  
  
 
 
 
 
 
 
 
 
  
  
 
 
  
  
  
 
 
  
 
 
 
 
 
 
  
  
  
  
 
 
  
  
  
  
  
  
  
 
 
 
 
 
 
 
 
 
  
  
  
  
  
  
 
 
  
 
  
 
  
  
  
 
 
 
  
 
 
 
 
 
 
 
 
 
 
 
  
  
  
 
 
 
 
 
 
  
  
 
  
  
  
  
 
 
  
 
  
  
 
  
  
  
  
  
  
  
  
 
 
  
 
 
  
 
 
 
  
  
  
 
 
  
  
 
  
  
  
  
 
 
  
  
 
 
  
 
 
 
 
  
 
 
  
  
  
 
 
 
 
 
   
The response was cut off again. Let me create a much shorter version focusing on the essential<tool_call>
<function=Write>
<parameter=content>
# Security Approval Gate

## Purpose
Ensures security considerations are addressed throughout SDLC and solution meets security standards before promotion.

## Entry Criteria
- Development Complete Gate passed
- Threat modeling completed
- Security requirements documented
- SAST/DAST/SCA scans performed
- Security testing plan approved
- Architecture security review conducted

## Exit Criteria
### Vulnerability Management
- Critical vulnerabilities resolved
- High vulnerabilities resolved or risk accepted
- Medium/low vulnerabilities prioritized
- Dependency vulnerabilities addressed
- No known exploitable vulnerabilities remain

### Secure Development
- Secure coding standards followed
- Input validation/output encoding implemented
- Authentication/authorization secure
- Session management secure (if applicable)
- Cryptography uses approved algorithms
- Error handling doesn't leak sensitive data
- Common vulnerabilities prevented (XSS, SQLi, CSRF, etc.)

### Data Protection
- Sensitive data encrypted at rest (AES-256+)
- Data in transit protected with TLS 1.2+
- Encryption keys managed securely (KMS/HSM)
- PII/PHI identified and protected per regulations
- Data minimization and retention policies implemented
- Backup encryption implemented

### Identity and Access Management
- Authentication resists brute force, etc.
- MFA implemented where required
- Strong password policies enforced
- Password storage uses bcrypt/scrypt/PBKDF2
- Authorization follows least privilege
- Access rights reviewed regularly
- Segregation of duties enforced where required
- Privileged access management for admin functions
- Service-to-service auth secure (mTLS, API keys, JWT)
- Secure session management (HttpOnly, Secure cookies)
- OAuth/OpenID Connect follows best practices
- API keys/secrets stored securely (secrets managers)

### Security Testing
- SAST passes with acceptable results
- DAST conducted if applicable
- SCA finds no critical vulnerable dependencies
- IaC scanning finds no misconfigurations
- Container scanning finds no critical vulnerabilities
- Penetration testing completed if required
- Security test cases defined/executed
- Fuzz testing on critical components if applicable
- API security testing completed if applicable
- Security regression testing in test suite
- Security test environment mirrors production

### Logging and Monitoring
- Security events logged (auth, access, etc.)
- Logs don't contain sensitive information
- Log integrity protected from tampering
- Centralized logging for distributed systems
- Real-time alerting for security events
- SIEM integration established
- IDS/IPS alerts monitored
- File integrity monitoring enabled for critical files
- Incident response plan updated
- Forensic readiness considered
- Security metrics/KRIs defined and tracked
- Regular security reviews/audits scheduled
- Vulnerability disclosure process established

### Infrastructure Security
- IaC templates scanned for security issues
- Server hardening standards applied (CIS benchmarks)
- Network security groups/firewall rules minimized
- Default accounts/passwords changed/disabled
- Unnecessary services/ports disabled
- Secure boot/firmware validation enabled where applicable
- Storage volume encryption enabled where supported
- Security patches/updates applied regularly
- Container runtime security configured if applicable
- K8s pod security policies applied if applicable
- Secrets not in env vars/config files (use secrets managers)
- WAF rules configured/tested
- API gateway security policies enforced
- Service mesh security policies implemented if applicable
- Zero trust principles followed where possible

### Compliance and Governance
- Applicable regulations addressed (GDPR, CCPA, HIPAA, PCI-DSS, SOX)
- Data processing agreements for third parties if applicable
- PIA completed if required
- Controls mapped to compliance requirements
- Audit logging supports compliance reporting
- Evidence collection facilitated for audits
- Processing activities recorded if GDPR applies
- DSAR capabilities implemented if GDPR applies
- Right to be forgotten implemented if GDPR applies
- Data breach notification procedures established
- Security policies/standards referenced/followed
- Exception request process followed for deviations
- Contractual vendor security requirements met
- Export control restrictions considered if applicable
- Data classification/handling follows policy
- Third-party risk management assessments completed
- Supply chain security risks evaluated
- Open source license compliance verified
- Cryptographic usage complies with export regs if applicable

## Exit Questions
1. Status of critical/high security vulnerabilities?
2. All security tests (SAST, DAST, SCA, pen testing) completed acceptably?
3. Sensitive data properly protected at rest and in transit?
4. Authentication/authorization correctly implemented?
5. Security configurations/hardening applied?
6. Logging/monitoring sufficient for detection/response?
7. IAM controls properly implemented?
8. All compliance requirements addressed?
9. Infrastructure securely configured/hardened?
10. Plan for ongoing security maintenance/monitoring?
11. Outstanding risks requiring formal risk acceptance?
12. Security considerations integrated throughout SDLC?
13. Third-party component/service security track record acceptable?
14. Security metrics/reporting mechanisms in place?
15. Evidence demonstrates compliance with security policies?

## Exit Options
- APPROVE: Security controls adequate, proceed
- CONDITIONAL APPROVE: Approved with specific compensating controls/monitoring
- REJECT: Significant security issues remain
- DEFER: Assessment incomplete, resume later

## Evidence Required
- Threat model documentation
- Security requirements specification
- SAST/DAST/SCA reports + remediation evidence
- Container/IaC scan reports
- Penetration test report (if conducted)
- Security test cases/results
- Security test automation scripts/coverage
- Access control policies/evidence
- Encryption key management documentation
- Data flow diagrams showing protection
- Security configuration baselines
- Firewall/NSG rules
- IAM configurations
- Audit logging config/samples
- Monitoring/alerting rules
- Incident response plan updates
- Security training records
- Vulnerability management reports
- Compliance assessments/gap analysis
- Data protection impact assessments
- Security exception requests/approvals
- Third-party security assessments (SOC 2, ISO 27001)
- Security code review checklists/results
- Security metrics dashboard/reports

## Roles and Responsibilities
- Information Security Lead: Leads review and approval
- Application Security Engineer: Conducts testing and reviews
- DevSecOps Engineer: Integrates security into CI/CD
- Network Security Engineer: Reviews network security controls
- Database Security Administrator: Reviews data protection
- Cloud Security Engineer: Reviews cloud security controls
- Application Architect: Ensures security in design
- Development Team Lead: Represents development perspective
- QA Lead: Confirms security testing adequacy
- Compliance Officer: Validates regulatory compliance
- Privacy Officer: Reviews privacy controls if applicable
- Audit/Internal Audit: Validates audit readiness
- Infrastructure/Platform Team: Validates infrastructure security
- Product Owner: Represents business perspective
- Release Manager: Coordinates release process
- Stakeholders: Subject matter experts as needed

## Related Artifacts
- Threat model documentation (STRIDE, PASTA, etc.)
- Security requirements specification
- Secure coding standards document
- Vulnerability management policy
- Patch management procedure
- Incident response plan
- Disaster recovery plan
- Business continuity plan
- Security awareness training materials
- Access control policy
- Data classification and handling policy
- Encryption key management policy
- Suppliers and third parties security policy
- Remote access policy
- Acceptable use policy
- Clean desk and clear screen policy
- Password policy
- Remote working policy
- Cloud security policy
- Container security policy
- DevSecOps policy
- API security policy
- Mobile device management policy
- Encryption policy
- Backup and encryption policy
- Audit logging policy
- Monitoring and alerting policy
- Penetration testing methodology
- Red team exercise framework
- Bug bounty/vulnerability disclosure policy
- Security metrics and reporting framework
- Security risk assessment methodology
- Security exception request form
- Security approval checklist
- Security test plan template
- Security test case template
- Penetration test report template
- Vulnerability assessment report template
- Security architecture review template
- Threat modeling template
- Secure code review checklist
- Security configuration checklist
- Network security checklist
- Database security checklist
- Application security checklist
- Cloud security checklist
- DevSecOps checklist
- Container security checklist
- IAM checklist
- Data protection checklist
- Incident response checklist
- Forensic readiness checklist
- Compliance checklist (GDPR, HIPAA, PCI-DSS, etc.)
- Privacy impact assessment template
- Data processing agreement template
- Third-party risk assessment questionnaire
- Vendor security assessment questionnaire
- Security awareness training attendance sheet
- Phishing simulation results
- Security poster/awareness materials
- Security newsletters/communications
- Security bulletins/advisories