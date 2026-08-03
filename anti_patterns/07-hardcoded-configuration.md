# Hardcoded Configuration Anti-Pattern

## Description
Hardcoded configuration occurs when configuration values, settings, or parameters are embedded directly in source code rather than being externalized to configuration files, environment variables, or other external sources. This makes the application inflexible, difficult to deploy across different environments, and requires recompilation and redeployment for any configuration changes.

## Characteristics
- **Magic Numbers and Strings**: Literal values scattered throughout code without explanation
- **Environment-Specific Values**: Hardcoded URLs, ports, paths, or credentials for specific environments
- **Business Rules in Code**: Configuration-driven behavior embedded as conditional logic
- **Duplicate Configuration**: Same values repeated in multiple places
- **Commented-Out Code**: Configuration alternatives left as comments instead of proper version control
- **Build-Time Configuration**: Values that require recompilation to change
- **Environment Detection**: Code that checks hostname, username, or paths to determine behavior
- **Hardcoded Credentials**: Passwords, API keys, or secrets embedded in source
- **File Path Dependencies**: Absolute or relative paths that assume specific directory structures
- **Protocol and Port Numbers**: Hardcoded network specifics that vary by environment
- **Third-Party Service Endpoints**: URLs for external services that change between environments
- **Feature Toggles**: Hardcoded boolean flags instead of external configuration
- **Timeout and Threshold Values**: Performance-related constants that need tuning
- **Internationalization Values**: Hardcoded strings that should be externalized for i18n
- **Database Connection Strings**: Connection details embedded in data access code
- **Messaging Queue Details**: Hardcoded exchange names, routing keys, or topic names
- **Cache Configuration**: Size, eviction policies, or TTL values hardcoded
- **Logging Configuration**: Log levels, appenders, or patterns embedded in code
- **Security Parameters**: Token expiration, encryption algorithms, or key sizes hardcoded
- **UI/UX Constants**: Dimensions, colors, or fonts hardcoded instead of theme-based

## Root Causes
- **Deployment Inexperience**: Lack of understanding about different deployment environments
- **Prototyping Mindset**: Treating temporary solutions as permanent
- **Perceived Simplicity**: Belief that hardcoding is simpler than configuration management
- **Fear of Complexity**: Avoiding configuration systems seen as overly complex
- **Lack of Standards**: No established patterns for configuration management in team/organization
- **Time Pressure**: Quick fix that becomes permanent due to delivery pressures
- **Developer Convenience**: Easier to hardcode than to set up configuration infrastructure
- **Inadequate Tooling**: Poor support for configuration management in development environment
- **Configuration Anxiety**: Fear of misconfiguration leading to preferring "known good" hardcoded values
- **Version Control Concerns**: Worry about exposing sensitive configuration in version control
- **Environment Parity Issues**: Difficulty replicating production-like environments for testing
- **Vendor Lock-in**: Proprietary systems that discourage external configuration
- **Knowledge Gaps**: Lack of awareness about configuration best practices and tools
- **Inconsistent Practices**: Different team members using different approaches
- **Legacy System Influence**: Copying patterns from older systems without questioning them
- **Performance Misconceptions**: Belief that indirection from configuration causes performance issues
- **Security Misunderstandings**: Belief that hardcoded secrets are more secure than externalized ones
- **Infrastructure Limitations**: Lack of proper configuration management infrastructure
- **Organizational Silos**: Separation between development and operations teams

## Impact on System
- **Deployment Inflexibility**: Cannot deploy to different environments without code changes
- **Compilation Requirement**: Configuration changes require recompilation and redeployment
- **Security Risks**: Hardcoded secrets exposed in source control and binaries
- **Environment Inconsistency**: Different behaviors in dev/test/prod due to undetected differences
- **Configuration Drift**: Gradual divergence between environments as hotfixes accumulate
- **Operational Overhead**: Need for specialized knowledge to make simple configuration changes
- **Slow Response to Incidents**: Inability to quickly adjust timeouts, thresholds, or feature flags
- **Testing Complications**: Difficulty testing edge cases or failure scenarios
- **Performance Tuning Delays**: Inability to tune performance parameters without code changes
- **Feature Flag Limitations**: Cannot enable/disable features for specific users or percentages
- **Internationalization Barriers**: Cannot easily adapt to different languages or locales
- **Vendor Lock-in Increase**: Hardcoded integrations make switching providers difficult
- **Audit and Compliance Issues**: Inability to demonstrate proper change management controls
- **Knowledge Transfer Problems**: New team members must learn undocumented hardcoded values
- **Merge Conflicts**: Higher likelihood of conflicts when multiple people change same hardcoded values
- **Rollback Complexity**: Configuration changes tied to code make rollbacks more complicated
- **Resource Wastage**: Rebuilding and redeploying entire application for simple config changes
- **Frustration and Toil**: Operations teams frustrated by needing developers for simple changes
- **Inconsistent Behavior**: Same binary behaving differently in different environments due to undetected differences
- **Configuration Sprawl**: Configuration scattered across multiple files, formats, and locations
- **Loss of Configuration History**: No audit trail of when and why configuration changed

## Examples

