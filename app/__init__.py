from flask import Flask
from app.extensions import db, login_manager, csrf
from app.routes import dashboard_bp, main, auth_bp, admin_bp, distributor_bp, customer_bp  # <-- Import all blueprints from the `routes` package
import os
import json
import traceback
import time
from web3 import Web3

# Initialize Flask application factory

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chemicals.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Set a secret key for session management
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Initialize logger
    import logging
    app.logger.setLevel(logging.DEBUG)

    # Initialize blockchain client attribute
    app.blockchain_client = None

    # Initialize blockchain client if environment variables are set
    if os.environ.get('ETH_CONTRACT_ADDRESS') and os.environ.get('ETH_ACCOUNT_ADDRESS') and os.environ.get('INFURA_URL'):
        print("Found blockchain environment variables:")
        print(f"  - ETH_CONTRACT_ADDRESS: {os.environ.get('ETH_CONTRACT_ADDRESS')}")
        print(f"  - ETH_ACCOUNT_ADDRESS: {os.environ.get('ETH_ACCOUNT_ADDRESS')}")
        print(f"  - INFURA_URL: {os.environ.get('INFURA_URL')}")
        
        # Load contract ABI from file
        contract_abi_path = os.path.join(app.root_path, 'contract_abi.json')
        if os.path.exists(contract_abi_path):
            try:
                with open(contract_abi_path, 'r') as f:
                    contract_abi = json.load(f)
                print(f"Successfully loaded contract ABI from {contract_abi_path}")
                
                try:
                    # First test the connection directly to ensure it's working
                    infura_url = os.environ.get('INFURA_URL')
                    print(f"Testing connection to {infura_url}...")
                    
                    # Try connecting multiple times with backoff
                    max_retries = 3
                    connected = False
                    
                    for attempt in range(1, max_retries + 1):
                        try:
                            w3 = Web3(Web3.HTTPProvider(infura_url))
                            connected = w3.is_connected()
                            print(f"Connection test (attempt {attempt}/{max_retries}): {'SUCCESS' if connected else 'FAILED'}")
                            
                            if connected:
                                # Get some basic info to verify connection
                                chain_id = w3.eth.chain_id
                                block_number = w3.eth.block_number
                                print(f"Connected to chain ID: {chain_id}, current block: {block_number}")
                                break
                                
                            if attempt < max_retries:
                                wait_time = 2 ** attempt  # Exponential backoff
                                print(f"Retrying in {wait_time} seconds...")
                                time.sleep(wait_time)
                        except Exception as e:
                            print(f"Connection error on attempt {attempt}: {str(e)}")
                            if attempt < max_retries:
                                wait_time = 2 ** attempt
                                print(f"Retrying in {wait_time} seconds...")
                                time.sleep(wait_time)
                    
                    if connected:
                        # Use the fallback blockchain client for better reliability
                        try:
                            # Import the blockchain client
                            from app.blockchain_client import BlockchainClient
                            
                            # Create an instance of the BlockchainClient class
                            app.blockchain_client = BlockchainClient(
                                os.environ.get('ETH_CONTRACT_ADDRESS'),
                                contract_abi
                            )
                            print("Using BlockchainClient implementation")
                            
                            # Verify that the client has the required methods
                            if not hasattr(app.app.blockchain_client, 'record_movement'):
                                print("DEBUG: Available methods:", dir(app.app.blockchain_client))
                                raise AttributeError("BlockchainClient does not have record_movement method")
                            if not hasattr(app.app.blockchain_client, 'get_movement_history'):
                                raise AttributeError("BlockchainClient does not have get_movement_history method")
                        except Exception as client_error:
                            print(f"Error initializing BlockchainClient: {str(client_error)}")
                            print("Falling back to BlockchainFallback implementation")
                            
                            # Fall back to the more reliable implementation
                            from app.blockchain_fallback import BlockchainFallback
                            app.blockchain_client = BlockchainFallback(
                                os.environ.get('ETH_CONTRACT_ADDRESS'),
                                contract_abi
                            )
                        
                        if app.blockchain_client.is_connected():
                            print("Blockchain client initialized successfully and connected to Ethereum network")
                            app.logger.info("Blockchain client initialized successfully and connected to Ethereum network")
                        else:
                            print("Blockchain client initialized but not connected to Ethereum network")
                            app.logger.warning("Blockchain client initialized but not connected to Ethereum network")
                    else:
                        print("Failed to establish connection to Ethereum network after multiple attempts")
                        app.logger.error("Failed to establish connection to Ethereum network after multiple attempts")
                        
                except Exception as e:
                    print(f"Failed to initialize blockchain client: {str(e)}")
                    print(traceback.format_exc())
                    app.logger.error(f"Failed to initialize blockchain client: {str(e)}")
            except Exception as e:
                print(f"Error loading contract ABI: {str(e)}")
                app.logger.error(f"Error loading contract ABI: {str(e)}")
        else:
            print(f"Contract ABI file not found at {contract_abi_path}. Blockchain features disabled.")
            app.logger.warning("Contract ABI file not found. Blockchain features disabled.")
    else:
        missing = []
        if not os.environ.get('ETH_CONTRACT_ADDRESS'):
            missing.append('ETH_CONTRACT_ADDRESS')
        if not os.environ.get('ETH_ACCOUNT_ADDRESS'):
            missing.append('ETH_ACCOUNT_ADDRESS')
        if not os.environ.get('INFURA_URL'):
            missing.append('INFURA_URL')
        
        print(f"Blockchain environment variables not set: {', '.join(missing)}. Blockchain features disabled.")
        app.logger.warning("Blockchain environment variables not set. Blockchain features disabled.")

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Setup Flask-Login
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(main)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp)  # Admin routes are already prefixed with '/admin' in the blueprint
    app.register_blueprint(distributor_bp)  # Distributor routes are prefixed with '/distributor' in the blueprint
    app.register_blueprint(customer_bp)  # Customer routes are prefixed with '/customer' in the blueprint

    return app
