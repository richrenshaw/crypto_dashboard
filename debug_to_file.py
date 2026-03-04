import streamlit as st
from cosmos_client import CosmosDBClient
import json
import os

def debug_to_file():
    client = CosmosDBClient()
    trades = client.get_recent_trades(limit=50)
    
    debug_info = {
        "count": len(trades),
        "sells": []
    }
    
    for t in trades:
        if t.get('action', '').lower() == 'sell':
            # Collect all keys and specific values
            sell_data = {k: str(v) for k, v in t.items() if not k.startswith('_')}
            debug_info["sells"].append(sell_data)

    output_path = "d:\\Code\\crypto_dashboard\\debug_output.json"
    with open(output_path, "w") as f:
        json.dump(debug_info, f, indent=2)
    
    print(f"Debug info written to {output_path}")

if __name__ == "__main__":
    debug_to_file()
