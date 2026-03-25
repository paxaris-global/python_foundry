# Template Reference Guide for RAG Code Generation

## Overview
This document serves as a comprehensive reference for all working templates in the AI Codegen Platform. All templates have been validated and are production-ready. RAG systems should follow these patterns when generating new code.

---

## Part 1: Backend (Spring Boot 3.3.5) Templates

### 1. pom.xml.j2 - Maven Project Configuration
**Purpose:** Defines all Java project dependencies, plugins, and build configuration.

**Context Variables Used:**
- `{{ project_name }}` - Project name/artifact ID
- `{{ project_package }}` - Java package namespace (e.g., `com.example.hotel`)

**Key Features:**
- Spring Boot 3.3.5 parent POM
- Java 17 target
- Spring Web, Security, Data JPA
- PostgreSQL + H2 database drivers (runtime scoped)
- Flyway database migrations
- SpringDoc OpenAPI 2.0.2 (Swagger)
- Spring Security testing
- Lombok for code generation
- Maven compiler plugin (Java 17)

**Critical Dependencies:**
```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-security</artifactId>
</dependency>
<dependency>
  <groupId>org.springdoc</groupId>
  <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
  <version>2.0.2</version>
</dependency>
<dependency>
  <groupId>org.flywaydb</groupId>
  <artifactId>flyway-core</artifactId>
</dependency>
```

**Docker Integration:** Used in multi-stage build with Maven 3.9 to compile project.

**RAG Pattern:** Always include security, OpenAPI, Flyway, and testing dependencies. Java 17 is standard.

---

### 2. application.yml.j2 - Spring Configuration
**Purpose:** Runtime configuration with environment profiles for different deployment scenarios.

**Context Variables Used:**
- `{{ project_name }}` - Used in logging configuration

**Dual Profile Architecture:**

#### Profile: `postgres` (Production)
```yaml
spring.datasource:
  url: jdbc:postgresql://${DB_HOST:postgres}:${DB_PORT:5432}/${DB_NAME:appdb}
  username: ${DB_USER:postgres}
  password: ${DB_PASSWORD:postgres}
spring.jpa.hibernate.ddl-auto: validate  # Schema must exist
```

#### Profile: `local` (Development)
```yaml
spring.datasource:
  url: jdbc:h2:mem:testdb
  driver-class-name: org.h2.Driver
spring.jpa.hibernate.ddl-auto: create-drop  # Auto-create schema
```

**Flyway Configuration:**
```yaml
spring.flyway:
  enabled: true
  baseline-on-migrate: true
  locations: classpath:db/migration
```

**Key Features:**
- Environment variable substitution with defaults
- SQL logging for debugging
- Jackson formatting on
- Actuator enabled for health checks

**RAG Pattern:** 
- Use environment variables for cloud deployments
- Keep validation mode in production (schema must be pre-migrated)
- Always enable Flyway with baseline-on-migrate
- Support both PostgreSQL and H2 profiles

---

### 3. security_config.java.j2 - Spring Security Configuration
**Purpose:** Authentication, authorization, and CORS configuration.

**Context Variables Used:**
- None (template is static, configuration is universal)

**Security Architecture:**

#### Authentication
- **Method:** HTTP Basic (stateless)
- **Password Encoding:** BCryptPasswordEncoder
- **Default User:** admin / admin123 with ROLE_ADMIN

```java
@Bean
PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}

@Bean
UserDetailsService userDetailsService() {
    UserDetails admin = User.builder()
        .username("admin")
        .password(passwordEncoder().encode("admin123"))
        .authorities("ROLE_ADMIN")
        .build();
    return new InMemoryUserDetailsManager(admin);
}
```

#### Authorization Rules
```
Public Endpoints:
  - /actuator/health
  - /v3/api-docs/**
  - /swagger-ui/**

Protected Endpoints (ROLE_ADMIN):
  - /api/v1/customers/**
```

#### CORS Configuration
```
Allowed Origins:
  - http://localhost:4200 (Angular dev)
  - http://localhost:80 (Production)

Methods: GET, POST, PUT, DELETE, OPTIONS
```

#### Session Strategy
- STATELESS - No session cookies, HTTP Basic on every request

**RAG Pattern:**
- Always use BCryptPasswordEncoder in production
- Use HTTP Basic for stateless APIs
- CORS must be explicitly configured
- Swagger endpoints must be public
- Business endpoints require role-based access (ROLE_ADMIN)
- Create at least one default admin user for initial access

