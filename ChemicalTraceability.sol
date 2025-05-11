// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ChemicalTraceability {
    struct Chemical {
        string name;
        string rfidTag;
        string manufacturer;
        uint256 registrationTimestamp;
        bool isRegistered;
    }
    
    struct MovementRecord {
        string rfidTag;
        string location;
        string movedBy;
        string purpose;
        string status;
        uint256 timestamp;
    }
    
    mapping(string => Chemical) public chemicals;
    mapping(string => MovementRecord[]) public movementHistory;
    
    event ChemicalRegistered(string rfidTag, string name, uint256 timestamp);
    event MovementRecorded(string rfidTag, string location, uint256 timestamp);
    
    function registerChemical(
        string memory _rfidTag, 
        string memory _name, 
        string memory _manufacturer
    ) public {
        require(!chemicals[_rfidTag].isRegistered, "Chemical already registered");
        
        chemicals[_rfidTag] = Chemical({
            name: _name,
            rfidTag: _rfidTag,
            manufacturer: _manufacturer,
            registrationTimestamp: block.timestamp,
            isRegistered: true
        });
        
        emit ChemicalRegistered(_rfidTag, _name, block.timestamp);
    }
    
    function recordMovement(
        string memory _rfidTag,
        string memory _location,
        string memory _movedBy,
        string memory _purpose,
        string memory _status
    ) public {
        require(chemicals[_rfidTag].isRegistered, "Chemical not registered");
        
        MovementRecord memory newRecord = MovementRecord({
            rfidTag: _rfidTag,
            location: _location,
            movedBy: _movedBy,
            purpose: _purpose,
            status: _status,
            timestamp: block.timestamp
        });
        
        movementHistory[_rfidTag].push(newRecord);
        
        emit MovementRecorded(_rfidTag, _location, block.timestamp);
    }
    
    function getMovementHistoryCount(string memory _rfidTag) public view returns (uint256) {
        return movementHistory[_rfidTag].length;
    }
    
    function getMovementRecord(string memory _rfidTag, uint256 _index) public view returns (
        string memory location,
        string memory movedBy,
        string memory purpose,
        string memory status,
        uint256 timestamp
    ) {
        require(_index < movementHistory[_rfidTag].length, "Index out of bounds");
        MovementRecord memory record = movementHistory[_rfidTag][_index];
        
        return (
            record.location,
            record.movedBy,
            record.purpose,
            record.status,
            record.timestamp
        );
    }
}
