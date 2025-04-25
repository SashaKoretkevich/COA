FROM python:3.10

WORKDIR /CAO

RUN pip install --no-cache-dir psycopg2 python-dotenv
RUN pip install grpcio grpcio-tools confluent_kafka

COPY . .

EXPOSE 50051

CMD ["python", "post.py"]