### Bad Example (Magic Numbers and Strings)
```java
// Service class littered with magic numbers
@Service
public class OrderProcessingService {
    // What does 7 mean? 30? 100? 0.05? 3? 24? 90? 5?
    // No way to tell without reading comments or documentation
    
    private static final int MAX_ORDER_ITEMS_PER_USER = 7;
    private static final int ORDER_PROCESSING_TIMEOUT_SECONDS = 30;
    private static final int MAX_RETRY_ATTEMPTS = 3;
    private static final double DISCOUNT_THRESHOLD = 0.05; // 5%
    private static final int BATCH_SIZE = 100;
    private static final int HOURS_IN_DAY = 24;
    private static final int DAYS_FOR_RETURN_POLICY = 90;
    private static final int LOYALTY_POINTS_PER_DOLLAR = 5;
    
    public ProcessingResult processOrder(Order order) {
        // Magic number used without explanation
        if (order.getItems().size() > MAX_ORDER_ITEMS_PER_USER) {
            throw new ValidationException("Too many items in order");
        }
        
        // Another magic number
        if (order.getTotalAmount() < 10.0) {
            // Why 10.0? Minimum order value? Shipping threshold?
            return processSmallOrder(order);
        }
        
        // Timeout value - is this in seconds? milliseconds?
        // What happens if we exceed it?
        return processWithTimeout(order, ORDER_PROCESSING_TIMEOUT_SECONDS);
    }
    
    private ProcessingResult processWithTimeout(Order order, int timeoutSeconds) {
        // What do these numbers mean?
        int startTime = (int) (System.currentTimeMillis() / 1000);
        while (!isOrderProcessed(order)) {
            if ((int) (System.currentTimeMillis() / 1000) - startTime > timeoutSeconds) {
                throw new TimeoutException("Order processing timed out");
            }
            
            // Magic numbers for retry logic
            try {
                Thread.sleep(500); // Why 500ms? Exponential backoff? Fixed interval?
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            
            // Another magic number - what's the significance of 3 retries?
            static int retryCount = 0;
            if (retryCount++ > MAX_RETRY_ATTEMPTS) {
                throw new ProcessingException("Max retries exceeded");
            }
        }
        return buildResult(order);
    }
}

// Even worse - hardcoded strings that should be configurable
public class NotificationService {
    // What are these strings? Why these specific values?
    private static final String EMAIL_FROM_ADDRESS = "noreply@company.com";
    private static final String SMS_SENDER_ID = "COMPANY";
    private static final String PUSH_NOTIFICATION_TITLE = "New Update";
    private static final String EMAIL_TEMPLATE_PATH = "/templates/email/welcome.html";
    private static final String SMS_GATEWAY_URL = "https://sms.provider.com/api/send";
    private static final String PUSH_GATEWAY_URL = "https://push.provider.com/v1/push";
    private static final String EMAIL_SUBJECT_PREFIX = "[Company] ";
    private static final String DEFAULT_LANGUAGE = "en";
    private static final String DATE_FORMAT_PATTERN = "yyyy-MM-dd HH:mm:ss";
    private static final String TIME_ZONE_ID = "America/New_York";
    private static final int EMAIL_PORT = 587;
    private static final String EMAIL_HOST = "smtp.emailprovider.com";
    private static final String EMAIL_USERNAME = "smtp_user";
    private static final String EMAIL_PASSWORD = "smtp_password_123"; // HARDCODED CREDENTIALS!
    
    public void sendWelcomeEmail(User user) {
        // Hardcoded email specifics
        MimeMessage message = new MimeMessage(session);
        message.setFrom(new InternetAddress(EMAIL_FROM_ADDRESS));
        message.addRecipient(Message.RecipientType.TO, new InternetAddress(user.getEmail()));
        message.setSubject(EMAIL_SUBJECT_PREFIX + "Welcome to our service!");
        message.setSentDate(new Date());
        
        // Hardcoded template path - what if we want to test different templates?
        String template = loadTemplate(EMAIL_TEMPLATE_PATH);
        message.setContent(replaceTemplateVariables(template, user), "text/html");
        
        // Hardcoded SMTP settings
        Transport transport = session.getTransport("smtp");
        transport.connect(EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD);
        try {
            transport.sendMessage(message, message.getAllRecipients());
        } finally {
            transport.close();
        }
    }
}
```

### Bad Example (Environment-Specific Hardcoding)
```java
// Configuration that assumes specific environment
public class DatabaseConfig {
    // These values work ONLY in the developer's local environment
    private static final String JDBC_URL = "jdbc:postgresql://localhost:5432/mydb";
    private static final String USERNAME = "dev_user";
    private static final String PASSWORD = "dev_password_123";
    
    // What happens when deployed to test/stage/prod?
    // Will fail with connection refused or authentication errors
    
    public Connection getConnection() throws SQLException {
        return DriverManager.getConnection(JDBC_URL, USERNAME, PASSWORD);
    }
}

// Even worse - environment detection via hostname
public class ServiceConfig {
    private static final String SERVICE_URL;
    
    static {
        String hostname = InetAddress.getLocalHost().getHostName();
        if (hostname.contains("dev") || hostname.contains("localhost")) {
            SERVICE_URL = "http://localhost:8080/api";
        } else if (hostname.contains("test")) {
            SERVICE_URL = "https://test-service.company.com/api";
        } else if (hostname.contains("stg")) {
            SERVICE_URL = "https://stg-service.company.com/api";
        } else {
            // Assume production - but what if hostname doesn't match any pattern?
            SERVICE_URL = "https://service.company.com/api";
        }
    }
    
    public static String getServiceUrl() {
        return SERVICE_URL;
    }
}

// The problems with this approach:
// 1. Fragile hostname patterns - what if naming convention changes?
// 2. No way to override for special cases (testing, debugging, etc.)
// 3. Difficult to test - need to mock InetAddress.getLocalHost()
// 4. Doesn't work in containerized environments where hostname is random
// 5. Violates parity between environments - same binary behaves differently
// 6. No central place to see all environment-specific values
// 7. Adding new environments requires code changes and redeployment
// 8. Impossible to have multiple instances of same service on same machine
// 9. Cloud environments often assign random hostnames
// 10. Load balancers and proxies often terminate SSL, making scheme detection wrong
```

