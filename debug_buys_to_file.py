import streamlit as st
from cosmos_client import CosmosDBClient
import json

def debug_buys_to_file():
    client = CosmosDBClient()
    trades = client.get_recent_trades(limit=50)
    
    debug_info = {
        "buys": []
    }
    
    for t in trades:
        if t.get('action', '').lower() == 'buy':
            buy_data = {k: str(v) for k, v in t.items() if not k.startswith('_')}
            debug_info["buys"].append(buy_data)

    output_path = "d:\\Code\\crypto_dashboard\\debug_buys.json"
    with open(output_path, "w") as f:
        json.dump(debug_info, f, indent=2)
    
    print(f"Debug info written to {output_path}")

if __name__ == "__main__":
    debug_buys_to_file()
