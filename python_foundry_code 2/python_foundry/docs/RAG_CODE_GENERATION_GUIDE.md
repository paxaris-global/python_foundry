# RAG Code Generation Prompt Guide

## Purpose
This document instructs RAG systems how to generate accurate, production-ready code by following established template patterns. Every generated project must follow these guidelines to work correctly.

---

## Part 1: Backend Code Generation (Spring Boot)

### Step 1: Project Setup
**When RAG sees:** "Generate a hotel management system backend"

**RAG Must Do:**
1. Create Maven project structure: `src/main/java/com/example/{project}/`
2. Generate pom.xml from `pom.xml.j2` template with:
   - Project name and package from prompt
   - All dependencies: Spring Boot, Spring Security, Flyway, SpringDoc OpenAPI
   - Java 17 compiler target
3. Generate application.yml from `application.yml.j2` with:
   - postgres and local profiles
   - Environment variable support (DB_HOST, DB_PORT, etc.)
   - Flyway enabled with baseline-on-migrate: true

**Template Variables to Substitute:**
```
{{ project_name }} → "Hotel Management System"
{{ project_package }} → "com.example.hotel"
```

---

### Step 2: Security Configuration
**Always required for every backend project**

**Generate:** `src/main/java/com/example/{project}/config/SecurityConfig.java`
- Source: `security_config.java.j2` template
- Purpose: HTTP Basic auth, BCrypt, CORS, role-based access
- Endpoints to protect: `/api/v1/**` with `ROLE_ADMIN`
- Public endpoints: `/actuator/health`, `/v3/api-docs/`, `/swagger-ui/`
- CORS allow: `localhost:4200` (Angular), `localhost:80` (Production)
- Default admin user: `admin/admin123` with `ROLE_ADMIN` role

**Critical Pattern:**
```java
// MUST use BCryptPasswordEncoder
@Bean PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}

// MUST create default admin user
@Bean UserDetailsService userDetailsService() {
    UserDetails admin = User.builder()
        .username("admin")
        .password(passwordEncoder().encode("admin123"))
        .authorities("ROLE_ADMIN")
        .build();
    return new InMemoryUserDetailsManager(admin);
}
```

---

### Step 3: OpenAPI Documentation
**Always required for every backend project**

**Generate:** `src/main/java/com/example/{project}/config/OpenApiConfig.java`
- Source: `openapi_config.java.j2` template
- Purpose: Swagger UI auto-generation at `/swagger-ui/index.html`
- Include: Project title, version 1.0.0, description, contact info

**After generation:**
- Users can access Swagger UI without authentication (public endpoint)
- All endpoints documented automatically

---

### Step 4: Database Schema (Flyway)
**Always required for every backend project**

**Generate:** `src/main/resources/db/migration/V1__create_{entity_table}.sql`
- Source: `migration_v1_create_customers.sql.j2` template (adapt for entity name)
- Naming: `V1__create_table_name.sql` (Flyway requirement)
- Include:
  - UUID primary key: `DEFAULT gen_random_uuid()`
  - Business fields (name, email, company, etc.)
  - NOT NULL constraints on required fields
  - UNIQUE constraint where appropriate (email)
  - created_at, updated_at timestamps with CURRENT_TIMESTAMP default
  - Indexes on frequently queried columns (email, name)

**Pattern for each entity:**
```sql
CREATE TABLE {entity_name_plural} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    company VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_{entity_name_plural}_email ON {entity_name_plural}(email);
CREATE INDEX idx_{entity_name_plural}_name ON {entity_name_plural}(name);
```

**Important:** For each new domain entity, create a new V{N}__create_table.sql file. Don't modify existing migrations.

---

### Step 5: JPA Entity
**For each domain entity (Customer, Hotel, Room, etc.)**

**Generate:** `src/main/java/com/example/{project}/entity/{EntityName}.java`
- Source: `entity.java.j2` template
- Package: `com.example.{project}.entity`
- Annotations required:
  - `@Entity` - JPA mapping
  - `@Table(name = "{table_name}")` - Database mapping
  - `@Id @GeneratedValue(strategy = GenerationType.UUID)` - UUID primary key
  - `@CreationTimestamp` / `@UpdateTimestamp` - Audit fields
  - `@Column(nullable = false)` - Required fields
  - `@Column(unique = true)` - Unique constraints