### Bad Example (Business Rules in Code)
```java
// Pricing logic with hardcoded business rules
@Service
public class PricingService {
    // What are these percentages based on? When do they change?
    // Why 10% for premium? 5% for bulk? Where are these defined?
    private static final double PREMIUM_CUSTOMER_DISCOUNT = 0.10;
    private static final double BULK_ORDER_THRESHOLD = 100.0;
    private static final double BULK_ORDER_DISCOUNT = 0.05;
    private static final double SEASONAL_SUMMER_MULTIPLIER = 1.15;
    private static final double SEASONAL_WINTER_MULTIPLIER = 0.85;
    private static final double NEW_CUSTOMER_BONUS = 25.0; // Loyalty points?
    private static final int LOYALTY_TIER_1_THRESHOLD = 500;
    private static final double LOYALTY_TIER_1_DISCOUNT = 0.02;
    private static final int LOYALTY_TIER_2_THRESHOLD = 2000;
    private static final double LOYALTY_TIER_2_DISCOUNT = 0.05;
    private static final int LOYALTY_TIER_3_THRESHOLD = 5000;
    private static
    private static final double LOYALTY_TIER_3_DISCOUNT = 0.10;
    
    public double calculateFinalPrice(BasePrice basePrice, Customer customer, Order order) {
        double price = basePrice.getAmount();
        
        // Hardcoded business rules scattered throughout
        if (customer.isPremiumMember()) {
            price *= (1 - PREMIUM_CUSTOMER_DISCOUNT);
        }
        
        if (order.getTotalAmount() > BULK_ORDER_THRESHOLD) {
            price *= (1 - BULK_ORDER_DISCOUNT);
        }
        
        // Seasonal adjustments - hardcoded months
        int month = order.getDate().getMonthValue();
        if (month >= 6 && month <= 8) { // June-August
            price *= SEASONAL_SUMMER_MULTIPLIER;
        } else if (month <= 2 || month == 12) { // Dec-Feb
            price *= SEASONAL_WINTER_MULTIPLIER;
        }
        
        // Loyalty program - hardcoded thresholds and values
        int loyaltyPoints = customer.getLoyaltyPoints();
        if (loyaltyPoints >= LOYALTY_TIER_3_THRESHOLD) {
            price *= (1 - LOYALTY_TIER_3_DISCOUNT);
            // Also add bonus points?
        } else if (loyaltyPoints >= LOYALTY_TIER_2_THRESHOLD) {
            price *= (1 - LOYALTY_TIER_2_DISCOUNT);
        } else if (loyaltyPoints >= LOYALTY_TIER_1_THRESHOLD) {
            price *= (1 - LOYALTY_TIER_1_DISCOUNT);
        }
        
        // New customer bonus - hardcoded date comparison
        LocalDate thirtyDaysAgo = LocalDate.now().minusDays(30);
        if (customer.getCreatedDate().isAfter(thirtyDaysAgo)) {
            price -= NEW_CUSTOMER_BONUS; // Flat amount discount?
        }
        
        // What happens when business wants to change these rules?
        // Need to find all these hardcoded values, change them, test, redeploy
        // What if they want to add A/B testing or gradual rollout?
        // What if they want to make these rules configurable per region or channel?
        return Math.max(0, price); // Don't go negative - another hardcoded rule?
    }
}
```

### Bad Example (Commented-Out Code as Configuration)
```java
// Configuration maintained through commenting/uncommenting - HORRIBLE practice
public class FeatureService {
    // To switch between implementations, you comment/uncomment lines
    // This prevents proper version control and makes tracking changes impossible
    
    public PaymentProcessor getPaymentProcessor() {
        // Option 1: Stripe
        // return new StripePaymentProcessor(
        //     "pk_test_1234567890abcdef", 
        //     "sk_test_1234567890abcdef"
        // );
        
        // Option 2: PayPal
        // return new PayPalPaymentProcessor(
        //     "client_id_sandbox",
        //     "secret_sandbox",
        //     "https://api.sandbox.paypal.com"
        // );
        
        // Option 3: Braintree
        // return new BraintreePaymentProcessor(
        //     "merchant_id",
        //     "public_key",
        //     "private_key",
        //     true // sandbox
        // );
        
        // Option 4: Authorize.net
        // return new AuthorizeNetPaymentProcessor(
        //     "API_LOGIN_ID",
        //     "TRANSACTION_KEY",
        //     false // test mode
        // );
        
        // Currently active option - but how do you know?
        // What if someone forgets to uncomment the right one?
        // What if two are accidentally uncommented?
        // What if commented code becomes outdated?
        return new StripePaymentProcessor(
            "pk_live_1234567890abcdef", 
            "sk_live_1234567890abcdef"
        );
    }
}

// Even worse - commented code in XML configuration
<!--
<bean id="dataSource" class="org.apache.commons.dbcp.BasicDataSource">
    <property name="driverClassName" value="com.mysql.jdbc.Driver"/>
    <property name="url" value="jdbc:mysql://localhost:3306/mydb"/>
    <property name="username" value="root"/>
    <property name="password" value="password"/>
</bean>
-->

<!--
<bean id="dataSource" class="org.apache.commons.dbcp.BasicDataSource">
    <property name="driverClassName" value="org.postgresql.Driver"/>
    <property name="url" value="jdbc:postgresql://localhost:5432/mydb"/>
    <property name="username" value="postgres"/>
    <property name="password" value="postgres"/>
</bean>
-->

<bean id="dataSource" class="org.apache.commons.dbcp.BasicDataSource">
    <property name="driverClassName" value="oracle.jdbc.driver.OracleDriver"/>
    <property name="url" value="jdbc:oracle:thin:@//localhost:1521/ORCL"/>
    <property name="username" value="app_user"/>
    <property name="password" value="app_password"/>
</bean>

// Problems:
// 1. Version control shows meaningless changes when uncommenting/commenting
// 2. Difficult to review - reviewers must mentally track what's active
// 3. Easy to accidentally leave multiple configurations active
// 4. Commented code becomes stale and outdated
// 5. No history of when and why configurations were changed
// 6. No way to A/B test or do gradual rollouts
// 7. Impossible to automate deployment of different configurations
// 8. Build process might include commented code needs to parse comments to determine active config
// 9. XML validation might fail on commented-out invalid configurations
// 10. IDEs might not provide proper code completion/comments in commented sections
```

