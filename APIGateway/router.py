from fastapi import FastAPI
from .main import api
import psycopg2


app = FastAPI()


@app.get("/")
def home_page():
    return {"message": "Прокси"}

app.include_router(api, prefix='/app/v1/api', tags=['api'])