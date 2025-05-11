import os
import sys
import json
import traceback
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
load_dotenv()

print("=" * 50)
print("RECORD MOVEMENT TEST")
print("=" * 50)

# Get environment variables
eth_account = os.environ.get('ETH_ACCOUNT_ADDRESS')
eth_private_key = os.environ.get('ETH_PRIVATE_KEY')
contract_address = os.environ.get('ETH_CONTRACT_ADDRESS')
infura_url = os.environ.get('INFURA_URL')

print(f"Account: {eth_account}")
print(f"Contract: {contract_address}")
print(f"Infura URL: {infura_url}")
print(f"Private Key: {'Set' if eth_private_key else 'Not set'}")
print("-" * 50)

# Load contract ABI
try:
    with open('app/contract_abi.json', 'r') as f:
        contract_abi = json.load(f)
    print("Contract ABI loaded successfully")
except Exception as e:
    print(f"ERROR: Failed to load contract ABI: {str(e)}")
    sys.exit(1)

# Test BlockchainClient
print("\nTesting BlockchainClient.record_movement...")
try:
    from app.blockchain_client import BlockchainClient
    
    client = BlockchainClient(contract_address, contract_abi)
    
    # Test record_movement method
    if hasattr(client, 'record_movement'):
        print("✅ record_movement method exists")
        
        # Test with sample data
        test_tag = "TEST-TAG-DEBUG"
        test_location = "Test Location"
        test_moved_by = "Test User"
        test_purpose = "Testing"
        test_status = "In Transit"
        
        print(f"Calling record_movement with tag: {test_tag}")
        
        try:
            result = client.record_movement(
                test_tag,
                test_location,
                test_moved_by,
                test_purpose,
                test_status
            )
            
            print("✅ record_movement call successful")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Error calling record_movement: {str(e)}")
            traceback.print_exc()
    else:
        print("❌ record_movement method does not exist")
except Exception as e:
    print(f"❌ Error initializing BlockchainClient: {str(e)}")
    traceback.print_exc()

# Test BlockchainFallback
print("\nTesting BlockchainFallback.record_movement...")
try:
    from app.blockchain_fallback import BlockchainFallback
    
    client = BlockchainFallback(contract_address, contract_abi)
    
    # Test record_movement method
    if hasattr(client, 'record_movement'):
        print("✅ record_movement method exists")
        
        # Test with sample data
        test_tag = "TEST-TAG-DEBUG"
        test_location = "Test Location"
        test_moved_by = "Test User"
        test_purpose = "Testing"
        test_status = "In Transit"
        
        print(f"Calling record_movement with tag: {test_tag}")
        
        try:
            result = client.record_movement(
                test_tag,
                test_location,
                test_moved_by,
                test_purpose,
                test_status
            )
            
            print("✅ record_movement call successful")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Error calling record_movement: {str(e)}")
            traceback.print_exc()
    else:
        print("❌ record_movement method does not exist")
except Exception as e:
    print(f"❌ Error initializing BlockchainFallback: {str(e)}")
    traceback.print_exc()

# Test the application's blockchain client
print("\nTesting application's blockchain client record_movement...")
try:
    from app import create_app
    
    app = create_app()
    with app.app_context():
        from app import blockchain_client
        
        if blockchain_client is None:
            print("❌ blockchain_client is None")
        else:
            print(f"✅ blockchain_client is initialized as: {type(blockchain_client).__name__}")
            
            # Test record_movement method
            if hasattr(blockchain_client, 'record_movement'):
                print("✅ record_movement method exists")
                
                # Test with sample data
                test_tag = "TEST-TAG-DEBUG"
                test_location = "Test Location"
                test_moved_by = "Test User"
                test_purpose = "Testing"
                test_status = "In Transit"
                
                print(f"Calling record_movement with tag: {test_tag}")
                
                try:
                    result = blockchain_client.record_movement(
                        test_tag,
                        test_location,
                        test_moved_by,
                        test_purpose,
                        test_status
                    )
                    
                    print("✅ record_movement call successful")
                    print(f"Result: {result}")
                except Exception as e:
                    print(f"❌ Error calling record_movement: {str(e)}")
                    traceback.print_exc()
            else:
                print("❌ record_movement method does not exist")
except Exception as e:
    print(f"❌ Error testing application's blockchain client: {str(e)}")
    traceback.print_exc()

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)
