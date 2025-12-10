# 🛒 Real-Time Cart Abandonment Detection

A real-time streaming pipeline that processes e-commerce clickstream data to detect shopping cart abandonment instantly. This system uses Apache Kafka for event ingestion and QuixStreams for stateful stream processing.

**Tech Stack:** Python, Apache Kafka, QuixStreams, Docker

---

## 📂 Project Structure

| File | Description |
| :--- | :--- |
| **`producer.py`** | Simulates live user traffic by reading from `events_sample_nov.csv` and sending events to Kafka topics. |
| **`processor.py`** | Basic stream processing logic for filtering and transforming incoming data. |
| **`processor_abandonment.py`** | The core consumer logic. It monitors user sessions and detects when a cart is abandoned (Time-to-Live expiration without checkout). |
| **`dashboard.py`** | A real-time visualization dashboard to monitor abandonment metrics. |
| **`docker-compose.yml`** | Configuration to spin up the local Kafka broker and Zookeeper environment. |
| **`events_sample_nov.csv`** | A sample dataset of user behavior (View, Cart, Purchase) used for testing. |

---

## 🏗️ Architecture

1.  **Ingestion:** The `producer.py` reads raw CSV data and streams it into a Kafka topic.
2.  **Processing:** QuixStreams (`processor_abandonment.py`) listens to the stream, maintaining a state for each user session.
3.  **Detection:** If a "Cart" event is not followed by a "Purchase" event within the defined window, an "Abandoned" alert is generated.
4.  **Visualization:** The `dashboard.py` consumes the results to display live stats.

---

## 🛠️ Setup & Usage

### Prerequisites
* Docker Desktop (for running Kafka)
* Python 3.8+

### 1. Start Infrastructure
Start the Kafka broker and Zookeeper using Docker:
```bash
docker-compose up -d
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
# OR manually:
pip install quixstreams kafka-python streamlit
```

### 3. Run the Pipeline

**Step A: Start the Dashboard (Optional)**
```bash
python dashboard.py
```
**Step B: Start the Processor**
This will start listening for events.
```bash
python processor_abandonment.py
```

**Step C: Start the Producer**
This will begin sending the sample data to the system.
```bash
python producer.py
```

---

## ⚙️ Configuration
* **Dataset:** The system uses `events_sample_nov.csv` by default.
* **Note:** The full dataset (`2019-Nov.csv`) is excluded from this repository due to size constraints (>100MB).

---

> *"Real-time data turns hindsight into foresight."*
