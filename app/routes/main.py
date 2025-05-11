from flask import Blueprint, request, jsonify, redirect, url_for, current_app
from app.models import Chemical, MovementLog
from app.extensions import db
from datetime import datetime
import traceback  # Add traceback for better error reporting
import os  # Add os for environment variable access

# Function to directly get blockchain history when using the original client
def get_blockchain_history_direct(client, rfid_tag):
    """Get the complete movement history for a chemical directly from blockchain"""
    try:
        print(f"DEBUG: Getting movement history directly for RFID tag: {rfid_tag}")
        
        # Check connection before proceeding
        if not client.w3.is_connected():
            print("DEBUG: Web3 connection lost, attempting to reconnect...")
            return {
                'success': False,
                'error': 'Lost connection to Ethereum network',
                'history': []
            }
        
        # Get count of movement records
        print(f"DEBUG: Calling getMovementHistoryCount for {rfid_tag}")
        count = client.contract.functions.getMovementHistoryCount(rfid_tag).call()
        print(f"DEBUG: Found {count} movement records on blockchain")
        
        # Get all movement records
        history = []
        for i in range(count):
            print(f"DEBUG: Fetching movement record {i+1}/{count}")
            location, moved_by, purpose, status, timestamp = client.contract.functions.getMovementRecord(
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
        print(f"DEBUG: Error getting movement history directly: {str(e)}")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'history': []
        }

main = Blueprint('main', __name__)

@main.route('/register-chemical', methods=['POST'])
def register_chemical():
    data = request.get_json()
    
    # Convert date strings to datetime objects
    expiry_date = None
    received_date = None
    if data.get('expiry_date'):
        expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
    if data.get('received_date'):
        received_date = datetime.strptime(data['received_date'], '%Y-%m-%d').date()
    
    # Create chemical in local database
    new_chemical = Chemical(
        name=data['name'],
        rfid_tag=data['rfid_tag'],
        manufacturer=data.get('manufacturer', ''),
        current_location=data.get('current_location', 'Storage'),
        quantity=data.get('quantity'),
        unit=data.get('unit'),
        expiry_date=expiry_date,
        storage_condition=data.get('storage_condition'),
        received_date=received_date,
        batch_number=data.get('batch_number'),
        hazard_class=data.get('hazard_class'),
        cas_number=data.get('cas_number'),
        description=data.get('description')
    )
    
    # Add to local database
    db.session.add(new_chemical)
    db.session.commit()
    
    # Record on blockchain if client is available
    blockchain_result = None
    if current_app.blockchain_client:
        blockchain_result = current_app.blockchain_client.register_chemical(
            data['rfid_tag'],
            data['name'],
            data.get('manufacturer', '')
        )
    
    response = {
        'message': 'Chemical registered successfully',
        'chemical_id': new_chemical.id
    }
    
    if blockchain_result:
        response['blockchain'] = blockchain_result
    
    return jsonify(response), 201

