import os
import json
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
eth_account = os.environ.get('ETH_ACCOUNT_ADDRESS')
eth_private_key = os.environ.get('ETH_PRIVATE_KEY')
contract_address = os.environ.get('ETH_CONTRACT_ADDRESS')
infura_url = os.environ.get('INFURA_URL')

print(f"Environment variables loaded:")
print(f"  Account: {eth_account}")
print(f"  Contract: {contract_address}")
print(f"  Infura URL: {infura_url}")
print(f"  Private Key: {'Set' if eth_private_key else 'Not set'}")

# Connect to Ethereum
w3 = Web3(Web3.HTTPProvider(infura_url))
connected = w3.is_connected()
print(f"\nConnection to Ethereum: {'SUCCESS' if connected else 'FAILED'}")

if connected:
    # Get network info
    chain_id = w3.eth.chain_id
    block_number = w3.eth.block_number
    gas_price = w3.eth.gas_price
    
    print(f"Chain ID: {chain_id}")
    print(f"Current Block: {block_number}")
    print(f"Gas Price: {gas_price}")
    
    # Check account balance
    if eth_account:
        balance = w3.eth.get_balance(eth_account)
        balance_eth = w3.from_wei(balance, 'ether')
        print(f"\nAccount Balance: {balance_eth} ETH")
    
    # Load contract ABI
    try:
        with open('app/contract_abi.json', 'r') as f:
            contract_abi = json.load(f)
        print("\nContract ABI loaded successfully")
        
        # Load contract
        if contract_address:
            contract = w3.eth.contract(address=contract_address, abi=contract_abi)
            print(f"Contract loaded successfully at {contract_address}")
            
            # Try to call a contract function
            try:
                # Try to get the count of movement records for a test tag
                test_tag = "TEST-TAG-001"
                count = contract.functions.getMovementHistoryCount(test_tag).call()
                print(f"\nTest contract call successful!")
                print(f"Movement history count for '{test_tag}': {count}")
            except Exception as e:
                print(f"\nError calling contract function: {str(e)}")
    except Exception as e:
        print(f"\nError loading contract ABI: {str(e)}")
else:
    print("Cannot proceed with contract testing due to connection failure")