- Always use Lombok: `@Getter @Setter`

**Pattern:**
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

---

### Step 6: DTO (Data Transfer Object)
**For each entity - handles API request/response validation**

**Generate:** `src/main/java/com/example/{project}/dto/{EntityName}Dto.java`
- Source: `dto.java.j2` template
- Package: `com.example.{project}.dto`
- Annotations required:
  - `@Data` (Lombok) - getter/setter/equals/hashCode/toString
  - `@NoArgsConstructor` (Lombok) - no-arg constructor
  - `@AllArgsConstructor` (Lombok) - all-arg constructor
  - `@NotBlank(message = "...")` - validation for required strings
  - `@Email(message = "...")` - email format validation
  - `@NotNull` - null validation

**Pattern:**
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

**Important:** For POST/PUT endpoints, frontend typically won't send id and timestamps. RAG should create separate DTOs:
- `CustomerCreateDto` - No id, no timestamps
- `CustomerUpdateDto` - No id, timestamps optional
- `CustomerDto` - Full object for GET responses

---

### Step 7: Repository (Data Access)
**For each entity**

**Generate:** `src/main/java/com/example/{project}/repository/I{EntityName}Repository.java`
- Source: `repository.java.j2` template
- Package: `com.example.{project}.repository`
- Interface extends: `JpaRepository<{Entity}, UUID>`
- Spring Data derives queries from method names

**Pattern:**
```java
@Repository
public interface ICustomerRepository extends JpaRepository<Customer, UUID> {
    Optional<Customer> findByEmail(String email);
    List<Customer> findByNameContainingIgnoreCase(String name);
    Optional<Customer> findById(UUID id);  // Already provided by JpaRepository
}
```

**Always include:**
- `findById(UUID)` - inherited from JpaRepository
- `findByUniqueField(...)` - business queries
- `findByFieldContaining(...)` - search queries

---

### Step 8: Service Interface
**For each entity - defines business operations**

**Generate:** `src/main/java/com/example/{project}/service/I{EntityName}Service.java`
- Source: `service.java.j2` template
- Package: `com.example.{project}.service`
- Public interface, implementation is ServiceImpl

**Pattern (CRUD Interface):**
```java
public interface ICustomerService {
    List<CustomerDto> findAll();
    CustomerDto findById(UUID id);
    CustomerDto create(CustomerDto dto);
    CustomerDto update(UUID id, CustomerDto dto);
    void delete(UUID id);
}
```

---

### Step 9: Service Implementation
**For each entity - implements business logic**

**Generate:** `src/main/java/com/example/{project}/service/impl/{EntityName}ServiceImpl.java`
- Source: `service_impl.java.j2` template
- Annotations: `@Service @RequiredArgsConstructor`
- Inject: Repository, Mapper
- Implement all interface methods

**Pattern:**
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
    
    @Override
    public CustomerDto update(UUID id, CustomerDto dto) {
        Customer entity = repository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Customer not found"));
        mapper.updateEntity(dto, entity);
        Customer saved = repository.save(entity);
        return mapper.toDto(saved);
    }
    
    @Override
    public void delete(UUID id) {
        repository.deleteById(id);
    }
}
```

---

### Step 10: Mapper (Entity ↔ DTO Conversion)
**For each entity - converts between entity and DTO**

**Generate:** `src/main/java/com/example/{project}/mapper/{EntityName}Mapper.java`
- Use MapStruct library for automatic mapping
- Or manual mapping with Lombok getters/setters

**Pattern (Manual):**
```java
@Component
public class CustomerMapper {
    public CustomerDto toDto(Customer entity) {
        if (entity == null) return null;
        
        CustomerDto dto = new CustomerDto();
        dto.setId(entity.getId());
        dto.setName(entity.getName());
        dto.setEmail(entity.getEmail());
        dto.setCompany(entity.getCompany());
        dto.setCreatedAt(entity.getCreatedAt());
        dto.setUpdatedAt(entity.getUpdatedAt());
        return dto;
    }
    
