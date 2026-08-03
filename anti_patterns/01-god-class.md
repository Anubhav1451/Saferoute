# God Class Anti-Pattern

## Description
The God Class (also known as God Object or Monster Object) is an anti-pattern where a single class knows too much or does too much. It violates the Single Responsibility Principle by having too many responsibilities, making it overly complex, difficult to maintain, and prone to bugs.

## Characteristics
- A class with too many methods and/or attributes
- High coupling with many other classes
- Low cohesion - the class does many unrelated things
- Difficult to test due to numerous dependencies and complex interactions
- Violates SOLID principles, particularly Single Responsibility Principle
- Often becomes a bottleneck for changes and development
- Makes code difficult to understand and navigate
- Tends to accumulate functionality over time without proper refactoring
- Frequently modified by many different developers for different reasons
- High cyclomatic complexity due to numerous conditional branches
- Large number of instance variables representing different concepts
- Methods often have long parameter lists
- Difficult to extend or modify without introducing bugs
- Often contains duplicated code that should be moved to other classes
- Poor encapsulation with too much internal state exposed

## Root Causes
- Lack of adherence to object-oriented design principles
- Insufficient refactoring during development
- Pressure to add features quickly without considering design
- Inexperienced developers not recognizing when a class is becoming too large
- Failure to decompose complex functionality into smaller, focused classes
- Using inheritance poorly, leading to bloated base classes
- Not applying design patterns appropriately
- Inadequate code reviews that fail to identify growing complexity
- Lack of architectural guidelines or enforcement
- Technical debt accumulation without allocation time for refactoring
- Misunderstanding of encapsulation leading to god-like objects
- Evolution of the system without corresponding architectural evolution

## Impact on System
- Increased maintenance costs and effort
- Higher defect density due to complexity
- Difficulty in onboarding new team members
- Slower development velocity due to merge conflicts and coordination
- Increased risk when making changes
- Difficult to test thoroughly, leading to lower test coverage
- Reduced reusability of code
- Hinders parallel development efforts
- Makes performance optimization challenging
- Complicates debugging and troubleshooting
- Reduces system flexibility and adaptability
- Increases cognitive load on developers
- Can become a single point of failure in terms of knowledge
- Makes it difficult to apply modern architectural approaches
- Impedes adoption of microservices or other distributed architectures

## Examples

