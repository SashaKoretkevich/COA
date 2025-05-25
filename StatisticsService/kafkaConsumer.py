import json
import os
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaException
from clickhouse_connect import get_client

load_dotenv()

client = get_client(
    host=os.getenv("DBNAME2"),
    port=int(os.getenv("PORT2")),
    username=os.getenv("USER2"),
    password=os.getenv("PASSWORD2")
)

TOPICS = ['post_viewed', 'post_liked', 'post_comment']

def insert_view(event):
    client.command("""
        insert into views (timestamp, postId, userId) values (%(timestamp)s, %(post_id)s, %(user_id)s)
    """, parameters=event)

def insert_like(event):
    client.command("""
        insert into likes (timestamp, postId, userId) values (%(timestamp)s, %(post_id)s, %(user_id)s)
    """, parameters=event)

def insert_comment(event):
    client.command("""
        insert into comments (timestamp, postId, userId) values (%(timestamp)s, %(post_id)s, %(user_id)s)
    """, parameters=event)

def process_message(topic, msg):
    try:
        event = json.loads(msg.value().decode('utf-8'))
        if topic == 'post_viewed':
            insert_view(event)
        elif topic == 'post_liked':
            insert_like(event)
        elif topic == 'post_comment':
            insert_comment(event)
    except Exception as e:
        print(f"Error processing message on topic '{topic}': {e}")

def start_kafka_consumer():
    conf = {
        'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        'group.id': 'statistics-consumer-group',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True
    }

    consumer = Consumer(conf)
    consumer.subscribe(TOPICS)

    print("Kafka consumer started...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())
            process_message(msg.topic(), msg)
    except KeyboardInterrupt:
        print("Kafka consumer interrupted")
    finally:
        consumer.close()