from fastapi import FastAPI
from app.users import users
import psycopg2


app = FastAPI()


@app.get("/")
def home_page():
    return {"message": "Социальная сеть"}

app.include_router(users, prefix='/app/v1/users', tags=['users'])