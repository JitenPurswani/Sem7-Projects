import csv
import json
import time
from kafka import KafkaProducer

# --- Kafka Producer Configuration ---
# Connects to the Kafka server running on your machine
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    # Encode messages as JSON
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    # Use the user_id as the key for partitioning
    key_serializer=lambda k: str(k).encode('utf-8')
)

# --- CSV Reading and Streaming ---
csv_file_path = 'events_sample_nov.csv'
print(f"Streaming data from {csv_file_path} to Kafka topic 'user-events'...")

# Open and read the sample CSV file
with open(csv_file_path, mode='r') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        try:
            # Construct the message payload
            message = {
                'eventTime': row['event_time'],
                'eventType': row['event_type'],
                'productId': int(row['product_id']),
                'categoryId': int(row['category_id']),
                'categoryCode': row['category_code'],
                'brand': row['brand'],
                'price': float(row['price']),
                'userId': int(row['user_id']),
                'userSession': row['user_session']
            }

            # Use 'userId' as the key
            user_id_key = message['userId']

            # Send the message to the 'user-events' topic
            producer.send('user-events', key=user_id_key, value=message)

            print(f"Sent message for user: {user_id_key}")

            # Add a small delay to simulate a real-time stream
            time.sleep(0.01)

        except (ValueError, KeyError) as e:
            print(f"Skipping row due to error: {e} -> {row}")
            continue

# Ensure all messages are sent before exiting
producer.flush()
print("Finished streaming data.")