---

### 4. openapi_config.java.j2 - Swagger/OpenAPI Configuration
**Purpose:** Generates OpenAPI 3.0 metadata for API documentation.

**Context Variables Used:**
- `{{ project_name }}` - API title
- `{{ description }}` - API full description

**Configuration:**
```java
@Bean
OpenAPI customOpenAPI() {
    return new OpenAPI()
        .info(new Info()
            .title("{{ project_name }} API")
            .version("1.0.0")
            .description("{{ description }}")
            .contact(new Contact().name("API Support"))
            .license(new License().name("Apache 2.0")))
        .components(new Components()
            .addSecuritySchemes("basicAuth", 
                new SecurityScheme()...));
}
```

**Output:**
- Swagger UI: `/swagger-ui/index.html`
- OpenAPI Spec: `/v3/api-docs`
- Available without authentication (public endpoints)

**RAG Pattern:**
- Always configure OpenAPI bean in main Spring config
- Include contact and license information
- Security schemes must be defined in components
- Documentation endpoint must be public

---

### 5. migration_v1_create_customers.sql.j2 - Flyway Database Migration
**Purpose:** Versioned schema creation using Flyway framework.

**Naming Convention:** `V1__create_customers_table.sql`
- V = Version marker (Flyway standard)
- 1 = Version number
- __ = Double underscore separator
- create_customers_table = Description

**Schema:**
```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(email)
);

CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_name ON customers(name);
```

**Key Characteristics:**
- UUID primary keys (distributed system friendly)
- NOT NULL constraints on business-critical fields
- UNIQUE constraint on email
- Automatic timestamps with defaults
- Indexes on frequently queried columns (email, name)

**RAG Pattern:**
- Flyway migration naming: `V{number}__{descriptive_name}.sql`
- Always use UUID for primary keys in distributed systems
- Include audit timestamps (created_at, updated_at)
- Create indexes on fields used in WHERE clauses
- Version migrations sequentially (V1, V2, V3...)

---

### 6. entity.java.j2 - JPA Entity
**Purpose:** Maps customers table to Java object with ORM annotations.

**Context Variables Used:**
- `{{ entity_class_name }}` - Class name (Customer)
- `{{ project_package }}` - Package namespace

**Annotations:**
- `@Entity` - JPA mapping
- `@Table(name="customers")` - Database table mapping
- `@Id @GeneratedValue` - UUID primary key
- `@Column` - Column-specific configuration
- `@Temporal` - Timestamp handling
- `@CreationTimestamp` / `@UpdateTimestamp` - Audit fields (Hibernate)

**Structure:**
```java
@Entity
@Table(name = "customers")
@Getter @Setter
public class Customer {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    
    @Column(nullable = false)
    private String name;
    
    @Column(nullable = false, unique = true)
    private String email;
    
    @Column
    private String company;
    
    @CreationTimestamp
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @UpdateTimestamp
    @Column(nullable = false)
    private LocalDateTime updatedAt;
}
```

**RAG Pattern:**
- Always include id with @GeneratedValue(GenerationType.UUID)
- Include audit fields: createdAt, updatedAt with timestamps
- Use @Column(nullable = false) for required fields
- Use @Column(unique = true) for unique constraints
- Use Lombok @Getter @Setter for boilerplate reduction
- Map to exact table name in database

---

### 7. dto.java.j2 - Data Transfer Object
**Purpose:** API request/response object with validation annotations.

**Context Variables Used:**
- `{{ dto_class_name }}` - Class name (CustomerDto)
- `{{ project_package }}` - Package namespace

**Validation:**
- `@NotBlank` - String not null/empty
- `@Email` - Valid email format
- `@NotNull` - Field not null

**Structure:**
```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CustomerDto {
    
    private UUID id;
    
    @NotBlank(message = "Name is required")
    private String name;
    
    @Email(message = "Email should be valid")
    private String email;
    
    private String company;
    
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
```

**Purpose:**
- Decouples API contract from entity structure
- Provides validation at boundary layer
- Hides internal fields (id, timestamps) from POST/PUT requests
- Clear API documentation

**RAG Pattern:**
- DTOs should include id and timestamps for GET responses
- Create/Update DTOs should exclude id and timestamps
- Always validate at DTO layer with @NotBlank, @Email, etc.
- Use Lombok @Data for getter/setter generation
- DTOs are the API contract - don't expose internal fields

---

