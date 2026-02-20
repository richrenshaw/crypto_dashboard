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
