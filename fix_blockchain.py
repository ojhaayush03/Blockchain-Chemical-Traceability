import os
import json
import time
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
eth_account = os.environ.get('ETH_ACCOUNT_ADDRESS')
eth_private_key = os.environ.get('ETH_PRIVATE_KEY')
contract_address = os.environ.get('ETH_CONTRACT_ADDRESS')
infura_url = os.environ.get('INFURA_URL')

print("=" * 50)
print("BLOCKCHAIN CONNECTION TEST")
print("=" * 50)
print(f"Account: {eth_account}")
print(f"Contract: {contract_address}")
print(f"Infura URL: {infura_url}")
print(f"Private Key: {'Set' if eth_private_key else 'Not set'}")
print("-" * 50)

# Test connection with retry logic
max_retries = 3
connected = False

for attempt in range(1, max_retries + 1):
    try:
        print(f"Connection attempt {attempt}/{max_retries}...")
        
        # Create Web3 instance with HTTP provider
        w3 = Web3(Web3.HTTPProvider(infura_url))
        
        # Check connection
        connected = w3.is_connected()
        print(f"Connection status: {'SUCCESS' if connected else 'FAILED'}")
        
        if connected:
            # Get network info
            chain_id = w3.eth.chain_id
            print(f"Chain ID: {chain_id}")
            
            # Check if we're on Sepolia (chain ID 11155111)
            if chain_id == 11155111:
                print("Successfully connected to Sepolia testnet!")
            else:
                print(f"WARNING: Connected to chain ID {chain_id}, but Sepolia should be 11155111")
            
            # Get current block
            block_number = w3.eth.block_number
            print(f"Current Block: {block_number}")
            
            # Check account balance
            if eth_account:
                balance = w3.eth.get_balance(eth_account)
                balance_eth = w3.from_wei(balance, 'ether')
                print(f"Account Balance: {balance_eth} ETH")
            
            # Test contract connection
            try:
                with open('app/contract_abi.json', 'r') as f:
                    contract_abi = json.load(f)
                print("Contract ABI loaded successfully")
                
                contract = w3.eth.contract(address=contract_address, abi=contract_abi)
                print(f"Contract loaded successfully at {contract_address}")
                
                # Try to call a contract function
                test_tag = "TEST-TAG-001"
                count = contract.functions.getMovementHistoryCount(test_tag).call()
                print(f"Contract function call successful!")
                print(f"Movement history count for '{test_tag}': {count}")
                
                # Everything is working!
                print("\nALL TESTS PASSED! Your blockchain connection is working correctly.")
                break
            except Exception as e:
                print(f"Error with contract: {str(e)}")
        else:
            print("Connection failed")
            
        if not connected and attempt < max_retries:
            wait_time = 2 ** attempt
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            
    except Exception as e:
        print(f"Error on attempt {attempt}: {str(e)}")
        if attempt < max_retries:
            wait_time = 2 ** attempt
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

if not connected:
    print("\nFAILED: Could not connect to Ethereum network after multiple attempts")
    print("\nTROUBLESHOOTING TIPS:")
    print("1. Check your INFURA_URL - make sure it's correct and the API key is valid")
    print("2. Check your internet connection")
    print("3. Verify that the Infura project has access to Sepolia testnet")
    print("4. Try using a different RPC provider (like Alchemy)")
