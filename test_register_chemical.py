import os
import json
import requests

print("==================================================")
print("TESTING CHEMICAL REGISTRATION ENDPOINT")
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
    "rfid_tag": "TEST-TAG-002",
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

print("\nMaking request to /register-chemical...")

# Make request to register chemical
response = requests.post(
    'http://localhost:5000/register-chemical',
    json=test_data
)

print(f"\nStatus Code: {response.status_code}\n")

print("Response Headers:")
for header, value in response.headers.items():
    print(f"{header}: {value}")

print("\nResponse Body:")
try:
    formatted_response = json.dumps(response.json(), indent=2)
    print(formatted_response)
    
    # Check if blockchain registration was successful
    if 'blockchain' in response.json():
        blockchain_result = response.json()['blockchain']
        if blockchain_result.get('success', False):
            print("\nBlockchain Registration Successful:")
            print(f"Transaction Hash: {blockchain_result.get('transaction_hash')}")
            print(f"Block Number: {blockchain_result.get('block_number')}")
        else:
            print("\nBlockchain Registration Failed:")
            print(f"Error: {blockchain_result.get('error', 'Unknown error')}")
            print("\nPossible Fix: Make sure the blockchain client is properly configured and connected.")
    else:
        print("\nNo blockchain result in response. Chemical was only registered in local database.")
except json.JSONDecodeError:
    print("Error: Could not parse JSON response")
    print(response.text)

print("\n==================================================")
print("TEST COMPLETE")
print("==================================================")
