# Quick Reference - Code Generation Patterns

## Backend Layers (Spring Boot)

```
REQUEST → Controller (@RestController)
                ↓
            Service (@Service)
                ↓
           Repository (JpaRepository)
                ↓
          Database (SQL)
                ↓
           Mapper (Entity↔DTO)
                ↓
         RESPONSE (JSON)
```

---

## Backend Code Patterns

### Package Structure
```
com.example.hotel
├── entity/          Customer.java (@Entity)
├── dto/             CustomerDto.java (@Data)
├── repository/      ICustomerRepository.java extends JpaRepository
├── service/         ICustomerService.java (interface)
├── service/impl/    CustomerServiceImpl.java (@Service)
├── mapper/          CustomerMapper.java (@Component)
├── controller/      CustomerController.java (@RestController)
├── config/          SecurityConfig.java, OpenApiConfig.java
└── exception/       GlobalExceptionHandler.java (@RestControllerAdvice)
```

### Entity Pattern
```java
@Entity @Table(name = "customers") @Getter @Setter
public class Customer {
    @Id @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    
    @NotNull @Column(nullable = false)
    private String name;
    
    @CreationTimestamp @Column(updatable = false)
    private LocalDateTime createdAt;
    
    @UpdateTimestamp
    private LocalDateTime updatedAt;
}
```

### DTO Pattern
```java
@Data @NoArgsConstructor @AllArgsConstructor
public class CustomerDto {
    private UUID id;
    @NotBlank private String name;
    @Email private String email;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
```

### Service Pattern
```java
@Service @RequiredArgsConstructor
public class CustomerServiceImpl implements ICustomerService {
    private final ICustomerRepository repo;
    private final CustomerMapper mapper;
    
    public List<CustomerDto> findAll() {
        return repo.findAll().stream()
            .map(mapper::toDto).collect(Collectors.toList());
    }
}
```

### Controller Pattern
```java
@RestController @RequestMapping("/api/v1/customers")
@RequiredArgsConstructor
public class CustomerController {
    private final ICustomerService service;
    
    @GetMapping
    public ResponseEntity<List<CustomerDto>> findAll() {
        return ResponseEntity.ok(service.findAll());
    }
    
    @PostMapping
    public ResponseEntity<CustomerDto> create(@Valid @RequestBody CustomerDto dto) {
        return ResponseEntity
            .status(HttpStatus.CREATED)
            .body(service.create(dto));
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<CustomerDto> update(
        @PathVariable UUID id, @Valid @RequestBody CustomerDto dto) {
        return ResponseEntity.ok(service.update(id, dto));
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        service.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

---

## Frontend Layers (Angular)

```
USER INPUT ↙ Template (HTML)
            ↓
        Component (TypeScript)
            ↓
        Service (HTTP calls)
            ↓
      Backend API (/api/v1)
```

---

## Frontend Code Patterns

### Module Structure
```
src/app/
├── app.module.ts (BrowserModule, HttpClientModule, AppRoutingModule, CustomersModule)
├── app.component.ts + .html
├── app-routing.module.ts
├── core/
│   │── services/
│   │   └── api.service.ts (exports Customer interface)
│   └── models/
├── features/
│   └── customers/
│       ├── customers.module.ts (CommonModule, HttpClientModule, FormsModule)
│       └── customer-list/
│           ├── customer-list.component.ts
│           ├── customer-list.component.html
│           └── customer-list.component.css
└── environments/
    ├── environment.ts (localhost)
    └── environment.prod.ts (production)
