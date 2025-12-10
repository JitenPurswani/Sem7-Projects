import os
from quixstreams import Application
import json
from datetime import datetime, timedelta

# --- 1. Create a Quix Streams Application ---
app = Application(
    broker_address="127.0.0.1:9092",
    consumer_group="cart-abandonment-detector"
)

input_topic = app.topic("user-events")
output_topic = app.topic("cart-abandonment-alerts")


# --- 2. Define the Streaming Logic ---
sdf = app.dataframe(input_topic)

def parse_event(value):
    data = value
    data['userId'] = str(data['userId'])
    data['event_timestamp'] = datetime.fromisoformat(data['eventTime'].replace(' UTC', '+00:00'))
    return data

sdf = sdf.apply(parse_event)
print("Parsing events from Kafka...")


# The core stateful logic for detecting abandonment
def detect_abandonment(row, state):
    event_type = row['eventType']
    user_id = row['userId']
    timestamp = row['event_timestamp']

    last_cart_time_str = state.get('last_cart_time')
    last_cart_time = None
    if last_cart_time_str:
        last_cart_time = datetime.fromisoformat(last_cart_time_str)

    if event_type == 'cart':
        print(f"User {user_id} added to cart. Storing state.")
        state.set('last_cart_time', timestamp.isoformat())
        return None

    elif event_type == 'purchase':
        if last_cart_time:
            print(f"User {user_id} purchased. Clearing state.")
            # THIS LINE IS NOW CORRECTED
            state.delete('last_cart_time')
        return None

    elif last_cart_time:
        time_since_cart = timestamp - last_cart_time
        
        if time_since_cart > timedelta(minutes=5):
            alert = f"🚨 ALERT: User {user_id} abandoned their cart! Last activity was at {last_cart_time}."
            print(alert)
            # THIS LINE IS ALSO CORRECTED
            state.delete('last_cart_time')
            return alert

    return None


# Group by 'userId' to track each user's state separately
sdf = sdf.group_by('userId').apply(detect_abandonment, stateful=True)

# Filter out the "None" results using the .filter() method
sdf = sdf.filter(lambda value: value is not None)

# Send the real alerts to the output topic
sdf = sdf.to_topic(output_topic)


# --- 4. Run the Application ---
if __name__ == "__main__":
    print("Starting cart abandonment detection job...")
    app.run()