### Bad Example (Hardcoded File Paths)
```java
// Service that assumes specific directory structure
public class ReportGenerationService {
    // What if deployed to different OS? Different drive layout?
    // Different user permissions? Different disk space availability?
    private static final String REPORT_TEMPLATE_DIR = "/opt/company/reports/templates/";
    private static final String REPORT_OUTPUT_DIR = "/var/www/html/reports/";
    private static final String LOGO_FILE = "/opt/company/assets/logo.png";
    private static final String FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf";
    private static final String TEMP_DIR = "/tmp/report_generation/";
    private static final String WKHTMLTOPDF_PATH = "/usr/local/bin/wkhtmltopdf";
    
    public byte[] generatePdfReport(ReportData data, String reportType) throws Exception {
        // Hardcoded paths - will fail in different environments
        
        // Load template
        String templatePath = REPORT_TEMPLATE_DIR + reportType + ".html";
        String template = Files.readString(Paths.get(templatePath));
        
        // Process template with data
        String htmlContent = processTemplate(template, data);
        
        // Save to temporary file
        String tempHtmlPath = TEMP_DIR + "report_" + UUID.randomUUID() + ".html";
        Files.writeString(Paths.get(tempHtmlPath), htmlContent);
        
        // Convert to PDF using hardcoded external tool path
        String outputPath = REPORT_OUTPUT_DIR + "report_" + UUID.randomUUID() + ".pdf";
        ProcessBuilder pb = new ProcessBuilder(
            WKHTMLTOPDF_PATH,
            "--page-size", "Letter",
            "--margin-top", "10mm",
            "--margin-right", "10mm",
            "--margin-bottom", "10mm",
            "--margin-left", "10mm",
            tempHtmlPath,
            outputPath
        );
        
        Process process = pb.start();
        // ... wait for process, handle errors, etc.
        
        // Read output
        byte[] pdfBytes = Files.readAllBytes(Paths.get(outputPath));
        
        // Cleanup temporary files
        Files.deleteIfExists(Paths.get(tempHtmlPath));
        // Note: Often forget to cleanup output file - disk space leak!
        
        return pdfBytes;
    }
    
    // Similar issues with logo and font loading
    private void embedLogoAndFont(String htmlContent) {
        // What if these files don't exist or aren't readable?
        byte[] logoBytes = Files.readAllBytes(Paths.get(LOGO_FILE));
        byte[] fontBytes = Files.readAllBytes(Paths.get(FONT_FILE));
        // ... embed them in HTML
    }
}
```

### Bad Example (Hardcoded Third-Party Service Endpoints)
```java
// Integration service with hardcoded external endpoints
public class PaymentIntegrationService {
    // What happens when the provider changes their URLs?
    // What about sandbox vs production? 
    // What about different regions or instances?
    private static final String AUTH_URL = "https://api.paymentprovider.com/v1/auth";
    private static final String CHARGE_URL = "https://api.paymentprovider.com/v1/charges";
    private static final String REFUND_URL = "https://api.paymentprovider.com/v1/refunds";
    private static final String WEBHOOK_URL = "https://api.paymentprovider.com/v1/webhooks";
    private static final String THREE_DS_URL = "https://api.paymentprovider.com/v1/3ds";
    
    // What if we want to switch providers or use multiple providers?
    // What if we want to route different transaction types to different endpoints?
    // What if we want to implement circuit breaker or retry logic?
    
    public PaymentResponse processPayment(PaymentRequest request) {
        // Step 1: Authenticate
        String authToken = authenticateWithHardcodedEndpoint(AUTH_URL, request.getApiKey());
        
        // Step 2: Charge card
        PaymentResponse chargeResponse = chargeCard(
            CHARGE_URL, 
            authToken, 
            request.getCardDetails(),
            request.getAmount()
        );
        
        // Step 3: Handle 3D Secure if needed
        if (chargeResponse.requires3DSecure()) {
            String threeDsResult = handle3DSecure(
                THREE_DS_URL,
                authToken,
                chargeResponse.getThreeDsToken(),
                request.getBrowserInfo()
            );
            // ... process 3DS result
        }
        
        return chargeResponse;
    }
    
    private String authenticateWithHardcodedEndpoint(String url, String apiKey) {
        // Hardcoded timeout values
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setConnectTimeout(5000); // Why 5 seconds?
        connection.setReadTimeout(10000);   // Why 10 seconds?
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);
        
        try (OutputStream os = connection.getOutputStream()) {
            os.write(("apiKey=" + apiKey).getBytes());
            os.flush();
        }
        
        int responseCode = connection.getResponseCode();
        if (responseCode != 200) {
            throw new IOException("Authentication failed with code: " + responseCode);
        }
        
        // Hardcoded parsing assumptions
        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(connection.getInputStream()))) {
            StringBuilder response = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                response.append(line);
            }
            return new JSONObject(response.toString()).getString("token");
        }
    }
}
```

