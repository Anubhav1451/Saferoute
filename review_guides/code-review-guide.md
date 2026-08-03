# Code Review Guide

This checklist provides a comprehensive framework for reviewing code quality, maintainability, adherence to standards, and best practices. Use this guide to ensure consistent, thorough, and effective code reviews across all projects and teams.

## How to Use This Guide

1. Review the code changes in the context of the overall codebase
2. Consider both immediate correctness and long-term maintainability
3. Check each item in the relevant categories below
4. Provide specific, actionable feedback with examples
5. Focus on helping the author improve their code, not just finding faults
6. Balance thoroughness with efficiency - don't let perfect be the enemy of good
7. Follow up on agreed-upon changes in subsequent reviews

## Review Categories

### 1. Correctness & Functionality
- [ ] Does the code correctly implement the intended functionality?
- [ ] Are all edge cases and error conditions handled appropriately?
- [ ] Does the code handle null/undefined/invalid inputs gracefully?
- [ ] Are boundary conditions tested and handled correctly?
- [ ] Are race conditions and concurrency issues addressed where relevant?
- [ ] Are mathematical calculations correct (precision, rounding, overflow)?
- [ ] Are external API calls handled correctly (timeouts, retries, error responses)?
- [ ] Is the logic consistent with requirements and specifications?
- [ ] Are there any obvious bugs or logical errors?
- [ ] Does the code produce the expected output for given inputs?

### 2. Readability & Clarity
- [ ] Is the code easy to read and understand at a glance?
- [ ] Are variable, function, and class names descriptive and meaningful?
- [ ] Is the code formatted consistently with project standards?
- [ ] Are comments useful and up-to-date (explaining why, not what)?
- [ ] Is the code structure logical and easy to follow?
- [ ] Are complex operations broken down into smaller, well-named functions?
- [ ] Is nesting depth reasonable (avoiding excessive indentation)?
- [ ] Are magic numbers and strings replaced with named constants?
- [ ] Is the code free of commented-out or dead code?
- [ ] Are similar patterns implemented consistently throughout?

### 3. Maintainability & Extensibility
- [ ] Is the code easy to modify and extend without breaking existing functionality?
- [ ] Does the code follow the Single Responsibility Principle?
- [ ] Are concerns properly separated (layers, modules, components)?
- [ ] Is coupling between components minimized and well-defined?
- [ ] Is cohesion high within modules and classes?
- [ ] Are inheritance and polymorphism used appropriately?
- [ ] Are interfaces and abstractions used where beneficial?
- [ ] Is the code testable (loose coupling, dependency injection)?
- [ ] Would a new developer be able to understand and modify this code easily?
- [ ] Are design patterns applied appropriately and consistently?

### 4. Performance & Efficiency
- [ ] Are there any obvious performance bottlenecks or inefficiencies?
- [ ] Are loops and iterations optimized (avoiding unnecessary work inside loops)?
- [ ] Are data structures chosen appropriately for the use case (lookup, insertion, deletion patterns)?
- [ ] Are database queries efficient (proper indexing, avoiding N+1 problems)?
- [ ] Are expensive operations cached where appropriate?
- [ ] Are resource-intensive operations asynchronous where beneficial?
- [ ] Are lazy loading/eager loading patterns used appropriately?
- [ ] Are string concatenation operations efficient (using builders where appropriate)?
- [ ] Are object creation patterns efficient (avoiding unnecessary instantiation)?
- [ ] Are algorithms chosen appropriately for the expected data sizes?

### 5. Security Considerations
- [ ] Are input validation and output encoding performed correctly?
- [ ] Are authentication and authorization checks in place where needed?
- [ ] Are sensitive data handling practices followed (encryption, masking)?
- [ ] Are common vulnerabilities avoided (SQL injection, XSS, CSRF, etc.)?
- [ ] Are secrets and credentials handled properly (not hard-coded)?
- [ ] Are file operations protected against path traversal attacks?
- [ ] Are deserialization vulnerabilities prevented?
- [ ] Are server-side validations performed for critical operations?
- [ ] Are rate limiting and abuse prevention considered where appropriate?
- [ ] Are security headers and protections used in web applications?