### 8. service.java.j2 & service_impl.java.j2 - Service Layer
**Purpose:** Business logic with interface-based design.

**Interface (service.java.j2):**
```java
public interface ICustomerService {
    List<CustomerDto> findAll();
    CustomerDto findById(UUID id);
    CustomerDto create(CustomerDto dto);
    CustomerDto update(UUID id, CustomerDto dto);
    void delete(UUID id);
}
```

**Implementation (service_impl.java.j2):**
```java
@Service
@RequiredArgsConstructor
public class CustomerServiceImpl implements ICustomerService {
    private final ICustomerRepository repository;
    private final CustomerMapper mapper;
    
    @Override
    public List<CustomerDto> findAll() {
        return repository.findAll()
            .stream()
            .map(mapper::toDto)
            .collect(Collectors.toList());
    }
    
    @Override
    public CustomerDto create(CustomerDto dto) {
        Customer entity = mapper.toEntity(dto);
        Customer saved = repository.save(entity);
        return mapper.toDto(saved);
    }
}
```

**RAG Pattern:**
- Always use interface-based design (ICustomerService)
- Inject dependencies with @RequiredArgsConstructor (Lombok)
- Use mapper for entity ↔ DTO conversion
- Stream API for collection transformations
- Each method maps to one database operation
- Service encapsulates business logic (validation, mapping)

---

### 9. repository.java.j2 - Data Access Layer
**Purpose:** Database query interface using Spring Data JPA.

**Structure:**
```java
@Repository
public interface ICustomerRepository extends JpaRepository<Customer, UUID> {
    Optional<Customer> findByEmail(String email);
    List<Customer> findByNameContainingIgnoreCase(String name);
}
```

**Features:**
- Extends JpaRepository (provides CRUD automatically)
- UUID type parameter (primary key type)
- Custom query methods derived from method names
- `Optional<T>` for nullable results
- Case-insensitive search (`IgnoreCase`)

**RAG Pattern:**
- Repository provides data access abstraction
- Let Spring Data derive queries from method names
- Use Optional<T> instead of nullable returns
- Include common search queries (by email, name, etc.)
- No manual SQL - let Spring generate it

---

### 10. controller.java.j2 - REST API Endpoints
**Purpose:** HTTP request handling and routing.

**Context Variables Used:**
- `{{ project_package }}` - Package namespace
- `{{ base_path }}` - API base path (/api/v1/customers)

**Structure:**
```java
@RestController
@RequestMapping("/api/v1/customers")
@RequiredArgsConstructor
@Tag(name = "Customers", description = "Customer Management API")
public class CustomerController {
    private final ICustomerService service;
    
    @GetMapping
    @Operation(summary = "List all customers")
    public ResponseEntity<List<CustomerDto>> findAll() {
        return ResponseEntity.ok(service.findAll());
    }
    
    @GetMapping("/{id}")
    @Operation(summary = "Get customer by ID")
    public ResponseEntity<CustomerDto> findById(@PathVariable UUID id) {
        return ResponseEntity.ok(service.findById(id));
    }
    
    @PostMapping
    @Operation(summary = "Create new customer")
    public ResponseEntity<CustomerDto> create(@Valid @RequestBody CustomerDto dto) {
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(service.create(dto));
    }
    
    @PutMapping("/{id}")
    @Operation(summary = "Update customer")
    public ResponseEntity<CustomerDto> update(
        @PathVariable UUID id,
        @Valid @RequestBody CustomerDto dto) {
        return ResponseEntity.ok(service.update(id, dto));
    }
    
    @DeleteMapping("/{id}")
    @Operation(summary = "Delete customer")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        service.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

**Key Annotations:**
- `@RestController` - Marks as REST endpoint (auto-serializes to JSON)
- `@RequestMapping` - Base API path
- `@GetMapping/@PostMapping/@PutMapping/@DeleteMapping` - HTTP methods
- `@PathVariable` - URL path parameter
- `@RequestBody` - JSON request body
- `@Valid` - DTO validation
- `@Operation` - Swagger documentation

**RAG Pattern:**
- Follow REST conventions: GET list, GET by ID, POST create, PUT update, DELETE
- Use @PathVariable for URL parameters
- Use @RequestBody for JSON payloads
- Validate with @Valid annotation
- Use ResponseEntity for flexible HTTP responses
- Include Swagger @Operation annotations
- Protect with security in SecurityConfig

---

### 11. exception_handler.java.j2 - Global Exception Handling
**Purpose:** Centralized error handling for consistent API responses.

**Structure:**
```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(ResourceNotFoundException ex) {
        ErrorResponse error = new ErrorResponse(
            HttpStatus.NOT_FOUND.value(),
            ex.getMessage(),
            System.currentTimeMillis()
        );
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationError(MethodArgumentNotValidException ex) {
        String message = ex.getBindingResult()
            .getAllErrors()
            .stream()
            .map(ObjectError::getDefaultMessage)
            .collect(Collectors.joining(", "));
        
        ErrorResponse error = new ErrorResponse(
            HttpStatus.BAD_REQUEST.value(),
            message,
            System.currentTimeMillis()
        );
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }
}
```

**RAG Pattern:**
- Centralize exception handling with @RestControllerAdvice
- Map exceptions to appropriate HTTP status codes
- Return consistent error response format
- Include timestamp for easier debugging
- Handle both business exceptions and validation errors

---

### 12. customer_service_test.java.j2 - Service Unit Tests
**Purpose:** Test business logic with mocked dependencies.

**Test Coverage:**
```java
@ExtendWith(MockitoExtension.class)
class CustomerServiceImplTest {
    