### Bad Example (God Class)
```java
public class UserService {  // God Class - does too many things
    // User management fields
    private List<User> users;
    private Map<String, User> userMap;
    
    // Authentication fields
    private PasswordEncoder passwordEncoder;
    private SessionManager sessionManager;
    
    // Notification fields
    private EmailService emailService;
    private SMSService smsService;
    private NotificationQueue notificationQueue;
    
    // Reporting fields
    private ReportGenerator reportGenerator;
    private AnalyticsService analyticsService;
    
    // Payment fields
    private PaymentProcessor paymentProcessor;
    private InvoiceGenerator invoiceGenerator;
    
    // Preferences fields
    private PreferenceService preferenceService;
    
    // Security fields
    private AuditLogger auditLogger;
    private PermissionChecker permissionChecker;
    
    // Constructor with too many dependencies
    public UserService(List<User> users, PasswordEncoder passwordEncoder,
                      SessionManager sessionManager, EmailService emailService,
                      SMSService smsService, NotificationQueue notificationQueue,
                      ReportGenerator reportGenerator, AnalyticsService analyticsService,
                      PaymentProcessor paymentProcessor, InvoiceGenerator invoiceGenerator,
                      PreferenceService preferenceService, AuditLogger auditLogger,
                      PermissionChecker permissionChecker) {
        this.users = users;
        this.userMap = new HashMap<>();
        for (User user : users) {
            userMap.put(user.getId(), user);
        }
        this.passwordEncoder = passwordEncoder;
        this.sessionManager = sessionManager;
        this.emailService = emailService;
        this.smsService = smsService;
        this.notificationQueue = notificationQueue;
        this.reportGenerator = reportGenerator;
        this.analyticsService = analyticsService;
        this.paymentProcessor = paymentProcessor;
        this.invoiceGenerator = invoiceGenerator;
        this.preferenceService = preferenceService;
        this.auditLogger = auditLogger;
        this.permissionChecker = permissionChecker;
    }
    
    // User management methods (too many responsibilities)
    public User createUser(String username, String email, String password) { /* ... */ }
    public User getUserById(String userId) { /* ... */ }
    public User getUserByUsername(String username) { /* ... */ }
    public List<User> getAllUsers() { /* ... */ }
    public User updateUser(String userId, String username, String email) { /* ... */ }
    public boolean deleteUser(String userId) { /* ... */ }
    public boolean userExists(String userId) { /* ... */ }
    public boolean userExistsByUsername(String username) { /* ... */ }
    public void bulkImportUsers(List<User> newUsers) { /* ... */ }
    public void bulkDeleteUsers(List<String> userIds) { /* ... */ }
    public List<User> searchUsersByCriteria(Map<String, Object> criteria) { /* ... */ }
    
    // Authentication methods (should be in separate AuthService)
    public boolean authenticate(String username, String password) { /* ... */ }
    public String login(String username, String password) { /* ... */ }
    public void logout(String sessionId) { /* ... */ }
    public boolean validateSession(String sessionId) { /* ... */ }
    public String refreshToken(String refreshToken) { /* ... */ }
    public void forcePasswordReset(String userId) { /* ... */ }
    public boolean changePassword(String userId, String oldPassword, String newPassword) { /* ... */ }
    public void lockAccount(String userId) { /* ... */ }
    public void unlockAccount(String userId) { /* ... */ }
    
    // Notification methods (should be in NotificationService)
    public void sendWelcomeEmail(User user) { /* ... */ }
    public void sendPasswordResetEmail(User user, String token) { /* ... */ }
    public void sendAccountLockedNotification(User user) { /* ... */ }
    public void sendSMSNotification(String phoneNumber, String message) { /* ... */ }
    public void queueNotification(User user, NotificationType type, Object data) { /* ... */ }
    public void sendWelcomeSMS(User user) { /* ... */ }
    public void sendUsageReportEmail(User user, Report report) { /* ... */ }
    
    // Reporting methods (should be in ReportingService)
    public Report generateUserActivityReport(String userId, Date startDate, Date endDate) { /* ... */ }
    public Report generateSystemUsageReport(Date startDate, Date endDate) { /* ... */ }
    public void scheduleDailyReports() { /* ... */ }
    public void exportReportToPDF(Report report, OutputStream outputStream) { /* ... */ }
    public void exportReportToCSV(Report report, OutputStream outputStream) { /* ... */ }
    
    // Payment methods (should be in PaymentService)
    public boolean processPayment(String userId, double amount, PaymentMethod method) { /* ... */ }
    public String createInvoice(User user, List<LineItem> items) { /* ... */ }
    public boolean processRefund(String paymentId, double amount) { /* ... */ }
    public Transaction getTransaction(String transactionId) { /* ... */ }
    public List<Transaction> getUserTransactions(String userId) { /* ... */ }
    public double calculateTax(double amount, String taxRegion) { /* ... */ }
    public void applyDiscount(String userId, DiscountCode code) { /* ... */ }
    
    // Preference methods (should be in PreferenceService)
    public UserPreferences getUserPreferences(String userId) { /* ... */ }
    public void updateUserPreference(String userId, String key, String value) { /* ... */ }
    public void resetUserPreferencesToDefault(String userId) { /* ... */ }
    public Map<String, String> getAllUserPreferences(String userId) { /* ... */ }
    public void bulkUpdateUserPreferences(List<String> userIds, String key, String value) { /* ... */ }
    
    // Security methods (should be in SecurityService)
    public void logAccess(String userId, String resource, String action) { /* ... */ }
    public boolean checkPermission(String userId, String permission) { /* ... */ }
    public List<String> getUserPermissions(String userId) { /* ... */ }
    public void grantPermission(String userId, String permission) { /* ... */ }
    public void revokePermission(String userId, String permission) { /* ... */ }
    public boolean isAdmin(String userId) { /* ... */ }
    public void promoteToAdmin(String userId) { /* ... */ }
    public void demoteFromAdmin(String userId) { /* ... */ }
    public boolean validateInput(String input, ValidationRule rule) { /* ... */ }
    public String sanitizeInput(String input) { /* ... */ }
    
    // Utility methods that don't belong here
    public String formatDate(Date date, String format) { /* ... */ }
    public String maskCreditCard(String cardNumber) { /* ... */ }
    public boolean isValidEmail(String email) { /* ... */ }
    public String generateRandomPassword(int length) { /* ... */ }
    public String calculateMD5(String input) { /* ... */ }
    public String base64Encode(byte[] data) { /* ... */ }
    public byte[] base64Decode(String encoded) { /* ... */ }
    public String jsonToString(Object object) { /* ... */ }
    public Object stringToJson(String json, Class<?> clazz) { /* ... */ }
    public String truncateString(String input, int maxLength) { /* ... */ }
    public String capitalizeFirstLetter(String input) { /* ... */ }
}
```