### Good Approach (Externalized Configuration)
```java
// Configuration class using typesafe configuration (Typesafe Config, Spring Boot @ConfigurationProperties, etc.)
@ConfigurationProperties("app")
@ConstructorBinding
@Component
@RequiredArgsConstructor
public class AppConfig {
    // All configuration externalized and typed
    private final int maxOrderItemsPerUser;
    private final Duration orderProcessingTimeout;
    private final int maxRetryAttempts;
    private final double discountThresholdPercentage;
    private final int batchSize;
    private final int hoursInDay;
    private final int daysForReturnPolicy;
    private final int loyaltyPointsPerDollar;
    
    // Notification configuration
    private final String emailFromAddress;
    private final String smsSenderId;
    private final String pushNotificationTitle;
    private final String emailTemplatePath;
    private final String smsGatewayUrl;
    private final String pushGatewayUrl;
    private final String emailSubjectPrefix;
    private final String defaultLanguage;
    private final String dateFormatPattern;
    private final String timeZoneId;
    private final int emailPort;
    private final String emailHost;
    private final String emailUsername;
    // Password handled separately via secrets management
    
    // Database configuration
    private final String jdbcUrl;
    private final String dbUsername;
    // Password handled separately
    
    // Service endpoints
    private final String serviceUrl;
    
    // Pricing configuration
    private final double premiumCustomerDiscount;
    private final double bulkOrderThreshold;
    private final double bulkOrderDiscount;
    private final Map<Season, Double> seasonalMultipliers;
    private final double newCustomerBonusAmount;
    private final Map<LoyaltyTier, Double> loyaltyTierDiscounts;
    private final LoyaltyTierConfig loyaltyTiers;
    
    // External service endpoints
    private final String paymentAuthUrl;
    private final String paymentChargeUrl;
    private final String paymentRefundUrl;
    private final String paymentWebhookUrl;
    private final String paymentThreeDsUrl;
    
    // File system paths
    private final String reportTemplateDir;
    private final String reportOutputDir;
    private final String logoFilePath;
    private final String fontFilePath;
    private final String tempDir;
    private final String wkhtmltopdfPath;
    
    // Getters for all fields
    // No setters - immutable after construction
}

// Usage in services - all dependencies explicit
@Service
@RequiredArgsConstructor
public class OrderProcessingService {
    private final AppConfig config;
    
    public ProcessingResult processOrder(Order order) {
        // All values come from configuration - clear, understandable, changeable
        if (order.getItems().size() > config.getMaxOrderItemsPerUser()) {
            throw new ValidationException("Too many items in order");
        }
        
        if (order.getTotalAmount() < 10.0) {
            return processSmallOrder(order);
        }
        
        return processWithTimeout(order, config.getOrderProcessingTimeout());
    }
    
    private ProcessingResult processWithTimeout(Order order, Duration timeout) {
        long startTimeMillis = System.currentTimeMillis();
        while (!isOrderProcessed(order)) {
            long elapsedMillis = System.currentTimeMillis() - startTimeMillis;
            if (elapsedMillis > timeout.toMillis()) {
                throw new TimeoutException("Order processing timed out");
            }
            
            // Configurable retry interval with exponential backoff
            try {
                Thread.sleep(config.getRetryBaseDelayMillis());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            
            // Configurable max attempts
            if (retryCount++ > config.getMaxRetryAttempts()) {
                throw new ProcessingException("Max retries exceeded");
            }
        }
        return buildResult(order);
    }
}

// Even better - use proper configuration framework
@ConfigurationProperties("notification")
@ConstructorBinding
@Component
@RequiredArgsConstructor
public class NotificationConfig {
    private final String emailFromAddress;
    private final String smsSenderId;
    private final String pushNotificationTitle;
    private final String emailTemplatePath;
    private final String smsGatewayUrl;
    private final String pushGatewayUrl;
    private final String emailSubjectPrefix;
    private final String defaultLanguage;
    private final String dateFormatPattern;
    private final String timeZoneId;
    private final int emailPort;
    private final String emailHost;
    private final String emailUsername;
    // Email password handled via secrets manager injection
    
    // Getters
}

@Service
@RequiredArgsConstructor
public class NotificationService {
    private final NotificationConfig config;
    private final SecretsManager secretsManager; // For handling passwords securely
    private final EmailTemplateEngine templateEngine;
    
    public void sendWelcomeEmail(User user) {
        // All configuration explicit and externalized
        MimeMessage message = new MimeMessage(session);
        message.setFrom(new InternetAddress(config.getEmailFromAddress()));
        message.addRecipient(Message.RecipientType.TO, new InternetAddress(user.getEmail()));
        message.setSubject(config.getEmailSubjectPrefix() + "Welcome to our service!");
        message.setSentDate(new Date());
        
        // Template path from configuration
        String template = templateEngine.loadTemplate(config.getEmailTemplatePath());
        message.setContent(
            templateEngine.replaceTemplateVariables(template, user), 
            "text/html"
        );
        
        // SMTP configuration from configuration + secrets
        String emailPassword = secretsManager.getSecret("email/smtp/password");
        Transport transport = session.getTransport("smtp");
        transport.connect(
            config.getEmailHost(), 
            config.getEmailPort(), 
            config.getEmailUsername(), 
            emailPassword
        );
        
        try {
            transport.sendMessage(message, message.getAllRecipients());
        } finally {
            transport.close();
        }
    }
}

// Configuration backed by external files (application.yaml, application.properties, etc.)
# application.yaml
app:
  max-order-items-per-user: 7
  order-processing-timeout-seconds: 30
  max-retry-attempts: 3
  discount-threshold-percentage: 0.05
  batch-size: 100
  hours-in-day: 24
  days-for-return-policy: 90
  loyalty-points-per-dollar: 5

notification:
  email-from-address: noreply@company.com
  sms-sender-id: COMPANY
  push-notification-title: "New Update"
  email-template-path: templates/email/welcome.html
  sms-gateway-url: https://sms.provider.com/api/send
  push-gateway-url: https://push.provider.com/v1/push
  email-subject-prefix: "[Company] "
  default-language: en
  date-format-pattern: yyyy-MM-dd HH:mm:ss
  time-zone-id: America/New_York
  email-port: 587
  email-host: smtp.emailprovider.com
  email-username: smtp_user
  # email-password: handled by secrets manager

database:
  jdbc-url: jdbc:postgresql://db-host:5432/mydb
  username: db_user
  # password: handled by secrets manager

service:
  url: https://api.company.com

pricing:
  premium-customer-discount: 0.10
  bulk-order-threshold: 100.0
  bulk-order-discount: 0.05
  seasonal-multipliers:
    SUMMER: 1.15
    WINTER: 0.85
  new-customer-bonus-amount: 25.0
  loyalty-tiers:
    - threshold: 500
      discount: 0.02
    - threshold: 2000
      discount: 0.05
    - threshold: 5000
      discount: 0.10

external-services:
  payment:
    auth-url: https://api.paymentprovider.com/v1/auth
    charge-url: https://api.paymentprovider.com/v1/charges
    refund-url: https://api.paymentprovider.com/v1/refunds
    webhook-url: https://api.paymentprovider.com/v1/webhooks
    three-ds-url: https://api.paymentprovider.com/v1/3ds

file-system:
  report-template-dir: /opt/company/reports/templates/
  report-output-dir: /var/www/html/reports/
  logo-file-path: /opt/company/assets/logo.png
  font-file-path: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
  temp-dir: /tmp/report_generation/
  wkhtmltopdf-path: /usr/local/bin/wkhtmltopdf

# Environment-specific overrides can be provided via:
# - application-{profile}.yaml
# - Environment variables: APP_MAX_ORDER_ITEMS_PER_USER=10
# - Command line arguments: --app.max-order-items-per-user=10
# - Docker/Kubernetes secrets and config maps
# - Cloud provider parameter stores (AWS SSM, Azure Key Vault, GCP Secret Manager)
# - Consul, Etcd, Zookeeper for dynamic configuration
```

