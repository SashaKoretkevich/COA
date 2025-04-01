FROM python:3.10

WORKDIR /CAO
COPY . .

RUN pip install --no-cache-dir fastapi asyncpg pydantic bcrypt passlib python-jose[cryptography] uvicorn psycopg2 pydantic[email] python-dotenv

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]