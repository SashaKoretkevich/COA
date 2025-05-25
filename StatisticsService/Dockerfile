FROM python:3.10

WORKDIR /CAO COPY

RUN pip install --no-cache-dir python-dotenv
RUN pip install grpcio grpcio-tools confluent_kafka clickhouse_connect

COPY . .

EXPOSE 50052

CMD ["python", "stat.py", "kafkaConsumer.py"]