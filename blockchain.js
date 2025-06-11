/**
 * Blockchain API integration for Chemical Traceability System
 * Provides functions to interact with the blockchain backend
 */

class BlockchainClient {
    constructor() {
        this.baseUrl = 'http://127.0.0.1:5000'; // Base URL for API endpoints
        this.connectionStatus = 'pending'; // pending, connected, disconnected
        this.lastCheck = null;
        this.connectionInfo = {};
        
        // Initialize connection status
        this.checkConnection();
        
        // Check connection status periodically
        setInterval(() => this.checkConnection(), 30000); // Check every 30 seconds
    }
    
    // Check blockchain connection status
    async checkConnection() {
        try {
            const response = await fetch(`${this.baseUrl}/blockchain-status`);
            const data = await response.json();
            this.connectionStatus = data.connected ? 'connected' : 'disconnected';
            this.lastCheck = new Date();
            this.provider = data.provider || 'Unknown';
            this.contractAddress = data.contract_address || 'Unknown';
            this.chainInfo = data.chain_info || {};
            
            // Update UI if status element exists
            const statusElement = document.getElementById('blockchain-connection-status');
            if (statusElement) {
                if (data.connected) {
                    statusElement.textContent = `Connected to blockchain network (${this.provider})`;
                    statusElement.style.color = '#27ae60';
                } else {
                    statusElement.textContent = 'Disconnected from blockchain network';
                    statusElement.style.color = '#e74c3c';
                }
            }
            
            return data;
        } catch (error) {
            console.error('Error checking blockchain connection:', error);
            this.connectionStatus = 'disconnected';
            
            // Update UI if status element exists
            const statusElement = document.getElementById('blockchain-connection-status');
            if (statusElement) {
                statusElement.textContent = `Blockchain connection error: ${error.message}`;
                statusElement.style.color = '#e74c3c';
            }
            
            return { 
                status: 'error', 
                connected: false,
                message: error.message
            };
        }
    }
    
    /**
     * Register a new chemical on the blockchain
     * @param {Object} chemicalData - Object containing chemical data
     * @returns {Promise} Promise that resolves to registration result
     */
    async registerChemical(chemicalData) {
        try {
            const response = await fetch(`${this.baseUrl}/register-chemical`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(chemicalData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            return {
                success: true,
                data,
                blockchainStatus: data.blockchain ? data.blockchain.success : false,
                message: 'Chemical successfully registered'
            };
        } catch (error) {
            console.error('Error registering chemical:', error);
            return {
                success: false,
                message: `Failed to register chemical: ${error.message}`,
                error
            };
        }
    }
    
    /**
     * Log a movement event for a chemical
     * @param {Object} eventData - Data about the movement event
     * @returns {Promise} Promise that resolves to event logging result
     */
    async logEvent(eventData) {
        try {
            const response = await fetch(`${this.baseUrl}/log-event`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(eventData)
            });
            
            // Status 207 means partial success (local DB success but blockchain failure)
            if (response.status !== 201 && response.status !== 207) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            const isPartialSuccess = response.status === 207;
            
            return {
                success: true,
                data,
                blockchainStatus: data.blockchain ? data.blockchain.success : false,
                partialSuccess: isPartialSuccess,
                message: isPartialSuccess ? 
                    'Event logged in local database, but blockchain recording failed' :
                    'Event successfully logged with blockchain verification'
            };
        } catch (error) {
            console.error('Error logging movement event:', error);
            return {
                success: false,
                message: `Failed to log movement event: ${error.message}`,
                error
            };
        }
    }
    
    /**
     * Get movement history for a chemical with blockchain verification
     * @param {string} tagId - RFID tag ID of the chemical
     * @returns {Promise} Promise that resolves to history data
     */
    async getChemicalHistory(tagId) {
        try {
            // First get history with blockchain verification
            const blockchainVerificationResponse = await fetch(`${this.baseUrl}/blockchain-verification/${tagId}`);
            if (blockchainVerificationResponse.ok) {
                const blockchainData = await blockchainVerificationResponse.json();
                return {
                    success: true,
                    history: blockchainData.history || [],
                    blockchainEnabled: blockchainData.blockchain_enabled,
                    blockchainError: blockchainData.blockchain_error || null,
                    message: blockchainData.message || 'Retrieved chemical history with blockchain verification'
                };
            }
            
            // Fallback to just getting local history
            const response = await fetch(`${this.baseUrl}/chemical-history/${tagId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            return {
                success: true,
                history: data.history || [],
                blockchainEnabled: false,
                blockchainError: 'Blockchain verification unavailable, showing local database records only',
                message: 'Retrieved chemical history from local database'
            };
        } catch (error) {
            console.error('Error getting chemical history:', error);
            return {
                success: false,
                message: `Failed to get chemical history: ${error.message}`,
                history: [],
                error
            };
        }
    }
}

// Create a global blockchain client instance
const blockchainClient = new BlockchainClient();

// Export the blockchain client for use in other modules
window.blockchainClient = blockchainClient;
