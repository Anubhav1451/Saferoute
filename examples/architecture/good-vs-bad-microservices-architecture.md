# Good vs Bad Microservices Architecture Examples

## Bad Example: Distributed Monolith Anti-Pattern

### Characteristics
- Services share a common database
- Synchronous communication chains causing tight coupling
- Shared libraries/services creating version coupling
- Distributed transactions requiring two-phase commit
- Services Deployed together due to dependencies
- Common error handling and logging infrastructure
- Shared caching layer causing contention

### Problems Introduced
- Cannot deploy services independently
- Failure in one service cascades to others
- Scaling requires scaling entire system
- Technology stack locked due to shared dependencies
- Debugging distributed transactions is extremely complex
- Team autonomy reduced due to coordination needs
- Performance bottlenecks in shared resources

### Code Example (Bad)
```java
// Service A - Direct database access to Service B's tables
@Service
public class OrderService {
    @Autowired
    private InventoryRepository inventoryRepo; // Direct access to another service's data!
    
    @Autowired
    private PaymentServiceClient paymentClient;
    
    public OrderResult placeOrder(OrderRequest request) {
        // Business logic spread across services without boundaries
        InventoryItem item = inventoryRepo.findById(request.getItemId());
        if (item == null || item.getQuantity() < request.getQuantity()) {
            throw new InsufficientInventoryException();
        }
        
        // Direct DB update - no service boundary
        item.setQuantity(item.getQuantity() - request.getQuantity());
        inventoryRepo.save(item);
        
        // Synchronous call chain
        PaymentResult payment = paymentClient.processPayment(request.getPaymentInfo());
        if (!payment.isSuccessful()) {
            // No rollback mechanism for inventory change!
            throw new PaymentFailedException();
        }
        
        return new OrderResult(true, "Order placed");
    }
}

// Service B - Inventory Service with direct external access
@Service
public class InventoryService {
    @Autowired
    private InventoryRepository repo;
    
    // Exposes internal implementation through repository
    public InventoryItem findById(String id) {
        return repo.findById(id);
    }
    
    public void save(InventoryItem item) {
        repo.save(item);
    }
}
```

### Deployment Architecture (Bad)
```
[Load Balancer]
       |
[Service A] <--DB Connection--> [Shared Database] <--DB Connection--> [Service B]
       |                               ^
       |                               |
[Service C] <--DB Connection-->       |
       |                               |
[Service D] <--API Calls--------------+
       |
[Shared Library JAR] <-- Used by all services
```

## Good Example: Properly Decoupled Microservices

### Characteristics
- Each service owns its data exclusively
- Asynchronous communication via events/messaging
- Clear service boundaries with well-defined APIs
- Independent deployment and scaling
- Technology heterogeneity allowed per service
- Resilience patterns (circuit breaker, bulkhead)
- Comprehensive observability per service
- Event-driven architecture for loose coupling

### Benefits Achieved
- Independent deployability
- Fault isolation
- Technology flexibility
- Team autonomy
- Independent scaling
- Better fault tolerance
- Easier to understand and maintain