### 6. Testing & Testability
- [ ] Is the code easily testable (loose coupling, dependency injection)?
- [ ] Are unit tests provided for new functionality?
- [ ] Do existing tests still pass with the changes?
- [ ] Are edge cases and error conditions covered in tests?
- [ ] Are tests readable, maintainable, and focused on single responsibilities?
- [ ] Are mocks and stubs used appropriately in tests?
- [ ] Are tests independent and able to run in any order?
- [ ] Is code coverage adequate for new and changed code?
- [ ] Are integration and end-to-end tests considered where appropriate?
- [ ] Are test names descriptive and following team conventions?

### 7. Documentation & Comments
- [ ] Is complex logic adequately explained with comments?
- [ ] Are public APIs and interfaces properly documented?
- [ ] Are tricky workarounds or hacks documented with justification?
- [ ] Are architectural decisions and rationales documented?
- [ ] Are TODOs and FIXMEs used appropriately and tracked?
- [ ] Is outdated or misleading comments removed?
- [ ] Are public methods and classes documented with parameter and return value descriptions?
- [ ] Are code examples provided where helpful?
- [ ] Are spelling and grammar correct in comments and documentation?
- [ ] Is documentation kept up-to-date with code changes?

### 8. Consistency & Standards Compliance
- [ ] Does the code follow the project's coding standards and style guide?
- [ ] Are naming conventions followed consistently (camelCase, PascalCase, snake_case)?
- [ ] Are import/include statements organized and sorted consistently?
- [ ] Are braces, parentheses, and spacing used consistently?
- [ ] Are line lengths kept within reasonable limits?
- [ ] Are language-specific idioms and best practices followed?
- [ ] Are deprecated APIs and functions avoided?
- [ ] Are licensing headers present where required?
- [ ] Are file headers and metadata up-to-date?
- [ ] Are build and configuration files updated as needed?

### 9. Error Handling & Logging
- [ ] Are exceptions caught and handled appropriately?
- [ ] Are error messages informative for debugging but safe for production?
- [ ] Are exceptions logged at appropriate levels (debug, info, warn, error)?
- [ ] Are exceptions neither swallowed nor excessively logged (avoiding log spam)?
- [ ] Are resources properly cleaned up in error conditions (using finally, try-with-resources)?
- [ ] Are error codes and messages consistent and follow established patterns?
- [ ] Are exceptions neither overly generic nor overly specific?
- [ ] Are validation errors handled appropriately and communicated clearly?
- [ ] Are logging levels used appropriately (not overusing ERROR or WARN)?
- [ ] Is sensitive data avoided in log outputs?
- [ ] Are logging frameworks configured appropriately?

### 10. Dependencies & Imports
- [ ] Are external dependencies justified and necessary?
- [ ] Are dependency versions appropriate and up-to-date?
- [ ] Are transitive dependencies understood and acceptable?
- [ ] Are licensing implications of dependencies considered?
- [ ] Are unused imports and dependencies removed?
- [ ] Are imports organized and grouped logically?
- [ ] Are circular dependencies avoided?
- [ ] Are dependency conflicts resolved appropriately?
- [ ] Are native/platform-specific dependencies handled correctly?
- [ ] Are dependency management tools used properly (Maven, npm, pip, etc.)?

### 11. Code Duplication & Reuse
- [ ] Is duplicated code avoided through extraction and reuse?
- [ ] Are utility functions and classes created for common operations?
- [ ] Are design patterns used appropriately to avoid reinvention?
- [ ] Are similar implementations consolidated into shared components?
- [ ] Is the "Don't Repeat Yourself" (DRY) principle followed?
- [ ] Are template methods and strategy patterns used where appropriate?
- [ ] Are inheritance and composition used effectively for code reuse?
- [ ] Are code snippets from external sources properly attributed and licensed?
- [ ] Are generated code files marked appropriately and not manually edited?
- [ ] Are abstract classes and interfaces used to define common contracts?