### Good Example (Refactored)
```java
// UserManagementService - handles only user CRUD operations
@Service
public class UserManagementService {
    private final UserRepository userRepository;
    private final UserMapper userMapper;
    
    public UserManagementService(UserRepository userRepository, UserMapper userMapper) {
        this.userRepository = userRepository;
        this.userMapper = userMapper;
    }
    
    public UserDto createUser(CreateUserDto createUserDto) {
        User user = userMapper.toEntity(createUserDto);
        return userMapper.toDto(userRepository.save(user));
    }
    
    public UserDto getUserById(String userId) {
        return userRepository.findById(userId)
                .map(userMapper::toDto)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
    }
    
    public List<UserDto> getAllUsers(Pageable pageable) {
        return userRepository.findAll(pageable)
                .stream()
                .map(userMapper::toDto)
                .collect(Collectors.toList());
    }
    
    public UserDto updateUser(String userId, UpdateUserDto updateUserDto) {
        User existingUser = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        userMapper.updateEntityFromDto(updateUserDto, existingUser);
        return userMapper.toDto(userRepository.save(existingUser));
    }
    
    public void deleteUser(String userId) {
        if (!userRepository.existsById(userId)) {
            throw new EntityNotFoundException("User not found");
        }
        userRepository.deleteById(userId);
    }
    
    public boolean userExists(String userId) {
        return userRepository.existsById(userId);
    }
    
    public List<UserDto> searchUsers(UserSearchCriteria criteria) {
        return userRepository.search(criteria)
                .stream()
                .map(userMapper::toDto)
                .collect(Collectors.toList());
    }
}

// AuthenticationService - handles only authentication concerns
@Service
public class AuthenticationService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final SessionManager sessionManager;
    private final TokenService tokenService;
    
    public AuthenticationService(UserRepository userRepository, 
                                PasswordEncoder passwordEncoder,
                                SessionManager sessionManager,
                                TokenService tokenService) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.sessionManager = sessionManager;
        this.tokenService = tokenService;
    }
    
    public AuthResponse login(LoginRequest loginRequest) {
        User user = userRepository.findByUsername(loginRequest.getUsername())
                .orElseThrow(() -> new InvalidCredentialsException("Invalid credentials"));
        
        if (!passwordEncoder.matches(loginRequest.getPassword(), user.getPassword())) {
            throw new InvalidCredentialsException("Invalid credentials");
        }
        
        String sessionId = sessionManager.createSession(user.getId());
        String accessToken = tokenService.generateAccessToken(user.getId());
        String refreshToken = tokenService.generateRefreshToken(user.getId());
        
        return new AuthResponse(sessionId, accessToken, refreshToken);
    }
    
    public void logout(String sessionId) {
        sessionManager.invalidateSession(sessionId);
    }
    
    public boolean validateSession(String sessionId) {
        return sessionManager.isValid(sessionId);
    }
    
    public String refreshAccessToken(String refreshToken) {
        // Validate refresh token and generate new access token
        return tokenService.refreshAccessToken(refreshToken);
    }
    
    public void forcePasswordReset(String userId) {
        // Force password reset at next login
        userRepository.forcePasswordResetFlag(userId, true);
    }
    
    public boolean changePassword(String userId, String oldPassword, String newPassword) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        
        if (!passwordEncoder.matches(oldPassword, user.getPassword())) {
            return false;
        }
        
        user.setPassword(passwordEncoder.encode(newPassword));
        userRepository.save(user);
        return true;
    }
    
    public void lockAccount(String userId) {
        userRepository.setAccountLocked(userId, true);
    }
    
    public void unlockAccount(String userId) {
        userRepository.setAccountLocked(userId, false);
    }
}

// NotificationService - handles only notification concerns
@Service
public class NotificationService {
    private final EmailService emailService;
    private final SMSService smsService;
    private final NotificationQueue notificationQueue;
    private final UserRepository userRepository;
    
    public NotificationService(EmailService emailService,
                              SMSService smsService,
                              NotificationQueue notificationQueue,
                              UserRepository userRepository) {
        this.emailService = emailService;
        this.smsService = smsService;
        this.notificationQueue = notificationQueue;
        this.userRepository = userRepository;
    }
    
    public void sendWelcomeEmail(String userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        emailService.sendEmail(user.getEmail(), "Welcome!", 
                "Welcome to our service, " + user.getFirstName() + "!");
    }
    
    public void sendPasswordResetEmail(String userId, String resetToken) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        emailService.sendEmail(user.getEmail(), "Password Reset Request",
                "Click here to reset your password: https://example.com/reset?token=" + resetToken);
    }
    
    public void sendAccountLockedNotification(String userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        // Implementation...
    }
    
    public void sendSMSNotification(String phoneNumber, String message) {
        smsService.sendSMS(phoneNumber, message);
    }
    
    public void queueNotification(String userId, NotificationType type, Object data) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        notificationQueue.add(new Notification(user.getId(), type, data));
    }
    
    // Other notification methods...
}

// ReportService - handles only reporting concerns
@Service
public class ReportService {
    private final ReportGenerator reportGenerator;
    private final UserRepository userRepository;
    private final AnalyticsService analyticsService;
    
    public ReportService(ReportGenerator reportGenerator,
                        UserRepository userRepository,
                        AnalyticsService analyticsService) {
        this.reportGenerator = reportGenerator;
        this.userRepository = userRepository;
        this.analyticsService = analyticsService;
    }
    
    public Report generateUserActivityReport(String userId, Date startDate, Date endDate) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        return reportGenerator.generateUserActivityReport(user, startDate, endDate);
    }
    
    public Report generateSystemUsageReport(Date startDate, Date endDate) {
        return reportGenerator.generateSystemUsageReport(startDate, endDate);
    }
    
    public void scheduleDailyReports() {
        // Implementation...
    }
    
    public void exportReportToPDF(Report report, OutputStream outputStream) {
        reportGenerator.exportToPDF(report, outputStream);
    }
    
    public void exportReportToCSV(Report report, OutputStream outputStream) {
        reportGenerator.exportToCSV(report, outputStream);
    }
    
    // Other reporting methods...
}

// PaymentService - handles only payment concerns
@Service
public class PaymentService {
    private final PaymentProcessor paymentProcessor;
    private final InvoiceGenerator invoiceGenerator;
    private final TaxService taxService;
    private final UserRepository userRepository;
    
    public PaymentService(PaymentProcessor paymentProcessor,
                         InvoiceGenerator invoiceGenerator,
                         TaxService taxService,
                         UserRepository userRepository) {
        this.paymentProcessor = paymentProcessor;
        this.invoiceGenerator = invoiceGenerator;
        this.taxService = taxService;
        this.userRepository = userRepository;
    }
    
    public PaymentResult processPayment(String userId, double amount, PaymentMethod method) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        
        double taxAmount = taxService.calculateTax(amount, user.getTaxRegion());
        double totalAmount = amount + taxAmount;
        
        return paymentProcessor.processPayment(user.getId(), totalAmount, method);
    }
    
    public String createInvoice(String userId, List<LineItem> items) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        return invoiceGenerator.generateInvoice(user.getId(), items);
    }
    
    public PaymentResult processRefund(String paymentId, double amount) {
        return paymentProcessor.processRefund(paymentId, amount);
    }
    
    // Other payment methods...
}

// PreferenceService - handles only user preferences
@Service
public class PreferenceService {
    private final PreferenceRepository preferenceRepository;
    private final UserRepository userRepository;
    
    public PreferenceService(PreferenceRepository preferenceRepository,
                            UserRepository userRepository) {
        this.preferenceRepository = preferenceRepository;
        this.userRepository = userRepository;
    }
    
    public UserPreferences getUserPreferences(String userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        return preferenceRepository.findByUserId(userId)
                .orElseGet(() -> preferenceRepository.save(new UserPreferences(userId)));
    }
    
    public void updateUserPreference(String userId, String key, String value) {
        UserPreferences prefs = getUserPreferences = getUserPreferences(userId);
        prefsPreferencesPreference = userRepositoryService.getUserPreferences(userId);
 .orElseGet(() -> preference preferenceRepository.save(new UserPreferences(userId));
        preferences.setPreference(key, value);
        preferenceRepository.save(preferences);
    }
    
    public void resetUserPreferencesToDefault(String userId) {
        UserPreferences prefs = getUserPreferences(userId);
        prefs.resetToDefaults();
        preferenceRepository.save(prefs);
    }
    
    public Map<String, String> getAllUserPreferences(String userId) {
        return getUserPreferences(userId).getAllPreferences();
    }
    
    public void bulkUpdateUserPreferences(List<String> userIds, String key, String value) {
        for (String userId : userIds) {
            updateUserPreference(userId, key, value);
        }
    }
}

// SecurityService - handles only security concerns
@Service
public class SecurityService {
    private final AuditLogger auditLogger;
    private final PermissionChecker permissionChecker;
    private final InputValidator inputValidator;
    private final UserRepository userRepository;
    
    public SecurityService(AudLogger auditLogger,
                          PermissionChecker permissionChecker,
                          InputValidator inputValidator,
                          UserRepository userRepository) {
        this.auditLogger = auditLogger;
        this.permissionChecker = permissionChecker;
        this.inputValidator = inputValidator;
        this.userRepository = userRepository;
    }
    
    public void logAccess(String userId, String resource, String action) {
        auditLogger.logAccess(userId, resource, action);
    }
    
    public boolean checkPermission(String userId, String permission) {
        return permissionChecker.hasPermission(userId, permission);
    }
    
    public List<String> getUserPermissions(String userId) {
        return permissionChecker.getUserPermissions(userId);
    }
    
    public void grantPermission(String userId, String permission) {
        permissionChecker.grantPermission(userId, permission);
    }
    
    public void revokePermission(String userId, String permission) {
        permissionChecker.revokePermission(userId, permission);
    }
    
    public boolean isAdmin(String userId) {
        return permissionChecker.isAdmin(userId);
    }
    
    public void promoteToAdmin(String userId) {
        permissionChecker.grantRole(userId, "ADMIN");
    }
    
    public void demoteFromAdmin(String userId) {
        permissionChecker.revokeRole(userId, "ADMIN");
    }
    
    public boolean validateInput(String input, ValidationRule rule) {
        return inputValidator.isValid(input, rule);
    }
    
    public String sanitizeInput(String input) {
        return inputValidator.sanitize(input);
    }
}
```

