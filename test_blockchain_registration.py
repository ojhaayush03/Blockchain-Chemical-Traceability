import os
import json
import time
import requests

print("==================================================")
print("TESTING BLOCKCHAIN REGISTRATION VERIFICATION")
print("==================================================")

# Print environment variables (without private key)
print("\nEnvironment Variables:")
print(f"INFURA_URL: {os.environ.get('INFURA_URL')}")
print(f"ETH_ACCOUNT_ADDRESS: {os.environ.get('ETH_ACCOUNT_ADDRESS')}")
print(f"ETH_CONTRACT_ADDRESS: {os.environ.get('ETH_CONTRACT_ADDRESS')}")
print(f"ETH_PRIVATE_KEY: {'Set' if os.environ.get('ETH_PRIVATE_KEY') else 'Not Set'}")

# Test data
test_data = {
    "name": "Test Chemical",
    "rfid_tag": "TEST-TAG-004",  # Using a new tag
    "manufacturer": "Test Manufacturer",
    "current_location": "Test Lab",
    "quantity": 100.0,
    "unit": "mL",
    "expiry_date": "2026-12-31",
    "storage_condition": "Room Temperature",
    "received_date": "2025-05-11",
    "batch_number": "BATCH-001",
    "hazard_class": "Class 3 - Flammable",
    "cas_number": None,
    "description": "Test chemical for blockchain integration testing"
}

print("\nTest Data:")
print(json.dumps(test_data, indent=2))

print("\nStep 1: Registering chemical...")
# Register chemical
response = requests.post(
    'http://localhost:5000/register-chemical',
    json=test_data
)

print(f"\nRegistration Status Code: {response.status_code}")
print("\nRegistration Response:")
try:
    formatted_response = json.dumps(response.json(), indent=2)
    print(formatted_response)
except json.JSONDecodeError:
    print("Error: Could not parse JSON response")
    print(response.text)

print("\nStep 2: Waiting for transaction confirmation (15 seconds)...")
time.sleep(15)  # Wait for transaction to be confirmed

print("\nStep 3: Verifying blockchain registration...")
# Verify blockchain registration
verify_response = requests.get(
    f'http://localhost:5000/blockchain-verification/{test_data["rfid_tag"]}'
)

print(f"\nVerification Status Code: {verify_response.status_code}")
print("\nVerification Response:")
try:
    formatted_response = json.dumps(verify_response.json(), indent=2)
    print(formatted_response)
except json.JSONDecodeError:
    print("Error: Could not parse JSON response")
    print(verify_response.text)

print("\n==================================================")
print("TEST COMPLETE")
print("==================================================")
