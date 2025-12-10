import os
from quixstreams import Application
import json

# --- 1. Create a Quix Streams Application ---
app = Application(
    broker_address="127.0.0.1:9092",
    consumer_group="realtime-spending-calculator"
)

input_topic = app.topic("user-events")
output_topic = app.topic("user-spending-alerts")

# --- 2. Define the Streaming Logic ---
sdf = app.dataframe(input_topic)

# Filter for "purchase" events only
sdf = sdf[sdf['eventType'] == 'purchase']

# THE FIX: Apply a function to convert the userId to a string
def convert_userid_to_str(row):
    row['userId'] = str(row['userId'])
    return row

sdf = sdf.apply(convert_userid_to_str)

print("Processing purchase events...")

# The core stateful logic
def calculate_total_spending(row, state):
    total = state.get('total_spent', 0)
    new_total = total + row['price']
    state.set('total_spent', new_total)
    
    alert = f"ALERT: User {row['userId']} total spending is now ${new_total:.2f}"
    print(alert)
    return alert

# Group the stream by 'userId'
sdf = sdf.group_by('userId').apply(calculate_total_spending, stateful=True)

# Send the generated alerts to our output topic
sdf = sdf.to_topic(output_topic)

# --- 4. Run the Application ---
if __name__ == "__main__":
    # Remove the "sdf" argument to fix the warning
    app.run()