## How to Fix
1. **Identify the God Class**: Look for classes with too many responsibilities, methods, or attributes
2. **Apply Single Responsibility Principle**: Split the class into multiple classes, each with one clear responsibility
3. **Use Extract Class Refactoring**: Move related methods and fields to new classes
4. **Apply Dependency Injection**: Inject collaborators instead of creating them internally
5. **Use Facade Pattern**: If the class provides a simplified interface to a complex subsystem
6. **Apply Adapter Pattern**: If the class is adapting between incompatible interfaces
7. **Use Strategy Pattern**: For algorithms that can be swapped
8. **Apply Observer Pattern**: For event handling and notifications
9. **Implement Proper Layering**: Separate concerns into layers (presentation, business, data access)
10. **Apply Domain-Driven Design**: Identify bounded contexts and aggregates
11. **Use Microservices Architecture**: For large systems, consider splitting into services
12. **Conduct Code Reviews**: Focus on identifying god classes during reviews
13. **Set Size Limits**: Establish team guidelines for maximum class size
14. **Use Static Analysis Tools**: Tools like SonarQube can detect god classes
15. **Allocate Refactoring Time**: Include refactoring in sprint planning
16. **Educate Team**: Train developers on SOLID principles and code smells
17. **Monitor Metrics**: Track class size, complexity, and coupling over time
18. **Apply Boy Scout Rule**: Leave the code cleaner than you found it

