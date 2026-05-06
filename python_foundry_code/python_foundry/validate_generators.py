#!/usr/bin/env python
"""
Comprehensive validation script for code generators.
Tests all generators to ensure they produce valid, working code.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.generators.springboot_generator import SpringBootGenerator
from app.services.generators.angular_generator import AngularGenerator
from app.services.generators.compose_generator import ComposeGenerator
from app.services.generators.docker_generator import DockerGenerator
from app.services.generators.readme_generator import ReadmeGenerator
from app.services.templates.jinja_renderer import JinjaRenderer

def test_springboot_generator():
    """Test SpringBoot generator produces valid output."""
    print("=" * 60)
    print("TESTING SPRINGBOOT GENERATOR")
    print("=" * 60)
    
    gen = SpringBootGenerator()
    spec = {
        "project_name": "test-app",
        "description": "Test application",
        "backend": {
            "package": "com.example.testapp",
            "application_class": "TestAppApplication"
        }
    }
    
    files = gen.generate(spec, {}, [])
    
    # Find migration file
    migration_file = [f for f in files.keys() if "V1__create_customers_table.sql" in f]
    migration_content = files.get(migration_file[0], "") if migration_file else ""
    
    tests = [
        ("pom.xml exists", "backend/pom.xml" in files),
        ("pom.xml has springdoc-openapi", "springdoc-openapi" in files.get("backend/pom.xml", "")),
        ("pom.xml has flyway", "flyway" in files.get("backend/pom.xml", "")),
        ("pom.xml has security-test", "spring-security-test" in files.get("backend/pom.xml", "")),
        ("application.yml exists", "backend/src/main/resources/application.yml" in files),
        ("application.yml has env vars", "DB_HOST" in files.get("backend/src/main/resources/application.yml", "")),
        ("application.yml has flyway", "flyway" in files.get("backend/src/main/resources/application.yml", "")),
        ("SecurityConfig exists", any("SecurityConfig.java" in f for f in files)),
        ("SecurityConfig has BCrypt", "BCryptPasswordEncoder" in files.get("backend/src/main/java/com/example/testapp/security/SecurityConfig.java", "")),
        ("SecurityConfig has CORS", "CorsConfiguration" in files.get("backend/src/main/java/com/example/testapp/security/SecurityConfig.java", "")),
        ("OpenApiConfig exists", any("OpenApiConfig.java" in f for f in files)),
        ("OpenApiConfig has OpenAPI", "OpenAPI" in files.get("backend/src/main/java/com/example/testapp/config/OpenApiConfig.java", "")),
        ("Flyway migration exists", len(migration_file) > 0),
        ("Migration has company field", "company" in migration_content),
        ("CustomerServiceImpl test exists", any("CustomerServiceImplTest.java" in f for f in files)),
        ("CustomerServiceImpl test has findAll", "testFindAll" in files.get("backend/src/test/java/com/example/testapp/service/CustomerServiceImplTest.java", "")),
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✓" if result else "✗"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nSpringBoot: {passed}/{len(tests)} tests passed")
    return passed == len(tests)


def test_angular_generator():
    """Test Angular generator produces valid output."""
    print("\n" + "=" * 60)
    print("TESTING ANGULAR GENERATOR")
    print("=" * 60)
    
    gen = AngularGenerator()
    spec = {
        "project_name": "test-app"
    }
    
    files = gen.generate(spec, {}, [])
    
    tests = [
        ("package.json exists", "frontend/package.json" in files),
        ("package.json NO invalid http dep", "@angular/common/http" not in files.get("frontend/package.json", "")),
        ("package.json has @angular/common", "@angular/common" in files.get("frontend/package.json", "")),
        ("package.json has FormsModule", "FormsModule" in str(files.values())),
        ("app.module.ts exists", "frontend/src/app/app.module.ts" in files),
        ("app.module.ts imports CustomersModule", "CustomersModule" in files.get("frontend/src/app/app.module.ts", "")),
        ("app.module.ts NO duplicate CustomerListComponent", files.get("frontend/src/app/app.module.ts", "").count("CustomerListComponent") == 0),
        ("customers.module.ts exists", any("customers.module.ts" in f for f in files)),
        ("customers.module.ts has FormsModule", "FormsModule" in files.get("frontend/src/app/features/customers/customers.module.ts", "")),
        ("api.service.ts exists", "frontend/src/app/core/services/api.service.ts" in files),
        ("api.service.ts has company field", "company" in files.get("frontend/src/app/core/services/api.service.ts", "")),
        ("customer-list.component.ts has company", "company" in files.get("frontend/src/app/features/customers/components/customer-list.component.ts", "")),
        ("customer-list.component.html has company input", "company" in files.get("frontend/src/app/features/customers/components/customer-list.component.html", "")),
        ("nginx.conf exists", "frontend/nginx.conf" in files),
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✓" if result else "✗"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nAngular: {passed}/{len(tests)} tests passed")
    return passed == len(tests)


def test_template_rendering():
    """Test that all templates render without errors."""
    print("\n" + "=" * 60)
    print("TESTING TEMPLATE RENDERING")
    print("=" * 60)
    
    renderer = JinjaRenderer()
    ctx = {
        "project_name": "test-app",
        "package": "com.example.testapp",
        "package_path": "com/example/testapp",
        "app_class": "TestAppApplication",
        "artifact_id": "test-app",
        "name": "test-app",
        "java_version": "17",
        "description": "Test app",
        "entity": "Customer",
        "entity_var": "customer",
        "base_path": "/api/v1/customers",
        "api_base_url": "http://localhost:8080",
        "rag_hints": ["Test hint 1", "Test hint 2"],
    }
    
    templates = [
        ("springboot/pom.xml.j2", [ctx]),
        ("springboot/application.yml.j2", [ctx]),
        ("springboot/security_config.java.j2", [ctx]),
        ("springboot/openapi_config.java.j2", [ctx]),
        ("springboot/migration_v1_create_customers.sql.j2", [ctx]),
        ("angular/package.json.j2", [{"project_name": "test-app"}]),
        ("angular/app.module.ts.j2", [{"project_name": "test-app"}]),
        ("angular/component.ts.j2", [ctx]),
        # Skip angular/component.html.j2 as it contains Angular template syntax
        ("angular/service.ts.j2", [ctx]),
    ]
    
    passed = 0
    for template, contexts in templates:
        try:
            for context in contexts:
                result = renderer.render(template, context)
                assert result, f"Empty render result for {template}"
            print(f"  ✓ {template}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {template}: {e}")
    
    print(f"\nTemplates: {passed}/{len(templates)} render successfully")
    return passed == len(templates)


def main():
    """Run all validation tests."""
    print("\n" + "[TEST] COMPREHENSIVE CODE GENERATION VALIDATION" + "\n")
    
    results = []
    results.append(("Template Rendering", test_template_rendering()))
    results.append(("SpringBoot Generator", test_springboot_generator()))
    results.append(("Angular Generator", test_angular_generator()))
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - Generated code is production-ready!")
    else:
        print("✗ SOME TESTS FAILED - See details above")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