### 12. Scalability & Architecture
- [ ] Does the code scale appropriately with increased load or data size?
- [ ] Are bottlenecks avoided in critical paths?
- [ ] Are stateless designs preferred where appropriate for horizontal scaling?
- [ ] Are shared resources managed correctly to avoid contention?
- [ ] Are asynchronous patterns used where beneficial for scalability?
- [ ] Are database connection pools used and configured appropriately?
- [ ] Are caching strategies considered and implemented where beneficial?
- [ ] Are message queues and asynchronous processing used appropriately?
- [ ] Are microservices boundaries respected where applicable?
- [ ] Are event-driven patterns used where beneficial?
- [ ] Are circuit breaker and bulkhead patterns used for resilience?

### 13. Language & Framework Specific
[Customize this section based on the specific programming language and framework being reviewed]

#### For Java/JVM:
- [ ] Are collections used appropriately (ArrayList vs LinkedList, HashMap vs TreeMap)?
- [ ] Are resources properly closed using try-with-resources?
- [ ] Are equals() and hashCode() overridden together when needed?
- [ ] Are immutable objects preferred where appropriate?
- [ ] Are streams and lambdas used effectively for collection operations?
- [ ] Are concurrent collections used appropriately in multi-threaded contexts?
- [ ] Are exceptions either checked or unchecked for appropriate reasons?
- [ ] Are annotations used correctly and not abused?
- [ ] Are serialization considerations addressed for Serializable classes?

#### For JavaScript/TypeScript:
- [ ] Are variables properly scoped (let/const vs var)?
- [ ] Are closures used correctly and memory leaks avoided?
- [ ] Are asynchronous operations handled properly (promises, async/await)?
- [ ] Are event listeners properly removed to prevent memory leaks?
- [ ] Are DOM manipulations batched for performance?
- [ ] Are type definitions accurate and up-to-date (TypeScript)?
- [ ] Are linter rules followed and warnings addressed?
- [ ] Are module imports organized and circular dependencies avoided?
- [ ] Are eval() and similar dangerous functions avoided?
- [ ] Are prototype modifications avoided unless absolutely necessary?

#### For Python:
- [ ] Are PEP 8 style guidelines followed?
- [ ] Are virtual environments and dependency management used properly?
- [ ] Are list comprehensions and generator expressions used appropriately?
- [ ] Are context managers used for resource management?
- [ ] Are exceptions either caught or declared appropriately?
- [ ] Are mutable default arguments avoided in function definitions?
- [ ] Are properties used appropriately instead of getter/setter methods?
- [ ] Are virtual environments and requirements.txt kept up-to-date?
- [ ] Are absolute imports preferred over relative imports?
- [ ] Are docstrings formatted consistently (Google, NumPy, Sphinx)?

#### For C#/.NET:
- [ ] Are naming conventions followed (PascalCase for public members)?
- [ ] Are properties used appropriately instead of public fields?
- [ ] Are null checks performed appropriately (using null-conditional operators)?
- [ ] Are LINQ queries used effectively and efficiently?
- [ ] Are async/await patterns used correctly for asynchronous operations?
- [ ] Are IDisposable implementations correct and used with using statements?
- [ ] Are events and delegates used appropriately to avoid memory leaks?
- [ ] Are extension methods used judiciously and placed in appropriate namespaces?
- [ ] Are immutable objects and records used where beneficial?
- [ ] Are exception filters used appropriately?

### 14. Technical Debt & Maintenance
- [ ] Is technical debt identified and documented where incurred?
- [ ] Are shortcuts and workarounds minimized and well-documented?
- [ ] Are future maintenance costs considered in implementation decisions?
- [ ] Are deprecated APIs and patterns avoided?
- [ ] Are upgrade paths considered for libraries and frameworks?
- [ ] Are monitoring and observability hooks included where beneficial?
- [ ] Are feature flags and toggles used appropriately for gradual rollouts?
- [ ] Are backward compatibility concerns addressed for public APIs?
- [ ] Are database migrations backward compatible where needed?
- [ ] Are feature toggles cleaned up after use?
- [ ] Are long-term maintenance costs considered in architecture decisions?

