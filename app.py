import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from cosmos_client import CosmosDBClient
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Crypto Trader Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Premium Look
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div[data-testid="stExpander"] {
        border: none !important;
        background-color: #1e2130 !important;
        border-radius: 10px;
    }
    .stTable {
        background-color: #1e2130;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Cosmos Client
@st.cache_resource
def get_client():
    return CosmosDBClient()

client = get_client()

# --- SIDEBAR: SETTINGS ---
st.sidebar.title("⚙️ Trading Settings")
settings = client.get_settings()

if settings:
    with st.sidebar.form("settings_form"):
        st.subheader("Risk Parameters")
        tp = st.number_input("Take Profit (%)", value=float(settings.get("TAKE_PROFIT", 0)), step=0.1)
        sl = st.number_input("Stop Loss (%)", value=float(settings.get("STOP_LOSS", 0)), step=0.1)
        amount = st.number_input("Order Amount (USD)", value=float(settings.get("ORDER_AMOUNT", 0)), step=1.0)
        
        st.subheader("Tracking")
        coins_str = st.text_area("Coins to Track (comma separated)", 
                                 value=", ".join(settings.get("COINS_TO_TRACK", [])))
        
        st.subheader("Templates")
        prompt_template = st.text_area("Prompt Template", 
                                       value=settings.get("PROMPT_TEMPLATE", ""),
                                       height=200)
        
        submitted = st.form_submit_button("Update Settings")
        
        if submitted:
            new_coins = [c.strip() for c in coins_str.split(",") if c.strip()]
            settings["TAKE_PROFIT"] = tp
            settings["STOP_LOSS"] = sl
            settings["ORDER_AMOUNT"] = amount
            settings["COINS_TO_TRACK"] = new_coins
            settings["PROMPT_TEMPLATE"] = prompt_template
            
            if client.update_settings(settings):
                st.sidebar.success("Settings updated successfully!")
            else:
                st.sidebar.error("Failed to update settings.")

# --- MAIN CONTENT ---
st.title("📈 Crypto Trader Dashboard")

# 1. Top Metrics
portfolio = client.get_portfolio()
equity_logs = client.get_equity_logs()

if portfolio:
    # Display Last Run Time
    last_run = "Unknown"
    if equity_logs:
        latest_log = equity_logs[0] # Sorted DESC
        ts = latest_log.get("timestamp")
        if ts:
            last_run = pd.to_datetime(ts).strftime("%Y-%m-%d %H:%M:%S")
    
    st.markdown(f"**Last Update:** `{last_run}`")
    
    cols = st.columns(4)
    # Calculate total value using current_price if available
    total_holdings_val = 0
    for h in portfolio.get("holdings", {}).values():
        qty = h.get("quantity", 0)
        curr_price = h.get("current_price", h.get("entry_price", 0))
        total_holdings_val += qty * curr_price
        
    total_val = total_holdings_val + portfolio.get("balance_usd", 0)
    
    cols[0].metric("Total Portfolio Value", f"${total_val:,.2f}")
    cols[1].metric("Cash Balance", f"${portfolio.get('balance_usd', 0):,.2f}")
    cols[2].metric("Holdings Count", len(portfolio.get("holdings", {})))
    
    # Simple profit calculation if equity logs exist
    if len(equity_logs) > 1:
        start_val = equity_logs[-1].get("total_value", total_val)
        pnl = total_val - start_val
        pnl_pct = (pnl / start_val) * 100 if start_val != 0 else 0
        cols[3].metric("Period PnL", f"${pnl:,.2f}", f"{pnl_pct:+.2f}%")

st.divider()

# 2. Performance Chart
if equity_logs:
    st.subheader("Performance Over Time")
    df_equity = pd.DataFrame(equity_logs)
    df_equity['timestamp'] = pd.to_datetime(df_equity['timestamp'])
    df_equity = df_equity.sort_values('timestamp')
    
    fig = px.area(df_equity, x='timestamp', y='total_value', 
                  title="Equity Curve",
                  line_shape='spline',
                  color_discrete_sequence=['#00cc96'])
    fig.update_layout(
        template="plotly_dark", 
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Time",
        yaxis_title="Total Value (USD)"
    )
    st.plotly_chart(fig, use_container_width=True)

# 3. Portfolio & Trades
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Current Holdings")
    if portfolio:
        holdings = []
        for coin, data in portfolio.get("holdings", {}).items():
            qty = data.get("quantity", 0)
            entry = data.get("entry_price", 0)
            curr = data.get("current_price", entry)
            val = qty * curr
            pnl_usd = (curr - entry) * qty if entry > 0 else 0
            pnl_pct = ((curr / entry) - 1) * 100 if entry > 0 else 0
            
            holdings.append({
                "Coin": coin,
                "Quantity": qty,
                "Avg Entry": entry,
                "Current Price": curr,
                "Value (USD)": val,
                "P&L ($)": pnl_usd,
                "P&L (%)": pnl_pct,
                "URL": data.get("url", "")
            })
        df_holdings = pd.DataFrame(holdings)
        if not df_holdings.empty:
            st.dataframe(
                df_holdings.sort_values("Value (USD)", ascending=False), 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("Info Link", display_text="View Coin"),
                    "P&L (%)": st.column_config.NumberColumn("P&L (%)", format="%.2f%%"),
                    "P&L ($)": st.column_config.NumberColumn("P&L ($)", format="$%.2f"),
                    "Value (USD)": st.column_config.NumberColumn("Value (USD)", format="$%.2f"),
                    "Avg Entry": st.column_config.NumberColumn("Avg Entry", format="$%.4f"),
                    "Current Price": st.column_config.NumberColumn("Current Price", format="$%.4f")
                }
            )
        else:
            st.info("No active holdings.")

with col_right:
    st.subheader("Recent Trades")
    trades = client.get_recent_trades()
    if trades:
        df_trades = pd.DataFrame(trades)
        df_trades = df_trades[['timestamp', 'coin', 'action', 'price', 'quantity', 'reason']]
        df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(df_trades, use_container_width=True, hide_index=True)
    else:
        st.info("No recent trades found.")

st.divider()

# 4. Watchlist
st.subheader("Watchlist (DexScreener Discoveries)")
watchlist = client.get_watchlist()
if watchlist:
    import requests
    import time
    df_watch = pd.DataFrame(watchlist)
    
    st.dataframe(
        df_watch[['coin', 'priceUsd', 'liquidityUsd', 'volume24h', 'priceChange1h', 'status', 'addedAt']].sort_values(by="addedAt", ascending=False),
        use_container_width=True,
        hide_index=True
    )
    
    pending_coins = df_watch[df_watch['status'] != 'bought']['coin'].unique().tolist()
    if pending_coins:
        col1, col2 = st.columns([1, 4])
        with col1:
            buy_coin = st.selectbox("Select coin to Force Buy", [""] + pending_coins)
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if buy_coin and st.button(f"Force Buy {buy_coin}", type="primary"):
                with st.spinner(f"Executing force buy for {buy_coin}..."):
                    try:
                        resp = requests.get(f"http://localhost:7071/api/ForceBuy?coin={buy_coin}")
                        if resp.status_code == 200:
                            st.success(f"Success: {resp.json().get('message')}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Error: {resp.text}")
                    except Exception as e:
                        st.error(f"Failed to call ForceBuy API: {e}\nEnsure Function App is running locally.")
else:
    st.info("Watchlist is currently empty.")

st.sidebar.markdown("---")
st.sidebar.info("Last refresh: " + datetime.now().strftime("%H:%M:%S"))
if st.sidebar.button("Refresh Data"):
    st.rerun()
