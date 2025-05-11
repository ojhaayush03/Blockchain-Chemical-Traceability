import requests
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 50)
print("TESTING LOG EVENT ENDPOINT")
print("=" * 50)

# Print environment info
print("\nEnvironment Variables:")
print(f"INFURA_URL: {os.environ.get('INFURA_URL')}")
print(f"ETH_ACCOUNT_ADDRESS: {os.environ.get('ETH_ACCOUNT_ADDRESS')}")
print(f"ETH_CONTRACT_ADDRESS: {os.environ.get('ETH_CONTRACT_ADDRESS')}")
print(f"ETH_PRIVATE_KEY: {'Set' if os.environ.get('ETH_PRIVATE_KEY') else 'Not set'}")

# Test data
test_data = {
    "tag_id": "TEST-TAG-002",
    'location': 'Test Lab',
    'moved_by': 'Test User',
    'purpose': 'Testing',
    'status': 'In Transit'
}

print("\nTest Data:")
print(json.dumps(test_data, indent=2))

# Make request to the endpoint
try:
    print("\nMaking request to /log-event...")
    response = requests.post(
        'http://localhost:5000/log-event',
        json=test_data,
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print("\nResponse Headers:")
    for header, value in response.headers.items():
        print(f"{header}: {value}")
        
    print("\nResponse Body:")
    try:
        response_json = response.json()
        print(json.dumps(response_json, indent=2))
        
        # Additional error analysis
        if not response_json.get('blockchain_success', False):
            print("\nBlockchain Transaction Failed:")
            blockchain_error = response_json.get('blockchain', {}).get('error')
            if blockchain_error:
                print(f"Error: {blockchain_error}")
                
                if "no attribute 'record_movement'" in blockchain_error:
                    print("\nPossible Fix: The blockchain client needs to be restarted to pick up the new record_movement method.")
                elif "gas required exceeds allowance" in blockchain_error:
                    print("\nPossible Fix: Increase the gas limit or check account balance.")
    except Exception as e:
        print("Failed to parse JSON response:")
        print(response.text)
        print(f"Parse error: {str(e)}")
        
except requests.exceptions.ConnectionError:
    print("\nError: Could not connect to the server. Is Flask running?")
except Exception as e:
    print(f"\nError making request: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)
