# Security Review Checklist

## Assessment Information
- **Application/System Name**: [Name of the application or system]
- **Version/Release**: [Version being assessed]
- **Assessment Type**: [Initial Assessment / Periodic Review / Pre-release / Post-incident]
- **Assessment Date**: YYYY-MM-DD
- **Assessor(s)**: [Names and roles]
- **Stakeholders Consulted**: [Product, Engineering, Security, Ops, Legal, etc.]
- **Compliance Frameworks**: [SOC 2, ISO 27001, GDPR, HIPAA, PCI-DSS, etc.]
- **Environment**: [Development / Staging / Production]
- **Criticality Rating**: [P0/P1/P2/P3 or equivalent]

## Executive Summary
[High-level findings summary, overall risk rating, key recommendations]

### Overall Risk Rating
- [ ] Critical
- [ ] High
- [ ] Medium
- [ ] Low
- [ ] Informational

### Recommendation Summary
- [ ] Immediate action required (critical findings)
- [ ] Remediation recommended within 30 days (high findings)
- [ ] Remediation recommended within 90 days (medium findings)
- [ ] Consider for future improvement (low findings)
- [ ] No action required (findings addressed or accepted)

## 1. Identity and Access Management

### Authentication
- [ ] Multi-factor authentication (MFA) enforced for all user access
- [ ] Password policies enforced (length, complexity, history, expiration)
- [ ] Passwords stored using strong, adaptive hashing (bcrypt, scrypt, Argon2)
- [ ] Brute force protection implemented (account lockout, rate limiting, CAPTCHA)
- [ ] Passwordless options considered where appropriate (magic links, WebAuthn)
- [ ] Session management secure (HttpOnly, Secure, SameSite cookies)
- [ ] Session timeout and idle timeout configured appropriately
- [ ] Single Sign-On (SSO) implemented for enterprise applications
- [ ] Password reuse prevented across systems
- [ ] Credential stuffing protections in place
- [ ] Account enumeration prevented (consistent error messages)
- [ ] Forgotten password flow secure (rate-limited, token-based)

### Authorization
- [ ] Principle of least privilege applied to all roles and permissions
- [ ] Role-Based Access Control (RBAC) model implemented
- [ ] Attribute-Based Access Control (ABAC) considered for fine-grained needs
- [ ] Access controls enforced at both API and UI layers
- [ ] Insecure Direct Object References (IDOR) prevented
- [ ] Privilege escalation paths identified and mitigated
- [ ] Administrative functions segregated and restricted
- [ ] Service-to-service authentication using strong methods (mTLS, JWT)
- [ ] Just-In-Time (JIT) access implemented for privileged roles
- [ ] Regular access reviews conducted (quarterly minimum)
- [ ] Orphaned accounts detected and removed
- [ ] Privileged Access Management (PAM) solution in place for admin access

### Identity Federation
- [ ] Identity provider (IdP) securely configured and maintained
- [ ] SAML/OIDC configurations reviewed for security best practices
- [ ] Just-in-time provisioning configured appropriately
- [ ] Federation metadata exchanged securely
- [ ] Signature validation enforced on SAML assertions
- [ ] Encryption used for sensitive assertions where required
- [ ] Audience and recipient validation implemented
- [ ] Single Logout (SLO) configured where applicable
- [ ] Session synchronization between SP and IdP considered

## 2. Data Protection

### Data Classification and Handling
- [ ] Data inventory completed and maintained
- [ ] Data classification schema defined and applied
- [ ] Personally Identifiable Information (PII) identified and tagged
- [ ] Sensitive Personal Information (SPI) identified under regulations
- [ ] Intellectual property and trade secrets identified
- [ ] Data handling procedures documented for each classification level
- [ ] Data minimization principles followed
- [ ] Purpose limitation implemented
- [ ] Storage limitation and retention policies defined
- [ ] Data subject rights processes established (access, correction, deletion)