### Good Approach (Environment-Specific Configuration)
```java
// Instead of environment detection via hostname, use proper profiles
@Configuration
@Profile("dev")
@Component
@RequiredArgsConstructor
public class DevDatabaseConfig {
    private final SecretsManager secretsManager;
    
    @Bean
    public DataSource dataSource() {
        String url = "jdbc:postgresql://localhost:5432/mydb_dev";
        String username = "dev_user";
        String password = secretsManager.getSecret("database/dev/password");
        
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(url);
        config.setUsername(username);
        config.setPassword(password);
        // ... other dev-specific settings (more logging, etc.)
        
        return new HikariDataSource(config);
    }
}

@Configuration
@Profile("test")
@Component
@RequiredArgsConstructor
public class TestDatabaseConfig {
    private final SecretsManager secretsManager;
    
    @Bean
    public DataSource dataSource() {
        // Use testcontainers or similar for isolated testing
        PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:13")
                .withDatabaseName("mydb_test")
                .withUsername("test_user")
                .withPassword(secretsManager.getSecret("database/test/password"));
        
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(postgres.getJdbcUrl());
        config.setUsername(postgres.getUsername());
        config.setPassword(postgres.getPassword());
        // ... test-specific settings
        
        return new HikariDataSource(config);
    }
}

@Configuration
@Profile("prod")
@Component
@RequiredArgsConstructor
public class ProdDatabaseConfig {
    private final SecretsManager secretsManager;
    
    @Bean
    public DataSource dataSource() {
        String url = secretsManager.getSecret("database/prod/url");
        String username = secretsManager.getSecret("database/prod/username");
        String password = secretsManager.getSecret("database/prod/password");
        
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(url);
        config.setUsername(username);
        config.setPassword(password);
        // ... production-specific settings (connection pooling, etc.)
        
        return new HikariDataSource(config);
    }
}

// Usage - same code works in all environments
@Service
@RequiredArgsConstructor
public class OrderService {
    private final DataSource dataSource;
    
    public Order getOrderById(Long id) {
        try (Connection connection = dataSource.getConnection()) {
            // ... use connection
        }
    }
}

// Activation via:
// - SPRING_PROFILES_ACTIVE=dev test prod
# - spring.profiles.active=dev,test
# - Environment specific application files
# - Command line: --spring.profiles.active=dev
# - Kubernetes environments
# - Docker compose profiles
```

### Good Approach (Business Rules Externalized)
```java
// Business rules engine using external configuration
@Service
@RequiredArgsConstructor
public class PricingService {
    private final PricingRules pricingRules;
    private final CustomerService customerService;
    
    public double calculateFinalPrice(BasePrice basePrice, Customer customer, Order order) {
        double price = basePrice.getAmount();
        
        // All business rules come from external configuration
        if (customerService.isPremiumMember(customer.getId())) {
            price *= (1 - pricingRules.getPremiumCustomerDiscount());
        }
        
        if (order.getTotalAmount() > pricingRules.getBulkOrderThreshold()) {
            price *= (1 - pricingRules.getBulkOrderDiscount());
        }
        
        // Seasonal adjustments from configuration
        Season currentSeason = Season.fromDate(order.getDate());
        Double seasonalMultiplier = pricingRules.getSeasonalMultiplier(currentSeason);
        if (seasonalMultiplier != null) {
            price *= seasonalMultiplier;
        }
        
        // Loyalty program from configuration
        int loyaltyPoints = customerService.getLoyaltyPoints(customer.getId());
        LoyaltyDiscount loyaltyDiscount = pricingRules.getLoyaltyDiscountForPoints(loyaltyPoints);
        if (loyaltyDiscount != null) {
            price *= (1 - loyaltyDiscount.getDiscountRate());
        }
        
        // New customer bonus from configuration
        if (customerService.isNewCustomer(customer.getId(), pricingRules.getNewCustomerDaysThreshold())) {
            price -= pricingRules.getNewCustomerBonusAmount();
        }
        
        // Apply any dynamic pricing adjustments
        price = pricingRules.applyDynamicAdjustments(price, customer, order);
        
        return Math.max(0, price); // Still hardcoded? Could be configurable too...
    }
}

// Configuration class for pricing rules
@ConfigurationProperties("pricing")
@ConstructorBinding
@Component
@RequiredArgsConstructor
public class PricingRules {
    private final double premiumCustomerDiscount;
    private final double bulkOrderThreshold;
    private final double bulkOrderDiscount;
    private final Map<Season, Double> seasonalMultipliers;
    private final double newCustomerBonusAmount;
    private final int newCustomerDaysThreshold;
    private final List<LoyaltyTier> loyaltyTiers;
    // ... other pricing rule configurations
    
    // Getters
    
    public LoyaltyDiscount getLoyaltyDiscountForPoints(int points) {
        return loyaltyTiers.stream()
            .filter(tier -> points >= tier.getThreshold())
            .findFirst()
            .map(LoyaltyTier::getDiscount)
            .orElse(null);
    }
    
    public double applyDynamicAdjustments(double basePrice, Customer customer, Order order) {
        // Implementation for dynamic pricing, A/B testing, etc.
        // Could consult external services, machine learning models, etc.
        return basePrice; // Simplified
    }
}

// Pricing rules externalized in YAML
# pricing.yaml or application.yaml under pricing:
pricing:
  premium-customer-discount: 0.10
  bulk-order-threshold: 100.0
  bulk-order-discount: 0.05
  seasonal-multipliers:
    SUMMER: 1.15
    WINTER: 0.85
    SPRING: 1.05
    FALL: 0.95
  new-customer-bonus-amount: 25.0
  new-customer-days-threshold: 30
  loyalty-tiers:
    - threshold: 500
      discount: 0.02
    - threshold: 2000
      discount: 0.05
    - threshold: 5000
      discount: 0.10

# To change business rules:
# 1. Update the configuration file
# 2. Redeploy (or use dynamic configuration refresh)
# 3. No code changes needed
# 
# For even more flexibility:
# - Store rules in database with admin UI
# - Use rule engine (Drools) for complex logic
# - Implement feature flags for gradual rollout
# - Use machine learning models for dynamic pricing
# - Allow per-customer or per-segment pricing rules
```