## Prevention Strategies
- Follow SOLID principles rigorously
- Practice Test-Driven Development (TDD)
- Conduct regular code reviews focused on design
- Use pair programming to spread knowledge and improve design
- Implement coding standards that include class size guidelines
- Use architectural decision records to document design decisions
- Apply the Boy Scout Rule consistently
- Schedule regular refactoring sprints
- Use static analysis tools to detect code smells early
- Provide training on object-oriented design principles
- Encourage developers to think in terms of responsibilities, not just data
- Use design patterns appropriately
- Implement continuous integration with quality gates
- Monitor code complexity metrics over time
- Conduct architecture reviews periodically
- Use evolutionary architecture principles
- Apply Domain-Driven Design concepts
- Consider hexagonal/ports and adapters architecture
- Use event-driven architecture to decouple components

## Related Anti-Patterns
- Spaghetti Code
- Blob Class
- Swiss Army Knife
- Holy Class
- God Component
- God Module
- God Service
- God Controller
- God Repository
- Manager Syndrome
- Kitchen Sink
- Swiss Army Knife Anti-Pattern

## References
- Martin, Robert C. (2003). *Agile Software Development: Principles, Patterns, and Practices*
- Fowler, Martin. (1999). *Refactoring: Improving the Design of Existing Code*
- Gamma, Erich et al. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*
- Bloch, Joshua. (2018). *Effective Java*
- Martin, Robert C. (2017). *Clean Architecture: A Craftsman's Guide to Software Structure and Design*
- Evans, Eric. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software*
- Sommerville, Ian. (2015). *Software Engineering*
- Lachovere, Hevery. (2008). *Clean Code Talks - Don't Look For Things!*
- Ambrosini, Cristian. (2015). *God Object*
- Fowler, Martin. (2004). *Patterns of Enterprise Application Architecture*
- Hohpe, Gregor & Woolf, Bobby. (2004). *Enterprise Integration Patterns*
- Bass, Len et al. (2012). *Software Architecture in Practice*
- Martin, Robert C. (2002). *Agile Principles, Patterns, and Practices in C#*