// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VotingSystem {
    struct Vote {
        string voterUniqueId;
        uint256 candidateId;
        uint256 timestamp;
    }
    
    Vote[] public votes;
    mapping(string => bool) public hasVoted;
    
    event VoteCast(string voterUniqueId, uint256 candidateId, uint256 timestamp);
    
    function castVote(string memory _voterUniqueId, uint256 _candidateId) public {
        require(!hasVoted[_voterUniqueId], "You have already voted");
        
        votes.push(Vote({
            voterUniqueId: _voterUniqueId,
            candidateId: _candidateId,
            timestamp: block.timestamp
        }));
        
        hasVoted[_voterUniqueId] = true;
        emit VoteCast(_voterUniqueId, _candidateId, block.timestamp);
    }
    
    function getTotalVotes() public view returns (uint256) {
    return totalVotes;
}

function getCandidateVotes(uint256 candidateId) public view returns (uint256) {
    return candidates[candidateId].voteCount;
}