### Good Approach (Secrets Management)
```java
// NEVER hardcode credentials or secrets
@Service
@RequiredArgsConstructor
public class EmailService {
    private final EmailConfig config;
    private final SecretsManager secretsManager;
    
    public void sendEmail(EmailRequest request) {
        // Get password from secure secret store - NEVER in code
        String smtpPassword = secretsManager.getSecret("email/smtp/password");
        
        // All other configuration from external config
        Properties props = new Properties();
        props.put("mail.smtp.host", config.getEmailHost());
        props.put("mail.smtp.port", String.valueOf(config.getEmailPort()));
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.starttls.enable", "true");
        
        Session session = Session.getInstance(props, new Authenticator() {
            @Override
            protected PasswordAuthentication getPasswordAuthentication() {
                return new PasswordAuthentication(
                    config.getEmailUsername(), 
                    smtpPassword
                );
            }
        });
        
        // ... rest of email sending logic
    }
}

// Secrets manager implementations:
// - AWS Secrets Manager
// - Azure Key Vault
// - Google Cloud Secret Manager
// - HashiCorp Vault
// - Kubernetes Secrets
// - Docker Secrets
// - Spring Cloud Vault
// - Jasypt (for encrypting values in property files)
// - Custom wrapper around operating system keychains or credentials stores
```

## Detection and Prevention Strategies

