from app.services.generators.springboot_generator import SpringBootGenerator

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
print("All generated files:")
for filename in sorted(files.keys()):
    print(f"  • {filename}")
