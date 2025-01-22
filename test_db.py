"""Test database operations in development mode."""

from agent_backend.db.tokens import add_token, get_tokens
from agent_backend.db.nfts import add_nft, get_nfts
from agent_backend.db.wallets import save_wallet, get_wallet

def test_tokens():
    """Test token operations."""
    print("\nTesting token operations:")
    test_address = "0x123456789"
    add_token(test_address)
    tokens = get_tokens()
    print(f"Added token {test_address}")
    print(f"Retrieved tokens: {tokens}")
    assert test_address in tokens

def test_nfts():
    """Test NFT operations."""
    print("\nTesting NFT operations:")
    test_address = "0x987654321"
    add_nft(test_address)
    nfts = get_nfts()
    print(f"Added NFT {test_address}")
    print(f"Retrieved NFTs: {nfts}")
    assert test_address in nfts

def test_wallets():
    """Test wallet operations."""
    print("\nTesting wallet operations:")
    wallet_id = "test-wallet-123"
    wallet_data = {
        "address": "0xabcdef",
        "network": "test-network"
    }
    save_wallet(wallet_id, wallet_data)
    retrieved_data = get_wallet(wallet_id)
    print(f"Saved wallet {wallet_id} with data: {wallet_data}")
    print(f"Retrieved wallet data: {retrieved_data}")
    assert retrieved_data == wallet_data

if __name__ == "__main__":
    print("Testing database operations in development mode...")
    test_tokens()
    test_nfts()
    test_wallets()
    print("\nAll tests passed successfully!") 