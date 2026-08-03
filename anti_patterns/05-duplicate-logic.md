# Duplicate Logic Anti-Pattern

## Description
Duplicate logic (also known as code duplication or clone code) occurs when identical or very similar code sequences appear in multiple places within a codebase. This violates the DRY (Don't Repeat Yourself) principle and creates maintenance challenges, increases bug risk, and leads to inconsistencies when changes need to be made in multiple places.

## Characteristics
- **Exact Duplication**: Identical code blocks copied and pasted
- **Near-Miss Duplication**: Similar code with minor variations (different variable names, literals, etc.)
- **Structural Similarity**: Different implementations solving the same problem with similar structure
- **Logical Duplication**: Different code implementing the same business rule or logic
- **Copy-Paste Programming**: Using copy-paste as primary development technique
- **Template Cloning**: Copying entire files or classes and making minor modifications
- **Boilerplate Repetition**: Repeating the same setup/cleanup code patterns
- **Cross-cutting Concerns Duplication**: Repeating logging, validation, error handling patterns
- **Test Code Duplication**: Similar test patterns repeated across test classes
- **Configuration Duplication**: Similar configuration snippets repeated across files

## Root Causes
- **Lack of Abstraction**: Failure to identify common patterns and extract them
- **Time Pressure**: Copy-pasting seems faster than designing proper abstractions
- **Limited Visibility**: Developers unaware of existing similar code
- **Poor Code Navigation**: Difficulty finding existing relevant code
- **Weak Ownership**: "Not my module" attitude preventing code sharing
- **Inadequate Code Reviews**: Duplicates not caught during review process
- **Learning by Copying**: Novice developers learning by modifying existing code
- **Fear of Breaking Changes**: Reluctance to modify shared code due to regression fears
- **Merge Challenges**: Difficulty merging changes in shared code leading to avoidance
- **Tooling Limitations**: Lack of good refactoring support in development environments
- **Misunderstanding of DRY**: Believing duplication is acceptable if "it works"
- **Geographic/Team Separation**: Different teams solving similar problems in isolation
- **Legacy Code Anxiety**: Fear of touching old code leads to duplication instead of refactoring

## Impact on System
- **Maintenance Nightmare**: Bug fixes must be applied in multiple places
- **Inconsistency Risk**: Fixes applied to some copies but not others
- **Increased Bug Density**: More copies = more places for bugs to hide
- **Higher Cognitive Load**: Developers must track multiple versions of similar logic
- **Slower Development**: Time spent finding and updating all instances
- **Increased Testing Burden**: More test cases needed to cover duplicated logic
- **Merge Conflicts**: Higher likelihood of conflicts when multiple people edit similar code
- **Documentation Drift**: Comments and documentation become inconsistent
- **Performance Issues**: Inefficient patterns replicated instead of optimized once
- **Technical Debt Accumulation**: Duplication compounds over time
- **Onboarding Difficulty**: New developers confused by multiple similar implementations
- **Refactoring Resistance**: Fear of breaking something prevents cleanup efforts

## Examples

### Bad Example (Exact Duplication)
```java
// UserService.java - Copy-pasted validation logic
@Service
public class UserService {
    public User registerUser(UserRegistrationRequest request) {
        // DUPLICATED VALIDATION LOGIC - Appears in 5+ places
        if (request.getEmail() == null || request.getEmail().trim().isEmpty()) {
            throw new ValidationException("Email is required");
        }
        if (!request.getEmail().matches("^[A-Za-z0-9+_.-]+@(.+)$")) {
            throw new ValidationException("Invalid email format");
        }
        if (request.getPassword() == null || request.getPassword().length() < 8) {
            throw new ValidationException("Password must be at least 8 characters");
        }
        if (request.getPassword().equalsIgnoreCase("password") ||
            request.getPassword().equalsIgnoreCase("12345678")) {
            throw new ValidationException("Password too common");
        }
        
        // ... rest of method
    }
    
    public User updateUserEmail(String userId, String newEmail) {
        // SAME EXACT VALIDATION COPIED HERE
        if (newEmail == null || newEmail.trim().isEmpty()) {
            throw new ValidationException("Email is required");
        }
        if (!newEmail.matches("^[A-Za-z0-9+_.-]+@(.+)$")) {
            throw new ValidationException("Invalid email format");
        }
        // ... missing password validation (inconsistent!)
        
        // ... rest of method
    }
    
    public void changePassword(String userId, String currentPassword, String newPassword) {
        // ANOTHER COPY WITH SLIGHT VARIATIONS
        if (newPassword == null || newPassword.trim().isEmpty()) {
            throw new ValidationException("New password is required");
        }
        // Email validation missing entirely here!
        if (newPassword.length() < 8) {
            throw new ValidationException("Password must be at least 8 characters");
        }
        // Different error message for same check!
        if (newPassword.equals("password") || newPassword.equals("12345678")) {
            throw new ValidationException("Please choose a stronger password");
        }
        
        // ... rest of method
    }
}

// Even worse - duplicated in controllers
@RestController
@RequestMapping("/api/auth")
public class AuthController {
    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody UserRegistrationRequest request) {
        // YET ANOTHER COPY - slightly different error handling
        if (request.getEmail() == null || request.getEmail().isEmpty()) {
            return ResponseEntity.badRequest().body("Email cannot be empty");
        }
        String emailRegex = "^[A-Za-z0-9+_.-]+@(.+)$";
        if (!request.getEmail().matches(emailRegex)) {
            return ResponseEntity.badRequest().body("Email format is invalid");
        }
        if (request.getPassword() == null || request.getPassword().length() < 8) {
            return ResponseEntity.badRequest().body("Password too short");
        }
        // ... and so on
    }
}

// And in DTO validators
public class UserRegistrationRequestValidator implements Validator {
    @Override
    public boolean supports(Class<?> clazz) {
        return UserRegistrationRequest.class.equals(clazz);
    }

    @Override
    public void validate(Object target, Errors errors) {
        UserRegistrationRequest request = (UserRegistrationRequest) target;
        
        // YET ANOTHER VARIATION
        String email = request.getEmail();
        if (email == null || email.isEmpty()) {
            errors.rejectValue("email", "NotEmpty", "Email is required");
        } else if (!email.matches("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")) {
            // DIFFERENT REGEX PATTERN!
            errors.rejectValue("email", "Pattern", "Invalid email format");
        }
        
        String password = request.getPassword();
        if (password == null || password.isEmpty()) {
            errors.rejectValue("password", "NotEmpty", "Password is required");
        } else if (password.length() < 8) {
            errors.rejectValue("password", "Size", "Password must be at least 8 characters");
        } else if (Arrays.asList("password", "123456", "12345678", "qwerty", "abc123").contains(password.toLowerCase())) {
            // DIFFERENT LIST OF COMMON PASSWORDS!
            errors.rejectValue("password", "WeakPassword", "Password is too common");
        }
    }
}
```

### Bad Example (Structural/Logical Duplication)
```java
// ReportService.java - Similar algorithms duplicated
@Service
public class ReportService {
    
    public List<SalesReport> generateMonthlySalesReport(int year, int month) {
        // Complex date range calculation - copied in 3 methods
        LocalDate startDate = YearMonth.of(year, month).atDay(1);
        LocalDate endDate = YearMonth.of(year, month).atEndOfMonth();
        
        // Complex filtering logic - similar pattern elsewhere
        List<Sale> sales = salesRepository.findAll()
            .stream()
            .filter(sale -> !sale.getSaleDate().isBefore(startDate))
            .filter(sale -> !sale.getSaleDate().isAfter(endDate))
            .filter(sale -> sale.getStatus() == SaleStatus.COMPLETED)
            .filter(sale -> sale.getAmount() > 0)
            .collect(Collectors.toList());
        
        // ... processing logic
        return processSalesToReport(sales);
    }
    
    public List<SalesReport> generateQuarterlySalesReport(int year, int quarter) {
        // ALMOST IDENTICAL DATE LOGIC - copied and slightly modified
        int startMonth = (quarter - 1) * 3 + 1;
        int endMonth = startMonth + 2;
        LocalDate startDate = YearMonth.of(year, startMonth).atDay(1);
        LocalDate endDate = YearMonth.of(year, endMonth).atEndOfMonth();
        
        // SIMILAR BUT NOT IDENTICAL FILTERING - subtle differences
        List<Sale> sales = salesRepository.findAll()
            .stream()
            .filter(sale -> !sale.getSaleDate().isBefore(startDate.minusDays(1))) // Different!
            .filter(sale -> !sale.getSaleDate().isAfter(endDate.plusDays(1)))   // Different!
            .filter(sale -> sale.getStatus() == SaleStatus.COMPLETED || 
                          sale.getStatus() == SaleStatus.PENDING) // Different condition!
            .filter(sale -> sale.getAmount() >= 0) // Different condition!
            .collect(Collectors.toList());
        
        // ... similar but different processing logic
        return processSalesToReport(sales); // Same method name, different expectations
    }
    
    public List<SalesReport> generateYearlySalesReport(int year) {
        // YET ANOTHER VARIATION OF DATE LOGIC
        LocalDate startDate = YearMonth.of(year, 1).atDay(1);
        LocalDate endDate = YearMonth.of(year, 12).atEndOfMonth();
        
        // COMPLETELY DIFFERENT APPROACH THIS TIME - using JPQL
        String jpql = "SELECT s FROM Sale s WHERE s.saleDate >= :startDate AND s.saleDate <= :endDate";
        List<Sale> sales = entityManager.createQuery(jpql, Sale.class)
            .setParameter("startDate", startDate)
            .setParameter("endDate", endDate)
            .getResultList();
        
        // Different filtering approach entirely
        List<Sale> filteredSales = new ArrayList<>();
        for (Sale sale : sales) {
            if (sale.getStatus().equals(SaleStatus.COMPLETED)) {
                filteredSales.add(sale);
            }
        }
        
        // Yet another processing approach
        return processSalesToReportV2(filteredSales); // Different method!
    }
    
    // Three slightly different versions of essentially the same processing
    private List<SalesReport> processSalesToReport(List<Sale> sales) {
        // Implementation A
    }
    
    private List<SalesReport> processSalesToReport(List<Sale> sales) {
        // Implementation B - same signature but different logic (overload by return type not allowed in Java)
        // Actually this would be a different method name in reality
    }
    
    private List<SalesReport> processSalesToReportV2(List<Sale> sales) {
        // Implementation C
    }
}
```

### Good Approach (DRY Principle Applied)
```java
// Centralized validation service
@Service
public class ValidationService {
    private static final Pattern EMAIL_PATTERN = Pattern.compile(
        "^[A-Za-z0-9+_.-]+@(.+)$", 
        Pattern.CASE_INSENSITIVE
    );
    
    private static final Set<String> COMMON_PASSWORDS = Set.of(
        "password", "123456", "12345678", "qwerty", "abc123"
    );
    
    public void validateEmail(String email) {
        if (email == null || email.trim().isEmpty()) {
            throw new ValidationException("Email is required");
        }
        if (!EMAIL_PATTERN.matcher(email).matches()) {
            throw new ValidationException("Invalid email format");
        }
    }
    
    public void validatePassword(String password) {
        if (password == null || password.length() < 8) {
            throw new ValidationException("Password must be at least 8 characters");
        }
        String lower = password.toLowerCase();
        if (COMMON_PASSWORDS.contains(lower)) {
            throw new ValidationException("Password too common");
        }
    }
    
    public void validateUserRegistration(UserRegistrationRequest request) {
        validateEmail(request.getEmail());
        validatePassword(request.getPassword());
        // Additional validations...
    }
}

// Updated service using shared validation
@Service
public class UserService {
    private final ValidationService validationService;
    private final UserRepository userRepository;
    
    public UserService(ValidationService validationService, UserRepository userRepository) {
        this.validationService = validationService;
        this.userRepository = userRepository;
    }
    
    public User registerUser(UserRegistrationRequest request) {
        validationService.validateUserRegistration(request);
        // ... rest of method (clean and focused)
    }
    
    public User updateUserEmail(String userId, String newEmail) {
        validationService.validateEmail(newEmail);
        // ... rest of method
    }
    
    public void changePassword(String userId, String currentPassword, String newPassword) {
        validationService.validatePassword(newPassword);
        // Additional validation for current password if needed
        // ... rest of method
    }
}

// Centralized date range utility
@Component
public class DateRangeUtil {
    public static LocalDateRange getMonthRange(int year, int month) {
        LocalDate start = YearMonth.of(year, month).atDay(1);
        LocalDate end = YearMonth.of(year, month).atEndOfMonth();
        return new LocalDateRange(start, end);
    }
    
    public static LocalDateRange getQuarterRange(int year, int quarter) {
        if (quarter < 1 || quarter > 4) {
            throw new IllegalArgumentException("Quarter must be between 1 and 4");
        }
        int startMonth = (quarter - 1) * 3 + 1;
        int endMonth = startMonth + 2;
        LocalDate start = YearMonth.of(year, startMonth).atDay(1);
        LocalDate end = YearMonth.of(year, endMonth).atEndOfMonth();
        return new LocalDateRange(start, end);
    }
    
    public static LocalDateRange getYearRange(int year) {
        LocalDate start = YearMonth.of(year, 1).atDay(1);
        LocalDate end = YearMonth.of(year, 12).atEndOfMonth();
        return new LocalDateRange(start, end);
    }
    
    // Simple value object
    public static class LocalDateRange {
        private final LocalDate start;
        private final LocalDateEnd;
        
        public LocalDateRange(LocalDate start, LocalDate end) {
            this.start = start;
            this.end = end;
        }
        
        public LocalDate getStart() { return start; }
        public LocalDate getEnd() { return end; }
        public boolean contains(LocalDate date) {
            return !date.isBefore(start) && !date.isAfter(end);
        }
    }
}

// Using specification pattern for reusable queries
@Service
public class ReportService {
    private final SalesRepository salesRepository;
    private final DateRangeUtil dateRangeUtil;
    
    public ReportService(SalesRepository salesRepository, DateRangeUtil dateRangeUtil) {
        this.salesRepository = salesRepository;
        this.dateRangeUtil = dateRangeUtil;
    }
    
    public List<SalesReport> generateMonthlySalesReport(int year, int month) {
        LocalDateRange range = dateRangeUtil.getMonthRange(year, month);
        List<Sale> sales = salesRepository.findCompletedSalesInDateRange(
            range.getStart(), range.getEnd());
        return processSalesToReport(sales);
    }
    
    public List<SalesReport> generateQuarterlySalesReport(int year, int quarter) {
        LocalDateRange range = dateRangeUtil.getQuarterRange(year, quarter);
        List<Sale> sales = salesRepository.findCompletedSalesInDateRange(
            range.getStart(), range.getEnd());
        return processSalesToReport(sales);
    }
    
    public List<SalesReport> generateYearlySalesReport(int year) {
        LocalDateRange range = dateRangeUtil.getYearRange(year);
        List<Sale> sales = salesRepository.findCompletedSalesInDateRange(
            range.getStart(), range.getEnd());
        return processSalesToReport(sales);
    }
    
    // Single implementation of processing logic
    private List<SalesReport> processSalesToReport(List<Sale> sales) {
        // One clear implementation
    }
}

// Repository with specialized method
public interface SalesRepository extends JpaRepository<Sale, Long> {
    @Query("SELECT s FROM Sale s WHERE s.status = 'COMPLETED' AND s.saleDate BETWEEN :startDate AND :endDate")
    List<Sale> findCompletedSalesInDateRange(@Param("startDate") LocalDate startDate, 
                                           @Param("endDate") LocalDate endDate);
}

// Or using Specifications for even more flexibility
public class SaleSpecifications {
    public static Specification<Specification> hasStatus(SaleStatus status) {
        return (root, query, cb) -> cb.equal(root.get("status"), status);
    }
    
    public static Specification<Sale> createdBetween(LocalDate start, LocalDate end) {
        return (root, query, cb) -> 
            cb.between(root.get("saleDate"), start, end);
    }
    
    public static Specification<Sale> hasPositiveAmount() {
        return (root, query, cb) -> 
            cb.greaterThan(root.get("amount"), BigDecimal.ZERO);
    }
}

// Then in service:
public List<SalesReport> generateMonthlySalesReport(int year, int month) {
    LocalDateRange range = dateRangeUtil.getMonthRange(year, month);
    
    Specification<Sale> spec = Specification.where(
        SaleSpecifications.hasStatus(SaleStatus.COMPLETED)
    ).and(
        SaleSpecifications.createdBetween(range.getStart(), range.getEnd())
    ).and(
        SaleSpecifications.hasPositiveAmount()
    );
    
    List<Sale> sales = salesRepository.findAll(spec);
    return processSalesToReport(sales);
}
```

### Utility Class Approach for Common Functions
```java
// String utilities - one place for common string operations
public final class StringUtils {
    private StringUtils() { /* Prevent instantiation */ }
    
    public static boolean isNullOrEmpty(String str) {
        return str == null || str.isEmpty();
    }
    
    public static boolean isNullOrBlank(String str) {
        return str == null || str.trim().isEmpty();
    }
    
    public static String defaultIfEmpty(String str, String defaultValue) {
        return isNullOrEmpty(str) ? defaultValue : str;
    }
    
    public static String defaultIfBlank(String str, String defaultValue) {
        return isNullOrBlank(str) ? defaultValue : str;
    }
    
    public static boolean isValidEmail(String email) {
        if (isNullOrEmpty(email)) return false;
        String emailRegex = "^[A-Za-z0-9+_.-]+@(.+)$";
        Pattern pattern = Pattern.compile(emailRegex, Pattern.CASE_INSENSITIVE);
        Matcher matcher = pattern.matcher(email);
        return matcher.matches();
    }
    
    // ... other commonly used string methods
}

// Number utilities
public final class NumberUtils {
    private NumberUtils() { /* Prevent instantiation */ }
    
    public static int safeParseInt(String value, int defaultValue) {
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }
    
    public static boolean isPositive(int value) {
        return value > 0;
    }
    
    public static int ceilingDivide(int dividend, int divisor) {
        if (divisor == 0) throw new IllegalArgumentException("Divisor cannot be zero");
        return (divisor > 0) 
            ? (dividend + divisor - 1) / divisor 
            : (dividend + divisor + 1) / divisor;
    }
    
    // ... other commonly used number methods
}

// Validation using Apache Commons Validator (example of leveraging existing library)
public class ValidationUtils {
    private static final EmailValidator EMAIL_VALIDATOR = EmailValidator.getInstance();
    
    public static boolean isValidEmail(String email) {
        return EMAIL_VALIDATOR.isValid(email);
    }
    
    // ... other validations
}
```

## Strategies for Eliminating Duplication

### 1. Extract Method/Function
```java
// BEFORE - Duplicated validation logic
if (user.getAge() < 13) {
    throw new ValidationException("User must be at least 13 years old");
}
// ... same check in 5 other places

// AFTER - Extracted to method
private void validateMinimumAge(User user) {
    if (user.getAge() < 13) {
        throw new ValidationException("User must be at least 13 years old");
    }
}

// Used in all places where validation is needed
```

### 2. Extract Class
```java
// BEFORE - Duplicated email validation logic scattered
// AFTER - EmailValidator class encapsulates all email-related validation
public class EmailValidator {
    private static final Pattern EMAIL_PATTERN = Pattern.compile(
        "^[A-Za-z0-9+_.-]+@(.+)$", 
        Pattern.CASE_INSENSITIVE
    );
    
    public static boolean isValid(String email) {
        if (email == null || email.isEmpty()) return false;
        return EMAIL_PATTERN.matcher(email).matches();
    }
    
    public static String normalize(String email) {
        if (email == null) return null;
        return email.trim().toLowerCase();
    }
    
    public static String extractDomain(String email) {
        if (!isValid(email)) return null;
        int atIndex = email.indexOf('@');
        return email.substring(atIndex + 1);
    }
}
```

### 3. Use Template Method Pattern
```java
// BEFORE - Similar algorithms with duplicated skeleton
public void processTypeA(Data data) {
    validate(data);
    // Step 1 specific to A
    stepOneA(data);
    // Common steps 2-5
    stepTwo(data);
    stepThree(data);
    stepFour(data);
    stepFive(data);
    // Step 6 specific to A
    stepSixA(data);
}

public void processTypeB(Data data) {
    validate(data);
    // Step 1 specific to B
    stepOneB(data);
    // Common steps 2-5 (identical to above)
    stepTwo(data);
    stepThree(data);
    stepFour(data);
    stepFive(data);
    // Step 6 specific to B
    stepSixB(data);
}

// AFTER - Template method pattern
public abstract class DataProcessor {
    public final void process(Data data) {
        validate(data);
        stepOne(data);      // Abstract - implemented by subclasses
        stepTwo(data);      // Concrete - shared implementation
        stepThree(data);    // Concrete - shared implementation
        stepFour(data);     // Concrete - shared implementation
        stepFive(data);     // Concrete - shared implementation
        stepSix(data);      // Abstract - implemented by subclasses
    }
    
    protected abstract void stepOne(Data data);
    protected abstract void stepSix(Data data);
    
    // Shared implementations
    protected void stepTwo(Data data) { /* shared logic */ }
    protected void stepThree(Data data) { /* shared logic */ }
    protected void stepFour(Data data) { /* shared logic */ }
    protected void stepFive(Data data) { /* shared logic */ }
    
    protected void validate(Data data) {
        // Shared validation logic
    }
}

public class TypeAProcessor extends DataProcessor {
    @Override
    protected void stepOne(Data data) {
        // Implementation specific to A
    }
    
    @Override
    protected void stepSix(Data data) {
        // Implementation specific to A
    }
}

public class TypeBProcessor extends DataProcessor {
    @Override
    protected void stepOne(Data data) {
        // Implementation specific to B
    }
    
    @Override
    protected void stepSix(Data data) {
        // Implementation specific to B
    }
}
```

### 4. Use Strategy Pattern
```java
// BEFORE - Duplicated conditional logic
public double calculatePrice(Product product, Customer customer) {
    double basePrice = product.getBasePrice();
    
    if (customer.getType() == CustomerType.RETAIL) {
        // Complex retail pricing logic
        if (customer.isLoyaltyMember()) {
            // Loyalty discount calculation
        }
        // Volume discounts, seasonal adjustments, etc.
    } else if (customer.getType() == CustomerType.WHOLESALE) {
        // COMPLETELY DIFFERENT wholesale pricing logic
        // Duplicated complexity in different form
    } else if (customer.getType() == CustomerType.PARTNER) {
        // YET ANOTHER different partner pricing logic
        // Same complexity, different implementation
    }
    
    // Apply taxes, shipping, etc. (more duplicated logic)
}

// AFTER - Strategy pattern
public interface PricingStrategy {
    double calculatePrice(Product product, Customer customer);
}

@component
public class RetailPricingStrategy implements PricingStrategy {
    @Override
    public double calculatePrice(Product product, Customer customer) {
        // Encapsulated retail-specific logic
    }
}

@Component
public class WholesalePricingStrategy implements PricingStrategy {
    @Override
    public double calculatePrice(Product product, Customer customer) {
        // Encapsulated wholesale-specific logic
    }
}

@Component
public class PartnerPricingStrategy implements PricingStrategy {
    @Override
    public double calculatePrice(Product product, Customer customer) {
        // Encapsulated partner-specific logic
    }
}

@Service
public class PricingService {
    private final Map<CustomerType, PricingStrategy> strategies;
    
    public PricingService(List<PricingStrategy> strategies) {
        this.strategies = strategies.stream()
            .collect(Collectors.toMap(
                s -> s.getSupportedCustomerType(), 
                Function.identity()
            ));
    }
    
    public double calculatePrice(Product product, Customer customer) {
        PricingStrategy strategy = strategies.get(customer.getType());
        if (strategy == null) {
            throw new IllegalArgumentException(
                "No pricing strategy for customer type: " + customer.getType());
        }
        return strategy.calculatePrice(product, customer);
    }
}
```

### 5. Use Inheritance Judiciously
```java
// BEFORE - Duplicate fields and methods in similar entities
public class Employee {
    private String id;
    private String firstName;
    private String lastName;
    private String email;
    private LocalDate dateOfBirth;
    private LocalDate hireDate;
    
    // Getters/setters for all fields
    // Common methods like getFullName(), getAge(), yearsOfService(), etc.
}

public class Customer {
    private String id;
    private String firstName;
    private String lastName;
    private String email;
    private LocalDate dateOfBirth;
    private LocalDate registrationDate;
    
    // IDENTICAL getters/setters for first 5 fields
    // IDENTICAL methods like getFullName(), getAge(), yearsSinceDate(), etc.
    // Plus customer-specific fields and methods
}

// AFTER - Base class for common attributes
@MappedSuperclass
public abstract class Person {
    @Id
    protected String id;
    
    protected String firstName;
    protected String lastName;
    protected String email;
    protected LocalDate dateOfBirth;
    
    // Getters/setters for common fields
    // Common methods: getFullName(), getAge(), etc.
}

@Entity
public class Employee extends Person {
    @Column(name = "hire_date")
    private LocalDate hireDate;
    
    // Employee-specific fields and methods
    // Inherits all common functionality from Person
}

@Entity
public class Customer extends Person {
    @Column(name = "registration_date")
    private LocalDate registrationDate;
    
    // Customer-specific fields and methods
    // Inherits all common functionality from Person
}
```

### 6. Use Composition Over Inheritance (When Appropriate)
```java
// BEFORE - Inheritance hierarchy getting complex due to slight variations
public abstract class Shape {
    protected Color color;
    
    public abstract double area();
    public abstract double perimeter();
}

public class Circle extends Shape {
    private double radius;
    
    @Override
    public double area() {
        return Math.PI * radius * radius;
    }
    
    @Override
    public double perimeter() {
        return 2 * Math.PI * radius;
    }
}

public class Rectangle extends Shape {
    private double width;
    private double height;
    
    @Override
    public double area() {
        return width * height;
    }
    
    @Override
    public double perimeter() {
        return 2 * (width + height);
    }
}

// Imagine adding Square, Triangle, Polygon, etc. - each reimplementing similar patterns

// AFTER - Strategy pattern for algorithms that vary
public interface AreaCalculator {
    double calculateArea(Shape shape);
}

public interface PerimeterCalculator {
    double calculatePerimeter(Shape shape);
}

public class Shape {
    private final AreaCalculator areaCalculator;
    private final PerimeterCalculator perimeterCalculator;
    private final Color color;
    
    public Shape(AreaCalculator areaCalculator, PerimeterCalculator perimeterCalculator, Color color) {
        this.areaCalculator = areaCalculator;
        this.perimeterCalculator = perimeterCalculator;
        this.color = color;
    }
    
    public double area() {
        return areaCalculator.calculateArea(this);
    }
    
    public double perimeter() {
        return perimeterCalculator.calculatePerimeter(this);
    }
    
    // Getters/setters for dimensions (radius, width/height, etc.)
}

// Specific strategies
public class CircleAreaCalculator implements AreaCalculator {
    @Override
    public double calculateArea(Shape shape) {
        Circle circle = (Circle) shape;
        return Math.PI * circle.getRadius() * circle.getRadius();
    }
}

public class CirclePerimeterCalculator implements PerimeterCalculator {
    @Override
    public double calculatePerimeter(Shape shape) {
        Circle circle = (Circle) shape;
        return 2 * Math.PI * circle.getRadius();
    }
}

// Similar strategy classes for Rectangle, Triangle, etc.
// Each shape type gets its own strategy pair, but the Shape context remains simple
```

### 7. Use Annotations and AOP for Cross-Cutting Concerns
```java
// BEFORE - Duplicated logging, timing, security checks
public User getUserById(String userId) {
    logger.info("Fetching user with id: {}", userId);
    long start = System.nanoTime();
    
    // Security check duplicated everywhere
    if (!securityService.hasPermission(currentUser, "USER_READ")) {
        throw new AccessDeniedException("Insufficient permissions");
    }
    
    try {
        User user = userRepository.findById(userId);
        long end = System.nanoTime();
        logger.info("Retrieved user {} in {} ms", userId, TimeUnit.NANOSECONDS.toMillis(end - start));
        return user;
    } catch (Exception e) {
        long end = System.nanoTime();
        logger.error("Failed to retrieve user {} after {} ms: {}", 
                    userId, TimeUnit.NANOSECONDS.toMillis(end - start), e.getMessage());
        throw e;
    }
}

// Same pattern in 20+ methods

// AFTER - Aspect-Oriented Programming
@Aspect
@Component
public class ServiceMethodAspect {
    @Autowired
    private Logger logger;
    
    @Autowired
    private SecurityService securityService;
    
    @Around("execution(* com.example.service.*.*(..))")
    public Object monitorAndSecure(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().toShortString();
        logger.info("Entering {}", methodName);
        long start = System.nanoTime();
        
        // Security check in one place
        if (!securityService.hasPermission(currentUser, getRequiredPermission(joinPoint))) {
            throw new AccessDeniedException("Insufficient permissions for " + methodName);
        }
        
        try {
            Object result = joinPoint.proceed();
            long end = System.nanoTime();
            logger.info("Exited {} successfully in {} ms", 
                       methodName, TimeUnit.NANOSECONDS.toMillis(end - start));
            return result;
        } catch (Exception e) {
            long end = System.nanoTime();
            logger.error("Exited {} with exception after {} ms: {}", 
                        methodName, TimeUnit.NANOSECONDS.toMillis(end - start), e.toString());
            throw e;
        }
    }
    
    private String getRequiredPermission(ProceedingJoinPoint joinPoint) {
        // Logic to determine required permission based on method signature, annotations, etc.
        return "DEFAULT_PERMISSION"; // Simplified
    }
}

// Even cleaner with annotations
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Timed {}
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Secured {
    String value() default "";
}

@Aspect
@Component
public class AnnotationDrivenAspect {
    // Similar advice but triggered by @Timed and @Secured annotations
}
```

### 8. Use Inheritance for Test Code
```java
// BEFORE - Duplicated test setup
public class UserServiceTest {
    private UserService userService;
    private UserRepository userRepository;
    private ValidationService validationService;
    
    @BeforeEach
    void setUp() {
        userRepository = mock(UserRepository.class);
        validationService = mock(ValidationService.class);
        userService = new UserService(userRepository, validationService);
        // Common mock setup
        when(userRepository.findById(anyString())).thenReturn(Optional.empty());
        when(validationService.validateEmail(anyString())).thenReturn(true);
        // ... 10+ lines of common mock setup
    }
    
    @Test
    void testRegisterUser() {
        // Same setup as above copied here too if using @BeforeEach isn't sufficient
        // ... test logic
    }
    
    @Test
    void testUpdateUserEmail() {
        // Again, potentially duplicated setup
        // ... test logic
    }
}

// AFTER - Base test class
public abstract class BaseServiceTest {
    protected UserRepository userRepository;
    protected ValidationService validationService;
    protected UserService userService;
    
    @BeforeEach
    void setUp() {
        userRepository = mock(UserRepository.class);
        validationService = mock(ValidationService.class);
        userService = new UserService(userRepository, validationService);
        // Common mock setup in ONE place
        when(userRepository.findById(anyString())).thenReturn(Optional.empty());
        when(validationService.validateEmail(anyString())).thenReturn(true);
        when(validationService.validatePassword(anyString())).thenReturn(true);
        // ... other common stubs
    }
    
    protected User createTestUser(String id) {
        User user = new User();
        user.setId(id);
        user.setEmail("test@example.com");
        // ... common test object creation
        return user;
    }
    
    protected UserRegistrationRequest createValidRegistrationRequest() {
        UserRegistrationRequest request = new UserRegistrationRequest();
        request.setEmail("test@example.com");
        request.setPassword("SecurePass123!");
        // ... common test data creation
        return request;
    }
}

public class UserServiceTest extends BaseServiceTest {
    @Test
    void testRegisterUser() {
        // Inherits all setup - no duplication
        when(userRepository.save(any(User.class))).thenAnswer(i -> i.getArgument(0));
        
        UserRegistrationRequest request = createValidRegistrationRequest();
        User result = userService.registerUser(request);
        
        // Assertions
        assertNotNull(result);
        assertEquals("test@example.com", result.getEmail());
        verify(userRepository).save(any(User.class));
    }
    
    @Test
    void testUpdateUserEmail() {
        // Inherits all setup - no duplication
        User existingUser = createTestUser("user123");
        when(userRepository.findById("user123")).thenReturn(Optional.of(existingUser));
        
        User result = userService.updateUserEmail("user123", "newemail@example.com");
        
        // Assertions
        assertNotNull(result);
        assertEquals("newemail@example.com", result.getEmail());
        verify(userRepository).save(any(User.class));
    }
}
```

## Detection and Prevention Strategies

### Detection Techniques
1. **Code Review Checklists**: Include duplication checks in review process
2. **Static Analysis Tools**: 
   - SonarQube (duplication detection)
   - CPD (Copy-Paste Detector) - part of PMD
   - Simian
   - JCopy
   - Duploc
3. **IDE Features**:
   - IntelliJ IDEA: "Analyze > Run Inspection by Name > Duplicated code fragment"
   - Eclipse: "Find Duplicated Lines" plugin
   - Visual Studio: Code analysis tools
4. **Manual Techniques**:
   - Grep for similar patterns
   - File comparison tools
   - Architectural reviews focused on modularity
5. **Metrics Monitoring**:
   - Track duplication percentage over time
   - Set thresholds and alerts for increases
   - Correlate with defect rates

### Prevention Strategies
1. **Education and Awareness**:
   - Teach DRY principle early and often
   - Show real-world costs of duplication in your codebase
   - Share refactoring success stories
   
2. **Process Improvements**:
   - Definition of Done: "No unnecessary duplication"
   - Pair programming to catch duplication early
   - Mob programming for complex refactoring
   - Regular refactoring sprints dedicated to deduplication
   
3. **Tooling and Environment**:
   - IDE templates for common patterns
   - Code snippets library for reusable solutions
   - Shared utility libraries
   - Architectural decision records for common patterns
   
4. **Architectural Practices**:
   - Micro-services or modular monoliths with clear boundaries
   - Plugin/extension architectures
   - Service-oriented design
   - Library-first mindset
   
5. **Leadership and Culture**:
   - Reward simplicity and reuse
   - Make refactoring visible and valued
   - Leaders model good behavior
   - Blameless post-mortems when duplication causes issues
   
6. **Testing Practices**:
   - Test-driven development encourages simplicity
   - Mutation testing can reveal redundant code
   - Property-based testing highlights generalizations
   
### Refactoring Process for Existing Duplication
1. **Identify**: Use tools to find duplication hotspots
2. **Prioritize**: Focus on high-change, high-impact areas first
3. **Isolate**: Extract duplicated code into methods/classes without changing behavior
4. **Replace**: Replace all instances with calls to the new shared code
5. **Test**: Verify behavior hasn't changed
6. **Refactor**: Improve the extracted code (make it more general, robust, etc.)
7. **Repeat**: Continue until duplication is eliminated or reduced to acceptable levels

### Guidelines for When NOT to Eliminate Duplication
1. **Coincidental Similarity**: Two pieces of code that look similar but serve different purposes and will diverge
2. **Very Small Amounts**: Trivial duplication (e.g., 2-3 lines) where abstraction would be more complex
3. **Different Rates of Change**: Code that happens to be similar now but will change independently
4. **Performance Critical Paths**: Rare cases where indirection from abstraction causes measurable performance issues
5. **Legacy Integration Boundaries**: Duplication at anti-corruption layers is sometimes justified
6. **Technology Boundaries**: Similar logic in different languages/runtime environments may be necessary
7. **Temporary Expediency**: Short-term duplication with clear plan to resolve (technical debt with expiration date)

## Measuring the Impact of Duplication Reduction

### Quantitative Metrics
1. **Duplication Percentage**: (% of lines that are duplicated)
2. **Mean Time to Repair (MTTR)**: Track bug fix times before/after deduplication
3. **Defect Density**: Bugs per KLOC in deduplicated vs duplicated areas
4. **Development Velocity**: Story points completed per iteration
5. **Code Churn**: Frequency of changes to duplicated areas
6. **Merge Conflict Rate**: Reduction in conflicts during integration
7. **Onboarding Time**: Time for new developers to become productive

### Qualitative Benefits
1. **Improved Readability**: Less noise, clearer intent
2. **Reduced Cognitive Load**: Fewer variations to remember
3. **Increased Confidence**: Making changes in one place affects all uses
4. **Better Documentation**: Single source of truth for behavior
5. **Enhanced Reusability**: Components naturally become more reusable
6. **Consistent Behavior**: Eliminates "it works here but not there" issues
7. **Easier Testing**: Fewer test cases needed to cover variations

## Thresholds and Guidelines
- **Acceptable Duplication**: <5% for most applications (depends on type and criticality)
- **Concerning Duplication**: 5-15% - investigate and plan remediation
- **High Duplication**: >15% - prioritize refactoring effort
- **Critical Duplication**: >25% in core domains - immediate attention required
- **Trend Matters**: Increasing duplication percentage is concerning even if absolute value is low

## Related Concepts and Practices
- **Single Source of Truth (SSOT)**: architectural principle extending DRY beyond code
- **Database Normalization**: applying DRY principles to data design
- **Configuration Management**: avoiding duplicated configuration settings
- **Documentation DRY**: avoiding duplicated documentation (use references/includes)
- **Test DRY**: avoiding duplicated test code (use helpers, builders, factories)
- **Infrastructure as Code DRY**: avoiding duplicated infrastructure definitions
- **API DRY**: avoiding duplicated endpoint definitions or request/response handling
- **UI/UX DRY**: avoiding duplicated interface components or patterns
- **Design Patterns**: Many patterns (Template Method, Strategy, etc.) exist to eliminate duplication
- **Refactoring Catalog**: Martin Fowler's book contains many techniques for eliminating duplication

## References
- Andrew Hunt & David Thomas. "The Pragmatic Programmer": From Journeyman to Master - Section on DRY principle
- Martin Fowler. "Refactoring: Improving the Design of Existing Code" - Chapters on extracting methods, classes, etc.
- Robert C. Martin. "Clean Code: A Handbook of Agile Software Craftsmanship" - Chapters on DRY and abstractions
- Kent Beck. "Implementation Patterns" - Patterns for avoiding duplication
- Joshua Kerievsky. "Refactoring to Patterns" - How to apply patterns to eliminate duplication
- Brian Goetz et al. "Java Concurrency in Practice" - Avoiding duplication in concurrent code
- Paul DuBois. "MySQL Cookbook" - Examples of eliminating SQL duplication
- Steve McConnell. "Code Complete" - Sections on minimizing complexity through abstraction
- W. Wilson et al. "Software Factories" - Assemblies and model-driven approaches to eliminate duplication
- Greg Young. "CQRS Documents" - Command Query Responsibility Segregation as a way to separate concerns and reduce duplication
- Udi Dahan. "Don't Develop Load-Balanced Systems" - Insights on where duplication might be appropriate
- Daniel Terhorst-North. "Introducing BDD" - Behavior-driven development as a way to establish shared understanding and reduce requirement duplication
- Liz Keogh. "A Little Bit of Cojones" - Behavior-driven development techniques
- Gojko Adzic. "Specification by Example" - Reducing requirements documentation duplication
- Jason Van Zyle. "Version Control by Example" - Using version control to manage shared code and reduce duplication duplication
- Linus Torvalds. "Linus on Git" - Where he talks about distributed version code sharing