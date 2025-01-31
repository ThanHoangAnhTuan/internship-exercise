import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from confluent_kafka import Consumer
import json
from api.views import save_blood_indicator
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def run_kafka_worker():
    consumer = Consumer({
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'blood_glucose_worker',
        'auto.offset.reset': 'earliest',
    })
    consumer.subscribe(['blood_indicator_topic'])

    while True:
        try:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            data = json.loads(msg.value().decode('utf-8'))
            result = save_blood_indicator(data['user_id'], data['data'])
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{data['user_id']}",
                {
                    "type": "send_response",
                    "response": result
                }
            )
        except Exception as e:
            print(f"Error in worker loop: {e}")

if __name__ == '__main__':
    run_kafka_worker()