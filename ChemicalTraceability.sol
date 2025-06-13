// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ChemicalTraceability {
    // Role definitions
    enum Role { NONE, ADMIN, MANUFACTURER, DISTRIBUTOR, CUSTOMER }
    
    // Organization struct
    struct Organization {
        string name;
        string emailDomain;
        bool canManufacture;
        bool canDistribute;
        bool canReceive;
        bool isActive;
        uint256 registrationTimestamp;
    }
    
    // User struct with role
    struct User {
        address userAddress;
        string username;
        string email;
        Role role;
        uint256 organizationId;
        bool isActive;
        bool isAdmin;
    }
    
    // Enhanced Chemical struct with RBAC fields
    struct Chemical {
        string name;
        string rfidTag;
        uint256 manufacturerOrgId;   // ID of manufacturer organization
        uint256 registeredByUserId;  // ID of user who registered
        uint256 currentCustodianId;  // Current organization that has custody
        uint256 registrationTimestamp;
        bool isRegistered;
        bool isActive;               // Can be deactivated if expired/consumed
    }
    
    // Enhanced MovementRecord with validation
    struct MovementRecord {
        string rfidTag;
        string location;
        string sourceLocation;       // Where moved from
        uint256 movedByUserId;      // User who initiated movement
        uint256 sourceOrgId;        // Source organization
        uint256 destinationOrgId;   // Destination organization
        string purpose;
        string status;               // General status 
        string validationStatus;     // 'verified', 'suspicious', 'pending'
        bool blockchainRecorded;     // Successfully recorded flag
        uint256 timestamp;
    }
    
    // Owner of the contract (platform admin)
    address public owner;
    
    // Counter for IDs
    uint256 private organizationCounter = 1;
    uint256 private userCounter = 1;
    
    // Storage mappings
    mapping(string => Chemical) public chemicals;
    mapping(string => MovementRecord[]) public movementHistory;
    mapping(uint256 => Organization) public organizations;
    mapping(address => User) public users;
    mapping(string => bool) public validLocations;  // Whitelist of valid locations
    mapping(string => bool) public authorizedPersonnel; // Whitelist of authorized personnel
    
    // Events
    event ChemicalRegistered(string rfidTag, string name, uint256 timestamp, uint256 manufacturerOrgId);
    event MovementRecorded(string rfidTag, string location, uint256 timestamp, string validationStatus);
    event OrganizationAdded(uint256 orgId, string name, string emailDomain);
    event UserAdded(uint256 userId, address userAddress, Role role, uint256 organizationId);
    event AnomalyDetected(string rfidTag, string anomalyType, string description);
    
    constructor() {
        owner = msg.sender;
        // Add admin user
        users[msg.sender] = User({
            userAddress: msg.sender,
            username: "admin",
            email: "admin@gmail.com",
            role: Role.ADMIN,
            organizationId: 0, // System organization
            isActive: true,
            isAdmin: true
        });
        
        // Add system organization
        organizations[0] = Organization({
            name: "System",
            emailDomain: "gmail.com",
            canManufacture: true,
            canDistribute: true,
            canReceive: true,
            isActive: true,
            registrationTimestamp: block.timestamp
        });
    }
    
    // Modifiers for access control
    modifier onlyOwner() {
        require(msg.sender == owner, "Only the contract owner can call this function");
        _;
    }
    
    modifier onlyAdmin() {
        require(users[msg.sender].isAdmin, "Only admin can call this function");
        _;
    }
    
    modifier onlyManufacturer() {
        require(users[msg.sender].role == Role.MANUFACTURER || users[msg.sender].isAdmin, 
            "Only manufacturer can call this function");
        require(organizations[users[msg.sender].organizationId].canManufacture || users[msg.sender].isAdmin, 
            "Organization does not have manufacturer rights");
        _;
    }
    
    modifier onlyDistributor() {
        require(users[msg.sender].role == Role.DISTRIBUTOR || users[msg.sender].isAdmin, 
            "Only distributor can call this function");
        require(organizations[users[msg.sender].organizationId].canDistribute || users[msg.sender].isAdmin, 
            "Organization does not have distributor rights");
        _;
    }
    
    // Function to add an organization (only admin)
    function addOrganization(
        string memory _name,
        string memory _emailDomain,
        bool _canManufacture,
        bool _canDistribute,
        bool _canReceive
    ) public onlyAdmin returns (uint256) {
        uint256 orgId = organizationCounter;
        organizationCounter++;
        
        organizations[orgId] = Organization({
            name: _name,
            emailDomain: _emailDomain,
            canManufacture: _canManufacture,
            canDistribute: _canDistribute,
            canReceive: _canReceive,
            isActive: true,
            registrationTimestamp: block.timestamp
        });
        
        emit OrganizationAdded(orgId, _name, _emailDomain);
        return orgId;
    }
    
    // Function to add a user (only admin)
    function addUser(
        address _userAddress,
        string memory _username,
        string memory _email,
        uint8 _role, // Using uint8 to represent enum in parameters
        uint256 _organizationId,
        bool _isAdmin
    ) public onlyAdmin returns (uint256) {
        require(organizations[_organizationId].isActive, "Organization is not active");
        
        uint256 userId = userCounter;
        userCounter++;
        
        users[_userAddress] = User({
            userAddress: _userAddress,
            username: _username,
            email: _email,
            role: Role(_role),
            organizationId: _organizationId,
            isActive: true,
            isAdmin: _isAdmin
        });
        
        emit UserAdded(userId, _userAddress, Role(_role), _organizationId);
        return userId;
    }
    
    // Function to add valid locations (only admin)
    function addValidLocation(string memory _location) public onlyAdmin {
        validLocations[_location] = true;
    }
    
    // Function to add authorized personnel (only admin)
    function addAuthorizedPersonnel(string memory _personnel) public onlyAdmin {
        authorizedPersonnel[_personnel] = true;
    }
    
    // Enhanced register chemical function with RBAC
    function registerChemical(
        string memory _rfidTag, 
        string memory _name, 
        string memory _manufacturer // We still store the manufacturer name
    ) public onlyManufacturer {
        require(!chemicals[_rfidTag].isRegistered, "Chemical already registered");
        
        uint256 manufacturerOrgId = users[msg.sender].organizationId;
        
        chemicals[_rfidTag] = Chemical({
            name: _name,
            rfidTag: _rfidTag,
            manufacturerOrgId: manufacturerOrgId,
            registeredByUserId: uint256(uint160(msg.sender)), // Convert address to uint for storage
            currentCustodianId: manufacturerOrgId, // Initially with manufacturer
            registrationTimestamp: block.timestamp,
            isRegistered: true,
            isActive: true
        });
        
        emit ChemicalRegistered(_rfidTag, _name, block.timestamp, manufacturerOrgId);
    }
    
    // Enhanced movement record function with validation
    function recordMovement(
        string memory _rfidTag,
        string memory _location,
        string memory _movedBy, // Keep for compatibility
        string memory _purpose,
        string memory _status
    ) public onlyDistributor {
        require(chemicals[_rfidTag].isRegistered, "Chemical not registered");
        require(chemicals[_rfidTag].isActive, "Chemical is deactivated");
        require(validLocations[_location], "Invalid location");
        
        // Perform basic validation
        string memory validationStatus = "verified";
        
        // Check if moved by authorized personnel
        if (!authorizedPersonnel[_movedBy]) {
            validationStatus = "suspicious";
        }
        
        uint256 sourceOrgId = chemicals[_rfidTag].currentCustodianId;
        uint256 destOrgId = users[msg.sender].organizationId;
        
        // Create movement record
        MovementRecord memory newRecord = MovementRecord({
            rfidTag: _rfidTag,
            location: _location,
            sourceLocation: "", // Would need to get this from previous record
            movedByUserId: uint256(uint160(msg.sender)),
            sourceOrgId: sourceOrgId,
            destinationOrgId: destOrgId,
            purpose: _purpose,
            status: _status,
            validationStatus: validationStatus,
            blockchainRecorded: true, // Always true for blockchain records
            timestamp: block.timestamp
        });
        
        // Only update custodian if verified
        if (keccak256(bytes(validationStatus)) == keccak256(bytes("verified"))) {
            chemicals[_rfidTag].currentCustodianId = destOrgId;
        }
        
        // Add to movement history
        movementHistory[_rfidTag].push(newRecord);
        
        emit MovementRecorded(_rfidTag, _location, block.timestamp, validationStatus);
    }
    
    // Original view functions with some enhancements
    function getMovementHistoryCount(string memory _rfidTag) public view returns (uint256) {
        return movementHistory[_rfidTag].length;
    }
    
    function getMovementRecord(string memory _rfidTag, uint256 _index) public view returns (
        string memory location,
        string memory sourceLocation,
        string memory purpose,
        string memory status,
        string memory validationStatus,
        uint256 timestamp
    ) {
        require(_index < movementHistory[_rfidTag].length, "Index out of bounds");
        MovementRecord memory record = movementHistory[_rfidTag][_index];
        
        return (
            record.location,
            record.sourceLocation,
            record.purpose,
            record.status,
            record.validationStatus,
            record.timestamp
        );
    }
    
    // Report anomaly in the blockchain
    function reportAnomaly(
        string memory _rfidTag,
        string memory _anomalyType,
        string memory _description
    ) public {
        require(chemicals[_rfidTag].isRegistered, "Chemical not registered");
        emit AnomalyDetected(_rfidTag, _anomalyType, _description);
    }
}
