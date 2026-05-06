"""Quick verification that all modules import correctly."""
print("Importing generators...")
from app.services.generators.springboot_generator import SpringBootGenerator
from app.services.generators.angular_generator import AngularGenerator
from app.services.generators.compose_generator import ComposeGenerator
print("✓ All generators import successfully")

print("\nImporting template registry...")
from app.services.templates.template_registry import TemplateRegistry
print("✓ Template registry imports successfully")

print("\nTesting SpringBoot generator instantiation...")
sb_gen = SpringBootGenerator()
print("✓ SpringBoot generator instantiates")

print("\nTesting Angular generator instantiation...")
ng_gen = AngularGenerator()
print("✓ Angular generator instantiates")

print("\nGenerating test project...")
spec = {
    "project_name": "quick-test",
    "description": "Quick test",
    "backend": {
        "package": "com.test",
        "application_class": "QuickTestApp"
    }
}
files = sb_gen.generate(spec, {}, [])
print(f"✓ Generated {len(files)} backend files")

ng_files = ng_gen.generate({"project_name": "quick-test"}, {}, [])
print(f"✓ Generated {len(ng_files)} frontend files")

print("\n✓✓✓ ALL BASIC FUNCTIONALITY WORKING ✓✓✓")