### Encryption
- [ ] Data in transit encrypted using TLS 1.2+ everywhere
- [ ] Weak cipher suites and protocols disabled (SSLv3, TLS 1.0, RC4)
- [ ] Forward secrecy enabled (ECDHE cipher suites)
- [ ] HSTS headers configured with appropriate max-age
- [ ] Certificate pinning considered for mobile/thick clients
- [ ] Data at rest encrypted for sensitive information
- [ ] Encryption keys managed using KMS/HSM where possible
- [ ] Key rotation procedures documented and tested
- [ ] Key access controls enforced (least privilege)
- [ ] Hardware Security Modules (HSM) used for root keys where available
- [ ] Encryption algorithms appropriate for data sensitivity (AES-256-GCM)
- [ ] Initialization vectors generated securely (random, unique)
- [ ] Authenticated encryption modes preferred (GCM, CCM)
- [ ] Database field-level encryption considered for highly sensitive data
- [ ] Backup encryption verified and tested

### Data Loss Prevention
- [ ] DLP controls implemented for sensitive data exfiltration
- [ ] Email DLP configured for outbound messages
- [ ] Web proxy DLP monitored for uploads/downloads
- [ ] Endpoint DLP deployed on company devices
- [ ] Cloud Access Security Broker (CASB) used for SaaS applications
- [ ] USB and removable media controls enforced
- [ ] Print monitoring and controls implemented
- [ ] Screen capture and recording protections considered
- [ ] Watermarking applied to sensitive documents where appropriate
- [ ] Audit trails for sensitive data access and transmission

## 3. Application Security

### Input Validation and Output Encoding
- [ ] All input validated on server side (client-side validation insufficient)
- [ ] Input validated for type, length, format, range, and business rules
- [ ] Allow-lists (whitelists) preferred over block-lists (blacklists)
- [ ] SQL injection prevented through parameterized queries/prepared statements
- [ ] NoSQL injection prevented through proper query construction
- [ ] Command injection avoided through API use or proper escaping
- [ ] LDAP injection prevented through input sanitization or escaping
- [ ] XML External Entity (XXE) attacks prevented through parser configuration
- [ ] Cross-Site Scripting (XSS) prevented through output encoding
- [ ] Context-aware output encoding applied (HTML, JS, CSS, URL)
- [ ] Content Security Policy (CSP) implemented defense-in-depth
- [ ] HTTPOnly flag set on cookies to prevent client-side script access
- [ ] SameSite attribute set on cookies to mitigate CSRF
- [ ] Anti-CSRF tokens implemented for state-changing operations
- [ ] File uploads validated (type, size, content) and scanned for malware
- [ ] File uploads stored outside web root and served through secure handler
- [ ] Filename sanitization performed to prevent path traversal
- [ ] Deserialization vulnerabilities avoided or mitigated with whitelisting
- [ ] Template injection prevented through context-aware escaping
- [ ] Server-Side Includes (SSI) injection prevented

### Authentication and Session Management
- [ ] Passwords hashed using strong, adaptive algorithms
- [ ] Password hashing salt unique per user
- [ ] Work factor configured to balance security and performance
- [ ] Password hash migration strategy for algorithm upgrades
- [ ] Password reset tokens cryptographically random and time-limited
- [ ] Account verification tokens single-use and time-limited
- [ ] Remember-me functionality avoided or implemented securely
- [ ] Session IDs cryptographically random and sufficiently long
- [ ] Session IDs regenerated after login and privilege elevation
- [ ] Invalid sessions server-side invalidated immediately
- [ ] Session fixation prevented through regeneration
- [ ] Concurrent session limits on login from multiple devices***

### Code Quality and Dependencies
- [ ] Static Application Security Testing (SAST) integrated into CI/CD
- [ ] Software Bill of Materials (SBOM) generated and reviewed
- [ ] Dependency vulnerability scanning performed regularly
- [ ] Known vulnerabilities in dependencies patched within SLA
- [ ] License compliance checked for open-source components
- [ ] Prohibited dependencies blocked via allow/block lists
- [ ] Dependency update process automated and tested
- [ ] Legacy or unmaintained dependencies identified and replaced
- [ ] Custom cryptographic implementations avoided (use standard libraries)
- [ ] Random number generation uses cryptographically secure sources
- [ ] Error messages do not leak sensitive information (stack traces, etc.)
- [ ] Exception handling centralized and secure
- [ ] Logging does not capture sensitive data (passwords, tokens, PII)
- [ ] Debug information disabled in production builds
- [ ] Compiler warnings treated as errors in CI pipeline
- [ ] Code reviews include security considerations
- [ ] Developer security training provided and tracked

