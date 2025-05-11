from web3 import Web3
import os
import time
import traceback

class BlockchainClient:
    def __init__(self, contract_address, contract_abi):
        print("DEBUG: Initializing BlockchainClient")
        # Connect to Sepolia testnet via Infura
        self.infura_url = os.environ.get('INFURA_URL')
        if not self.infura_url or 'YOUR_INFURA_PROJECT_ID' in self.infura_url:
            raise ValueError("INFURA_URL environment variable not set or contains placeholder")
            
        print(f"DEBUG: Using Infura URL: {self.infura_url}")
        
        # Try connecting multiple times with backoff
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                self.w3 = Web3(Web3.HTTPProvider(self.infura_url))
                
                # Check connection
                connected = self.w3.is_connected()
                print(f"DEBUG: Connection to Ethereum network (attempt {attempt}/{max_retries}): {'SUCCESS' if connected else 'FAILED'}")
                
                if connected:
                    break
                    
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"DEBUG: Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            except Exception as e:
                print(f"DEBUG: Connection error on attempt {attempt}: {str(e)}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"DEBUG: Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        if not self.w3.is_connected():
            print("DEBUG: All connection attempts failed")
            raise ConnectionError("Failed to connect to Ethereum network after multiple attempts")
        
        # Load contract
        try:
            self.contract_address = Web3.to_checksum_address(contract_address)
            print(f"DEBUG: Using contract address: {self.contract_address}")
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=contract_abi)
            print("DEBUG: Contract loaded successfully")
        except Exception as e:
            print(f"DEBUG: Error loading contract: {str(e)}")
            traceback.print_exc()
            raise
        
        # Add connected status flag
        self.connected = True
        
        # Your Ethereum account (from environment variable for security)
        try:
            self.account_address = os.environ.get('ETH_ACCOUNT_ADDRESS')
            if not self.account_address:
                raise ValueError("ETH_ACCOUNT_ADDRESS environment variable not set")
                
            self.account_address = Web3.to_checksum_address(self.account_address)
            print(f"DEBUG: Using account address: {self.account_address}")
            
            self.private_key = os.environ.get('ETH_PRIVATE_KEY')
            if not self.private_key:
                raise ValueError("ETH_PRIVATE_KEY environment variable not set")
                
            print("DEBUG: Private key loaded (not showing for security)")
            
            # Verify account has ETH
            balance = self.w3.eth.get_balance(self.account_address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            print(f"DEBUG: Account balance: {balance_eth} ETH")
            
        except Exception as e:
            print(f"DEBUG: Error setting up account: {str(e)}")
            traceback.print_exc()
            raise
    
    def is_connected(self):
        """Check if connected to the Ethereum network"""
        if not hasattr(self, 'w3'):
            return False
        
        try:
            connected = self.w3.is_connected()
            return connected
        except Exception as e:
            print(f"DEBUG: Error checking connection: {str(e)}")
            return False
            
    def reconnect(self):
        """Attempt to reconnect to the Ethereum network"""
        try:
            print("DEBUG: Attempting to reconnect to Ethereum network...")
            self.w3 = Web3(Web3.HTTPProvider(self.infura_url))
            
            connected = self.w3.is_connected()
            self.connected = connected
            
            if connected:
                print("DEBUG: Successfully reconnected to Ethereum network")
                return True
            else:
                print("DEBUG: Failed to reconnect to Ethereum network")
                return False
        except Exception as e:
            print(f"DEBUG: Error during reconnection: {str(e)}")
            self.connected = False
            return False
    
    def register_chemical(self, rfid_tag, name, manufacturer):
        """Register a new chemical on the blockchain"""
        try:
            # Build transaction
            txn = self.contract.functions.registerChemical(
                rfid_tag, name, manufacturer
            ).build_transaction({
                'from': self.account_address,
                'nonce': self.w3.eth.get_transaction_count(self.account_address),
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(txn, private_key=self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'block_number': tx_receipt['blockNumber'],
                'contract_address': self.contract_address
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def record_movement(self, rfid_tag, location, moved_by, purpose, status):
        """Record a chemical movement on the blockchain"""
        try:
            # Build transaction
            txn = self.contract.functions.recordMovement(
                rfid_tag, location, moved_by or "", purpose or "", status or ""
            ).build_transaction({
                'from': self.account_address,
                'nonce': self.w3.eth.get_transaction_count(self.account_address),
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(txn, private_key=self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'block_number': tx_receipt['blockNumber'],
                'contract_address': self.contract_address
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def record_movement(self, rfid_tag, location, moved_by=None, purpose=None, status=None):
        """Record a chemical movement on the blockchain"""
        try:
            print(f"DEBUG: Recording movement for RFID tag: {rfid_tag}")
            
            # Check connection before proceeding
            if not self.w3.is_connected():
                print("DEBUG: Web3 connection lost, attempting to reconnect...")
                # Try to reconnect
                self.w3 = Web3(Web3.HTTPProvider(self.infura_url))
                if not self.w3.is_connected():
                    raise ConnectionError("Lost connection to Ethereum network and failed to reconnect")
                print("DEBUG: Successfully reconnected to Ethereum network")
                
                # Reload contract after reconnection
                self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.contract.abi)
            
            # Ensure all parameters are strings
            rfid_tag = str(rfid_tag)
            location = str(location)
            moved_by = str(moved_by or "")
            purpose = str(purpose or "")
            status = str(status or "")
            
            print(f"DEBUG: Parameters for recordMovement:")
            print(f"  - RFID Tag: {rfid_tag}")
            print(f"  - Location: {location}")
            print(f"  - Moved By: {moved_by}")
            print(f"  - Purpose: {purpose}")
            print(f"  - Status: {status}")
            
            # Estimate gas for the transaction
            try:
                gas_estimate = self.contract.functions.recordMovement(
                    rfid_tag,
                    location,
                    moved_by,
                    purpose,
                    status
                ).estimate_gas({
                    'from': self.account_address
                })
                print(f"DEBUG: Gas estimate: {gas_estimate}")
            except Exception as e:
                print(f"ERROR: Failed to estimate gas: {str(e)}")
                traceback.print_exc()
                raise
            
            # Add 10% buffer to gas estimate
            gas_limit = int(gas_estimate * 1.1)
            print(f"DEBUG: Gas limit with buffer: {gas_limit}")
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            print(f"DEBUG: Current gas price: {gas_price}")
            
            # Build transaction
            try:
                nonce = self.w3.eth.get_transaction_count(self.account_address)
                print(f"DEBUG: Current nonce: {nonce}")
                
                txn = self.contract.functions.recordMovement(
                    rfid_tag,
                    location,
                    moved_by,
                    purpose,
                    status
                ).build_transaction({
                    'from': self.account_address,
                    'nonce': nonce,
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                    'chainId': self.w3.eth.chain_id
                })
                print("DEBUG: Transaction built successfully")  # Simple string, no f-string needed
            except Exception as e:
                print(f"ERROR: Failed to build transaction: {str(e)}")
                traceback.print_exc()
                raise
            
            # Sign and send transaction
            try:
                signed_txn = self.w3.eth.account.sign_transaction(txn, private_key=self.private_key)
                print("DEBUG: Transaction signed successfully")
                
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                print(f"DEBUG: Transaction sent with hash: {tx_hash.hex()}")
                
                # Wait for transaction receipt
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                print(f"DEBUG: Transaction mined in block {tx_receipt['blockNumber']}")
                
                return {
                    'success': True,
                    'transaction_hash': tx_hash.hex(),
                    'block_number': tx_receipt['blockNumber'],
                    'contract_address': self.contract_address
                }
            except Exception as e:
                print(f"ERROR: Failed to send/mine transaction: {str(e)}")
                traceback.print_exc()
                raise
            
        except Exception as e:
            print(f"ERROR: Failed to record movement: {str(e)}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_movement_history(self, rfid_tag):
        """Get the complete movement history for a chemical from blockchain"""
        try:
            print(f"DEBUG: Getting movement history for RFID tag: {rfid_tag}")
            
            # Check connection before proceeding
            if not self.w3.is_connected():
                print("DEBUG: Web3 connection lost, attempting to reconnect...")
                # Try to reconnect
                self.w3 = Web3(Web3.HTTPProvider(self.infura_url))
                if not self.w3.is_connected():
                    raise ConnectionError("Lost connection to Ethereum network and failed to reconnect")
                print("DEBUG: Successfully reconnected to Ethereum network")
                
                # Reload contract after reconnection
                self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.contract.abi)
            
            # Get count of movement records
            print(f"DEBUG: Calling getMovementHistoryCount for {rfid_tag}")
            count = self.contract.functions.getMovementHistoryCount(rfid_tag).call()
            print(f"DEBUG: Found {count} movement records on blockchain")
            
            # Get all movement records
            history = []
            for i in range(count):
                print(f"DEBUG: Fetching movement record {i+1}/{count}")
                location, moved_by, purpose, status, timestamp = self.contract.functions.getMovementRecord(
                    rfid_tag, i
                ).call()
                
                print(f"DEBUG: Record {i+1}: location={location}, timestamp={timestamp}")
                
                history.append({
                    'location': location,
                    'moved_by': moved_by,
                    'purpose': purpose,
                    'status': status,
                    'timestamp': timestamp,
                    'blockchain_verified': True
                })
            
            print(f"DEBUG: Successfully retrieved {len(history)} records from blockchain")
            return {
                'success': True,
                'history': history
            }
        except Exception as e:
            print(f"DEBUG: Error getting movement history: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