## Review Process

### Before the Review
- [ ] Ensure the code builds successfully
- [ ] Verify that automated tests pass
- [ ] Check that the changes are related to a single issue or feature
- [ ] Ensure the branch is up-to-date with the target branch
- [ ] Confirm that the code follows the definition of done

### During the Review
- [ ] Start with high-level understanding before diving into details
- [ ] Look for patterns rather than just individual issues
- [ ] Balance positive feedback with constructive criticism
- [ ] Ask questions rather than making assumptions
- [ ] Focus on the code, not the author
- [ ] Be specific with examples and suggestions
- [ ] Prioritize issues by impact and severity
- [ ] Consider the context and constraints of the change
- [ ] Look for opportunities to mentor and teach
- [ ] Respect the author's time and expertise

### After the Review
- [ ] Summarize key findings and required changes
- [ ] Clearly distinguish between blocking issues and suggestions
- [ ] Provide actionable feedback with specific examples
- [ ] Acknowledge what was done well
- [ ] Follow up on agreed-upon changes in subsequent iterations
- [ ] Close the review when all concerns are addressed
- [ ] Thank the author for their work and responsiveness

## Severity Guidelines for Findings

**Blocker**: Must be fixed before merging
- Breaks existing functionality
- Introduces security vulnerabilities
- Causes significant performance degradation
- Violates fundamental architectural principles

**Major**: Should be fixed before merging
- Affects code maintainability or readability
- Introduces technical debt that will be costly to remove later
- Misses obvious improvement opportunities
- Violates important coding standards

**Minor**: Nice to have, can be addressed in follow-up
- Minor style inconsistencies
- Suggested improvements for readability
- Minor refactoring opportunities
- Documentation enhancements

**Informational**: For awareness only
- Questions about design decisions
- Suggestions for future considerations
- Alternative approaches to consider
- General observations

## Review Checklist Summary

**Pull Request/Branch**: ________________________
**Author**: _________________________________
**Reviewer**: _______________________________
**Date**: _________________________________
**Lines Changed**: _______ additions, _______ deletions
**Files Changed**: _______

### Review Scope
☐ New Feature    ☐ Bug Fix    ☐ Refactoring    ☐ Documentation    ☐ Performance    ☐ Security

### Overall Code Quality Assessment
- [ ] Excellent (ready to merge as-is)
- [ ] Good (minor issues to address)
- [ ] Satisfactory (needs some improvements)
- [ ] Needs Work (significant issues to resolve)
- [ ] Unsatisfactory (major rework required)

### Findings Summary

**Blocker Issues (Must Fix):**
1. ________________________________________
2. ________________________________________

**Major Issues (Should Fix):**
1. ________________________________________
2. ________________________________________
3. ________________________________________

**Minor Issues (Nice to Fix):**
1. ________________________________________
2. ________________________________________
3. ________________________________________

**Positive Aspects / What Was Done Well:**
1. ________________________________________
2. ________________________________________
3. ________________________________________

### Reviewer Comments & Suggestions
________________________________________________________________________
________________________________________________________________________
________________________________________________________________________
________________________________________________________________________

### Action Items for Author
[ ] Address all blocker issues
[ ] Address all major issues  
[ ] Consider minor issues and suggestions
[ ] Update documentation as needed
[ ] Add/update tests for new functionality
[ ] Ensure all existing tests pass
[ ] Update version numbers if applicable
[ ] Prepare for re-review if significant changes made

### Reviewer Recommendation
☐ Approve and merge
☐ Approve with minor changes (can merge after fixes)
☐ Request changes (must fix and resubmit for review)
☐ Request major changes (significant rework needed)