### Business Logic Security
- [ ] Authorization checks verify user can perform requested action
- [ ] Business rule bypasses identified and prevented
- [ ] Race conditions avoided through proper locking or transactions
- [ ] File operation paths validated to prevent traversal
- [ ] Download functionality checked for forced browsing
- [ ] Currency/fractional math uses appropriate decimal types
- [ ] Enumeration attacks mitigated (rate limiting, CAPTCHA)
- [ ] Discount/coupon abuse prevented (one-time use, validation)
- [ ] Workflow manipulation prevented (state machine validation)
- [ ] Time-of-check-time-of-use (TOCTOU) vulnerabilities addressed
- [ ] Uploaded file processing validated for malicious content
- [ ] Image processing libraries kept up-to-date (ImageMagick, etc.)
- [ ] External URL fetching validated (SSRF prevention)
- [ ] Redirects validated to prevent open redirect attacks
- [ ] CAPTCHA used appropriately for high-risk operations
- [ ] Business logic abuse scenarios considered and tested

## 4. Infrastructure and Platform Security

### Network Security
- [ ] Network segmentation implemented (DMZ, private, public subnets)
- [ ] Principle of least privilege applied to network access rules
- [ ] Firewalls configured with explicit deny by default
- [ ] Intrusion Detection/Prevention Systems (IDS/IPS) deployed
- [ ] Distributed Denial of Service (DDoS) mitigation in place
- [ ] Web Application Firewall (WAF) deployed for HTTP/HTTPS traffic
- [ ] Load balancers configured with secure TLS settings
- [ ] Server Name Indication (SNIP) properly supported
- [ ] Idle connection timeouts configured appropriately
- [ ] TLS termination handled securely at edge or load balancer
- [ ] Internal service communication encrypted (mTLS where sensitive)
- [ ] Egress filtering limits outbound connections to required endpoints
- [ ] DNS security extensions (DNSSEC) implemented where applicable
- [ ] Split-horizon DNS used for internal/external resolution
- [ ] Network monitoring and anomaly detection implemented
- [ ] Port scanning and penetration testing performed regularly
- [ ] Virtual Private Cloud (VPC) peering configured securely
- [ ] Service mesh or API gateway used for traffic management

### Host and Instance Security
- [ ] Operating systems kept current with security patches
- [ ] Automated patch management implemented for OS and runtime
- [ ] Unnecessary services and daemons disabled
- [ ] Default accounts renamed, disabled, or password changed
- [ ] Least privilege user accounts used for services
- [ ] Kernel hardening applied where appropriate (SELinux, AppArmor)
- [ ] System auditing configured (auditd, Windows Advanced Audit)
- [ ] Log forwarding to centralized SIEM/system
- [ ] File integrity monitoring (FIM) deployed on critical systems
- [ ] Rootkit and malware detection tools employed
- [ ] Disk encryption enabled for laptops and mobile devices
- [ ] Boot process secured (Secure Boot, TPM)
- [ ] Hardware security features utilized (TPU, SGX where relevant)
- [ ] Virtualization security configured (ESXi, Hyper-V, KVM hardening)
- [ ] Container runtime security configured (read-only roots, drop capabilities)
- [ ] Image scanning performed for vulnerabilities and misconfigurations
- [ ] Runtime security monitoring for containers (Falco, Trisomic)
- [ ] Orchestrator security configured (RBAC, network policies, PSPs)

### Secrets and Credential Management
- [ ] No hardcoded credentials in source code or configuration
- [ ] Secrets managed using dedicated vault (HashiCorp Vault, AWS Secrets Manager, etc.)
- [ ] Dynamic secrets used where possible (database credentials, API keys)
- [ ] Secret rotation automated and tested
- [ ] Access to secrets logged and monitored
- [ ] Least privilege applied to secret access
- [ ] Secrets encrypted at rest and in transit
- [ ] Secret splitting/sharing avoided where possible
- [ ] Environment-specific secret management
- [ ] Credential scavenging protections in place
- [ ] Memory scraping protections considered for high-value targets
- [ ] Key management lifecycle documented and followed
- [ ] Hardware Security Modules (HSM) considered for root of trust
- [ ] Code signing certificates properly managed and stored
- [ ] SSL/TLS certificates managed with automated renewal

## 5. Monitoring, Logging, and Incident Response

