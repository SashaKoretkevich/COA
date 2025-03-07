from fastapi import FastAPI, HTTPException, APIRouter, Response, Request
import psycopg2
from app.models import userCreate, userLogin, userUpdate, tokenSend
from app.auth import pwToHash, verifyPW, createToken
from jose import jwt, JWTError
import os
from dotenv import load_dotenv, dotenv_values
from datetime import datetime
import json

load_dotenv() 

users = APIRouter()
connection = psycopg2.connect(database=os.getenv("DBNAME"), user=os.getenv("USER"), 
                        password=os.getenv("PASSWORD"), host=os.getenv("HOST"))

@users.on_event("shutdown")
def shutdown():
    connection.close()

@users.post("/register")
async def register(user: userCreate):
    cur = connection.cursor()
    cur.execute('select * from auth where mail= %s', (user.mail, ))
    existUserEmail = cur.fetchone()

    cur.execute('select * from auth where userName= %s', (user.userName, ))
    existUserName = cur.fetchone()
    if existUserEmail:
        raise HTTPException(status_code=400, detail="Пользователь с такой почтой уже существует")
    if existUserName:
        raise HTTPException(status_code=400, detail="Пользователь с таким ником уже существует")
    
    hashPW = pwToHash(user.password)
    cur.execute("insert into auth (userName, mail, password) values (%s, %s, %s);", (user.userName, user.mail, hashPW))
    connection.commit()

    cur.execute('select userId from auth where userName= %s', (user.userName,))
    userId = cur.fetchone()[0]
    if not userId:
        raise HTTPException(status_code=400, detail="Ошибка в записи данных пользователя")
    cur.execute('''insert into users(userId, firstName, secondName, age, gender, status, phoneNumber)
    values (%s, %s, %s, %s, %s, %s, %s);''', (userId, user.firstName, user.secondName, user.age, user.gender, user.status, user.phoneNumber))
    connection.commit()
    cur.close()
    return {"id": userId, "username": user.userName, "email": user.mail}

@users.post("/login")
async def login(user: userLogin):
    cur = connection.cursor()
    userId = str()
    userPass = str()

    if  not user.userName == None:
        cur.execute('select userId from auth where userName= %s', (user.userName, ))
        userId = cur.fetchone()[0]
        cur.execute('select password from auth where userName= %s', (user.userName, ))
        userPass = cur.fetchone()[0]
    else:
        cur.execute('select userId from auth where mail= %s', (user.mail, ))
        userId = cur.fetchone()[0]
        cur.execute('select password from auth where mail= %s', (user.mail, ))
        userPass = cur.fetchone()[0]

    if not userId or not verifyPW(user.password, userPass):
        raise HTTPException(status_code=400, detail="Неверные данные")
    
    token = createToken({"sub": str(userId)})
    cur.close()
    return {"access_token": token, 'refresh_token': None}


def validateToken(token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=os.getenv("ALGORITHM"))
    except JWTError:
        raise HTTPException(status_code=400, detail='Токен не валидный!')

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=400, detail="Не найден ID пользователя")
    return user_id

@users.get("/profile")
async def getUser(token: tokenSend):
    userId = validateToken(token.token)
    cur = connection.cursor()
    cur.execute('select * from users where userID= %s', (userId, ))
    user = cur.fetchone()
    cur.close()
    return {"userID": user[0],"firstName": user[1],"secondName": user[2],"age": user[3],"gender": user[4],"status": user[5],"phoneNumber": user[6]}

@users.put("/profile")
async def updateProfile(user: userUpdate):
    userId = validateToken(user.token)
    cur = connection.cursor()
    time = datetime.utcnow()
    cur.execute('''update users set firstName = %s, secondName = %s,
     age = %s, gender = %s, status = %s, phoneNumber = %s, lastUpdate = %s where userID= %s''',(user.firstName,
     user.secondName, user.age, user.gender, user.status, user.phoneNumber, time, userId))
    connection.commit()

    cur.execute('select lastUpdate from users where userID= %s', (userId, ))
    timeLast = cur.fetchone()[0]
    cur.close()
    if timeLast != time:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"message": "Profile updated"}
