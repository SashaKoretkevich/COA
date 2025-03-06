FROM python:3.10

WORKDIR /CAO

COPY . .

RUN pip install --no-cache-dir fastapi requests uvicorn pydantic python-dotenv pydantic[email]

CMD ["uvicorn", "main:api", "--host", "0.0.0.0", "--port", "8080", "--reload"]