from web3_config import w3, contract

def test_contract():
    print("Web3 Connected:", w3.is_connected())
    print("Contract Address:", contract.address)
    print("Total Votes:", contract.functions.getTotalVotes().call())

if __name__ == "__main__":
    test_contract()
