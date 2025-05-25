import json
import os
from dotenv import load_dotenv, dotenv_values
from datetime import datetime
from typing import Dict, Any, Optional
from confluent_kafka import Producer

load_dotenv() 

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")


class KafkaProducer:
    def __init__(self):
        print(f"KAFKA_BOOTSTRAP_SERVERS = {KAFKA_BOOTSTRAP_SERVERS}")
        self.producer = Producer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'user_service_producer'
        })
        self.USER_REGISTERED_TOPIC = "user_registered"
    
    def _delivery_report(self, err, msg):
        if err is not None:
            print(f'Ошибка при доставки сообщения: {err}')
        else:
            print(f'Сообщение доставлено {msg.topic()} [{msg.partition()}]')
    
    def _serialize_datetime(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def send_event(self, topic: str, data: Dict[str, Any], key: Optional[str] = None):
        payload = json.dumps(data, default=self._serialize_datetime).encode('utf-8')
        self.producer.produce(
            topic=topic,
            key=key.encode('utf-8') if key else None,
            value=payload,
            callback=self._delivery_report
        )
        self.producer.flush()
    
    def send_user_registered_event(self, user_id: int):
        print(f"Отправка события в Kafka для пользователя {user_id}")
        self.send_event(
            topic=self.USER_REGISTERED_TOPIC,
            data={
                "event_type": "user_registered",
                "timestamp": datetime.now(),
                "user_id": user_id
            },
            key=str(user_id)
        )
    
    