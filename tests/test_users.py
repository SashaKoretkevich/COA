import pytest
from fastapi.testclient import TestClient
from APIGateway.main import api
from APIGateway.models import userCreate, userLogin, userUpdate
import os
from dotenv import load_dotenv
import psycopg2
import json

load_dotenv() 
 
conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("USER"), 
                        password=os.getenv("PASSWORD"), host=os.getenv("HOST"))

client = TestClient(api)

user_data_1 = userCreate(
    firstName="John",
    secondName="Doe",
    userName="user1",
    mail="user3@example.com",
    password="password123",
    age=30,
    gender="Male",
    status="Active",
    phoneNumber="+78004003377"
)

login_data_1 = userLogin(mail="user3@example.com", password="password123")

update_data_1 = userUpdate(
    firstName="tyyttyyt", 
    secondName="string",
    age=30,
    gender="Male",
    status="string",
    phoneNumber="+78004003377"
)

@pytest.fixture
def userRegister():
    response = client.post("/register", json=user_data_1.model_dump())
    assert response.status_code == 200

@pytest.fixture
def userLogin():
    response = client.post("/login", json=login_data_1.model_dump())
    assert response.status_code == 200
    token = response.cookies.get("access_token")
    assert token is not None
    return token

#Проверка валедаторов

def testWrongAge():
    with pytest.raises(ValueError) as info:
        userCreate(
            firstName="John",
            secondName="Doe",
            userName="user1",
            mail="user3@example.com",
            password="password123",
            age=5,
            gender="Male",
            status="Active",
            phoneNumber="+78004003377") 
    assert info.value.errors()[0]['msg'] == "Value error, Возраст должен быть больше 14 лет" 

def testWrongGender():
    with pytest.raises(ValueError) as info:  
        userCreate(
            firstName="John",
            secondName="Doe",
            userName="user1",
            mail="user3@example.com",
            password="password123",
            age=30,
            gender="Cat",
            status="Active",
            phoneNumber="+78004003377") 
    assert info.value.errors()[0]['msg'] == "Value error, Неправильно указан пол"

def testWrongPhone():
    with pytest.raises(ValueError) as info:  
        userCreate(
            firstName="John",
            secondName="Doe",
            userName="user1",
            mail="user3@example.com",
            password="password123",
            age=30,
            gender="Male",
            status="Active",
            phoneNumber="+78004003") 
    assert info.value.errors()[0]['msg'] == 'Value error, Номер телефона должен начинаться с "+" и содержать 11 цифр' 

#Проверка workflow

def testRegLog(userRegister, userLogin):
    assert userLogin is not None


def testGetProfile(userLogin):
    client.cookies.update({"access_token": userLogin})
    response = client.get("/profile")
    assert response.status_code == 200
    user = response.json()
    assert user["firstName"] == "John"

def testUpdateProfile(userLogin):
    client.cookies.update({"access_token": userLogin})
    response = client.put("/profile", json=update_data_1.model_dump())
    assert response.status_code == 200
    response1 = client.get("/profile")
    user = response1.json()
    assert user["firstName"] == "tyyttyyt"


def testLogout(userLogin):
    client.cookies.update({"access_token": userLogin})
    response = client.post("/logout")
    assert response.status_code == 200
    assert "access_token" not in response.cookies
    cur = conn.cursor()
    cur.execute("select userId from auth where mail = 'user3@example.com'")
    userId1 = cur.fetchone()
    cur.execute('delete from auth where userId = %s',(userId1, ) )
    conn.commit()
    cur.close()
    conn.close()