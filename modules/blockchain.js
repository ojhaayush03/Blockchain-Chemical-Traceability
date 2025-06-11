/**
 * Blockchain Client for interacting with the Ethereum blockchain
 * Handles all blockchain-related operations
 */

// Import Web3 library
import Web3 from 'https://cdn.jsdelivr.net/npm/web3@1.5.2/dist/web3.min.js';

class BlockchainClient {
    constructor(contractAddress, contractABI) {
        console.log("DEBUG: Initializing BlockchainClient");
        
        // Connect to Ethereum network (using Web3 provider)
        this.web3 = new Web3(Web3.givenProvider || 'http://localhost:7545');
        
        // Load contract
        this.contract = new this.web3.eth.Contract(contractABI, contractAddress);
        
        // Set default account (first account in the connected wallet)
        this.defaultAccount = null;
    }
    
    /**
     * Initialize the blockchain client with the user's account
     * @returns {Promise<boolean>} True if initialization was successful
     */
    async initialize() {
        try {
            // Request account access if needed
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            this.defaultAccount = accounts[0];
            console.log("DEBUG: Using account:", this.defaultAccount);
            return true;
        } catch (error) {
            console.error("Error initializing blockchain client:", error);
            return false;
        }
    }
    
    /**
     * Register a new chemical on the blockchain
     * @param {string} rfidTag - The RFID tag of the chemical
     * @param {string} name - The name of the chemical
     * @param {string} manufacturer - The manufacturer of the chemical
     * @returns {Promise<Object>} Transaction receipt
     */
    async registerChemical(rfidTag, name, manufacturer) {
        try {
            console.log("DEBUG: Registering chemical on blockchain:", { rfidTag, name, manufacturer });
            
            const result = await this.contract.methods
                .registerChemical(rfidTag, name, manufacturer)
                .send({ from: this.defaultAccount });
                
            console.log("DEBUG: Chemical registered successfully:", result);
            return {
                success: true,
                transactionHash: result.transactionHash,
                blockNumber: result.blockNumber
            };
        } catch (error) {
            console.error("Error registering chemical:", error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Record a movement event on the blockchain
     * @param {string} rfidTag - The RFID tag of the chemical
     * @param {string} location - The new location
     * @param {string} movedBy - The address of the mover
     * @param {string} purpose - The purpose of the movement
     * @param {string} status - The status of the movement
     * @returns {Promise<Object>} Transaction receipt
     */
    async recordMovement(rfidTag, location, movedBy = "", purpose = "", status = "") {
        try {
            console.log("DEBUG: Recording movement on blockchain:", { rfidTag, location, movedBy, purpose, status });
            
            const result = await this.contract.methods
                .recordMovement(rfidTag, location, movedBy, purpose, status)
                .send({ from: this.defaultAccount });
                
            console.log("DEBUG: Movement recorded successfully:", result);
            return {
                success: true,
                transactionHash: result.transactionHash,
                blockNumber: result.blockNumber
            };
        } catch (error) {
            console.error("Error recording movement:", error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Get the movement history for a chemical
     * @param {string} rfidTag - The RFID tag of the chemical
     * @returns {Promise<Array>} Array of movement events
     */
    async getMovementHistory(rfidTag) {
        try {
            console.log("DEBUG: Getting movement history for:", rfidTag);
            
            const events = await this.contract.getPastEvents('ChemicalMoved', {
                filter: { rfidTag: rfidTag },
                fromBlock: 0,
                toBlock: 'latest'
            });
            
            console.log("DEBUG: Retrieved movement history:", events);
            return events.map(event => event.returnValues);
        } catch (error) {
            console.error("Error getting movement history:", error);
            return [];
        }
    }
}

// Export the BlockchainClient class
export default BlockchainClient;