### Code Example (Good)
```java
// Service A - Order Service with clear boundaries
@Service
public class OrderService {
    @Autowired
    private OrderRepository orderRepo;
    
    @Autowired
    private InventoryEventPublisher inventoryPublisher;
    
    @Autowired
    private PaymentServiceClient paymentClient;
    
    @Transactional
    public OrderResult placeOrder(OrderRequest request) {
        // Validate request locally
        validateOrderRequest(request);
        
        // Create order in own database
        Order order = new Order(
            request.getCustomerId(),
            request.getItemId(),
            request.getQuantity(),
            OrderStatus.PENDING
        );
        orderRepo.save(order);
        
        // Publish event instead of direct call
        inventoryPublisher.publishInventoryReserved(
            order.getId(),
            request.getItemId(),
            request.getQuantity()
        );
        
        // Process payment (could also be event-driven)
        PaymentResult payment = paymentClient.processPayment(request.getPaymentInfo());
        if (!payment.isSuccessful()) {
            // Compensating action through events
            inventoryPublisher.publishInventoryReleased(
                order.getId(),
                request.getItemId(),
                request.getQuantity()
            );
            order.setStatus(OrderStatus.PAYMENT_FAILED);
            orderRepo.save(order);
            throw new PaymentFailedException();
        }
        
        order.setStatus(OrderStatus.CONFIRMED);
        orderRepo.save(order);
        return new OrderResult(true, "Order placed");
    }
}

// Service B - Inventory Service with encapsulated data
@Service
@EventListener
public class InventoryService {
    @Autowired
    private InventoryRepository inventoryRepo;
    
    @Autowired
    private LowStockNotifier lowStockNotifier;
    
    @EventListener
    public void handleInventoryReserved(InventoryReservedEvent event) {
        InventoryItem item = inventoryRepo.findById(event.getItemId());
        if (item == null) {
            throw new ItemNotFoundException(event.getItemId());
        }
        
        if (item.getQuantity() < event.getQuantity()) {
            // Publish shortage event
            inventoryPublisher.publishInventoryShortage(
                event.getOrderId(),
                event.getItemId(),
                event.getQuantity(),
                item.getQuantity()
            );
            return;
        }
        
        // Reserve inventory
        item.setQuantity(item.getQuantity() - event.getQuantity());
        inventoryRepo.save(item);
        
        // Check for low stock
        if (item.getQuantity() < item.getReorderThreshold()) {
            lowStockNotifier.notifyLowStock(item.getId(), item.getQuantity());
        }
        
        // Confirm reservation
        inventoryPublisher.publishInventoryConfirmed(event.getOrderId());
    }
}

// Separate Payment Service
@Service
public class PaymentService {
    @Autowired
    private PaymentProcessor paymentProcessor;
    
    public PaymentResult processPayment(PaymentInfo paymentInfo) {
        // Process payment through external gateway
        return paymentProcessor.charge(paymentInfo);
    }
}
```

### Deployment Architecture (Good)
```
[Load Balancer]
       |
[API Gateway]
       /  |  \
      /   |   \
[Order Service] [Inventory Service] [Payment Service]
      |           |                   |
[Order DB]    [Inventory DB]      [Payment DB]
      |           |                   |
[Event Publisher] [Event Publisher] [Event Publisher]
       \           |           /
        \          |          /
              [Event Bus/Kafka]
                       |
              [Email Service] [Analytics Service] [Notification Service]
                       |           |                   |
               [Email DB]   [Analytics DB]     [Notification DB]
```

## Migration Path from Bad to Good

### Step 1: Data Separation
- Extract each service's data into separate databases
- Implement dual-write pattern during migration
- Use change data capture (CDC) for initial data sync

### Step 2: Introduce Event-Driven Communication
- Replace synchronous calls with async events
- Implement event sourcing where beneficial
- Add event versioning and schema evolution

### Step 3: Implement Resilience Patterns
- Add circuit breakers for external service calls
- Implement bulkhead patterns for resource isolation
- Add retry mechanisms with exponential backoff

### Step 4: Decentralize Data Management
- Each service manages its own schema migrations
- Implement database per service pattern
- Use database abstraction layers

### Step 5: Enhance Observability
- Implement distributed tracing (OpenTelemetry/Jaeger)
- Add structured logging with correlation IDs
- Create service-level dashboards and alerts
- Implement health checks and readiness probes

## Key Takeaways

### Avoid These Anti-Patterns
1. **Shared Databases** - Leads to tight coupling and deployment dependencies
2. **Synchronous Chains** - Creates latency and failure propagation
3. **Shared Libraries** - Creates version coupling and deployment blocking
4. **Distributed Transactions** - Extremely complex and poor performance
5. **Uniform Technology Stack** - Prevents using right tool for each job

### Embrace These Practices
1. **Data Ownership** - Each service owns its data exclusively
2. **Async Communication** - Use events/messaging for loose coupling
3. **Independent Deployability** - Services can be deployed separately
4. **Technology Heterogeneity** - Choose best tech for each service
5. **Failure Isolation** - Faults don't cascade through the system
6. **Observability** - Comprehensive monitoring, logging, and tracing
7. **API Versioning** - Clear contracts between services
8. **Contract Testing** - Ensure service compatibility without integration tests