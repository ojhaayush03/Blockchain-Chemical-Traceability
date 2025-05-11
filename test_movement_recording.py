import os
import time
from dotenv import load_dotenv
from web3 import Web3
import json
import traceback

# Load environment variables
load_dotenv()

print("=" * 50)
print("BLOCKCHAIN MOVEMENT RECORDING TEST")
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
    print(f"Error loading contract ABI: {str(e)}")
    exit(1)

# Connect to Ethereum
try:
    print("Connecting to Ethereum network...")
    w3 = Web3(Web3.HTTPProvider(infura_url))
    
    if w3.is_connected():
        print("Successfully connected to Ethereum network")
        
        # Get network info
        chain_id = w3.eth.chain_id
        block_number = w3.eth.block_number
        print(f"Chain ID: {chain_id}")
        print(f"Current Block: {block_number}")
        
        # Check account balance
        balance = w3.eth.get_balance(eth_account)
        balance_eth = w3.from_wei(balance, 'ether')
        print(f"Account Balance: {balance_eth} ETH")
        
        # Load contract
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        print(f"Contract loaded at {contract_address}")
        
        # Test RFID tag
        test_tag = "TEST-TAG-" + str(int(time.time()))
        print(f"Using test RFID tag: {test_tag}")
        
        # First register the chemical
        try:
            print("\nSTEP 1: Registering test chemical...")
            
            # Get nonce
            nonce = w3.eth.get_transaction_count(eth_account)
            print(f"Using nonce: {nonce}")
            
            # Build transaction
            tx = contract.functions.registerChemical(
                test_tag, 
                "Test Chemical", 
                "Test Manufacturer"
            ).build_transaction({
                'from': eth_account,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
                'chainId': chain_id
            })
            
            # Sign and send transaction
            print("Signing transaction...")
            signed_tx = w3.eth.account.sign_transaction(tx, eth_private_key)
            
            print("Sending transaction...")
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction hash: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            print("Waiting for confirmation...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            print(f"Transaction confirmed in block {receipt.blockNumber}")
            print("Chemical registered successfully!")
            
            # Now record a movement
            print("\nSTEP 2: Recording movement...")
            
            # Get new nonce
            nonce = w3.eth.get_transaction_count(eth_account)
            print(f"Using nonce: {nonce}")
            
            # Build transaction
            tx = contract.functions.recordMovement(
                test_tag,
                "Test Location",
                "Test User",
                "Test Purpose",
                "In Transit"
            ).build_transaction({
                'from': eth_account,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
                'chainId': chain_id
            })
            
            # Sign and send transaction
            print("Signing transaction...")
            signed_tx = w3.eth.account.sign_transaction(tx, eth_private_key)
            
            print("Sending transaction...")
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction hash: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            print("Waiting for confirmation...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            print(f"Transaction confirmed in block {receipt.blockNumber}")
            print("Movement recorded successfully!")
            
            # Verify movement history
            print("\nSTEP 3: Verifying movement history...")
            count = contract.functions.getMovementHistoryCount(test_tag).call()
            print(f"Movement history count: {count}")
            
            if count > 0:
                print("\nMovement history:")
                for i in range(count):
                    location, moved_by, purpose, status, timestamp = contract.functions.getMovementRecord(
                        test_tag, i
                    ).call()
                    
                    print(f"Record {i+1}:")
                    print(f"  Location: {location}")
                    print(f"  Moved by: {moved_by}")
                    print(f"  Purpose: {purpose}")
                    print(f"  Status: {status}")
                    print(f"  Timestamp: {timestamp}")
                
                print("\nTEST PASSED! Movement recording and verification are working correctly.")
            else:
                print("\nTEST FAILED! No movement records found for the test tag.")
            
        except Exception as e:
            print(f"\nError during test: {str(e)}")
            traceback.print_exc()
    else:
        print("Failed to connect to Ethereum network")
except Exception as e:
    print(f"Error: {str(e)}")
    traceback.print_exc()