    @Mock
    private ICustomerRepository repository;
    
    @Mock
    private CustomerMapper mapper;
    
    @InjectMocks
    private CustomerServiceImpl service;
    
    @Test
    void testFindAll_Success() {
        // GIVEN
        Customer entity = new Customer();
        CustomerDto dto = new CustomerDto();
        when(repository.findAll()).thenReturn(List.of(entity));
        when(mapper.toDto(entity)).thenReturn(dto);
        
        // WHEN
        List<CustomerDto> result = service.findAll();
        
        // THEN
        assertThat(result).hasSize(1).contains(dto);
        verify(repository).findAll();
    }
    
    @Test
    void testCreate_Success() {
        // Similar pattern: GIVEN, WHEN, THEN
    }
}
```

**RAG Pattern:**
- Use @ExtendWith(MockitoExtension.class) for Mockito integration
- Mock external dependencies (@Mock)
- Inject mocks into service (@InjectMocks)
- Follow Given-When-Then test structure
- Assert on results (AssertJ: `assertThat()`)
- Verify method calls: `verify(mock).method()`
- Test both success and failure paths

---

## Part 2: Frontend (Angular 18.2.0) Templates

### 1. package.json.j2 - npm Configuration
**Purpose:** Project dependencies and npm scripts.

**Context Variables Used:**
- `{{ project_name }}` - Project name for the package

**Key Dependencies:**
```json
{
  "dependencies": {
    "@angular/animations": "^18.2.0",
    "@angular/common": "^18.2.0",
    "@angular/compiler": "^18.2.0",
    "@angular/core": "^18.2.0",
    "@angular/forms": "^18.2.0",
    "@angular/platform-browser": "^18.2.0",
    "@angular/platform-browser-dynamic": "^18.2.0",
    "@angular/router": "^18.2.0",
    "rxjs": "^7.8.1",
    "tslib": "^2.8.1",
    "zone.js": "^0.14.10"
  },
  "devDependencies": {
    "@angular-devkit/build-angular": "^18.2.0",
    "@angular/cli": "^18.2.0",
    "@angular/compiler-cli": "^18.2.0",
    "typescript": "~5.5.4"
  }
}
```

**Critical Field (MUST NOT include):**
- ❌ `@angular/common/http` - This is NOT an npm package
- ✅ Import it from `@angular/common/http` in TypeScript instead

**RAG Pattern:**
- Use exact Angular versions (18.2.0)
- Include all core @angular packages
- HTTP is imported from @angular/common/http in code, NOT in package.json
- Keep rxjs and zone.js for Angular runtime
- Use TypeScript ~5.5.4

---

### 2. app.module.ts.j2 - Root Module
**Purpose:** Bootstraps Angular application and registers feature modules.

**Structure:**
```typescript
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { CustomersModule } from './features/customers/customers.module';

