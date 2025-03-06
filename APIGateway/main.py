from fastapi import FastAPI, Response, Request,  HTTPException
from .models import userCreate, userLogin, userUpdate
import requests
import json
import os
from dotenv import load_dotenv, dotenv_values 

load_dotenv() 


url = os.environ.get('USER_SERVICE')

api = FastAPI()

@api.post("/register")
def register(user: userCreate):
    response = requests.post(f"{url}register", json=user.model_dump())
    return response.json()

@api.post("/login")
def login(response: Response, user: userLogin):
    responseData = requests.post(f"{url}login", json=user.model_dump()).json()
    if not responseData['access_token']:
        raise HTTPException(status_code=400, detail="Неправильные данные")
    response.set_cookie(key="access_token", value=responseData['access_token'], httponly=True)
    return responseData

@api.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {'message': 'Пользователь вышел из системы'}

@api.put("/profile")
def updateProfile(request: Request, user_data: userUpdate):
    token = request.cookies.get('access_token')
    user_data.token = token
    if not token:
        raise HTTPException(status_code=400, detail="Токен не найден")
    response = requests.put(f"{url}profile", json=user_data.model_dump())
    return response.json()

@api.get("/profile")
def getUser(request: Request):
    send = {}
    send['token'] = request.cookies.get('access_token')
    if not request.cookies.get('access_token'):
        raise HTTPException(status_code=400, detail="Токен не найден")
    response = requests.get(f"{url}profile", json = send)
    return response.json()
