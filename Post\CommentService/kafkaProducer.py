import json
from dotenv import load_dotenv, dotenv_values
import os
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
            'client.id': 'post_service_producer'
        })
        
        self.POST_VIEWED_TOPIC = "post_viewed"
        self.POST_LIKED_TOPIC = "post_liked"
        self.POST_COMMENT_TOPIC = "post_comment"
    
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
    
    def send_post_viewed_event(self, user_id: int, post_id: int):
        print(f"Отправка события просмотра в Kafka для поста {post_id}")
        self.send_event(
            topic=self.POST_VIEWED_TOPIC,
            data={
                "event_type": "post_viewed",
                "timestamp": datetime.now(),
                "user_id": user_id,
                "post_id": post_id
            },
            key=str(post_id)
        )
    
    def send_post_liked_event(self, user_id: int, post_id: int):
        print(f"Отправка события лайка в Kafka для поста {post_id}")
        self.send_event(
            topic=self.POST_LIKED_TOPIC,
            data={
                "event_type": "post_liked",
                "timestamp": datetime.now(),
                "user_id": user_id,
                "post_id": post_id
            },
            key=str(post_id)
        ) 
    def send_post_comment_event(self, user_id: int, post_id: int):
        print(f"Отправка события комментария в Kafka для поста {post_id}")
        self.send_event(
            topic=self.POST_COMMENT_TOPIC,
            data={
                "event_type": "post_comment",
                "timestamp": datetime.now(),
                "user_id": user_id,
                "post_id": post_id
            },
            key=str(post_id)
        ) 