#!/usr/bin/env python3
"""
Test script to generate a hotel-management-system project and verify auto-download
"""
import requests
import time
import json
import os

API_BASE = "http://localhost:8000/api/v1"

def test_generate_project():
    """Test project generation and auto-download"""
    print("🚀 Testing auto-download functionality...")

    # Step 1: Generate project
    print("\n📝 Step 1: Generating hotel-management-system project...")
    payload = {"project_name": "hotel-management-system"}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(f"{API_BASE}/generate", json=payload, headers=headers)
        print(f"Response status: {response.status_code}")

        if response.status_code == 202:
            data = response.json()
            job_id = data["job_id"]
            print(f"✅ Job created with ID: {job_id}")

            # Step 2: Poll job status
            print("\n⏳ Step 2: Monitoring job progress...")
            while True:
                job_response = requests.get(f"{API_BASE}/jobs/{job_id}")
                job_data = job_response.json()

                status = job_data["status"]
                progress = job_data.get("progress", 0)
                stage = job_data.get("current_stage", "unknown")

                print(f"Status: {status} | Progress: {progress}% | Stage: {stage}")

                if status == "completed":
                    print("✅ Job completed successfully!")

                    # Check if download_path is in result_data
                    result_data = job_data.get("result_data", {})
                    download_path = result_data.get("download_path")
                    if download_path:
                        print(f"📁 Auto-download path: {download_path}")
                    else:
                        print("⚠️  No download_path found in job result")

                    # Step 3: Check local directory
                    print("\n🔍 Step 3: Checking local download directory...")
                    local_dir = r"C:\Users\Admin\Downloads\download_ai_project"
                    if os.path.exists(local_dir):
                        files = os.listdir(local_dir)
                        zip_files = [f for f in files if f.endswith('.zip')]
                        print(f"📂 Found {len(zip_files)} ZIP files in {local_dir}:")
                        for zip_file in zip_files:
                            print(f"   - {zip_file}")
                    else:
                        print(f"❌ Directory {local_dir} does not exist")

                    break
                elif status == "failed":
                    print(f"❌ Job failed: {job_data.get('error', 'Unknown error')}")
                    break

                time.sleep(5)  # Wait 5 seconds before checking again

        else:
            print(f"❌ Failed to create job: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_generate_project()