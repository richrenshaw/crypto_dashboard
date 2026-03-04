from cosmos_client import CosmosDBClient
import json

def test_reset():
    client = CosmosDBClient()
    print("--- Running clear_all_data() ---")
    success = client.clear_all_data()
    print(f"Success: {success}")
    
    print("\n--- Checking Portfolio ---")
    portfolio = client.get_portfolio()
    if portfolio:
        print(json.dumps({k: v for k, v in portfolio.items() if not k.startswith('_')}, indent=2))
        if portfolio.get('balance_usd') == 1000.0 and portfolio.get('holdings') == {}:
            print("\nSUCCESS: Portfolio reset correctly.")
        else:
            print("\nFAILURE: Portfolio NOT reset correctly.")
    else:
        print("Portfolio not found.")

if __name__ == "__main__":
    test_reset()
