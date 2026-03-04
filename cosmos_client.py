import streamlit as st
from azure.cosmos import CosmosClient, PartitionKey

# load_dotenv()

class CosmosDBClient:
    def __init__(self):
        # Fetch credentials from Streamlit Secrets
        try:
            self.url = st.secrets["COSMOS_DB_URL"]
            self.key = st.secrets["COSMOS_DB_KEY"]
            self.db_name = st.secrets.get("COSMOS_DB_NAME", "tradingdb")
        except KeyError as e:
            st.error(f"Missing Streamlit Secret: {e}")
            st.stop()
            
        self.client = CosmosClient(self.url, self.key)
        self.database = self.client.get_database_client(self.db_name)
        
        # Containers
        self.settings_container = self.database.get_container_client("settings")
        self.trades_container = self.database.get_container_client("trades")
        self.equity_logs_container = self.database.get_container_client("equity_logs")
        self.portfolio_container = self.database.get_container_client("portfolio")
        self.watchlist_container = self.database.get_container_client("watchlist")

    def get_settings(self):
        try:
            return self.settings_container.read_item(item="main_settings", partition_key="main_settings")
        except Exception as e:
            st.error(f"Error fetching settings: {e}")
            return None

    def update_settings(self, settings_doc):
        try:
            self.settings_container.replace_item(item="main_settings", body=settings_doc)
            return True
        except Exception as e:
            st.error(f"Error updating settings: {e}")
            return False

    def get_portfolio(self):
        try:
            return self.portfolio_container.read_item(item="main_portfolio", partition_key="main_portfolio")
        except Exception as e:
            st.error(f"Error fetching portfolio: {e}")
            return None

    def get_equity_logs(self, year="2026"):
        try:
            query = f"SELECT * FROM c WHERE c.year = '{year}' ORDER BY c.timestamp DESC"
            items = list(self.equity_logs_container.query_items(query=query, enable_cross_partition_query=True))
            return items
        except Exception as e:
            st.error(f"Error fetching equity logs: {e}")
            return []

    def get_recent_trades(self, limit=50):
        try:
            query = f"SELECT TOP {limit} * FROM c ORDER BY c.timestamp DESC"
            items = list(self.trades_container.query_items(query=query, enable_cross_partition_query=True))
            return items
        except Exception as e:
            st.error(f"Error fetching trades: {e}")
            return []

    def get_watchlist(self):
        try:
            query = "SELECT * FROM c ORDER BY c.addedAt DESC"
            items = list(self.watchlist_container.query_items(query=query, enable_cross_partition_query=True))
            return items
        except Exception as e:
            st.error(f"Error fetching watchlist: {e}")
            return []

    def clear_all_data(self):
        """
        Clears trades, equity logs, watchlist and resets portfolio.
        Preserves application settings.
        """
        try:
            # 1. Clear Trades (Partition Key is /coin)
            trades = list(self.trades_container.query_items("SELECT c.id, c.coin FROM c", enable_cross_partition_query=True))
            for t in trades:
                pk = t.get('coin')
                # If coin is missing, we must provide something. 
                # According to container definition it's /coin.
                if pk is not None:
                    self.trades_container.delete_item(item=t['id'], partition_key=pk)
                else:
                    # Try to delete without PK or use id if that's how it was stored
                    try:
                        self.trades_container.delete_item(item=t['id'], partition_key=t['id'])
                    except:
                        pass
            
            # 2. Clear Equity Logs (Partition Key is /year)
            logs = list(self.equity_logs_container.query_items("SELECT c.id, c.year FROM c", enable_cross_partition_query=True))
            for l in logs:
                pk = l.get('year')
                if pk is not None:
                    self.equity_logs_container.delete_item(item=l['id'], partition_key=pk)
            
            # 3. Clear Watchlist (Partition Key is /coin)
            watchlist = list(self.watchlist_container.query_items("SELECT c.id, c.coin FROM c", enable_cross_partition_query=True))
            for w in watchlist:
                pk = w.get('coin')
                if pk is not None:
                    self.watchlist_container.delete_item(item=w['id'], partition_key=pk)
            
            # 4. Reset Portfolio
            portfolio = self.get_portfolio()
            if portfolio:
                portfolio['holdings'] = {}
                portfolio['balance_usd'] = 1000.0
                # Explicitly pass partition_key for reliability
                self.portfolio_container.replace_item(item="main_portfolio", body=portfolio, partition_key="main_portfolio")
            
            return True
        except Exception as e:
            print(f"Error in clear_all_data: {e}")
            return False
