from confluent_kafka import Producer

producer = Producer({'bootstrap.servers': 'localhost:9092'})

def send_to_kafka(topic, message):
    try:
        producer.produce(topic, value=message)
        producer.flush()
    except Exception as e:
        print(f"Error sending to Kafka: {e}")