### Detection Techniques
1. **Code Reviews**: Look for literals, especially strings that look like URLs, paths, numbers that seem arbitrary
2. **Static Analysis**:
   - Search for patterns like `jdbc:`, `http://`, `https://`, `/opt/`, `/var/`, `C:\\`, etc.
   - Find magic numbers (non-0, non-1, non-2 integers that aren't loop controls or array indices)
   - Detect hardcoded strings that look like credentials (password, secret, key, token)
   - Identify environment checks (`System.getenv()`, `InetAddress.getLocalHost()`, `System.getProperty()`)
   - Look for commented-out code that resembles configuration
   - Find use of `System.getProperty()` without default values
3. **Dependencies Analysis**:
   - Check for direct instantiation of configuration classes instead of injection
   - Look for service locator patterns or direct singleton access
   - Identify tight coupling to specific implementations (constructors with concrete types)
4. **Build Artifact Analysis**:
   - Examine compiled binaries/JARs/WARs for string literals
   - Use strings command or similar to find embedded configuration
   - Check Docker images for exposed secrets
5. **Runtime Monitoring**:
   - Watch for configuration-related failures in logs
   - Monitor for environment-specific behavior differences
   - Track deployment frequency for trivial configuration changes
6. **Architectural Review**:
   - Examine component boundaries for configuration dependencies
   - Check for proper separation of concerns between code and configuration
   - Validate that configuration can be changed without recompilation

### Prevention Strategies
1. **Architectural Guidelines**:
   - Externalize all configuration that might vary between environments or deployments
   - Use typesafe configuration objects with constructor binding
   - Implement proper secrets management for credentials
   - Apply the 12-factor app principles (especially III. Config)
   - Make configuration explicit in component interfaces
   
2. **Development Practices**:
   - Never commit secrets to version control (use .gitignore, git-crypt, etc.)
   - Use template configuration files with placeholders
   - Implement configuration validation at startup
   - Provide default values for development environments
   - Use environment-specific configuration files (application-dev.yaml, etc.)
   - Implement configuration change notification/reloading where appropriate
   
3. **Tooling and Automation**:
   - Use configuration management tools (Spring Boot Config, Micronaut Config, etc.)
   - Implement secrets management integration (AWS Secrets Manager, Vault, etc.)
   - Use configuration validation libraries (Hibernate Validator, etc.)
   - Implement configuration drift detection
   - Use infrastructure as code (Terraform, CloudFormation) for provisioning
   - Implement configuration testing in CI/CD pipelines
   
4. **Standards and Conventions**:
   - Establish naming conventions for configuration properties
   - Define configuration scopes (application-wide, service-specific, instance-specific)
   - Create configuration documentation standards
   - Establish secrets handling procedures and tools
   - Define configuration change management processes
   
5. **Education and Culture**:
   - Teach the 12-factor app principles
   - Share stories of deployment failures due to hardcoded configuration
   - Recognize and reward proper configuration management
   - Make configuration review part of pull request process
   - Include configuration in definition of done
   
6. **Refactoring Legacy Code**:
   - Identify configuration hotspots (files with most literals)
   - Apply strangler fig pattern: externalize one configuration at a time
   - Use feature flags to transition from hardcoded to configurable
   - Implement configuration validation tests
   - Track progress through metrics (reduced literals, increased injection usage)
   - Create configuration extraction scripts or refactoring tools

### Migration Strategies for Existing Code
1. **Inventory**: Scan codebase for literals, environment checks, and hardcoded values
2. **Prioritize**: Focus on security-sensitive values (credentials, secrets) first
3. **Abstract**: Create configuration interfaces before implementing externalization
4. **Replace Gradually**: Replace one hardcoded value at a time with configuration lookup
5. **Validate**: Ensure behavior remains unchanged after each replacement
6. **Document**: Maintain configuration documentation alongside code
7. **Test**: Write tests that verify configuration can be changed without code changes
8. **Automate**: Create scripts to help identify and extract hardcoded values
9. **Team Agreement**: Establish clear guidelines on what should be externalized
10. **Monitor**: Track configuration-related incidents and deployment frequency

## Configuration Hierarchy and Precedence
When implementing external configuration, establish a clear precedence order:
1. **Command Line Arguments** (highest priority - for override/testing)
2. **Environment Variables** (for container/platform provided values)
3. **Application-Specific Files** (application.yaml, application.properties)
4. **Profile-Specific Files** (application-dev.yaml, application-prod.yaml)
5. **Default Values** (in code or default configuration files)
6. **Hardcoded Fallbacks** (should ideally be eliminated, but sometimes necessary during transition)

## Related Concepts and Practices
- **The Twelve-Factor App**: Especially Factor III: Store config in the environment
- **Configuration as Code**: Treating configuration files with same rigor as application code
- **Infrastructure as Code**: Applying similar principles to infrastructure provisioning
- **Secrets Management**: Specialized handling for sensitive configuration values
- **Feature Toggles**: Managing feature lifecycle through configuration
- **Dynamic Configuration**: Configuration that can be changed without restart
- **Configuration Validation**: Ensuring configuration values are valid before use
- **Configuration Documentation**: Maintaining clear documentation of what each setting does
- **Environment Parity**: Ensuring similar configuration structure across environments
- **Immutable Infrastructure**: Where configuration is baked into images rather than modified at runtime
- **Blue/Green Deployments**: Where configuration travels with the application version
- **Canary Releases**: Where configuration can vary between release versions
- **A/B Testing**: Where configuration enables different user experiences
- **Blue/Green Configuration**: Where configuration itself can be deployed in patterns
- **Configuration Drift Detection**: Identifying and correcting configuration deviations
- **Immutable Configuration Objects**: Preventing runtime modification of configuration
- **Typesafe Configuration**: Configuration with compile-time checking and IDE support
- **Configuration Templates**: Standardized configuration files for different service types
- **Configuration Versioning**: Tracking changes to configuration over time
- **Configuration Auditing**: Logging who changed what configuration and when
- **Configuration Testing**: Automated tests that validate configuration correctness
- **Configuration Performance**: Ensuring configuration lookup doesn't become a bottleneck
- **Security Considerations**: Protecting sensitive configuration values at rest and in transit
- **Format

## References
- Martin Fowler. "Patterns of Enterprise Application Architecture": Chapters on configuration management
- Chris Richardson. "Microservices Patterns": Pattern: Externalized Configuration
- Josh Long & Kenny Bastani. "Spring Microservices in Action": Chapters on external configuration
- Craig Walls. "Spring in Action": Chapters on Spring Boot external configuration
- Paul Hammant. "Dependency Injection": Chapters on configuration management
- Markus Eisele. "Java EE 7 Development": Chapters on configuration and resources
- Bert Ertman & Ludo Huisman. "Configuring Spring Applications": Modern approaches to Spring configuration
- Petri Kainulainen. "Spring Data JPA Tutorial": Configuration aspects of Spring Data
- Eugen Paraschiv. "REST with Spring": Configuration for RESTful services
- Baeldung. Various articles on Spring Boot configuration, properties, and YAML
- Josh Long. "Cloud Native Java": Chapters on configuration in cloud-native applications
- Olivier Gérardin. "Micronaut in Action": Chapters on Micronaut configuration
- Shawn Clark & Presley Deveau. "Hibernate Tips": Configuration tips for Hibernate
- Craig Walls. "Spring Boot in Action": Chapters on externalized configuration in Spring Boot
- Alex Theedom. "Beginning Jakarta EE Web Development": Configuration chapters
- Manu Sinha. "JBoss Weld CDI for Java EE": Configuration aspects of CDI
- Ali Arsalan. "Java Cloud Development with Azure": Configuration in Azure cloud services
- Steve Poole & Robert Schott. "Hardcore JSF": Configuration in JSF applications
- Steven Harris. "BlackBerry Java Application Development": Configuration considerations
- Daniel Bryant et al. "Microservices Security in Action": Configuration security considerations
- Kenny Bastani & Josh Long. "Spring Microservices": Pattern: Service Discovery and Load Balancing
- Roland Huß. "Fabric8: DevOps for Java": Configuration in Fabric8 and Kubernetes
- Alex Soto Bueno & David García González. "Testing Java Microservices": Configuration testing strategies
- Richard Sitze. "Docker: Up and Running": Configuration in Docker containers
- Jerry Carter. "LDAP System Administration": Configuration in LDAP directories
- Tim Bray et al. "XML Schema": Configuration aspects of XML schema definition
- Elliotte Rusty Harold. "XML in a Nutshell": Configuration considerations in XML processing
- Craig Walls. "Spring Boot 2.0 in Action": Updated coverage of external configuration
- Josh Long & Kenny Bastani. "Building Blockchain Projects": Configuration considerations in blockchain applications
- Craig Larman. "Applying UML and Patterns": GRASP principles including information expert related to configuration
- Giovanni Asproni. "Test Driven Development in .NET": Configuration aspects of TDD
- Roy Osherove. "The Art of Unit Testing": Configuration considerations in test frameworks
- Micahel Feathers. "Working Effectively with Legacy Code": Techniques for dealing with hardcoded configuration
- Robert Martin. "Clean Code": Chapters on meaningful names and avoiding magic numbers
- Brian Kernighan & Dennis Ritchie. "The C Programming Language": Historical perspective on hardcoded values
- Donald Knuth. "Literate Programming": Approach to mixing documentation and code (relevant to configuration documentation)
- Doug McIlroy. "Mass Produced Software Components": Early thoughts on software configurability
- Ken Thompson. "Reflections on Trusting Trust": Security implications of trusting configuration sources
- Butler Lampson. "Hints for Computer System Design": Points 4 and 11 relevant to configuration and secrets
- Jim Gray. "Why Do Computers Stop and What Can Be Done?": Discussion on reliability and configuration faults