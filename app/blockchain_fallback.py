import os
import time
from web3 import Web3

class BlockchainFallback:
    """A simplified blockchain client that gracefully handles connection failures"""
    
    def __init__(self, contract_address, contract_abi):
        self.contract_address = contract_address
        self.contract_abi = contract_abi
        self.infura_url = os.environ.get('INFURA_URL')
        self.account_address = os.environ.get('ETH_ACCOUNT_ADDRESS')
        self.private_key = os.environ.get('ETH_PRIVATE_KEY')
        
        # Initialize Web3 connection
        self.w3 = None
        self.contract = None
        self.connected = False
        
        # Try to connect
        self._connect()
    
    def _connect(self):
        """Attempt to connect to the Ethereum network with retry logic"""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Attempting to connect to Ethereum network (attempt {attempt}/{max_retries})...")
                self.w3 = Web3(Web3.HTTPProvider(self.infura_url))
                
                if self.w3.is_connected():
                    print("Successfully connected to Ethereum network")
                    self.connected = True
                    
                    # Get network info to verify connection
                    try:
                        chain_id = self.w3.eth.chain_id
                        block_number = self.w3.eth.block_number
                        print(f"Connected to chain ID: {chain_id}, current block: {block_number}")
                    except Exception as e:
                        print(f"Warning: Connected but couldn't get chain info: {str(e)}")
                    
                    # Load contract
                    if self.contract_address and self.contract_abi:
                        try:
                            self.contract_address = Web3.to_checksum_address(self.contract_address)
                            self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.contract_abi)
                            print(f"Contract loaded at {self.contract_address}")
                            
                            # Test contract connection with a simple call
                            try:
                                # Try a simple call to verify contract connection
                                test_tag = "TEST-TAG-001"
                                _ = self.contract.functions.getMovementHistoryCount(test_tag).call()
                                print("Contract connection verified with test call")
                            except Exception as contract_call_error:
                                print(f"Warning: Contract loaded but test call failed: {str(contract_call_error)}")
                        except Exception as e:
                            print(f"Error loading contract: {str(e)}")
                            self.contract = None
                    
                    # Connection successful, break out of retry loop
                    break
                else:
                    print(f"Failed to connect to Ethereum network on attempt {attempt}")
                    self.connected = False
                    
                    if attempt < max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
            except Exception as e:
                print(f"Error connecting to Ethereum network on attempt {attempt}: {str(e)}")
                self.connected = False
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
    
    def reconnect(self):
        """Attempt to reconnect to the Ethereum network with multiple retries"""
        print("Attempting to reconnect to the Ethereum network...")
        
        # Try multiple times with increasing backoff
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Reconnection attempt {attempt}/{max_retries}...")
                
                # Create a new Web3 instance
                self.w3 = Web3(Web3.HTTPProvider(self.infura_url))
                
                # Check connection
                if self.w3.is_connected():
                    print("Successfully reconnected to Ethereum network")
                    self.connected = True
                    
                    # Reload contract
                    if self.contract_address and self.contract_abi:
                        try:
                            self.contract_address = Web3.to_checksum_address(self.contract_address)
                            self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.contract_abi)
                            print(f"Contract reloaded at {self.contract_address}")
                            
                            # Verify contract connection
                            try:
                                # Simple call to verify contract
                                test_tag = "TEST-TAG-001"
                                _ = self.contract.functions.getMovementHistoryCount(test_tag).call()
                                print("Contract connection verified")
                            except Exception as e:
                                print(f"Warning: Contract loaded but test call failed: {str(e)}")
                        except Exception as e:
                            print(f"Error reloading contract: {str(e)}")
                            self.contract = None
                    
                    return True
                else:
                    print(f"Reconnection attempt {attempt} failed")
                    
                    if attempt < max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"Waiting {wait_time} seconds before next attempt...")
                        time.sleep(wait_time)
            except Exception as e:
                print(f"Error during reconnection attempt {attempt}: {str(e)}")
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"Waiting {wait_time} seconds before next attempt...")
                    time.sleep(wait_time)
        
        # All attempts failed
        print("All reconnection attempts failed")
        self.connected = False
        return False
    
    def is_connected(self):
        """Check if connected to the Ethereum network"""
        if not self.w3:
            return False
        
        try:
            connected = self.w3.is_connected()
            if not connected:
                # Connection lost, try to reconnect
                return self.reconnect()
            return True
        except Exception:
            return False
    
    def register_chemical(self, rfid_tag, name, manufacturer):
        """Register a new chemical on the blockchain with fallback"""
        if not self.is_connected() or not self.contract:
            return {
                'success': False,
                'error': 'Blockchain connection unavailable',
                'fallback': True
            }
        
        try:
            # Build transaction
            tx = self.contract.functions.registerChemical(
                rfid_tag, name, manufacturer
            ).build_transaction({
                'from': self.account_address,
                'nonce': self.w3.eth.get_transaction_count(self.account_address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'block_number': receipt.blockNumber
            }
        except Exception as e:
            print(f"Error registering chemical on blockchain: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback': True
            }
    
    def record_movement(self, rfid_tag, location, moved_by, purpose, status):
        """Record a movement on the blockchain with fallback"""
        if not self.is_connected() or not self.contract:
            print("Cannot record movement: blockchain connection unavailable")
            return {
                'success': False,
                'error': 'Blockchain network connection unavailable',
                'fallback': True
            }
        
        try:
            # Verify connection before proceeding
            if not self.w3.is_connected():
                print("Connection lost before recording movement, attempting to reconnect...")
                if not self.reconnect():
                    return {
                        'success': False,
                        'error': 'Blockchain network connection unavailable',
                        'fallback': True
                    }
            
            # Ensure we have the latest nonce
            nonce = self.w3.eth.get_transaction_count(self.account_address)
            print(f"Using nonce: {nonce} for transaction")
            
            # Get current gas price with a slight increase for faster confirmation
            gas_price = int(self.w3.eth.gas_price * 1.1)  # 10% higher than current gas price
            print(f"Using gas price: {gas_price} wei")
            
            # Try to estimate gas (this will also validate if the transaction can succeed)
            try:
                estimated_gas = self.contract.functions.recordMovement(
                    rfid_tag, location, moved_by, purpose, status
                ).estimate_gas({'from': self.account_address})
                print(f"Estimated gas: {estimated_gas}")
                
                # Add 10% buffer to estimated gas
                gas_limit = int(estimated_gas * 1.1)
            except Exception as gas_error:
                print(f"Gas estimation failed: {str(gas_error)}. Using default gas limit.")
                gas_limit = 300000  # Higher default gas limit
            
            print(f"Building transaction with gas limit: {gas_limit}")
            
            # Build transaction with optimized parameters
            tx = self.contract.functions.recordMovement(
                rfid_tag, location, moved_by, purpose, status
            ).build_transaction({
                'from': self.account_address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id  # Explicitly set chain ID for better reliability
            })
            
            # Sign and send transaction
            print("Signing transaction...")
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            
            print("Sending transaction to network...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction sent with hash: {tx_hash.hex()}")
            
            # Wait for transaction receipt with longer timeout
            print("Waiting for transaction confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            print(f"Transaction confirmed in block {receipt.blockNumber}")
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'block_number': receipt.blockNumber
            }
        except Exception as e:
            print(f"Error recording movement on blockchain: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'fallback': True
            }
    
    def get_movement_history(self, rfid_tag):
        """Get the movement history from blockchain with fallback"""
        if not self.is_connected() or not self.contract:
            return {
                'success': False,
                'error': 'Blockchain connection unavailable',
                'fallback': True
            }
        
        try:
            # Get count of movement records
            count = self.contract.functions.getMovementHistoryCount(rfid_tag).call()
            
            # Get all movement records
            history = []
            for i in range(count):
                location, moved_by, purpose, status, timestamp = self.contract.functions.getMovementRecord(
                    rfid_tag, i
                ).call()
                
                history.append({
                    'location': location,
                    'moved_by': moved_by,
                    'purpose': purpose,
                    'status': status,
                    'timestamp': timestamp,
                    'blockchain_verified': True
                })
            
            return {
                'success': True,
                'history': history
            }
        except Exception as e:
            print(f"Error getting movement history: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback': True
            }
    
    def get_status(self):
        """Get the current status of the blockchain connection"""
        connected = self.is_connected()
        
        status = {
            'connected': connected,
            'contract_loaded': self.contract is not None,
            'account_address': self.account_address,
            'contract_address': self.contract_address,
        }
        
        if connected and self.w3:
            try:
                status['chain_id'] = self.w3.eth.chain_id
                status['block_number'] = self.w3.eth.block_number
                
                if self.account_address:
                    balance = self.w3.eth.get_balance(self.account_address)
                    status['balance'] = self.w3.from_wei(balance, 'ether')
            except Exception as e:
                print(f"Error getting blockchain status: {str(e)}")
        
        return status
