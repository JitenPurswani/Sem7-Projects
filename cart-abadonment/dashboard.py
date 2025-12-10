import streamlit as st
from kafka import KafkaConsumer
import time
import re
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="Live E-commerce Analysis Dashboard",
    layout="wide"
)

# --- Kafka Consumer Configuration ---
# We need to create two separate consumers for our two topics.
def create_kafka_consumer(topic_name):
    return KafkaConsumer(
        topic_name,
        bootstrap_servers="127.0.0.1:9092",
        auto_offset_reset='earliest', # Read all historical messages
        value_deserializer=lambda v: v.decode('utf-8'),
        consumer_timeout_ms=1000 # Stop blocking for messages after 1 second
    )

abandonment_consumer = create_kafka_consumer("cart-abandonment-alerts")
spending_consumer = create_kafka_consumer("user-spending-alerts")

# --- Session State Initialization ---
# This is where we will store our data so it persists between Streamlit's reruns.
if 'abandonments' not in st.session_state:
    st.session_state.abandonments = []
if 'spending_data' not in st.session_state:
    st.session_state.spending_data = {} # Use a dict to store the latest total for each user

# --- Dashboard UI ---
st.title("📈 Live E-commerce Analysis Dashboard")

# Create placeholders for our KPIs so they can be updated live.
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.markdown("### Total Abandoned Carts")
    kpi1_placeholder = st.empty()

with kpi2:
    st.markdown("### Total Spending Tracked")
    kpi2_placeholder = st.empty()
    
with kpi3:
    st.markdown("### Unique Abandoning Users")
    kpi3_placeholder = st.empty()

st.markdown("<hr/>", unsafe_allow_html=True)

# Create columns for our detailed views
col1, col2 = st.columns(2)

with col1:
    st.header("Top 5 Spenders")
    chart_placeholder = st.empty()

with col2:
    st.header("Latest Abandonment Alerts")
    alerts_placeholder = st.empty()

# --- Data Processing Loop ---
print("Dashboard is running...")
while True:
    # --- Process Abandonment Data ---
    for message in abandonment_consumer:
        st.session_state.abandonments.append(message.value)
    
    # --- Process Spending Data ---
    for message in spending_consumer:
        # Use regex to parse the user ID and spending amount from the alert string
        match = re.search(r"User (\d+) total spending is now \$([\d.]+)", message.value)
        if match:
            user_id = match.group(1)
            total_spent = float(match.group(2))
            st.session_state.spending_data[user_id] = total_spent
            
    # --- Update KPIs ---
    kpi1_placeholder.subheader(f"{len(st.session_state.abandonments)}")
    
    total_spending = sum(st.session_state.spending_data.values())
    kpi2_placeholder.subheader(f"${total_spending:,.2f}")
    
    # Calculate unique users from the abandonment alerts
    unique_users = set()
    for alert in st.session_state.abandonments:
        match = re.search(r"User (\d+)", alert)
        if match:
            unique_users.add(match.group(1))
    kpi3_placeholder.subheader(f"{len(unique_users)}")
    
    # --- Update Chart ---
    if st.session_state.spending_data:
        # Convert dict to a Pandas DataFrame for easy charting
        df = pd.DataFrame(list(st.session_state.spending_data.items()), columns=['User ID', 'Total Spending'])
        df = df.sort_values(by='Total Spending', ascending=False).head(5)
        chart_placeholder.bar_chart(df.set_index('User ID'))
        
    # --- Update Alerts Log ---
    with alerts_placeholder.container():
        for alert in st.session_state.abandonments[:10]: # Show latest 10
            st.warning(alert)
            
    # Wait for 1 second before polling for new messages again
    time.sleep(1)