import streamlit as st
from cosmos_client import CosmosDBClient
import json
import pandas as pd

def debug_thorough():
    client = CosmosDBClient()
    trades = client.get_recent_trades(limit=50)
    if not trades:
        print("No trades found.")
        return

    print(f"--- DEBUG: Analying {len(trades)} trades ---")
    sells = [t for t in trades if t.get('action', '').lower() == 'sell']
    
    if not sells:
        print("No sell trades found in recent 50.")
        return

    for i, t in enumerate(sells[:5]):
        print(f"\nSell #{i+1} - Coin: {t.get('coin')}")
        print(f"  Action: {t.get('action')}")
        print(f"  Price: {t.get('price')} (type: {type(t.get('price'))})")
        print(f"  Entry Price: {t.get('entry_price')} (type: {type(t.get('entry_price'))})")
        print(f"  Quantity: {t.get('quantity')} (type: {type(t.get('quantity'))})")
        
        # Check other potential fields
        others = ['profit', 'profit_usd', 'amount', 'executed_qty', 'buy_price']
        for o in others:
            if o in t:
                print(f"  {o}: {t[o]} (type: {type(t[o])})")

    df = pd.DataFrame(sells)
    print("\nColumn existence check:")
    for col in ['price', 'entry_price', 'quantity', 'profit']:
        print(f"  Column '{col}' exists: {col in df.columns}")
        if col in df.columns:
            print(f"    Value counts:\n{df[col].value_counts().head(3)}")

if __name__ == "__main__":
    debug_thorough()