```

### AppModule Pattern (DO NOT duplicate components)
```typescript
@NgModule({
  declarations: [AppComponent],  // ✓ ONLY root component
  imports: [
    BrowserModule,
    HttpClientModule,
    AppRoutingModule,
    CustomersModule  // ✓ Import module, not component
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}
```

### Feature Module Pattern
```typescript
@NgModule({
  declarations: [CustomerListComponent],
  imports: [
    CommonModule,      // ✓ For *ngIf, *ngFor
    HttpClientModule,  // ✓ For HTTP
    FormsModule        // ✓ For [(ngModel)]
  ],
  exports: [CustomerListComponent]
})
export class CustomersModule {}
```

### Component Pattern (State Management)
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
    name: '', email: '', company: ''
  };
  
  selectedCustomer: Customer | null = null;
  
  constructor(private apiService: ApiService) {}
  
  ngOnInit(): void {
    this.load();
  }
  
  load(): void {
    this.loading = true;
    this.apiService.getCustomers().subscribe({
      next: (data) => {
        this.customers = data;
        this.loading = false;
      },
      error: () => {
        this.error = 'Load failed';
        this.loading = false;
      }
    });
  }
}
```

### Template Pattern (Two-Way Binding)
```html
<!-- Error handling -->
<div *ngIf="error" class="error">{{ error }}</div>

<!-- Loading state -->
<div *ngIf="loading">Loading...</div>

<!-- Add form -->
<form (ngSubmit)="addCustomer()">
  <label>Name:
    <input [(ngModel)]="newCustomer.name" name="name" required />
  </label>
  <button type="submit">Add</button>
</form>

<!-- Edit form (conditional) -->
<div *ngIf="selectedCustomer" class="edit-form">
  <label>Name:
    <input [(ngModel)]="selectedCustomer.name" name="editName" />
  </label>
  <button (click)="updateCustomer()">Save</button>
</div>

<!-- List -->
<ul>
  <li *ngFor="let customer of customers" (click)="selectCustomer(customer)">
    {{ customer.name }}
    <button (click)="deleteCustomer(customer.id); $event.stopPropagation()">
      Delete
    </button>
  </li>
</ul>
```

### Service Pattern
```typescript
export interface Customer {
  id: string;
  name: string;
  email: string;
  company: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = environment.apiBaseUrl;
  
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

---

## Database & Migrations

### Flyway Migration Naming
```
V1__create_customers_table.sql       ← Initial
V2__add_company_column.sql           ← Enhancement
V3__create_hotels_table.sql          ← New entity
```

### Table Creation Pattern
```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    company VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_name ON customers(name);
```

---

## Configuration Files

### pom.xml Key Dependencies
```xml
<!-- Spring Boot -->
<groupId>org.springframework.boot</groupId>
<artifactId>spring-boot-starter-web</artifactId>
<artifactId>spring-boot-starter-security</artifactId>
<artifactId>spring-boot-starter-data-jpa</artifactId>

<!-- Database -->
<artifactId>spring-boot-starter-data-jpa</artifactId>
<groupId>org.flywaydb</groupId>
<artifactId>flyway-core</artifactId>

<!-- API Documentation -->
<groupId>org.springdoc</groupId>
<artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
<version>2.0.2</version>

<!-- Testing -->
<groupId>org.springframework.security</groupId>
<artifactId>spring-security-test</artifactId>
```

### application.yml Sections
```yaml
spring:
  jpa:
    hibernate.ddl-auto: validate  # or create-drop for local
  flyway:
    enabled: true
    baseline-on-migrate: true
    locations: classpath:db/migration
```

### package.json Angular Dependencies
```json
"@angular/common": "^18.2.0",
"@angular/forms": "^18.2.0",
"@angular/platform-browser": "^18.2.0",
"rxjs": "^7.8.1",
"zone.js": "^0.14.10",
"typescript": "~5.5.4"
```

---

## Testing Patterns

### Service Test Pattern
```java
@ExtendWith(MockitoExtension.class)
class CustomerServiceImplTest {
    @Mock ICustomerRepository repo;
    @Mock CustomerMapper mapper;
    @InjectMocks CustomerServiceImpl service;
    
    @Test
    void testFindAll() {
        // GIVEN
        Customer entity = new Customer();
        CustomerDto dto = new CustomerDto();
        when(repo.findAll()).thenReturn(List.of(entity));
        when(mapper.toDto(entity)).thenReturn(dto);
        
        // WHEN
        List<CustomerDto> result = service.findAll();
        
        // THEN
        assertThat(result).hasSize(1);
        verify(repo).findAll();
    }
}
```

---

## REST API Endpoints Reference

```
GET    /api/v1/customers         → List all
GET    /api/v1/customers/{id}    → Get one
POST   /api/v1/customers         → Create (202 Created)
PUT    /api/v1/customers/{id}    → Update
DELETE /api/v1/customers/{id}    → Delete (204 No Content)

Public:
GET    /actuator/health
GET    /v3/api-docs
GET    /swagger-ui/index.html

Protected:
All /api/v1/** endpoints require ROLE_ADMIN
```

---

## Common Mistakes to Avoid

| ❌ WRONG | ✅ CORRECT |
|---------|-----------|
| `@angular/common/http` in package.json | Import from `@angular/common/http` |
| Declare component in 2 modules | Declare in 1 module, import module in root |
| FormsModule missing | Add to feature module imports |
| @RequestBody without @Valid | Always validate DTOs |
| Service with business logic in controller | Service handles logic, controller handles HTTP |
| Observable with subscribe in service | Return Observable, let component subscribe |
| Timestamps editable by user | Use @CreationTimestamp/@UpdateTimestamp |
| id in create request | Use Omit<T, 'id'> for form models |
| No error handling in tests | Test both success and error paths |
| Database without migrations | Use Flyway, version all schema changes |

---

## Quick Validation Commands

```bash
# Backend
mvn clean compile          # Syntax check
mvn test                   # Run unit tests
mvn spring-boot:run       # Start server

# Frontend
npm install                # Install deps
npm build                  # Compile TypeScript
ng serve                  # Dev server
npm test                  # Run tests

# Docker
docker-compose up --build # Build & run all services
```

---

## Environment Variables (for Docker)

Backend needs:
```
DB_HOST=postgres        # Service name in docker-compose
DB_PORT=5432
DB_NAME=appdb
DB_USER=postgres
DB_PASSWORD=postgres
```

Frontend needs (in environment.ts):
```
apiBaseUrl=http://localhost:8080/api/v1  # Local dev
```

---

## Useful Property Substitutions

| Context Variable | Example | Usage |
|-----------------|---------|-------|
| `{{ project_name }}` | "Hotel Management" | Titles, pom.xml, package.json |
| `{{ project_package }}` | "com.example.hotel" | Package names, namespaces |
| `{{ description }}` | "Hotel booking system" | OpenAPI info, README |
| `{{ entity_name }}` | "Customer" | Class names, types |
| `{{ entity_name_plural }}` | "customers" | Table names, API paths, URLs |
| `{{ base_path }}` | "/api/v1" | Controller base paths |
| `{{ port_backend }}` | "8080" | Port configuration |
| `{{ port_frontend }}` | "4200" | Angular dev server port |

---

## Template Files Reference

| Template File | Generates | Package |
|---------------|-----------|---------|
| pom.xml.j2 | Maven config | N/A |
| application.yml.j2 | Spring config | N/A |
| security_config.java.j2 | SecurityConfig.java | config/ |
| openapi_config.java.j2 | OpenApiConfig.java | config/ |
| migration_v1_create_customers.sql.j2 | V1__.sql | db/migration/ |
| entity.java.j2 | Entity.java | entity/ |
| dto.java.j2 | Dto.java | dto/ |
| service.java.j2 | IService.java | service/ |
| service_impl.java.j2 | ServiceImpl.java | service/impl/ |
| mapper.java.j2 | Mapper.java | mapper/ |
| repository.java.j2 | IRepository.java | repository/ |
| controller.java.j2 | Controller.java | controller/ |
| exception_handler.java.j2 | GlobalExceptionHandler.java | exception/ |
| customer_service_test.java.j2 | ServiceTest.java | test/service/ |
| package.json.j2 | package.json | / |
| app.module.ts.j2 | app.module.ts | app/ |
| component.ts.j2 | component.ts | features/{entity}/ |
| component.html.j2 | component.html | features/{entity}/ |
| service.ts.j2 | api.service.ts | core/services/ |

---

## Decision Tree: What to Generate

```
User says "Generate a {system}" with "{entity}"
    ↓
├─ Backend needed?
│  ├─ YES → Generate ALL Spring Boot layers
│  │   ├─ pom.xml
│  │   ├─ application.yml
│  │   ├─ SecurityConfig.java (ALWAYS)
│  │   ├─ OpenApiConfig.java (ALWAYS)
│  │   ├─ V1__create_table.sql (ALWAYS)
│  │   ├─ Entity.java
│  │   ├─ Dto.java
│  │   ├─ IRepository.java
│  │   ├─ IService.java + ServiceImpl.java
│  │   ├─ Mapper.java
│  │   ├─ Controller.java
│  │   ├─ GlobalExceptionHandler.java
│  │   └─ ServiceTest.java
│  └─ NO → Skip backend
│
├─ Frontend needed?
│  ├─ YES → Generate ALL Angular files
│  │   ├─ package.json (NO @angular/common/http)
│  │   ├─ app.module.ts (Import CustomersModule, NOT component)
│  │   ├─ CustomersModule (With FormsModule)
│  │   ├─ component.ts (ngOnInit, fetchData, CRUD methods)
│  │   ├─ component.html (Forms with [(ngModel)], lists)
│  │   ├─ component.css (Styling)
│  │   ├─ ApiService (Returns Observable<T>)
│  │   ├─ Customer interface (In service)
│  │   ├─ environment.ts
│  │   ├─ app-routing.module.ts
│  │   └─ app.component.ts/html
│  └─ NO → Skip frontend
│
└─ Docker needed?
   ├─ YES → Generate
   │   ├─ Dockerfile (Multi-stage)
   │   └─ docker-compose.yml
   └─ NO → Skip Docker
```

---

## Success Checklist

After generation, verify:

**Backend:**
- [ ] mvn compile succeeds
- [ ] mvn test all pass
- [ ] All classes compile
- [ ] SecurityConfig has BCrypt + CORS
- [ ] OpenApiConfig bean created
- [ ] Flyway migration named V1__*
- [ ] Entity has timestamps
- [ ] DTO has validation
- [ ] Service has CRUD operations
- [ ] Controller validates @RequestBody

**Frontend:**
- [ ] npm install succeeds
- [ ] npm build succeeds
- [ ] NO `@angular/common/http` in package.json
- [ ] AppModule imports CustomersModule
- [ ] CustomersModule imports FormsModule
- [ ] Component has error/loading state
- [ ] Template uses [(ngModel)] bindings
- [ ] ApiService exports Customer interface
- [ ] environment.ts has apiBaseUrl

**Integration:**
- [ ] Docker compose builds
- [ ] Backend starts on 8080
- [ ] Frontend accessible on 4200
- [ ] Database migrations run
- [ ] API responds to requests
