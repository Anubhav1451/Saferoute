# Frontend Review Checklist

## UI/UX & Accessibility
- [ ] Is the UI responsive and mobile-friendly?
- [ ] Are accessibility guidelines followed (WCAG 2.1 AA)?
- [ ] Is color contrast sufficient for readability?
- [ ] Are interactive elements keyboard accessible?
- [ ] Are ARIA labels used appropriately?
- [ ] Are loading states and error states handled gracefully?
- [ ] Is the user experience intuitive and consistent?

## Code Quality & Maintainability
- [ ] Is the code following the project's coding standards?
- [ ] Are components/composables reusable and focused?
- [ ] Is state management implemented correctly?
- [ ] Are props and events properly typed/documented?
- [ ] Is code duplication minimized?
- [ ] Are custom hooks/utilities well-tested and documented?
- [ ] Are there any console warnings or errors?

## Performance
- [ ] Are images and assets optimized (sizes, formats)?
- [ ] Is lazy loading implemented for off-screen content?
- [ ] Are expensive computations debounced/throttled?
- [ ] Is CSS optimized (unused CSS removed, critical CSS inlined)?
- [ ] Are bundle sizes monitored and optimized?
- [ ] Are React/Vue/Svelte components optimized (memo, useMemo, useCallback)?
- [ ] Are network requests minimized and cached appropriately?

## State Management
- [ ] Is state properly normalized and structured?
- [ ] Are state updates immutable where required?
- [ ] Are selectors/memoized getters used for derived data?
- [ ] Are side effects properly cleaned up in useEffect/useWatch?
- [ ] Are state updates batched where beneficial?
- [ ] Is persisting state handled correctly (localStorage, cookies)?

## Data Handling & API Integration
- [ ] Are API requests properly handled (loading, error, success states)?
- [ ] Is data validation performed on incoming/outgoing data?
- [ ] Are API endpoints consumed correctly (methods, headers, params)?
- [ ] Is authentication handled properly (token storage, refresh)?
- [ ] Are file uploads/downloads handled securely?
- [ ] Are websockets/realtime connections managed properly?

## Testing & Quality
- [ ] Are unit tests covering components tested with appropriate coverage?
- [ ] Are user interactions tested (clicks, forms, navigation)?
- [ ] Are edge cases and error states tested?
- [ ] Are visual regression tests in place for critical UI?
- [ ] Are accessibility tests included?
- [ ] Are tests maintainable and not overly brittle?

## Security
- [ ] Is user input properly sanitized to prevent XSS?
- [ ] Are dangerous HTML/URLs properly sanitized?
- [ ] Are authentication tokens stored securely (HttpOnly cookies, secure storage)?
- [ ] Are CSRF protections in place where applicable?
- [ ] Are third-party scripts evaluated for security risks?
- [ ] Is sensitive data masked in UI (passwords, PII)?
- [ ] Are CSP headers considered and implemented?

## Build & Deployment
- [ ] Are environment variables properly managed?
- [ ] Are builds optimized for production (minification, tree shaking)?
- [ ] Are source maps handled appropriately for debugging?
- [ ] Are CDN configurations optimized for asset delivery?
- [ ] Are service workers configured correctly for PWAs?
- [ ] Are feature flags properly integrated for rollouts?