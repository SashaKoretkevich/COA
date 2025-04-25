FROM python:3.10

WORKDIR /CAO

RUN pip install --no-cache-dir fastapi requests uvicorn pydantic python-dotenv pydantic[email] psycopg2
RUN pip install grpcio grpcio-tools

COPY . .
CMD ["uvicorn", "router:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]