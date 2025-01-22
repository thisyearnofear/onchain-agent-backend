import json
from cdp_langchain.utils import CdpAgentkitWrapper

# Read the CDP config
with open("cdp_api_key.json") as f:
    config = json.load(f)

# Initialize CDP Agentkit wrapper
values = {
    "cdp_api_key_name": config['name'],
    "cdp_api_key_private_key": config['privateKey']
}

print("Initializing CDP Agentkit wrapper...")
agentkit = CdpAgentkitWrapper(**values)
print("CDP SDK configured successfully")

# Get wallet details
wallet = agentkit.wallet
print(f"\nWallet Details:")
print(f"Wallet ID: {wallet.id}")
print(f"Network: {wallet.network_id}")
print(f"Default Address: {wallet.default_address.address_id}")

# Try to get seed/private key info
print("\nWallet Configuration:")
print(json.dumps(agentkit.to_dict(), indent=2))

print("\nAll Addresses:")
for address in wallet.addresses:
    print(f"- {address.address_id}") 