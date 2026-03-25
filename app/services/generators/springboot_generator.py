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
            f"backend/src/test/java/{package_path}/{app_class}Tests.java": self._test_java(package, app_class),
            f"backend/src/test/java/{package_path}/service/CustomerServiceImplTest.java": self._customer_service_test(package),
        }
        return files

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