### Security Monitoring
- [ ] Security-relevant events logged and monitored
- [ ] Authentication successes and failures logged
- [ ] Authorization failures (access denied) logged
- [ ] Privileged access and elevation events logged
- [ ] New account creation and modification logged
- [ ] Password changes and resets logged
- [ ] Security policy changes logged
- [ ] System and application changes logged
- [ ] Network traffic anomalies detected and alerted
- [ ] Malware and intrusion detection alerts configured
- [ ] Data exfiltration attempts detected and alerted
- [ ] User behavior analytics (UBA) considered for anomaly detection
- [ ] Insider threat monitoring implemented where appropriate
- [ ] Alert fatigue managed through tuning and suppression
- [ ] Runbooks created for common security alerts
- [ ] Escalation paths defined for security incidents
- [ ] SOC or MDR service engaged where appropriate
- [ ] Threat intelligence feeds integrated into monitoring

### Logging and Audit Trails
- [ ] Centralized logging implemented for all systems and applications
- [ ] Logs include sufficient context for investigation (timestamps, user, source IP)
- [ ] Sensitive data excluded from logs (PII, passwords, tokens)
- [ ] Log integrity protected through write-once storage or signing
- [ ] Log retention compliant with legal and regulatory requirements
- [ ] Log tampering detected and alerted
- [ ] Time synchronization (NTP) configured across all systems
- [ ] Log formats standardized (JSON, CEF, LEEF) for parsing
- [ ] Log parsing and normalization implemented
- [ ] Log indexing and search capability provided
- [ ] Dashboard and visualization tools available for log analysis
- [ ] Regular log review conducted for anomalous activity
- [ ] Archive and retrieval procedures tested periodically
- [ ] Legal hold capability implemented for litigation support
- [ ] Cloud-native logging services used where appropriate (CloudWatch, Azure Monitor)

### Incident Response
- [ ] Incident response plan (IRP) documented and approved
- [ ] Roles and responsibilities clearly defined in IRP
- [ ] Communication plan internal and external defined
- [ ] Evidence collection and preservation procedures documented
- [ ] Forensic readiness maintained (tools, access, skills)
- [ ] Malware analysis capability available or contracted
- [ ] Incident classification and prioritization system defined
- [ ] Escalation matrix with contacts and response times
- [ ] Legal and regulatory notification requirements understood
- [ ] Public relations and customer communication plans prepared
- [ ] Tabletop exercises conducted biannually minimum
- [ ] Post-incident review process defined (blameless postmortem)
- [ ] Lessons learned incorporated into controls and procedures
- [ ] Cyber insurance policy reviewed and understood
- [ ] Third-party breach notification procedures established
- [ ] Ransomware response plan developed and tested
- [ ] Insider threat response procedures established
- [ ] Supply chain compromise response planned

### Vulnerability Management
- [ ] Vulnerability scanning performed regularly (network, host, application)
- [ ] Penetration testing conducted annually or per major release
- [ ] Red team/blue team exercises conducted periodically
- [ ] Bug bounty program or responsible disclosure process established
- [ ] Vulnerability remediation tracked with SLAs based on severity
- [ ] False positive rate monitored and tuning performed
- [ ] Asset inventory maintained for accurate scanning coverage
- [ ] Configuration scanning performed for hardening compliance
- [ ] Database Activity Monitoring (DAM) implemented for sensitive data
- [ ] File integrity monitoring (FIM) deployed on critical systems
- [ ] Web Application Firewall (WAF) logs reviewed for attack attempts
- [ ] Common Vulnerabilities and Exposures (CVEs) tracked for exposures
- [ ] Zero-day threat monitoring and response procedures defined
- [ ] Virtual patching capabilities evaluated for legacy systems
- [ ] Application Security as a Service (ASaaS) considered

## 6. Third-Party and Supply Chain Security

### Vendor Management
- [ ] Security assessments conducted for critical vendors
- [ ] Right to audit clause included in contracts where appropriate
- [ ] Service Organization Control (SOC) reports reviewed
- [ ] Independent security assessments commissioned for high-risk vendors
- [ ] Security requirements included in RFPs and contracts
- [ ] Data processing agreements (DPAs) reviewed for compliance
- [ ] Sub-notification procedures established for vendor breaches
- [ ] Data destruction or return certified at contract end
- [ ] Insurance requirements verified (cyber, E&O)
- [ ] Exit strategies defined for critical vendor relationships
- [ ] Supply chain risk assessments performed for critical components
- [ ] Component integrity verified (code signing, hashes)
- [ ] Supplier security posture monitored over time
- [ ] Geopolitical risks considered in vendor selection
- [ ] Single point of failure dependencies identified and mitigated