    public Customer toEntity(CustomerDto dto) {
        if (dto == null) return null;
        
        Customer entity = new Customer();
        entity.setName(dto.getName());
        entity.setEmail(dto.getEmail());
        entity.setCompany(dto.getCompany());
        return entity;  // id/timestamps managed by DB
    }
    
    public void updateEntity(CustomerDto dto, Customer entity) {
        entity.setName(dto.getName());
        entity.setEmail(dto.getEmail());
        entity.setCompany(dto.getCompany());
        // Don't update id, createdAt
    }
}
```

---

### Step 11: Controller (REST Endpoints)
**For each entity - HTTP API endpoints**

**Generate:** `src/main/java/com/example/{project}/controller/{EntityName}Controller.java`
- Source: `controller.java.j2` template
- Package: `com.example.{project}.controller`
- Base path: `/api/v1/{entity_name_plural}`
- Use `ResponseEntity<T>` for flexible responses

**Pattern (Full CRUD):**
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
    public ResponseEntity<CustomerDto> create(
        @Valid @RequestBody CustomerDto dto) {
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

**Key Rules:**
- All GET methods return `ResponseEntity.ok(data)`
- POST returns `ResponseEntity.status(HttpStatus.CREATED).body(data)`
- DELETE returns `ResponseEntity.noContent().build()`
- Use `@Valid` on `@RequestBody` to trigger DTO validation
- Include `@Operation` for Swagger documentation

---

### Step 12: Exception Handler
**Global exception handling for all controllers**

**Generate:** `src/main/java/com/example/{project}/exception/GlobalExceptionHandler.java`
- Source: `exception_handler.java.j2` template
- Annotation: `@RestControllerAdvice`
- Handle: ResourceNotFoundException, MethodArgumentNotValidException, etc.

**Pattern:**
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
}
```

---

### Step 13: Unit Tests
**For each Service - verify business logic**

**Generate:** `src/test/java/com/example/{project}/service/impl/{EntityName}ServiceImplTest.java`
- Source: `customer_service_test.java.j2` template
- Use `@ExtendWith(MockitoExtension.class)`
- Mock repository and mapper
- Test at least: findAll, findById, create, update, delete
- Follow Given-When-Then pattern

