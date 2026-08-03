# Security Review Checklist

## Authentication & Authorization
- [ ] Is strong authentication implemented (multi-factor where appropriate)?
- [ ] Are passwords stored using strong, adaptive hashing algorithms (bcrypt, scrypt, Argon2)?
- [ ] Are password policies enforced (length, complexity, rotation)?
- [ ] Are session tokens secure (HttpOnly, Secure, SameSite flags)?
- [ ] Is session expiration and invalidation properly implemented?
- [ ] Are authorization checks performed at both API and UI levels?
- [ ] Is the principle of least privilege enforced for all users and services?
- [ ] Are role-based access controls (RBAC) properly implemented?
- [ ] Are API keys and service credentials rotated regularly?
- [ ] Are OAuth/OIDC implementations following best practices?

## Data Protection
- [ ] Is sensitive data encrypted at rest using industry-standard algorithms?
- [ ] Are encryption keys managed securely (KMS, HSM, or equivalent)?
- [ ] Is data in transit encrypted using TLS 1.2+?
- [ ] Are weak cipher suites and protocols disabled (SSLv3, TLS 1.0, RC4)?
- [ ] Are secrets managed properly (not in code, config files, or logs)?
- [ ] Is PII minimized and handled according to privacy regulations?
- [ ] Are data backups encrypted?
- [ ] Are encryption algorithms and key lengths appropriate for data sensitivity?

## Input Validation & Output Encoding
- [ ] Is all input validated (type, length, format, range)?
- [ ] Is output properly encoded for context (HTML, JS, SQL, etc.)?
- [ ] Are SQL/NoSQL injection prevented through parameterized queries?
- [ ] Are XSS vulnerabilities prevented through proper output encoding?
- [ ] Are path traversal attacks prevented through input validation?
- [ ] Are file uploads validated (type, size, content) and scanned for malware?
- [ ] Are deserialization vulnerabilities avoided or mitigated?
- [ ] Are XML external entity (XXE) attacks prevented?
- [ ] Are command injection vulnerabilities prevented?

## Network & Infrastructure Security
- [ ] Are networks properly segmented (DMZ, private, public subnets)?
- [ ] Are firewalls configured with least privilege principles?
- [ ] Are intrusion detection/prevention systems (IDS/IPS) in place?
- [ ] Are DDoS protection measures implemented?
- [ ] Are insecure services disabled (telnet, FTP, etc.)?
- [ ] Are unnecessary ports closed?
- [ ] Are VPNs used for remote access where appropriate?
- [ ] Are wireless networks secured with WPA2/WPA3?
- [ ] Are default credentials changed on all devices?

## Logging & Monitoring
- [ ] Are security-relevant events logged (logins, access changes, failures)?
- [ ] Are logs stored securely and protected from tampering?
- [ ] Are log retention periods compliant with regulatory requirements?
- [ ] Are security alerts generated and monitored in real-time?
- [ ] Are SIEM solutions used for correlation and analysis?
- [ ] Are penetration tests and vulnerability scans conducted regularly?
- [ ] Are security patches applied in a timely manner?
- [ ] Are vulnerability disclosure processes established?

## Application Security
- [ ] Are dependencies checked for known vulnerabilities (SCA)?
- [ ] Is the application protected against common web vulnerabilities (OWASP Top 10)?
- [ ] Are security headers implemented (CSP, HSTS, X-Frame-Options, etc.)?
- [ ] Is clickjacking prevented?
- [ ] Are HTTP methods restricted appropriately?
- [ ] Are error messages generic and not leaking sensitive information?
- [ ] Are file permissions set appropriately (least privilege)?
- [ ] Are debug modes disabled in production?
- [ ] Are third-party integrations security-reviewed?

## API Security
- [ ] Are APIs authenticated and authorized properly?
- [ ] Is rate limiting implemented to prevent abuse?
- [ ] Is input validation performed on all API parameters?
- [ ] Are API responses stripped of sensitive data?
- [ ] Are API versions managed and deprecated securely?
- [ ] Are API endpoints documented with security considerations?
- [ ] Are webhooks secured with signature validation?
- [ ] Are GraphQL queries protected against excessive depth/complexity?

## Compliance & Governance
- [ ] Are relevant compliance requirements met (GDPR, HIPAA, PCI-DSS, etc.)?
- [ ] Are data processing agreements in place with third parties?
- [ ] Are privacy impact assessments conducted for new features?
- [ ] Are data retention and deletion policies implemented?
- [ ] Are access reviews conducted periodically?
- [ ] Are security policies and procedures documented and reviewed?
- [ ] Are security awareness trainings conducted regularly?
- [ ] Are incident response plans tested and updated?