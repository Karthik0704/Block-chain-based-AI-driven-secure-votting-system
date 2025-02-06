from web3_config import w3, contract

def test_vote():
    # Get account from Ganache
    account = w3.eth.accounts[0]
    
    # Test vote transaction
    transaction = contract.functions.castVote(
        "TEST_USER_123",  # Test voter ID
        1  # Test candidate ID
    ).build_transaction({
        'from': account,
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account),
    })
    
    # Send transaction
    tx_hash = w3.eth.send_transaction(transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    print("Transaction successful:", tx_receipt.status == 1)
    print("Total votes after transaction:", contract.functions.getTotalVotes().call())

if __name__ == "__main__":
    test_vote()
