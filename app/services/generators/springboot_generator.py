from app.services.generators.base import BaseGenerator
from app.services.templates.jinja_renderer import JinjaRenderer
from app.services.templates.template_registry import TemplateRegistry


class SpringBootGenerator(BaseGenerator):
    def __init__(self) -> None:
        self.renderer = JinjaRenderer()

    def generate(self, project_spec: dict, api_contract: dict, rag_context: list[dict]) -> dict[str, str]:
        package = project_spec["backend"]["package"]
        package_path = package.replace(".", "/")
        app_class = project_spec["backend"]["application_class"]
        domain = str(project_spec.get("domain", "general")).lower()
        ecommerce_mode = domain in {"ecommerce", "retail"}

        ctx = {
            "project_name": project_spec["project_name"],
            "package": package,
            "package_path": package_path,
            "app_class": app_class,
            "java_version": "17",
            "artifact_id": project_spec["project_name"],
            "name": project_spec["project_name"],
            "description": project_spec["description"],
            "entity": "Customer",
            "entity_var": "customer",
            "base_path": "/api/v1/customers",
            "rag_hints": [item.get("content", "")[:180] for item in rag_context[:2]],
            "domain": domain,
        }

        files: dict[str, str] = {
            "backend/pom.xml": self.renderer.render(TemplateRegistry.SPRINGBOOT_POM.path, ctx),
            "backend/src/main/resources/application.yml": self.renderer.render(
                TemplateRegistry.SPRINGBOOT_APP_YML.path,
                ctx,
            ),
            f"backend/src/main/java/{package_path}/{app_class}.java": self._application_java(package, app_class),
            f"backend/src/main/java/{package_path}/controller/CustomerController.java": self.renderer.render(
                TemplateRegistry.SPRINGBOOT_CONTROLLER.path,
                ctx,
            ),
            f"backend/src/main/java/{package_path}/service/CustomerService.java": self.renderer.render(
                TemplateRegistry.SPRINGBOOT_SERVICE.path,
                ctx,
            ),
            f"backend/src/main/java/{package_path}/service/impl/CustomerServiceImpl.java": self._service_impl_java(package),
            f"backend/src/main/java/{package_path}/repository/CustomerRepository.java": self.renderer.render(
                TemplateRegistry.SPRINGBOOT_REPOSITORY.path,
                ctx,
            ),
            f"backend/src/main/java/{package_path}/entity/Customer.java": self.renderer.render(
                TemplateRegistry.SPRINGBOOT_ENTITY.path,
                ctx,
            ),
            f"backend/src/main/java/{package_path}/dto/CustomerDto.java": self.renderer.render(
                TemplateRegistry.SPRINGBOOT_DTO.path,
                ctx,
            ),
            f"backend/src/main/java/{package_path}/mapper/CustomerMapper.java": self._mapper_java(package),
            f"backend/src/main/java/{package_path}/exception/GlobalExceptionHandler.java": self.renderer.render(
                TemplateRegistry.SPRINGBOOT_EXCEPTION.path,
                ctx,
            ),
            f"backend/src/main/java/{package_path}/exception/ResourceNotFoundException.java": self._resource_not_found(package),
            f"backend/src/main/java/{package_path}/security/SecurityConfig.java": self.renderer.render(
                TemplateRegistry.SPRINGBOOT_SECURITY_CONFIG.path,
                ctx,
            ),
            f"backend/src/main/java/{package_path}/config/OpenApiConfig.java": self.renderer.render(
                TemplateRegistry.SPRINGBOOT_OPENAPI_CONFIG.path,
                ctx,
            ),
            "backend/src/main/resources/db/migration/V1__create_customers_table.sql": self.renderer.render(
                TemplateRegistry.SPRINGBOOT_MIGRATION_V1.path,
                ctx,
            ),
            "backend/Dockerfile": self.renderer.render(TemplateRegistry.SPRINGBOOT_DOCKERFILE.path, ctx),
            "backend/.gitignore": self._gitignore(),
            f"backend/src/test/java/{package_path}/{app_class}Tests.java": self._test_java(package, app_class),
            f"backend/src/test/java/{package_path}/service/CustomerServiceImplTest.java": self._customer_service_test(package),
        }
        if ecommerce_mode:
            files.update(
                {
                    f"backend/src/main/java/{package_path}/entity/Product.java": self._product_entity_java(package),
                    f"backend/src/main/java/{package_path}/dto/ProductDto.java": self._product_dto_java(package),
                    f"backend/src/main/java/{package_path}/repository/ProductRepository.java": self._product_repository_java(
                        package
                    ),
                    f"backend/src/main/java/{package_path}/service/ProductService.java": self._product_service_java(package),
                    f"backend/src/main/java/{package_path}/service/impl/ProductServiceImpl.java": self._product_service_impl_java(
                        package
                    ),
                    f"backend/src/main/java/{package_path}/controller/ProductController.java": self._product_controller_java(
                        package
                    ),
                    "backend/src/main/resources/db/migration/V2__create_products_table.sql": self._product_migration_sql(),
                }
            )
        return files

    @staticmethod
    def _gitignore() -> str:
        return """target/
!.mvn/wrapper/maven-wrapper.jar
!**/src/main/**/target/
!**/src/test/**/target/
.idea
*.iml
*.ipr
*.iws
.vscode/
.DS_Store
HELP.md
"""

    @staticmethod
    def _trigger_workflow() -> str:
        return """name: Build Push And GitOps Update (Backend)

on:
  push:
    branches:
      - main
      - master

permissions:
  contents: write

jobs:
  build-and-update:
    if: github.actor != 'github-actions[bot]'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set image variables
        id: vars
        run: |
          IMAGE_REPO="devopspaxarisglobalrepo/finaltest36-admin-backend-test-backend"
          IMAGE_TAG="${GITHUB_SHA}"
          echo "image_repo=$IMAGE_REPO" >> "$GITHUB_OUTPUT"
          echo "image_tag=$IMAGE_TAG" >> "$GITHUB_OUTPUT"

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ vars.DOCKERHUB_USERNAME }}
          password: ${{ vars.DOCKERHUB_TOKEN }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Build and push image
        uses: docker/build-push-action@v6
        with:
          context: ./backend
          file: ./backend/Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ${{ steps.vars.outputs.image_repo }}:latest
            ${{ steps.vars.outputs.image_repo }}:${{ steps.vars.outputs.image_tag }}

      - name: Update k8 image tag
        run: |
          sed -E -i.bak "s|^([[:space:]]*)image:[[:space:]].*|\\1image: ${{ steps.vars.outputs.image_repo }}:${{ steps.vars.outputs.image_tag }}|" k8/deployment.yaml
          rm -f k8/deployment.yaml.bak

      - name: Commit and push manifest changes
        run: |
          if git diff --quiet; then
            echo "No manifest changes to commit"
            exit 0
          fi
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add k8/deployment.yaml
          git commit -m "ci: update image tag [skip ci]"
          git push
"""

    @staticmethod
    def _application_java(package: str, app_class: str) -> str:
        return f"""package {package};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class {app_class} {{
    public static void main(String[] args) {{
        SpringApplication.run({app_class}.class, args);
    }}
}}
"""

    @staticmethod
    def _service_impl_java(package: str) -> str:
        return f"""package {package}.service.impl;

import {package}.dto.CustomerDto;
import {package}.entity.Customer;
import {package}.exception.ResourceNotFoundException;
import {package}.mapper.CustomerMapper;
import {package}.repository.CustomerRepository;
import {package}.service.CustomerService;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class CustomerServiceImpl implements CustomerService {{
    private final CustomerRepository customerRepository;

    public CustomerServiceImpl(CustomerRepository customerRepository) {{
        this.customerRepository = customerRepository;
    }}

    @Override
    public List<CustomerDto> findAll() {{
        return customerRepository.findAll().stream().map(CustomerMapper::toDto).collect(Collectors.toList());
    }}

    @Override
    public CustomerDto findById(UUID id) {{
        Customer customer = customerRepository
            .findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Customer not found: " + id));
        return CustomerMapper.toDto(customer);
    }}

    @Override
    public CustomerDto create(CustomerDto dto) {{
        Customer customer = CustomerMapper.toEntity(dto);
        customer.setId(null);
        return CustomerMapper.toDto(customerRepository.save(customer));
    }}

    @Override
    public CustomerDto update(UUID id, CustomerDto dto) {{
        Customer existing = customerRepository
            .findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Customer not found: " + id));
        existing.setName(dto.getName());
        existing.setEmail(dto.getEmail());
        existing.setCompany(dto.getCompany());
        return CustomerMapper.toDto(customerRepository.save(existing));
    }}

    @Override
    public void delete(UUID id) {{
        if (!customerRepository.existsById(id)) {{
            throw new ResourceNotFoundException("Customer not found: " + id);
        }}
        customerRepository.deleteById(id);
    }}
}}
"""

    @staticmethod
    def _mapper_java(package: str) -> str:
        return f"""package {package}.mapper;

import {package}.dto.CustomerDto;
import {package}.entity.Customer;

public class CustomerMapper {{
    private CustomerMapper() {{}}

    public static CustomerDto toDto(Customer entity) {{
        CustomerDto dto = new CustomerDto();
        dto.setId(entity.getId());
        dto.setName(entity.getName());
        dto.setEmail(entity.getEmail());
        dto.setCompany(entity.getCompany());
        return dto;
    }}

    public static Customer toEntity(CustomerDto dto) {{
        Customer entity = new Customer();
        entity.setId(dto.getId());
        entity.setName(dto.getName());
        entity.setEmail(dto.getEmail());
        entity.setCompany(dto.getCompany());
        return entity;
    }}
}}
"""

    @staticmethod
    def _resource_not_found(package: str) -> str:
        return f"""package {package}.exception;

public class ResourceNotFoundException extends RuntimeException {{
    public ResourceNotFoundException(String message) {{
        super(message);
    }}
}}
"""

    @staticmethod
    def _test_java(package: str, app_class: str) -> str:
        return f"""package {package};

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class {app_class}Tests {{
    @Test
    void contextLoads() {{
    }}
}}
"""

    @staticmethod
    def _customer_service_test(package: str) -> str:
        return f"""package {package}.service;

import {package}.dto.CustomerDto;
import {package}.entity.Customer;
import {package}.exception.ResourceNotFoundException;
import {package}.mapper.CustomerMapper;
import {package}.repository.CustomerRepository;
import {package}.service.impl.CustomerServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CustomerServiceImplTest {{
    @Mock
    private CustomerRepository customerRepository;

    @InjectMocks
    private CustomerServiceImpl customerService;

    private UUID customerId;
    private Customer customer;
    private CustomerDto customerDto;

    @BeforeEach
    void setUp() {{
        customerId = UUID.randomUUID();
        
        customer = new Customer();
        customer.setId(customerId);
        customer.setName("John Doe");
        customer.setEmail("john@example.com");
        customer.setCompany("ACME Corp");

        customerDto = new CustomerDto();
        customerDto.setId(customerId);
        customerDto.setName("John Doe");
        customerDto.setEmail("john@example.com");
        customerDto.setCompany("ACME Corp");
    }}

    @Test
    void testFindAll() {{
        List<Customer> customers = List.of(customer);
        when(customerRepository.findAll()).thenReturn(customers);

        List<CustomerDto> result = customerService.findAll();

        assertNotNull(result);
        assertEquals(1, result.size());
        verify(customerRepository, times(1)).findAll();
    }}

    @Test
    void testFindById() {{
        when(customerRepository.findById(customerId)).thenReturn(Optional.of(customer));

        CustomerDto result = customerService.findById(customerId);

        assertNotNull(result);
        assertEquals("John Doe", result.getName());
        verify(customerRepository, times(1)).findById(customerId);
    }}

    @Test
    void testFindByIdNotFound() {{
        when(customerRepository.findById(customerId)).thenReturn(Optional.empty());

        assertThrows(ResourceNotFoundException.class, () -> customerService.findById(customerId));
        verify(customerRepository, times(1)).findById(customerId);
    }}

    @Test
    void testCreate() {{
        when(customerRepository.save(any(Customer.class))).thenReturn(customer);

        CustomerDto result = customerService.create(customerDto);

        assertNotNull(result);
        assertEquals("John Doe", result.getName());
        verify(customerRepository, times(1)).save(any(Customer.class));
    }}

    @Test
    void testUpdate() {{
        when(customerRepository.findById(customerId)).thenReturn(Optional.of(customer));
        when(customerRepository.save(any(Customer.class))).thenReturn(customer);

        CustomerDto updated = new CustomerDto();
        updated.setId(customerId);
        updated.setName("Jane Doe");
        updated.setEmail("jane@example.com");
        updated.setCompany("ACME Inc");

        CustomerDto result = customerService.update(customerId, updated);

        assertNotNull(result);
        verify(customerRepository, times(1)).findById(customerId);
        verify(customerRepository, times(1)).save(any(Customer.class));
    }}

    @Test
    void testDelete() {{
        when(customerRepository.existsById(customerId)).thenReturn(true);

        customerService.delete(customerId);

        verify(customerRepository, times(1)).deleteById(customerId);
    }}

    @Test
    void testDeleteNotFound() {{
        when(customerRepository.existsById(customerId)).thenReturn(false);

        assertThrows(ResourceNotFoundException.class, () -> customerService.delete(customerId));
    }}
}}
"""

    @staticmethod
    def _product_entity_java(package: str) -> str:
        return f"""package {package}.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.util.UUID;

@Entity
@Table(name = "products")
public class Product {{
    @Id
    @GeneratedValue
    private UUID id;

    @Column(nullable = false)
    private String name;

    @Column(length = 2000)
    private String description;

    @Column(nullable = false)
    private BigDecimal price;

    @Column(nullable = false)
    private Integer stockQuantity;

    private String brand;
    private String category;
    private String imageUrl;

    public UUID getId() {{ return id; }}
    public void setId(UUID id) {{ this.id = id; }}
    public String getName() {{ return name; }}
    public void setName(String name) {{ this.name = name; }}
    public String getDescription() {{ return description; }}
    public void setDescription(String description) {{ this.description = description; }}
    public BigDecimal getPrice() {{ return price; }}
    public void setPrice(BigDecimal price) {{ this.price = price; }}
    public Integer getStockQuantity() {{ return stockQuantity; }}
    public void setStockQuantity(Integer stockQuantity) {{ this.stockQuantity = stockQuantity; }}
    public String getBrand() {{ return brand; }}
    public void setBrand(String brand) {{ this.brand = brand; }}
    public String getCategory() {{ return category; }}
    public void setCategory(String category) {{ this.category = category; }}
    public String getImageUrl() {{ return imageUrl; }}
    public void setImageUrl(String imageUrl) {{ this.imageUrl = imageUrl; }}
}}
"""

    @staticmethod
    def _product_dto_java(package: str) -> str:
        return f"""package {package}.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.UUID;

public class ProductDto {{
    private UUID id;
    @NotBlank
    private String name;
    private String description;
    @NotNull
    @DecimalMin("0.0")
    private BigDecimal price;
    @NotNull
    private Integer stockQuantity;
    private String brand;
    private String category;
    private String imageUrl;

    public UUID getId() {{ return id; }}
    public void setId(UUID id) {{ this.id = id; }}
    public String getName() {{ return name; }}
    public void setName(String name) {{ this.name = name; }}
    public String getDescription() {{ return description; }}
    public void setDescription(String description) {{ this.description = description; }}
    public BigDecimal getPrice() {{ return price; }}
    public void setPrice(BigDecimal price) {{ this.price = price; }}
    public Integer getStockQuantity() {{ return stockQuantity; }}
    public void setStockQuantity(Integer stockQuantity) {{ this.stockQuantity = stockQuantity; }}
    public String getBrand() {{ return brand; }}
    public void setBrand(String brand) {{ this.brand = brand; }}
    public String getCategory() {{ return category; }}
    public void setCategory(String category) {{ this.category = category; }}
    public String getImageUrl() {{ return imageUrl; }}
    public void setImageUrl(String imageUrl) {{ this.imageUrl = imageUrl; }}
}}
"""

    @staticmethod
    def _product_repository_java(package: str) -> str:
        return f"""package {package}.repository;

import {package}.entity.Product;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ProductRepository extends JpaRepository<Product, UUID> {{
}}
"""

    @staticmethod
    def _product_service_java(package: str) -> str:
        return f"""package {package}.service;

import {package}.dto.ProductDto;
import java.util.List;
import java.util.UUID;

public interface ProductService {{
    List<ProductDto> findAll();
    ProductDto findById(UUID id);
    ProductDto create(ProductDto dto);
    ProductDto update(UUID id, ProductDto dto);
    void delete(UUID id);
}}
"""

    @staticmethod
    def _product_service_impl_java(package: str) -> str:
        return f"""package {package}.service.impl;

import {package}.dto.ProductDto;
import {package}.entity.Product;
import {package}.exception.ResourceNotFoundException;
import {package}.repository.ProductRepository;
import {package}.service.ProductService;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class ProductServiceImpl implements ProductService {{
    private final ProductRepository productRepository;

    public ProductServiceImpl(ProductRepository productRepository) {{
        this.productRepository = productRepository;
    }}

    @Override
    public List<ProductDto> findAll() {{
        return productRepository.findAll().stream().map(this::toDto).collect(Collectors.toList());
    }}

    @Override
    public ProductDto findById(UUID id) {{
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product not found: " + id));
        return toDto(product);
    }}

    @Override
    public ProductDto create(ProductDto dto) {{
        Product product = toEntity(dto);
        product.setId(null);
        return toDto(productRepository.save(product));
    }}

    @Override
    public ProductDto update(UUID id, ProductDto dto) {{
        Product existing = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product not found: " + id));
        existing.setName(dto.getName());
        existing.setDescription(dto.getDescription());
        existing.setPrice(dto.getPrice());
        existing.setStockQuantity(dto.getStockQuantity());
        existing.setBrand(dto.getBrand());
        existing.setCategory(dto.getCategory());
        existing.setImageUrl(dto.getImageUrl());
        return toDto(productRepository.save(existing));
    }}

    @Override
    public void delete(UUID id) {{
        if (!productRepository.existsById(id)) {{
            throw new ResourceNotFoundException("Product not found: " + id);
        }}
        productRepository.deleteById(id);
    }}

    private ProductDto toDto(Product entity) {{
        ProductDto dto = new ProductDto();
        dto.setId(entity.getId());
        dto.setName(entity.getName());
        dto.setDescription(entity.getDescription());
        dto.setPrice(entity.getPrice());
        dto.setStockQuantity(entity.getStockQuantity());
        dto.setBrand(entity.getBrand());
        dto.setCategory(entity.getCategory());
        dto.setImageUrl(entity.getImageUrl());
        return dto;
    }}

    private Product toEntity(ProductDto dto) {{
        Product entity = new Product();
        entity.setId(dto.getId());
        entity.setName(dto.getName());
        entity.setDescription(dto.getDescription());
        entity.setPrice(dto.getPrice());
        entity.setStockQuantity(dto.getStockQuantity());
        entity.setBrand(dto.getBrand());
        entity.setCategory(dto.getCategory());
        entity.setImageUrl(dto.getImageUrl());
        return entity;
    }}
}}
"""

    @staticmethod
    def _product_controller_java(package: str) -> str:
        return f"""package {package}.controller;

import {package}.dto.ProductDto;
import {package}.service.ProductService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/products")
public class ProductController {{
    private final ProductService productService;

    public ProductController(ProductService productService) {{
        this.productService = productService;
    }}

    @GetMapping
    public ResponseEntity<List<ProductDto>> findAll() {{
        return ResponseEntity.ok(productService.findAll());
    }}

    @GetMapping("/{{id}}")
    public ResponseEntity<ProductDto> findById(@PathVariable UUID id) {{
        return ResponseEntity.ok(productService.findById(id));
    }}

    @PostMapping
    public ResponseEntity<ProductDto> create(@Valid @RequestBody ProductDto payload) {{
        return ResponseEntity.status(HttpStatus.CREATED).body(productService.create(payload));
    }}

    @PutMapping("/{{id}}")
    public ResponseEntity<ProductDto> update(@PathVariable UUID id, @Valid @RequestBody ProductDto payload) {{
        return ResponseEntity.ok(productService.update(id, payload));
    }}

    @DeleteMapping("/{{id}}")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {{
        productService.delete(id);
        return ResponseEntity.noContent().build();
    }}
}}
"""

    @staticmethod
    def _product_migration_sql() -> str:
        return """CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    brand VARCHAR(120),
    category VARCHAR(120),
    image_url VARCHAR(512),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO products (id, name, description, price, stock_quantity, brand, category, image_url)
VALUES
    (gen_random_uuid(), 'Solid Casual Shirt', 'Breathable cotton shirt for daily wear', 1299.00, 120, 'Roadster', 'Men', 'https://picsum.photos/seed/prod1/600/800'),
    (gen_random_uuid(), 'Printed Kurta Set', 'Elegant festive kurta with matching bottoms', 1599.00, 80, 'Libas', 'Women', 'https://picsum.photos/seed/prod2/600/800'),
    (gen_random_uuid(), 'Running Sneakers', 'Cushioned running shoes', 2499.00, 140, 'Puma', 'Footwear', 'https://picsum.photos/seed/prod3/600/800')
ON CONFLICT DO NOTHING;
"""