@NgModule({
  declarations: [AppComponent],  // Only root component
  imports: [
    BrowserModule,
    HttpClientModule,
    AppRoutingModule,
    CustomersModule  // Feature module imported, not components
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule {}
```

**Key Rules:**
- ✅ Only AppComponent in declarations
- ✅ CustomersModule in imports (not CustomerListComponent)
- ❌ Never declare feature components in root module
- HttpClientModule enables HTTP functionality

**RAG Pattern:**
- Root module is super minimal
- Feature components belong in feature modules (CustomersModule)
- Feature modules are imported in root module
- HttpClientModule must be imported for API calls
- Never duplicate component declarations between modules

---

### 3. customers.module.ts - Feature Module
**Purpose:** Encapsulates customer-related components and dependencies.

**Generated Structure:**
```typescript
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { CustomerListComponent } from './customer-list/customer-list.component';

@NgModule({
  declarations: [CustomerListComponent],
  imports: [
    CommonModule,      // *ngIf, *ngFor, etc.
    HttpClientModule,  // For ApiService
    FormsModule        // For [(ngModel)] two-way binding
  ],
  exports: [CustomerListComponent]
})
export class CustomersModule {}
```

**Required Imports:**
- `CommonModule` - Provides *ngIf, *ngFor, async pipe
- `HttpClientModule` - For service HTTP calls
- `FormsModule` - For [(ngModel)] binding in forms

**RAG Pattern:**
- Feature modules encapsulate related components
- Always include CommonModule (not BrowserModule)
- FormsModule is essential for template forms with [(ngModel)]
- HttpClientModule provides HTTP service capability
- Export components if they need external access

---

### 4. app.component.ts - Root Component
**Purpose:** Entry point component that bootstraps the application.

**Minimal Structure:**
```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = '{{ project_name }}';
}
```

**RAG Pattern:**
- Root component is typically minimal
- Contains navigation and layout
- Child components handle features
- Selector must be 'app-root' (matches index.html <app-root> tag)

---

### 5. customer-list.component.ts - Feature Component
**Purpose:** Implements customer management UI (list, add, edit, delete).

**Complete Structure:**
```typescript
import { Component, OnInit } from '@angular/core';
import { ApiService, Customer } from '../../../core/services/api.service';

@Component({
  selector: 'app-customer-list',
  templateUrl: './customer-list.component.html',
  styleUrls: ['./customer-list.component.css']
})
export class CustomerListComponent implements OnInit {
  customers: Customer[] = [];
  loading = false;
  error: string | null = null;

  newCustomer: Omit<Customer, 'id'> = {
    name: '',
    email: '',
    company: ''
  };

  selectedCustomer: Customer | null = null;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.fetchCustomers();
  }

  fetchCustomers(): void {
    this.loading = true;
    this.error = null;
    this.apiService.getCustomers().subscribe({
      next: (customers: Customer[]) => {
        this.customers = customers;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load customers';
        console.error(err);
        this.loading = false;
      }
    });
  }

  addCustomer(): void {
    if (!this.newCustomer.name || !this.newCustomer.email) {
      this.error = 'Name and email are required';
      return;
    }
    
    this.apiService.create(this.newCustomer).subscribe({
      next: () => {
        this.fetchCustomers();
        this.newCustomer = { name: '', email: '', company: '' };
      },
      error: () => {
        this.error = 'Failed to add customer';
      }
    });
  }

  updateCustomer(): void {
    if (this.selectedCustomer?.id) {
      this.apiService.update(this.selectedCustomer.id, this.selectedCustomer).subscribe({
        next: () => {
          this.fetchCustomers();
          this.selectedCustomer = null;
        },
        error: () => {
          this.error = 'Failed to update customer';
        }
      });
    }
  }

  deleteCustomer(id: string): void {
    this.apiService.delete(id).subscribe({
      next: () => {
        this.fetchCustomers();
      },
      error: () => {
        this.error = 'Failed to delete customer';
      }
    });
  }

  selectCustomer(customer: Customer): void {
    this.selectedCustomer = { ...customer };
  }
}
```

**Key Patterns:**
- `Omit<Customer, 'id'>` - Form model without ID/timestamps
- Observable subscribers with `next` and `error` handlers
- Loading and error state management
- Array spread to create edit copy: `{ ...customer }`

**RAG Pattern:**
- Separate state for new vs. edit operations
- Manage loading/error states explicitly
- Use Omit<T, K> for form models
- Subscribe to observables with error handling
- Fetch fresh data after mutations (create/update/delete)

---

### 6. customer-list.component.html - Component Template
**Purpose:** Renders customer management UI with forms and list.

**Structure:**
```html
<h2>Customers</h2>
<p>Full CRUD demo for customer management.</p>

<div *ngIf="error" class="error">{{ error }}</div>
<div *ngIf="loading">Loading customers...</div>

<!-- Add Customer Form -->
<form (ngSubmit)="addCustomer()">
  <h3>Add Customer</h3>
  <label>
    Name:
    <input type="text" [(ngModel)]="newCustomer.name" name="name" required />
  </label>
  <br />
  <label>
    Email:
    <input type="email" [(ngModel)]="newCustomer.email" name="email" required />
  </label>
  <br />
  <label>
    Company:
    <input type="text" [(ngModel)]="newCustomer.company" name="company" />
  </label>
  <br />
  <button type="submit">Add</button>
</form>

<!-- Edit Customer Form -->
<div *ngIf="selectedCustomer" class="edit-form">
  <h3>Edit Customer</h3>
  <label>
    Name:
    <input type="text" [(ngModel)]="selectedCustomer.name" name="editName" />
  </label>
  <br />
  <label>
    Email:
    <input type="email" [(ngModel)]="selectedCustomer.email" name="editEmail" />
  </label>
  <br />
  <label>
    Company:
    <input type="text" [(ngModel)]="selectedCustomer.company" name="editCompany" />
  </label>
  <br />
  <button (click)="updateCustomer()">Save</button>
  <button (click)="selectedCustomer = null">Cancel</button>
</div>

<!-- Customer List -->
<ul>
  <li *ngFor="let customer of customers" (click)="selectCustomer(customer)">
    {{ customer.name }} ({{ customer.email }}) - {{ customer.company }}
    <button (click)="deleteCustomer(customer.id); $event.stopPropagation()">Delete</button>
  </li>
</ul>
```

**Two-Way Binding:**
- `[(ngModel)]="newCustomer.name"` - Binds input to component property
- Requires FormsModule in CustomersModule

**Directives:**
- `*ngIf="condition"` - Conditional rendering
- `*ngFor="let item of array"` - List rendering

**Event Binding:**
- `(ngSubmit)="addCustomer()"` - Form submission
- `(click)="deleteCustomer(id)"` - Delete button
- `$event.stopPropagation()` - Prevent event bubbling

**RAG Pattern:**
- Forms use [(ngModel)] for two-way binding
- Manage edit state with *ngIf="selectedCustomer"
- Display errors and loading states
- Use (click) and (ngSubmit) for user actions
- Use $event.stopPropagation() to prevent unintended event bubbling
- Separate add and edit sections in template

---

### 7. api.service.ts - HTTP Service
**Purpose:** Centralized API communication with Customer interface definition.

**Structure:**
```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Customer {
  id: string;
  name: string;
  email: string;
  company: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getCustomers(): Observable<Customer[]> {
    return this.http.get<Customer[]>(`${this.baseUrl}/customers`);
  }

  getCustomerById(id: string): Observable<Customer> {
    return this.http.get<Customer>(`${this.baseUrl}/customers/${id}`);
  }

  create(customer: Omit<Customer, 'id'>): Observable<Customer> {
    return this.http.post<Customer>(`${this.baseUrl}/customers`, customer);
  }

  update(id: string, customer: Partial<Customer>): Observable<Customer> {
    return this.http.put<Customer>(`${this.baseUrl}/customers/${id}`, customer);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/customers/${id}`);
  }
}
```

**Key Features:**
- `@Injectable({ providedIn: 'root' })` - Singleton service
- TypeScript interface for type safety
- Typed observables: `Observable<Customer[]>`
- Base URL from environment configuration
- RESTful methods: GET, POST, PUT, DELETE

**RAG Pattern:**
- Export interfaces alongside service for type consistency
- Use `providedIn: 'root'` for singleton pattern
- Separate DTOs for create (Omit<T, 'id'>) and update (Partial<T>)
- Always type HTTP calls generically: `http.get<Type>()`
- Return observables without subscribing (let components subscribe)

---

### 8. environment.ts & environment.prod.ts - Configuration
**Purpose:** Environment-specific settings (API URL, etc.)

**Development (environment.ts):**
```typescript
export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8080/api/v1'
};
```

**Production (environment.prod.ts):**
```typescript
export const environment = {
  production: true,
  apiBaseUrl: 'https://api.example.com/api/v1'
};
```

**RAG Pattern:**
- Keep API base URL in environment configuration
- Development points to localhost
- Production points to actual API domain
- Import: `import { environment } from '../../../environments/environment'`

---

### 9. app.component.html - Root Template
**Purpose:** Main layout with router outlet for page rendering.

**Minimal Structure:**
```html
<header>
  <h1>{{ title }}</h1>
  <nav>
    <a routerLink="/">Home</a>
    <a routerLink="/customers">Customers</a>
  </nav>
</header>

<main>
  <router-outlet></router-outlet>
</main>

<footer>
  <p>&copy; {{ title }}</p>
</footer>
```

**Key Elements:**
- `<router-outlet></router-outlet>` - Where routed components render
- `routerLink="path"` - Navigation without page reload
- `{{ title }}` - Property binding

**RAG Pattern:**
- Root template provides layout structure
- Feature components render in router-outlet
- Navigation via routerLink directives

---

### 10. app-routing.module.ts - Routing Configuration
**Purpose:** Defines application routes.

**Structure:**
```typescript
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { AppComponent } from './app.component';

const routes: Routes = [
  { path: '', redirectTo: '/customers', pathMatch: 'full' },
  { path: 'customers', component: CustomerListComponent },
  { path: '**', redirectTo: '/customers' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}
```

**RAG Pattern:**
- Default route redirects to /customers
- Wildcard route (\\*\\*) catches unmatched URLs
- Use pathMatch: 'full' for exact route matching

---

### 11. app.component.css & component.css - Styling
**Purpose:** Component-scoped CSS styling.

**Basic Styling Pattern:**
```css
h2 {
  color: #333;
  border-bottom: 2px solid #007bff;
  padding-bottom: 10px;
}

form {
  margin: 20px 0;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

input {
  padding: 8px;
  margin: 5px 0;
  width: 200px;
  border: 1px solid #ccc;
  border-radius: 3px;
}

button {
  padding: 8px 15px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}

.error {
  color: red;
  margin: 10px 0;
  padding: 10px;
  background-color: #ffe6e6;
  border-radius: 3px;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  padding: 10px;
  margin: 5px 0;
  background-color: #f9f9f9;
  border-left: 4px solid #007bff;
  cursor: pointer;
}

li:hover {
  background-color: #e6f2ff;
}
```

**RAG Pattern:**
- CSS is component-scoped (not global)
- Use consistent color scheme (#007bff for primary)
- Provide hover states for interactivity
- Use padding/margin consistently
- Error states with distinct colors

---

## Part 3: Docker Configuration

### Dockerfile (Multi-Stage Build)
**Purpose:** Containerizes both backend and frontend for deployment.

**Backend Stage (Maven):**
```dockerfile
FROM maven:3.9-eclipse-temurin-17 as builder
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src/main src/main
RUN mvn clean package -DskipTests
```

**Frontend Stage (Node → Nginx):**
```dockerfile
FROM node:20-alpine as frontend-builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
RUN npm run build
```

**Runtime Stage (Java):**
```dockerfile
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
```

**RAG Pattern:**
- Multi-stage Docker builds reduce final image size
- Maven 3.9 + Java 17 for Java builds
- Node 20-alpine for Angular transpilation
- eclipse-temurin:17-jre for Java runtime (lightweight)
- WORKDIR and COPY paths must align with project structure

---

### docker-compose.yml - Orchestration
**Purpose:** Runs frontend, backend, and database together.

**Services:**
1. **Frontend (Nginx):** Port 4200 (dev) or 80 (prod)
2. **Backend (Java):** Port 8080
3. **PostgreSQL:** Port 5432

**RAG Pattern:**
- Services communicate via service name (backend:8080)
- Environment variables passed for configuration
- Volumes for persistence (database data)
- Networks isolate services
- Port mappings expose services

---

## Part 4: RAG Code Generation Patterns

### When Generating New Projects

**Follow These Patterns:**

#### Backend Patterns
1. **Package Structure:**
   - `com.example.{project}.entity` - JPA entities
   - `com.example.{project}.dto` - Transfer objects
   - `com.example.{project}.service` - Business logic interfaces
   - `com.example.{project}.service.impl` - Service implementations
   - `com.example.{project}.repository` - Data access
   - `com.example.{project}.controller` - REST endpoints
   - `com.example.{project}.config` - Spring configurations

2. **Security:**
   - Always use BCryptPasswordEncoder
   - Create admin user in UserDetailsService
   - Protect /api/** endpoints with ROLE_ADMIN
   - Allow /actuator/health, /v3/api-docs, /swagger-ui

3. **Database:**
   - Use UUID for primary keys
   - Include created_at and updated_at timestamps
   - Use Flyway with V{number}__{description}.sql naming
   - Create indexes on frequently queried columns

4. **API:**
   - Use HTTP Basic authentication (stateless)
   - Return ResponseEntity<T> for flexibility
   - Include @Valid on @RequestBody
   - Add @Operation annotations for Swagger

5. **Testing:**
   - Use Mockito for unit tests
   - Mock repositories and mappers
   - Follow Given-When-Then structure
   - Test success AND error paths

#### Frontend Patterns
1. **Module Structure:**
   - Root module (AppModule) minimal
   - Feature modules encapsulating components
   - Always include CommonModule in feature modules
   - Import FormsModule if using [(ngModel)]

2. **Services:**
   - Export interfaces alongside services
   - Use Omit<T, 'id'> for create payloads
   - Return raw observables (let components subscribe)
   - Type all HTTP calls: http.get<Type>()

3. **Components:**
   - Separate state for new/edit operations
   - Manage loading and error states
   - Use [(ngModel)] for two-way binding
   - Subscribe with next/error handlers

4. **Templates:**
   - Use *ngIf for conditional rendering
   - Use *ngFor for list rendering
   - Use [(ngModel)] for forms
   - Use (click)/(ngSubmit) for events

---

## Part 5: Validation Checklist for Generated Code

### Backend Validation
- [ ] pom.xml includes: springdoc-openapi, flyway, spring-security-test
- [ ] application.yml has postgres and local profiles
- [ ] SecurityConfig has BCryptPasswordEncoder and CORS configured
- [ ] OpenApiConfig exists and creates OpenAPI bean
- [ ] Migration file named V1__create_table.sql
- [ ] Entity has @CreationTimestamp/@UpdateTimestamp
- [ ] DTO has @NotBlank/@Email validation
- [ ] Service uses interface (ICustomerService)
- [ ] Repository extends JpaRepository<T, UUID>
- [ ] Controller uses @Valid on @RequestBody
- [ ] Tests use @ExtendWith(MockitoExtension.class)

### Frontend Validation
- [ ] package.json uses @angular/common (NOT @angular/common/http)
- [ ] AppModule only declares AppComponent
- [ ] Feature module imports CommonModule + FormsModule
- [ ] Component has proper error/loading state management
- [ ] Template uses [(ngModel)] for forms (requires FormsModule)
- [ ] Service exports Customer interface
- [ ] API service returns Observable<T> (not subscribed)
- [ ] All HTTP calls typed: http.get<Type>()
- [ ] Environment.ts has apiBaseUrl

---

## Part 6: Known Issues & Solutions

### Issue 1: Angular Build Error "declared in multiple NgModules"
**Cause:** Component declared in both root module and feature module
**Solution:** Remove from root module declarations, import feature module instead
**Reference:** [app.module.ts.j2](../templates/angular/app.module.ts.j2) - AppModule has NO CustomerListComponent

### Issue 2: npm install fails with "invalid package name"
**Cause:** @angular/common/http as npm dependency (instead of import)
**Solution:** package.json should only include @angular/common, NOT `@angular/common/http`
**Reference:** [package.json.j2](../templates/angular/package.json.j2) - Correct dependency list

### Issue 3: Template binding doesn't work `[(ngModel)]` shows error
**Cause:** FormsModule not imported in feature module
**Solution:** Add FormsModule to module imports
**Reference:** [customers.module.ts in angular_generator.py](../app/generators/angular_generator.py) - CustomersModule includes FormsModule

### Issue 4: API calls fail with CORS error
**Cause:** SecurityConfig doesn't allow frontend origin
**Solution:** Configure CORS in SecurityConfig for localhost:4200
**Reference:** [security_config.java.j2](../templates/springboot/security_config.java.j2) - CORS configured for localhost

### Issue 5: Database migration doesn't run
**Cause:** Flyway not configured or migration naming incorrect
**Solution:** Enable Flyway in application.yml, name files V1__, V2__, etc.
**Reference:** [application.yml.j2](../templates/springboot/application.yml.j2) - Flyway enabled with baseline

---

## Summary

These templates represent production-ready code patterns. When RAG systems generate code:

1. **Use exact template structures** - Don't customize without reason
2. **Follow naming conventions** - Flyway V1__, package structure, class names
3. **Include enterprise features** - Security, testing, migrations, documentation
4. **Map variables correctly** - Match context keys in generators to template variables
5. **Test generated code** - Run validate_generators.py to verify
6. **Document new patterns** - If adding features, update this guide

All templates have been validated against working code and actual generated projects.
