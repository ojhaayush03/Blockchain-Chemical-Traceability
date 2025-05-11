import os
import sys
import json
import traceback
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
load_dotenv()

print("=" * 50)
print("BLOCKCHAIN CLIENT DIAGNOSTIC TOOL")
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

# Check if all required environment variables are set
missing_vars = []
if not eth_account:
    missing_vars.append("ETH_ACCOUNT_ADDRESS")
if not eth_private_key:
    missing_vars.append("ETH_PRIVATE_KEY")
if not contract_address:
    missing_vars.append("ETH_CONTRACT_ADDRESS")
if not infura_url:
    missing_vars.append("INFURA_URL")

if missing_vars:
    print(f"ERROR: Missing environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Load contract ABI
try:
    with open('app/contract_abi.json', 'r') as f:
        contract_abi = json.load(f)
    print("Contract ABI loaded successfully")
except Exception as e:
    print(f"ERROR: Failed to load contract ABI: {str(e)}")
    sys.exit(1)

# Test direct Web3 connection
print("\nTesting direct Web3 connection...")
try:
    w3 = Web3(Web3.HTTPProvider(infura_url))
    
    if w3.is_connected():
        print("✅ Successfully connected to Ethereum network")
        
        # Get network info
        chain_id = w3.eth.chain_id
        block_number = w3.eth.block_number
        print(f"Chain ID: {chain_id}")
        print(f"Current Block: {block_number}")
        
        # Check account balance
        balance = w3.eth.get_balance(eth_account)
        balance_eth = w3.from_wei(balance, 'ether')
        print(f"Account Balance: {balance_eth} ETH")
    else:
        print("❌ Failed to connect to Ethereum network")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error connecting to Ethereum network: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

# Test contract connection
print("\nTesting contract connection...")
try:
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    print(f"✅ Contract loaded at {contract_address}")
    
    # Try to call a contract function
    test_tag = "TEST-TAG-001"
    try:
        count = contract.functions.getMovementHistoryCount(test_tag).call()
        print(f"✅ Contract function call successful!")
        print(f"Movement history count for '{test_tag}': {count}")
    except Exception as e:
        print(f"❌ Error calling contract function: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
except Exception as e:
    print(f"❌ Error loading contract: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

# Test both blockchain client implementations
print("\nTesting BlockchainClient implementation...")
try:
    from app.blockchain_client import BlockchainClient
    
    client = BlockchainClient(contract_address, contract_abi)
    if hasattr(client, 'w3') and client.w3.is_connected():
        print("✅ BlockchainClient initialized and connected")
        
        # Test register_chemical method
        if hasattr(client, 'register_chemical'):
            print("✅ register_chemical method exists")
        else:
            print("❌ register_chemical method does not exist")
        
        # Test record_movement method
        if hasattr(client, 'record_movement'):
            print("✅ record_movement method exists")
        else:
            print("❌ record_movement method does not exist")
    else:
        print("❌ BlockchainClient failed to connect")
except Exception as e:
    print(f"❌ Error initializing BlockchainClient: {str(e)}")
    traceback.print_exc()

print("\nTesting BlockchainFallback implementation...")
try:
    from app.blockchain_fallback import BlockchainFallback
    
    client = BlockchainFallback(contract_address, contract_abi)
    if hasattr(client, 'w3') and client.w3.is_connected():
        print("✅ BlockchainFallback initialized and connected")
        
        # Test register_chemical method
        if hasattr(client, 'register_chemical'):
            print("✅ register_chemical method exists")
        else:
            print("❌ register_chemical method does not exist")
        
        # Test record_movement method
        if hasattr(client, 'record_movement'):
            print("✅ record_movement method exists")
        else:
            print("❌ record_movement method does not exist")
    else:
        print("❌ BlockchainFallback failed to connect")
except Exception as e:
    print(f"❌ Error initializing BlockchainFallback: {str(e)}")
    traceback.print_exc()

# Test the application's blockchain client initialization
print("\nTesting application's blockchain client initialization...")
try:
    from app import create_app
    
    app = create_app()
    with app.app_context():
        from app import blockchain_client
        
        if blockchain_client is None:
            print("❌ blockchain_client is None")
        else:
            print(f"✅ blockchain_client is initialized as: {type(blockchain_client).__name__}")
            
            if hasattr(blockchain_client, 'w3') and blockchain_client.w3.is_connected():
                print("✅ blockchain_client is connected to Ethereum network")
            else:
                print("❌ blockchain_client is not connected to Ethereum network")
            
            # Test register_chemical method
            if hasattr(blockchain_client, 'register_chemical'):
                print("✅ register_chemical method exists")
            else:
                print("❌ register_chemical method does not exist")
            
            # Test record_movement method
            if hasattr(blockchain_client, 'record_movement'):
                print("✅ record_movement method exists")
            else:
                print("❌ record_movement method does not exist")
except Exception as e:
    print(f"❌ Error testing application's blockchain client: {str(e)}")
    traceback.print_exc()

print("\n" + "=" * 50)
print("DIAGNOSTIC COMPLETE")
print("=" * 50)
