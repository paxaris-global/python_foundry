from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateRef:
    name: str
    path: str


class TemplateRegistry:
    SPRINGBOOT_POM = TemplateRef("springboot_pom", "springboot/pom.xml.j2")
    SPRINGBOOT_APP_YML = TemplateRef("springboot_application_yml", "springboot/application.yml.j2")
    SPRINGBOOT_CONTROLLER = TemplateRef("springboot_controller", "springboot/controller.java.j2")
    SPRINGBOOT_SERVICE = TemplateRef("springboot_service", "springboot/service.java.j2")
    SPRINGBOOT_REPOSITORY = TemplateRef("springboot_repository", "springboot/repository.java.j2")
    SPRINGBOOT_ENTITY = TemplateRef("springboot_entity", "springboot/entity.java.j2")
    SPRINGBOOT_DTO = TemplateRef("springboot_dto", "springboot/dto.java.j2")
    SPRINGBOOT_EXCEPTION = TemplateRef("springboot_exception", "springboot/exception_handler.java.j2")
    SPRINGBOOT_DOCKERFILE = TemplateRef("springboot_dockerfile", "springboot/Dockerfile.j2")
    SPRINGBOOT_SECURITY_CONFIG = TemplateRef("springboot_security_config", "springboot/security_config.java.j2")
    SPRINGBOOT_OPENAPI_CONFIG = TemplateRef("springboot_openapi_config", "springboot/openapi_config.java.j2")
    SPRINGBOOT_MIGRATION_V1 = TemplateRef("springboot_migration_v1", "springboot/migration_v1_create_customers.sql.j2")

    ANGULAR_ANGULAR_JSON = TemplateRef("angular_json", "angular/angular.json.j2")
    ANGULAR_PACKAGE_JSON = TemplateRef("angular_package_json", "angular/package.json.j2")
    ANGULAR_APP_MODULE = TemplateRef("angular_app_module", "angular/app.module.ts.j2")
    ANGULAR_APP_ROUTING = TemplateRef("angular_app_routing", "angular/app-routing.module.ts.j2")
    ANGULAR_COMPONENT = TemplateRef("angular_component", "angular/component.ts.j2")
    ANGULAR_COMPONENT_HTML = TemplateRef("angular_component_html", "angular/component.html.j2")
    ANGULAR_COMPONENT_CSS = TemplateRef("angular_component_css", "angular/component.css.j2")
    ANGULAR_SERVICE = TemplateRef("angular_service", "angular/service.ts.j2")
    ANGULAR_DOCKERFILE = TemplateRef("angular_dockerfile", "angular/Dockerfile.j2")
    ANGULAR_ENVIRONMENT = TemplateRef("angular_environment", "angular/environment.ts.j2")
    ANGULAR_STYLES_CSS = TemplateRef("angular_styles_css", "angular/styles.css.j2")

    DOCKER_COMPOSE = TemplateRef("docker_compose", "docker/docker-compose.yml.j2")
    README = TemplateRef("docs_readme", "docs/README.md.j2")
