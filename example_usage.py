#!/usr/bin/env python3
"""
Example Usage of the Free Fire JWT & MajorLogin API with Random Device Selection.

This script demonstrates:
  1. Inspecting the 56 authentic real devices pool and filtering by brand/model.
  2. How devices are randomly selected on every request.
  3. Making MajorLogin requests using a randomly selected device.
  4. Filtering random selection by brand (e.g., 'Samsung', 'Xiaomi', 'OnePlus').
  5. Forcing a specific device model (e.g., 'Pixel 8 Pro' or 'SM-S928B').
  6. Using the API endpoints (/token, /majorlogin, /devices, /usage).
"""

import json
import devices
import app

def separator(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)

def example_1_device_catalog():
    separator("EXAMPLE 1: Inspecting the Real Devices Pool")
    total = len(devices.REAL_ANDROID_DEVICES)
    brands = sorted(list(set(d["brand"] for d in devices.REAL_ANDROID_DEVICES)))
    print(f"Total Authentic Real Devices Loaded: {total}")
    print(f"Supported Brands ({len(brands)}): {', '.join(brands)}")
    
    # Show 3 sample device profiles
    print("\nSample Device Profiles in the Pool:")
    for sample in devices.REAL_ANDROID_DEVICES[:3]:
        print(f"  • [{sample['brand']}] {sample.get('marketing_name', sample['model'])} ({sample['model']})")
        print(f"    - OS     : {sample['system_software']}")
        print(f"    - Screen : {sample['screen_width']}x{sample['screen_height']} ({sample['screen_dpi']} dpi)")
        print(f"    - CPU    : {sample['processor_details']} | RAM: {sample['memory']} MB")
        print(f"    - GPU    : {sample['gpu_renderer']} ({sample['opengl']})")
        print(f"    - Network: {sample.get('carrier', 'WIFI')} ({sample.get('network', '4G')})")
        print()

def example_2_random_device_selection():
    separator("EXAMPLE 2: Random Device Selection in Action")
    print("Selecting 5 random devices consecutively (showing model, GPU, and generated IP):\n")
    for i in range(1, 6):
        dev = devices.get_random_device()
        print(f"  Selection #{i}: {dev['brand']} {dev['model']} (Marketing: {dev.get('marketing_name', 'N/A')})")
        print(f"    - GPU      : {dev['gpu_renderer']}")
        print(f"    - Client IP: {dev['client_ip']}")
        print(f"    - Google ID: {dev['unique_device_id']}")
        print()

def example_3_brand_filtered_random_selection():
    separator("EXAMPLE 3: Random Selection Filtered by Brand")
    target_brand = "Samsung"
    print(f"Randomly selecting 3 devices from brand '{target_brand}':\n")
    for i in range(1, 4):
        dev = devices.get_random_device(brand=target_brand)
        print(f"  Samsung Pick #{i}: {dev['model']} - {dev.get('marketing_name', 'N/A')}")
        print(f"    - CPU: {dev['processor_details']} | RAM: {dev['memory']} MB")
        print(f"    - OS : {dev['system_software']}")
        print()

def example_4_flask_test_client_usage():
    separator("EXAMPLE 4: Calling API Endpoints via Flask Client")
    client = app.app.test_client()

    # 1. GET /usage
    print("1. Querying /usage endpoint:")
    usage_resp = client.get("/usage")
    usage_data = usage_resp.get_json()
    print(f"   Service: {usage_data.get('service')} (v{usage_data.get('version')})")
    print(f"   Selection Mode: {usage_data.get('devices', {}).get('selection_mode')}")
    print(f"   Available Endpoints: {list(usage_data.get('endpoints', {}).keys())}")

    # 2. GET /devices with filter
    print("\n2. Querying /devices?brand=Xiaomi:")
    dev_resp = client.get("/devices?brand=Xiaomi")
    dev_data = dev_resp.get_json()
    print(f"   Found {dev_data.get('total')} Xiaomi devices in pool:")
    for d in dev_data.get("devices", [])[:3]:
        print(f"     - {d['model']} ({d.get('marketing_name')})")

    # 3. GET /majorlogin with specific device model parameter
    print("\n3. Calling /majorlogin with ?model=Pixel+8+Pro:")
    # We demonstrate how passing access_token & open_id picks that device
    # Here we show parameter resolution
    print("   Endpoint accepts:")
    print("     - URL Query: /majorlogin?access_token=AT&open_id=OI&model=Pixel+8+Pro")
    print("     - JSON Body: POST /majorlogin with {'access_token': 'AT', 'open_id': 'OI', 'brand': 'OnePlus'}")
    print("     - URL Query: /token?uid=UID&password=PASS (auto-retrieves OAuth, then MajorLogin)")

def example_5_curl_commands():
    separator("EXAMPLE 5: Ready-to-Run cURL Commands")
    print("""
# 1. Full Login with UID and Password (random real device):
curl -s 'http://localhost:5000/token?uid=YOUR_UID&password=YOUR_PASSWORD'

# 2. Full Login via POST JSON:
curl -s -X POST 'http://localhost:5000/token' \\
     -H 'Content-Type: application/json' \\
     -d '{"uid": "YOUR_UID", "password": "YOUR_PASSWORD"}'

# 3. MajorLogin with specific device model override (e.g. Galaxy S24 Ultra):
curl -s 'http://localhost:5000/majorlogin?access_token=AT&open_id=OI&model=SM-S928B'

# 4. MajorLogin with random device from a specific brand (e.g. OnePlus):
curl -s 'http://localhost:5000/majorlogin?access_token=AT&open_id=OI&brand=OnePlus'

# 5. List all 56 authentic real devices:
curl -s 'http://localhost:5000/devices'

# 6. View API interactive usage documentation:
curl -s 'http://localhost:5000/usage'
""")

if __name__ == "__main__":
    example_1_device_catalog()
    example_2_random_device_selection()
    example_3_brand_filtered_random_selection()
    example_4_flask_test_client_usage()
    example_5_curl_commands()
    print("=" * 65)
    print(" All examples executed successfully!")
    print("=" * 65 + "\n")
