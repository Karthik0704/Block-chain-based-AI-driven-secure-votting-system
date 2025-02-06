from web3 import Web3
from decouple import config
import json
import os

# Connect to Ganache
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))

# Update with your new contract address
CONTRACT_ADDRESS = '0x00bcbD2E7aF2Da136CCB9F09aa5b486E047648b7'

# Get the path to the contract JSON file
current_dir = os.path.dirname(os.path.abspath(__file__))
contract_path = os.path.join(current_dir, '..', '..', 'blockchain', 'build', 'contracts', 'VotingSystem.json')

# Get contract ABI
with open(contract_path) as f:
    contract_json = json.load(f)
    CONTRACT_ABI = contract_json['abi']

# Initialize contract
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# Private key for transactions
PRIVATE_KEY = config('BLOCKCHAIN_PRIVATE_KEY')
