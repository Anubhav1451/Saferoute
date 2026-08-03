# Code Review Checklist

## Functional Correctness
- [ ] Does the code correctly implement the requirements?
- [ ] Are edge cases handled properly?
- [ ] Are error conditions handled appropriately?
- [ ] Is the logic correct and easy to follow?
- [ ] Are there any obvious bugs or logical errors?

## Code Quality & Maintainability
- [ ] Is the code readable and well-formatted?
- [ ] Are variable and function names descriptive and consistent?
- [ ] Are functions/methods focused and do they have a single responsibility?
- [ ] Is the code DRY (Don't Repeat Yourself)?
- [ ] Are there any commented-out code or debug statements?
- [ ] Is the code following the project's coding standards and style guide?

## Security
- [ ] Are inputs properly validated and sanitized?
- [ ] Are there any potential security vulnerabilities (SQL injection, XSS, etc.)?
- [ ] Are sensitive data handled correctly (encryption, hashing)?
- [ ] Are authentication and authorization checks in place where needed?
- [ ] Are dependencies checked for known vulnerabilities?

## Performance
- [ ] Are there any obvious performance bottlenecks?
- [ ] Are database queries efficient (proper indexing, N+1 queries)?
- [ ] Are resources properly closed/re resources properly closed/released (files, database connections)?
- [ ] Are loops and iterations optimized?
- [ ] Is caching used appropriately where beneficial?

## Testing
- [ ] Are there unit tests for new functionality?
- [ ] Do existing tests still pass?
- [ ] Are tests readable and maintainable?
- [ ] Are edge cases covered in tests?
- [ ] Is test coverage adequate for changed/added code?

## Documentation
- [ ] Is complex logic adequately commented?
- [ ] Are public APIs documented?
- [ ] Are there any TODOs or FIXMEs that need addressing?
- [ ] Is the README or documentation updated if needed?

## Dependencies & Imports
- [ ] Are imports necessary and from correct locations?
- [ ] Are there any unused imports?
- [ ] Are external dependencies properly managed?
- [ ] Are version constraints appropriate?

## Additional Considerations
- [ ] Are there any breaking changes that need documentation?
- [ ] Is backward compatibility maintained where required?
- [ ] Are configuration changes documented?
- [ ] Are there any licensing concerns with new dependencies?