### Open Source Software
- [ ] Open source inventory maintained (SBOM)
- [ ] License compliance verified for all components
- [ ] Security vulnerabilities monitored in OSS dependencies
- [ ] Update process established for critical OSS components
- [ ] Contribution to critical OSS projects considered
- [ ] Security audits performed on critical OSS dependencies
- [ ] Internal approval process for new OSS components
- [ ] Approved and prohibited OSS lists maintained
- [ ] Ossification risks evaluated (abandoned projects)
- [ ] Contributor legitimacy verified for security-critical OSS
- [ ] Build processes verify integrity of downloaded OSS
- [ ] Binary integrity checked where source not available
- [ ] OSS license obligations fulfilled (attribution, source availability)

### Cloud and Third-Party Services
- [ ] Shared responsibility model understood for cloud services
- [ ] Cloud security posture management (CSPM) tools deployed
- [ ] Infrastructure as Code (IaC) scanned for misconfigurations
- [ ] CloudTrail or equivalent logging enabled and monitored
- [ ] Identity and Access Management (IAM) reviewed for least privilege
- [ ] Storage bucket permissions validated (no public buckets unintentionally)
- [ ] Serverless function permissions minimized
- [ ] Container registry vulnerabilities scanned
- [ ] API gateways configured with security policies
- [ ] Service mesh security policies enforced
- [ ] Data transfer costs and security considered for multi-region
- [ ] Compliance certifications reviewed for cloud providers (SOC 2, ISO, etc.)
- [ ] Data residency controls configured for regional requirements
- [ ] Encryption key management evaluated (bring your own key vs provider managed)
- [ ] Network controls reviewed (security groups, NACLs, VPC peering)
- [ ] Logging and monitoring enabled for all relevant services
- [ ] Resource tags used for cost allocation and security grouping
- [ ] Immutable infrastructure principles applied where possible
- [ ] Blueprint/templating used for consistent deployment
- [ ] Drift detection implemented for infrastructure compliance

## 7. Physical and Environmental Security

### Facilities Security
- [ ] Physical access controls implemented for data centers and offices
- [ ] Visitor management and escort procedures enforced
- [ ] Surveillance systems deployed and monitored
- [ ] Intrusion detection systems installed on perimeter
- [ ] Security guards or patrols utilized where appropriate
- [ ] Tailgating prevented through turnstiles or mantraps
- [ ] Asset tracking and inventory management implemented
- [ ] Secure disposal of electronic media (degaussing, shredding)
- [ ] Clean desk and clear screen policies enforced
- [ ] Removable media controls implemented (USB ports disabled/epoxy)
- [ ] Wireless network security verified (WPA2-Enterprise, segregation)
- [ ] Guest network isolated from internal networks
- [ ] Environmental monitoring (temperature, humidity, water detection)
- [ ] Fire suppression systems installed and maintained
- [ ] Uninterruptible Power Supply (UPS) and generator capacity adequate
- [ ] Physical security incidents reported and investigated
- [ ] Access logs reviewed regularly for anomalies
- [ ] Perimeter security maintained (fencing, barriers, lighting)
- [ ] Security awareness training includes physical security components
- [ ] Contractor and temporary worker access controlled

### Equipment Security
- [ ] Device encryption enabled for laptops and mobile devices
- [ ] Mobile Device Management (MDM) deployed for corporate devices
- [ ] Bring Your Own Device (BYOD) policy defined and enforced
- [ ] Remote wipe capability for lost or stolen devices
- [ ] Screen lock timeout configured (5 minutes or less)
- [ ] Biometric authentication evaluated for device access
- [ ] Port control implemented (USB, Thunderbolt, etc.)
- [ ] Camera and microphone access monitored and controlled
- [ ] Hardware theft detection and recovery services considered
- [ ] Asset tagging and tracking implemented
- [ ] Endpoint Detection and Response (EDR) deployed
- [ ] Antivirus/anti-malware kept current with behavioral detection
- [ ] Application control/whitelisting implemented where feasible
- [ ] Memory exploitation mitigations enabled (DEP, ASLR)
- [ ] Exploit prevention tools utilized where appropriate
- [ ] Boot process verified (Secure Boot, measured boot)
- [ ] Firmware updates applied regularly for devices
- [ ] Hardware security modules used where appropriate for keys
- [ ] Trusted Platform Module (TPM) utilized for device integrity
- [ ] Secure enclaves considered for high-value key operations
- [ ] Virtualization security hardened for hosted workloads
- [ ] Container escape protections implemented
- [ ] Firmware integrity verified at boot
- [ ] JTAG and debug ports disabled in production hardware

