import subprocess
import sys

print("Running pytest on tests/test_generate.py...\n")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/test_generate.py", "-v", "--tb=short"],
    timeout=120
)
sys.exit(result.returncode)
