#!/usr/bin/env python3
"""
Final test script to verify auto-download functionality to C:\Users\Admin\Downloads\download_ai_project
"""
import requests
import time
import os

API_BASE = "http://localhost:8000/api/v1"

def test_auto_download():
    """Test the complete auto-download workflow"""
    print("🚀 Testing Auto-Download to C:\\Users\\Admin\\Downloads\\download_ai_project")
    print("=" * 70)

    # Step 1: Check API health
    print("\n📡 Step 1: Checking API health...")
    try:
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"❌ API health check failed: {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return

    # Step 2: Generate project
    print("\n🏗️  Step 2: Generating hotel-management-system project...")
    payload = {"project_name": "hotel-management-system"}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(f"{API_BASE}/generate", json=payload, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")

        if response.status_code == 202:
            data = response.json()
            job_id = data["job_id"]
            print(f"✅ Job created successfully with ID: {job_id}")

            # Step 3: Monitor progress
            print("\n⏳ Step 3: Monitoring generation progress...")
            start_time = time.time()
            max_wait = 600  # 10 minutes max

            while time.time() - start_time < max_wait:
                try:
                    job_response = requests.get(f"{API_BASE}/jobs/{job_id}", timeout=10)
                    job_data = job_response.json()

                    status = job_data["status"]
                    progress = job_data.get("progress", 0)
                    stage = job_data.get("current_stage", "unknown")

                    print(f"Status: {status} | Progress: {progress}% | Stage: {stage}")

                    if status == "completed":
                        print("\n🎉 SUCCESS: Project generation completed!")

                        # Check result data
                        result_data = job_data.get("result_data", {})
                        download_path = result_data.get("download_path")

                        if download_path:
                            print(f"📁 Reported download path: {download_path}")
                        else:
                            print("⚠️  No download_path in job result (but should still be downloaded)")

                        # Step 4: Verify file exists locally
                        print("\n🔍 Step 4: Checking local download directory...")
                        local_dir = r"C:\Users\Admin\Downloads\download_ai_project"

                        if os.path.exists(local_dir):
                            files = os.listdir(local_dir)
                            zip_files = [f for f in files if f.endswith('.zip')]

                            if zip_files:
                                print(f"✅ SUCCESS: Found {len(zip_files)} ZIP file(s) in {local_dir}:")
                                for zip_file in sorted(zip_files):
                                    file_path = os.path.join(local_dir, zip_file)
                                    file_size = os.path.getsize(file_path)
                                    print(f"   📦 {zip_file} ({file_size:,} bytes)")
                            else:
                                print(f"❌ No ZIP files found in {local_dir}")
                                print("   Directory contents:", files if files else "Empty")
                        else:
                            print(f"❌ Directory does not exist: {local_dir}")

                        print("\n" + "=" * 70)
                        print("🎯 AUTO-DOWNLOAD TEST COMPLETE!")
                        print("If you see ZIP files above, the feature is working perfectly!")
                        return

                    elif status == "failed":
                        error_msg = job_data.get("error", "Unknown error")
                        print(f"\n❌ Job failed: {error_msg}")
                        return

                except requests.exceptions.RequestException as e:
                    print(f"Error checking job status: {e}")

                time.sleep(3)  # Check every 3 seconds

            print(f"\n⏰ Timeout: Job did not complete within {max_wait/60:.1f} minutes")

        else:
            print(f"❌ Failed to create job: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_auto_download()