## 8. Compliance and Governance

### Regulatory Compliance
- [ ] Applicable regulations identified (GDPR, CCPA, HIPAA, PCI-DSS, SOX, etc.)
- [ ] Data Protection Impact Assessment (DPIA) conducted where required
- [ ] Records of processing activities (ROPA) maintained
- [ ] Privacy notices and consent mechanisms implemented
- [ ] Data subject request (DSR) process established and tested
- [ ] Data breach notification procedures defined and tested
- [ ] International data transfer mechanisms evaluated (SCCs, BCRs)
- [ ] Data localization requirements understood and addressed
- [ ] Employee monitoring policies compliant with local laws
- [ ] Video surveillance compliance verified
- [ ] Biometric data handling compliant with regulations
- [ ] Credit card handling compliant with PCI-DSS if applicable
- [ ] Health information handling compliant with HIPAA if applicable
- [ ] Financial reporting controls compliant with SOX if applicable
- [ ] Export control regulations understood (EAR, ITAR)
- [ ] Sanctions screening implemented where applicable
- [ ] Anti-bribery and corruption controls in place (FCPA, UK Bribery Act)
- [ ] Modern slavery statement published where required
- [ ] Environmental, social, and governance (ESG) reporting considered

### Internal Policies and Standards
- [ ] Information Security Policy reviewed and updated annually
- [ ] Acceptable Use Policy (AUP) communicated and acknowledged
- [ ] Data Classification and Handling Standard defined
- [ ] Encryption Standard defined and implemented
- [ ] Access Control Standard defined and implemented
- [ ] Incident Response Plan reviewed and tested annually
- [ ] Business Continuity and Disaster Recovery Plan validated
- [ ] Vulnerability Management Procedure defined
- [ ] Patch Management Procedure documented
- [ ] Security Awareness Training Program established
- [ ] Third-Party Risk Management Program established
- [ ] Software Development Lifecycle (SDL) integrated with security
- [ ] Change Management Process includes security review
- [ ] Configuration Management Database (CMDB) maintained
- [ ] Asset Management Program includes security considerations
- [ ] Records Retention Policy includes security logs and evidence
- [ ] Legal Hold Procedure established for litigation readiness
- [ ] Audit and Assessment Cooperation Process defined
- [ ] Metrics and Reporting Framework established for security
- [ ] Budget allocation process includes security considerations
- [ ] Risk assessment methodology documented and applied
- [ ] Executive reporting on security posture regularized
- [ ] Board-level oversight of cybersecurity established

### Security Awareness and Training
- [ ] Role-based security training provided (developers, admins, users)
- [ ] Phishing simulation and training conducted quarterly minimum
- [ ] Password hygiene and management training provided
- [ ] Data handling and classification training conducted
- [ ] Social engineering awareness training provided
- [ ] Secure coding practices training for developers
- [ ] Privileged user training conducted annually
- [ ] Executive security briefings provided
- [ ] Contractor and vendor security requirements communicated
- [ ] Training completion tracked and enforced
- [ ] Knowledge assessments performed post-training
- [ ] Security champions program established in development teams
- [ ] Security newsletters and updates distributed regularly
- [ ] Incident reporting procedures widely communicated
- [ ] Clean desk and clear screen policies reinforced
- [ ] Mobile device security guidelines provided
- [ ] Travel security advisories provided for international travel
- [ ] Work-from-home security guidelines established
- [ ] Incident reporting made easy and anonymous where possible
- [ ] Recognition program for security-conscious behavior
- [ ] Lessons learned from incidents incorporated into training

---
*Assessment Completed By:* _________________________
*Title:* _________________________
*Date:* _________________________

*Reviewed By:* _________________________
*Title:* _________________________
*Date:* _________________________

*Next Review Due:* _________________________ (or per significant change)