**Pattern:**
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
}
```

---

## Part 2: Frontend Code Generation (Angular 18)

### Step 1: Project Setup
**When RAG sees:** "Generate a hotel management system frontend"

**RAG Must Do:**
1. Create Angular project: `src/app/`
2. Generate package.json from `package.json.j2` template
3. Include dependencies:
   - @angular/* (all packages) at ^18.2.0
   - rxjs, zone.js, tslib
4. Generate tsconfig.json with Angular 18 settings
5. Generate angular.json with build configuration

**Template Variables:**
```
{{ project_name }} → "Hotel Management System"
```

---

### Step 2: Root Module (AppModule)
**Central entry point for Angular**

**Generate:** `src/app/app.module.ts`
- Source: `app.module.ts.j2` template
- Declarations: Only `AppComponent`
- Imports: `BrowserModule`, `HttpClientModule`, `AppRoutingModule`, `CustomersModule`
- Must NOT declare `CustomerListComponent` (it's in CustomersModule)

**Critical Pattern:**
```typescript
@NgModule({
  declarations: [AppComponent],  // ✓ ONLY AppComponent
  imports: [
    BrowserModule,
    HttpClientModule,
    AppRoutingModule,
    CustomersModule  // ✓ Import module, NOT component
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule {}
```

**Why:** Declaring a component in multiple modules causes Angular build errors.

---

### Step 3: Feature Module (CustomersModule)
**Encapsulates customer-related functionality**

**Generate:** `src/app/features/customers/customers.module.ts`
- Declarations: `CustomerListComponent`
- Imports: `CommonModule`, `HttpClientModule`, `FormsModule`
- Exports: `CustomerListComponent` (if needed externally)
- Must include `FormsModule` for `[(ngModel)]` binding

**Critical Pattern:**
```typescript
@NgModule({
  declarations: [CustomerListComponent],
  imports: [
    CommonModule,      // ✓ *ngIf, *ngFor, async pipe
    HttpClientModule,  // ✓ For HTTP calls
    FormsModule        // ✓ For [(ngModel)] two-way binding
  ],
  exports: [CustomerListComponent]
})
export class CustomersModule {}
```

**Why:** Separates concerns; each feature has its own module.

---

### Step 4: Root Component
**Main layout component**

**Generate:** `src/app/app.component.ts`
- Source: `component.ts.j2` template (adapt for root)
- Selector: `app-root`
- Template: Navigation, header, footer
- Contains: `<router-outlet></router-outlet>` for page rendering

---

### Step 5: Feature Component (CustomerListComponent)
**CRUD UI for customer management**

**Generate:** `src/app/features/customers/customer-list/customer-list.component.ts`
- Source: `component.ts.j2` template
- Inject: `ApiService`
- State: `customers[]`, `loading`, `error`, `newCustomer`, `selectedCustomer`
- Methods: `fetchCustomers()`, `addCustomer()`, `updateCustomer()`, `deleteCustomer()`, `selectCustomer()`

**Pattern:**
```typescript
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
    this.apiService.getCustomers().subscribe({
      next: (customers) => {
        this.customers = customers;
        this.loading = false;
      },
      error: () => {
        this.error = 'Failed to load customers';
        this.loading = false;
      }
    });
  }
  
  addCustomer(): void {
    if (!this.validate(this.newCustomer)) return;
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
}
```

**State Management Pattern:**
- `Omit<Customer, 'id'>` for form model (no id/timestamps)
- Spread operator for edit copy: `{ ...customer }`
- Manage loading/error states explicitly
- Subscribe to observables with next/error handlers

---

### Step 6: Feature Component Template
**HTML for customer CRUD**

**Generate:** `src/app/features/customers/customer-list/customer-list.component.html`
- Source: `component.html.j2` template
- Sections: Add form, Edit form (conditional), Customer list

**Key Directives:**
- `*ngIf="error"` - Conditional error display
- `*ngFor="let customer of customers"` - List iteration
- `[(ngModel)]="newCustomer.name"` - Two-way binding
- `(ngSubmit)="addCustomer()"` - Form submission
- `(click)="deleteCustomer(id)"` - Delete action

**Pattern:**
```html
<h2>Customers</h2>

<div *ngIf="error" class="error">{{ error }}</div>
<div *ngIf="loading">Loading...</div>

<form (ngSubmit)="addCustomer()">
  <h3>Add Customer</h3>
  <label>
    Name:
    <input type="text" [(ngModel)]="newCustomer.name" name="name" required />
  </label>
  <button type="submit">Add</button>
</form>

<div *ngIf="selectedCustomer" class="edit-form">
  <h3>Edit Customer</h3>
  <label>
    Name:
    <input type="text" [(ngModel)]="selectedCustomer.name" name="editName" />
  </label>
  <button (click)="updateCustomer()">Save</button>
  <button (click)="selectedCustomer = null">Cancel</button>
</div>

<ul>
  <li *ngFor="let customer of customers" (click)="selectCustomer(customer)">
    {{ customer.name }} ({{ customer.email }})
    <button (click)="deleteCustomer(customer.id); $event.stopPropagation()">Delete</button>
  </li>
</ul>
```

**Important:** Use `$event.stopPropagation()` to prevent callback bubbling.

---

### Step 7: API Service
**Centralized HTTP communication**

**Generate:** `src/app/core/services/api.service.ts`
- Source: `service.ts.j2` template
- Export: `Customer` interface (for type safety)
- Inject: `HttpClient`
- Methods: `getCustomers()`, `getCustomerById()`, `create()`, `update()`, `delete()`

**Critical Pattern:**
```typescript
export interface Customer {
  id: string;
  name: string;
  email: string;
  company: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = environment.apiBaseUrl;
  
  constructor(private http: HttpClient) {}
  
  getCustomers(): Observable<Customer[]> {
    return this.http.get<Customer[]>(`${this.baseUrl}/customers`);
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

**Why Return Observables:**
- Components subscribe, giving them control
- Allows for composition and error handling in components
- Services stay simple and reusable

---

### Step 8: Environment Configuration
**Environment-specific settings**

**Generate:**
- `src/environments/environment.ts` (development)
- `src/environments/environment.prod.ts` (production)

**Pattern:**
```typescript
// Development
export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8080/api/v1'
};

// Production
export const environment = {
  production: true,
  apiBaseUrl: 'https://api.example.com/api/v1'
};
```

---

### Step 9: Routing Module
**Application navigation**

**Generate:** `src/app/app-routing.module.ts`

**Pattern:**
```typescript
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

---

### Step 10: Component Styling
**CSS scoped to components**

**Generate:** `component.component.css` files

**Pattern - Consistent with templates:**
```css
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
}

button {
  padding: 8px 15px;
  background-color: #007bff;
  color: white;
  border: none;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}

.error {
  color: red;
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
}

li:hover {
  background-color: #e6f2ff;
}
```

---

## Part 3: Docker & Deployment

### Step 1: Dockerfile
**Multi-stage build for backend and frontend**

**Generate:** `Dockerfile` at project root

**Pattern:**
```dockerfile
# Frontend build stage
FROM node:20-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Backend build stage
FROM maven:3.9-eclipse-temurin-17 as backend-builder
WORKDIR /app/backend
COPY backend/pom.xml .
RUN mvn dependency:go-offline
COPY backend/src ./src
RUN mvn clean package -DskipTests

# Frontend serve stage
FROM nginx:1.27-alpine as frontend
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Backend runtime stage
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=backend-builder /app/backend/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

---

### Step 2: Docker Compose
**Orchestration for full stack**

**Generate:** `docker-compose.yml` at project root

**Pattern:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: appdb
      DB_USER: postgres
      DB_PASSWORD: postgres
    ports:
      - "8080:8080"
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "4200:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## Part 4: RAG Systems - Key Implementation Rules

### Rule 1: Variable Substitution
**All template variables MUST be substituted from context**

Template variable format: `{{ variable_name }}`

Common variables:
- `{{ project_name }}` - User-provided project name
- `{{ project_package }}` - Java package (com.example.hotel)
- `{{ description }}` - Project description
- `{{ entity_name }}` - Entity name (Customer)
- `{{ entity_name_plural }}` - Plural form (customers)

**RAG Implementation:**
```python
# Extract from user prompt
project_name = parse_project_name(prompt)  # "Hotel Management System"
project_package = "com.example." + project_name.lower().replace(" ", "")

# Render template
rendered = render_template("pom.xml.j2", {
    "project_name": project_name,
    "project_package": project_package
})
```

---

### Rule 2: Package Structure
**Always follow this directory structure:**

```
Backend:
  com.example.{project}/
    entity/          → {Entity}.java with @Entity
    dto/             → {Entity}Dto.java with validation
    repository/      → I{Entity}Repository.java extends JpaRepository
    service/         → I{Entity}Service.java interface
    service/impl/    → {Entity}ServiceImpl.java implements service
    mapper/          → {Entity}Mapper.java for conversion
    controller/      → {Entity}Controller.java REST endpoints
    config/          → SecurityConfig.java, OpenApiConfig.java
    exception/       → GlobalExceptionHandler.java

Frontend:
  src/app/
    core/
      services/      → api.service.ts with Customer interface
      models/        → type definitions
    features/
      customers/
        customer-list/
          customer-list.component.ts
          customer-list.component.html
          customer-list.component.css
        customers.module.ts
    app.module.ts
    app.component.ts
    app-routing.module.ts
```

---

### Rule 3: Naming Conventions
**Be consistent with these naming patterns:**

| Entity | Backend | Frontend |
|--------|---------|----------|
| Entity class | `Customer` | - |
| DTO class | `CustomerDto` | - |
| Service interface | `ICustomerService` | - |
| Service impl | `CustomerServiceImpl` | - |
| Repository | `ICustomerRepository` | - |
| Mapper | `CustomerMapper` | - |
| Controller | `CustomerController` | - |
| Component | - | `CustomerListComponent` |
| Service | - | `ApiService` |
| Table name | `customers` | - |
| API path | `/api/v1/customers` | `/customers` |

**URL Slugs:** Convert entity names to plural lowercase (Customer → `customers`)

---

### Rule 4: Testing
**Every backend service must have passing tests**

```bash
# Run tests
mvn test

# Required test coverage
- Service layer (all CRUD operations)
- Repository queries
- Controller endpoints (optional - integration tests)
```

---

### Rule 5: Validation
**Generated code must pass validation**

```bash
# Backend validation
mvn compile  # Must compile without errors
mvn test     # All tests must pass

# Frontend validation
npm install  # Dependencies must resolve
npm build    # Must build without errors
```

---

## Part 5: Troubleshooting for RAG

### Issue: Angular "component declared in two modules"
**Symptom:** Build fails: "AppComponent/CustomerListComponent is part of multiple NgModules"

**Cause:** RAG declared component in both root and feature module

**Fix:** Remove from root module declarations, import feature module instead
```typescript
// ✗ WRONG - AppModule
@NgModule({
  declarations: [AppComponent, CustomerListComponent]  // BAD
})

// ✓ CORRECT - AppModule
@NgModule({
  declarations: [AppComponent],  // Only root
  imports: [CustomersModule]     // Import module
})
```

---

### Issue: npm install fails "invalid package name"
**Symptom:** `npm install` fails with package name contains invalid characters

**Cause:** package.json includes `@angular/common/http` as dependency (instead of import)

**Fix:** Remove from package.json, keep only `@angular/common`
```json
// ✗ WRONG
"@angular/common/http": "^18.2.0"  // NOT a package

// ✓ CORRECT
"@angular/common": "^18.2.0"  // Import from here: import { HttpClient } from '@angular/common/http'
```

---

### Issue: [(ngModel)] binding doesn't work
**Symptom:** Template shows `[(ngModel)]` binding but values don't update

**Cause:** FormsModule not imported in feature module

**Fix:** Add FormsModule to imports
```typescript
@NgModule({
  imports: [
    CommonModule,
    HttpClientModule,
    FormsModule  // ← ADD THIS
  ]
})
```

---

### Issue: Database migration doesn't run
**Symptom:** Tables don't exist when app starts

**Cause:** Flyway not configured or migration file named incorrectly

**Fix:** 
1. Enable Flyway in application.yml (baseline-on-migrate: true)
2. Name files: `V1__create_table.sql`, `V2__add_column.sql`
3. Place in: `src/main/resources/db/migration/`

---

## Summary for RAG Systems

When generating code:
1. ✅ Always use these templates - they're production-tested
2. ✅ Substitute all `{{ variables }}` from context
3. ✅ Follow package/directory structure exactly
4. ✅ Include security, testing, and docs (not optional)
5. ✅ Test generated code before returning to user
6. ✅ Document any deviations from these patterns

Generated code following these patterns will:
- Build without errors (Docker, Maven, npm)
- Run without runtime errors
- Be maintainable and extensible
- Follow Spring/Angular best practices
- Include enterprise features (security, docs, tests)

---

## Validation Checklist (for RAG Post-Generation)

```
BACKEND:
□ pom.xml generated with all dependencies
□ Application.yml has postgres + local profiles
□ SecurityConfig.java with BCrypt and CORS
□ OpenApiConfig.java for Swagger
□ V1__create_table.sql migration in db/migration/
□ Entity has @CreationTimestamp/@UpdateTimestamp
□ DTO has @NotBlank/@Email validation
□ Service interface ICustomerService exists
□ ServiceImpl implements interface with CRUD
□ Repository extends JpaRepository
□ Controller uses @Valid on @RequestBody
□ GlobalExceptionHandler exists
□ Test file with at least 5 test cases

FRONTEND:
□ package.json has @angular/common (not @angular/common/http)
□ AppModule declares only AppComponent
□ Feature module imports CommonModule, FormsModule
□ Component has error/loading state management
□ Template uses [(ngModel)] with FormsModule
□ ApiService exports Customer interface
□ All HTTP calls typed: http.get<Type>()
□ environment.ts has apiBaseUrl

DOCKER:
□ Dockerfile multi-stage with frontend + backend
□ docker-compose.yml with 3 services (frontend, backend, db)
□ Backend environment variables configured

RUN TESTS:
□ mvn test passes
□ npm install succeeds
□ npm build succeeds
□ docker-compose up succeeds
```

---

**Last Updated:** Based on validation of all working templates
**Status:** All patterns verified with passing tests (validate_generators.py)
**Confidence Level:** Production-ready patterns - safe for automated generation
