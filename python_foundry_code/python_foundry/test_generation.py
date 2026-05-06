import subprocess
import json
import time

# Test generation request using curl via subprocess
curl_cmd = [
    'curl', '-X', 'POST', 'http://localhost:8000/api/v1/generate',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps({
        "project_name": "hotel-management-system",
        "prompt": "Generate a production-ready hotel management system with Spring Boot backend and Angular frontend, including authentication, role-based access, dashboard, CRUD modules for rooms, bookings, guests, and staff management, Docker support, tests, and README.",
        "backend": "springboot",
        "frontend": "angular",
        "features": ["authentication", "role-based-access", "dashboard", "crud-rooms", "crud-bookings", "crud-guests", "crud-staff"],
        "mode_preference": "generate"
    })
]

print("Making generation request...")
result = subprocess.run(curl_cmd, capture_output=True, text=True)
print(f"Status: {result.returncode}")
print(f"Response: {result.stdout}")
if result.stderr:
    print(f"Error: {result.stderr}")

if result.returncode == 0:
    try:
        response_data = json.loads(result.stdout)
        if response_data.get("job_id"):
            job_id = response_data["job_id"]
            print(f"Job ID: {job_id}")

            # Poll job status
            for i in range(60):  # 5 minutes max
                job_curl = ['curl', '-s', f'http://localhost:8000/api/v1/jobs/{job_id}']
                job_result = subprocess.run(job_curl, capture_output=True, text=True)
                if job_result.returncode == 0:
                    job_data = json.loads(job_result.stdout)
                    print(f"Job status: {job_data['status']}, progress: {job_data['progress']}%")

                    if job_data["status"] == "completed":
                        project_id = job_data["result_data"]["project_id"]
                        print(f"Project ID: {project_id}")

                        # Try download
                        download_curl = ['curl', '-s', '-o', 'hotel-management-system.zip', f'http://localhost:8000/api/v1/projects/{project_id}/download']
                        download_result = subprocess.run(download_curl, capture_output=True, text=True)
                        if download_result.returncode == 0:
                            print("Project downloaded successfully!")
                        else:
                            print(f"Download failed: {download_result.stderr}")
                        break
                    elif job_data["status"] == "failed":
                        print(f"Job failed: {job_data}")
                        break

                time.sleep(5)

            if i >= 59:
                print("Timeout: Job did not complete within 5 minutes")
    except json.JSONDecodeError as e:
        print(f"Failed to parse response: {e}")
else:
    print("Request failed")