import streamlit as st
from cosmos_client import CosmosDBClient
import json

def debug_buys():
    client = CosmosDBClient()
    trades = client.get_recent_trades(limit=50)
    
    buys = [t for t in trades if t.get('action', '').lower() == 'buy']
    print("--- DEBUG: Buy Records ---")
    for t in buys[:3]:
        print(json.dumps({k: str(v) for k, v in t.items() if not k.startswith('_')}, indent=2))

if __name__ == "__main__":
    debug_buys()