@main.route('/log-event', methods=['POST'])
def log_event():
    try:
        # Try to get JSON data first
        if request.is_json:
            data = request.get_json()
        else:
            # Fall back to form data if not JSON
            data = request.form.to_dict()
        
        # Validate required fields
        if 'tag_id' not in data or 'location' not in data:
            return jsonify({'error': 'Missing required fields: tag_id and location are required'}), 400
        
        # Create new movement log with all fields
        new_log = MovementLog(
            tag_id=data['tag_id'],
            location=data['location'],
            timestamp=datetime.utcnow(),
            moved_by=data.get('moved_by'),
            purpose=data.get('purpose'),
            status=data.get('status'),
            remarks=data.get('remarks')
        )
        
        # Update the chemical's current location
        chemical = Chemical.query.filter_by(rfid_tag=data['tag_id']).first()
        if chemical:
            chemical.current_location = data['location']
        else:
            # Log a warning but don't fail if chemical not found
            print(f"Warning: No chemical found with RFID tag {data['tag_id']}")
        
        db.session.add(new_log)
        db.session.commit()
        
        # Record on blockchain if client is available
        blockchain_result = None
        if hasattr(current_app, 'blockchain_client') and current_app.blockchain_client:
            try:
                blockchain_result = current_app.blockchain_client.record_movement(
                    data['tag_id'],
                    data['location'],
                    data.get('moved_by', ''),
                    data.get('purpose', ''),
                    data.get('status', '')
                )
                
                if not blockchain_result.get('success', False):
                    print(f"WARNING: Blockchain transaction failed: {blockchain_result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"ERROR: Failed to record movement on blockchain: {str(e)}")
                traceback.print_exc()
                blockchain_result = {
                    'success': False,
                    'error': str(e)
                }
        
        response = {
            'message': 'Event logged successfully',
            'local_db_success': True
        }
        
        if blockchain_result:
            response['blockchain'] = blockchain_result
            response['blockchain_success'] = blockchain_result.get('success', False)
        
        # Return JSON response for API calls, or redirect for form submissions
        if request.is_json:
            # If blockchain transaction failed but local DB succeeded, return 207 Multi-Status
            if blockchain_result and not blockchain_result.get('success', False):
                return jsonify(response), 207
            return jsonify(response), 201
        else:
            return redirect(url_for('dashboard_bp.dashboard'))
            
    except Exception as e:
        # Roll back any changes and return error
        db.session.rollback()
        error_msg = str(e)
        print(f"Error in log_event: {error_msg}")
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        else:
            return f"Error logging event: {error_msg}", 500

@main.route('/chemical-history/<tag_id>', methods=['GET'])
def chemical_history(tag_id):
    logs = MovementLog.query.filter_by(tag_id=tag_id).order_by(MovementLog.timestamp.desc()).all()
    history = [{
        'location': log.location,
        'timestamp': log.timestamp.isoformat(),
        'status': log.status,
        'moved_by': log.moved_by,
        'purpose': log.purpose,
        'remarks': log.remarks
    } for log in logs]
    return jsonify({'history': history}), 200

@main.route('/blockchain-status', methods=['GET'])
def blockchain_status():
    """Check the status of the blockchain client"""
    try:
        # If blockchain client is not initialized
        if not current_app.blockchain_client:
            return jsonify({
                'status': 'disabled',
                'message': 'Blockchain features are disabled',
                'connected': False
            })
        
        # Check if client is connected
        connected = False
        contract_address = 'Unknown'
        account_address = 'Unknown'
        chain_info = {}
        
        # Check connection status
        if hasattr(current_app.blockchain_client, 'is_connected'):
            connected = current_app.blockchain_client.is_connected()
            print(f"DEBUG: Blockchain connection status from is_connected(): {connected}")
        elif hasattr(current_app.blockchain_client, 'w3'):
            try:
                connected = current_app.blockchain_client.w3.is_connected()
                print(f"DEBUG: Blockchain connection status from w3.is_connected(): {connected}")
            except Exception as conn_error:
                print(f"DEBUG: Error checking connection: {str(conn_error)}")
                connected = False
        
        # Get contract address
        if hasattr(current_app.blockchain_client, 'contract_address'):
            contract_address = current_app.blockchain_client.contract_address
        elif hasattr(current_app.blockchain_client, 'contract') and hasattr(current_app.blockchain_client.contract, 'address'):
            contract_address = current_app.blockchain_client.contract.address
        
        # Get account address
        if hasattr(current_app.blockchain_client, 'account_address'):
            account_address = current_app.blockchain_client.account_address
        elif os.environ.get('ETH_ACCOUNT_ADDRESS'):
            account_address = os.environ.get('ETH_ACCOUNT_ADDRESS')
        
        # Get chain info if connected
        if connected and hasattr(current_app.blockchain_client, 'w3'):
            try:
                chain_info['chain_id'] = current_app.blockchain_client.w3.eth.chain_id
                chain_info['block_number'] = current_app.blockchain_client.w3.eth.block_number
                
                # Check account balance
                if account_address != 'Unknown':
                    balance = current_app.blockchain_client.w3.eth.get_balance(account_address)
                    chain_info['balance'] = current_app.blockchain_client.w3.from_wei(balance, 'ether')
            except Exception as chain_error:
                print(f"DEBUG: Error getting chain info: {str(chain_error)}")
                traceback.print_exc()
        
        # If not connected, try to reconnect
        if not connected and hasattr(current_app.blockchain_client, 'reconnect'):
            try:
                print("DEBUG: Attempting to reconnect to blockchain...")
                reconnect_result = current_app.blockchain_client.reconnect()
                print(f"DEBUG: Reconnect result: {reconnect_result}")
                connected = current_app.blockchain_client.is_connected()
                print(f"DEBUG: Connection status after reconnect: {connected}")
            except Exception as reconnect_error:
                print(f"DEBUG: Error during reconnect: {str(reconnect_error)}")
        
        return jsonify({
            'status': 'enabled',
            'connected': connected,
            'contract_address': contract_address,
            'account_address': account_address,
            'provider': str(current_app.blockchain_client.w3.provider) if hasattr(current_app.blockchain_client, 'w3') else 'Unknown',
            'chain_info': chain_info if connected else {}
        })
    except Exception as e:
        traceback.print_exc()  # Print full traceback to console
        return jsonify({
            'status': 'error',
            'message': str(e),
            'connected': False
        }), 500

@main.route('/blockchain-verification/<tag_id>', methods=['GET'])
def blockchain_verification(tag_id):
    """Get blockchain verification status for a chemical's movement history"""
    try:
        print(f"DEBUG: Blockchain verification requested for tag_id: {tag_id}")
        
        # Get local history first - this will always work
        local_logs = MovementLog.query.filter_by(tag_id=tag_id).order_by(MovementLog.timestamp).all()
        print(f"DEBUG: Found {len(local_logs)} local movement logs")
        
        local_history = [{
            'location': log.location,
            'moved_by': log.moved_by if log.moved_by else '',
            'purpose': log.purpose if log.purpose else '',
            'status': log.status if log.status else '',
            'timestamp': int(log.timestamp.timestamp()),
            'blockchain_verified': False
        } for log in local_logs]
        
        # If blockchain client isn't available, return local history only
        if not current_app.blockchain_client:
            print("DEBUG: Blockchain client is not initialized")
            return jsonify({
                'success': True,  # Success is True because we have local history
                'blockchain_enabled': False,
                'history': local_history,
                'message': 'Blockchain features are disabled'
            })
        
        # Try to get blockchain history directly from the contract
        print("DEBUG: Blockchain client is available, fetching history from blockchain")
        print(f"DEBUG: Blockchain client type: {type(current_app.blockchain_client).__name__}")
        
        try:
            # First check if the client is connected
            is_connected = False
            if hasattr(current_app.blockchain_client, 'is_connected'):
                is_connected = current_app.blockchain_client.is_connected()
                print(f"DEBUG: Blockchain connection status from is_connected(): {is_connected}")
            elif hasattr(current_app.blockchain_client, 'w3'):
                try:
                    is_connected = current_app.blockchain_client.w3.is_connected()
                    print(f"DEBUG: Blockchain connection status from w3.is_connected(): {is_connected}")
                except Exception as e:
                    print(f"DEBUG: Error checking w3 connection: {str(e)}")
                    is_connected = False
            
            # If not connected, try to reconnect
            if not is_connected and hasattr(current_app.blockchain_client, 'reconnect'):
                print("DEBUG: Blockchain client is not connected, attempting to reconnect...")
                try:
                    is_connected = current_app.blockchain_client.reconnect()
                    print(f"DEBUG: Reconnection attempt result: {is_connected}")
                except Exception as e:
                    print(f"DEBUG: Error during reconnection attempt: {str(e)}")
            
            if not is_connected:
                print("DEBUG: Blockchain client is not connected after reconnection attempts")
                blockchain_result = {
                    'success': False,
                    'error': 'Blockchain network connection unavailable',
                    'history': []
                }
                return jsonify({
                    'success': True,  # Success is True because we have local history
                    'blockchain_enabled': True,
                    'blockchain_error': 'Blockchain network connection unavailable',
                    'history': local_history,
                    'message': 'Blockchain verification failed'
                })
            
            # Implement direct blockchain history retrieval
            if hasattr(current_app.blockchain_client, 'contract') and hasattr(current_app.blockchain_client, 'w3'):
                try:
                    # Verify connection is still active
                    if not current_app.blockchain_client.w3.is_connected():
                        print("DEBUG: Connection lost before querying blockchain, attempting to reconnect...")
                        if hasattr(current_app.blockchain_client, 'reconnect'):
                            is_connected = current_app.blockchain_client.reconnect()
                            if not is_connected:
                                raise ConnectionError("Failed to reconnect to blockchain network")
                        else:
                            raise ConnectionError("Connection lost and no reconnect method available")
                    
                    # Get count of movement records
                    print(f"DEBUG: Calling getMovementHistoryCount for {tag_id}")
                    count = current_app.blockchain_client.contract.functions.getMovementHistoryCount(tag_id).call()
                    print(f"DEBUG: Found {count} movement records on blockchain")
                    
                    # Get all movement records
                    blockchain_history = []
                    for i in range(count):
                        print(f"DEBUG: Fetching movement record {i+1}/{count}")
                        location, moved_by, purpose, status, timestamp = current_app.blockchain_client.contract.functions.getMovementRecord(
                            tag_id, i
                        ).call()
                        
                        print(f"DEBUG: Record {i+1}: location={location}, timestamp={timestamp}")
                        
                        blockchain_history.append({
                            'location': location,
                            'moved_by': moved_by,
                            'purpose': purpose,
                            'status': status,
                            'timestamp': timestamp,
                            'blockchain_verified': True
                        })
                    
                    # Even if there are no records, consider this a success as long as we could query the blockchain
                    blockchain_result = {
                        'success': True,
                        'history': blockchain_history,
                        'message': 'No blockchain records found' if len(blockchain_history) == 0 else 'Blockchain records retrieved successfully'
                    }
                except Exception as e:
                    print(f"DEBUG: Error during blockchain history retrieval: {str(e)}")
                    traceback.print_exc()
                    blockchain_result = {
                        'success': False,
                        'error': str(e),
                        'history': []
                    }
            else:
                print("DEBUG: Blockchain client does not have contract or w3 attributes")
                blockchain_result = {
                    'success': False,
                    'error': 'Blockchain client not properly initialized',
                    'history': []
                }
        except Exception as e:
            print(f"DEBUG: Error getting blockchain history: {str(e)}")
            traceback.print_exc()
            blockchain_result = {
                'success': False,
                'error': str(e),
                'history': []
            }
        
        # Check if blockchain fetch was successful
        if blockchain_result.get('success'):
            blockchain_history = blockchain_result.get('history', [])
            print(f"DEBUG: Found {len(blockchain_history)} blockchain movement records")
            
            # If we have blockchain records, try to match them with local records
            if blockchain_history:
                # Simple matching algorithm - can be improved for production
                for i, local_record in enumerate(local_history):
                    for j, blockchain_record in enumerate(blockchain_history):
                        if (local_record['location'] == blockchain_record['location'] and
                            abs(local_record['timestamp'] - blockchain_record['timestamp']) < 300):  # Within 5 minutes
                            local_record['blockchain_verified'] = True
                            print(f"DEBUG: Verified record {i} (local) matches record {j} (blockchain)")
                            break
                
                return jsonify({
                    'success': True,
                    'blockchain_enabled': True,
                    'blockchain_connected': True,
                    'history': local_history,
                    'message': 'Blockchain verification completed successfully'
                })
            else:
                # Blockchain is connected but no records found - this is still a success
                print("DEBUG: Blockchain is connected but no records found for this tag")
                return jsonify({
                    'success': True,
                    'blockchain_enabled': True,
                    'blockchain_connected': True,
                    'history': local_history,
                    'message': 'Chemical not yet registered on blockchain'
                })
        else:
            # Blockchain fetch failed but we still have local history
            error_message = blockchain_result.get('error', 'Unknown blockchain error')
            print(f"DEBUG: Blockchain fetch failed: {error_message}")
            
            # Check if this is a fallback response
            if blockchain_result.get('fallback'):
                return jsonify({
                    'success': True,  # Success is True because we have local history
                    'blockchain_enabled': True,
                    'blockchain_available': False,
                    'error': error_message,
                    'history': local_history,
                    'message': 'Using local history due to blockchain unavailability'
                })
            else:
                return jsonify({
                    'success': True,  # Success is True because we have local history
                    'blockchain_enabled': True,
                    'blockchain_error': error_message,
                    'history': local_history,
                    'message': 'Blockchain verification failed'
                })
    
    except Exception as e:
        traceback.print_exc()  # Print full traceback to console
        print(f"ERROR in blockchain verification: {str(e)}")
        
        # Try to get local history even if there was an error
        try:
            local_logs = MovementLog.query.filter_by(tag_id=tag_id).order_by(MovementLog.timestamp).all()
            local_history = [{
                'location': log.location,
                'moved_by': log.moved_by if log.moved_by else '',
                'purpose': log.purpose if log.purpose else '',
                'status': log.status if log.status else '',
                'timestamp': int(log.timestamp.timestamp()),
                'blockchain_verified': False
            } for log in local_logs]
            
            return jsonify({
                'success': True,
                'blockchain_enabled': True,
                'blockchain_error': str(e),
                'history': local_history,
                'message': 'Error during blockchain verification'
            })
        except Exception as inner_e:
            return jsonify({
                'success': False,
                'error': f"Failed to get movement history: {str(e)}, then failed to get local history: {str(inner_e)}"
            }), 500
